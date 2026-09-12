# EXP-067 — Forensic Baseline

Captured at commit `6ea5430` (HEAD of EXP-066).

## Baseline metrics (EXP-066 state, BEFORE EXP-067 work)

| Metric | Value |
|---|---|
| Git commit | `6ea5430` |
| APK SHA256 | `193ad551e2cbb745387f26370369f9cd0cf0353ecbc318398ada087ac2bf945e` |
| APK size | 82,680,854 bytes |
| DEX files | 5 |
| Runtime binary SHA256 | `e5131978...` |
| ViewNode count | 1385 |
| Text-bearing ViewNodes | 49 |
| Hint-bearing ViewNodes | 0 |
| `login_ui.png` SHA256 | `ad36fa85c3aaf4a65d79e0d434587518d74884aaab7dfc037c431307831442df` |
| PNG dimensions | 1080 × 1920 |
| OCR match rate | 1.0 (3 of 3 strings) |
| OCR strings detected | `Please confirm your country code...`, `Phone number`, `Country` |
| Stub count in dalvik_engine.cpp | 34 |
| Multi-DEX audit | 0 remaining UNSAFE occurrences |

## Resource inventory (from `resource_values.json`)

| Type | Count |
|---|---|
| string | 11,263 |
| drawable | 1,965 |
| id | 481 |
| color | 165 |
| dimen | 179 |
| raw | 423 |
| mipmap | 33 |
| anim | 54 |
| xml | 10 |
| integer | 18 |
| interpolator | 12 |
| animator | 6 |
| bool | 4 |
| array | 0 |
| attr | 0 |
| style | 0 |
| layout | 95 |

## Known gaps at baseline (carried from EXP-066)

- No real drawable decoding — ImageView placeholders are gray rectangles
- No real color resolution — `Resources.getColor(int)` returns default black
- No real dimension resolution — `Resources.getDimension(int)` not implemented
- No AXML parser — cannot inflate layouts from XML
- No generic LayoutInflater — `setContentView(R.layout.foo)` doesn't work
- No real measure/layout engine — renderer uses heuristic positioning
- No view inheritance tracking — anonymous subclasses recognized by name pattern only
- No input system — can't dispatch text/click to EditText
- No click listener dispatch — `dispatchClick` doesn't execute the callback
- No exception engine — DEX try/catch handlers not implemented
- No reflection layer — `Class.forName`/`getMethod` not implemented
- No SQLite — only SharedPreferences
- No JNI/loadLibrary — native methods all stubbed
- No Java networking — `Socket`/`HttpURLConnection` not implemented

## Status

`CHECKPOINT_L_LOGIN_UI = PROVEN` (from EXP-066). EXP-067 aims to reach `CHECKPOINT_M` (real Login UI with phone EditText + Next button + synthetic interaction).
