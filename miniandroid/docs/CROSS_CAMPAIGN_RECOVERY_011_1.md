# CROSS_CAMPAIGN_RECOVERY_011_1

**Campaign**: UNIFIED_011.1 — COMPLETE CROSS-CAMPAIGN RECOVERY / IMPORT EVERYTHING
**Date**: 2026-08-30 · **Canonical repo**: MiniAndroid-Compatibility-Runtime
**Recovery basis**: direct archives + git forensics + build/test verification (provenance-graded)

## 1. The recovery story in one paragraph

Campaign 011 graded UNIFIED_003/004/006 as `NOT AVAILABLE` and
UNIFIED_005/008/009/010 as `conversation-level only (HISTORICAL/UNVERIFIED)`,
and its marker re-check concluded `libpng not wired (R1 open)`. UNIFIED_011.1
§2 mandated searching *every possible source*. The search found the complete
missing archive set at `/tmp/my-project/download/miniandroid_unified_campaign/`
(a preserved copy of the older workspace), including UNIFIED_003…010_FINAL and
the Campaign 005–010 scripts, mining datasets and knowledge files. All nine
archives were SHA256-verified against their recorded sidecar hashes (9/9
match), extracted, diffed against the canonical tree, classified and
selectively imported. Every UNIFIED_011 "not available / not wired" grading
that depended on archive absence is hereby **corrected** — the historical
grading stays in this file for the audit trail (§6: success AND failure both
matter; history is never rewritten).

## 2. Source inventory (§1–§2)

| Source | Location | Status |
|---|---|---|
| UNIFIED_000.zip / 001 / 002 | `download/miniandroid_unified_campaign/` | SHA verified |
| UNIFIED_003.zip / 004 | same | SHA verified (knowledge archives) |
| UNIFIED_005.zip / 006 / 007 / 007_FINAL | same | SHA verified |
| UNIFIED_008_FINAL / 009_FINAL / 010_FINAL | same | SHA verified |
| Campaign 005/006 knowledge files | same (+ `TASKS_*`, `EXP-111/115/117-120`) | imported |
| Campaign 008 mining dataset | `/tmp/my-project/scripts/p1_mining/` (11 files) | imported |
| Campaign 003–010 build scripts | `/tmp/my-project/scripts/` (build_unified_003..008, uc010_*, u008_*, exp10x/11x/13x) | preserved in forensics; key ones imported |
| Full git bundle (Campaign 011) | `download/UNIFIED_011_backup/miniandroid_unified_011_full.bundle` | verified |
| Patch series 0001–0010 (Campaign 011) | `download/UNIFIED_011_backup/patches/` | verified (already in history) |
| `UNIFIED_011_CANONICAL_HANDOFF.zip` | `download/UNIFIED_011/` | restore-tested in `/tmp/u011_zipcheck` |
| Old workspace copy | `/tmp/my-project/` (apk_cache 18 APKs, apktool_out Telegram 5-DEX decompile, worklog) | external evidence cache — **never enters repo/ZIP** |
| tool-results read caches (10 files) | `/tmp/my-project/tool-results/`, `/home/z/my-project/tool-results/` | historical read snapshots; superseded by archives |
| rlottie clone + static lib | `/home/z/my-project/tools/rlottie` (Samsung 43075538) | build dependency (external, by design) |

`/tmp` recovery candidates: `u011_zipcheck` (Campaign 011 restore test — superseded),
`boot-timeline.log` (session noise), `my-project` (the decisive recovery source above).

## 3. Git forensics (§3) — dangling objects, all accounted for

| Object | What it is | Verdict |
|---|---|---|
| `d872616` | stash WIP 2026-08-27 on 8f0a85b — only `runtime/…/default.xml` churn | noise; anchored in `archive/011-stash-runtime-noise` |
| `edac6a6` | stash "On main: UNIFIED_007 resource pipeline (recovered work)" — Campaign 011's A/B stash | superseded by canonical commit `23900f8`; anchored in `archive/011-stash-unified007` |
| `313ed5c` | "§45 final consistency pass" commit, reset away | superseded by `388fb45` (same content re-anchored to final HEAD); anchored in `archive/011-superseded-consistency` |
| 3 dangling tags | superseded iterations of annotated tag `v0.11-unified-011` (→ f45505d, 937f043, 313ed5c) | final ref → `388fb45`; iterations anchored via the archive branches above |

Archive branches created so bundles retain these objects (a `--all` bundle
otherwise drops dangling objects). **No force-push, no history rewrite** (§21).

## 4. Cross-campaign map (§12)

Legend — Source/Evidence: `A`=archive on disk, `C`=canonical history,
`T`=/tmp workspace, `—`=not found. Imported: `BUILD` = in default build,
`PRESERVE` = vendored for future wiring, `DOCS` = knowledge only.

| Campaign | Original claim | Source found | Commit found | Implementation found | Evidence found | Current state | Imported | Reason |
|---|---|---|---|---|---|---|---|---|
| UNIFIED_000 | consolidation of WS-C2..C5; numbered-archive system | A (ZIP 000) | C (86bd646, f2e8ad9) | yes (docs+UC-CM-001) | A (3 PNG + metrics) | VERIFIED | DOCS | already canonical; re-verified |
| UNIFIED_001 | knowledge consolidation (15 docs, 024–038) | A (ZIP 001) | C (same commits) | docs only | A | VERIFIED | DOCS | already canonical |
| UNIFIED_002 | EXP-100 click/chain audit, EXP-101 corpus, EXP-101c RTL proof, EXP-102 oracles | A (ZIP 002) | C (7cc4254, 8f0a85b) | yes | A (06fb40da 3/3, corpus JSON) | VERIFIED | BUILD | already canonical |
| UNIFIED_003 | campaign continuation (knowledge snapshot) | A (ZIP 003) — 011 said NOT AVAILABLE | (lineage commit, unpushed) | docs only | A | RECOVERED | DOCS | found in /tmp/my-project |
| UNIFIED_004 | same (FILE_MANIFEST_004) | A (ZIP 004) — 011 said NOT AVAILABLE | (lineage, unpushed) | docs only | A | RECOVERED | DOCS | found in /tmp/my-project |
| UNIFIED_005 | real audio (MP3/OGG) + real 3D tic-tac-toe + corpus re-run | A (ZIP 005) — 011 said conversation-only | d6b4020 lineage (unpushed) | `src/audio`, `src/games/tictactoe3d.h`, `third_party/audio`, exp113/114 | A (33/33 audio, 16/16 3D, WAV artifacts) | RECOVERED | PRESERVE | modules vendored; not wired into default build (matches 010-reduced tree) |
| UNIFIED_006 | font shaping prototype + Telegram Lottie probe | A (ZIP 006) — 011 said NOT AVAILABLE | lineage (unpushed) | exp116, exp117 | A (42MB log excluded by policy) | RECOVERED | PRESERVE | prototypes imported to tools/ |
| UNIFIED_007 | real resource pipeline (ARSC→AXML→inflation) + golden journey | A (ZIP 007/007_FINAL) | C (23900f8 = recovered work) + d6b4020→…→lineage | yes — pipeline already canonical; exp120/121/124, text_shaper, view_renderer, real_layout new | A (gmdice 6425c0f6, ssw ef334f7c) | VERIFIED | BUILD+PRESERVE | pipeline was canonical; companions now imported |
| UNIFIED_008 | open-source mining (119 candidates), audio/fonts modules, Dooz path, GLES investigation | A (008_FINAL) — 011 said conversation-only | lineage (unpushed) | `src/audio`(reduced), `src/fonts/text_shaper`, `u007_job_server`, fixtures | A (knowledge set + regression) | RECOVERED | PRESERVE+DOCS | modules + full knowledge set imported |
| UNIFIED_009 | 201 GitHub projects, ARSC config matching, dooz attach chain, 25-APK corpus, observability | A (009_FINAL, src tar.gz) — 011 said conversation-only | lineage 4a2d39b base (unpushed) | `res_config.cpp/.h` + probe | A (campaign009 16 docs, APK matrices) | RECOVERED | BUILD+DOCS | res_config in default build; knowledge imported |
| UNIFIED_010 | libpng R1, PortableGL R9/R10, Yoga R3, stack traces R14, 31-APK corpus | A (010_FINAL) — 011 re-check wrongly said "not wired" | 8d4e25b, 4e128c0, f131606, f9190da (on 4a2d39b, unpushed) | **yes — all four, verified by build+tests in 011.1** | A (12/12 PNG fixtures, cube bench, yoga differential, REGRESSION_010) | VERIFIED→CANONICAL | BUILD | source promoted into default build (commit 3b862e5) |
| UNIFIED_011 | canonical recovery, ZERO-APK hygiene, master docs, tag | C (this repo) | bbe0ce3→388fb45 | yes (guard, docs, scripts) | docs/evidence/u011 | VERIFIED | BUILD | canonical base of 011.1 |

Totals: **12/12 campaigns recovered or verified**; archives 9/9 hash-verified;
0 implemented-features lost; 0 claims accepted without source+build+test.

## 5. Correction chains (§6) — historical claim → later correction → current truth

1. **libpng**: `010: ADOPTED (8d4e25b)` → `011 re-check: "libpng not wired (R1 open)"` → **`011.1: ADOPTED verified`** — software_renderer.cpp uses `png.h` decode+encode; custom codec absent; builds; 12/12 fixture test imported; 011's re-check failed because its marker scan pointed at non-existent `…/UNIFIED_010_FINAL/miniandroid/src` path (the 010 tree root *is* the miniandroid root). Lesson recorded: negative claims require a positive path check.
2. **UNIFIED_005/008/009/010 availability**: `011: conversation-level only / HISTORICAL` → **`011.1: RECOVERED from /tmp/my-project`** (9/9 SHA-verified archives).
3. **SMS milestone**: `000: v12 SMS screen OBSERVED, auth NOT PROVEN` → `002: full auth chain PROVEN (controlled boundary: sendCode → mocked sentCode)` → current: chain stands on v12, pixel-identical.
4. **Persian/RTL**: `000: POC only` → `002: §14 6/6 proof with codepoints+bidi+glyphs` → current: POC standing, in-runtime text_shaper module recovered (not wired).
5. **Dooz**: `002: TIMEOUT→exit 0, attribution open` → `008: DOOZ_PATH_008 attach chain` → `010: R14 unblocks Kotlin Intrinsics; 9 real NPEs; livelock moved to StringBuilder.append PC-advance` → current: BLOCKED with precise blocker (improvement from FAILED/livelock).
6. **Audio**: `005: PROVEN in lineage (33/33)` → `009/010: reduced out of tree` → **`011.1: modules recovered + vendored; not wired` → PARTIAL**.
7. **uNote 23,472-px shot**: `002: believed uNote UI` → `002 REVISED: shared default screen (10 apps)` → current: unote = default screen (obfuscated res/0s.xml paths), guard/reduced-tree agree.

## 6. Feature timelines (§13) — where multiple campaigns touched one feature

- **ARSC**: 007 parser/ARSC→AXML→inflation (gmdice/ssw) → 009 `res_config` config matching → 010 tree carries both → 011.1: parser + res_config in default build.
- **PNG**: custom decoder (≤EXP-098) → 008 spec-compat fixes (CRC/tRNS comments) → 010 libpng replaces decode+encode (7,036/7,036 corpus; 12/12 fixtures) → 011.1 default.
- **Font**: bitmap font (EXP-092) → WS-C2 typography POC (FriBidi→HarfBuzz→FreeType) → 006 shaping prototype → 008 `src/fonts/text_shaper` module → 010 keeps FriBidi (SheenBidi differential rejected: base-direction calibration) → 011.1: system libs wired, text_shaper recovered.
- **Audio**: 005 audio_engine + stb_vorbis/minimp3 (33/33) → 008 reduction (2 files) + fixtures/test → 009/010 removed from tree → 011.1 recovered+vendored (adoption-ready; miniaudio verified as B-class candidate).
- **3D/GLES**: 005 tictactoe3d (real perspective+minimax, 16/16) → 008 GLES_INVESTIGATION → 010 PortableGL backend (`src/gles` glue, golden cube 1,668 fps @320×240 / 27.5 fps @1080×1920; GLSL strings NOT executable — recorded honestly) → 011.1: bridge vendored in tree; dispatch hook into engine = open blocker.
- **Telegram**: EXP-042..098 lineage → v12.10.1 first-run (3/3 SHA) → 002 auth chain PROVEN → 010 pixdata b9b06072 stable across all adoptions → 011.1 pixel metrics identical (41,233 px), PNG file hash changed by design (libpng encoder).
- **Layout**: inflater fallback → 007 inflater pipeline → 010 Yoga adapter (10/10 nodes <8px, 35–39× faster) → 011.1: adapter experiment preserved; engine render stage not switched (tracked follow-up).
- **Touch**: EXP-088/089 runtime automation → EXP-100 click/chain audit → current: env-gated audit in build.
- **Corpus**: 002: 14 F-Droid APKs → 009: 25 → 010: 31 (registry `tests/corpus/apks.json`) → 011: ZERO-APK external cache + download scripts → 011.1: 31-row registry canonical.
- **Observability**: 002 EXP-100 per-click evidence → 009 observability docs → 011 evidence index + SHA256SUMS pattern → 011.1: `docs/evidence/u011_1/` added.

## 7. Conflict resolution (§18)

| Conflict | Resolution | Evidence priority applied |
|---|---|---|
| 011 "libpng not wired" vs 010 source | source wins; 011 grading marked as scan-path error | source at verified commit + build |
| Makefile: 010 `rm -rf run/` vs 011 "never delete run/" | 011 clean-target kept; only res_config line taken from 010 | later safety fix |
| android_shadows: 010 R14 vs 011 guard | merged: R14 fall-through + 011 inflation guard (both verified) | direct code merge + tests |
| telegram PNG hash 06fb40da vs 088ea640 | 088ea640 = new baseline; pixel-identical (41,233 px); encoder change by design (010 precedent) | execution evidence + pixel metric |
| u011 guard vs 010 reduced tree on unote/headingcalc | both fall back to default screen — outcomes identical; guard retained | test matrix |
| multiple README/status variants across archives | canonical 011 layer kept authoritative; archive copies preserved under docs/knowledge/campaign0XX/ | MASTER = current truth, HISTORICAL = original (§29) |

## 8. Post-import regression (§19) — merged canonical binary

| APK | exit | non-white px | screenshot SHA-256 (16) | verdict |
|---|---|---|---|---|
| gmdice | 0 | 158,040 | 472c1d3c0ee12330 | REAL UI — matches all baselines |
| telegram_v12 | 0 | 41,233 | 088ea640587ec0d2 | pixel-identical; libpng encoder by design; determinism 3/3 |
| microtimer | 0 | 23,472 | eb16ab5c68fa9b6c | default screen (pre-existing) |
| stopwatch | 1 | 23,472 | eb16ab5c68fa9b6c | pre-existing truncated APK |
| simplestopwatch | 0 | 930,980 | d495e3cb2ccf6c11 | REAL UI — matches |
| tictactoe | 0 | 0 | 31ddd4d5b8e6d18e | pre-existing blank |
| unote | 0 | 23,472 | eb16ab5c68fa9b6c | safe fallback (guard + reduced tree agree) |
| dooz | 0 | 0 | 31ddd4d5b8e6d18e | blank pre-existing; engine progresses (see CURRENT_TRUTH) |

Byte-identical to the standalone UNIFIED_010 snapshot run (same SHAs) — the
merge introduced zero behavioral delta on the default build.

## 9. What was deliberately NOT imported (§20, §25, §26)

- 15 APKs inside UNIFIED_007_FINAL + 73MB telegram corpus in `/tmp/my-project/download/corpus` — stay external (`apk_cache`), ZERO-APK enforced.
- `EVIDENCE/telegram/telegram_stderr_trace.log` (49.7MB), `err_v12.log` (49.6MB), `freeotpplus_timeout.log` (42.6MB), all run logs >1MB — external evidence cache only.
- Archive README/status/SHA256SUMS snapshots that would clobber canonical 011 docs (§29: MASTER vs HISTORICAL).
- `test_media/` runtime media (fixtures already cover audio tests).
- Campaign scripts that duplicate canonical tooling (build_unified_003..006 zips builders) — kept in forensics cache, listed in MASTER_TIMELINE.

## 10. Provenance statement

Everything in this file is derived from: on-disk archives with matching
recorded SHA-256, the canonical git history, a verified clean build of the
merged tree, and the regression matrix reproduced twice (010 snapshot +
merged canonical). Items that could NOT be re-verified remain graded in
`CURRENT_TRUTH_011_1.md` exactly as `UNVERIFIED`/`HISTORICAL` — nothing was
invented (§39 SEARCH→RECOVER→VERIFY→RECONCILE→IMPORT, else UNAVAILABLE).
