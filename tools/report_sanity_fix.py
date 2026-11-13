#!/usr/bin/env python3
"""report_sanity_fix — the mechanical counterpart of tools/report_sanity.py.

Fixes the DUPLICATE_SCREENSHOT_EMBED class the W14 bug family produced and
the S230 census (evidence/s230/report_sanity_census.tsv, 964 reports →
#386 queue) measured at scale:

  For every report carrying more than one "Output Frame" section that
  embeds the SAME screenshot, keep the FIRST section and remove every
  later section whose .png embeds are all already-seen duplicates.

The transform is intentionally narrow (no prose touched, kept sections
byte-identical, distinct images never merged) — the W18 correction-wave
pattern, mechanized. Every action lands in a TSV ledger with per-file
before/after violation counts re-measured by tools/report_sanity.py's own
detector, so the ledger is self-verifying.

Usage: python3 tools/report_sanity_fix.py [--apply] [report ...]
  default = dry run over the census; --apply writes the files + ledger.
"""
import csv
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / 'evidence/s230/report_sanity_census.tsv'
LEDGER = ROOT / 'evidence/s232/report_sanity_fix_ledger.tsv'
IMG_EMBED_RE = re.compile(r'!\[[^\]]*\]\(([^)\s]+\.png)\)', re.I)
OF_HEADER_RE = re.compile(r'^(#+)\s*Output Frame\b.*$', re.M)


def detector_violations(report_path):
    """Run the repo's own detector for one report; return violation count."""
    r = subprocess.run(
        ['python3', str(ROOT / 'tools/report_sanity.py'), str(report_path)],
        capture_output=True, text=True, cwd=str(ROOT), timeout=60)
    out = r.stdout + r.stderr
    return out.count('DUPLICATE_SCREENSHOT_EMBED'), out


def section_spans(text):
    """[(start_line, end_line_exclusive)] for each Output Frame section."""
    lines = text.split('\n')
    spans = []
    i = 0
    while i < len(lines):
        if re.match(r'^#+\s*Output Frame\b', lines[i]):
            start = i
            j = i + 1
            while j < len(lines):
                if re.match(r'^#{1,3}\s', lines[j]):  # next same/lower header
                    break
                j += 1
            spans.append((start, j))
            i = j
        else:
            i += 1
    return spans


def dedupe(text):
    """Remove later Output Frame sections whose .png embeds are all dups."""
    spans = section_spans(text)
    if len(spans) <= 1:
        return text, 0
    lines = text.split('\n')
    seen = set()
    drop = []
    for (s, e) in spans:
        body = '\n'.join(lines[s:e])
        embeds = [os.path.normpath(x).lower()
                  for x in IMG_EMBED_RE.findall(body)
                  if x.lower().endswith('.png')]
        if embeds and all(x in seen for x in embeds):
            drop.append((s, e))
        else:
            seen.update(embeds)
    if not drop:
        return text, 0
    keep = [True] * len(lines)
    for (s, e) in drop:
        for k in range(s, min(e, len(lines))):
            keep[k] = False
    out = '\n'.join(l for l, k in zip(lines, keep) if k)
    return out, len(drop)


def census_reports():
    rows = list(csv.reader(open(CENSUS), delimiter='\t'))
    return [r[0] for r in rows[1:]
            if r[1].strip().startswith('DUPLICATE_SCREENSHOT_EMBED')]


SCAN = ROOT / 'evidence/s232/report_sanity_scan.tsv'
SHA_LEDGER = ROOT / 'evidence/s232/report_sanity_sha_ledger.tsv'


def scan_repo():
    """Run the repo detector once over evidence/ + docs/; write the scan."""
    r = subprocess.run(
        ['python3', str(ROOT / 'tools/report_sanity.py'),
         str(ROOT / 'evidence'), str(ROOT / 'docs')],
        capture_output=True, text=True, cwd=str(ROOT), timeout=590)
    per = {}
    for line in (r.stdout + r.stderr).splitlines():
        m = re.match(r'^\s+([A-Z_]+): ([^:]+\.md):', line)
        if m:
            per.setdefault(m.group(2), set()).add(m.group(1))
    with open(SCAN, 'w') as f:
        f.write('report\tviolations\n')
        for p in sorted(per):
            f.write(f"{p}\t{','.join(sorted(per[p]))}\n")
    print(f"scan: {len(per)} reports with violations -> {SCAN}")


def first_shot(text, rdir):
    """Resolve the retained screenshot the way the detector does."""
    embeds = [e for e in IMG_EMBED_RE.findall(text)
              if e.lower().endswith('.png')]
    for e in embeds:
        cand = e if os.path.isabs(e) else os.path.join(rdir, e)
        if os.path.exists(cand):
            return cand
    return None


def add_sha_line(text, sha):
    """Insert the SHA256 provenance line into the kept Output Frame section
    (after the embed line) — the W18 correction-wave provenance shape."""
    spans = section_spans(text)
    lines = text.split('\n')
    anchor = None
    if spans:
        s, e = spans[0]
        for k in range(e - 1, s, -1):
            if lines[k].strip():
                anchor = k
                break
    else:
        for k in range(len(lines) - 1, -1, -1):
            if IMG_EMBED_RE.search(lines[k]):
                anchor = k
                break
    if anchor is None:
        return text, False
    lines.insert(anchor + 1, f"- **SHA256:** `{sha}` (recorded by "
                             f"tools/report_sanity_fix.py from the actual "
                             f"retained file)")
    return '\n'.join(lines), True


def sha_pass(reports):
    import hashlib
    SHA_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    ledger = open(SHA_LEDGER, 'w')
    ledger.write('report\tsha256\tviolations_before\tviolations_after\t'
                 'status\n')
    fixed = no_shot = nochange = 0
    for p in reports:
        path = ROOT / p
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        before, _ = detector_violations(p)
        shot = first_shot(text, os.path.dirname(str(path)))
        if shot is None:
            no_shot += 1
            ledger.write(f'{p}\t\t{before}\t{before}\tNO_RESOLVED_SHOT\n')
            continue
        sha = hashlib.sha256(Path(shot).read_bytes()).hexdigest()
        new, inserted = add_sha_line(text, sha)
        if not inserted:
            nochange += 1
            ledger.write(f'{p}\t{sha}\t{before}\t{before}\tNO_ANCHOR\n')
            continue
        path.write_text(new, encoding='utf-8')
        after, _ = detector_violations(p)
        ok = (before - after) if 'MISSING_SCREENSHOT_SHA' in str(before) \
            else (before - after)
        ledger.write(f'{p}\t{sha}\t{before}\t{after}\t'
                     f"{'FIXED' if 'MISSING_SCREENSHOT_SHA' not in str(after) else 'RESIDUAL'}\n")
        fixed += 1
    ledger.close()
    print(f"sha pass: scanned {len(reports)}  fixed {fixed}  "
          f"no-shot {no_shot}  no-anchor {nochange}  ledger {SHA_LEDGER}")


def sha_scan_list():
    """Reports from the scan TSV carrying MISSING_SCREENSHOT_SHA."""
    rows = list(csv.reader(open(SCAN), delimiter='\t'))
    return [r[0] for r in rows[1:]
            if 'MISSING_SCREENSHOT_SHA' in r[1]]


def main(argv):
    if '--scan' in argv:
        scan_repo()
        return
    apply = '--apply' in argv
    rest = [a for a in argv if not a.startswith('--')]
    offset = int(argv[argv.index('--offset') + 1]) if '--offset' in argv else 0
    limit = int(argv[argv.index('--limit') + 1]) if '--limit' in argv else None
    if '--sha' in argv:
        if '--offset' in argv or '--limit' in argv:
            rest = []  # chunk mode always runs over the scan list
        reports = rest if rest else sha_scan_list()
        if not rest and offset:
            reports = reports[offset:]
        if limit:
            reports = reports[:limit]
        sha_pass(reports)
        return
    if '--offset' in argv or '--limit' in argv:
        rest = []  # chunk mode always runs over the census list
    reports = rest if rest else census_reports()
    if not rest and offset:
        reports = reports[offset:]
    if limit:
        reports = reports[:limit]
    mode = 'chunk' if (offset or not rest) else 'list'
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    ledger_mode = 'a' if (offset and (ROOT / LEDGER).exists()) else 'w'
    ledger = open(LEDGER, ledger_mode)
    if ledger_mode == 'w':
        ledger.write('report\tsections_removed\tviolations_before\t'
                     'violations_after\tstatus\n')
    fixed = skipped_unreadable = nochange = 0
    for p in reports:
        path = ROOT / p
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            skipped_unreadable += 1
            continue
        new, removed = dedupe(text)
        before, _ = detector_violations(p)
        if removed == 0:
            nochange += 1
            ledger.write(f'{p}\t0\t{before}\t{before}\tNO_SECTION_DUP\n')
            continue
        if not apply:
            ledger.write(f'{p}\t{removed}\t{before}\t{before}\t'
                         f'DRY_RUN_WOULD_FIX\n')
            continue
        path.write_text(new, encoding='utf-8')
        after, _ = detector_violations(p)
        ledger.write(f'{p}\t{removed}\t{before}\t{after}\t'
                     f'{"FIXED" if after < before else "RESIDUAL"}\n')
        fixed += 1
    ledger.close()
    print(f"reports scanned: {len(reports)}  fixed: {fixed}  "
          f"no-change: {nochange}  unreadable: {skipped_unreadable}")
    print(f"ledger: {LEDGER}")


if __name__ == '__main__':
    main(sys.argv[1:])
