# MASTER_TIMELINE_011_1 (§22)

Chronological chain: **EXP era → UNIFIED campaigns → commits → results**.
Provenance: canonical git history + verified archives (see
`CROSS_CAMPAIGN_RECOVERY_011_1.md` for grading). Branch lineages that never
reached GitHub are marked `(unpushed lineage)`.

## Phase I — GitHub lineage (canonical history, pushed to bbe0ce3)

| EXP | Result |
|---|---|
| EXP-022..029 | DEX parser, corpus mining, opcode/API frequency databases |
| EXP-030..036 | real Dalvik engine, object model, vtable dispatch, execution gating |
| EXP-037..043 | Telegram compatibility research, JNI inventory, native dependency map, loop detectors |
| EXP-046..059 | disassembly oracles, exception tests, replay validation, Androguard oracle |
| EXP-060..067 | image validator, render/view dumps, multidex regression, AXML parser tooling |
| EXP-068..077 | baselines, opcode audit, event semantics, auth sendCode callgraph, RLottie pre-work, bootstrap matrix |
| EXP-083..089 | repo forensics, source purge, generic runtime validation, multidex injection, handler queue, click automation |
| EXP-092..093 | bitmap font, ViewPager pre-load confound, stack-trace stub (later removed by R14) |
| EXP-096..098 (`7a2d278..bbe0ce3`, GitHub HEAD) | WebP+JPEG decoders, truncated-APK hang fix, RLottie wiring on SMS screen |

## Phase II — UNIFIED campaign era (2026-08-27..30)

| Campaign | Base → Head | Commits | Result |
|---|---|---|---|
| UNIFIED-CAMPAIGN (WS-C2..C5) | bbe0ce3 → f2e8ad9 | 86bd646 (UC-CM-001 type-aware stub defaults, closes F012), f2e8ad9 (knowledge wave) | v12.10.1 first-run 3/3 SHA 06fb40da; RTL typography POC; rlottie built |
| UNIFIED-ARCHIVE-000 | — | — | UNIFIED_000.zip (d4a7bd57…) |
| UNIFIED-KNOWLEDGE-001 | — | — | 15 consolidation docs (files 024–038) |
| UNIFIED-ARCHIVE-001 | — | — | UNIFIED_001.zip (e45e1035…) |
| UNIFIED_002 | f2e8ad9 → 8f0a85b | 7cc4254 (EXP-100 click/chain audit), 8f0a85b (EXP-101/102 tooling) | auth chain PROVEN (sendCode→sentCode controlled); 14-APK corpus ×2; RTL §14 6/6; Robolectric oracle run; UNIFIED_002.zip (6fb9a963…) |
| UNIFIED_003 / 004 `(unpushed lineage)` | 8f0a85b → … | EXP-103..110 era | knowledge archives (FILE_MANIFEST_003/004); session loss recorded at the time, archives since rebuilt |
| UNIFIED_005 `(unpushed lineage)` | 8f0a85b → d6b4020 | EXP-113/114 | **real audio (MP3/OGG, stb_vorbis+minimp3) 33/33; real 3D tic-tac-toe 16/16**; corpus re-run |
| UNIFIED_006 `(unpushed lineage)` | d6b4020 → … | EXP-116/117 | font shaping prototype; Telegram Lottie probe; TASKS_CAMPAIGN005_MASTER |
| UNIFIED_007 `(unpushed lineage)` | … → … | EXP-120/121/124 | real resource pipeline (ARSC→AXML→inflation); golden journey; text_shaper/view_renderer/real_layout; UNIFIED_007 + FINAL archives |
| UNIFIED_008 `(unpushed lineage, 4a2d39b base)` | … | EXP-131 + u008 series | open-source mining (119 candidates), audio/fonts reduced modules, job server, Dooz path, GLES investigation |
| UNIFIED_009 | 4a2d39b base | campaign009 set | 201 GitHub projects; **res_config ARSC config matching**; Dooz attach-chain evidence; 25-APK corpus; observability docs |
| UNIFIED_010 | 4a2d39b → f9190da-lineage | 8d4e25b (R1 libpng), 4e128c0 (R9/R10 PortableGL), f131606 (R3 Yoga), f9190da (R14 stack traces) | PNG 100% corpus (7,036), −383 LoC; GLES pipeline golden cube; Yoga differential 10/10; dooz livelock→9 real NPEs; 31-APK corpus; zero regressions (REGRESSION_010) |

## Phase III — canonical recovery era (this repo)

| Campaign | Commits | Result |
|---|---|---|
| UNIFIED_011 | 23900f8 (recover UNIFIED_007 pipeline + guard), 288ff6f, c061770 (master docs), f45505d (ppm drop), 937f043 (START_HERE), 388fb45 (tag anchor) | ZERO-APK hygiene, evidence policy, master doc set, tag v0.11-unified-011; archives 003–010 wrongly graded unavailable (corrected by 011.1) |
| **UNIFIED_011.1** | **3b862e5** (cross-campaign import) + docs commit | 12/12 campaigns recovered/verified; Campaign 010 source promoted to default build; Campaign 005–010 knowledge sets imported; dangling objects anchored; regression zero-delta; tag v0.11.1-unified-011-1 |

## Archive ledger

| Archive | Size (B) | SHA-256 (16) | Location |
|---|---|---|---|
| UNIFIED_000.zip | 372,241 | d4a7bd57fb142c95 | download/miniandroid_unified_campaign/ |
| UNIFIED_001.zip | 536,847 | e45e1035fda20820 | same |
| UNIFIED_002.zip | 690,262 | 6fb9a963131e702d | same |
| UNIFIED_003.zip | 954,460 | (FORENSICS_SUMMARY.json) | /tmp/my-project/download/... (recover) |
| UNIFIED_004.zip | 1,222,484 | (see forensics) | same |
| UNIFIED_005.zip | 800,451 | 60e94e029a032817 (index) | same |
| UNIFIED_006.zip | 4,657,333 | (see forensics) | same |
| UNIFIED_007.zip / 007_FINAL.zip | 11,060,369 / 94,771,893 | (see forensics) | same |
| UNIFIED_008_FINAL.zip | 7,595,036 | 4e2723e15f42ad32 | same |
| UNIFIED_009_FINAL.zip | 5,238,878 | 2c8653ef1291dbdc | same |
| UNIFIED_010_FINAL.zip | 3,085,682 | 698f7b0b681ee625 | same |
| UNIFIED_011_CANONICAL_HANDOFF.zip | 6,776,544 | abe216929a0955dd | download/UNIFIED_011/ |

Full hashes: `/home/z/my-project/u011_1_forensics/FORENSICS_SUMMARY.json`
(mirrored into the handoff package under `recovery/`).
