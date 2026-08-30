# REGRESSION_009 — every adoption re-verified (§35)

## 1. Golden baselines after the §6 config-matching adoption

| Target | Metric | Before | After | Verdict |
|---|---|---|---|---|
| GMDice | screenshot SHA-16 | `26fc4116e4ba65b4` | `26fc4116e4ba65b4` | **IDENTICAL** ✓ |
| GMDice | non-white px | 158,040 | 158,040 | ✓ |
| Telegram 12.10.1 | screenshot SHA-16 | `b9b06072ea17d7fd` (UNIFIED_002 baseline) | `b9b06072ea17d7fd` | **IDENTICAL** ✓ |
| Telegram | non-white px | 41,233 | 41,233 | ✓ |
| uNote | non-white px | 23,472 (EXP-101) | 23,472 | ✓ |
| bgclock | non-white px | 2,073,600 (EXP-101) | 2,073,600 | ✓ |
| simplestopwatch | exit code | 1 (known) | 1 | ✓ unchanged |
| dooz (flag OFF) | non-white px | 0 | 0 | ✓ unchanged |

## 2. Regression after the §10 attach-dispatch commit (flag OFF by default)

| Target | Metric | Verdict |
|---|---|---|
| GMDice | screenshot SHA-16 | `26fc4116e4ba65b4` **IDENTICAL** ✓ (re-verified after rebuild) |
| dooz | default run | unchanged (dispatch env-gated) |

The dispatch only executes when `MINIANDROID_DISPATCH_ATTACH` is set — by construction zero behavior change when unset, and the binary change was re-verified against the golden SHA.

## 3. Positive (non-regression) evidence produced

### §6 ARSC configuration matching (new capability, PROVEN)
Probe tool: `build/res_config_probe` (source `tests/tools/res_config_probe.cpp`).

Telegram 12.10.1 resources:
```
device en-US:  [default] MATCH → SELECTED;  de/uk/nl/ko/ar/es/it/ru/pt-rBR all REJECT ✓
device ru-RU:  [ru] MATCH "Прервать" → SELECTED ✓  (was impossible under old heuristic)
drawables:     ab_progress → [480dpi] selected on 480dpi device ✓
               _menu_stream_comments_off_24 → [anydpi-v24] beats density buckets (AOSP DENSITY_ANY rule) ✓
```
Old behavior (deleted): first-bucket-wins string heuristic → would select 160dpi for `ab_progress`.

### §10 Compose attach chain (new capability, structural PROOF)
dooz, `MINIANDROID_DISPATCH_ATTACH=1`:
```
[UC009-ATTACH] onAttachedToWindow dispatched view=27 ComposeView
[UC009-ATTACH] onAttachedToWindow dispatched view=63 AndroidComposeView
[EXP092-RENDER] ComposeView children=1  (was children=0)
```
317 log lines of real Compose-runtime interpretation inside the attach window (AndroidComposeView.onAttachedToWindow 227B, LayoutNode `node/i`,`node/e`, Snapshot observer, Recomposer `P/l`).

### §24 PortableGL GLES2 (open-source route PROVEN)
`run/exp_uc009_gles/pgl_gles2_test.c` (header-only, plain gcc, no SDL):
```
colored (non-black) pixels: 31104 / 76800
PGL GLES2 RESULT: SHADER TRIANGLE RASTERIZED
```

## 4. Evidence-terminology check (§34)

- No claim of "PASS" anywhere; per-criteria columns only.
- The 23,472-px fallback screen is never counted as app UI.
- §26–§28 browser/API stress: **NOT RUN** (server absent in recovered environment) — recorded, not simulated.
- §12 official compose-samples: **NOT RUN** (no Android SDK/gradle in env) — real Compose APKs (Droid-ify, NewPipe) profiled instead.

## 5. Known-good reproducibility for the next campaign

Commands (from repo/miniandroid):
```
make -j2
./build/miniandroid run -o /tmp/r1 download/corpus/gmdice.apk     # expect SHA16 26fc4116e4ba65b4
./build/miniandroid run -o /tmp/r2 download/exp038_telegram/Telegram.apk  # expect b9b06072ea17d7fd
MINIANDROID_DISPATCH_ATTACH=1 ./build/miniandroid run -o /tmp/r3 download/corpus/dooz.apk
  # expect: "[UC009-ATTACH] onAttachedToWindow dispatched view=27 ComposeView" + children=1
MINIANDROID_LOCALE=ru-RU ./build/res_config_probe download/exp038_telegram/Telegram.apk Abort
  # expect: => SELECTED: [ru]
```
