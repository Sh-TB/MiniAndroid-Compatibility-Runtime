# RELEASE_NOTES_011_1 — UNIFIED_011_1_CANONICAL (§36)

**Date**: 2026-08-30 · **Tag**: `v0.11.1-unified-011-1` · **Parent**: v0.11-unified-011 (388fb45)

## What was recovered

All twelve campaigns (UNIFIED_000 → UNIFIED_011) were re-verified and, where
possible, **imported** — including the nine archives Campaign 011 had graded
`NOT AVAILABLE` / `conversation-level only`, found SHA-valid at
`/tmp/my-project` and fully processed (§ SEARCH→RECOVER→VERIFY→RECONCILE→IMPORT):

- **UNIFIED_005** — real audio stack (audio_engine + stb_vorbis + minimp3;
  33/33 in lineage) and real 3D tic-tac-toe (16/16) — recovered and vendored.
- **UNIFIED_006** — font-shaping and Telegram-Lottie prototypes — recovered.
- **UNIFIED_007** — resource-pipeline companion modules (text_shaper,
  view_renderer, real_layout, EXP-120/121/124 tools, build scripts) — recovered.
- **UNIFIED_008** — reduced audio + fonts modules, browser job server, audio
  fixtures/tests, 17 knowledge docs + the p1_mining open-source-mining
  dataset — recovered.
- **UNIFIED_009** — ARSC config matching (`res_config`) and the 16-doc
  campaign009 knowledge set — recovered; res_config now builds by default.
- **UNIFIED_010** — the four verified adoptions: **libpng PNG codec**,
  **PortableGL GLES glue**, **Yoga adapter**, **real stack traces (R14)**,
  the 12-fixture PNG test, the 31-row APK registry, and the campaign009/010
  knowledge sets — **source promoted into the default build** after a
  byte-identical regression reproduction.

## What was verified

- 9/9 recovered archives matched their recorded SHA-256 sidecars.
- Standalone UNIFIED_010 snapshot: clean build + 8-APK matrix, byte-identical
  to canonical behavior (gmdice 158,040 px; telegram 41,233 px; ssw 930,980 px).
- Merged canonical build: **zero behavioral delta** vs the 010 snapshot
  (same screenshot SHAs across all 8 APKs).
- Telegram v12 determinism **3/3** = `088ea640587ec0d2…` — pixel-identical to
  the `06fb40da…` lineage (PNG *file* hash changed by design: libpng's encoder
  replaces the custom one at identical pixel content — Campaign 010 precedent).
- Git forensics: 3 dangling commits + 3 superseded tag objects identified and
  anchored in `archive/011-*` branches; no history rewrite; no force-push.

## What changed (default build)

software_renderer.cpp: custom PNG decode+encode → libpng (−383 LoC, 100%
of the 7,036-PNG corpus incl. tRNS/Adam7/16-bit); dalvik_engine + shadows:
real `StackTraceElement[]` (ThreadShadow fall-through) while retaining the
UNIFIED_011 inflation guard; resources: `res_config` (ARSC config matching);
new `src/gles/` PortableGL glue; Makefile builds res_config. +38,349 lines
across 152 files in the import commit (knowledge + preserved modules included).

## What was rejected / not imported

All APK/AAB files (ZERO-APK policy), logs >1MB (external evidence cache),
archive README/status snapshots that would clobber canonical docs (§29
MASTER-vs-HISTORICAL), `test_media/` runtime media, SheenBidi (uncalibrated
differential; FriBidi stays), SwiftShader (research-only, memory blocker).

## What remains (honest)

Dooz/Compose blank (StringBuilder.append PC-advance livelock — next site
known), GLES20 dispatch hook + Yoga render-stage wiring open (bridges ready),
audio/text_shaper recovered but unwired, push PUSH_PENDING (no credentials —
owner runs `git push origin main && git push origin --tags`), GitHub
issues/PR metadata NOT AVAILABLE (API-limited).

## How to start

Open `START_HERE.md` → `README.md` → `CODER_HANDOFF_011_1.md` (evidence
commands, blockers, regression one-liner) → `status_011_1.json`.
Build: `cd miniandroid && make -j$(nproc)`. Test:
`python3 scripts/u011_test_matrix.py`. APKs: `scripts/download_test_apks.sh`.
