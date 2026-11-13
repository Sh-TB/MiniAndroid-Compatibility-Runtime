#!/usr/bin/env python3
"""S212/WP1 — disposition ledger for #587 R02/R04 (+R26/R27 evidence rows).

Every action candidate gets: path, bytes, blob sha16, class, action,
consumer proof / reason, regeneration method.
Committed as compact TSV; deletions executed in reviewed batches after this.
"""
import hashlib
import subprocess
from pathlib import Path

BASE = Path("/home/z/my-project")
OUT = BASE / "evidence/s212/wp1_inventory"
OUT.mkdir(parents=True, exist_ok=True)


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def sz(p: Path) -> int:
    return p.stat().st_size


rows = []


def add(path, action, cls, reason, regen="not regenerated; historical session artifact"):
    p = BASE / path
    if p.exists():
        rows.append((path, sz(p), sha16(p), cls, action, reason, regen))
    else:
        rows.append((path, -1, "-" * 16, cls, action + " (already absent)", reason, regen))


# ── Batch 1: session residue at root + miniandroid (raw command logs, transient outputs)
add("gfx_trace.jsonl", "DELETE", "RAW_LOG_OUTPUT",
    "transient engine gfx-trace output captured at repo root; writers set their own output path via MINIANDROID_GFX_TRACE_FILE (scripts/cont83_gfx_matrix.py); no reader of the root path",
    "produced by any engine run with gfx tracing enabled")
for i in ["2", "3", "4", "5", "6", "7"]:
    add(f"s203_out{i}.txt", "DELETE", "RAW_LOG_OUTPUT",
        "S203 session make/output residue at repo root; no consumer (root-law R28)")
for n in range(2, 13):
    add(f"miniandroid/make_out{n}.txt" if n >= 4 else None or "", "", "", "", "") if False else None
for n in range(4, 13):
    add(f"miniandroid/make_out{n}.txt", "DELETE", "RAW_LOG_OUTPUT",
        "compiler stdout residue; reproducible via documented build command `make -C miniandroid`")
for n in ["", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]:
    add(f"miniandroid/make_err{n}.txt", "DELETE", "RAW_LOG_OUTPUT",
        "compiler stderr residue; make_err10.txt==make_err11.txt byte-identical (same-blob dup); reproducible via documented build command")
add("miniandroid/build_status.txt", "DELETE", "RAW_LOG_OUTPUT",
    "one-off session status dump; no consumer (build truth is the binary + gate records)")

# ── Batch 2: exact duplicate evidence (blob-identical, proven by SHA)
add("evidence/s195_audit/comments_raw.partial.json", "DEDUPLICATE(keep comments_raw.json)", "RAW_API_DUMP",
    "byte-identical dup of comments_raw.json (sha 386eb21b…); .partial is a fetch transient written by scripts/s195_audit_fetch_comments.py; the 4 consumer scripts read comments_raw.json",
    "scripts/s195_audit_fetch_comments.py refetch")

# ── Batch 4: OSMesa (R26) — resolved in osmesa batch, recorded here
osmesa_files = subprocess.run(["git", "ls-files", "third_party/osmesa"], cwd=BASE,
                              capture_output=True, text=True).stdout.splitlines()
for p in osmesa_files:
    if p == "third_party/osmesa/test_osmesa.c":
        add(p, "MOVE->tests/graphics/backends/osmesa/", "THIRD_PARTY_VENDORED",
            "standalone OSMesa sanity probe (context create + pixel readback); only consumer of libOSMesa; no build/runtime consumer anywhere else in tree (searched all source/CMake/Make/scripts/workflows)")
    elif p == "third_party/osmesa/test_osmesa":
        add(p, "DELETE", "BINARY_CACHE_OBJ",
            "prebuilt test ELF; regenerable from test_osmesa.c via documented recipe; tracked binaries forbidden by R26/R32")
    elif p.startswith("third_party/osmesa/README") or p.endswith("MANIFEST.json"):
        add(p, "MOVE->tests/graphics/backends/osmesa/", "THIRD_PARTY_VENDORED",
            "provenance/license/recipe documentation travels with the test")
    else:
        add(p, "DELETE", "THIRD_PARTY_VENDORED",
            "vendored OSMesa distribution (6 paths share one 15,693,864-byte blob 75dd953d…; debs duplicate extracted trees): no build/runtime consumer; renderer uses PortableGL + own GLES bridge; replaced by pinned-bootstrap recipe (R26 disposition 2/4/5)")

# ── Batch 5: forensic raw dumps (R27) — generator decoupling precedes removal
for p in subprocess.run(["git", "ls-files", "forensic_data"], cwd=BASE,
                        capture_output=True, text=True).stdout.splitlines():
    if p.startswith("forensic_data/ar5_patch/"):
        add(p, "TRIAGE->patch provenance record", "FORENSIC_RAW",
            "3 saved patch/diff parts: individually traced to originating issue/commit; merged ones documented, still-live ones rehomed (R27-1)")
    else:
        add(p, "DELETE(after ledger rebuild validated)", "RAW_API_DUMP",
            "raw GitHub API export consumed only by scripts/forensic_ledger.py; generator migrated to compact normalized source + optional online mode writing to ignored .cache/forensics/ (R27-3/4); canonical result = docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl (390 rows)")

with open(OUT / "disposition_ledger.tsv", "w") as f:
    f.write("path\tbytes\tblob_sha16\tclass\taction\treason\tregeneration\n")
    for r in rows:
        f.write("\t".join(str(x) for x in r) + "\n")
print(f"ledger rows: {len(rows)}")
for cls_action in sorted({(r[3], r[4].split("(")[0].strip()) for r in rows}):
    print(cls_action)
