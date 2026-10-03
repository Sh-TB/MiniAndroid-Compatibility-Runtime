# DIFFERENTIAL EXECUTION — WHY 4 APPS WORK AND 5 APPS STAY WHITE

> Issue #366 · 2026-10-03 · CURRENT HEAD `204aed6bdec7325daf8f7360517d4ef74333d086`
> RUNTIME BUILD: `miniandroid/build/miniandroid` sha256-16 `4b2db3540575b1c4` (v0.1, REAL_DALVIK)
> Method: OBSERVE→MEASURE→RECONSTRUCT→CORRELATE→VERIFY→CLASSIFY (all nine apps re-run on
> CURRENT HEAD through the SAME installed-identity pipeline; zero package-specific anything).

## 0. ANSWER TO THE MISSION QUESTION

> **Is the white screen because the APK was not installed/loaded correctly, or did the APK
> really run from the installed identity and fail later in lifecycle / ViewTree / resource /
> storage / decode / layout / draw / native / Compose / WebView?**

**Verdict — Case A, not Case B, for all five white apps.** Every one of the five white apps
was installed correctly (installed SHA == source SHA, proven), executed **from the installed
base.apk identity with the source APK hidden**, parsed its manifest and DEX, resolved its
launcher activity, and reached Activity lifecycle (all five end `RESUMED`). The white frames
happen **later**, and the five first divergences are **NOT one cause**:

| # | App | First divergence | Root category |
|---|-----|------------------|---------------|
| 1 | org.fossify.clock | authoritative WINDOW_ROOT absent at frame time (deferred UI pending) after App.onCreate EventBus death + LayoutInflater.inflate null-XmlPullParser NPE | VIEWTREE/ATTACH |
| 2 | com.sidhant.blockblast | content view never materialized — `ComposeView NOT in class index` (tree stays 1 node) | COMPOSE |
| 3 | com.game.asteroids_revenge | `Arrays.toString` shadow returned null (REC-MISS) → kotlin Intrinsics NPE → `GodotActivity.onCreate` died at pc=0x3a before creating the native GodotView | NATIVE/JNI (trigger: null-semantics §18) |
| 4 | fr.arnaudguyon.spacevertex | `Class.forName("kotlin.internal...implementations").newInstance()` → null → NPE; re-dispatch dies on androidx Fragment ISE ("HomeFragment must be a public static class") | FRAGMENT |
| 5 | com.sanskritbasics.memory | null-receiver `.getClass` NPE inside androidx WindowInsets compat (`s0$k.<clinit>`→`s0.v/.u`) during `ActionBarOverlayLayout.<init>`; content (WebView) inflated but never painted | ANDROIDX LIFECYCLE |

> **Where exactly does the working path continue and the white path stop?** For the working
> apps the chain `setContentView → Window → ViewTree(n≥9) → measure → layout → draw
> (app_draw_ops≥7) → app-owned pixels (≥302,400)` completes. For three whites the chain
> never reaches measure (NO_ROOT: no authoritative window root); for two it reaches
> measure/layout/draw but emits only the window-background draw op (DEFAULT_BACKGROUND_ONLY).
> Every divergence sits **above the byte-loading layer** — resource/asset/file/stream/FD
> loading did NOT fail in any of the nine apps.

## 1. LAWS READ

`LAWS READ: YES` (worklog, this task ID). CONSTITUTION_V2 (§0-§17, §27-§35, §44-§46 quoted in
full); `.agent/CODER_REQUEST_PROTOCOL.md`; `.agent/mission.md`, `state.md`,
`master_campaign_state.md`, `decisions.md`, `backlog.md`; `CAMPAIGN_STATE.md` (forensic+upstream
wave); worklog tail (LOADING-EXEC-CLOSE + FORENSIC-365); `docs/WHITE_SCREEN_LOADING_ROOTS.md`,
`WORKING_APP_LOADING_EXPLANATIONS.md`, `WORKING_VS_FAILING_LOADING_MATRIX.jsonl`. Laws applied:
FIRST DIVERGENCE (§16), BLANK SCREEN IS A SYMPTOM (§27), PIXEL PROOF (§33), NO FAKE VISUAL
SUCCESS (§34), REAL APP IS EXECUTION TRUTH (§46). New law discovered during this work (recorded
here per request §1): **a byte-stable golden is not a pixel-truth golden** — chess/dooz goldens
were determinism gates and their frames are 100% white; the F-NEW-233 frame-truth verdict must
accompany every "working" claim.

## 2. THE NINE (plus two honesty controls)

**WORKING (4)** — real pixels proven (F-NEW-233 verdict `REAL_APP_CONTENT`):

| App | Package | Why selected | Screenshot SHA-256 (16) |
|-----|---------|--------------|--------------------------|
| OpenCalc | com.darkempire78.opencalculator | request-mandated; re-proven at HEAD | `e364b001ee7abd66` |
| uNote | app.varlorg.unote | request-mandated; re-proven at HEAD | `4f1a9e4e8f64fae8` |
| MicroTimer | dubrowgn.microtimer | request-mandated; re-proven at HEAD | `da73010a37dd0189` |
| Bouncy | com.dozingcatsoftware.bouncy | REPLACEMENT for Chess (regression, §7); canonical corpus | `b6dde6074bf47264` |

**WHITE (5)** — from the S115 NEAR_BLANK population, all re-screened on CURRENT HEAD (12
candidates screened, 12/12 still BLANK, corrupt-fetch/PARTIAL/splash-only classes excluded;
5 selected spanning distinct root families F1/F3/F5/F6+F7):

| App | Package | S115 ticket/family | Screenshot SHA-256 (16) |
|-----|---------|--------------------|--------------------------|
| Fossify Clock | org.fossify.clock | #202, empty-viewtree | `31ddd4d5b8e6d18e` |
| BlockBlast | com.sidhant.blockblast | #86, LifecycleRegistry/Compose | `31ddd4d5b8e6d18e` |
| Asteroids Revenge | com.game.asteroids_revenge | #109, libGDX/JNI natives | `31ddd4d5b8e6d18e` |
| Space Vertex | fr.arnaudguyon.spacevertex | #96, FragmentManager | `9d8c64b1f9f908b4` |
| Memory (Sanskrit Basics) | com.sanskritbasics.memory | #67, MultiDex-ticket family | `0666775d14475766` |

**Honesty findings (outside the quota, recorded per request §2/§10):**

- **Chess (jwtc.android.chess) — REGRESSION-CLASSIFICATION.** Golden `b5a7a35d5fe0564b` is
  byte-stable ×3 at HEAD but the frame is **100% white** (1 unique color, app_draw_ops=0,
  verdict DEFAULT_BACKGROUND_ONLY, first_missing_stage=APP_DRAW_OPS). The historical golden was
  a **determinism/persistence gate** (chess_pgn.db), never a pixel gate. Its start activity
  dies on an uncaught NPE (`Ljwtc/android/chess/start;.onCreate` pc=9) and the game-list
  RecyclerView never binds a child (node 429, children=0). Replaced by Bouncy; cause recorded.
- **Dooz (control)** — same class: golden `d602648e8e401895` byte-stable, frame white
  (2 obfuscated Compose host nodes, 0 draw ops; final-campaign P1-8 removed its diagnostic
  placeholder pixels). Root category COMPOSE.

## 3. INSTALL IDENTITY PROOF (all 11 apps)

Pipeline per app: `install <src> --data-root <store>` → SHA(source) vs SHA(`data/app/<pkg>/base.apk`)
→ `pkgaudit --package <pkg> --data-root <store>` (live re-hash) → **source APK moved to
`run/diff366/hidden_sources/`** → `run --package <pkg> --data-root <store>` (the runtime
resolves ONLY `<store>/data/app/<pkg>/base.apk`; run.log prints `INSTALLED-PACKAGE MODE` +
`codePath`). Full SHAs in `docs/DIFFERENTIAL_WORKING_VS_WHITE.jsonl`.

| App | source==installed SHA (16) | pkgaudit live | source hidden |
|-----|------------------------------|----------------|----------------|
| opencalc | 2642613868a8a80f | 2642613868a8a80f | YES |
| unote | be91103f0e7db443 | be91103f0e7db443 | YES |
| microtimer | 79c6f730f64886e7 | 79c6f730f64886e7 | YES |
| chess | 3245b9ec35f6c1df | 3245b9ec35f6c1df | YES |
| bouncy | ffda0d9cb0b1b2aa | ffda0d9cb0b1b2aa | YES |
| dooz | 299eab21ac8b3c61 | 299eab21ac8b3c61 | YES |
| fossifyclock | 43cf9f0ec45f1f1f | 43cf9f0ec45f1f1f | YES |
| blockblast | 64589a3a7e5c0f73 | 64589a3a7e5c0f73 | YES |
| asteroids | ca4575b2953d7100 | ca4575b2953d7100 | YES |
| spacevertex | 591f15ec76183bd5 | 591f15ec76183bd5 | YES |
| memory | 830798a6e70653d6 | 830798a6e70653d6 | YES |

11/11 `sha_match=True`, 11/11 runs launched from installed identity with the source hidden.
(No `source SHA != installed SHA` discrepancy occurred; had one occurred it would have been
investigated before any run, per request §3.)

## 4. WORKING-vs-WHITE STAGE MATRIX

Compact view (Y = proven by trace/log artifact, n/a = not applicable to this app's tech,
NO = expected observable absent). Full 27-row matrix per app:
`run/diff366/stage_matrices.json` (generated by `scripts/diff366_report.py`).

| Stage | opencalc | unote | microtimer | bouncy | fossifyclock | blockblast | asteroids | spacevertex | memory |
|---|---|---|---|---|---|---|---|---|---|
| Install + identity | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| Manifest parsed | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| Application.onCreate | Y | Y | Y | Y | died-mid (EventBus) | Y (fallback app) | Y (default app) | Y | Y |
| Activity resolved | Y | Y | Y | Y | Y (Splash→Main) | Y | Y | Y | Y |
| Activity.onCreate | Y | Y | Y | Y | Main yes | Y | died pc=0x3a | died ×2 | died ×3 |
| setContentView | Y | Y | Y | Y | Y (root=2192) | NO content | NO | Y (decor) | Y (decor+content) |
| Window/decor | Y | Y | Y | Y | linked, not authoritative | NO | NO | Y | Y |
| ViewTree nodes | 67 | 14 | 26 | 31 | 6 | 1 | 2 | 8 | 7 |
| Resource resolution | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| Asset access | n/a | n/a | n/a | Y (12 opens) | n/a | n/a | Y (`_cl_` x3) | n/a | n/a |
| File access | WRITE×2 | sqlite | MKDIR×7 OPEN×3 | LIST+OPEN | — | — | — | — | — |
| Stream/FD | n/a | n/a | n/a | Y (openFd fd=4..7) | n/a | n/a | Y (stream) | n/a | n/a |
| Decode | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| View attach | Y | Y | Y | Y | ok=false | ok=false | ok=false | ok=true | ok=true |
| Measure/Layout | Y | Y | Y | Y | NO | NO | NO | Y | Y |
| Draw walk | Y | Y | Y | Y | NO | NO | NO | Y | Y |
| App draw ops | 36 | 7 | 22 | 11 | 0 | 0 | 0 | 1 | 1 |
| App-owned pixels | 732,555 | 302,400 | 1,029,909 | 978,380 | 0 | 0 | 0 | 0 | 0 |
| Frame verdict | REAL_APP_CONTENT | REAL_APP_CONTENT | REAL_APP_CONTENT | REAL_APP_CONTENT | NO_ROOT | NO_ROOT | NO_ROOT | DEFAULT_BG_ONLY | DEFAULT_BG_ONLY |
| State change | YES | YES | YES | YES | NO | NO | NO (asset reads only) | NO | NO |

**Reading the matrix:** the boundary between WORKING and WHITE is exactly the pair
`app_draw_ops > 0 ∧ app-owned pixels > 0` — i.e., the **DRAW stage**, with three distinct
upstream arrest points (no-window-root; window-but-no-app-draw; content-inflated-but-never-fed).

## 5. FIRST DIVERGENCES — evidence

Each entry cites the runtime log lines that prove it (full chains in §6/§7;
machine-readable: `docs/DIFFERENTIAL_FIRST_DIVERGENCES.jsonl`).

1. **fossifyclock** — `[F-NEW-233] verdict=NO_ROOT first_missing_stage=WINDOW_ROOT`,
   `[F-NEW-232] deferred-UI pending queue_size=1`; damage chain upstream:
   `[EXC-UNWIND] EventBusException unwound Lorg/fossify/clock/App;.onCreate`, then
   `[EXCEPTION] Ln/h;.inflate pc=86 NPE "XmlPullParser.getEventType on null object reference"`,
   then `[R005-DECOR] view=2192 under decor=1133` + `[F-NEW-220] CONTENT-PARENT-REUSED` —
   content linked but never authoritative at frame time. **Not an installation failure.**
2. **blockblast** — `[UC009-ATTACH-DIAG] classes_indexed=633 nodes=1 + "ComposeView NOT in
   class index"`, `attach dispatch complete ok=false`, `[R341-APP] Application hint not in DEX`.
3. **asteroids** — `[REC-MISS] Ljava/util/Arrays;.toString caller=GodotActivity.onCreate` →
   `[THROWABLE-STACK] Intrinsics.checkNotNullExpressionValue → GodotActivity.onCreate(pc=0x3a)
   → GodotApp.onCreate` → `APP BOUNDARY`; tree frozen at 2 decor nodes. Before dying, the
   engine DID stream command-line assets (`[STREAM-READ] asset=_cl_ ×3`).
4. **spacevertex** — `[THROWABLE-MSG] NPE forName("kotlin.internal…implementations")
   .newInstance() must not be null (Lji;.n pc=11 depth=11)`; re-dispatch →
   `[THROWABLE-MSG] ISE "Fragment … HomeFragment must be a public static class…"
   (Landroidx/fragment/app/a;.b pc=232)`; decor attaches ok (12 nodes) but content never
   inflated → `app_draw_ops=1` (window background only).
5. **memory** — `[SYNTH-EXC] f141-null-recv NPE (…'getClass' on null) method=Lx/h;.g pc=0`
   unwinding `s0$k.<clinit> → s0.<clinit> → s0.v → s0.u → ActionBarOverlayLayout.<init> →
   appcompat h.c0 → MainActivity.onCreate` ×3; tree includes the app WebView
   (`[EXP092-RENDER] node=702 WebView 1080x1920`) but 0 app draw ops.

## 6. WHY EACH WORKING APP WORKS (runtime evidence, request §7)

**OpenCalc.** (1) First real UI: calculator display + keypad grid (570 unique colors).
(2-3) APIs: AXML inflation, ConstraintLayout measure/layout, TextView/paint draw, theme attrs
(`[F-NEW-175] obtainStyledAttributes theme-backed`), atomic prefs WRITE ×2, ARSC values.
(4) NOT exercised: assets, openFd, decodeStream, providers beyond androidx.startup.
(5) UI: XML. (6) Compose: no. (7) WebView: no. (8) SurfaceView: no. (9-10) native/JNI: no.
(11) MultiDex: no. (12) Fragment/AndroidX: only the startup provider. (13) ContentProvider:
androidx.startup — its StartupException (`LH1/g;`) is **absorbed** at the app boundary and
does not kill the chain. (14) config/density: theme-backed ARSC values. (15) persistence:
SharedPreferences (atomic, escaped). (16) The generic path that carried it:
provider(absorbed) → Application.onCreate → Activity.onCreate → setContentView →
F-NEW-220 content-parent → ARSC inflate → DEFAULT-MEASURE → draw walk (48 nodes) →
36 draw ops → 732,555 app pixels. (17) That path suffices only because OpenCalc stays inside
implemented surface: it never instantiates a Compose view, never loads natives, never walks
androidx WindowInsets compat (`s0` family), and never relies on Fragment recreation.

**uNote.** Narrowest surface of the four, **zero uncaught exceptions** (crash.log empty):
plain `android.widget` XML (RelativeLayout/LinearLayout/ListView/Button), real SQLite
`notes.db`, 7 draw ops / 302,400 app pixels. It proves the plain-widget + SQLite path is
complete — and nothing else.

**MicroTimer.** Fully programmatic UI (no AXML): LinearLayout/ScrollView from constructors,
26 views, 22 draw ops, 1,029,909 app pixels. Real file family: `File.mkdirs`×6, cache
`FileOutputStream` OPEN×3, STAT×6, SQLite `app-data` with `-wal`/`-shm` on the store.
No assets, no FDs, no Compose, no natives.

**Bouncy.** Custom-View game: `ScoreView`(1080×147) + `CanvasFieldView`(1080×1773) with real
sizes; 11 draw ops, 978,380 app pixels, 314 colors. Asset layer proven live: 12 asset OPENs,
including `openFd` returning **real host fds** with offset/len (dinga1.ogg fd=4 off=1459454
len=60630), and the honest `FileNotFoundException` for missing `assets/tables/tablenull.json`
which the app **caught** (deferred handler) and continued. libGDX `SharedLibraryLoader`
executed; its `SharedLibraryLoadRuntimeException` unwound but was absorbed inside app frames —
the Canvas fallback renders. Contrast with Asteroids: same native-load frontier, but Bouncy's
failure lands inside a catchable app frame while Godot's kills `onCreate` outright.

**Why working ≠ sufficient (§7.17).** Each working app survives because it never touches the
four frontiers that kill the whites: Compose view materialization (blockblast/dooz), the
java.util shadow null-contracts that kotlin Intrinsics converts into lethal NPEs
(asteroids/spacevertex), androidx Fragment recreation law (spacevertex), and WindowInsets
compat static-init (memory). None of the working apps exercises those paths — that is why
"working" was never evidence of "complete".

## 7. WHY EACH WHITE APP IS WHITE (request §8, per-question verdicts)

Per-app 22-question tables (answered YES/NO with values) are in
`run/diff366/stage_matrices.json` + §4 matrix above. Shared verdicts, then per-app deltas:

Common YES (all five): installed correctly; installed APK opened; package identity correct;
Application.onCreate dispatched; launcher Activity resolved; Activity object created;
resource requests served (ARSC-VALUES in every log). Common NO: framebuffer never shows app
pixels (`window_background_px=2,073,600` only).

- **fossifyclock**: App.onCreate died mid-way (EventBusException); SplashActivity
  onStart/onResume ran; `startActivity` → MainActivity constructed (2007 insns), themed,
  `getLayoutInflater` dispatched; inflate NPE (null XmlPullParser); setContentView linked
  root=2192 but deferred-UI queue still pending at frame time → NO_ROOT. Object created YES,
  consumer NO (draw walk never ran).
- **blockblast**: onCreate/onResume dispatched (106 insns); no setContentView content ever;
  tree=1 node; ComposeView not instantiable from DEX; attach ok=false.
- **asteroids**: GodotApp.onCreate dispatched and streamed `_cl_` assets; GodotActivity.onCreate
  died at pc=0x3a (Arrays.toString null → Intrinsics NPE); no view beyond decor stubs (2);
  no draw, no state change; asset reads were the only I/O.
- **spacevertex**: setContentView executed (decor, 12 nodes); attach ok=true; measure/layout/draw
  ran; draw emitted 1 op (window background); content fragment never inflated (2 stacked deaths:
  forName-null NPE, then Fragment ISE).
- **memory**: setContentView executed; 13-node tree INCLUDING app content (RelativeLayout +
  WebView); attach ok=true; MainActivity.onCreate killed ×3 by WindowInsets-compat NPE;
  WebView walked by renderer but emits 0 draw ops (no content ever loaded into it).

## 8. CASE A vs CASE B (request §10)

All five whites are **Case A** (`INSTALL/PACKAGE/APPLICATION/ACTIVITY = PASS` with per-app
exceptions above; `VIEWTREE/DRAW/FRAME = FAIL` — ViewTree empty-or-decor-only, draw fails,
frame white). **No Case B** (no app failed to launch from installed identity). The App.onCreate
partial-death in fossifyclock is a lifecycle sub-damage *inside* Case A — the activity chain
still ran from the installed identity.

## 9. SCREENSHOT PROOF (request §11)

Metrics computed on the actual frame (`scripts/diff366_final.py::pixel_metrics`, PIL decode,
270×480 downsample; full fields in JSONL):

| App | unique colors | non-bg ratio | entropy | classification |
|-----|---------------|--------------|---------|-----------------|
| opencalc | 570 | 0.3668 | 1.467 | REAL_APP_UI |
| unote | 326 | 0.1521 | 0.922 | REAL_APP_UI |
| microtimer | 305 | 0.5026 | 1.572 | REAL_APP_UI |
| bouncy | 314 | 0.4833 | 1.905 | REAL_APP_UI |
| fossifyclock | 1 | 0.0 | 0.0 | WHITE_BLANK |
| blockblast | 1 | 0.0 | 0.0 | WHITE_BLANK |
| asteroids | 1 | 0.0 | 0.0 | WHITE_BLANK |
| spacevertex | 1 | 0.0 | 0.0 | WHITE_BLANK |
| memory | 1 | 0.0 | 0.0 | WHITE_BLANK |
| chess (regression) | 1 | 0.0 | 0.0 | WHITE_BLANK |
| dooz (control) | 1 | 0.0 | 0.0 | WHITE_BLANK |

Working pixels are proven app-owned by the F-NEW-233 census (`app_owned_pixels` counts only
pixels owned by app draw ops inside content bounds; e.g. opencalc 732,555). For whites, the
capture path itself is proven healthy: the SAME capture produced the four working frames in
the same session, and each white's `window_background_px=2,073,600` matches a full-HD frame
painted with exactly the window background.

## 10. THREE-RUN REPRODUCIBILITY (request §12)

`run1/2/3` per app, fresh run dirs, same store; screenshot SHA-256 compared.

| App | run1 | run2 | run3 | Verdict |
|-----|------|------|------|---------|
| opencalc | e364b001ee7abd66 | e364b001ee7abd66 | e364b001ee7abd66 | DETERMINISTIC |
| unote | 4f1a9e4e8f64fae8 | 4f1a9e4e8f64fae8 | 4f1a9e4e8f64fae8 | DETERMINISTIC |
| microtimer | da73010a37dd0189 | da73010a37dd0189 | da73010a37dd0189 | DETERMINISTIC |
| chess | b5a7a35d5fe0564b | b5a7a35d5fe0564b | b5a7a35d5fe0564b | DETERMINISTIC |
| bouncy | b6dde6074bf47264 | b6dde6074bf47264 | b6dde6074bf47264 | DETERMINISTIC |
| dooz (control) | d602648e8e401895 | d602648e8e401895 | d602648e8e401895 | DETERMINISTIC |
| fossifyclock | 31ddd4d5b8e6d18e | 31ddd4d5b8e6d18e | 31ddd4d5b8e6d18e | DETERMINISTIC |
| blockblast | 31ddd4d5b8e6d18e | 31ddd4d5b8e6d18e | 31ddd4d5b8e6d18e | DETERMINISTIC |
| asteroids | 31ddd4d5b8e6d18e | 31ddd4d5b8e6d18e | 31ddd4d5b8e6d18e | DETERMINISTIC |
| spacevertex | 9d8c64b1f9f908b4 | 9d8c64b1f9f908b4 | 9d8c64b1f9f908b4 | DETERMINISTIC |
| memory | 0666775d14475766 | 0666775d14475766 | 0666775d14475766 | DETERMINISTIC |

(≥2 working + ≥3 white required; delivered 4 working + 5 white + 2 controls, 3-run each.)
**Evidence-integrity closure (continuation §0, option A)**: the first publication of this
report overclaimed 3-run coverage — `microtimer` and `dooz` had executed only `run1`
(`three_run=False` in the pipeline table). The missing run2/run3 have now been **executed**
(`scripts/diff366_run23.py`, same binary `4b2db3540575b1c4`, same stores, pkgaudit live
re-hash match, source APKs still hidden): all four new runs are byte-identical to run1
(microtimer `da73010a37dd0189…` ×3, REAL_APP_CONTENT; dooz `d602648e8e401895…` ×3,
DEFAULT_BACKGROUND_ONLY; first divergence stable; per-run trace SHAs in the JSONL
`trace_shas` field). The x9/x11 3-run claim is now true on persisted artifacts —
no `single-run` residue remains in any ledger. First divergence identical across runs in
every case — **no NONDETERMINISTIC divergences**. Trace SHA per run recorded in the JSONL.

## 11. WHY WORKING APPS WORK WHILE WHITE APPS FAIL (request §15 — causal analysis)

**APIs exercised by BOTH groups** (proven present in both groups' logs): manifest parse,
DEX parse, class loading, Application/Activity lifecycle dispatch, ARSC resource resolution,
theme/obtainStyledAttributes, view inflation (appcompat decor at minimum), attach dispatch,
 SharedPreferences/asset/file reads where applicable.

**APIs exercised ONLY by the working group**: successful `setContentView` with an
in-DEX content class (XML or programmatic or custom View); ConstraintLayout/ListView/
custom-View measure-layout-draw to completion; Canvas draw ops reaching the frame census
(`app_draw_ops` 7-36); real fds via `openFd` (bouncy); cache file writes (microtimer);
caught-and-continued missing-asset `FileNotFoundException` (bouncy).

**APIs exercised ONLY by the white group** (the discriminator set):
- Compose/ComponentActivity content materialization (`ComposeView NOT in class index`) —
  blockblast, dooz.
- `java.util.Arrays.toString` / `Class.forName(...).newInstance()` shadows returning **null**
  where the AOSP contract says non-null — converted by kotlin `Intrinsics` checks into lethal
  NPEs — asteroids, spacevertex.
- androidx Fragment instance-state recreation law (`Fragment must be a public static class`) —
  spacevertex.
- androidx core WindowInsets compat static-init (`s0$k.<clinit>` null-receiver) inside
  `ActionBarOverlayLayout.<init>` — memory.
- EventBus bootstrap inside `Application.onCreate` (throws, unwinds app init) — fossifyclock.
- Godot native activity surface creation (`GodotView`/JNI) — asteroids (open frontier
  independently of the NPE trigger).

**Group deltas (per axis)**: lifecycle — whites die inside `onCreate` frames (3/5) or finish
lifecycle with empty content (2/5); component resolution — identical; ViewTree — working
9-67 nodes vs white 1-13 (decor-only or stub); resource — identical (never the cause);
asset — identical (never the cause; asteroids even streamed assets while dying); file/storage
— identical (loading is NOT the differentiator); native/JNI — only whites attempt it
(asteroids Godot, bouncy libGDX — bouncy SURVIVES because its failure is catchable in app
frames); Compose — only whites (blockblast); WebView — only memory (inflated but unfed);
MultiDex — the #67 ticket's S115 label is obsolete: current-HEAD memory fails in
androidx core view, NOT in MultiDex.

**The single sharpest discriminator**: every working app's path crosses
`ViewTree → measure → layout → draw-op emission`; every white path is arrested before a
single app-owned draw op survives — three arrested at window-root authority, two after the
walk with an empty/undrawn content. The arrest causes are five distinct generic gaps, not one.

## 12. FIX POLICY (request §13/§14)

**No fix was applied in this mission** — the request is diagnose-first. Root hypotheses above
are already runtime-evidence-backed (each carries its log-line proof). Candidate generic fixes,
in leverage order, each requiring its own fixture + 9-app rerun + golden regression per §14:

1. **java.util/java.lang shadow null-contracts** (`Arrays.toString`, `Class.forName`
   chain): return contract-honoring values instead of null (AOSP: `Arrays.toString(null)` →
   `"null"`; `Class.forName` → real ClassObject or honest throw). Fixtures: kotlin
   `Intrinsics.checkNotNullExpressionValue` probe. Expected fan-out: asteroids content chain
   advances; spacevertex advances to its Fragment frontier.
2. **androidx WindowInsets compat static-init** (null-receiver `.getClass` inside
   `s0$k.<clinit>`): complete the `androidx.core.view` WindowInsetsBuilder law. Expected
   fan-out: memory decor init completes; WebView feeding frontier becomes reachable.
3. **androidx Fragment instance-state recreation** (`a;.b` law): the
   "public static class" check path. Fan-out: spacevertex HomeFragment inflation.
4. **ComposeView materialization** (already a known frontier, #344 family).
5. **GodotView/native surface** — native/JNI frontier (S-2), largest, unchanged.

No package name, no app title, no screenshot appears in any rule — all five are expressible
as AOSP-cited semantic laws.

## 13. COMPLETION GATE (request §18)

- [x] 4 Working tested (opencalc, unote, microtimer, bouncy — REAL_APP_CONTENT)
- [x] 5 White/Failed tested (fossifyclock, blockblast, asteroids, spacevertex, memory)
- [x] installed identity proof for all (11 incl. chess/dooz) — SHA match + pkgaudit + hidden-source run
- [x] lifecycle/component trace for all (`trace.jsonl`, `lifecycle_trace.json`)
- [x] ViewTree result for all (`view_tree.json` counts + classes)
- [x] First Divergence for all (log-line evidence, §5)
- [x] screenshot metrics + SHA for all (§9)
- [x] 3-run for 4 working + 5 white (§10)
- [x] Working-vs-White matrix (§4 + `run/diff366/stage_matrices.json`)
- [x] why-working explanation (§6)
- [x] why-white explanation (§7)
- [x] no package-specific patch (diagnose-only mission)
- [x] current HEAD verified (`204aed6b…`, binary `4b2db3540575b1c4`)
- [x] generic regression — n/a (no fix applied); goldens byte-identical ×3 at HEAD as side-proof
- [x] runtime conclusion ≥ E3 — delivered E4 (runtime + state change + consumer + output per app; 3-run reproducibility on all 9; provenance via trace SHAs). E5 reserved for the post-fix rerun cycle.

## 14. ARTIFACTS

- `docs/DIFFERENTIAL_WORKING_VS_WHITE.md` — this document
- `docs/DIFFERENTIAL_WORKING_VS_WHITE.jsonl` — 11 rows × 27 fields (request §17 field set)
- `docs/DIFFERENTIAL_FIRST_DIVERGENCES.jsonl` — per-app divergence + category + evidence
- `docs/DIFFERENTIAL_EVIDENCE_INDEX.jsonl` — per-app artifact index (dirs, runs, artifacts)
- `run/diff366/stage_matrices.json` — full 27-row stage matrix per app
- `evidence/diff366/final/<name>_<pkg>/run{1,2,3}/` — run.log, screenshot.png/ppm,
  view_tree.json, trace.jsonl, trace_summary.json, lifecycle_trace.json, api_trace.json,
  crash.log, file_io.jsonl
- `run/diff366/hidden_sources/` — every source APK, hidden before its runs
- `scripts/diff366_fetch.py`, `diff366_screen.py`, `diff366_final.py`, `diff366_report.py` —
  the reproducible pipeline (12 candidates fetched, 12 screened, 11 canonicalized)

## 15. BLOCKERS / CONTINUATION

- 12/12 S115 candidates remain blank at HEAD — the five selected are representative, the other
  seven remain open population (their screen evidence: `evidence/diff366/screen/`).
- Chess regression root (start.onCreate NPE + RecyclerView never bound) is recorded but not
  fixed (diagnose-only mission); its RecyclerView-never-bound frontier joins continuation.
- The five generic fix candidates (§12) are the recommended next campaign, in leverage order.
