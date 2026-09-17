# S51 — Historical Bloat Report (PHASE 9)

Date: 2026-09-17 · Method: `git rev-list --objects <ref>` + `git cat-file --batch-check`
threshold = 1 MiB per blob · Raw inventory: `docs/forensics/S51_HISTORICAL_BLOB_INVENTORY.txt`
Pre-purge snapshot: tree `8b74cb093e06f624cae45c9205dd43bb05570a34`, HEAD `15f25d04` (S49 phase-2).
Backup: `backup-s51/pre-purge-main-tags.bundle` (487,858,487 bytes, SHA256 in HISTORY_PURGE_PLAN.md).

## Per-ref totals (uncompressed blob bytes reachable from each ref)

| Ref | commits | blobs total | blobs >1 MiB | big-bytes |
|---|---|---|---|---|
| main (pre-purge) | 279 | 3762 = 1128.1 MiB | **127** | **991.0 MiB** |
| archive/origin-main-ad95d928 | 394 | 18224 = 1430.7 MiB | 178 | 972.3 MiB |
| archive/local-main-12cf043f | 227 | 2464 = 195.7 MiB | 51 | 81.0 MiB |
| archive/local-main-167c27fb | 91 | 1513 = 99.9 MiB | 8 | 59.3 MiB |
| archive/local-main-d358a0c9-stale | 174 | 2182 = 165.3 MiB | 15 | 76.1 MiB |
| v0.0.6-Leghorn (tag) | 272 | 3743 = 1126.4 MiB | 126 | 989.6 MiB |
| v0.0.1..v0.0.5 tags | — | subsets of main chain | — | — |

GitHub-reported repo size at audit time: 519,916 KB (~508 MiB compressed packs).

## Category classification (main history, 127 big blobs)

| Category | Count | ~Size | Examples (paths) | Verdict |
|---|---|---|---|---|
| Raw stderr run logs | 56 | ~900 MiB | `miniandroid/run/*_stderr.txt` (sttt_runN 29.8 MB, s26_* 17.2 MB, m3c_* 15.1 MB, s23_* 14.9 MB) | STRIP — giant raw logs; knowledge already distilled into run/*/report.md + registry |
| Forensic dumps (S39-era gpg_*) | 26 | ~35 MiB | `gpg_f092..f104/api_trace.json`, `screenshot.ppm`, `classes.dex` | STRIP — raw dumps; conclusions preserved in ledger + registry |
| Runtime binary in git | 1 | 9.39 MiB | `miniandroid/core` | STRIP — build artifact, reproducible via make |
| Engine source history | ~35 | ~40 MiB | `miniandroid/src/dex/dalvik_engine.cpp` historical versions (1.0–1.5 MiB each) | KEEP — legitimate source-code history |
| Evidence (current tree) | 4 | ~10.5 MiB | `docs/evidence/campaign3_chessclock_real_screenshot/screenshot.ppm`, `docs/evidence/campaign014/*/api_trace.json` ×3 | KEEP — canonical curated evidence (candidates for future compaction, not part of history purge) |
| Upstream jars (current tree) | 2 | ~2 MiB | `upstream/s44/protobuf.jar`, `upstream/s43/ui-android-1.11.4-sources.jar` | KEEP — documented fetched-source evidence |
| Toolchain jars | 3 | 44 MiB | `tools/android-34.jar` 25.1, `tools/d8/r8.jar` 15.9, `tools/ecj/ecj.jar` 3.0 | Archive-branches only; gone when archives are decommissioned (toolchain now bootstrapped via `scripts/build/bootstrap_toolchain.sh`) |
| LLVM/Windows toolchain + APK dumps | 8+ | ~440 MiB | `miniandroid/build-win/work/llvm-mingw.tar.xz` 80.0, `libLLVM.so.23.1` 78.1, `libclang-cpp.so.23.1` 52.9, `hb.tgz` 34.6, `miniandroid/download/exp038_telegram/Telegram.apk` 78.9, `fdroid_index_v2.json` 53.3, `miniandroid/reports/telegram_call_graph.json` 62.5, `miniandroid/build_asan/miniandroid_asan` 28.6 | Archive-only; gone with archive decommission. LLVM dependency: build-time only, reproducible by download — never a repo blob (S51 PHASE 5 verdict) |

## Security-relevant history findings

- Pickaxe over credential-signature families (fine-grained PAT prefix, classic PAT
  prefix) across ALL refs: only security-scanner pattern definitions
  (S49 `check_secrets.sh`, `deep_secret_scan.py`, `SECURITY_AUDIT.md`) and old tooling commits.
- One truncated fine-grained-PAT prefix fragment (22-char user prefix + literal `...`,
  unusable as a credential, verified truncated at commit time) was added in eae90166 and
  redacted in a6958b46. Both commits are reachable ONLY from `archive/origin-main-ad95d928`.
  Archive decommission removes the fragment from all refs.
- Full new-token probe (unique substring pickaxe over all refs + working-tree grep): ZERO hits.
- `scripts/security/check_secrets.sh --tree`: PASS at audit time.

## Resolution (executed under explicit owner authorization "remove all old pushes")

1. main history: strip the 83 exact junk paths (~940 MiB) via git-filter-repo; KEEP-set
   verified collision-free against current tracked files (`strip ∩ tracked = ∅`).
2. tags v0.0.1..v0.0.6-Leghorn: rewritten onto the purged chain (release provenance preserved,
   bloat unreachable).
3. archive/* branches (4): decommissioned locally and on origin — they are the "old pushes"
   holding the LLVM/APK/toolchain era.
4. Post-purge invariant: HEAD tree hash MUST equal the tree at purge time
   `89dc0b144127deb7ad2b241eaf41d332a96ea414` (tree of S51 prep commit 61f1b5e7;
   the S49-head tree was `8b74cb093e06f624cae45c9205dd43bb05570a34` before the prep
   commit added the forensic docs). VERIFIED: post-purge tree == 89dc0b14, zero
   content regression, confirmed inside a fresh clone of the pushed remote.

Known caveat: after force-push, GitHub may retain now-unreachable objects server-side until
its internal GC runs; no ref will reach them. Repo-size display may lag until that GC.
