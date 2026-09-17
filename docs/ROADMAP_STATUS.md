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
| Regression battery | **VERIFIED** | "BATTERY GATE: ALL PASS (94 stages)" at current HEAD (92 stages when the external EXT fixture is absent — the two EXT run stages collapse; the count law is documented in the battery script) |

## 2. What was fixed THIS session (root cause → law → proof)

| ID | Blocker | Root cause (evidence) | Fix | Proof |
|---|---|---|---|---|
| **F-080** | ChessClock "2-color dark blank" | `Resources.getColor(I, Theme)` two-arg overload: shadow read a fixed arg slot and resolved the NULL THEME (int 0) as the resid → every lookup black | resid = first INT-typed arg (robust under receiver-included/excluded conventions; AOSP law: references can never be the resid) | `[RES] resid=0x7f050005 → 0xff499ebd`; frame 99.3% nb/2 colors → 187 colors |
| **F-081** | ChessClock clock text = "null" | M3-19 active-cycle key was name-only: legal `formatTime(J)` overload delegation inside active `formatTime(J Z)` falsely matched as re-entry → stubbed null | include the method descriptor in the active-invoke key (JVM identity = name+descriptor) | 0 cycle stubs; `setText "10:00"` ×2; real clock face rendered |
| (infra) | battery 54-fixture collapse | disk 100% full + un-bootstrapped aapt2/ECJ/D8 toolchain on this machine | residue freed (7 GB, manifest recorded); `scripts/build/bootstrap_toolchain.sh` re-run; EXT fixture re-fetched SHA-verified | battery 92→94 stages ALL PASS |

## 3. Active frontier (P0 first, attack order)

1. **R-NEW-361 — Dooz v18 ScatterMap long-law** (OBSERVED-FAIL, P0).
   ASC decompile narrowed candidates: (a) growth-metadata long-shift sentinel
   writes, (b) probe index mask-wrap, (c) `Long.numberOfTrailingZeros`,
   (d) capacity normalization. Next: law-probe fixture, one candidate at a
   time. *Unblocks Dooz v18 composition and the ScatterMap-using family.*
2. **R-NEW-344 — Recomposer suspension / Job-active law** (OBSERVED-FAIL, P0).
   First non-blank Compose frame (`31ddd4d5…` covers dooz v23, emmanuelmess
   tictactoe, RTTT).
3. **Notes ListView/Adapter paint path** (P1, PRECISELY CHARACTERIZED at S54).
   7 views inflate, 0 unresolved; frame stays 99.1% near-white / 5 colors;
   item-content layer never paints. Same root-cause method as ChessClock
   (inflate→measure→layout→draw trace + ASC `getclass` on the adapter chain)
   is expected to yield a shared law. *Unblocks Notes L5→L7.*
4. **R-NEW-368 — uNote touch-target geometry** (P1, unchanged). Paint renders
   buttons; touch path finds no target on a 16-probe grid. *Unblocks uNote
   L6–L10 incl. the notes.db persistence ladder.*
5. **Persistence ladder L10** (P2) for the 5 interactive apps — ChessClock
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

## 6. Direct answers (S54 §12)

**What is the biggest runtime blocker?** The Compose first-frame pair
(R-NEW-344 recomposer suspension + R-NEW-361 ScatterMap arithmetic) — it holds
the entire modern Compose app class (Dooz, RTTT, emmanuelmess tictactoe) below
L5.

**What prevents complete HelloWorld?** Nothing — HelloWorldSelfAware is
visually proven end-to-end (L7 via EXT-01/02) at the current HEAD.

**What prevents a playable game?** Nothing for the proven set — GM Dice (real
F-Droid game) and Chess Clock both demonstrate launch→input→state→rendered
change at this HEAD, and tictactoe_golden proves 9-tap win-state play.

**What prevents Dooz?** R-NEW-361 (v18) / R-NEW-344 (v23) — see §3.

**What prevents Telegram?** Init-chain depth (REC-MISS surface, SafeIterableMap
stub, NativeLoader boundary) — no frame within the 540 s budget.

**What prevents general APK compatibility?** The long tail of framework REC-MISS
surface plus the two Compose P0s; every fixed law transfers (F-080/F-081 were
found in one app and are corpus-generic).

**What prevents one genuinely fully runnable application?** Nothing —
HelloWorldSelfAware IS the fully runnable reference application (full chain +
visual proof + interaction + reproducibility), and Chess Clock is the first
real corpus app at L7 with a visual state transition.

## 7. Binding laws (restated)

- Regression gate: micro-proof fixture → pixel golden → 3-run determinism →
  full battery (94 stages with the EXT fixture) → affected real-APK re-run →
  honest frontier update. Never silently reduce the battery.
- Forbidden: app-specific shortcuts, package-name hacks, blank-frame
  acceptance, rc=0-as-success, committing raw logs/traces/APKs/blank
  screenshots, token/secret material anywhere.
- One file per role: `ACHIEVEMENTS.md` (executions), `KNOWLEDGE_INDEX.md`
  (knowledge), `ROADMAP_STATUS.md` (this file), `README.md` (landing).
  Everything else: roleful, merged, archived, or deleted.

_Era roadmaps remain in place as history with header pointers where their
claims were absorbed here. Do not update them._
