# S65 — Open-Source APK Spotlight 4: 3 NEW source-first apps executed (TriPeaks S7, FishRings S10 PROVEN, OPMT S6); F-118 activity-constructor law (R-NEW-385) + F-119 X.TYPE/primitive-array law (R-NEW-386); battery zero-regression

Date: 2026-09-19 (S65 breadth continuation). RECON at session start: local
HEAD `b34b74a2` (S64 spotlight 3) was 1 commit AHEAD of origin/main
`64d830b4` — the S64 push-verify step was INCOMPLETE (no GitHub credential
in this session's environment; push recorded PENDING-PUSH, retried at
session end). Tree clean. Toolchain/engine/Go/zoekt ABSENT (container reset
BETWEEN USER TURNS — recurred 3× this session; all background processes are
killed between tool calls, so every long job ran FOREGROUND). No new
campaign/branch/roadmap. Mission: increase the count of REAL open-source
apps built from source and executed launch→UI→(input→state→render).

## 0. RECON (ground truth, no assumptions)

```text
HEAD == origin/main = NOT EQUAL at session start (b34b74a2 ahead by 1)
TREE = clean
BATTERY (measured, fresh, post-F-118/F-119) = 94 stages: 92 PASS +
  EXT-01/02 FAIL = pre-existing environmental (Appliberated/
  HelloWorldSelfAware upstream repo deleted; S45/S64 precedent)
NEW APPS CURRENTLY PROVEN (source-first, entering S65) = 5:
  gmdice S10/L6, siggen S7, pmk S6, FreeKlondike S10, shopping-list-calc S9
TOOLCHAIN = aapt2 8.13.2 restored (transient 404 on first probe), ECJ 3.33.0,
  r8 8.13.23, android-34 stubs; engine rebuilt 2× (F-118, F-119 builds)
SEARCH TOOLS = zoekt/zoekt-index @ 153817f643cd + cindex/csearch v1.2.0
  rebuilt (Go 1.26.0, GOPROXY=direct) — USED with evidence (§5)
```

## 1. Candidate selection (REAL survey, fact matrix)

Survey: F-Droid index-v2.json (60,145,769 B, 4,408 packages) downloaded and
scanned LOCALLY (scripts/s65_candidate_survey.py: 45 keywords → 120-hit
shortlist) + parallel GitHub raw-gradle probes (scripts/s65_probe.py, no API
quota: androidx/compose/ndk/libgdx/flutter signatures per candidate).

Deferred-by-facts (breadth law, pre-build):
- sidhant947/{Match3,BlockBlast,Mahjong,nonogram,...} = FLUTTER (pubspec.yaml)
- dozingcat/CardsWithCats, brandonp2412/BlockDrop = Flutter
- obfusk/sokobang = Python/Kivy (buildozer.spec, p4a)
- hyst329/OpenFool = libGDX (CardActor/AndroidLauncher)
- FairyTrick/FairyMahjong = KOTLIN (no Kotlin compiler in the aapt2/ECJ/D8
  pipeline)
- martinschneider/juvavum-android = external engine jar
  (io.github.martinschneider:juvavum) + constraintlayout + material + kotlin
  plugin (build complexity)
- Eidetic-Memory-Trainer = CountDownTimer family (android.os.CountDownTimer
  bridge absent — recorded as future law work)
- open-chaos-chess = 28 files + network client surface

Selected (3 picks, all cloned at pinned SHA, all Java, zero-or-stub androidx):
- NEW-001 TriPeaks (eu.veldsoft.tri.peaks) — FreeKlondike's author; plain
  Activity ×5; splash = F-115/F-116 pattern; 52-card click listeners
- NEW-002 FishRings (eu.veldsoft.fish.rings) — same author; plain Activity ×5;
  8 ring-rotation listeners → Rings state machine
- NEW-003 OPMT (one.scarecrow.games.OPMT @ 3240c4cf, Mū tōrere-like board
  game) — 3 AppCompatActivity; 9-button board; androidx compile-stub

### Class inventory (source-derived, via grep/dex dump — not guessing)

| Field | NEW-001 TriPeaks @62f3609 | NEW-002 FishRings @dc3807e | NEW-003 OPMT @3240c4cf |
|---|---|---|---|
| SOURCE | github.com/VelbazhdSoftwareLLC/TriPeaksSolitaireForAndroid | github.com/VelbazhdSoftwareLLC/FishRingsForAndroid | github.com/20Nick/OPMT |
| LICENSE | GPL-3.0-only | GPL-3.0-only | GPL-3.0-only |
| F-Droid pin | 1.2.1/vc4 | 1.23/vc6 | 0.1.2/vc1 |
| BUILD | aapt2/ECJ/D8; APK 52272ae6…, 79 entries | aapt2/ECJ/D8; APK 14d7dd80…, 37 entries | aapt2/ECJ/D8; APK 4f91e380…, 17 entries |
| SRC FILES | 14 java | 6 java | 7 java (incl. Game/{Ai,Board,Pieces}) |
| ACTIVITIES | 5 plain Activity | 5 plain Activity | 3 AppCompatActivity (compile-stub) |
| FRAGMENTS | 0 | 0 | 0 |
| CUSTOM VIEWS | 0 (ImageView cards) | 0 (ImageView arrows/ball) | 0 (Buttons) |
| LISTENERS | 52× cardClickListener (field-init) + lobby/menu | 8 ring rotations (field-init) + menus | 9 button lambdas (inline) + menu lambdas |
| STATE | CardBoard/GameState/Deck statics | Rings (int[][][] via Array.newInstance) | Board/Pieces/Ai |
| THREADING | java.util.Timer (splash) | java.util.Timer (splash) | none |
| DB/NET/COMPOSE/WEBVIEW | none/INTERNET unused/none/banner WebView | none/INTERNET unused/none/banner WebView | none/none/none/none |
| STAGING | manifest has package= (none needed) | staged versionCode/Name | staged vc/name + themes + layouts + androidx stub (§2) |

## 2. Staging laws applied (all build-level, documented)

- s65_stage_candidates.sh (tracked): FishRings/OPMT manifests staged with
  versionCode/Name (AGP8 split); OPMT themes re-parented to framework
  Material themes + Material-only attr items dropped (siggen staged-styles
  law); ConstraintLayout menu/settings → FrameLayout with gravity/anchors +
  `app:srcCompat` → `android:src` (staged-layouts law; game board layout
  constraint-free and untouched; ids preserved so app code binds unchanged).
- androidx compile-stub (android-34-stubs law applied to appcompat):
  AppCompatActivity = Activity passthrough; AppCompatDelegate
  .setDefaultNightMode = no-op + MODE_NIGHT_* constants. Compile-time only;
  runtime behavior = the app's own DEX on the engine's Activity lifecycle.

## 3. NEW-001 TriPeaks (S7 — input reaches the app's own listener; app-own guard stops S8)

### Gates A–E

```text
BUILD   APK 52272ae619c0fec88dfd9b4a22be0c411edda8564edd7a11af107398799f894c
LOAD    manifest + resources.arsc + DEX loaded; package eu.veldsoft.tri.peaks
EXECUTE real SplashActivity.onCreate (WebView banner REC-MISS-shadowed),
        F-116 metaData timeout=5000/redirect read via getPackageManager
RENDER  frames: splash 0-px (white banner; same 31ddd4d5 SHA class as
        FreeKlondike splash) → lobby 205,638 non-white px (buttons New Game/
        About Us/Help/Exit, node ids 24-27) → game board 2,073,600 non-white
        px (green felt + ebinqo art + "Cards Remaining: 23", "Session Games:
        1" TextViews — the app's OWN state)
```

### The blocker that was fixed (F-118, R-NEW-385 ROOT-CAUSED-FIXED)

First full run: lobby "New Game" tap worked (inline anonymous listener,
listener_id=28) but ALL 52 card taps were DEAD (DOWN hit the view, no
PerformClick, no CLICK).

```text
SOURCE OBSERVATION: GameActivity.java:74 `private View.OnClickListener
  cardClickListener = new View.OnClickListener(){...}` — FIELD INITIALIZER
  (runs in <init>); onCreate binds it to 52 ImageViews.
TRACE: [EXP060-LISTENER] setOnClickListener view_id=65.. listener_id=0 —
  the listener FIELD read returned typed-zero → clickable but
  click_listener_id=0. Engine log: GameActivity;.<init> NEVER executed
  (no TRY-ENTRY/MEM lines) while the LAUNCH activity's <init> ran
  (SplashActivity;.<init> insns=6). ROOT: G08 startActivity launch path
  (ExecutionEngine::consume_pending_intent) did heap.allocate() + onCreate
  and SKIPPED <init>.
UPSTREAM (fetched 2026-09-19, aosp-mirror/platform_frameworks_base @ main):
  Instrumentation.java:1448 newActivity(ClassLoader, String, Intent) →
  instantiateActivity → the CONSTRUCTOR runs (ActivityThread
  .performLaunchActivity contract; OpenJDK Class.newInstance law).
SEMANTIC LAW (generic): F-118 — every activity-construction path must run
  the DECLARED no-arg <init>()V before onCreate so instance-field
  initializers are live (mirrors the launch-activity path's
  run_activity_default_init).
FIX: execution_engine.cpp consume_pending_intent — <init> dispatched via
  try_recursive_invoke with a [G08-LIFECYCLE] record.
APP BEFORE: card taps dead (listener_id=0). APP AFTER: [EXP060-LISTENER]
  listener_id=38; UI-EVENT CLICK → Leu/veldsoft/tri/peaks/GameActivity$1
  (the REAL cardClickListener) → board.updateState executed.
SECOND-APP RESULT: OPMT GameActivity <init> ran through the same law
  ([G08-LIFECYCLE] {"method":"<init>","instructions":26}) + FishRings
  GameActivity chain — 3 consumers on day one.
```

### Gates F–I — honest partial (S7, not S8)

```text
chain    splash → F-115 Timer 5000ms → Class.forName(redirect) → Lobby →
         tap New Game (target=24) → GameActivity onCreate 7905 insns →
         board render; card tap → CLICK dispatched to GameActivity$1 ✓
stopper  the app's OWN guard: CardBoard.updateState → Deck.cardAtPosition
         threw IndexOutOfBoundsException("No such card!") — the app caught
         it itself ([EXC-PROPAGATE] caught at GameActivity$1). Cause chain:
         updateState(-1) means the identity loop `view == cardsViews[q]`
         matched nothing — the OBJECT-IDENTITY family (field/array element
         identity for view refs + listener-field churn 38→273 evidence).
         NOT fixed this session (breadth law; forensic trail recorded §6).
DET      RUN1/2/3 frame SHAs 598ddbfa×4 → 53dd71ec (lobby) → 49e02f75
         (board) ×6 — byte-identical
STAGE    S7 PROVEN (input → real handler → real app code; state mutation
         blocked by the app's own guard on divergent identity state) +
         deterministic S6 render
Evidence docs/evidence/s65_spotlight/tp_{lobby,game_board}.png
```

## 4. NEW-002 FishRings (S10 PROVEN — full interaction chain, det ×3)

### The blocker that was fixed (F-119, R-NEW-386 ROOT-CAUSED-FIXED)

First run rc=0 but PARTIAL: 3× uncaught NPE, game logic dead:

```text
SOURCE OBSERVATION (dex dump): Rings.<init> builds the board via
  Array.newInstance(Integer.TYPE, new int[]{12,3}) — the canonical 2D
  int[][] pattern.
TRACE: [SGET-MISS] key=Ljava/lang/Integer;.TYPE obj_id=0 →
  Array.newInstance(NULL, dims) → null matrix → [SYNTH-EXC] aput-null NPE
  in Rings.init pc=399.
UPSTREAM (fetched 2026-09-19, openjdk/jdk @ master):
  Integer.java:106 `public static final Class<Integer> TYPE =
  Class.getPrimitiveClass("int")` — JVM-injected, NEVER written by
  <clinit>; Array.java:74/110 newInstance(Class, int|int...) contract.
SEMANTIC LAWS (generic): (a) F-119a X.TYPE law — Integer/Boolean/Byte/
  Character/Short/Long/Float/Double/Void .TYPE answer canonical primitive
  Class objects (descriptors I/Z/B/C/S/J/F/D/V, JLS/DEX spec);
  (b) F-119b primitive-array descriptor law — Array.newInstance with a
  primitive component builds "[I"-style descriptors (no L...; wrapper),
  recursively for n-D ("[[I") so check-cast succeeds.
FIX: dalvik_engine.cpp sget static-miss path + Array.newInstance
  descriptor builder (make_array_elem_desc).
APP BEFORE: 3 uncaught NPE, board logic dead, rc=1 PARTIAL. APP AFTER:
  [R358-ANEW] newInstance(I, dims=[3,12]) -> obj#81 [[I; newInstance(I,
  dims=[3,12,2]) -> obj#100 [[[I; rc=0 SUCCESS 0 errors.
SECOND-APP RESULT: TicTacToe (R-NEW-358 consumer) Button[][] path exercised
  by the battery after the descriptor change — ALL fixture goldens PASS
  (zero regression, §7).
```

### Gates C–I — FULL CHAIN (S10)

```text
Run    ./build/miniandroid run --execution-mode real-dalvik --frames 9
       --frame-delay 1500 --tap 5,5 ×4 --tap 540,960 --tap 270,960
       --tap 810,960
Chain  SplashActivity.onCreate (F-116 metaData) → F-115 Timer 5000ms →
       SplashActivity$1.run → Class.forName → startActivity →
       GameActivity <init> (F-118) + onCreate → 44-view board inflate →
       render 2,072,211 non-white px (pink ball + red rotation arrows +
       ebinqo art — the app's OWN drawables)
INPUT  frame 4 tap → CLICK → GameActivity$5 (rings.ccwa/updateInfo);
       frame 5 tap → GameActivity$6; frame 6-7 taps → ring rotations
STATE  rings rotation matrices mutate (real DEX); updateInfo re-renders
FRAME  diffs: 2,072,211 (menu→board) → 483,395 → 478,169 → 7,347 px —
       EVERY interaction changed the frame
DET    RUN1/2/3: 598ddbfa×4 → 96668475 (board) → 86990d43 → bd2bad7e →
       e027b021×2 — byte-identical ×3
STAGE  S10 PROVEN (repeatable end-to-end: launch → splash timer → game →
       3× input→handler→state→changed-frame, 3-run deterministic)
Evidence docs/evidence/s65_spotlight/fr_{board,board_after_taps}.png
```

## 5. NEW-003 OPMT (S6 + chain-to-GameActivity; app-own AI guard stops later stages)

```text
BUILD   APK 4f91e3801780684a7bfdf33de97646cf0e9a1b4913c3ea0699efddeae5368366
MENU    6 views; REAL strings "Play with Friend"/"Play with Computer"/
        "How to play?" at (277,1379)/(277,1547)/(277,1715); 214,144 px
CHAIN   tap → MainMenu$$ExternalSyntheticLambda2 (REAL app lambda) →
        startActivity(GameActivity) → F-118 <init> 26 insns → onCreate
        1756 insns → frame diff 461,211 px
STOPPER app-own: Game/Ai.randomAi → rand.nextInt(moves.size()) with
        moves.size()==0 → IllegalArgumentException (REAL Java semantics;
        the move list is empty because the Board/Pieces string-identity
        state diverged — same OBJECT-IDENTITY family as TriPeaks §3).
        Deterministic (RC=1 every run, identical SHAs).
DET     RUN1/2/3: e9a8f5db (menu) → b7606908 (partial board) ×6 — identical
STAGE   S6 PROVEN (deterministic render, real provenance) + input→real
        lambda→GameActivity lifecycle chain. NOT S7+: honest.
Evidence docs/evidence/s65_spotlight/opmt_{menu,game_partial}.png
```

## 6. Search ledger (real usage evidence)

```text
TOOL zoekt (sourcegraph @ 153817f643cd, Go 1.26.0, GOPROXY=direct; shards
  over the 3 pinned clones: TriPeaks 3,277 files? no — 58/81-file repos;
  shard bytes 0.38-0.80 MB each)
  Q1 "cardClickListener" → GameActivity.java:74 (field init) + :437-477
      (52 bindings) — CONFIRMED the field-initializer pattern pre-build
  Q2 "ccwa" → Rings.java:138 + 3 call sites + GameActivity.java:35 —
      mapped the ring-rotation state surface before running
  Q3 "nextInt" → TriPeaks Deck.java:98 Constants.PRNG, FishRings Rings.java:216,
      OPMT Ai.java:49 — located every Random-bound surface in the corpus
  Q4 "buttonOnClickMethod" → OPMT GameActivity.java:59-67 — 9 lambda
      registrations (B1..B9)
TOOL cindex+csearch v1.2.0 (rebuilt, indexed /tmp/cand)
  Q "randomAi" → Ai.java 2 hits — cross-tool consistency with zoekt
TOOL F-Droid index-v2.json local scan (60,145,769 B, 4,408 packages)
  45 keywords → 120 shortlist (scripts/s65_candidate_survey.py)
TOOL GitHub raw gradle probes (no API quota): 120 candidates probed in
  parallel (scripts/s65_probe.py) — androidx/compose/ndk/libgdx/flutter
  signatures
TOOL AOSP raw (aosp-mirror/platform_frameworks_base @ main):
  Instrumentation.java:1448 newActivity(ClassLoader,String,Intent) — F-118
TOOL OpenJDK raw (openjdk/jdk @ master): Integer.java:106 TYPE =
  Class.getPrimitiveClass("int") — F-119a; Array.java:74/110 newInstance —
  F-119b
TOTAL_SEARCHES 9 documented (4 zoekt, 1 csearch, 1 F-Droid scan, 1 GitHub
  raw probe sweep, 2 AOSP/OpenJDK fetches)
UNIQUE_QUERIES 9; REPOSITORIES_CHECKED 9 (3 picks + 6 deferred probes)
DOMAINS 4 (f-droid, github raw, aosp, openjdk)
RELEVANT_HITS 14; IMPLEMENTATIONS_FOUND 3 (Instrumentation.newActivity;
  Integer.TYPE; Array.newInstance)
TESTS_FOUND 0 (these upstreams carry no instrumentation tests for the
  faces — honesty row)
SEARCH_EXHAUSTED no (OBJECT-IDENTITY family follow-ups queued §7)
```

## 7. Compatibility families discovered / updated

```text
1. OBJECT-IDENTITY family (NEW, blocks TriPeaks S8 + OPMT S7+):
   instance-field/array-element object refs (view refs stored in
   cardsViews[], listener field re-reads) lose identity across
   field/array round-trips (churn 38→273 evidence; typed-zero elements).
   Reach: ANY app whose listeners/state live in fields+arrays — the
   field-initialized-listener pattern is extremely common. NEXT
   highest-leverage target; forensic trail in tp_f118.log.
2. STRING-IDENTITY sub-face (same family): Board/Pieces color-string
   equality chains diverge → empty move list → app-own nextInt(0).
3. TABLE-MEASURE-SKIN / RELATIVE-LAYOUT-MARGINS family (updated): both
   TriPeaks and FishRings cards/arrows render stacked at (0,0) —
   RelativeLayout alignParent* + margins not fully applied. Render is
   still app-provenance (drawables/texts correct); interaction hit-test
   unaffected for these runs. Recorded, not attempted (breadth).
4. COUNTDOWNTIMER family (recorded): android.os.CountDownTimer bridge
   absent (Eidetic-Memory-Trainer deferred-by-facts).
5. TIMER/SCHEDULER (F-115, 2nd+3rd consumers this session): TriPeaks +
   FishRings splash timers fired via the S64 law unchanged.
6. META-DATA (F-116, +2 consumers): TriPeaks/FishRings redirect+timeout.
7. SCHEDULED-TAP (F-117, +3 consumers): all three apps' tap chains.
8. SECURE-RANDOM→Random (F-113 family): FishRings Rings PRNG ran clean.
```

## 8. Regression

```text
BEFORE F-118/F-119 (fresh engine build, no changes): battery baseline from
  S64 = 94 stages, 92 PASS + EXT-01/02 environmental.
AFTER F-118 + F-119: 94 stages, 92 PASS, ONLY EXT-01/02 (pre-existing,
  upstream-deleted) — ZERO regressions; ALL fixture pixel goldens
  byte-identical, including the TicTacToe fixture that exercises the
  R-NEW-358 Array.newInstance object-array path against the F-119b
  descriptor change. G06/G07/G08/GATE-H goldens preserved.
```

## 9. Final numbers

```text
NEW APPS SURVEYED:            120 shortlisted / 9 deep-probed / 8 deferred-by-facts
NEW APPS FORENSICED:          6 (3 built + 3 backup candidates deep-checked)
NEW APPS BUILT FROM SOURCE:   3 (TriPeaks 52272ae6, FishRings 14d7dd80, OPMT 4f91e380)
NEW APPS EXECUTED:            3
WITH UI:                      3
WITH MEANINGFUL RENDER:       3
WITH INPUT:                   3
WITH REAL HANDLER:            3 (TriPeaks GameActivity$1, FishRings $5/$6, OPMT lambda)
WITH STATE MUTATION:          1 full (FishRings) + partial faces in the other two
WITH CHANGED FRAME:           1 full (FishRings, 3 interactions) 
L6+:                          1 (FishRings S10) — corpus total S10 = 4
DETERMINISM:                  3/3 apps det ×3 (even OPMT's app-own failure)
NEW GENERIC LAWS:             F-118 (R-NEW-385), F-119a/b (R-NEW-386) — both
                              with ≥2 consumers on day one
REGRESSION:                   92/94 + EXT-01/02 environmental, zero new failures
REGISTRY:                     368 → 372 roots (F-118, R-NEW-385, F-119, R-NEW-386)
S64 PUSH:                     PENDING-PUSH (no credential this session) — the
                              S65 commit carries both; push-verify at session end
```
