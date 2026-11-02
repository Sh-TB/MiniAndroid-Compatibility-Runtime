# BIGFILE PURGE MANIFEST — S153 (history slimming)

Generated: 2026-11-02 19:57 UTC · Method: `git filter-repo` (paths + globs + blob-ids) across ALL 1437 commits, 3 branches, 8 tags.

## Why
GitHub repo showed ~600 MB+. Root cause: raw screenshots (.ppm), downloaded toolchains (kotlinc/r8/android.jar), engine binary snapshots, extracted framework resources, APK/DEX artifacts, raw runtime traces (api/method/heap/view_tree JSON) and tmp/ scratch had accumulated in HISTORY even though HEAD had already been cleaned in earlier passes.

## What was removed (history-wide, raw blob bytes)

| category | blobs | raw MB |
|---|---:|---:|
| purged dir | 17470 | 1221.0 |
| trace/view_tree >=1MB | 129 | 256.3 |
| **TOTAL raw removed** | **17599** | **1477.3** |

Remaining reachable blob bytes (source/docs/ledgers, delta-friendly): 2.37 GB raw → pack after rewrite: **79 MiB** (was ~600 MB+).

## Removed by location (>= one entry)

| path | blobs | raw MB |
|---|---:|---:|
| miniandroid/build-win/ | 12709 | 327.1 |
| upstream/cont12_maven/ | 222 | 221.5 |
| tmp/c94_binaries/ | 2 | 190.4 |
| tmp/archidx.json
/ | 1 | 88.4 |
| tmp/index-v1.json
/ | 1 | 60.2 |
| tools/toolchain/ | 3 | 56.7 |
| miniandroid/run/ | 6 | 49.6 |
| evidence/s106_fresh/ | 30 | 42.3 |
| evidence/s107_games/ | 12 | 32.5 |
| evidence/s113_fullgui/ | 17 | 31.5 |
| tools/android-34/ | 1 | 25.1 |
| tmp/cont12_b1/ | 30 | 24.1 |
| tmp/cont12_oracle_build/ | 13 | 21.6 |
| evidence/s112_html5_generalization/ | 13 | 21.2 |
| miniandroid/framework_res/ | 1085 | 20.0 |
| evidence/s107_fresh/ | 15 | 18.5 |
| tools/r8/ | 1 | 15.9 |
| tmp/mykanji_extract/ | 16 | 14.4 |
| tmp/idx.jar
/ | 1 | 14.0 |
| tmp/cont32/ | 3 | 12.6 |
| evidence/s109_telegram/ | 5 | 10.2 |
| evidence/s114_bigfix/ | 6 | 8.9 |
| tmp/w7_compose_src/ | 727 | 8.1 |
| tmp/blid/ | 2 | 7.2 |
| miniandroid/download/ | 94 | 7.0 |
| tmp/bb_t6/ | 9 | 6.0 |
| tmp/bb_t5/ | 9 | 6.0 |
| tmp/bb_t7/ | 9 | 6.0 |
| tmp/bb_trace/ | 9 | 6.0 |
| tmp/bb_trace3/ | 9 | 6.0 |

## What was KEPT (untouched)

| area | blobs | raw MB |
|---|---:|---:|
| miniandroid | 6727 | 1126.0 |
| evidence | 3335 | 357.4 |
| worklog.md
 | 556 | 354.5 |
| docs | 3992 | 272.0 |
| canonical | 194 | 101.9 |
| root_registry.json
 | 229 | 91.3 |
| run | 390 | 40.5 |
| scripts | 2017 | 11.9 |
| forensic_data | 230 | 8.3 |
| upstream | 574 | 7.7 |
| gpg_f092_matrace | 5 | 7.0 |
| apk_build | 458 | 6.9 |
| fixtures | 444 | 4.7 |
| registry | 50 | 1.4 |

Kept: full engine source history (miniandroid/src/** incl. dalvik_engine.cpp), worklog.md (556 revisions), root_registry.json + canonical registries, ALL evidence ledger JSONs (S-series verdict books), curated small view_tree.json + PNG/GIF visual evidence, fixture fonts, dex_census/knowledge_graph analysis JSONs.

## Nothing is lost

- Full pre-rewrite history: `backup/ma_full_backup_s153.bundle` (576 MB, all refs) — restore: `git clone backup/ma_full_backup_s153.bundle restored`

- Working-tree tool artifacts (jars/aars/dexes/framework_res/test_apks/tmp) restored locally from `backup/wt_offenders.tar` and remain on disk, now untracked.

- Toolchains re-downloadable: kotlinc 2.1.20 (kotlinlang.org), r8.jar (r8.googlesource), android-34.jar (sdkmanager) — SHA-256s in evidence/s153_purge/purge_manifest.json.

- Issues, releases (8/8 published), pages — unaffected by history rewrite.

- Per-blob ledger: evidence/s153_purge/purge_manifest.json (path, sha16, bytes, category).
