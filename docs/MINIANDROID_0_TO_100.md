# MINIANDROID 0→100 — MASTER ROADMAP

> **Canonical for the strategic 0→100 layer view** (S95-CTRL, 2026-09-25).
> Wave-level reconciled status stays canonical in
> [ROADMAP_STATUS.md](ROADMAP_STATUS.md); problem state lives in
> [TICKET_REGISTRY.json](TICKET_REGISTRY.json); per-title evidence lives in
> [ACHIEVEMENTS.md](ACHIEVEMENTS.md) +
> [canonical/registry.json](evidence/canonical/registry.json).
> **Nothing here is checked without evidence.** Incomplete items stay visible.
> Status vocabulary: `DONE / VERIFIED / IMPLEMENTED / TESTED / OBSERVED /
> PARTIAL / BLOCKED / PENDING / SUPERSEDED`.
> Evidence levels: E0 hypothesis · E1 source · E2 unit · E3 runtime trace ·
> E4 real APK · E5 deterministic repeated APK · E6 corpus fan-out
> ([TICKET_REGISTRY.json](TICKET_REGISTRY.json) `evidence_levels`).

## How to read this roadmap

Each layer lists **actionable semantic milestones** (never vague "implement X"
items), the current status **with its evidence level**, the exact tests that
guard it, the upstream source authority, and the open tickets. A milestone is
marked done only when a real APK or the zero-skip battery proves it at the
stated evidence level. New discovered issues are added, never hidden.

**Current overall position: ~52/100** — the APK→DEX→lifecycle→View→render→
input→state chain is proven on real APKs (E5/E6), with deep semantics open in
text shaping, media-at-APK-level, real networking, web, native and modern
runtime idioms.

---

## Layer 0–10 · FOUNDATION — container, manifest, resources

| # | Milestone | Status | Evidence | Tests | Source authority | Tickets |
|---|---|---|---|---|---|---|
| 0.1 | APK (ZIP) container parse | **DONE** | E4+ (every corpus run) | battery build/parse stages | AOSP ApkAssets | — |
| 0.2 | AndroidManifest.xml (AXML) parse | **DONE** | E4 | battery stages | platform_frameworks_base | — |
| 0.3 | resources.arsc (ARSC/string pools/configs) | **DONE** | E4 (resource-backed golden law) | helloworld_golden RESOURCE-BACKED check | AOSP Resources | — |
| 0.4 | AXML layout inflate (LayoutInflater) | **DONE** | E4 | battery + corpus | AOSP LayoutInflater | — |
| 0.5 | Resource qualifiers (density/locale/night) | **PARTIAL** | E4 partial (density laws L-S94-DENSITY-1/2) | s95_vector battery stage | AOSP AssetManager2 | GFX-004 |
| 0.6 | Vector / adaptive-icon drawables | **TESTED** (S95) | E4 (hotdeath FAIL→PASS) | s95_vector fixture (9 law checks) | AOSP VectorDrawable | — |
| 0.7 | Theme resolution chain (activity≻app≻framework) | **TESTED** (S95) | E4 (L-S95-DEFTHEME-1) | GATE H, helloworld re-derived golden | AOSP themes_material.xml (pinned SHA) | — |

## Layer 10–20 · DEX / EXECUTION

| # | Milestone | Status | Evidence | Tests | Source authority | Tickets |
|---|---|---|---|---|---|---|
| 10.1 | DEX parser + class resolver | **DONE** | E4/E6 | battery semantic stages | AOSP ART / libdexfile | — |
| 10.2 | Interpreter (invokes, arrays, boxing, exceptions) | **DONE** | E5/E6 | 96-stage semantic family; 21 ROOT-CAUSED-FIXED roots | AOSP ART interpreter | DEX-001 |
| 10.3 | invoke variants incl. range/3rc descriptor dispatch | **DONE** | E2/E5 | f102_range_ctor_overload_exact_dispatch | ART | — |
| 10.4 | Class init, method resolution, verification semantics | **PARTIAL** | E2 | per-root regressions | ART | DEX-001 |
| 10.5 | Reflection meta-laws (Class/isInstance/assignable) | **TESTED** | E2 | f103_* (3 checks) | libcore | DEX-002 |
| 10.6 | Modern runtime idioms (lambdas, default methods, Compose-era) | **PARTIAL** | E4 (dooz/Telegram L1 OBSERVED) | frontier triage pending | Kotlin codegen; ART reference | DEX-001, COMPOSE-001 |

## Layer 20–30 · JAVA/KOTLIN CORE

| # | Milestone | Status | Evidence | Tests | Source authority | Tickets |
|---|---|---|---|---|---|---|
| 20.1 | java.lang core (String/MUTF-8, Long compare bridge, boxing) | **DONE** | E2/E5 | MUTF-8 7/7; semantic long/cmp/conv 14 | libcore / OpenJDK | — |
| 20.2 | Collections + Deque family | **DONE** | E2 | F-NEW-165 family tests | OpenJDK | — |
| 20.3 | IO/file sandbox laws | **TESTED** | E4 (v139 real read chain) | F-104 regressions | libcore | — |
| 20.4 | Kotlin object model (data classes, lambdas, companions) | **PARTIAL** | E4 | corpus-dependent | Kotlin | DEX-001 |
| 20.5 | Concurrency primitives (locks/atomics shadows) | **PARTIAL** | E2 | shadows unit-level | OpenJDK / kotlinx.coroutines | CONC-001, CONC-002 |

## Layer 30–40 · ANDROID FRAMEWORK

| # | Milestone | Status | Evidence | Tests | Source authority | Tickets |
|---|---|---|---|---|---|---|
| 30.1 | Context / Application / Activity lifecycle | **DONE** | E4/E5 | lifecycle_controller + battery | AOSP ActivityThread | — |
| 30.2 | Intent + PendingIntent semantics | **TESTED** | E2 | pending_intent_shadow | AOSP | — |
| 30.3 | Fragment / FragmentActivity super-chain | **TESTED** | E4 | F-NEW-172 A/B | androidx fragment | — |
| 30.4 | Dialog family | **TESTED** | E3/E4 | s82_dialog_gate ×2 | AOSP | — |
| 30.5 | Choreographer / handler / postDelayed clock | **TESTED** | E5 (S95 animation refutation) | s95 determinism ×3 | AOSP Choreographer | — |
| 30.6 | SharedPreferences | **TESTED** | E4 | shared_prefs + getPreferences F-NEW-167 | AOSP | — |
| 30.7 | ViewConfiguration / Display family | **TESTED** | E4 | F-NEW-166/171 A/B | AOSP | — |

## Layer 40–50 · UI / LAYOUT

| # | Milestone | Status | Evidence | Tests | Source authority | Tickets |
|---|---|---|---|---|---|---|
| 40.1 | View/ViewGroup measure-layout-draw traversal | **DONE** | E5/E6 | battery goldens | AOSP View root | GFX-001 |
| 40.2 | FrameLayout / LinearLayout basic measure | **DONE** | E4/E5 | battery | AOSP | — |
| 40.3 | LinearLayout **weight** distribution | **ROOT_CAUSE_FOUND, open** | E4 (dodge panel ~1645px children) | fixture pending | AOSP LinearLayout.java | GFX-002 |
| 40.4 | Button minHeight/minWidth (Widget.Material 48/88dip) | **TESTED** (S95) | E4 (bobball 44→126 px) | helloworld golden re-derived | styles_material.xml (pinned) | — |
| 40.5 | Touch dispatch (per-child hit-test walk) | **TESTED** | E4 | R-NEW-399 HITPROBE | AOSP ViewPostImeInputStage | — |
| 40.6 | RecyclerView / ScrollView family | **PARTIAL** | E4 partial | corpus-dependent | androidx | — |
| 40.7 | Custom-view onDraw dispatch | **ROOT_CAUSE_FOUND, open** | E4 ([C013-ONDRAW] dispatched=NO) | simplestopwatch | AOSP View.draw | GFX-001 |

## Layer 50–60 · GRAPHICS / TEXT

| # | Milestone | Status | Evidence | Tests | Source authority | Tickets |
|---|---|---|---|---|---|---|
| 50.1 | Canvas/Paint/Bitmap software raster | **DONE** | E5/E6 | battery goldens; 3-run determinism | Skia reference | — |
| 50.2 | Clip stack / save-restore obedience | **TESTED** | E2/E4 | battery law tests (S95: no real clip divergence found) | SkCanvas | — |
| 50.3 | Density selection at decode | **TESTED** (S95) | E4 | s95_vector stage | AOSP BitmapFactory; glide Downsampler | — |
| 50.4 | Vector/adaptive/state-list drawables | **TESTED** (S95) | E4 (3 titles cleared of WRONG_COLOR) | s95_vector | AOSP VectorDrawable | — |
| 50.5 | NinePatch parse + stretch fidelity | **UNTESTED** | E0 | dedicated fixture pending | cdroid NinePatch; AOSP | GFX-004 |
| 50.6 | GIF disposal semantics 0–3 | **OBSERVED, open** | E4 partial (12 GIF titles) | Pillow/wuffs fixture port pending | wuffs; Pillow; go image/gif | GFX-003 |
| 50.7 | Shader / color-filter family | **UNTESTED** | E0 | fixture pending | Skia | GFX-006 |
| 50.8 | SurfaceView surface chain | **TESTED** | E4 (Dodge fully playable) | F-NEW-164..170 A/B | AOSP SurfaceView | — |
| 50.9 | Bitmap decode (PNG/JPEG/WebP) | **TESTED** | E4 | GATE H IoU pins; battery | libpng/libjpeg/libwebp | — |
| 51.1 | Latin text render (FreeType direct) | **DONE** | E5 | typography goldens EXT-01 | FreeType | — |
| 51.2 | Theme text color chain (textColorPrimary) | **TESTED** (S95) | E4 | GATE H re-earned | themes/colors material (pinned) | — |
| 51.3 | Complex-script shaping (HarfBuzz/Minikin) | **PARTIAL** | E2 (POC) — not wired | shaping gate pending | harfbuzz; minikin Layout.cpp | TEXT-001 |
| 51.4 | Bidi/RTL layout mirroring | **UNTESTED** | E0 | RTL fixture pending | fribidi | TEXT-002 |
| 51.5 | Glyph-truth verification (OCR-grade) | **OBSERVED, open** | E4 (urlchecker chevrons) | tamper battery stays red | tesseract | GFX-005 |

## Layer 60–70 · INPUT / ANIMATION / MEDIA

| # | Milestone | Status | Evidence | Tests | Source authority | Tickets |
|---|---|---|---|---|---|---|
| 60.1 | Click dispatch → state change (real DEX listeners) | **DONE** | E5/E6 | tictactoe_golden 9/9; 12 interactive titles | AOSP input pipeline | — |
| 60.2 | Long-press | **TESTED** | E4 | EXT-02 12/12 | AOSP | — |
| 60.3 | Animation machinery (postDelayed/invalidation) | **TESTED** (S95) | E5 (6/2 unique frames ×3, frozen claim refuted) | determinism runs | AOSP AnimationDrawable | — |
| 60.4 | AnimationDrawable per-frame timing | **UNTESTED** | E0 | CDroid cts port pending | AOSP AnimationDrawable | — |
| 60.5 | Audio state machines (MediaPlayer/SoundPool/AudioTrack) | **IMPLEMENTED, APK-level UNTESTED** | E2 | unit tests (audio_engine) | AOSP MediaPlayer.java | AUDIO-001, AUDIO-002 |
| 60.6 | Audio real codecs (mpg123/libsndfile) | **IMPLEMENTED, APK-level UNTESTED** | E2 | codec unit tests | mpg123; libsndfile | AUDIO-001 |
| 60.7 | Video decode + presentation | **UNKNOWN frontier** | E0 | — | Media3/ExoPlayer; ffmpeg | VIDEO-001, MEDIA-001 |

## Layer 70–80 · STORAGE / NETWORK

| # | Milestone | Status | Evidence | Tests | Source authority | Tickets |
|---|---|---|---|---|---|---|
| 70.1 | File sandbox (filesDir/external) | **DONE** | E4 | file_sandbox + F-104 | AOSP ContextImpl | — |
| 70.2 | SharedPreferences persistence | **DONE** | E4 | shared_prefs battery | AOSP | — |
| 70.3 | SQLite (Room law fixture) | **TESTED** | E2/E4 | F-026+F-027 battery stage | sqlite; androidx room | STORE-001 |
| 70.4 | SQLite transactions/locking depth | **UNTESTED** | E0 | sqlite corpus port pending | sqlite test corpus | STORE-001 |
| 71.1 | Network API **shadow tracking** (URL capture) | **DONE** (as instrument) | E3/E4 | android_shadows web_url record | — | — |
| 71.2 | **Real** HTTP(S) stack (DNS/TCP/TLS/redirect/timeout) | **OBSERVED gap — top P0** | E4 (no real socket; urlchecker core function shadowed) | curl conformance subset pending | curl; openssl; asio | NET-001 |
| 71.3 | INTERNET DIAGNOSTIC APK target | **PENDING** | E0 | per-stage self-report app | — | NET-002 |
| 71.4 | Chunked transfer / compression / proxies | **UNTESTED** | E0 | subsumed by NET-001 plan | curl | NET-001, NET-003 |

## Layer 80–90 · ANDROIDX / COMPOSE / NATIVE / WEB

| # | Milestone | Status | Evidence | Tests | Source authority | Tickets |
|---|---|---|---|---|---|---|
| 80.1 | AppCompat/FragmentActivity chains | **PARTIAL** | E4 | F-NEW-171..174 | androidx | — |
| 80.2 | Compose composition | **BLOCKED frontier** | E4 (dooz OBSERVED) | idiom triage | Compose runtime | COMPOSE-001, DEX-001 |
| 80.3 | JNI bridge + System.loadLibrary | **PARTIAL** | E2 | hello-JNI fixture pending | AOSP core/jni | JNI-001 |
| 80.4 | WebView callbacks | **UNTESTED** | E3 (loadUrl tracked) | callback-order fixture | AOSP WebView; AwContents | WEB-002 |
| 80.5 | SIMPLE BROWSER target (html+css-lite) | **PENDING** | E0 | reuse matrix first (litehtml/lexbor) | litehtml; lexbor; html5ever | WEB-001 |

## Layer 90–100 · REAL-WORLD COMPATIBILITY / CORPUS

| # | Milestone | Status | Evidence | Tests | Source authority | Tickets |
|---|---|---|---|---|---|---|
| 90.1 | Canonical corpus (148 titles: 87 games · 60 apps · 1 fixture) | **DONE** | E4/E5/E6 | verify_canonical_evidence | — | — |
| 90.2 | Content-verified tier (22 VERIFIED + 12 interactive GIF + candidates) | **DONE** | E5/E6 | ACHIEVEMENTS matrix | — | — |
| 90.3 | Failure-mapped frontier (8 titles root-caused S93→S95) | **DONE** (as map) | E4/E5 | GRAPHICS_SOURCE_LIBRARY_VALIDATION §3 | — | APP-0001/0002, GAME-0001..0006 |
| 90.4 | Predictive risk map (all subsystems) | **DONE** (S95-CTRL) | E0–E4 | RISK_REGISTER → tickets | — | all |
| 90.5 | Fan-out measurement loop (law → N APKs) | **OPERATIONAL** (S95: 1 law → 3 APKs cleared) | E6 | ROI record | — | — |
| 90.6 | External corpus growth (F-Droid families beyond current 148) | **PENDING** | E0 | registry downloader | — | — |

---

## Progress scorecard (evidence-derived)

- **Content-verified titles:** 22 VERIFIED + 5 candidate-visual/interactive +
  12 interactive-GIF (subset) — canonical registry is the single source.
- **Battery gate:** **99/99 ALL PASS** at HEAD `d5946533` (S95 final binary,
  re-verified this session after toolchain bootstrap + SHA-pinned fixture
  re-fetch).
- **Source-first infrastructure:** 127 registry entries / 122 distinct
  verified repos / 48 evidenced laws / 65 deep-inspected
  (GRAPHICS_SOURCE_REGISTRY).
- **Open problem state:** 33 canonical tickets (TICKET_REGISTRY.json): 1 P0
  (NET-001), 10 P1, 16 P2, 6 P3; statuses: 3 ROOT_CAUSE_FOUND, 7 PARTIAL,
  4 OBSERVED, 10 UNTESTED, 2 UNKNOWN, 1 BLOCKED, 2 PENDING, 4 CLOSED.

## Next strategic jumps (must follow measured fan-out, see MASTER_QUEUE)

1. **NET-001 real network stack** (P0) — unblocks urlchecker's core function
   and enables the NET-002 diagnostic instrument; highest cross-subsystem
   fan-out remaining.
2. **GFX-001 + GFX-002** (P1) — two named, root-caused measure/dispatch gaps
   with fixture-ready plans.
3. **WEB-001 simple-browser reuse matrix** (P1) — decision document before
   any browser code (litehtml vs lexbor vs html5ever).
4. **TEXT-001 shaping wire-up** (P1) — POC exists; wiring unblocks RTL/Indic.
