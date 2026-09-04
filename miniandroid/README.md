# MiniAndroid

**Real Android APK compatibility runtime** — a C++17 runtime that parses real
APK files, interprets real Dalvik bytecode, resolves real resources
(`resources.arsc` + binary XML), and renders the result to a framebuffer with
pixel-evidence output.

[![C++17](https://img.shields.io/badge/C%2B%2B-17-blue)](https://isocpp.org)
[![status](https://img.shields.io/badge/status-research%20runtime-orange)]()

---

## Current state (UNIFIED_011.1 canonical, 2026-08-30)

- **HEAD:** tag `v0.11.1-unified-011-1` (local, ahead of `origin/main` — push pending)
- **Latest remote (`origin/main`):** `bbe0ce3`
- **Canonical baseline proof:** Telegram v12.10.1 full journey renders
  deterministically **3/3 runs** (`088ea640…`; pixel-identical to the
  `06fb40da…` lineage — PNG file hash changed by design: libpng's encoder
  replaced the custom one, Campaign 010 R1).
- **New in 011.1:** complete cross-campaign recovery — all nine archives
  Campaign 011 had graded unavailable were found SHA-valid and processed;
  Campaign 010's verified source (libpng codec, GLES glue, ARSC config
  matching, real stack traces) is now the default build; Campaign 005–010
  knowledge sets and historical modules (audio, fonts, 3D game, codecs,
  job server) are recovered in-tree. See `MASTER_RECONCILIATION_011_1.md`.

## Proven capabilities (evidence-backed)

| Capability | Evidence |
|---|---|
| Real APK parse (ZIP+DEX+ARSC+AXML) | every run; corpus 14/15 exit 0 |
| Dalvik interpreter on real bytecode | 12,544 classes loaded (Telegram v12) |
| Telegram v12 deterministic journey incl. click chain | 3/3 identical SHA `06fb40da…` |
| SMS auth chain (controlled boundary: mocked `TL_auth_sentCode`) | EXP-100 trace, UNIFIED_002 |
| **Real layout inflation** (ARSC → AXML → ViewShadow) — NEW | GMDice real UI `6425c0f6…`, 158,040 px |
| **Real rendered controls — NEW | Simple Stopwatch Start/Reset, 930,980 px |
| **PNG 100% corpus decode (libpng)** — 011.1 | 7,036/7,036 real APK PNGs; 12/12 PIL-oracle fixtures; tRNS/Adam7/16-bit |
| **GLES2 pipeline via PortableGL (glue)** — 011.1 | golden cube 1,668 fps @320×240 / 27.5 fps @1080×1920 (dispatch hook open) |
| **Real stack traces → Kotlin Intrinsics progress** — 011.1 | R14: 9 real NPEs on dooz attach (was livelock) |
| **Recovered audio / 3D / codecs modules** — 011.1 | audio_engine 33/33 lineage; tictactoe3d 16/16 lineage; stb_vorbis/minimp3 vendored |
| Persian/RTL text shaping POC (FriBidi→HarfBuzz→FreeType) | EXP-101 §14 proof, 6/6 |
| Lottie animation (Samsung rlottie) on SMS screen | EXP-098/CM-027 |
| Zero-regression guard policy | headingcalc falls back byte-identical to baseline |

## Current blockers

| Blocker | Root cause | Status |
|---|---|---|
| Dooz / Compose apps render blank | Compose runtime expectations unmet; Kotlin Intrinsics NPEs analyzed in UNIFIED_002 | BLOCKED |
| `@string/` refs unresolved inside layouts | ARSC string-ref resolution in inflater not implemented yet | PARTIAL (guard protects) |
| Obfuscated resource names (`res/0s.xml`) | ARSC name→path mapping incomplete | PARTIAL (safe fallback) |
| Real GLES | no GPU backend; PortableGL/ANSwiftShader candidates researched, not integrated | RESEARCH |
| Telegram real network / real SMS | network + telephony stacks out of scope of current boundary | BY DESIGN |
| stopwatch APK | truncated/corrupt zip (androguard concurs) | FAILED (bad APK) |

## Quick start

```bash
# 1. system deps (Debian/Ubuntu names)
sudo apt install g++ make zlib1g-dev libwebp-dev libjpeg-dev \
                 libpng-dev libfreetype-dev libharfbuzz-dev libfribidi-dev

# 2. rlottie (only external static lib; path is overridable)
git clone https://github.com/Samsung/rlottie ../tools/rlottie
cd ../tools/rlottie && cmake -S . -B build -DBUILD_SHARED_LIBS=OFF && cmake --build build -j

# 3. build
make                      # RLOTTIE_DIR=../tools/rlottie is the default
./build/miniandroid --help
```

## Build

```bash
make          # executable: build/miniandroid
make clean    # only removes build/ (never touches tracked evidence in run/)
```

## Test

```bash
# canonical regression matrix (gmdice, telegram v12, 6 more corpus apps)
python3 scripts/u011_test_matrix.py --apk-dir /path/to/apk_cache
# expected: telegram_v12 BASELINE_MATCH (06fb40da...), gmdice 6425c0f6... real UI
```

## Real APK testing (ZERO-APK policy)

This repository contains **no APK files** and never will. Test APKs are
described in `tests/corpus/apks.json` (name, version, SHA256, URL) and fetched
into an **external** cache directory:

```bash
scripts/download_test_apks.sh                 # default cache: ../../../apk_cache
MINIANDROID_APK_CACHE=~/apk_cache scripts/download_test_apks.sh --only gmdice
```

The runner reports `APK FOUND / MISSING / SHA MATCH / MISMATCH` for every APK.

## Open-source components

rlottie (MIT), libwebp, libjpeg-turbo, libpng, zlib, FreeType, HarfBuzz,
FriBidi, nlohmann/json (vendored). Details, versions and integration status:
[`OPEN_SOURCE_MASTER.md`](OPEN_SOURCE_MASTER.md) ·
policy: [`DO_NOT_REINVENT.md`](DO_NOT_REINVENT.md)

## Latest release

`UNIFIED_011_CANONICAL` — see
[`RELEASE_NOTES_UNIFIED_011.md`](RELEASE_NOTES_UNIFIED_011.md),
[`MASTER_PROJECT_STATE_011.md`](MASTER_PROJECT_STATE_011.md) (state) and
[`MASTER_HANDOFF_011.md`](MASTER_HANDOFF_011.md) (3-minute onboarding).
Full history & knowledge: [`MASTER_CHANGELOG_KNOWLEDGE_011.md`](MASTER_CHANGELOG_KNOWLEDGE_011.md).

## New here?

Read in this order: **README → MASTER_HANDOFF_011 → MASTER_PROJECT_STATE_011**,
then build, run the test matrix, and continue from the blockers table.
