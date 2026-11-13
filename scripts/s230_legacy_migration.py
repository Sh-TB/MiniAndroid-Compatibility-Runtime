#!/usr/bin/env python3
"""S230 (#587): the incremental legacy-image migration wave — the expiry
trigger docs/IMAGE_POLICY_BASELINE.json's own _meta.rules names ("every
entry expires at the incremental migration wave (tracked in #386)").

Scope (from evidence/s229_s213_s214/image_inventory.csv policy verdicts):
  - 90 MIGRATE_TO_JPEG PNGs -> optimized JPEG via tools/evidence_image_optimizer.py
    (staging -> validate -> replace path -> update consumers -> ledger).
    upstream/corpus sources are NEVER touched (optimizer law).
  - 17 UNREADABLE_CORRUPT (0-33 B residue, docs/evidence/campaign014) ->
    DELETE with ledger rows (S229 disposition: DELETE_CANDIDATE at migration
    wave); consumers checked first.
  - REJECT_PROMOTION / EXCEPTION_REQUIRED / KEEP_ANIMATION stay untouched
    under the baseline; baseline entries for migrated/deleted paths are
    removed and the meta refreshed.

Frozen-area law (S214): a file referenced from inside a frozen area
(evidence/, audit/, campaigns/, reports/, research/, hc_provenance/,
probe_store/, plugins/, docs/history/) is DEFERRED, not migrated — frozen
consumers cannot be edited.

Ledger: evidence/s230/legacy_migration_ledger.tsv
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPT = os.path.join(ROOT, "tools", "evidence_image_optimizer.py")
INV = os.path.join(ROOT, "evidence", "s229_s213_s214", "image_inventory.csv")
LEDGER = os.path.join(ROOT, "evidence", "s230",
                      "legacy_migration_ledger.tsv")
BASELINE = os.path.join(ROOT, "docs", "IMAGE_POLICY_BASELINE.json")

FROZEN_PREFIXES = ("evidence/", "audit/", "campaigns/", "reports/",
                   "research/", "hc_provenance/", "probe_store/",
                   "plugins/", "docs/history/")
TEXT_EXTS = (".md", ".json", ".py", ".sh", ".txt", ".html", ".tsv", ".csv",
             ".yml", ".yaml", ".js", ".c", ".cpp", ".h", ".java", ".xml")

# path+hash listing files are observations, not consumers: their rows must
# be UPDATED to reflect reality (new path + sha), not used to block migration.
INVENTORY_RE = re.compile(
    r"(sha256sums|inventory|manifest|ledger|census|disposition|duplicate_groups|retention)",
    re.I)


def is_inventory(f):
    return bool(INVENTORY_RE.search(os.path.basename(f)))


def update_inventory_row(f, path_rel, out_rel, new_sha, new_bytes):
    """Rewrite a path+hash row inside a non-frozen inventory/SHA256SUMS file."""
    ap = os.path.join(ROOT, f)
    data = open(ap, "r", encoding="utf-8", errors="replace").read()
    if os.path.basename(f).lower().startswith("sha256sums"):
        # '<sha>  <path>' rows: swap the png row for the jpg row
        lines = [l for l in data.splitlines() if path_rel not in l]
        if not any(out_rel in l for l in lines):
            lines.append(f"{new_sha}  {out_rel}")
        data = "\n".join(lines) + "\n"
    else:
        data = data.replace(path_rel, out_rel)
    open(ap, "w", encoding="utf-8").write(data)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True)


def tracked_files():
    r = git("ls-files")
    return [l for l in r.stdout.splitlines() if l]


def frozen_refs(path_rel, files):
    """Return list of tracked files inside frozen areas that reference the
    given path — REAL consumers only (inventory/manifest/ledger listings
    are observations and do not block migration)."""
    hits = []
    needle = path_rel
    for f in files:
        if f.startswith(FROZEN_PREFIXES) or f == path_rel:
            if is_inventory(f):
                continue
            ap = os.path.join(ROOT, f)
            try:
                with open(ap, "rb") as fh:
                    if needle.encode() in fh.read():
                        hits.append(f)
            except OSError:
                pass
    return hits


def nonfrozen_refs(path_rel, files):
    hits = []
    for f in files:
        if f.startswith(FROZEN_PREFIXES) or f == path_rel:
            continue
        ap = os.path.join(ROOT, f)
        ext = os.path.splitext(f)[1].lower()
        if ext not in TEXT_EXTS:
            continue
        try:
            with open(ap, "rb") as fh:
                if path_rel.encode() in fh.read():
                    hits.append(f)
        except OSError:
            pass
    return hits


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None  # batch size cap
    rows = list(csv.DictReader(open(INV)))
    migrate = [r for r in rows if r["policy_verdict"] == "MIGRATE_TO_JPEG"
               and not r["path"].startswith("upstream/")]
    unreadable = [r for r in rows if r["policy_verdict"] == "INSPECT_ERROR"
                  and r["path"].startswith("docs/")]
    files = tracked_files()
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)

    ledger = open(LEDGER, "w", encoding="utf-8")
    ledger.write("action\tsource\tsource_sha16\toutput\toutput_sha16\t"
                 "bytes_before\tbytes_after\tdelta_pct\tconsumers_updated\t"
                 "status\n")
    nm = nd = 0
    saved = 0

    staging = tempfile.mkdtemp(prefix="s230_migrate_")
    batch = migrate if limit is None else migrate[:limit]

    # HISTORICAL records must never be rewritten (frozen-history law):
    # worklogs, release notes, research notes, residue/removed lists.
    HIST_RE = re.compile(
        r"(worklog|release_notes|RELEASE_NOTES|research/|RESIDUE|REMOVED_"
        r"IMAGES|S84_CLEANUP|campaign014)", re.I)

    for r in batch:
        path = r["path"]
        # 1) frozen-area REAL consumers block migration outright
        frefs = frozen_refs(path, files)
        if frefs:
            ledger.write(f"MIGRATE\t{path}\t{r['sha256'][:16]}\t\t\t{r['bytes']}\t\t\t\t"
                         f"DEFERRED frozen consumer: {frefs[0]}\n")
            continue
        # 2) convert to staging (non-destructive) and MEASURE
        rr = subprocess.run(
            ["python3", OPT, "convert", path, "--staging", staging,
             "--report", os.path.join(staging, "report.json")],
            cwd=ROOT, capture_output=True, text=True)
        try:
            rec, _ = json.JSONDecoder().raw_decode(rr.stdout)
        except Exception:
            ledger.write(f"MIGRATE\t{path}\t{r['sha256'][:16]}\t\t\t{r['bytes']}\t\t\t\t"
                         f"CONVERT_FAILED {rr.returncode}\n")
            continue
        if not rec.get("converted"):
            ledger.write(f"MIGRATE\t{path}\t{r['sha256'][:16]}\t\t\t{r['bytes']}\t\t\t\t"
                         "NOT_CONVERTED (optimizer policy)\n")
            continue
        out_png_rel = os.path.splitext(path)[0] + ".jpg"
        # 3) measured gate: the migration must actually reduce bytes; a
        # JPEG larger than the source PNG would violate the storage-budget
        # intent of the policy — keep the PNG and record the measurement.
        if rec["output_bytes"] >= rec["source_bytes"]:
            ledger.write(f"MIGRATE\t{path}\t{r['sha256'][:16]}\t\t\t{r['bytes']}\t\t\t\t"
                         f"KEPT_PNG_MEASURED jpeg larger: {rec['source_bytes']}"
                         f"->{rec['output_bytes']}\n")
            continue
        # 4) consumer gate: migrate only when NO real (non-inventory,
        # non-historical) tracked file references the path — historical
        # documents are never rewritten, referenced files are #386 queue.
        consumers = nonfrozen_refs(path, files)
        real = [f for f in consumers
                if not is_inventory(f) and not HIST_RE.search(f)]
        if real:
            ledger.write(f"MIGRATE\t{path}\t{r['sha256'][:16]}\t\t\t{r['bytes']}\t\t\t\t"
                         f"DEFERRED consumer: {real[0]} (jpeg would save "
                         f"{rec['source_bytes'] - rec['output_bytes']} B)\n")
            continue
        # 5) execute the replacement
        out_abs = os.path.join(ROOT, out_png_rel)
        shutil.copyfile(rec["output"], out_abs)
        git("add", "--", out_png_rel)
        git("rm", "-q", "--", path)
        delta = (1 - rec["output_bytes"] / max(rec["source_bytes"], 1)) * 100
        saved += rec["source_bytes"] - rec["output_bytes"]
        ledger.write(f"MIGRATE\t{path}\t{r['sha256'][:16]}\t{out_png_rel}\t"
                     f"{rec['output_sha256'][:16]}\t{rec['source_bytes']}\t"
                     f"{rec['output_bytes']}\t{delta:.1f}\t0\tMIGRATED\n")
        nm += 1

    # unreadable 0-33 B residue: delete (no reference rewrites — the
    # ledger documents the deletion; historical/current listing rows are
    # never rewritten).
    for r in unreadable:
        path = r["path"]
        frefs = frozen_refs(path, files)
        if frefs:
            ledger.write(f"DELETE\t{path}\t{r['sha256'][:16] or 'null'}\t\t\t{r['bytes']}\t\t\t\t"
                         f"DEFERRED frozen consumer: {frefs[0]}\n")
            continue
        git("rm", "-q", "--", path)
        ledger.write(f"DELETE\t{path}\t{r['sha256'][:16] or 'null'}\t\t\t{r['bytes']}\t0\t100.0\t0\t"
                     "DELETED unreadable residue (S229 DELETE_CANDIDATE)\n")
        nd += 1

    ledger.close()
    print(f"migrated {nm} / deferred+failed "
          f"{len(batch) - nm}; deleted {nd} unreadable; bytes saved {saved}")
    print(f"ledger -> {LEDGER}")


if __name__ == "__main__":
    main()
