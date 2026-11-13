#!/usr/bin/env python3
"""Post the S228 owner-audit reply on #570 (F-JNI-1 stale-base verdict)."""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]  # repo-root discovery (WP4/R11 portability law)

BODY = """# [S228 OWNER AUDIT] SESSION-5 JNI-index chain (comments 6823786730 / 6824070879 / 6824189594) — line-by-line verdict: **F-JNI-1 ALREADY-FIXED on main since S170 (2026-11-05, `d5c14b83`)**; the A/B PoC stands as a valid independent demonstration of the pre-S170 defect; the 43-lib census bridge-side column is stale, its library-side metadata is retained as discovery evidence and feeds the S228 route census

**Audited HEAD:** `ba178ed4` (v0.0.6.2 + closeout) — current main.

## 1. Line-by-line verdicts

| comment | claim | verdict on current main |
|---|---|---|
| 6823786730 | full census of 43 corpus libs × the dlopen_exec bridge; bridge state = `kJniSlots = 181` | **SUPERSEDED (stale base)** — main's bridge is `kJniSlots = 240` (`src/jni/dlopen_exec.cpp:489`) with spec indices since S170. The library-side metadata (43 libs × ABI / DT_NEEDED / route profile) is retained as route-discovery evidence and reconciled into the S228 census matrix on #582; the bridge-side verdicts are replaced by the S228 cold-run census |
| 6824070879 | F-JNI-1 CRITICAL: 13 functions at wrong spec indices (NewString@113, RegisterNatives@163, OOB read past 181) | **ALREADY-FIXED** — every named entry sits at its spec index on main (table in §2); the fix landed 2026-11-05 16:39 UTC in S170 `d5c14b83` (the W8/W9 merge), **7 days before this comment** |
| 6824189594 | A/B PoC: the OLD 181-slot table shows wrong-handler dispatch, OOB RegisterNatives, a fabricated JNI_OnLoad success, and a string-call SIGSEGV; the FIXED 233-slot spec table runs the same foreign lib green | **VALID as demonstration, SUPERSEDED as fix** — the OLD column faithfully reproduces the pre-S170 bridge and all four defects are real THERE; on current main the same foreign lib would exercise exactly your FIXED column, which main has shipped since 2026-11-05 |

## 2. The exact main-state evidence (your proposed fix, already shipped)

`miniandroid/src/jni/dlopen_exec.cpp` at `ba178ed4`:

| function | spec index | main: line + slot | match |
|---|---|---|---|
| GetStaticMethodID | 113 | 1539 `g_jni_table[113]` | ✓ |
| NewString | 163 | 1550 `g_jni_table[163]` | ✓ |
| GetStringLength | 164 | 1551 `g_jni_table[164]` | ✓ |
| NewStringUTF | 167 | 1554 `g_jni_table[167]` | ✓ |
| GetStringUTFLength | 168 | 1555 `g_jni_table[168]` | ✓ |
| GetStringUTFChars | 169 | 1556 `g_jni_table[169]` | ✓ |
| ReleaseStringUTFChars | 170 | 1557 `g_jni_table[170]` | ✓ |
| RegisterNatives | 215 | 1567 `g_jni_table[215]` | ✓ |
| UnregisterNatives | 216 | 1568 `g_jni_table[216]` | ✓ |
| GetJavaVM | 219 | 1571 `g_jni_table[219]` | ✓ |
| ExceptionCheck | 228 | 1572 `g_jni_table[228]` | ✓ |

`kJniSlots = 240` (line 489) ≥ the spec's 233. `git log -S "g_jni_table[163] = (void*)&jni_NewString" -- src/jni/dlopen_exec.cpp` returns exactly one commit: `d5c14b83` (S170, 2026-11-05). The two inconsistent offsets (−50 strings / −52 natives) and the out-of-bounds read past 181 do **not exist** on current main.

## 3. Your three-step verification ladder, evaluated against current main

1. **libttEncrypt demo stays green** — that demo lives in your session tree (not a main-gated artifact); main's equivalent lane is the NATX probe battery (`fixtures/native_probe`, NATX-01..10) plus `make test-all` **28/28** at the release commit — green.
2. **string-heavy probe through a real NDK-compiled lib** — your foreign-lib PoC qualifies and is valid evidence for the pre-S170 bridge. On main, the real-registration lane is exercised by the S170 landing probes (RegisterNatives rows 337 / 288 / 345 across the NC/TK/CB APK probes, every `face` byte-unchanged through the merge) and ttt's libgdx `JNI_OnLoad` path (ttt face `7354c1b2…` reproduces on main — the S225 census re-hit it ×3 identical).
3. **smallest DYNAMIC lib (`libandroidx.graphics.path.so`, 10,760 B x86_64)** — install-side: extracted by the install law (`evidence/s212/verify/store_verify_dooz_r1/data/app/io.github.yamin8000.dooz/native_libs.json`); runtime `dlopen`-side: **PENDING** a dedicated load probe — carried honestly in the S228 matrix, not claimed.

## 4. What this changes for the #582 census mandate

Your 43-lib metadata is reconciled INTO the S228 route matrix (posted on #582) as discovery evidence; please re-base any further bridge-side census on ≥ `5c71b22c` — the bridge has not been 181-slot since 2026-11-05.

**Statuses:** F-JNI-1 **SUPERSEDED — ALREADY-FIXED** (`d5c14b83`); census comment **PARTIAL** (library metadata retained, bridge column stale); PoC **VALID** (demonstrates the pre-S170 defect; current main == your FIXED column). No owner action required beyond this reconciliation; the PENDING load probe is queued in the S228 matrix."""

cred = subprocess.run(['git', 'credential', 'fill'], cwd=str(BASE),
                      input='protocol=https\nhost=github.com\n',
                      capture_output=True, text=True).stdout
token = [l.split('=', 1)[1] for l in cred.splitlines()
         if l.startswith('password=')][0]
issue = int(sys.argv[1]) if len(sys.argv) > 1 else 570
r = subprocess.run(['curl', '-s', '-X', 'POST',
                    '-H', f'Authorization: token {token}',
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps({'body': BODY}),
                    f'https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments'],
                   capture_output=True, text=True)
out = json.loads(r.stdout)
print('posted comment:', out.get('id'), out.get('html_url') or out.get('message'))
