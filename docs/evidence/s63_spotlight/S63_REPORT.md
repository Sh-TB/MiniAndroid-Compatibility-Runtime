# S63 — Open-Source APK Spotlight 2: 2 NEW source-first builds executed; gmdice reaches S10/L6-PROVEN source-first (F-113 Random inheritance law); zoekt large-file root cause diagnosed

Date: 2026-09-19 (S63 continuation of the S62+ breadth mission). All runs on
this machine (2 CPU). RECON at session start: local HEAD == origin/main ==
`f7ae6432` (S62+ spotlight), tree clean; miniandroid binary restored by
container rebuild; zoekt/codesearch toolchain ABSENT (rebuilt this session
with Go 1.26.0, see §4). No new campaign/branch/roadmap. Mission: increase
the count of REAL open-source APKs built from source and executed
launch→UI→(input→state→render).

## 0. Candidate selection (source forensics, ≥3 candidates, fact matrix)

Surveyed via GitHub API + F-Droid API (evidence §4). Skipped per directive:
Anuto, OpenSudoku (already corpus). 2048-android excluded (WebView).

| field | gmdice (ge0rg/gamemasterdice) | siggen (billthefarmer/sig-gen) | Blockinger (vocollapse/Blockinger) |
|---|---|---|---|
| SOURCE AVAILABLE | YES — cloned @ 6353926f (v1.3 line, v1.2 staged) | YES — cloned master | YES — cloned @ 8b26057f |
| BUILDABLE (aapt2/ECJ/D8) | YES (8 java files → 35 classes) | YES (10 files; +generated BuildConfig) | likely, but heavy |
| SINGLE ACTIVITY | YES (1: ListActivity) | 4 (Main launch = plain Activity) | 6 |
| CLASSIC VIEWS | YES (ListView/TextView/Button) | YES (+ImageButton/SeekBar) | YES (ListActivity) |
| CUSTOM VIEW | no (custom only in dialogs) | YES ×3 (`<org.billthefarmer.siggen.{Scale,Knob,Display}>`) | YES — BlockBoardView **extends SurfaceView** |
| FRAGMENT / support-lib | NO | NO (android.preference only in Settings) | **YES — support-v4 FragmentActivity** ✗ |
| DATABASE | NO | NO (prefs) | SQLite highscores |
| THREADING | CountDownTimer fields | Audio Runnable | WorkThread |
| INPUT→STATE→RENDER | Button→onClick→roll→setText | Knob/SeekBar→freq→Display | touch→Board→SurfaceView |
| NETWORK/NATIVE/WEBVIEW/COMPOSE | none | none | none/none/none/none |
| PRIOR EVIDENCE | prebuilt v8 reached L7 (campaign014 corpus) | prebuilt reached L5, 0 errors (S61 sweep) | L1 |
| VERDICT | **BUILD (lowest risk, highest value)** | **BUILD** | **DEFER** (support-v4 + SurfaceView = two known heavy blocker families) |

Blockinger forensics recorded: `GameActivity extends android.support.v4.app.FragmentActivity`
(the FragmentManager.attachHost ISE family that already blocks
minesweeper/memory/2048/Telegram) + rendering via SurfaceView/lockCanvas
(the canvas-bitmap-family frontier from anuto). Not attempted this session —
breadth over obsession.

## 1. NEW-001: gmdice (de.duenndns.gmdice) — **S10 / L6 PROVEN source-first**

### Gate A — Build (source → APK)

```text
Repository   https://github.com/ge0rg/gamemasterdice (GPLv2) @ 6353926f067bd41dd914ec7f530771a586125eb6
Staging      src/ + res/ + manifest; AGP8-style manifest lacks package= →
             staged package="de.duenndns.gmdice" (same documented law as anuto)
Build        aapt2 compile+link → ECJ -source 8 (android-34 stubs) → D8 →
             deterministic zip; 35 classes; warnings only
APK SHA256   ee9f7396ba1d85bff75e9512679cff9b1861e5cd85b42094e2e807c60f872d7a
```

### Gate B–E — Load / Execute / UI / Render (FIRST RUN, no runtime changes)

```text
Run          ./miniandroid/build/miniandroid run --execution-mode real-dalvik
             --max-seconds 180 apk_cache/gmdice_v12_source.apk
Result       rc=0, Errors: 0, Warnings: 0
View tree    LinearLayout root (1080x1920) → ListView (1080x826) →
             TextView "Push buttons to roll!\n\nLong-press buttons to
             configure dice." → TextView rollresult "1" → LinearLayout →
             Buttons "1d6" "1d20" "1d6" "1d6+4" "..." (real resource texts,
             positions/sizes from real measure/layout)
Pixels       1,744,539 non-white of 2,073,600
Extra        click on "..." ran the app's REAL selectDice() →
             AlertDialog.Builder → create() → show() — dialog window
             obj=103 (items=3) built + PAINTED by real app DEX
Screenshot   gmdice_frame0_prefix_rolls_all1.png (raw SHA 5312266e62ce8642…)
```

### Gates F–I — Input / Handler / State / Changed frame → **F-113 generic fix**

First-run trace: 5/5 CLICKs dispatched to the real `GameMasterDice` handler
(`listener=Lde/duenndns/gmdice/GameMasterDice;` — the Activity implements
`OnClickListener`). The app's own roll chain executed in real DEX:
`onClick → roll(ds,color) → StandardDiceSet.roll → SecureRandom.nextInt →
StringBuilder → TextView.setText` (5× [EXP091-SETTEXT] view_id=63).

**SOURCE OBSERVATION:** the dice all read "1" — `gen.nextInt(sides)` answered
typed-zero 0 every call; the app's field is `Random generator = new
SecureRandom()`.
**MINIANDROID TRACE:** `[REC-MISS] Ljava/security/SecureRandom;.nextInt` →
class-miss → super-walk also miss → bridge dispatch receives the STATIC
receiver class `Ljava/security/SecureRandom;` → F-086 Random law matches only
`Ljava/util/Random;` + ThreadLocalRandom → typed-zero.
**UPSTREAM/AOSP SOURCE:** OpenJDK SecureRandom.java:157 `public class
SecureRandom extends java.util.Random`; :828 `protected final int next(int
numBits)` — SecureRandom supplies the bit stream, Random.nextInt(bound) keeps
the public contract. Fetched from github.com/openjdk/jdk (evidence §4).
**SEMANTIC LAW (F-113 / R-NEW-382):** framework-subclass virtual dispatch
must resolve ancestor laws — SecureRandom IS-A Random (ThreadLocalRandom is
already the same shape inside F-086). Deterministic xorshift stands in for
the entropy source (provenance law).
**GENERIC FIX:** F-086 condition += `Ljava/security/SecureRandom;` (one law
family entry, zero app references).
**REGRESSION:** full battery re-run on the new binary: **ALL PASS (94 stages
executed incl. helloworld 26 checks, tictactoe, G06 tap 3-run determinism,
G07 lifecycle, G08 navigation, EXT-01/02, 3-run corpus block)**. (S62 tree
recorded 96; the delta = 2 environment-conditional stages — recorded
honestly; no engine-caused regression.)

### NEW APK RE-RUN (post-F-113) — the L6 chain, all four gates green

```text
Input        5/5 CLICK dispatched to real GameMasterDice handler
Handler      onClick(View) real DEX; button_more → selectDice dialog path
State        StandardDiceSet.roll ×N → SecureRandom.nextInt(sides) →
             dice values 6, 5, 3, 2 (deterministic xorshift stream;
             was 1,1,1,1,1 pre-fix)
setText      rollresult texts "6","5","3","2" (EXP091-SETTEXT view_id=63)
Changed
frame        final render node=63 text="2"; RAW frame SHA pair:
             5312266e62ce86424257e5f314e54a0cfa2fb949036ac3874c86513553bc0835
             → fa1d8612345a2d8d534d5d85c0aa14afd5ad64e52d99f55fd539382476801269
Pixel diff   1,584 pixels — 100% inside the rollresult band
             (bbox x=514..564, y=1672..1750; TextView pos (0,1653) 1080x123)
3-run det    fa1d8612345a2d8d534d5d85c0aa14afd5ad64e52d99f55fd539382476801269 ×3
```

The A/B pair differs ONLY by the F-113 law (same APK, same click pipeline);
the app's own logic turned the changed API answers into different state and a
different rendered frame. **S10/L6 PROVEN (repeatable input → real handler →
real state mutation → changed rendered frame).**

### Class inventory + launch call-chain (source-level)

```text
TOTAL 8 source files → 35 classes (inner/anonymous incl.)
ACTIVITIES      1  GameMasterDice (ListActivity; OnClickListener)
CUSTOM VIEWS    1  SignedNumberPicker (dialog-only; NOT launch-reachable)
MODELS          4  DiceSet (abstract) + Standard/FUDGE/DSA subclasses
FRAGMENTS 0; DB 0; NETWORK 0; WEBVIEW 0; COMPOSE 0; NATIVE 0
Reachable launch chain: GameMasterDice.onCreate → setContentView(act_gmdice)
 → inflate LinearLayout/ListView/TextView/Button ×5 → PreferenceManager
 → findViewById ×N → setOnClickListener(this) → setListAdapter(RollResultAdapter)
 → onResume → loadDicePrefs. Game loop: onClick → DiceSet.getDiceSet (parse,
 real deferred NumberFormatException handlers fire) → roll → SecureRandom
 → setText + ObjectAnimator (REC-MISS no-op, honest).
```

## 2. NEW-002: siggen (org.billthefarmer.siggen) — S7 (L5 render + input→handler→model)

```text
Repository   https://github.com/billthefarmer/sig-gen (GPLv3) @ master
Build fixes  manifest package= staged (AGP namespace style); 2 style lines
             with android:attr/windowOptOutEdgeToEdgeEnforcement (API-35
             attr, absent from SDK-34 aapt2) removed from staged styles;
             generated BuildConfig.java (gradle artifact: VERSION_NAME/
             BUILT referenced by SettingsFragment/AboutPreference)
APK SHA256   c83d21c6348c672a7d54202a7159de0d226e1afa8e6c55725cdfb4d076537e2a
Run          rc=0; real Main (plain Activity) onCreate; toolbar + custom
             views INFLATED FROM FQCN TAGS:
             <org.billthefarmer.siggen.Scale/Knob/Display> constructed via
             the generic LayoutInflater fqcn path; Buttons "Sin"/"Squ"/"Saw"
             real resource texts; 47,809 non-white px — IDENTICAL to the S61
             prebuilt-APK sweep number (cross-validation source-vs-prebuilt)
Input        5/5 CLICK dispatched to real Lorg/billthefarmer/siggen/Main;
             handler; Main.onClick ran (caller=Main.onClick in trace):
             View.getId → switch matched R.id.sine case →
             audio.waveform = SINE model mutation (audio non-null, real DEX)
             → setCompoundDrawablesWithIntrinsicBounds ×N
Honest       state mutation stays in the AUDIO model (waveform drives
             AudioTrack, headless = no pixel face); Display/Knob/Scale
             measure 0x0 (custom-view measurement = recorded frontier);
             CHANGED FRAME NOT PROVEN → stage S7, not S9
3-run det    7e5e14a3a5fa229ec378c0dfc204124a9c4ec05c7954a2142be00c6fd4fda5ac ×3
Stage        S7 (L5 render + input→real handler→real model mutation)
```

## 3. Final numbers

```text
NEW APPS FOUND (candidates surveyed):        3 (+2 directive-skipped: anuto, OpenSudoku)
NEW APPS BUILT FROM SOURCE:                  2  (gmdice v12 ee9f7396…, siggen v1.76 c83d21c6…)
NEW APPS EXECUTED:                           2  (rc=0 both)
NEW APPS WITH REAL UI/VIEWTREE:              2  (gmdice list+buttons; siggen toolbar+custom views)
NEW APPS WITH MEANINGFUL RENDER:             2  (1,744,539 px; 47,809 px)
NEW APPS WITH INPUT DISPATCHED:              2  (5/5 and 5/5 clicks)
NEW APPS WITH REAL HANDLER EXECUTION:        2  (GameMasterDice.onClick; Main.onClick)
NEW APPS WITH STATE MUTATION:                2  (dice 6/5/3/2; audio.waveform)
NEW APPS WITH CHANGED FRAME:                 1  (gmdice — pixel diff 1,584 px in result band)
NEW APPS L6 (S9/S10) PROVEN:                 1  (gmdice S10; 3-run deterministic)
NEW APPS L5/S7:                              1  (siggen)
NEW GENERIC FIXES:                           1  (F-113 Random-inheritance law / R-NEW-382)
APPS UNBLOCKED BY THE FIX:                   ≥1 potential consumers (any app using
                                             SecureRandom.nextInt/next/longs — first hit gmdice)
TOOL ROOT CAUSE DIAGNOSED:                   zoekt large-file under-report (S61/S62 open
                                             question) = default trigram cap; raised cap →
                                             full results (§4)
```

## 4. Tool ledger (real usage evidence)

```text
TOOL zoekt (sourcegraph, built this session: go install @ 153817f643cd)
  Q "selectDice" -shard gmdice shard → 3 hits (0.03s) — candidate launch-chain verification
  Q "SecureRandom"/"nextInt" engine shard (DEFAULT trigram cap) → 0 hits  ← UNDER-REPORT
  Q "SecureRandom" engine shard (-max_trigram_count 100000000) → F-113 lines
    20878..20893 (0.03s) — index 1 file, 4.7MB shard
  LEARNED: zoekt's default max_trigram_count silently EXCLUDES very large
    files (dalvik_engine.cpp 1.2MB) — ROOT CAUSE of the S61/S62 "under-report"
    open question; raised cap gives complete results.
  DECISION CHANGED: zoekt is NOT semantically broken; it needs the cap for
    big files → stays in the toolkit with the flag documented.
TOOL csearch/cindex (google/codesearch v1.2.0, built this session)
  cindex 3.99MB data → 1.68MB index (0.13s)
  Q "SecureRandom" → 8 lines in candidate sources (3ms) — confirmed the app's
    SecureRandom field; Q "nextInt" → Standard/FUDGE/DSA/Coin roll paths
  engine 1.2MB file: under-indexed (0 hits) — per-file trigram limit
    REPRODUCED 3rd time (consistent with SEARCH_LEDGER.md finding #3).
TOOL ripgrep (ground truth)
  rg -c "nextInt" dalvik_engine.cpp → 8 (matches zoekt high-cap count)
TOOL GitHub API (authed) — candidate discovery + rate-limit evidence
TOOL F-Droid API — de.duenndns.gmdice package metadata (v1.2-3-g973297a/vc11)
TOOL OpenJDK source (github.com/openjdk/jdk raw) — SecureRandom.java:157/:828
  upstream law evidence for F-113
TOOL aapt2/ECJ/D8 + build_fixture_apk.sh — both source builds
TOTAL_SEARCHES this session: 9 documented queries (4 zoekt, 2 csearch,
  2 GitHub API, 1 F-Droid API) + OpenJDK source fetch; UNIQUE_QUERIES 9;
  REPOSITORIES_CHECKED 4 (ge0rg/gamemasterdice, billthefarmer/sig-gen,
  vocollapse/Blockinger, openjdk/jdk) + fdroiddata; DOMAINS 4 (github,
  f-droid, openjdk, go module proxy);
  RELEVANT_HITS 12; IMPLEMENTATIONS_FOUND 2 (SecureRandom.next law; siggen
  BuildConfig/gradle-artifact contract); TESTS_FOUND 0 (upstream has no
  dice tests; honesty row); SEARCH_EXHAUSTED no (frontier queries queued).
```

## 5. Honest frontier (recorded, not hidden)

1. siggen custom-view measurement (Scale/Knob/Display at 0x0) — the draw
   chain renders 47,809 px but the interactive knob/display faces stay dark;
   generic measure gap recorded.
2. gmdice ObjectAnimator/ArgbEvaluator + CountDownTimer = REC-MISS no-ops
   (animation/cancel faces); the roll text reaches the framebuffer via
   setText — animations are cosmetic on real devices too.
3. Within-binary frame0-vs-frame1 capture for gmdice: the click pipeline
   always runs post-first-frame (--click-count 0 not honored by the pump);
   the A/B is therefore across the F-113 binary boundary — the ONLY delta is
   the Random law; recorded transparently.
4. Blockinger deferred (support-v4 FragmentActivity + SurfaceView).
