# CONT-34 — GATE A Virtual-Path Frontier: F-NEW-293
# Root-Cause, Fix, Probe, and the Death of the DataStore Prefix Multiplication

Wave: CONT-34 (user directive: ادامه). Predecessor: evidence/cont33
(FORMAT_LOCALE_FRONTIER.md, §12 pinned this wave's targets). Environment
recovered first (container reset: local clone was stale at the CONT-10
lineage again; binary and tmp/ gone). This wave: (1) rebuilt the binary
byte-exact and re-supplied both APKs SHA-exact, (2) reproduced the
composeStopwatch PARTIAL SUCCESS baseline ×3 with the mangled DataStore
faces, (3) built the contract probe BEFORE any engine change and recorded
the PRE face ×3(+1), (4) decoded the prefix-multiplication mechanism to ONE
semantic root — the GATE A reverse mapping comparing an absolute host path
against a RELATIVE prefix table, (5) fixed it with a two-line anchor
canonicalization, (6) probe POST ×3 + target ×3 + full zero-drift
regression.

## 0. RESUMABLE STATE BLOCK

| item | value |
|---|---|
| HEAD at wave start | 8081a64e (CONT-33, pulled from origin/main after the reset) |
| pre-wave binary | 859557953a3b144c (rebuilt byte-exact == the CONT-33 record) |
| post-F-NEW-293 binary | **702813ff2d5d8be8** |
| target APK | tmp/cont34_apks/composeStopwatch_1009011.apk (sha256 dbf937ebbe7c0b3d… — re-supplied from F-Droid, SHA-exact) |
| control APK | tmp/cont34_apks/simplecalc_8.apk (sha256 68da25fd9fdf54b4… — re-supplied, SHA-exact) |
| probe | fixtures/fnew293_probe (real aapt2/ECJ/D8 via scripts/w4_build_probes.sh; package com.probe.f293, activity "Main" per the hygiene law) |
| regression | run/cont34/regression + scripts/cont34_regression.sh |

## 1. ENVIRONMENT RECOVERY + BASELINE

- Local clone found stale at the CONT-10 lineage (e99c2fbd tmp-snapshot on
  top); `git fetch` → remote main 8081a64e; fast-forward (61 commits;
  local HEAD verified ancestor, no divergence, snapshot branch kept as
  backup). `timeout 570 make -j1 BUILD_DIR=build` → **859557953a3b144c
  byte-exact** == the CONT-33 record (source-faithful rebuild).
- composeStopwatch v1.9.1 vc1009011 re-supplied from the F-Droid repo,
  SHA-exact `dbf937ebbe7c0b3d…`; Simple Calculator vc8 re-supplied,
  SHA-exact `68da25fd9fdf54b4…`.
- Baseline ×3 on the rebuilt binary: rc=1, screenshot **9afb2bd2606f303e**
  ×3 (== the CONT-33 PARTIAL SUCCESS anchor byte-identical), DataStore
  `preference.preferences_pb` traffic ×12/run, **mangled `runtime/data`
  spellings ×10/run** (the CONT-33 §9 face reproduces exactly).

## 2. THE FACE (pre-fix, binary 859557953a3b144c)

```
[R347-FILE-CTOR] path="runtime/data/data/data/<pkg>/files/datastore/
                 preference.preferences_pb" caller=Lu7;.a          ← leak
[R347-FILE] getAbsoluteFile path="runtime/data/data/data/<pkg>/runtime/
            data/runtime/data/…"                                    ← ×2
[SYNTH-EXC] STREAM-OPEN (deferred): FileNotFoundException
            (runtime/data/data/data/<pkg>/runtime/data/…/…preferences_pb
            (open failed: ENOENT))                                  ← ×N
```

One logical file (the DataStore preferences_pb), three different app-visible
spellings depending on WHICH engine surface answered — and a multiplied
physical anchor that can never be the file the dir getter offered.

## 3. DECODE — THREE ANCHORS FOR ONE FILE

| consumer | law | spelled |
|---|---|---|
| dir getters (get_or_create_dir_file, getFileStreamPath) | `logical_android_path(path)` → silent no-op → **raw host spelling** | `runtime/data/data/data/<pkg>/files` (relative!) |
| `resolve_android_path` (streams/open) | RELATIVE_APP_DATA → anchored under **`package_data_dir()`** | `<pkg>/runtime/data/data/data/<pkg>/files/…` (×2) |
| `getAbsolutePath`/`getAbsoluteFile` (R-NEW-390) | relative → anchored under **`app_data_root()`** | `runtime/data/runtime/data/data/data/<pkg>/files/…` (×2, ×3 via joins) |

ROOT: `logical_android_path` (data_root.cpp) built its prefix table from
`g_app_data_root` — which stays the RELATIVE literal `"runtime/data"` when
neither `--data-root` nor `MINIANDROID_DATA_ROOT` is set (main.cpp:914
applies the override only when present) — while the host side is
`fs::absolute(host_path)`. `h.rfind("runtime/data/data/data/", 0)` can
never match an absolute path, so EVERY prefix row silently failed and the
GATE A promise ("an application NEVER sees a host path") was voided for
the entire dir-getter family on every default-root run.

## 4. THE FIX — ONE SEMANTIC ROOT, TWO LINES

`logical_android_path` (src/storage/data_root.cpp): canonicalize the ANCHOR
exactly like the host side — `fs::absolute(g_app_data_root)` before
building the prefix table. Both sides of the comparison now resolve against
the SAME process anchor (the CWD the relative root already resolves against
at every use — create_directories included). No name dispatch, no per-app
branches; covers the whole dir-getter family through the two GATE A call
sites. The back-compat relative default is preserved (tool paths keep
resolving `runtime/data` under their CWD); only the APP-VISIBLE spelling
changes — to the AOSP logical one.

## 5. PROBE fnew293 — CONTRACT BEFORE THE ENGINE CHANGE

Rows: DIR-FILES-LOGICAL / DIR-CACHE-LOGICAL (the app-visible namespace
law), FILE-JOIN-LOGICAL (the EXACT DataStore join shape), RT-CREATE-EXISTS
(delete-then-create — deterministic across runs), RT-WRITE-READ (write →
FRESH-File read-back, same bytes = the same-file law), DS-DIR-MKDIRS
(datastore/ dir law across two independently minted Files), NO-HOST-LEAK
(explicit guard). Hygiene: package com.probe.f293, activity "Main".

| run | binary | result |
|---|---|---|
| PRE ×3 + r4 | 859557953a3b144c | SUMMARY **FAIL** (3 pass, 4 fail): DIR-FILES/DIR-CACHE got the DOUBLE prefix `runtime/data/data/data/<pkg>/runtime/data/data/data/<pkg>/files`; FILE-JOIN got the single host prefix; NO-HOST-LEAK leak=true; the round-trip rows PASS (both sides anchor identically — the mangled location is at least SELF-consistent, which is why apps only saw ENOENT churn, not corruption) |
| POST ×3 | 702813ff2d5d8be8 | SUMMARY **PASS 7/0** — `getFilesDir().getAbsolutePath()` = `/data/data/com.probe.f293/files`, join = `/data/data/…/files/datastore/preference.preferences_pb`, round-trip paths all logical, leak=false |

Physical verification: the probe file lands at
`runtime/data/data/data/com.probe.f293/files/probe293.txt` (the SINGLE
canonical backing — the same tree the dir getter create_directories'd),
while the PRE-era double-prefixed leftover stays behind unread.

## 6. TARGET — composeStopwatch ×3 on 702813ff2d5d8be8

| run | rc | screenshot | mangled spellings | verdict |
|---|---|---|---|---|
| csw_post_r1..r3 | 1 | **9afb2bd2606f303e** ×3 | **0 app-visible** (10→0; the 2 remaining log lines are the host-side `[DATA-ROOT]` startup banner and the FIRST-RUN DataStore read ENOENT — faithful: the file does not exist until the app writes it) | PARTIAL SUCCESS retained, **zero render drift** |

- The R347 chain now spells `/data/data/<pkg>/files/datastore/…` at every
  step (ctor, getName, getAbsoluteFile, getCanonicalFile) — the prefix
  multiplication is DEAD at the source.
- Honest residuals: the ENOENT exception MESSAGE embeds the host backing
  path (the synthetic STREAM-OPEN law builds the message from the physical
  path — an app-visible string via getMessage(); recorded PENDING, no
  failing consumer today); the Lh4; ops=0 face, the empty dialog body, the
  f141-null-recv at Lk6;.<init> pc=409 and the F084 budget-halt churn are
  unchanged standing fronts (CONT-33 §8).

## 7. REGRESSION GATE — ZERO DRIFT at 702813ff2d5d8be8

scripts/cont34_regression.sh (anchors / probes / control):

| gate | result |
|---|---|
| anchors ×3 ×8 apps | dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622 — **24/24 BYTE-IDENTICAL MATCH** |
| probe battery | fcol 140/0, f259 49/0, f259g 84/7 (known-honest F259-L row), f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0 (rebuilt fresh after the reset-wiped APK), fnew289 28/0, fnew252 56/0, fnew290 56/0, fnew291 56/0, fnew292 70/0 — **== CONT-28..33 records EXACTLY** |
| new probe | fnew293 **56/0** (7 rows × the run's row echoes) |
| Track B control | Simple Calculator ×3 rc=0 `7960bce447ac6d8f` — FULL SUCCESS retained |

## 8. STATUS WORDS

- F-NEW-293: **ROOT_CAUSED_FIXED / TESTED / OBSERVED** (probe PRE/POST ×3
  both directions + target mangled-face elimination ×3 + 24/24 anchors +
  full battery == records).
- The stream-open ENOENT message spelling: **OBSERVED / PENDING** (same
  family, separate construction site, no failing consumer — not
  speculatively patched).
- Registry: 601 → **602** (F-NEW-293; dedup-checked).

## 9. NEXT RESUMABLE CHECKPOINT

1. composeStopwatch standing fronts: f141-null-recv at Lk6;.<init> pc=409;
   the Lh4; ops=0 face; the empty dialog body (items=0).
2. The STREAM-OPEN exception-message spelling face (§6 residual) — its own
   probe row first (getMessage() must answer the logical spelling).
3. Standing: F-NEW-288 (TextUnit value-class spin, Track A P0) and Simple
   Calculator input-pump (Track B).
