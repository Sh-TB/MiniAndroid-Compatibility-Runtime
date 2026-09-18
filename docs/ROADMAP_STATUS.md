# ROADMAP_STATUS — Canonical, Reconciled (S58)

> **SINGLE SOURCE OF TRUTH for what is done, what is open, and what is next.**
> Reconciles ALL historical roadmaps against actual committed evidence: nothing
> disappeared because it got old; nothing is checked without evidence.
> Canonical by the S54 documentation law. Supersedes `docs/ROADMAP.md` (S52/S53
> canonical — now a pointer), `docs/runtime/FUTURE_ROADMAP.md`,
> `docs/runtime/EXP037_IMPLEMENTATION_ROADMAP.md`,
> `docs/research/ROOT_LAW_IMPLEMENTATION_ROADMAP.md` (kept as the live tier
> source), and campaign TODO blocks in session records.
>
> Status vocabulary: `DONE / VERIFIED / IMPLEMENTED / TESTED / OBSERVED /
> PARTIAL / BLOCKED / PENDING / SUPERSEDED`. Evidence states per
> `docs/ACHIEVEMENTS.md` §0.

## 1. What already works (evidence-pinned)

| Capability | Status | Evidence |
|---|---|---|
| APK → DEX → lifecycle → View → render pipeline | **VERIFIED** | battery 94/94; §28 helloworld_golden; 6 real-APK GUI successes |
| **HelloWorld complete execution (control target)** | **VERIFIED** | EXT-01 typography 9/9 + EXT-02 interaction 12/12 + `s54_frames/helloworld_ext01_base.jpg` (real text incl. app-computed hash) |
| Real game with input→state→render chain | **VERIFIED** | GM Dice 8/8 clicks → app-rolled dice rendered (L7 + app-specific result); Chess Clock click → active-player switch (80,289 px); battery §29 tictactoe_golden 9/9 + determinism |
| Real corpus APKs rendering recognizable GUI | **VERIFIED** | 6 apps (Chess Clock, GM Dice, MicroTimer, Simple Stopwatch, Heading Calculator, uNote) |
| Screenshot quality gate + canonical gallery | **VERIFIED** | `s54_frames/` 12 JPGs + SHA256SUMS + REJECTED section; S53→S54 byte-identical replay proof |
| Lifecycle/input/persistence dispatch | **VERIFIED** | G06/G07/G08 law goldens; SharedPreferences/SQLite round-trips (R-NEW-367) |
| Regression battery | **VERIFIED** | "BATTERY GATE: ALL PASS (96 stages)" at current HEAD (92 stages when the external EXT fixture is absent — the two EXT run stages collapse; the count law is documented in the battery script) |

## 2. What was fixed THIS session (root cause → law → proof)

S58 rows above the S57 row for continuity.

| ID | Blocker | Root cause (evidence) | Fix | Proof |
|---|---|---|---|---|
| **F-102 (S58)** | R-NEW-376 dooz ctor-climb: Compose init ctor chains hit the 2048-frame cap — v23 `Lgz1;.<init>` ×3 + `Lbp1;.<init>` ×1, v18 `Lj/j0;` ×7 + `Lt0/t;`/`LE0/c;` ×2, caller==callee, same receiver | The 3rc invoke path (invoke-*/range) DROPPED the call-site method PROTO at the try_recursive_invoke boundary (default "") → the F-023 exact-descriptor overload law could not fire → the arity heuristic (prefer LARGEST bytecode body) re-selected the CALLING ctor overload itself → same-receiver self-recursion. DEX ground truth (androguard, scripts/s58_gz1_forensic.py): Kotlin default-args ladders — overload1(mask+I)→overload2, argc identical, descriptors distinct, NO self-call in valid DEX | Range-invoke dispatch passes the resolved proto (`range_proto` hoisted + passed on both attempts); when the proto misses, the heuristic path is unchanged | RECURSION-LIMIT count **0** on v18 AND v23 (was 4 on v23); v18 rc=0 at 310k+ instructions with the Choreographer doFrame loop alive (Compose composing); regression `f102_range_ctor_overload_exact_dispatch` (discriminating: pre-fix picks the larger (I)V overload → f==0; post-fix exact-descriptor → f==127). Evidence: docs/evidence/s58_r376/ |
| **F-103 (S58)** | R-NEW-378 cascade past R-NEW-376: compose rememberSaveable IAE "Can't put value with type null into saved state" (Lje;.<init> ACCEPTABLE_CLASSES loop) + IAE "Key must be a class" (Lwl0;.containsKey instance-of) → APP BOUNDARY unwind at MainActivity.onCreate | (1) `Class.isInstance/isAssignableFrom` had NO handler → STUBBED typed-zero 0 for all 29 elements; (2) Class tokens minted from a private counter collided with real heap ids → §19 runtime-class dispatch sent Class-token receivers to UNRELATED objects; (3) instance-of trusted the register's cached class_desc unless EMPTY — the CollectionShadow round-trip degraded the token tag to "Ljava/lang/Object;" | Class type-question laws over class_to_superclass_/class_to_interfaces_; HEAP-BACKED Class tokens (const-class allocates a real Ljava/lang/Class; object with `__referent_desc`; F-069 identity preserved); instance-of runtime-type authority law (heap class wins over the register tag) | Both IAE faces = 0 post-fix; regressions f103_isInstance_string_exact / f103_isAssignableFrom_subclass / f103_instanceof_heap_subclass; same failure family as F-086 (missing handler → typed-zero → wrong branch). Evidence: docs/evidence/s58_r376/ |
| **F-104 (S58)** | F-085 Notes content path: the app's real read chain died silently (file ABSENT → stream EOF → empty model → empty markdown body) | io/state surface gaps: no FileInputStream sandbox reads (assets only), no Uri.fromFile/getPath/getLastPathSegment, no ContentResolver.openInputStream, no AsyncTask.execute dispatch, no EnumSet.of, no java.util.regex Pattern/Matcher (appendTail destroyed the text in mediaCheck), requestPermissions auto-grant never dispatched the callback | Law family: FileInputStream/FileReader sandbox ctor + "file:" stream keys (4 MiB bound); Uri file-scheme family; ContentResolver.openInputStream; AsyncTask.execute (doInBackground+onPostExecute, ancestor-walk recognized); EnumSet.of; regex Pattern.compile/Matcher.find/matches/group/appendReplacement/appendTail (std::regex); onRequestPermissionsResult dispatch; BufferedInputStream joins EXP-071 propagation; [EXP093-FNA] trace env-gated (F-074 hygiene) | Notes real read chain PROVEN live: seeded sandbox doc → app defaultFile/readNote/ReadTask → openInputStream present=1 → readLine ×10 REAL lines → setText sb_value extraction (230 chars verified) → markdownCheck appendTail (230 chars preserved). REMAINING: commonmark parse→render yields an empty body (F-085 open at that face). Battery 96/96 at this HEAD |
| **R-NEW-352 closure (S58)** | microtimer Room initDb 50k forName retry loop starving the run budget (the R-NEW-350 default-OFF reason) | STALE BLOCKER: the S43 A/B pre-dated R-NEW-355 (S44) — the retry loop was the missing pc-advance contract, already root-caused+fixed | Re-proved A/B at the fixed HEAD: microtimer law-ON vs law-OFF PIXEL-IDENTICAL (1,041,437 non-white both; rc=0; HALT-LOOP 0; 2 forName resolutions); the forName law is DEFAULT-ON (MINIANDROID_R350_LAW=0 opt-out) | Corpus pixel-identical to S57 records: chessclock 2,040,736 nb / notes 2,073,600 nb / unote 236,520 nb; 3-run determinism (dooz v23 ef47a2d3cdc6929e ×3) |

S55/S56/S57 rows retained below for continuity.

| ID | Blocker | Root cause (evidence) | Fix | Proof |
|---|---|---|---|---|
| **F-086 (S57)** | dooz v23 (R-NEW-344): ScatterMap full-table probe spin — the second grow computed newCapacity=15 instead of nextCapacity(15)=31 and re-filled the same arrays → zero EMPTY metadata → HALT-LOOP → blank first frame | `java.lang.Long.compare(JJ)I` / `compareUnsigned` had NO bridge handler → STUBBED typed-zero exit returned 0 → the R8-compiled growth decision `if-gtz Long.compare(size*32 ^ MIN, capacity*25 ^ MIN)` fell through to the cleanup-instead-of-resize branch. The cap-7 grow never touches the compare (capacity≤8 branches straight to resize), which is why only the SECOND grow failed | 64-bit compare family (compare signed -1/0/+1, compareUnsigned) in the F-055 Long block (OpenJDK law); regression group in semantic_long_cmp_conv_test (6 checks incl. the bit-exact dooz23 idiom) | Capacity field trace on obj#2658: 7 → 15 → 31; HALT-LOOP 0; F084 fires 0; aput-oob gone; battery ALL PASS; post-fix run advances into the R-NEW-376 ctor-climb (now observed on v18 AND v23 — alias absorbed into R-NEW-376). Evidence: docs/evidence/s57_dooz23/ |
| **F-085 (S56)** | WebView-family apps: getSettings/setWebViewClient/loadUrl/loadData were REC-MISS silent no-ops → content face blank (Notes read face) | No WebView content model existed — the markdown/WebView pipeline died at its first call | Generic model (app-agnostic): ViewShadow dispatches the WebView family; WebSettingsShadow = symmetric set/get property bag; load family stores the document and the render law extracts visible text via a generic HTML→text pass (no markdown special-casing) into the node text so the standard pipeline paints it | Notes v139 getSettings → settings object identity memoized ([F085-WV] logs); battery ALL PASS 96/96; shadow-count invariant updated 19→20/22 |
| **F-084 (S56)** | Halted callee (loop-detector) fed a STALE last_invoke_return_ to the caller's move-result → garbage slot index −733270216 → AIOOBE → APP BOUNDARY death (dooz v23) | The invoke boundary blanket-cleared halted_ without discriminating the abnormal-halt signature (halted_ && !halted_on_return_) from a normal return (which also sets halted_) | HALT-RETURN containment law: the halt escalates to the caller as a deferred VirtualMachineError (F084-HALT-RETURN); no return value is fabricated | Battery ALL PASS 96/96 (first attempt without the discriminator broke stages 59-63 and was fixed pre-commit); dooz v23 face changed from garbage-index AIOOBE to honest halt propagation; docs/evidence/s56_dooz23/ |
| **F-082 (S55)** | Notes v139 read↔edit face swap was a silent no-op (S53 "RENDER_ONLY") | `ViewSwitcher.setDisplayedChild` (the whole ViewAnimator family) was REC-MISS — no displayed-child law in ViewShadow. S55 tree forensics REFUTED the S53 "ListView item paint" hypothesis: v139 has NO ListView | AOSP ViewAnimator law on the ViewShadow node model: setDisplayedChild/getDisplayedChild/showNext/showPrevious (exact AOSP clamp `which≥count→count-1; <0→0`, showOnly visibility walk, requestLayout flag) | law test 18/18 (battery "F-082 ViewAnimator law"); Notes FAB click → face swap **2,057,718 px (99.23%)**, probed=3 changed=1 (was 0/3); frames byte-identical across runs (s55_notes_v2/SHA256SUMS) |
| **F-083 (S55)** | Dooz v18 R-NEW-361: ScatterMap probe spin (HALT-LOOP → aput-oob) | DOWNSTREAM of a depth-cap drop: 56th `Ln/a;.r` (LongArray-fill helper) entered at depth=80 == MAX_RECURSION_DEPTH → silently dropped → metadata stayed heap-zero → sentinel write made ghost bytes `0xff007f6600000000` (zero EMPTY) → probe never terminates. EXP-053: ~80KB C++ stack/DEX frame → 80-frame cap on the 8MB stack | (1) cmd_run executes on a dedicated 1GB-virtual-stack pthread (ART contract: recursion bounded by thread stack); (2) MAX_RECURSION_DEPTH 80 → 2048 (~164MB worst case); (3) limit-drop is ALWAYS loud (`[RECURSION-LIMIT]` stderr); (4) hygiene: F-074 always-on trace (heap lookup per inherited call, ~1.6K instr/s throttle) now env-gated `MINIANDROID_F074_TRACE` | dispatch trace: 55/56 r calls OK, failing call at depth=80; [R361-STORE] ghost vs healthy metadata words; post-fix: NO HALT-LOOP/aput-oob, metadata `0xff80808080808080`, MainActivity.onStart/onResume dispatched (first time); key traces docs/evidence/s55_dooz/ (SHA256SUMS) |
| **F-080 (S54)** | ChessClock "2-color dark blank" | `Resources.getColor(I, Theme)` two-arg overload: shadow read a fixed arg slot and resolved the NULL THEME (int 0) as the resid → every lookup black | resid = first INT-typed arg (robust under receiver-included/excluded conventions; AOSP law: references can never be the resid) | `[RES] resid=0x7f050005 → 0xff499ebd`; frame 99.3% nb/2 colors → 187 colors |
| **F-081 (S54)** | ChessClock clock text = "null" | M3-19 active-cycle key was name-only: legal `formatTime(J)` overload delegation inside active `formatTime(J Z)` falsely matched as re-entry → stubbed null | include the method descriptor in the active-invoke key (JVM identity = name+descriptor) | 0 cycle stubs; `setText "10:00"` ×2; real clock face rendered |
| (infra S54) | battery 54-fixture collapse | disk 100% full + un-bootstrapped aapt2/ECJ/D8 toolchain on this machine | residue freed (7 GB, manifest recorded); `scripts/build/bootstrap_toolchain.sh` re-run; EXT fixture re-fetched SHA-verified | battery 92→94 stages ALL PASS |

## 3. Active frontier (P0 first, attack order)

S58 state after R-NEW-376 closure:

1. **R-NEW-379 — Dooz ViewTreeLifecycleOwner frontier (P1, pinned S58)**
   (OBSERVED-FAIL). Past F-102/F-103, Compose init dies at
   `ISE "ViewTreeLifecycleOwner not found from Lho;@1074"` (Log0;.c) —
   uncaught at MainActivity.onCreate invoke_pc=317; the themed window
   paints (2,073,600 nb) before death. The S24 R-NEW-317 fix covered the
   ViewShadow routing only; the owner SET law (ComponentActivity.onCreate
   sets the owner on the decor view) + get-walk extension remain.
   NEXT: ViewTreeLifecycleOwner.set/get law on the ViewShadow node model
   → WindowRecomposer law (checkPrecondition isAttachedToWindow).
   *Unblocks the entire Compose family below the composition bootstrap.*
2. **F-085 content probe — chain live, commonmark face remains** (P1).
   The real read chain is PROVEN live end-to-end through the app's own
   code (seeded doc → defaultFile/readNote/ReadTask → openInputStream →
   readLine ×10 real lines → setText 230 chars → markdownCheck appendTail
   230 chars). REMAINING: the commonmark Parser.parse → HtmlRenderer.render
   DEX chain yields an empty body (loadData bytes=251, text_chars=0).
3. **uNote NoteEdition ladder** (P2) — continues from the S56-proven
   L6 input→navigation (PreferenceManager/getApplicationContext surface).
4. **Persistence ladder L10** (P2) for the interactive apps — ChessClock
   first (start clock → close → reopen → state kept).
5. **Telegram init chain** (P2). Ranked: REC-MISS static-init surface →
   SafeIterableMap iterator law → NativeLoader boundary decision.

## 4. BLOCKED (external dependency — do not spend runtime sessions)

| Item | Blocker | Evidence |
|---|---|---|
| WhatsApp | no legitimate APK (0-byte placeholder proven) | ledger §3.3 |
| TicTacToe Classic re-verification | APK lost with legacy cache; F-Droid `com.palahsu.ttt` NOT_FOUND (checked S54) | ledger §3.3; historical S37/S44 records stand |

## 5. Reconciliation of historical roadmaps (unchanged from S52 unless noted)

- FUTURE_ROADMAP (EXP-023 era): all rows DONE/SUPERSEDED as recorded in
  S52; nothing re-opened.
- EXP037 phases: unchanged (B SQLite PARTIAL, C Execution PARTIAL).
- ROOT_LAW tier ladder: P0 landed set now includes **F-080/F-081 (S54)**;
  F-046/F-047/F-048/F-049 items 15-18/20 unchanged; regression-gate law
  VERIFIED with the 92/94 count law documented.
- Campaign worklist S51–S54: S54 rows = canonical doc rename
  (ACHIEVEMENTS/ROADMAP_STATUS), F-080/F-081, gate refinement (DARK-CONTENT),
  divergent-lineage residue classification (campaign reports referencing
  foreign HEADs quarantined as unverified), gallery s54_frames (12 JPGs),
  toolchain bootstrap re-proven, EXT fixture re-fetched SHA-verified.

## 6. Direct answers (S54 §12, S58 refresh)

**What is the biggest runtime blocker?** The Compose init chain after the
F-102/F-103 fixes: **R-NEW-379** (ViewTreeLifecycleOwner owner-tag walk) —
Dooz v23 now runs past the ctor-climb AND the saved-state/class-key faces
into Compose attach, and dies at the ViewTreeLifecycleOwner lookup.
R-NEW-344 (F-086, S57) and R-NEW-376 (F-102, S58) are both
ROOT-CAUSED-FIXED with regression protection.

**What prevents complete HelloWorld?** Nothing — HelloWorldSelfAware is
visually proven end-to-end (L7 via EXT-01/02) at the current HEAD.

**What prevents a playable game?** Nothing for the proven set — GM Dice (real
F-Droid game) and Chess Clock both demonstrate launch→input→state→rendered
change at this HEAD, and tictactoe_golden proves 9-tap win-state play.

**What prevents Dooz?** R-NEW-379 (ViewTreeLifecycleOwner walk; the pinned
frontier). R-NEW-376 (ctor-climb) is ROOT-CAUSED-FIXED via F-102: the 3rc
descriptor-dispatch law, RECURSION-LIMIT 0 on both v18 and v23, regression-
protected. The saved-state cascade (R-NEW-378) is ROOT-CAUSED-FIXED via F-103.

**What prevents Notes content rendering?** The WebView content model is
SHIPPED (F-085) and the real read chain is now PROVEN live through the
app's own code (F-104: file→stream→reader→model, 230 chars verified into
the EditText and through markdownCheck). The remaining gap is INSIDE the
commonmark Parser.parse → HtmlRenderer.render DEX chain (empty body at
loadData). The app's state machine itself is FIXED (F-082). uNote's
main-menu input chain is PROVEN at S56 (R-NEW-368 premise refuted).

**What prevents Telegram?** Init-chain depth (REC-MISS surface, SafeIterableMap
stub, NativeLoader boundary) — no frame within the 540 s budget. Note: F-083's
deep-stack thread directly attacks the depth side of this frontier too.

**What prevents general APK compatibility?** The long tail of framework REC-MISS
surface plus the Compose P0s; every fixed law transfers (F-080/F-081/F-082/
F-083/F-084/F-085/F-102/F-103/F-104 were found in one app and are corpus-generic).

**What prevents one genuinely fully runnable application?** Nothing —
HelloWorldSelfAware IS the fully runnable reference application (full chain +
visual proof + interaction + reproducibility), and Chess Clock is the first
real corpus app at L7 with a visual state transition.

## 7. Binding laws (restated)

- Regression gate: micro-proof fixture → pixel golden → 3-run determinism →
  full battery (96 stages with the EXT fixture) → affected real-APK re-run →
  honest frontier update. Never silently reduce the battery.
- Forbidden: app-specific shortcuts, package-name hacks, blank-frame
  acceptance, rc=0-as-success, committing raw logs/traces/APKs/blank
  screenshots, token/secret material anywhere.
- One file per role: `ACHIEVEMENTS.md` (executions), `KNOWLEDGE_INDEX.md`
  (knowledge), `ROADMAP_STATUS.md` (this file), `README.md` (landing).
  Everything else: roleful, merged, archived, or deleted.

_Era roadmaps remain in place as history with header pointers where their
claims were absorbed here. Do not update them._
