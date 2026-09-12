# CODER_HANDOFF_011_1 (§28)

You are reading the entry point for continuing MiniAndroid after
UNIFIED_011.1. Read `START_HERE.md` → `README.md` → this file →
`status_011_1.json` → `docs/CURRENT_TRUTH_011_1.md`.

## 1. Top proven capabilities (with the evidence to re-run)

| Capability | Proof command / evidence |
|---|---|
| Real APK execution (DEX interpreter) | `make && ./build/miniandroid run <apk> -o out -v` |
| GMDice REAL UI (inflated resources) | matrix row gmdice: 158,040 px, views=10 strings=2 |
| Telegram v12 deterministic render | `scripts/u011_test_matrix.py`; 3/3 × `088ea640…` |
| Telegram auth chain (controlled boundary) | EXP-100 records; `docs` EXP-100 click/chain audit |
| SimpleStopwatch REAL controls | matrix row ssw: 930,980 px |
| PNG 100% corpus decode (libpng) | `tests/exp088_a4_png_decoder_test.cpp` 12/12 |
| WebP/JPEG/Lottie decode+render | EXP-097/098 lineage (linked decoders) |
| Persian/RTL typography (POC) | WS-C2 proof 6/6, proof.png c15673b6 |
| Touch automation + audit | EXP-088/089 + EXP-100 (env-gated) |
| Corpus breadth | 31-row registry; 12+ exit-0 honest statuses |
| Observability | evidence indexes + SHA256SUMS pattern |

## 2. Top unresolved blockers (attack in this order)

1. **Dooz/Compose**: `LM1/i;.f StringBuilder.append(null)` PC-advance livelock
   (R14 already removed the previous livelock site; next site located).
2. **GLES dispatch**: wire `GLES20` static dispatch into the engine's
   framework-static chain — bridge `src/gles/gles20_bridge.*` is ready.
3. **Yoga render-stage**: switch engine layout stage to Yoga bounds —
   adapter scaffold + differential harness ready (`run/uc010_yoga_layout.cpp`).
4. **Audio wiring**: `src/audio/audio_engine.*` + `third_party/audio`
   (stb_vorbis/minimp3) recovered; or adopt miniaudio (verified B-class).
5. **text_shaper wiring**: recovered `src/fonts/text_shaper` into runtime text path.
6. **ARSC gaps**: unresolved `@string` refs; obfuscated res names (unote/headingcalc).
7. **Push**: `git push origin main && git push origin --tags` (owner credentials).

## 3. Recovered historical implementations (where + status)

- **In default build**: libpng codec (software_renderer), res_config (009),
  R14 stack traces, src/gles glue, 12-fixture PNG test, 31-row registry.
- **Preserved, not wired**: `src/audio/`, `src/fonts/`, `src/games/tictactoe3d.h`,
  `third_party/audio/`, `src/renderer/view_renderer.*`,
  `src/resources/real_layout.*`, `tools/exp113…124`, `tools/u007_job_server.cpp`,
  `tests/test_audio.cpp` + `tests/fixtures/audio/`.
- Statuses and reasons per item: `docs/CROSS_CAMPAIGN_RECOVERY_011_1.md` §4.

## 4. Open-source components actually used (≠ researched)

libpng 1.6.48 · rlottie 43075538 · FriBidi 1.0.16 · HarfBuzz 10.2.0 ·
FreeType 2.13.3 · libwebp · libjpeg-turbo · PortableGL 7cf39dc (glue;
`portablegl.h` is an external include) · vendored: nlohmann_json, stb_image
2.30, stb_vorbis, minimp3. Full provenance:
`docs/CURRENT_TRUTH_011_1.md` §"open-source".

## 5. Important failed approaches (do NOT redo)

Custom PNG codec (tRNS bug) · EXP-093 stack-trace stub (livelock) ·
GLSL-source execution on PortableGL (by design impossible — translator or
llvmpipe instead) · SheenBidi differential (uncalibrated; FriBidi proven) ·
SwiftShader backend (memory blocker) · "uNote UI at 23,472 px" (it was the
shared default screen) · availability claims without a filesystem-wide search
(the 011 lesson — the "missing" archives were in /tmp/my-project).

## 6. Regression commands (run after ANY change)

```bash
cd miniandroid && make -j$(nproc)
python3 scripts/u011_test_matrix.py --binary build/miniandroid \
        --out run/regression
# pass criteria: gmdice 158,040 px; ssw 930,980 px; telegram nonwhite 41,233
# and determinism (run telegram 3x → identical SHA); no new nonzero exits
```

Baselines and per-APK verdicts: `status_011_1.json` → `.regression`.

## 7. Evidence locations

- In-repo: `docs/evidence/u011/` (011), `docs/evidence/u011_1/` (011.1, with
  SHA256SUMS_U011_1.txt), campaign knowledge `docs/knowledge/campaign005…010/`
  (incl. campaign010/evidence bench files).
- External (never commit): `/home/z/my-project/apk_cache` (APKs),
  `/home/z/my-project/u011_1_forensics/` (recovered archives, extractions,
  diffs, FORENSICS_SUMMARY.json), `/home/z/my-project/download/UNIFIED_011_1_backup/`
  (git bundle + patches), `/tmp/my-project/download/corpus/` (raw corpus).

## 8. Build environment notes

- System deps: libpng-dev 1.6.48, zlib, libwebp, libjpeg, freetype, harfbuzz,
  fribidi, g++ ≥ 12. rlottie: static lib at `/home/z/my-project/tools/rlottie`
  (override `RLOTTIE_DIR`).
- Optional GLES harness: fetch PortableGL —
  `git clone https://github.com/rswinkle/PortableGL` (verify 7cf39dc) and add
  its dir to the include path; Yoga adapter: `facebook/yoga @ bd8fe0d`.
- APKs are NEVER in the repo: `scripts/download_test_apks.{sh,py}` fetch into
  an external cache and verify SHA256 against `tests/corpus/apks.json`.
