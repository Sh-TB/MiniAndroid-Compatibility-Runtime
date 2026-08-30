# MASTER_HANDOFF_011 — 3-minute onboarding for the next coder/agent

Generated 2026-08-30 (CAMPAIGN 011). If you read only one file: read this one.

---

## What this project is

**MiniAndroid** — a C++17 **real-APK compatibility runtime**: it opens a real
Android APK, parses ZIP + DEX + `resources.arsc` + binary XML, interprets the
real Dalvik bytecode, bridges framework APIs to a shadow object model, inflates
the APK's **real layouts**, renders frames to a software framebuffer, and
writes deterministic pixel/trace evidence (PNG + JSON). Acceptance = real APKs
running real journeys with byte-stable proof (Telegram v12: 3/3 identical
screenshot SHA).

## How to build

```bash
sudo apt install g++ make zlib1g-dev libwebp-dev libjpeg-dev \
                 libpng-dev libfreetype-dev libharfbuzz-dev libfribidi-dev
git clone https://github.com/Samsung/rlottie ../tools/rlottie   # only external static lib
( cd ../tools/rlottie && cmake -S . -B build -DBUILD_SHARED_LIBS=OFF && cmake --build build -j )
make            # inside miniandroid/ ; RLOTTIE_DIR defaults to ../tools/rlottie
```

Verified this session on g++ 14.2 (Debian) from a fresh clone.

## What is proven (evidence you can re-run)

| proof | how to reproduce | expected |
|---|---|---|
| Telegram v12 journey | `scripts/download_test_apks.sh --only Telegram,Telegram v12` then `python3 scripts/u011_test_matrix.py` | exit 0, `06fb40da…` BASELINE_MATCH, 41,233 px |
| Real layout inflation | matrix `gmdice` row | real UI "Push buttons to roll!", `6425c0f6…`, 158,040 px |
| Real controls | matrix `simplestopwatch` row | Start/Reset rendered, 930,980 px |
| Zero-regression guard | matrix `unote`/`headingcalc`(via corpus) | fallback `c200c521…` = historical baseline |
| Determinism | run telegram row 3× | identical SHA every run |

## What is blocked (don't rediscover — read first)

1. **Compose/Dooz & tictactoe blank renders** (`c035e9ba…`) — pre-existing,
   byte-identical on the old baseline; Kotlin Intrinsics/NPE analysis in
   `docs/` (UNIFIED_002 set). Not a regression of the new pipeline.
2. **`@string/` refs unresolved** in inflated layouts (headingcalc-class).
   Fix in `src/resources/layout_inflater.cpp`; the substantive-tree guard in
   `src/framework/android_shadows.cpp` (search `UNIFIED_011`) protects you meanwhile.
3. **Obfuscated resource names** (`res/0s.xml`) unsupported in ARSC→path mapping.
4. **GLES**: no backend; PortableGL/SwiftShader/ANGLE researched only.
5. **PNG decode is still the custom decoder** — libpng is linked but not wired
   (CAMPAIGN 010 R1 remains open; do NOT claim it done).
6. **Push pending** — 6 commits + tag await credentials
   (`git push origin main && git push origin --tags`).

## Where evidence is

- In-repo curated: `docs/evidence/u011/` (3 PNGs + `EVIDENCE_INDEX.md` +
  SHA256SUMS; provenance per §24/§25) and `docs/` (121 experiment docs).
- Generated per run: `run/<campaign>/` (screenshots, api_trace.json, reports;
  bulk kept out of Git by design — §26).
- External: APK cache (`MINIANDROID_APK_CACHE`) + full logs/backups live
  OUTSIDE the repository (ZERO-APK policy).

## Where code is

| domain | path |
|---|---|
| APK/ZIP/manifest | `src/apk/` |
| DEX + Dalvik interpreter | `src/dex/` |
| journey/render stages | `src/runtime/execution_engine.cpp` |
| **resource pipeline (new)** | `src/resources/arsc_parser.*`, `axml_parser.*`, `layout_inflater.*`, `resource_runtime.*` |
| renderer + image decoders | `src/renderer/software_renderer.cpp` |
| framework shadows (95+ classes) | `src/framework/android_shadows.cpp` |
| prefs/storage sandbox | `src/api/`, `src/storage/` |
| tests + diagnostics | `tests/`, `tests/tools/`, `scripts/u011_test_matrix.py` |

## How to continue

1. `make && python3 scripts/u011_test_matrix.py` — establish your baseline.
2. Pick the top item from `MASTER_PROJECT_STATE_011.md §11` (recommended:
   ARSC `@string/` resolution — highest value/effort ratio).
3. Keep the house rules: **zero APKs in repo**, evidence with provenance,
   byte-stable baselines, honest status labels
   (PROVEN/PARTIAL/BLOCKED/FAILED/UNTESTED — see `TEST_MATRIX.md`).
4. When you can push: `git push origin main && git push origin --tags`, then
   create the GitHub Release `UNIFIED_011_CANONICAL` from
   `RELEASE_NOTES_UNIFIED_011.md`.
