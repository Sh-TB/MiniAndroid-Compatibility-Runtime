# ROADMAP_STATUS — Canonical, Reconciled (S54)

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
2. **R-NEW-344 — Recomposer suspension / Job-active law** (OBSERVED-FAIL, P0).
   First non-blank Compose frame (`31ddd4d5…` covers dooz v23, emmanuelmess
   tictactoe, RTTT).
3. **WebView content model** (P1, PRECISELY PINNED at S55, supersedes the
   old "Notes ListView paint path" entry). Notes' read face is
   `Lorg.billthefarmer.markdown.MarkdownView; extends Landroid/webkit/WebView;`
   (runtime dex parser verified); the markdown pipeline dies at REC-MISS
   `getSettings`. The generic next dependency is a WebView content model;
   app-specific markdown rendering is forbidden. *Unblocks Notes content
   L5→L7 + BGClock-class WebView-root apps.*
4. **R-NEW-368 — uNote touch-target geometry** (P1, unchanged). Paint renders
   buttons; touch path finds no target on a 16-probe grid. *Unblocks uNote
   L6–L10 incl. the notes.db persistence ladder.*
5. **Persistence ladder L10** (P2) for the interactive apps — ChessClock
   first (start clock → close → reopen → state kept).
6. **Telegram init chain** (P2). Ranked: REC-MISS static-init surface →
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

## 6. Direct answers (S54 §12, S55 refresh)

**What is the biggest runtime blocker?** The Compose first-frame pair —
now **R-NEW-376** (post-F-083 ctor-climb budget, v18) + **R-NEW-344**
(recomposer suspension, v23) — it holds the entire modern Compose app class
(Dooz, RTTT, emmanuelmess tictactoe) below L5. R-NEW-361 itself is FIXED
(F-083): the probe spin was downstream of a depth-cap frame drop.

**What prevents complete HelloWorld?** Nothing — HelloWorldSelfAware is
visually proven end-to-end (L7 via EXT-01/02) at the current HEAD.

**What prevents a playable game?** Nothing for the proven set — GM Dice (real
F-Droid game) and Chess Clock both demonstrate launch→input→state→rendered
change at this HEAD, and tictactoe_golden proves 9-tap win-state play.

**What prevents Dooz?** R-NEW-376 (v18, new pinned frontier) / R-NEW-344
(v23) — see §3. The pre-S55 blocker R-NEW-361 is VERIFIED-FIXED (F-083).

**What prevents Notes content rendering?** The read face is a WebView
subclass (R-NEW-377 evidence); the generic WebView content model is the next
dependency. The app's state machine itself is FIXED (F-082) — mode-switch
input→state→render is proven at 2.06M px.

**What prevents Telegram?** Init-chain depth (REC-MISS surface, SafeIterableMap
stub, NativeLoader boundary) — no frame within the 540 s budget. Note: F-083's
deep-stack thread directly attacks the depth side of this frontier too.

**What prevents general APK compatibility?** The long tail of framework REC-MISS
surface plus the Compose P0s; every fixed law transfers (F-080/F-081/F-082/
F-083 were found in one app and are corpus-generic).

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
