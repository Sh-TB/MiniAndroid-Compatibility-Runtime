# ROADMAP_STATUS — Canonical, Reconciled (S56)

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

S54 rows retained below the S55 rows for continuity.

| ID | Blocker | Root cause (evidence) | Fix | Proof |
|---|---|---|---|---|
| **F-085 (S56)** | WebView-family apps: getSettings/setWebViewClient/loadUrl/loadData were REC-MISS silent no-ops → content face blank (Notes read face) | No WebView content model existed — the markdown/WebView pipeline died at its first call | Generic model (app-agnostic): ViewShadow dispatches the WebView family; WebSettingsShadow = symmetric set/get property bag; load family stores the document and the render law extracts visible text via a generic HTML→text pass (no markdown special-casing) into the node text so the standard pipeline paints it | Notes v139 getSettings → settings object identity memoized ([F085-WV] logs); battery ALL PASS 96/96; shadow-count invariant updated 19→20/22 |
| **F-084 (S56)** | Halted callee (loop-detector) fed a STALE last_invoke_return_ to the caller's move-result → garbage slot index −733270216 → AIOOBE → APP BOUNDARY death (dooz v23) | The invoke boundary blanket-cleared halted_ without discriminating the abnormal-halt signature (halted_ && !halted_on_return_) from a normal return (which also sets halted_) | HALT-RETURN containment law: the halt escalates to the caller as a deferred VirtualMachineError (F084-HALT-RETURN); no return value is fabricated | Battery ALL PASS 96/96 (first attempt without the discriminator broke stages 59-63 and was fixed pre-commit); dooz v23 face changed from garbage-index AIOOBE to honest halt propagation; docs/evidence/s56_dooz23/ |
| **F-082 (S55)** | Notes v139 read↔edit face swap was a silent no-op (S53 "RENDER_ONLY") | `ViewSwitcher.setDisplayedChild` (the whole ViewAnimator family) was REC-MISS — no displayed-child law in ViewShadow. S55 tree forensics REFUTED the S53 "ListView item paint" hypothesis: v139 has NO ListView | AOSP ViewAnimator law on the ViewShadow node model: setDisplayedChild/getDisplayedChild/showNext/showPrevious (exact AOSP clamp `which≥count→count-1; <0→0`, showOnly visibility walk, requestLayout flag) | law test 18/18 (battery "F-082 ViewAnimator law"); Notes FAB click → face swap **2,057,718 px (99.23%)**, probed=3 changed=1 (was 0/3); frames byte-identical across runs (s55_notes_v2/SHA256SUMS) |
| **F-083 (S55)** | Dooz v18 R-NEW-361: ScatterMap probe spin (HALT-LOOP → aput-oob) | DOWNSTREAM of a depth-cap drop: 56th `Ln/a;.r` (LongArray-fill helper) entered at depth=80 == MAX_RECURSION_DEPTH → silently dropped → metadata stayed heap-zero → sentinel write made ghost bytes `0xff007f6600000000` (zero EMPTY) → probe never terminates. EXP-053: ~80KB C++ stack/DEX frame → 80-frame cap on the 8MB stack | (1) cmd_run executes on a dedicated 1GB-virtual-stack pthread (ART contract: recursion bounded by thread stack); (2) MAX_RECURSION_DEPTH 80 → 2048 (~164MB worst case); (3) limit-drop is ALWAYS loud (`[RECURSION-LIMIT]` stderr); (4) hygiene: F-074 always-on trace (heap lookup per inherited call, ~1.6K instr/s throttle) now env-gated `MINIANDROID_F074_TRACE` | dispatch trace: 55/56 r calls OK, failing call at depth=80; [R361-STORE] ghost vs healthy metadata words; post-fix: NO HALT-LOOP/aput-oob, metadata `0xff80808080808080`, MainActivity.onStart/onResume dispatched (first time); key traces docs/evidence/s55_dooz/ (SHA256SUMS) |
| **F-080 (S54)** | ChessClock "2-color dark blank" | `Resources.getColor(I, Theme)` two-arg overload: shadow read a fixed arg slot and resolved the NULL THEME (int 0) as the resid → every lookup black | resid = first INT-typed arg (robust under receiver-included/excluded conventions; AOSP law: references can never be the resid) | `[RES] resid=0x7f050005 → 0xff499ebd`; frame 99.3% nb/2 colors → 187 colors |
| **F-081 (S54)** | ChessClock clock text = "null" | M3-19 active-cycle key was name-only: legal `formatTime(J)` overload delegation inside active `formatTime(J Z)` falsely matched as re-entry → stubbed null | include the method descriptor in the active-invoke key (JVM identity = name+descriptor) | 0 cycle stubs; `setText "10:00"` ×2; real clock face rendered |
| (infra S54) | battery 54-fixture collapse | disk 100% full + un-bootstrapped aapt2/ECJ/D8 toolchain on this machine | residue freed (7 GB, manifest recorded); `scripts/build/bootstrap_toolchain.sh` re-run; EXT fixture re-fetched SHA-verified | battery 92→94 stages ALL PASS |

## 3. Active frontier (P0 first, attack order)

1. **R-NEW-376 — Dooz v18 post-F-083 ctor-climb frontier** (OBSERVED-FAIL,
   P1, pinned at S55). Compose init builds constructor chains that exceed
   the 2048-frame budget (9 cap-climbs: Lj/j0;.<init> ×7 [okhttp-family,
   DEX-verified delegation LinkedHashMap,I→Map overload], Lt0/t;
   +LE0/c;.<init> ×2 [t0/t↔E0/c alternation; every resolved invoke target
   is legal; E0/c has an if(j≠0) throw guard that never fires]). Each
   climb costs 2048×80KB committed stack; a cap-drop corrupts the
   half-initialized object. NEXT (ranked in the registry entry): wide-arg
   VALUE trace per t0/t↔E0/c hop (constant ⇒ mis-dispatch; varying ⇒
   finite-but-huge chain) → either a ctor-target selection fix or frame-cost
   reduction. *Unblocks Dooz v18 first frame and the Compose family.*
2. **R-NEW-344 — dooz23 first frame / ScatterMap full-table probe spin**
   (OBSERVED-FAIL, P0, REFINED at S56). Post-F-083/F-084 the run reaches
   Recomposer/ControlledComposition; the blocker is an androidx.collection
   ScatterMap insert into a FULL table (cap 15, size 15, zero EMPTY
   metadata bytes): the second grow (budget e==0 at size 14) entered the
   R8-inlined resize but computed newCapacity=15 instead of 31 and
   re-filled the same arrays after convertMetadataForCleanup. NEXT: trace
   Lmg1;.b (nextCapacity = cap*2+1) around insert #16; compare the cap-7
   grow (f(15) ran) vs the cap-15 grow (no f) at the d() pc=128 branch.
   The crash face is CONTAINED by F-084 (honest halt, no garbage index).
3. **WebView content model — model SHIPPED (F-085); end-to-end content
   probe pending** (P1, was R-NEW-377 BLOCKED-PINNED). The WebView call
   surface (getSettings/setWebViewClient/load family) now dispatches
   generically and the render law extracts visible text. Remaining for
   the L5→L7 claim: a full note-create→save→read-face UI flow proving
   pixels from a real document (needs the multi-step click sequence).
4. **Persistence ladder L10** (P2) for the interactive apps — ChessClock
   first (start clock → close → reopen → state kept). uNote ladder
   continues at NoteEdition (PreferenceManager/getApplicationContext
   surface).
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

## 6. Direct answers (S54 §12, S56 refresh)

**What is the biggest runtime blocker?** The Compose first-frame pair —
now **R-NEW-376** (post-F-083 ctor-climb budget, v18) + **R-NEW-344**
(S56 refinement: androidx.collection ScatterMap full-table probe spin in
Recomposer/ControlledComposition dirty-scope tracking, v23; the
garbage-index crash face is contained by F-084) — it holds the entire
modern Compose app class (Dooz, RTTT, emmanuelmess tictactoe) below L5.
R-NEW-361 itself is FIXED (F-083): the probe spin was downstream of a
depth-cap frame drop.

**What prevents complete HelloWorld?** Nothing — HelloWorldSelfAware is
visually proven end-to-end (L7 via EXT-01/02) at the current HEAD.

**What prevents a playable game?** Nothing for the proven set — GM Dice (real
F-Droid game) and Chess Clock both demonstrate launch→input→state→rendered
change at this HEAD, and tictactoe_golden proves 9-tap win-state play.

**What prevents Dooz?** R-NEW-376 (v18, new pinned frontier) / R-NEW-344
(v23) — see §3. The pre-S55 blocker R-NEW-361 is VERIFIED-FIXED (F-083).

**What prevents Notes content rendering?** The WebView content model is
SHIPPED (F-085): the WebView call surface (getSettings/setWebViewClient/
load family) dispatches generically and the render law extracts visible
text. The remaining gap to the L5→L7 claim is the end-to-end content
probe (a real note-create→save→read-face UI flow with pixel proof). The
app's state machine itself is FIXED (F-082) — mode-switch input→state→
render is proven at 2.06M px. uNote's main-menu input chain is PROVEN at
S56 (R-NEW-368 premise refuted: the old 16-probe grid never covered the
bottom-44px button band; a coordinate-correct tap consumed and launched
NoteEdition).

**What prevents Telegram?** Init-chain depth (REC-MISS surface, SafeIterableMap
stub, NativeLoader boundary) — no frame within the 540 s budget. Note: F-083's
deep-stack thread directly attacks the depth side of this frontier too.

**What prevents general APK compatibility?** The long tail of framework REC-MISS
surface plus the Compose P0s; every fixed law transfers (F-080/F-081/F-082/
F-083/F-084/F-085 were found in one app and are corpus-generic).

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
