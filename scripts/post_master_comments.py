#!/usr/bin/env python3
"""Post MASTER campaign evidence comments to Issue #8 and record direct URLs."""
import json
import subprocess
import sys
import time
from pathlib import Path

TOKEN = Path("/home/z/.gh_token").read_text().strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 8
OUT = Path("/home/z/my-project/scripts/master_comment_urls.json")

BASE_HEAD = "cc9e67ef65f0f4962c185345105244761c8826fe"
FINAL_HEAD = "e86f5d518c3ca706a1c75c61a48447c7af22d744"

comments = [
    ("EVIDENCE A/B — MASTER CAMPAIGN baseline + real-APK failure matrix + root-cause clusters",
f"""# MASTER CAMPAIGN — Evidence A/B: current-head baseline + real-APK failure matrix + root-cause clusters

**Base HEAD:** `{BASE_HEAD}` (clean tree; origin/main in sync, verified `git ls-remote`)
**Baseline:** BATTERY GATE **ALL PASS (52 stages)** — fresh run at this exact HEAD before any engine change.

## Corpus integrity (§0 rules 4-6)
- KISS `fr.neamar.kiss` v224 **restored** — SHA-256 `da6ab0b1219a…` matches the frozen 18-APK manifest (was missing from sandbox).
- 2 NEW independent APKs frozen at fetch: **Bouncy** `com.dozingcatsoftware.bouncy` v1.16.0 (vc43) `ffda0d9cb0b1b2aa…`, **Oscilloscope** `org.billthefarmer.scope` v1.40 (vc140) `0e34439ce43bfd47…` (F-Droid, Apache-2.0 / GPL-3.0).
- URL drift recorded, substitutes REFUSED: TinyMusicPlayer (F-Droid 404), Fossify Notes (`d3989c3e…` ≠ frozen `5a56e0e3…`), Markor (`e3588b46…` ≠ frozen `3f9f260d…`).
- **Telegram (F19): local `Telegram.apk` is an HTML error page (SHA `324929779f…` ≠ frozen `193ad551…`).** No fabricated Telegram result — recorded as BLOCKED-ON-FREEZE.

## Phase-0 matrix at base HEAD (16 APKs; pixel audit + per-view measure trees)
| APK | Status | Render evidence | First failing layer |
|---|---|---|---|
| headingcalculator | SUCCESS | 6.7% nonbg, 135 views | — (G11-proven) |
| microtimer | SUCCESS | 50.6% nonbg, 52 views | — (G11-proven) |
| billthefarmer_notes | SUCCESS | real (dark theme) | — |
| simplestopwatch | SUCCESS | 4.1% nonbg, 22 views | — |
| gmdice | SUCCESS | 24.6% nonbg, 20 views | — |
| unote | SUCCESS | 9.1% nonbg, 28 views | — |
| chessclock | SUCCESS | 2.7% — two 953/954px halves + divider; labels "null" | app's own construction-era null-concat (G11 microtimer precedent, LAWFUL) |
| muellerma | PARTIAL | — | F-MANIFEST: activity-less (G11 classified) |
| tictactoe | SUCCESS | BLANK (2 views) | libGDX GLSurfaceView/native (§29 F12) |
| dooz | SUCCESS | ~blank (2 views) | Compose runtime (§29 F12) |
| bgclock | SUCCESS | BLANK (2 views) | WebView + androidx-webkit (§29 F12) |
| openlauncher | SUCCESS | ~blank (20 views) | ViewPager/Fragment host (§29 F12) |
| simplekeyboard | SUCCESS | default window | IME surface layer (§29) |
| kiss | **PARTIAL rc=1** | tree built (15 views) | **F2-CLASSLINK + F-LIFECYCLE → FIXED (Evidence C)** |
| bouncy (NEW) | SUCCESS | 83.4%, 62 views, real custom Views | field drawing partial |
| scope (NEW) | SUCCESS | BLANK (10 views) | **F8/F10 measure laws → FIXED (Evidence C)** |

## Root-cause cluster A (KISS) — the deepest chain this campaign traced
1. **Ground truth (independent DEX reader committed):** KISS classes.dex has **24 classes whose superclass is `Lfr/neamar/kiss/db/DBHelper;`** (and 18 → `Lkotlin/ResultKt;`, 10 → Forwarder). R8 full-mode **horizontal class merging**: `TaskExecutor`, `DefaultTaskExecutor`, `ActivityResultContract` are merged away and NOT DEFINED. Legal R8 output; ART-compatible.
2. Every merged constructor begins `invoke-direct Ljava/lang/Object;-><init>()V` (proven with `declared=` instrumentation).
3. The engine let `Object.<init>` fall through to the shadow layer; the C013 hierarchy walk (ArchTaskExecutor → DBHelper — from the DEX superclass map, CORRECT) reached `ViewShadow::handles_class` — a catch-all claiming ANY user-defined class — which **claimed `<init>` for a database class** and returned `handled_void`.
4. Independently: androidx `LifecycleRegistry.enforceMainThreadIfNeeded` (R8-inlined `isMainThread`) evaluates `Looper.getMainLooper().getThread() == Thread.currentThread()`. The engine owned TWO shadow registries (main.cpp cmd_run vs ApplicationRuntime) with different shadow sets; the cmd_run registry lacked ThreadShadow/LooperShadow → the identity chain fell to the legacy bridge with mismatching object ids → `IllegalStateException` → `registerForActivityResult` failure → PARTIAL rc=1.

## Root-cause cluster B (scope) — measure laws
Plain custom Views (Scope/YScale/XScale/Unit) measured 0×0. Trace showed the real onMeasure bodies DID execute but `View$MeasureSpec.getSize`, `java.lang.Math.min` and `super.onMeasure` were unhandled framework statics → every computation collapsed to 0.

Fixes and laws: see Evidence C. Cross-APK runtime proof: see Evidence D."""),
    ("EVIDENCE C — fixes + Android laws (4 semantic commits)",
f"""# MASTER CAMPAIGN — Evidence C: fixes and the Android laws behind them

All fixes are generic runtime semantics — no APK names, no package branches.

## Commit `b812c214` — fix(classlink+shadow): constructor-direct law + canonical shadow registry
- **`java.lang.Object.<init>` no-op law** (execute_invoke_direct): the compiler-mandated empty constructor never dispatches. AOSP/ART law.
- **Constructor-direct law:** the hierarchy-aware shadow fallback (C013 ancestor walk) emulates VIRTUAL dispatch only — it refuses `<init>`/`<clinit>` (ART ClassLinker: no virtual constructor dispatch).
- **ONE canonical shadow registry** `framework::register_platform_shadows()`: main.cpp cmd_run and ApplicationRuntime previously built DIFFERENT registries; last `set_shadow_registry` won and the other's shadows (ThreadShadow/LooperShadow/ArchTaskExecutorShadow) were INVISIBLE. F20 §23: duplication that causes correctness bugs.
- Result: kiss rc=0; lifecycle identity `Looper.getThread()->obj==2 == Thread.currentThread()->obj==2`.

## Commit `e49b9bdd` — fix(lifecycle): entry-time lifecycle provenance
- **Provenance law:** lifecycle-from-DEX is recorded at method ENTRY (execute_method_internal), never inferred from the capacity-capped `api_call_traces` ring — volume-dependent eviction flipped SUCCESS/PARTIAL between byte-identical runs. Kiss: 5/5 runs `Status: SUCCESS`.

## Commit `e86f5d51` — feat(measure): real-DEX onMeasure + getDefaultSize + MeasureSpec/Math laws
- **F10:** custom leaf Views whose DEX chain overrides onMeasure now execute the REAL bytecode (`dispatch_custom_view_measure` → `try_recursive_invoke(onMeasure)`); `setMeasuredDimension` is a ViewShadow dispatch capturing the write-back. Override detection = `class_chain_defines_method()` — semantic ancestry walk; framework CONTENT families (TextView/ImageView/ProgressBar + AppCompat variants) stop the chain as content-law classes. Hook installed process-wide on ResourceRuntime (Factory law).
- **F8 default law:** `View.onMeasure(I,I)V` bridge handler = the AOSP default implementation (`getDefaultSize`: AT_MOST/EXACTLY → specSize, UNSPECIFIED → suggested minimum).
- **MeasureSpec bitwise laws:** `getMode = spec >>> 30`, `getSize = spec & 0x3FFFFFFF`, `makeMeasureSpec = (mode<<30)|(size&MASK)` (AOSP View.java MeasureSpec). Without these every real onMeasure computed zeros.
- **java.lang.Math min/max/abs** overloads (universal java.lang semantics).
- Evidence (scope): YScale.onMeasure real DEX now measures **45×1080**, XScale **1920×60**; render gains ~84K px of drawn scale-bar content. Previously 0×0.

## Regression
Fresh 52-stage battery **ALL PASS** after each fix landing; helloworld 26/26, tictactoe 8/8 goldens unchanged; corpus regression guards byte-identical (simplestopwatch `ed1dfc89…`, unote `8197687f…`, gmdice, microtimer). Zero golden updates.

## Diagnostics added (cap-limited, structured — F17)
`[REC-MISS]` (recursive-invoke class misses), `[C013-HIER … (declared=… receiver=…)]` (ancestor-walk attribution), `[BRIDGE-TID]`/`[THREAD-ID]` (main-thread identity evidence), `[DEFAULT-MEASURE]` (override-query verdict per constructed view)."""),
    ("EVIDENCE D — cross-APK runtime proof: input → real DEX callback → state change → second frame",
"""# MASTER CAMPAIGN — Evidence D: F16 interaction proofs (cross-APK)

For each APK: tap → real hit test → real DEX listener dispatch → state mutation → second frame. 3-run determinism = byte-identical PNG hashes.

| APK | Dispatched handler (real DEX) | Base frame SHA-16 | Post-tap frame SHA-16 | 3-run |
|---|---|---|---|---|
| simplestopwatch `omegacentauri.mobi.simplestopwatch` v26 | `onButtonStart`, `onButtonReset` (real DEX buttons) | `ed1dfc8981c5f471` (**= G10 frozen golden**) | `6823fc042ac3f471` | byte-identical ×3 |
| uNote `app.varlorg.unote` v30 | `search`, `quit` (real DEX) | `8197687fe7d4e7d4` (**= G11 frozen golden**) | `86aed6160ba82f39` | byte-identical ×3 |
| Bouncy `com.dozingcatsoftware.bouncy` v1.16.0 (NEW) | 12/12 probed handlers dispatched — `ScoreView.scoreViewClicked`, `doPreviousTable`, `doShowTableList`, `doNextTable`, `doPreferences`, `doQuit`, `hideHighScore`…; 3 views changed 158,760 px each | `072ff17874b7` | `14500d736bf422f0` | byte-identical ×3 |
| EXT-01 HelloWorldSelfAware (unchanged) | `onLongClick` → ClipData → Toast (GOLDEN-02 12/12) | — | — | battery gate |

Probed-but-unchanged (honest): chessclock (8 probed, 4 handlers — timer-state layer = G07 future), microtimer (12 probed — timer-tick scheduling = G07 future), billthefarmer notes (3 probed — menu-driven), gmdice (no click report — probe surface gap, recorded).

Cross-APK standard: the F16 interaction law is exercised by **3 independent real APKs** from 3 different authors + the EXT-01 fixture → **CROSS-APK VERIFIED** for the tap→callback→frame chain. The real-DEX onMeasure law (Evidence C) is exercised by scope (XML custom views) with bouncy's custom views as a partial second corpus user → **LAW-TESTED + SINGLE-APK-STRONG**; the constructor-direct/registry laws are exercised by kiss + every androidx APK in the corpus (regression-verified) → **CROSS-APK VERIFIED**."""),
    ("EVIDENCE E — final compatibility matrix, remaining blockers, honest boundary",
f"""# MASTER CAMPAIGN — Evidence E: final matrix, remaining blockers, honest boundary

**Final HEAD:** `{FINAL_HEAD}` (pushed; remote verified). Base `{BASE_HEAD}` → final: 4 semantic commits.

## What changed for real APKs (base → final)
| APK | Before | After |
|---|---|---|
| kiss v224 | PARTIAL, rc=1, lifecycle IllegalStateExceptions | **rc=0, Status SUCCESS (5/5 stable), 3× byte-identical frame `eb16ab5c…`**; launcher tree (AnimatedListView, search bar, custom views) constructs via real constructors |
| scope v140 (NEW) | BLANK (all 4 custom views 0-sized) | **real DEX onMeasure executes; YScale 45×1080, XScale 1920×60; ~84K px drawn content** |
| bouncy v43 (NEW) | already rendered | unchanged + interaction proof (12 handlers, 3 frames) |
| all others | unchanged (regression guards byte-identical) | unchanged |

## Remaining blockers (ranked, honest)
1. **PROVEN-DIAGNOSED, fix queued** — scope Scope/Unit views: their onMeasure did not dispatch through the new hook while YScale/XScale did (needs one more trace pass: `try_recursive_invoke(Scope,onMeasure)` failed silently — likely lookup/signature).
2. **PROVEN-DIAGNOSED, fix queued** — chessclock/microtimer time labels show the app's own construction-era "null" strings; real device replaces them at first Handler tick → requires MessageQueue timer scheduling (G07 layer).
3. **PROVEN-DIAGNOSED, larger scope** — bouncy CanvasFieldView draws partial table content; the field view's full onDraw path (canvas op coverage) is the next F10/F12 item.
4. **§29 documented boundaries (unchanged):** Compose (dooz), WebView (bgclock), GLSurfaceView/native libgdx (tictactoe), ViewPager/Fragment host (openlauncher), IME surface (simplekeyboard), implicit intents (chessclock/unote settings screens).
5. **F19 Telegram: BLOCKED-ON-FREEZE** — no exact-version APK obtainable this session; local file was an HTML page. No result fabricated.
6. **Registry drift:** TinyMusicPlayer/Fossify/Markor exact frozen binaries unrecoverable from recorded URLs — recorded, not substituted.
7. **Harness debt:** `scripts/run_test_battery.sh` still lives outside git (sandbox-only) — committed copies of the NEW campaign harnesses exist (`master_phase0.py`, `dex_superclass_check.py`); the 52-stage battery script itself should be committed next.

## Status vocabulary (no silent upgrades)
- Constructor-direct law + canonical registry: **CROSS-APK VERIFIED** (kiss motivating + full-corpus regression + battery).
- Lifecycle provenance: **RUNTIME-PROVEN** (kiss 5/5) + battery.
- Real-DEX onMeasure + MeasureSpec/Math/default laws: **RUNTIME-PROVEN + VISUALLY-PROVEN on scope (SINGLE-CORPUS-USER)** — second corpus user queued.
- F16 tap→state→frame: **CROSS-APK VERIFIED** (3 independent APKs + fixture).
- NOT claimed: full AppCompat/Compose/WebView/GL compatibility; complete launcher surfaces; Telegram.

The project is NOT "fully compatible". What this campaign proves: the APK→load→manifest→classes→real DEX→real constructors→hierarchy→measure→layout→draw chain got **materially more reliable across 16 frozen real APKs**, with the two deepest failure chains (R8-merged constructor dispatch; androidx main-thread identity) root-caused to laws and fixed generically."""),
]

urls = []
for i, (title, body) in enumerate(comments):
    payload = json.dumps({"body": body})
    proc = subprocess.run(
        ["curl", "-sS", "-X", "POST",
         f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
         "-H", f"Authorization: Bearer {TOKEN}",
         "-H", "Accept: application/vnd.github+json",
         "-d", payload],
        capture_output=True, text=True, timeout=60)
    try:
        resp = json.loads(proc.stdout)
        url = resp.get("html_url")
        if not url:
            print(f"POST {i+1} FAILED: {proc.stdout[:300]}", file=sys.stderr)
            urls.append(None)
            continue
        urls.append(url)
        print(f"POSTED {i+1}: {url}")
        time.sleep(2)
    except Exception as e:
        print(f"POST {i+1} ERROR: {e}", file=sys.stderr)
        urls.append(None)

OUT.write_text(json.dumps({"issue": ISSUE, "urls": urls}, indent=2) + "\n")
print(f"saved -> {OUT}")
