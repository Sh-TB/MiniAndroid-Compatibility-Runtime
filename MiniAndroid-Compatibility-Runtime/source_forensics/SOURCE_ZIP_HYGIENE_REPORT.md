# SOURCE ZIP HYGIENE REPORT — FINAL CANONICAL DISTRIBUTION ARTIFACT
Date: 2026-09-03 · Artifact audited: `MiniAndroid_CANONICAL_MASTER_RECONCILED_f714420.zip`
(157,354,279 B, SHA256 11b2c482d73d…; A-04; extract-verified byte-exact vs canonical HEAD tree).

## 1. Forbidden/non-source artifact scan (full entry list, 1,042 files + .git)

| Forbidden class | Count | Notes |
|---|---:|---|
| .apk / .aab | **0** | zero-APK policy holds; test APKs live in EXTERNAL cache via scripts/download_test_apks.py |
| .ppm / raw screenshots | **0** | |
| .so / .jar / .class | **0** | |
| node_modules / .gradle / gradle caches | **0** | |
| emulator images / huge binaries | **0** | |
| credentials/secrets | **0** | (no .env/key/token files in tree) |
| duplicate archives / nested ZIPs | **0** | |

## 2. Size profile (top entries — all legitimate)

| Bytes | Entry | Class |
|---:|---|---|
| 153,567,168 | repo/.git/objects/pack/*.pack | **complete non-shallow .git (362 commits)** — REQUIRED by spec §15/§29 |
| 1,944,660 / 1,944,620 | docs/campaign014_evidence/droidify/{,click/}api_trace.json | committed campaign-014 evidence (knowledge) |
| 1,159,277 / 1,128,599 / 583,342 | docs/campaign014_evidence/{dooz,openlauncher,bgclock…}/… | committed evidence |
| 919,975 | third_party/nlohmann/json.hpp | vendored dependency (build-required) |
| 745,882 | src/dex/dalvik_engine.cpp | the interpreter itself |
| 721,579 | docs/EXP083_run_inventory.csv | historical knowledge doc |
| 467,068 / 428,895 / 376,158 | docs/research/raw/*.json | AOSP/bytecode reference research |
| 283,010 / 192,790 | third_party/stb (stb_image.h, stb_vorbis.c) | vendored |
| 250,746 | worklog.md | multi-agent work log (provenance) |
| 176,478 | tests/fixtures/audio/sine_2s.wav | test fixture |

Extension census (top): md 343 · json 181 · (dirs/none) 170 · py 148 · png 107 (golden/fixture
screenshots, all < 100 KB policy) · cpp 98 · h 51 · dex 29 (**test fixtures** — required by §20/§22
semantic tests) · txt 26 · sh 11 · csv 3 · xml 3 · kts 3 · java 2 · c 2.

## 3. Retention check (spec §15 MUST-retain list)

| Must retain | Present? |
|---|---|
| complete .git (non-shallow, fsck-clean) | YES — pack verified; clone test: 362 commits, non-shallow, fsck CLEAN |
| source | YES — 98 cpp + 51 h + build system |
| tests | YES — fixtures + 3 discriminating semantic suites + tools |
| essential fixtures | YES — incl. 29 .dex test fixtures, goldens, audio fixture |
| essential documentation / knowledge | YES — KNOWLEDGE_LEDGER.csv, KNOWLEDGE_RECONCILIATION.md, PASS3_* docs, MASTER_PROJECT_KNOWLEDGE, NOT_DONE, VERIFIED_TESTS, campaign014_evidence |
| provenance files | YES — worklog.md, SHA256SUMS, HANDOFF records |
| required scripts/configuration | YES — scripts/, Makefile, .gitignore, .agent |

## 4. Hygiene of OTHER archives (context; spec §15 applies only to the final canonical ZIP)

* A-10 carries 5 robolectric `target/*` build artifacts + 2 runtime-prefs files **inside git
  history** (unreachable stashes) — never propagated to canonical; recorded SRC-007.
* A-06/A-01/… carry 101/34 untracked runtime logs in their worktrees (SRC-017/SRC-018) — not in
  canonical.
* No historical archive was modified or cleaned (rule: hygiene applies only to the final
  distribution artifact).

## 5. Verdict

```text
FINAL ZIP HYGIENE: PASS
  forbidden artifacts: 0 · must-retain coverage: complete · oversized offenders: none
  (largest non-.git entry = 1.9 MB committed evidence JSON)
```
