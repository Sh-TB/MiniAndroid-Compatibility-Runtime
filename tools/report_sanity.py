#!/usr/bin/env python3
"""report_sanity.py — mechanical honesty checks for run report.md files.

Enforces the #587 evidence-size forensic addendum (comment 6844286329) §5/§7
laws that the S212/W18 correction wave applied by hand, as an always-on tool:

  - STALE_SCREENSHOT_SIZE   report states a screenshot byte size that does not
                            match the actual tracked file.
  - DUPLICATE_SCREENSHOT_EMBED  the same screenshot embedded twice / two
                            "Output Frame" sections pointing at one image.
  - MISSING_RUN_ID          the report never names its own run id.
  - APK_PATH_MISMATCH       the report references an APK/store path that names
                            a different run id (e.g. r4 report -> r1 store).
  - MISSING_SCREENSHOT_SHA  no sha256 recorded for the retained screenshot.
  - CONTRADICTORY_VERDICT   a SUCCESS/REAL_APP_CONTENT headline while the same
                            report records NO_APP_OPS / app_draw_ops=0 /
                            uncaught>0 / STUBBED census without the explicit
                            caveat line ("first-frame boundary only" /
                            "NOT <app> gameplay/UI" / "NOT evidence of app UI").
  - PIXEL_PROVENANCE_MISMATCH  a REAL_APP_CONTENT claim with app_draw_ops=0
                            in the same report.

Every violation prints the exact path + reason. Exit 1 when any violation is
found (warnings alone never pass — S214 law). Repo-portable: discovers the
repository root from __file__; no machine-specific paths.
"""
import hashlib
import os
import re
import sys

SIZE_RE = re.compile(r"(\d[\d,]*)\s*bytes", re.I)
SHA_RE = re.compile(r"\b[0-9a-f]{64}\b", re.I)
RUNID_RE = re.compile(r"([a-z0-9][a-z0-9_]*_r\d+[a-z0-9_]*)", re.I)
RUNFAM_RE = re.compile(r"_r\d+", re.I)
STORE_RE = re.compile(r"store_([a-z0-9_]+r\d+[a-z0-9_]*)", re.I)
SUCCESS_RE = re.compile(r"\bSUCCESS\b", re.I)
REAL_CONTENT_RE = re.compile(r"REAL_APP_CONTENT", re.I)
NOOPS_RE = re.compile(r"NO_APP_OPS|app_draw_ops\s*=\s*0\b", re.I)
UNCAUGHT_RE = re.compile(r"(\d+)\s+uncaught", re.I)
STUB_RE = re.compile(r"\bSTUBBED\b", re.I)
CAVEAT_RE = re.compile(
    r"first[- ]frame boundary only|NOT\s+\w+\s+gameplay|NOT evidence of app UI|"
    r"unreconciled classifier contradiction|explicit F-016/stub caveats|"
    r"honest status|caveat", re.I)
IMG_EMBED_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_report(report_path):
    """Return a list of (code, detail) violations for one report.md."""
    violations = []
    rdir = os.path.dirname(os.path.abspath(report_path))
    try:
        with open(report_path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        return [("REPORT_UNREADABLE", str(e))]

    # run id: the folder name is the run id when it carries a digit (any
    # naming convention, not only *_rN); otherwise look for "run id:" in
    # the body, then any run-id token.
    run_id = os.path.basename(rdir)
    if not (re.search(r"\d", run_id) and not run_id.startswith("store_")):
        m = re.search(r"run id:\s*`?([a-z0-9_\-]+)", text, re.I) \
            or RUNID_RE.search(text)
        run_id = m.group(1) if m else None
    if not run_id:
        violations.append(("MISSING_RUN_ID",
                           f"{report_path}: no run id in folder name or body"))

    # screenshot target(s): every image embed that looks like a png
    embeds = [e for e in IMG_EMBED_RE.findall(text) if e.lower().endswith(".png")]

    # duplicate embed law (D-tier rule): never embed the SAME screenshot
    # twice in one Markdown report (the W14 bug: two 'Output Frame'
    # sections pointing at the same image). Distinct images may coexist.
    seen = set()
    for e in embeds:
        key = os.path.normpath(e).lower()
        if key in seen:
            violations.append(("DUPLICATE_SCREENSHOT_EMBED",
                               f"{report_path}: the same screenshot embedded "
                               f"twice ({e})"))
            break
        seen.add(key)
    # duplicate "Output Frame" section headers
    of = len(re.findall(r"^#+\s*Output Frame\b", text, re.M))
    if of > 1:
        violations.append(("DUPLICATE_SCREENSHOT_EMBED",
                           f"{report_path}: {of} 'Output Frame' sections"))

    # resolve the embedded screenshot path (relative to the report)
    shot = None
    if embeds:
        cand = os.path.normpath(os.path.join(rdir, embeds[0]))
        shot = cand if os.path.exists(cand) else None

    # stale size law: any "<N> bytes" claim about the screenshot must match
    if shot is not None:
        actual = os.path.getsize(shot)
        for m in SIZE_RE.finditer(text):
            claimed = int(m.group(1).replace(",", ""))
            # only flag claims that are screenshot-sized (within any range)
            # but wrong — the W18 bug was 7.91 MB claimed vs 2.86 MB actual
            if claimed != actual and claimed > 100_000:
                violations.append((
                    "STALE_SCREENSHOT_SIZE",
                    f"{report_path}: claims {claimed} bytes, actual "
                    f"{actual} bytes ({os.path.relpath(shot, repo_root())})"))
                break

    # sha law: a retained screenshot must have its sha256 recorded
    if shot is not None and not SHA_RE.search(text):
        violations.append(("MISSING_SCREENSHOT_SHA",
                           f"{report_path}: no sha256 for the retained "
                           "screenshot"))

    # apk/store path mismatch: a store path naming another run of the SAME
    # batch family (the W18 bug: r4's report pointed at store_..._r1).
    if run_id:
        my_fam = RUNFAM_RE.sub("", run_id).lower()
        for m in STORE_RE.finditer(text):
            their_fam = RUNFAM_RE.sub("", m.group(1)).lower()
            their_r = RUNID_RE.search(m.group(1))
            if my_fam == their_fam and their_r and their_r.group(1).lower() != run_id.lower():
                violations.append((
                    "APK_PATH_MISMATCH",
                    f"{report_path}: references store_{m.group(1)} but the "
                    f"report's run id is {run_id}"))
                break

    # contradiction law: SUCCESS/REAL_APP_CONTENT headline vs NO_APP_OPS /
    # uncaught>0 / stub census without the explicit honest-status caveat
    success_claim = bool(SUCCESS_RE.search(text)) or bool(REAL_CONTENT_RE.search(text))
    noops = bool(NOOPS_RE.search(text))
    uncaught = UNCAUGHT_RE.search(text)
    uncaught_n = int(uncaught.group(1)) if uncaught else 0
    stubbed = bool(STUB_RE.search(text))
    caveat = bool(CAVEAT_RE.search(text))
    if success_claim and (noops or uncaught_n > 0 or stubbed) and not caveat:
        why = []
        if noops:
            why.append("NO_APP_OPS/app_draw_ops=0")
        if uncaught_n > 0:
            why.append(f"{uncaught_n} uncaught")
        if stubbed:
            why.append("STUBBED census")
        violations.append((
            "CONTRADICTORY_VERDICT",
            f"{report_path}: success/REAL_APP_CONTENT claim with "
            f"{'/'.join(why)} and no honest-status caveat"))
    if REAL_CONTENT_RE.search(text) and noops and not caveat:
        violations.append((
            "PIXEL_PROVENANCE_MISMATCH",
            f"{report_path}: REAL_APP_CONTENT claimed while the same report "
            "records NO_APP_OPS / app_draw_ops=0"))
    return violations


def iter_reports(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                if ".git" in root:
                    continue
                for fn in files:
                    if fn == "report.md":
                        yield os.path.join(root, fn)
        elif os.path.isfile(p):
            yield p


def main(argv):
    """Usage: report_sanity.py <path>...

    The gate usage passes the NEW run directory being promoted (the runner
    and tests do this). Historical frozen evidence is NOT mass-scanned by
    default (S214 frozen-area law: existing content may not be batch-edited;
    use --scan <tree> for an opt-in count-only census).
    """
    args = [a for a in argv[1:] if not a.startswith("--")]
    scan_mode = "--scan" in argv
    if not args:
        print("usage: report_sanity.py [--scan] <path>...  (pass the new run "
              "dir for gate use; --scan for an opt-in historical census)")
        return 2
    violations = []
    checked = 0
    for rp in iter_reports(args):
        checked += 1
        violations.extend(check_report(rp))
    print(f"report_sanity: checked {checked} report.md files, "
          f"{len(violations)} violation(s)")
    for code, detail in violations:
        print(f"  {code}: {detail}")
    if scan_mode:
        # opt-in census: count-only verdict, no gate failure
        return 0
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
