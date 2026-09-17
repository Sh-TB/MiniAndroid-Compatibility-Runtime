# ROADMAP — Canonical, Reconciled (S52)

> **SINGLE SOURCE OF TRUTH for what is done, what is open, and what is next.**
> Reconciles ALL historical roadmaps against actual committed evidence: nothing
> disappeared because it got old; nothing is checked without evidence.
> Supersedes: `docs/runtime/FUTURE_ROADMAP.md` (EXP-023 era), 
> `docs/runtime/EXP037_IMPLEMENTATION_ROADMAP.md` (EXP-037 phases),
> `docs/research/ROOT_LAW_IMPLEMENTATION_ROADMAP.md` (law-tier ladder — kept as
> the live tier source), campaign TODO blocks in session records.
>
> Task vocabulary: `DONE` · `PARTIALLY DONE` · `VERIFIED` ·
> `IMPLEMENTED BUT UNVERIFIED` · `BLOCKED` · `OBSOLETE` · `DUPLICATE` · `OPEN`.
> Status vocabulary for evidence: see `docs/EXECUTION_ACHIEVEMENTS.md` §0.

## 1. Reconciliation of historical roadmaps

### 1.1 FUTURE_ROADMAP (EXP-023 era, 2026-08-12)

| Item (as written) | Reconciled status | Evidence |
|---|---|---|
| DEX parser production-ready | **DONE** | real-dalvik execution of 20+ real APKs |
| APK parser production-ready | **DONE** | battery G06-G08 + all corpus runs |
| Interpreter 70+ opcodes | **DONE (superseded)** | full real-dalvik engine; semantic battery (long/cmp/conv/bridge/switch) PASS |
| Class resolver good coverage | **DONE (superseded)** | Hilt/DI chains resolve in dooz23 |
| Application runtime "partial" | **DONE** | manifest-Application binding (R-NEW-341), lifecycle → RESUMED on every SUCCESS app |
| Resource parser "partial" | **DONE** | aapt2-linked builds, M3 ARSC/style chain PASS |
| Software renderer "partial" | **DONE** | 6 full-render apps + pixel goldens + hello_widgets |
| Trace engine comprehensive | **DONE (superseded by S52 log policy)** | QUIET/DIAGNOSTIC/FORENSIC levels; raw traces now OUT of the tree |
| API stubs ~40% | **PARTIALLY DONE (by design)** | REC-MISS accounting + shadow registry; long-tail tracked per-app |
| P0 "invoke-static completeness" plan | **DONE** | engine far beyond the 20-method plan |
| "Compatibility score 55.2 projected" | **OBSOLETE** | superseded by per-app ladder in EXECUTION_ACHIEVEMENTS |

### 1.2 EXP037_IMPLEMENTATION_ROADMAP (persistence → Telegram phases)

| Phase (weeks) | Reconciled status | Evidence |
|---|---|---|
| A: File sandbox | **DONE** | package-scoped data dirs (`--data-root`) |
| A: SharedPreferences | **DONE** | R-NEW-367 fix + S52 round-trip experiment |
| A: Basic Context | **DONE** | Context law chain across SUCCESS apps |
| A: Synthetic app integration | **DONE** | fixture battery chain |
| B: SQLite integration | **PARTIALLY DONE** | notes.db created + round-trips (S52); full CRUD ladder not driven |
| B: DB abstractions | **PARTIALLY DONE** | on-demand coverage; no corpus blocker active |
| B: Activity lifecycle | **DONE** | full chain, F-0xx laws |
| B: Application class | **DONE** | R-NEW-341 (real DEX-bound manifest Application) |
| C: Real APK loading (Telegram) | **DONE** | 73 MB APK loads; init runs 540 s inside real code |
| C: Static analysis | **DONE** | androguard-era + **ASC** (S52 startup-path card) |
| C: Execution attempt | **PARTIALLY DONE** | no first frame; REC-MISS init chain ranked |
| C: Stub native library experiment | **OPEN** | NativeLoader.initNativeLibs boundary decision pending |

### 1.3 ROOT_LAW_IMPLEMENTATION_ROADMAP (law-tier ladder — live source)

| Tier/item | Reconciled status | Evidence / note |
|---|---|---|
| P0 landed set (F-050 family etc.) | **VERIFIED** | battery 92/92 incl. F-0xx law chain at HEAD `1b37afd1` |
| Item 10 — Job isActive / coroutine-completion law | **OPEN (P0)** | = R-NEW-344 recomposer suspension; blank Compose frame class `31ddd4d5…` still the first-frame blocker |
| F-046 system-service entries | **PARTIALLY DONE** | R-NEW-339 landed autofill + getSystemService registry; INPUT_METHOD/WINDOW/NOTIFICATION tail open |
| F-047 Long/Integer bit methods | **OPEN → PROMOTED** | R-NEW-361 suspect (c): `Long.numberOfTrailingZeros` — ASC decompile now points here directly |
| F-048 measure/weight edge semantics | **OPEN** | quantify on a weights-heavy APK first |
| F-049 identityHashCode micro band | **OPEN** | — |
| 15-18 (IntentFilter/qualifiers/Canvas corners/reflection) | **OPEN (evidence-gated)** | as written |
| 19 JNI/ELF loader contract | **BLOCKED-CLASS** | native .so boundary (Telegram NativeLoader); classify missing-library separately, never as Java blocker |
| 20 Arrays family | **OPEN** | — |
| 21-22 (P3 specialized) | **OPEN** | — |
| Deferred/rejected set | **REJECTED (kept)** | snapshot-v0, observer-scope pairing, pump-on-faith, app-specific shortcuts — all still rejected |
| Regression gate law | **VERIFIED (binding)** | battery = 92 stages; never silently reduce |

### 1.4 Campaign/S51-S52 worklist (worklog TODO reconciliation)

| Item | Reconciled status | Evidence |
|---|---|---|
| S51: publish all old pushes / purge verification | **VERIFIED** | S51-PUSH-VERIFY record; remote == local, fresh-clone checks |
| S51: per-app all-front audit | **DONE** | S51-ALLFRONT-AUDIT (17 fresh runs at rebuilt HEAD) |
| S51: screenshot gallery (JPG ≤100 KB, SHA) | **DONE** | `docs/evidence/s51_audit/` + SHA256SUMS |
| S51: roadmap reconcile | **DONE** | THIS FILE |
| S51: application matrix consolidation | **DONE (by consolidation)** | `docs/EXECUTION_ACHIEVEMENTS.md` §1 IS the per-app matrix; separate `APPLICATION_MATRIX.md` deliberately NOT created (duplicate avoidance); compatibility-matrix MERGE-CANDIDATE recorded in KNOWLEDGE_INDEX §4 |
| S51: README landing page | **DONE** | README updated (S52) with Execution Achievements link |
| S51: new games (crossword / Wordle-like / ball-or-minesweeper fixtures) | **OPEN** | deferred; corpus games exist as external APK targets instead |
| S52: ASC integration + evidence cards | **DONE** | `docs/evidence/s52_asc/README.md` |
| S52: persistence experiment | **PARTIALLY DONE** | chessclock/unote storage round-trip VERIFIED; state-delta ladder pending (blocked by R-NEW-368 for uNote) |
| S52: evidence/log/screenshot policies + residue removal | **DONE** | S52_RESIDUE_RECORD; 130 files removed from tree (history retained) |
| S52: knowledge index + map | **DONE** | `docs/KNOWLEDGE_INDEX.md` |
| S52: WhatsApp honest test | **BLOCKED** | APK unavailable (0-byte placeholder proven) |

## 2. Active frontier (P0, in attack order)

1. **R-NEW-361 — Dooz v18 ScatterMap long-law** (OBSERVED-FAIL, P0).
   ASC decompile narrowed candidates: (a) growth-metadata long-shift sentinel
   writes, (b) probe index mask-wrap, (c) `Long.numberOfTrailingZeros`,
   (d) capacity normalization. Next: law-probe fixture, one candidate at a
   time. *Unblocks: Dooz v18 composition; likely the whole ScatterMap-using
   corpus family.*
2. **R-NEW-344 — Recomposer suspension / Job-active law** (OBSERVED-FAIL, P0).
   First non-blank Compose frame (`31ddd4d5…` class covers dooz v23,
   emmanuelmess tictactoe, RTTT).
3. **R-NEW-368 — uNote touch-target geometry** (OBSERVED-FAIL, P1, NEW S52).
   Paint path renders buttons; touch path finds no target anywhere on a
   16-probe grid. Next: verbose run → ViewShadow bounds for view_ids 13/14/15
   → paint-vs-touch rect divergence. *Unblocks: uNote L6-L10 incl. the notes.db
   persistence ladder.*
4. **Telegram init chain** (PARTIAL). Ranked targets from the ASC startup card:
   REC-MISS static-init surface → SafeIterableMap iterator law →
   NativeLoader boundary decision (stub vs skip).
5. **Persistence ladder** for SUCCESS apps (chessclock prefs interaction →
   PERSISTENCE VERIFIED upgrade; unote after R-NEW-368).

## 3. Tier ladder (demand-driven, unchanged rules)

- **P1:** F-046 service tail · F-047 bit-method family (folded into #1) ·
  F-048 weights · F-049 identityHashCode band · corpus game ladder (L6+ on
  battery-interactive games).
- **P2 (evidence-gated):** items 15-18/20 as written in the law roadmap.
- **P3:** items 21-22.
- **New-fixture backlog (S51 carryover, OPEN):** crossword / Wordle-like /
  ball-or-minesweeper — only after the P0 frontier shrinks; corpus APKs are
  the interim demand signal.

## 4. Binding laws (unchanged, restated)

- Regression gate: micro-proof fixture → pixel golden → 3-run determinism →
  full battery (92 stages) → affected real APK re-run → honest frontier update.
  Never silently reduce the battery.
- Forbidden: app-specific shortcuts, package-name hacks, blank-frame
  acceptance, rc=0-as-success, committing raw logs/traces/APKs/blank
  screenshots (S52 evidence policy), token/secret material anywhere.
- One file per role: `EXECUTION_ACHIEVEMENTS.md` (executions),
  `KNOWLEDGE_INDEX.md` (knowledge), `ROADMAP.md` (this file), `README.md`
  (landing). Everything else: roleful, merged, archived, or deleted.

_Era roadmaps remain in place as history with header pointers where their
claims were absorbed here. Do not update them._
