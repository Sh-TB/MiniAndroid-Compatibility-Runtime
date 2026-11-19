# W21 APK VALIDATION REPORT — Phase 2 (original unmodified APKs, from the legitimate release source)

Binary: `build/miniandroid` (W21 tree). Screenshots sha256-16; all run dirs under
`miniandroid/evidence/w21/`. NO APK was rebuilt from source; every APK below is the
original artifact fetched from F-Droid (repo / archive — the original release source),
byte-identity verified against the independent coder's own receipts where they exist.

## 1. SolitaireCG (net.sourceforge.solitaire_cg) — GAME-090

| Item | Value |
|---|---|
| APK | `net.sourceforge.solitaire_cg_3041.apk` — the coder's exact pinned version |
| sha256 | `d4afb74d28680712d771181a696d5fec42cc13e5c55f0da546151f6a8c4244c6` |
| Source | https://f-droid.org/repo/net.sourceforge.solitaire_cg_3041.apk |
| Byte-identity | equals the coder's PLAY-wave receipt sha16 `d4afb74d28680712` ✓ |
| Also fetched | `_4010.apk` (latest 4.1) sha `39411dd82b0f2b274ef803f48d501fc102ab10bcb19bb7894433d17454765825` |

Runs (data-root `evidence/w21/solcg_3041_data`, dirs `evidence/w21/solcg_3041_runs/`):

| Run | Gesture | rc | Status | screenshot sha16 |
|---|---|---|---|---|
| r1 | none (first launch) | 0 | — | `56db5af701c9b6e4` (by-design splash face, WS2.02) |
| r2 | `--tap 540,960` | 0 | **SUCCESS ✅** | **`1787d115143ad5f3`** |
| r3 | `--tap 540,960` | 0 | SUCCESS | `1787d115143ad5f3` |
| r4 | `--tap 540,960` | 0 | SUCCESS | `1787d115143ad5f3` |

**Findings**
- **The board face is BYTE-IDENTICAL to the independent coder's own S237 receipt**
  (`1787d115143ad5f3`, "first launch + tap 540,960 → board; 5× identical") — ×3
  deterministic here.
- **The `createBitmap(w=0,h=-1)` IllegalArgumentException does NOT reproduce** — zero
  `IllegalArgumentException` lines in every run (the 66 grep hits are all
  `createBitmap`-related REC-MISS/F-NEW-495 lines, none an IAE). The PLAY-wave crash the
  coder recorded (GAME-090 BLOCKED) is not reachable on this tree+APK: the W20-K
  bitmap-dims fallback (AOSP BitmapDrawable law) is integrated in the ui_graphics domain.
- Honest residual: `DrawMaster.DrawPortraitCards` still issues 33 REC-MISS
  `Bitmap.createBitmap` calls per run (an unimplemented overload arm) — they are absorbed
  without a crash and do not affect the verified board face; recorded as a follow-up
  arm, not a playability blocker.
- NOTE (audit): the W20-K evidence dirs `k_apk/sol_r1..r3` are MISNAMED — they contain
  de.tcrass.minos runs (report + sha prove it), so W20-K's "SolitaireCG re-run" had never
  actually executed. This Phase 2 run is the FIRST real SolitaireCG re-verification.

## 2. Frozen Bubble (org.jfedor.frozenbubble)

| Item | Value |
|---|---|
| APKs | `org.jfedor.frozenbubble_11.apk` (coder's pinned) sha `fababf48eafa5e45d084c7e0ba6ec8a11ebb5617a713bc12d9a0ca95933bedef` — equals the coder's receipt `fababf48eafa5e45` ✓; `org.jfedor.frozenbubble_54.apk` (latest) sha `bf291a12e88c84e559bd4f0faf99163a6a5b55da995df69ef10f888c6bba77e4` |
| Source | https://f-droid.org/archive/org.jfedor.frozenbubble_{11,54}.apk |

Runs (dirs `evidence/w21/frozenbubble_11_coder_*`, `frozenbubble_11_fixed_r{1,2,3}`,
`frozenbubble_54_*`):

| Phase | v11 ×3 | v54 |
|---|---|---|
| Before W21 field-law fix | sha `238371330a9b17b7` ×3 det.; 1 false `IllegalAccessException` per run | `42f494e998c0f0a3` |
| After W21 field-law fix | sha `aaecbbdf4ed996cb` ×3 det.; **0 exceptions** | `42f494e998c0f0a3` (unchanged face, 0 IAE) |

**Findings**
- **W20-K's "Options public fields registered" claim VERIFIED LIVE**:
  `[R500-REFLECT] Class(BitmapFactory$Options).getField("inScaled") declared=… type=Z →
  Field obj#25` — the reflection lookup SUCCEEDS (the pre-registration NoSuchFieldException
  NSFE is gone).
- New precise defect found by the live run and **fixed in W21**: the framework-field
  fallback hardcoded `public static final` flags for every framework class, so `Field.set`
  on `Options.inScaled` threw a FALSE `IllegalAccessException` (AOSP
  `BitmapFactory.java` Options fields are public non-final INSTANCE decode options).
  Fix in BOTH getField copies (`dalvik_engine.cpp` + `dalvik_bridge_domain_app_runtime.cpp`):
  `BitmapFactory$Options` → public non-static non-final. After the fix the decode honors
  the app's `inScaled=false` write (v11 face changed `238371…`→`aaecbb…` — the scaling
  option now takes effect; deterministic ×3).
- Render: real GL content — **37,988 distinct colors** (exactly the coder's own census
  figure), nonwhite 1.0. Final status PARTIAL solely from the F-NEW-200 stub-census
  honesty bound (975 STUBBED of 99,501), **zero uncaught exceptions**.
- Gameplay interaction (tap/aim/shoot) remains unvalidated (single-gesture CLI; not
  claimed).

## 3. a2048 (com.uberspot.a2048) — WS4/WS4B vehicle

| APK | sha256 | source | outcome |
|---|---|---|---|
| `_23` | e7bf6cb62cda6830… (full hash in `apk_src/`) | https://f-droid.org/archive/com.uberspot.a2048_23.apk | **SUCCESS rc=0, zero exceptions** — the WS4B reproduction vehicle; now board-interactive (see `W21_PLAYABILITY_2048_REPORT.md`) |
| `_25` (newest archive) | `7c66ccdf3d1fb9fd18d2a088f34bde4069c1107e4fc4b787b18012d7021df17f` | https://f-droid.org/archive/com.uberspot.a2048_25.apk | **CRASHES at MainActivity.onCreate**: 3 uncaught NPEs (`XmlPullParserFactory.newPullParser` on null @ `ResourceChangeLogProvider.getChangeLog` pc=4, `AlertDialog.show` on null @ onCreate pc=88, `WebView.loadUrl` on null @ onResume pc=30) → DEFAULT_BACKGROUND_ONLY face `b5a7a35d5fe0564b` (same face as the minos/authsrng crash faces). Version-specific pre-WS4B blocker — recorded, NOT hidden; the changelog-library path (`de.cketti.changelog.*`) needs XmlPullParserFactory + dialog construction support before this version can boot. |

## 4. Corpus regression after all W21 runtime changes

- Full baseline: **15/15 APKs byte-identical screenshots vs the W20-K2 TSV**
  (per-phase comparison; `W21_RUNTIME_BASELINE.md`).
- Post-Options-law spot check (3 representative APKs, fresh runs): puzzle
  `6375a3a3813af176`, ugalay `87fe26766fc48d06`, minos `b5a7a35d5fe0564b` — all IDENTICAL
  to the baseline faces.
- test-all after the s235 harness fix: **48/48 PASS** (`evidence/w21/w21_testall_final.log`,
  runner-measured wall 288.4 s, rc=0).

## 5. Phase 2 verdicts

| App | Verdict |
|---|---|
| SolitaireCG | **ACCEPTED** — coder's crash absent, board face = coder's receipt hash ×3, SUCCESS |
| Frozen Bubble | **ACCEPTED** (render + field law) — registration verified live, false IAE fixed, ×3 deterministic; gameplay interaction still unvalidated |
| a2048 | **WS4B CLOSED** (board-interactive); v25 boot blocker recorded |
