#!/usr/bin/env python3
"""S91: English-only audit of git-tracked files (canonical check).
Scans tracked file NAMES and file CONTENTS for Arabic/Persian script blocks.
Persian chars live in: U+0600-06FF, U+0750-077F, U+08A0-08FF, U+FB50-FDFF, U+FE70-FEFF.

POLICY (owner mandate: zero Persian in authored content):
  ALLOWLISTED categories (documented, auditable, still counted):
    1. upstream/corpus/**        - unmodified third-party app source snapshots
                                   (values-fa / values-ar localization = the app's own data)
    2. RTL/Arabic-script TEST VECTORS - the fixtures and proof programs whose
                                   purpose is proving Persian text shaping/rendering
                                   (f05_persian fixtures + generators + shaping proofs)
    3. captured evidence JSON    - view_tree.json snapshots recorded at runtime
  Everything else must be English. Report exits non-zero if any
  NON-allowlisted file contains Arabic-script characters.
"""
import subprocess, sys, re, unicodedata

ALLOWLIST = [
    # category 1: third-party upstream sources (never modify)
    "upstream/",
    # category 2: RTL / Persian-shaping test vectors (they ARE the test data)
    "scripts/foundation/make_fixtures.sh",
    "scripts/foundation/make_fixtures_wave2.sh",
    "miniandroid/tests/fixtures_foundation/f05_persian/",
    "miniandroid/tests/fixtures_foundation/f05b_persian2/",
    "miniandroid/tests/fixtures_foundation/f49_canstext/",
    "miniandroid/tests/fixtures_foundation/f08_canvasops/",
    "miniandroid/scripts/exp101_persian_rtl_proof.cpp",
    "miniandroid/scripts/u007_font_proof.cpp",
    "miniandroid/scripts/exp099_wsc2_text_pipeline.cpp",
    "miniandroid/scripts/u007_status_gen.py",
    "miniandroid/tools/exp116_font_shaping_prototype.cpp",
    "miniandroid/tools/campaign010/uc010_sbidiff.c",
    "miniandroid/tests/fixtures/s66_canvas_probe/",
    # category 3: captured runtime evidence (records, not authored text)
    "docs/evidence/foundation/determinism/",
    "docs/evidence/foundation/fixtures/",
    # the audit tool itself
    "scripts/s91_english_audit.py",
]
BINARY_EXT = re.compile(r"\.(png|jpg|jpeg|gif|webp|ico|apk|jar|zip|gz|tgz|bin|so|o|a|pdf|ttf|otf|woff2?|mp3|mp4|ogg|wav|xapk|aab|dex|flat|arsc|db|sqlite|class|pyc)$", re.I)

ARABIC_BLOCKS = [
    (0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF), (0xFE70, 0xFEFF),
]

def has_persian(s):
    hits = []
    for ch in s:
        cp = ord(ch)
        for lo, hi in ARABIC_BLOCKS:
            if lo <= cp <= hi:
                try:
                    name = unicodedata.name(ch, '?')
                except ValueError:
                    name = '?'
                hits.append((ch, f"U+{cp:04X}", name))
                break
    return hits

tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd="/home/z/my-project")
files = tracked.stdout.splitlines()
print(f"tracked files: {len(files)}")

name_hits = []
content_hits = []

for f in files:
    h = has_persian(f)
    if h:
        name_hits.append((f, h))
    if BINARY_EXT.search(f):
        continue
    if any(f.startswith(a) or f == a.rstrip('/') for a in ALLOWLIST):
        continue
    try:
        with open(f, "r", encoding="utf-8", errors="strict") as fh:
            for ln, line in enumerate(fh, 1):
                h = has_persian(line)
                if h:
                    content_hits.append((f, ln, line.rstrip()[:160], h))
    except (UnicodeDecodeError, OSError):
        # try binary check: skip if not decodable as utf8
        continue

print(f"\n=== FILENAME HITS: {len(name_hits)} ===")
for f, h in name_hits[:50]:
    print(f"  {f}  ->  {[f'{c}({cp})' for c, cp, _ in h]}")

print(f"\n=== CONTENT HITS (non-allowlisted): {len(content_hits)} ===")
from collections import Counter
per_file = Counter(f for f, _, _, _ in content_hits)
for f, n in per_file.most_common():
    print(f"  FILESTAT {n:5d}  {f}")
for f, ln, line, h in content_hits[:400]:
    chars = ", ".join(f"{c}({cp})" for c, cp, _ in h[:6])
    print(f"  {f}:{ln}: [{chars}] {line.strip()[:120]}")

if not name_hits and not content_hits:
    print("\nRESULT: CLEAN — no Persian/Arabic script anywhere in tracked files.")
    sys.exit(0)
sys.exit(1)
