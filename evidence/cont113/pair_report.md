# CONT-113 — #366 First-Divergence Pair Report (CONT-110 P0, items 01–05/07/08)

**Binary:** `9f0fd0f4b9faa016` (fresh deterministic rebuild at HEAD `1e205d9a` + F-NEW-461)
**Anchor set:** present (`miniandroid/build/anchor_libs/` — rebuilt by `make anchors`, F-NEW-459)
**Matrix:** 4 working controls + 5 white targets per #366 §1 · harness `cont81_corpus_runner.py`
**Raw rows:** `run/c113/matrix_ctrl/result.json`, `run/c113/matrix_white/result.json`, `run/c113/matrix_white2/result.json`

## 01 — Baseline identity (item 01)

| target | package | APK sha16 | verdict_v2 | face sha16 (stable) | first_missing_stage |
|---|---|---|---|---|---|
| opencalc (control) | com.darkempire78.opencalculator | 2642613868a8a80f | REAL_APP_CONTENT | d5f3c7b5e9936ae6 | — |
| unote (control) | app.varlorg.unote | be91103f0e7db443 | REAL_APP_CONTENT | 90a67cc1ddda57b7 | — |
| microtimer (control) | dubrowgn.microtimer | 79c6f730f64886e7 | REAL_APP_CONTENT | bbd350b6c14fbd52 | — |
| chess (control) | jwtc.android.chess | 3245b9ec35f6c1df | REAL_APP_CONTENT | a0319686d56ff5c0 | — |
| stack.tower3d (white) | stack.tower3d | ba5b0a48d74e3348 | DEFAULT_BACKGROUND_ONLY | 11a38a5aeeff45a6 | APP_DRAW_OPS |
| solitaire (white) | de.tobiasbielefeld.solitaire | fdfaf7cad18e4416 | DEFAULT_BACKGROUND_ONLY | ba50a4d28ea62fe7 | APP_PIXELS |
| tripeaks (white) | eu.veldsoft.tri.peaks | 52272ae619c0fec8 | DEFAULT_BACKGROUND_ONLY | b5a7a35d5fe0564b | APP_DRAW_OPS |
| fishrings (white) | eu.veldsoft.fish.rings | 14d7dd80f7563c6a | DEFAULT_BACKGROUND_ONLY | b5a7a35d5fe0564b | APP_DRAW_OPS |
| klondike (white) | eu.veldsoft.free.klondike | 0203c4afd5123f88 | SPLASH_ONLY | 31ddd4d5b8e6d18e | APP_DRAW_OPS |

All 9 targets repeat-stable (3-run white / 2-run control; faces byte-identical).
Controls reproduce the recorded wall faces exactly (d5f3c7b5 / 90a67cc1 / bbd350b6 / a0319686).

**Stopwatch replacement (honest):** `com.github.muellerma.stopwatch_6.apk` was the #366-era
NO_ROOT row, but the CONT-113 decode proved the APK ARTIFACT ITSELF contains ZERO `<activity>`
elements — `aapt2 dump xmltree` shows no `E: activity` anywhere and `aapt2 dump badging` has no
`launchable-activity` line; MiniAndroid's `mainActivity=""` + `activities:[]` is a CORRECT parse
of a defective artifact (services/receivers/providers all parsed). Per #366 §1 ("do NOT use
corrupt APK-fetch cases") it was replaced by klondike and recorded ARTIFACT_DEFECTIVE, not a
runtime root.

## 02 — Pair structure (items 05/07): execution vs presentation, side by side

Independent verdicts per stage — `P`=present, `✗`=first missing stage (the primary diagnosis
is the EARLIEST ✗, not the last visible symptom):

| stage | opencalc/unote/microtimer/chess (working) | tower3d | solitaire | tripeaks/fishrings | klondike |
|---|---|---|---|---|---|
| PROCESS | P | P | P | P | P |
| LIFECYCLE (Application+Activity onCreate→onResume) | P | P | P | P | P |
| STATE (providers, prefs, resources) | P | P | P | P | P |
| WINDOW_ROOT (content root attached) | P | P (post F-NEW-459; was ✗ pre-wave) | P | P | P |
| VIEWTREE (inflated nodes) | P | P | P | P | P |
| GEOMETRY (measure/layout real sizes) | P | P | P | P | P |
| DRAW_OPS (app draw operations) | P | ✗ | ✗ | ✗ | ✗ |
| APP_PIXELS (owned non-background pixels) | P | ✗ | ✗ | ✗ | ✗ (splash face only) |
| REAL_APP_CONTENT verdict | YES | NO | NO | NO | NO |

**The one separating stage for ALL five whites is DRAW_OPS → APP_PIXELS** — a shared
presentation-layer frontier, NOT five independent boot failures. This is the pair report's
core finding: at current HEAD there is exactly ONE white family (draw), and its three
sub-cases decompose as:

## 03 — White sub-case decodes (evidence, per target)

1. **stack.tower3d** — natives + receiver binding. Pre-wave: NO_ROOT because `dlopen` of
   `libgdx.so` failed (`/lib/x86_64-linux-gnu/libm.so: invalid ELF header` — host ld-script).
   Post F-NEW-459/460/461 the libGDX chain is LIVE (`dlopen ok`, stub census 187→462
   IMPLEMENTED) and the run now dies at the AndroidGraphics `config/app`-NULL NPEs — the
   graphics-receiver binding decode = **F-NEW-462 (open, evidence captured)**.
2. **solitaire** (16 MB, GameSelector) — engine verdict DEFAULT_BACKGROUND_ONLY with
   first_missing_stage=APP_PIXELS; single uniform `93,128,240`-family face. Content draw
   frontier of the classic-canvas path; no uncaught exceptions in-flight at RUN_END.
3. **tripeaks/fishrings** — IDENTICAL faces (b5a7a35d) and shapes: SplashActivity inflates
   RelativeLayout+WebView (banner `file:///android_asset/banner.html` → F085 honest
   missing-asset placeholder), schedules the redirect `Timer.schedule` at **5000 ms virtual**;
   5-frame runs never reach it (`[F100-STATE] quiescence … DEFERRED-UI-PENDING earliest
   ready_at=5000ms — launch frame is provisional`). The splash draws no app pixels and the
   game Activity never launches inside the budget. Measurement-harness honesty note (CONT-110
   item 08): the pair verdict for these two is "splash-with-unreached-redirect", not dead boot.
4. **klondike** — SPLASH_ONLY at the canonical splash face `31ddd4d5b8e6d18e` ×3.

## 04 — What this wave closed inside the pair (fix lineage)

| fix | class | evidence |
|---|---|---|
| F-NEW-459 anchor-pipeline Makefile wiring | build-pipeline (generic) | tower3d NO_ROOT→DEFAULT_BACKGROUND_ONLY 3/3; bouncy box2d dlopen-fail→ok |
| F-NEW-460 libstdc++ anchor carries real C++ ABI | native loader law | `undefined symbol __cxa_pure_virtual` → `dlopen ok` |
| F-NEW-461 bionic LIBC_* version-family strip | native loader law | uncaughts 21→10 on bouncy; box2d live |
| F-NEW-462 graphics receiver binding | DEX shadow-heap law | CONFIRMED_OPEN_GAP, evidence-anchored, next-wave fixture |

## 05 — Next executable tasks (named levers, CONT-110 item 08 pass-2)

1. **F-NEW-462 fixture-first probe**: two-class ctor-calls-ctor receiver-binding probe;
   then the generic this-binding fix in the shadow heap.
2. **Draw-op frontier (solitaire family)**: why CLASSIC_CANVAS ViewGroups render zero app
   draw ops on a healthy tree — the same family dooz/compose already named; unify the law.
3. **Virtual-time measurement honesty**: document/pin the `--frames`→virtual-ms law so
   splash-timer apps are judged by their own redirect schedule, not an arbitrary 5-frame
   budget (harness change, no runtime law).
4. **F-NEW-449 MessageInfo (protobuf-lite)** — unchanged next-wave lever from CONT-112.
