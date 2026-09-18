# ACHIEVEMENTS — Canonical Record of Real APK Executions

> **SINGLE SOURCE OF TRUTH.** Every real APK execution MiniAndroid has achieved,
> verified, or honestly failed is recorded HERE — one entry per application.
> Canonical by the S54 documentation law (README · ACHIEVEMENTS · ROADMAP_STATUS ·
> KNOWLEDGE_INDEX). Supersedes `docs/EXECUTION_ACHIEVEMENTS.md` (S52/S53 era),
> `SCREENSHOT_INDEX*.md`, and any per-app achievement files.
>
> Status vocabulary (canonical, unchanged): `VERIFIED / PARTIAL / BLOCKED /
> NOT_TESTED` over the four evidence states `LOCAL / REMOTE / REMOTE HISTORY /
> GITHUB ATTACHMENTS`. Nothing is upgraded without runtime evidence.

## 0. Reading this file

| Field | Meaning |
|---|---|
| App | application (corpus APK or in-repo fixture) |
| Version | APK version (versionName / vc) |
| APK SHA256 | full SHA256 of the exact artifact; `-16` = first 16 hex chars |
| Source | F-Droid / telegram.org / GitHub release / in-repo fixture |
| Runtime HEAD | commit the verdict was produced at |
| Result | SUCCESS / PARTIAL / BLOCKED / FAIL (+ honest one-line reason) |
| Ladder | L0 recognized → L1 manifest → L2 DEX → L3 lifecycle → L4 UI machinery → L5 meaningful frame → L6 real input → L7 input→state change → L8 multiple interactions → L9 app-specific behavior → L10 close/reopen persistence |
| Persistence | PERSISTENCE VERIFIED / NOT VERIFIED / PARTIAL / NOT TESTED |
| Screenshot | only real, recognizable UI; deterministic name, ≤100 KB JPG, SHA256 in `docs/evidence/s54_frames/SHA256SUMS` |
| ASC | what the ASC (Droid ASC, MG1937/ASC) reconnaissance added |
| Root cause | registry ID (R-NEW-xxx) or engine law ID (F-xxx) when known |
| Next action | the concrete next step |

Reproduce any run: `./build/miniandroid run <apk> -o <dir> [--click-test]` at the
recorded HEAD (battery gate: `bash scripts/test/run_test_battery.sh` →
"BATTERY GATE: ALL PASS (96 stages)").

**Screenshot gate law (S54 refinement, binding).** A frame is BLANK when
`(near-white ≥ 97% or near-black ≥ 97%) AND colors ≤ 8`, or when `colors ≤ 8`
(renderer artifact class). A near-black frame with `colors > 8` is
DARK-CONTENT — real dark-themed UI — and may be stored only with an
independent content check (e.g. the battery EXT-01 typography golden).
The refinement strictly narrows S53's false-reject class: every S53
rejection (chessclock 2 colors, notes 5 colors) remains a rejection; the
only rescued class is dark UI with rich palettes (helloworld_ext01, 256
colors). Blank/white/black frames are NEVER stored as images — they are
recorded as text, exactly as done in §3.2.

## 1. Master matrix — current-HEAD verdicts

Verdicts at HEAD `8c575f71` + F-080/F-081 (S54) unless marked **[S53]**
(HEAD ef569eda+). All 25 corpus rows re-audited at S54; five interactive
apps re-RUN with fresh screenshot pairs (9/9 JPGs byte-identical to the
S53 gallery before the F-080/F-081 engine fixes — deterministic replay
across HEADs proven; gmdice/chessclock re-captured after the fixes as the
fixes legitimately change their frames).

| # | App | Version | APK SHA256-16 | Source | Result | Ladder | Persistence |
|---|-----|---------|---------------|--------|--------|--------|-------------|
| 1 | Chess Clock | 2.11.2 (vc29) | `5ca6f2c54c05efe7` | F-Droid | **SUCCESS — L7** **[S54 UPGRADE]**: real clock face restored by F-080+F-081; P1/P2 panels, active-player accent; click → active-player switch (80,289 px) | L4 → **L7** | PARTIAL (prefs round-trip [S52]) |
| 2 | uNote | 30 | `be91103f0e7db443` | F-Droid | **SUCCESS [S56 UPGRADE]**: main-menu input chain PROVEN — R-NEW-368 premise REFUTED (old probe grid never covered the bottom-44px button band y=1876..1920); canonical tap (270,1898) → DOWN consumed (target=13 Add note) → UP click → app's own addNote → startActivity **NoteEdition** launched | L5; **L6 input→navigation PROVEN** (persistence ladder next) | PARTIAL (notes.db round-trip; editor input pending) |
| 3 | Bouncy (ball) | 39 | (registry) | F-Droid | **SUCCESS** (S51 era; APK not re-fetched at S53 — corpus SHA mismatch) | L5 (frame `4219c511…`) | NOT TESTED |
| 4 | Heading Calculator | 1 | `274ec873098eea51` | F-Droid | **SUCCESS — L7**: full keypad UI; digit click → display text changes | L5→**L7** | NOT TESTED |
| 5 | Notes (billthefarmer) | 139 | `82cf8bc44c163748` | F-Droid | **SUCCESS — L7 [S55 UPGRADE]**: F-082 restores the ViewSwitcher read↔edit state machine — FAB click → face swap (2,057,718 px, 99.23%); note CONTENT stays blank-class (read face = MarkdownView **extends WebView** — R-NEW-377 next dep) | L4 → **L7** (content face blocked) | NOT TESTED |
| 6 | MicroTimer | 8 | `79c6f730f64886e7` | F-Droid | **SUCCESS — L7**: keypad UI; click → `00:00:00` timer display appears | L5→**L7** | NOT TESTED |
| 7 | Simple Stopwatch | 26 | `b3ec1a5ec24ce53b` | F-Droid | **SUCCESS — L7**: Start/Delay → **Stop/Lap** running-state transition | L5→**L7** | NOT TESTED |
| 8 | GM Dice | 8 | `1621eda11b5dbc0c` | F-Droid | **SUCCESS — L7/L9-quality**: 8/8 clicks state-changed; dialog roll rendered (1.85 M px); post-F-081 base additionally renders the result label | L5→**L7 + app-specific semantic result** | NOT TESTED |
| 9 | Simple Keyboard | 145 | `d83060833dc2bc97` | F-Droid | SUCCESS (entry screen — IME, no launch UI) | L5 (entry class `eb16ab5c…`) | NOT TESTED |
| 10 | RTTT (kirkezz) | 1.3 (vc3) | `704fa51869ad7ff4` | F-Droid | SUCCESS (entry screen; Compose frontier) | L5 (entry class) | NOT TESTED |
| 11 | Dooz v18 | 18 | `d81292cd346dcb23` | F-Droid | **PARTIAL [S55]** — R-NEW-361 **ROOT-CAUSED + FIXED (F-083)**: ScatterMap ghost-metadata probe spin eliminated (HALT-LOOP gone; MainActivity.onStart/onResume dispatched for the first time); new frontier **R-NEW-376** pinned (post-F-083 ctor-climb exceeds the 2048-frame budget) | L3 → L4-in-progress (composition runs, first frame not yet reached) | NOT TESTED |
| 12 | Dooz v23 | 23 | `299eab21ac8b3c61` | F-Droid | **PARTIAL [S57]** — R-NEW-344 **ROOT-CAUSED + FIXED (F-086 Long.compare bridge law)**: the ScatterMap second-grow decision no longer falls into the cleanup-instead-of-resize branch; capacity 7→15→31 proven at the runtime boundary (docs/evidence/s57_dooz23/); NO probe spin, NO fabricated returns; run advances into **R-NEW-376** ctor-climb (v18+v23 same family) | L4 (composition runs; first frame not yet reached — R-NEW-376) | NOT TESTED |
| 13 | TicTacToe (emmanuelmess) | 3 | `760fe5acf7b39435` | F-Droid | PARTIAL — blank first frame | L4 (blank class) | NOT TESTED |
| 14 | Telegram v12 | 12.10.1 (vc70389) | `f5e1192725772960` | telegram.org | **PARTIAL** — 540 s inside real init, no frame yet | L3-attempt (init depth) | NOT TESTED |
| 15 | WhatsApp | — | **NO APK** (0-byte placeholder) | — | **BLOCKED — APK unavailable** | — | — |
| 16 | Stopwatch (muellerma) | 6 | `3b6a10c8dc8ddc72` | F-Droid | PARTIAL — manifest has NO launchable Activity (QuickSettings Tile app) | L2 (by design) | — |
| 17 | BGClock | 2 | `72c140b0083ef273` | F-Droid | PARTIAL — WebView root (clock face is HTML/JS) | L4-minus (frame `2f85dd74…`) | NOT TESTED |
| 18 | TicTacToe (itsfrz) | 1.0.5 (vc5) | `2a057a9a519acd81` | F-Droid | PARTIAL — NPE at app boundary | L3 | NOT TESTED |
| 19 | Privacy Friendly Dicer | 2.0.0 (vc101) | `f2b4d3f021c3a620` | F-Droid | PARTIAL — ISE at app boundary | L3 | NOT TESTED |
| 20 | OpenLauncher | 39 | `b3320463a7a1ed46` | F-Droid | PARTIAL — heavy launcher, default screen | L5 (entry class) | NOT TESTED |
| 21 | Simple Flashlight | 66 | (corpus) | F-Droid | PARTIAL — app-boundary, default screen | L5 (entry class) | NOT TESTED |
| 22 | Antimine | 17.6.3 F | `e7b635b6629bc5b0` | F-Droid | PARTIAL — killed at 300 s; reaches MainActivity.onCreate | L3-attempt | NOT TESTED |
| 23 | Secuso Memory / Sudoku | 8 / 19 | (corpus) | F-Droid | PARTIAL — >300 s each, killed | L3-attempt | NOT TESTED |
| 24 | Secuso 2048 / Lexica | 1.4.2 / 3.13.1 | `02c799d3d582669d` / `255d26352ab1247c` | F-Droid | NOT re-run — historical EXEC BUDGET TIMEOUT (540 s heavy) | L3-attempt | NOT TESTED |
| 25 | s36/s37 game corpus (solitaire, braincup, minesweepers ×3, word game, puzzle, dice overflow, roll, game2048, yahtzee dicer, droidify) | various | (corpus) | F-Droid | NOT re-run this session — era records stand | era records | NOT TESTED |
| 26 | Tiny Music Player | 1.0 | `d7bcb24d101b04be` | F-Droid | era record (campaign014) | era record | NOT TESTED |
| 27 | TicTacToe Classic (palahsu) | ? | `752852c94c980788…` | legacy cache | **BLOCKED — APK unavailable** (cache lost; F-Droid `com.palahsu.ttt` NOT_FOUND at S54); historical S37 full-render + S44 playable record stands at its recorded HEADs | era: L9 | — |

**Count summary (S57, HEAD 28b644b7+F-086):** SUCCESS with real recognizable
GUI **6** (Chess Clock, GM Dice, MicroTimer, Simple Stopwatch, Heading
Calculator, uNote) + **Notes upgraded to L7 mode-switch** (content face still
blank-class — WebView end-to-end probe pinned) — **6 with proven input→state-change
screenshot pairs** (GM Dice additionally renders the app-specific dice-roll
result) · entry-class 2 · PARTIAL 13 · BLOCKED 2 (WhatsApp no APK; TicTacToe
Classic no APK) · persistence storage-round-trip verified 2 · S57 corpus
gate re-run at F-086 HEAD: chessclock 2,040,736 nb, notes 2,073,600 nb,
unote 236,520 nb (run/s57_corpus).

## 2. In-repo fixture achievements (strongest ladder proofs)

| Fixture | What is proven | Ladder | Evidence |
|---|---|---|---|
| **tictactoe_golden** | 9 scripted taps, X→O→X chain, **win state detected**, pixel-deterministic replay | **L9** | battery §29 ("tictactoe_golden PASS, interaction 9/9") |
| **helloworld_golden** | 18-check golden render (typography, density) | L5 | battery §28 |
| **hello_widgets** | most advanced View-world render: ImageView drawable + EditText + Button + TableLayout 3 rows + RelativeLayout layout_below (2,059,104 non-white px golden) | L5 | S38/S39 records |
| **hello_smoke** | click → setText state change under LinearLayout | L7 | S38 record |
| **s38_shift_law** | androidx.collection ScatterMap long-arithmetic law probe (7 laws, 26 checks) | law probe | S38 record |
| EXT-01/02 HelloWorldSelfAware | external APK re-fetched + SHA-verified (`009b4671…`), typography 9/9 + interaction 12/12 checks | L7 | battery G48 stages; §3.0 card |
| density_matrix / G06-G08 / M3 chain | toolchain fixtures, 3-run determinism, ARSC/style chain | — | battery 94/94 |
| F-0xx law chain | F-012/016/020/024/025/026/027/028/030/040/044/050/074/**080**/**081** | — | battery 94/94 |

## 3. Per-app detail cards

### 3.0 HelloWorld — canonical control target (S54)

**HelloWorldSelfAware** `com.appliberated.helloworldselfaware` v1.1.0 · APK
SHA256 `009b467109c4d48d…` (full-sha verified on fetch) · GitHub release
(Appliberated, MIT) · Runtime HEAD `8c575f71` (S54)
- Chain (all stages evidence-logged in the run): APK ZIP parse →
  AndroidManifest.xml (AXML) → resources.arsc + res/ → resource resolution →
  classes.dex load → real Dalvik execution → Activity creation → lifecycle
  onCreate→onStart→onResume → setContentView → View construction → measure →
  layout → draw (Canvas/text/background) → framebuffer screenshot.
- Visual proof: **`docs/evidence/s54_frames/helloworld_ext01_base.jpg`** — the
  app's real text UI rendered on its dark theme ("hello world" + the
  app-computed device hash "i'm 6f1c3a9d2e5b4780" + version lines). The frame
  is DARK-CONTENT (98.7% near-black, 256 colors) and passes the refined gate
  with the battery EXT-01 typography golden (9/9 static checks vs the upstream
  phone screenshot) as its independent content check.
- Interaction: EXT-02 long-press → 12/12 interaction checks (real dispatch into
  the app's DEX handlers, per-frame SHAs in manifest.json).
- Reproducibility: battery re-run 3× this session — ALL PASS.
- Known limitations: none recorded for this app at this HEAD.

### 3.1 SUCCESS — full render + input→state-change

**GM Dice** `de.duenndns.gmdice` v8 · APK SHA256 `1621eda11b5dbc0c…` · F-Droid ·
Runtime HEAD `8c575f71`+F-080/F-081 (S54)
- Lifecycle: launch→RESUMED, rc=0.
- UI [gate PASS]: real dice UI — dialog, "Push buttons to roll!",
  "Long-press buttons to configure dice.", dice bar `1d20 / 1d6 / 1d6+4`,
  and (new at S54, post-F-081) the rendered result label at base.
- Input→state change: `--click-test` 8/8 state_changed; most-changed frame
  renders the dialog roll (1,853,871 px delta). Deterministic: identical
  roll values `14 · 15 · 15` reproduced across S53→S54 HEADs.
- Semantic result: dice values produced by app logic and rendered — the
  strongest corpus-app record in this ledger (L7 chain + app-specific result).
- Screenshots: `s54_frames/gmdice_base.jpg` + `gmdice_after.jpg` (SHA256 +
  gate numbers in `s54_frames/SHA256SUMS`; the S53-era frames were
  byte-identical JPGs before the fixes — cross-HEAD determinism proven).
- Next: persistence (roll state across close/reopen) → L10.

**Chess Clock** `com.chessclock.android` v2.11.2 (vc29) · APK SHA256
`5ca6f2c54c05efe7…` · F-Droid · Runtime HEAD `8c575f71`+F-080/F-081 (S54)
- **[S54 UPGRADE — RENDER_ONLY → SUCCESS/L7.]** The S53 downgrade stood on a
  real defect, and S54 root-caused and fixed it with TWO generic shared-layer
  laws (no app-specific code):
  - **F-080 — Resources.getColor two-arg overload arg-mapping.** The app's
    `color()` helper compiles to `invoke-virtual {recv, resid, theme}` with
    `const/4 theme=0 (null)`; the shadow read a fixed slot and resolved the
    NULL THEME as the resid (`getColor resid=0x0` → black) — black text +
    black buttons on black panels = the "2-color dark blank". Fix: the resid
    is the FIRST int-typed argument (receiver/Theme are references) —
    robust under both receiver conventions. Evidence: `[RES] getColor
    resid=0x7f050005 -> 0xff499ebd` (real ARSC color) after the fix; frame
    went 99.3% near-black/2 colors → 187 colors.
  - **F-081 — M3-19 active-cycle key overload-distinct.** The app's
    `formatTime(J Z)` legally delegates to the `formatTime(J)` overload
    inside its own active window; the name-only cycle key stubbed the
    nested overload to null → the clock text was the literal "null".
    Fix: include the method descriptor in the active-invoke key (JVM/ART
    method identity is (name, descriptor)-exact). Evidence: `setText
    text="10:00"` ×2 after the fix; 0 cycle stubs.
- Visual proof: `s54_frames/chessclock_base.jpg` — the REAL clock face: P1
  "10:00" dimmed (inactive), P2 "10:00" white with the blue active accent
  (`0xff499ebd`), divider, dark theme.
- Input→state change: `--click-test` probed=8 state_changed=3; the
  most-changed frame (`chessclock_after.jpg`, 80,289 px) shows the
  active-player SWITCH — P1 becomes active (white + accent), P2 dims.
  The S52 "tap delta sub-perceptual" observation is superseded: the
  sub-perceptual delta was the blank-class frame, not the app.
- Persistence [S52]: `shared_prefs/default.xml` round-trips (storage-class
  evidence; full L10 ladder now unblocked).
- ASC [S52]: manifest decode 294 ms (`.ChessClock` launcher, minSdk 21/target
  25) + `getclass` (BRONSTEIN/FISCHER delay modes, P1/P2 click handlers).
- Next: L10 persistence ladder (start a clock → close → reopen → state kept).

**MicroTimer** — L7 re-verified at S54 (fresh run): click → `00:00:00` display
appears (31,863 px, frame byte-identical to S53). `s54_frames/microtimer_*.jpg`.

**Simple Stopwatch** — L7 re-verified at S54: Start → Stop/Lap running-state
transition (40,915 px, byte-identical to S53). `s54_frames/simplestopwatch_*.jpg`.

**Heading Calculator** — L7 re-verified at S54: digit click → display value
changes (1,389 px, byte-identical to S53). `s54_frames/headingcalculator_*.jpg`.

**uNote** — [S56: R-NEW-368 premise refuted; L6 input→navigation PROVEN]

S56 HEAD (F-084/F-085). The S52-era verdict "buttons unreachable for input"
was a PROBE-GRID artifact: the 16 probes (y ∈ 300..1780) never covered the
bottom-44px band where the main-menu buttons actually live (EXP092-RENDER:
node 13 Add note at (0,1876) 360×44, node 14 Search (360,1876), node 15
Quit (720,1876); the LinearLayout row is node 12 at (0,1876) 1080×44).
Paint rect == touch rect — no geometry-law divergence existed.

Proof (`--tap 270,1898`):
- `[G06-TAP] DOWN (270,1898) target=13 consumed=1` — canonical hit-test
  + consume on the Add note button.
- `[G06-TAP] UP click_posted=1` — UP posted the click.
- The app's own `NoteMain.addNote` ran → `startActivity →
  Lapp/varlorg/unote/NoteEdition;` — the editor activity was launched and
  its onCreate dispatched (its own calls logged).

That is the L6 input→state→navigation chain for uNote's main menu. Next
ladder rung: NoteEdition input + the notes.db persistence round-trip.

Historical (S54): uNote L5 re-verified at S54 (byte-identical): real list UI (417 colors);
2/4 small click changes (max 2,011 px); input BLOCKED by **R-NEW-368**
(paint vs touch-hit geometry divergence; 16-probe grid found no target) —
honestly not called interactive. Persistence [S52]: notes.db round-trips.
`s54_frames/unote_base.jpg`.

**Bouncy (ball)** v39 — SUCCESS rc=0 full render at HEAD `1b37afd1`
(deterministic frame `4219c511…`, s51_audit era). The F-Droid re-fetch at S53
does NOT match the original corpus SHA — no new verdict recorded. NOT stored
in the S54 gallery (era evidence).

### 3.2 RENDER_ONLY / downgraded — open roots

**Notes (billthefarmer) — [S55 UPGRADE: RENDER_ONLY → L7 mode-switch; content
face still blank-class.]** v139 · APK SHA256 `82cf8bc44c163748…` · F-Droid ·
Runtime HEAD 646952b6 + F-082/F-083 (S55)
- **S55 tree forensics REFUTE the S53 "ListView item paint" hypothesis:** the
  v139 main layout has NO ListView. `U007-INFLATE` inflates 7 views, 0
  unresolved: FrameLayout → ViewSwitcher [ScrollView+EditText (edit face) |
  MarkdownView (read face)] + FAB ViewSwitcher [2× ImageButton].
- **F-082 (generic AOSP ViewAnimator law)** — `setDisplayedChild/
  getDisplayedChild/showNext/showPrevious` were REC-MISS silent no-ops;
  now implemented on the ViewShadow node model (clamp + showOnly visibility
  walk + requestLayout). Regression: `tests/view_animator_law_test.cpp`
  18 checks ALL PASS (battery stage "F-082 ViewAnimator law").
- Runtime proof: `--click-test` FAB → `animateAccept` → `setDisplayedChild`
  → face swap = **2,057,718 px delta (99.23% of frame)**, probed=3
  state_changed=1 (was 0/3 at S53). Frames byte-identical across two runs
  (`docs/evidence/s55_notes_v2/SHA256SUMS`: cf521b16… / ae697935…;
  census + deltas in census_delta.json).
- **Content face root cause PROVEN (R-NEW-377):** the read face is
  `Lorg.billthefarmer.markdown.MarkdownView;` which **extends
  `Landroid/webkit/WebView;`** (verified by the runtime's own dex parser).
  `getSettings/setWebViewClient` REC-MISS → the markdown load pipeline
  never starts → honest inline placeholder (C013-CUSTOMVIEW). Editor face
  (ScrollView+EditText) inflates, measures, renders; fresh data dir =
  empty note is CORRECT behavior.
- Next dependency (pinned, P1 shared framework): a generic WebView content
  model. App-specific markdown rendering is forbidden by the campaign scope
  laws (§25-family). Screenshot: NONE stored for the content face (blank
  class, per policy); the mode-switch pair is recorded as SHA256 + census
  text only (both frames blank-class).

### 3.3 PARTIAL — open roots (the honest frontier)

**Dooz v18** — **[S55: R-NEW-361 ROOT-CAUSED + FIXED by F-083; new frontier
R-NEW-376 pinned.]** The v18 face (HALT-LOOP `Lh/r;.c` → aput-oob) was
DOWNSTREAM of the real defect: the 56th `Ln/a;.r` (Kotlin LongArray-fill
helper) invocation entered `try_recursive_invoke` at depth=80 ==
MAX_RECURSION_DEPTH and was silently dropped (EXP-053 law: ~80KB C++ stack
per DEX frame → 80-frame cap under the 8MB process stack). The dropped void
initializer left map o5051's metadata at heap-zero; the subsequent sentinel
write produced ghost bytes (`0xff007f6600000000`, zero EMPTY 0x80 —
[R361-STORE] traces) → the findImpl probe never terminates. **F-083**
(generic): cmd_run executes on a dedicated 1GB-virtual-stack thread;
MAX_RECURSION_DEPTH 80 → 2048; the limit-drop is ALWAYS loud
([RECURSION-LIMIT] stderr). Post-fix: no HALT-LOOP, no aput-oob, metadata
init correct (`0xff80808080808080` on healthy maps),
MainActivity.onStart/onResume dispatched for the FIRST time in campaign
history. Key traces: `docs/evidence/s55_dooz/` (SHA256SUMS). New frontier
**R-NEW-376**: Compose init ctor chains exceed the 2048-frame budget
(9 cap-climbs; j0/t0/E0 hop evidence captured) — next steps ranked in the
registry entry.

**Dooz v23** — PARTIAL: deterministic pipeline completion; first frame = blank
Compose class `31ddd4d5…` (×4+ runs). Root **R-NEW-344** (Recomposer suspends
without re-posting frame callback). Blank frame is NOT an achievement.

**Telegram v12** — PARTIAL: 540 s inside real init (989k log lines, SafeIterableMap
cycle-stub, 400 REC-MISS), no frame. ASC startup card ranks: REC-MISS
static-init surface → SafeIterableMap iterator law → NativeLoader boundary.

**WhatsApp** — **BLOCKED — APK unavailable** (0-byte placeholder proven; no
unauthorized acquisition per §30). Historical u011_3 probe stands at its HEAD.

**TicTacToe (emmanuelmess)** — blank first frame (Compose/libGDX family).
**BGClock** — WebView root boundary. **muellerma Stopwatch** — no launchable
Activity (L2 by design). **itsfrz TicTacToe / Privacy Friendly Dicer** — app
boundary. **Antimine / Secuso memory / sudoku** — >300 s kills. **TicTacToe
Classic (palahsu)** — APK lost with legacy cache, F-Droid NOT_FOUND (S54);
historical S37 full-render + S44 fully-playable records stand at their
recorded HEADs; re-verification BLOCKED until the APK is re-obtained.

## 4. Persistence testing (S52 experiment, section-14 protocol)

Method: two runs with the SAME `--data-root`; compare data-root tree + frames.
Both S52-tested apps were blank-class then, so these are storage-layer
round-trip proofs only. With ChessClock now L7, the full state-delta ladder
is unblocked and scheduled.

| App | data-root artifact | Survives reopen? | State delta observable? | Verdict |
|---|---|---|---|---|
| Chess Clock | `com.chessclock.android/shared_prefs/default.xml` | YES | no (tap state in-memory by design) | **PARTIAL** — storage round-trip VERIFIED |
| uNote | `app.varlorg.unote/databases/notes.db` | YES | no — input blocked (R-NEW-368) | **PARTIAL** — storage round-trip VERIFIED |

## 5. ASC reconnaissance ledger (S52, unchanged)

Tool: **Droid ASC (MG1937/ASC)** v0.1.1.post1 @ `3279d9dd…`, LOCAL venv
(gitignored). Reconnaissance helper ONLY — never a substitute for runtime
evidence; no ASC output committed; claims cross-checked at runtime.

| Query | Target | Time | Outcome |
|---|---|---|---|
| `getmanifest` | chessclock vc29 | 0.29 s | launcher + Prefs + sdk levels |
| `listclass`/`getclass` | chessclock | ms | fields/handlers recon |
| `findrefs` | chessclock | ms | ref-search semantics validated |
| `getmanifest` | Telegram v12 (73 MB) | 0.32 s | ApplicationLoaderImpl + LaunchActivity |
| `getclass` ×2 | ApplicationLoader(+Impl) | s | full startup-path law list |
| `findrefs type` | SafeIterableMap | s | LiveData/SavedStateRegistry consumers |
| `getclass` | Dooz18 `Lh/r;` | s | ScatterMap.set loop → R-NEW-361 candidates |
| `getmanifest` | WhatsApp placeholder | — | exposed 0-byte file → BLOCKED provable |

S54 added: bytecode-level disassembly (androguard probe, saved as
`scripts/forensic/s54_chessclock_disasm.py`) of `ChessClock.color` /
`formatTime` — this is what pinned F-080/F-081 to exact DEX shapes.
Compact cards: `docs/evidence/s52_asc/`. Raw decompiled files stay
LOCAL-ONLY.

## 6. Screenshot policy (binding)

A screenshot may be committed only if: real recognizable UI · proves something
text alone cannot · linked to an entry above · SHA256 recorded · deterministic
name · ≤100 KB JPG · **passes the gate** (§0 refined law; checker
`scripts/s54_image_audit.py`, gallery emit `scripts/s54_gallery_emit.py`).

**Canonical gallery: `docs/evidence/s54_frames/`** (12 gate-passing JPGs +
`SHA256SUMS` with per-file gate numbers; REJECTED section records the
blank-class refusals). Era galleries: `s53_frames/` (9 JPGs, superseded by
this file but kept for provenance — 9/9 byte-identical JPGs were re-produced
at S54 pre-fix, proving cross-HEAD determinism), `s51_audit/` (6 meaningful
era JPGs). No gallery is generated for its own sake.

## 7. Historical records (superseded pointers)

- `docs/EXECUTION_ACHIEVEMENTS.md` — S52/S53 canonical; absorbed HERE at S54.
- `docs/evidence/SCREENSHOT_INDEX_S51.md`, `SCREENSHOT_INDEX*.md` — era records.
- `docs/history/campaign-reports/`, `docs/evidence/{campaign014,MASTER4…}` —
  era evidence. **Divergent-lineage caution (S54):** campaign reports dated
  Sep 9–15 reference HEADs (`8de5382b`, `d202e43d`, `12cf043f`, `4931f8a4`,
  `7dc70e9c`, `f60634e4`, `e2e91928`) that are NOT objects in this
  repository — those sessions ran in divergent workspaces. Any claim sourced
  ONLY from those reports is treated as unverified here unless independently
  re-proven at a canonical HEAD. (The equivalent laws F-028/F-028h/F-029
  exist in this lineage via `52e4a5c5`.)
- `docs/achievements/*.png` (untracked residue): the gate rejected
  `chessclock_rendered.png` (SHA-16 `e4a2d7c90cd2fd26` = the EXACT S53
  blank-class frame — an old "achievement" image that was actually the
  blank frame; refusal recorded). The remaining 7 PNGs have no provenance
  chain in this repo and are not presented as achievements.
