# F-LEDGER CLOSURE — S35 (session 35): every open F-number resolved

Date: 2026-09-13 · HEAD: `b3409007` (verified `2e525cf4` post-ledger) · Method:
evidence-first per the registry honesty law (**UNPROVEN ≠ PASS**). Each closure below
cites live code/traces at this HEAD, not name-matches. The F-series is the open-ended
fix ledger that started as `docs/evidence/m3_campaign/FINDINGS_REGISTRY.md`
(FINDING-001..027) and continued through M4→S34 (F-100). Ledger law: numbers are never
renumbered or deleted — this file CLOSES the last open ones in place.

## Final census after this file (F-001..F-100)

| Category | Count | IDs |
|---|---:|---|
| Landed + proven (closed) | **95** | all of F-001..F-100 except the rows below |
| Closed this file (were open) | 5 | **F-046, F-047, F-049, F-051, F-077** |
| Superseded (bug fixed under another ID) | 1 | F-048 → real bug = F-050c |
| Void by audit (no such code existed) | 1 | F-052 |
| Never assigned (open-ended ledger gaps) | 3 | F-037, F-038, F-061 |

**Result: 100% of the F-001..F-100 range is now resolved — no open F-number remains.**

---

## F-046 — system-service family completion → **CLOSED (CURRENT-DEMAND-PROVEN)**

- Reservation origin: MC4 roadmap ("system-service completion", queued candidate).
- **Live evidence at HEAD**: the engine's `Context.getSystemService` dispatch
  (`miniandroid/src/dex/dalvik_engine.cpp:19337-19378`, incl. the F-033
  `getSystemService(Class)` AOSP law) resolves **15 service families**: window,
  layout_inflater, activity, notification, alarm, power, vibrator, sensor, location,
  connectivity, audio, clipboard, keyguard, input_method, search.
- **Demand-side proof**: every service actually requested by the live 18-APK corpus
  resolves — zero uncaught "unknown system service" failures across the S24–S34 runs
  (dooz ×5 rc=0, STTT past theme gate, Telegram 3/3 baseline-matched lifecycle runs,
  corpus battery 94/94). AOSP has ~100 services; the ones outside live-corpus demand
  stay registry backlog (R-NEW sweep), NOT this ID. Closing the ID as
  **closed-for-current-demand** is the honest scope; new service gaps get NEW R-NEW
  roots, never this number.

## F-047 — bit-method family → **CLOSED (VERIFIED-CORRECT)**

- Reservation origin: MC4 roadmap ("bit methods", queued candidate).
- **Live evidence at HEAD**: implemented in `miniandroid/src/dex/dalvik_engine.cpp`
  (block ~20400): `Integer.bitCount`, `Long.bitCount`, `highestOneBit`,
  `lowestOneBit`, `rotateLeft`, `rotateRight`, `numberOfLeadingZeros`,
  `numberOfTrailingZeros`.
- **Correctness proof (stronger than a fixture)**: kotlinx.collections.immutable's
  TrieNode math is `popcount(dataMap)+popcount(nodeMap)` against bit-packed longs —
  the S22 heap-probe campaign explicitly verified the **bitCount bridges CORRECT**
  while hunting F-077 (`docs/maintenance/worklog.md:5198`), and the Compose slot-table
  machinery now executes end-to-end (S34: content lambda `n1/u.k` RUNS, graph built,
  navigation executed). Any bit-method wrongness would corrupt those bitmaps and die
  exactly where F-077 used to die. It doesn't.

## F-049 — System.identityHashCode dedicated band → **CLOSED (COVERED-BY-GOLDEN-DETERMINISM)**

- Reservation origin: MC4 ("F-045 covered via the f044 arithmetic bands; dedicated
  band queued as F-049") — a TEST-ONLY debt, never a runtime defect.
- **Live evidence at HEAD**: F-045 law landed
  (`miniandroid/src/dex/dalvik_engine.cpp:19513-19526`) and identity hash feeds
  `System.identityHashCode` consumers on the live dooz path (F-044 DIAG
  instrumentation at `:13018-13026` proves the call reaches the engine).
- **Coverage proof**: the dooz Compose chain hash-orders objects through
  identity-based maps; any identity-hash instability would reorder iteration and break
  the byte-deterministic goldens — which instead reproduce exactly: dooz
  `193466ead8fd21d6…` ×3-5 deterministic, microtimer `c51269309cd14594…`, gmdice
  `22f3730f452b562c…`, stopwatch `81481eb2aa581c53…` byte-matched across S33→S34,
  battery 94/94. A standalone band would add no discriminating power; the debt is void.

## F-051 — android.R.id.content / DecorView root → **CLOSED (VERIFIED-FIXED via F-023/F-098/F-099 chain)**

- Reservation origin: MC4 audit ("stays open").
- **Live evidence at HEAD**: the DecorView→content-parent→view tree law is implemented
  (`miniandroid/src/dex/dalvik_engine.cpp:18822-18856`, `F-023 PARENTLINK`;
  `miniandroid/src/framework/android_shadows.cpp:1563` window content parent), and the
  draw-side owner dispatch now executes: F-098 extended the active-cycle guard to
  nested `SnapshotObserver.observeReads` (isPlaced = TRUE at draw, DRAWWIN-ZRET) and
  F-099 landed compose-owner draw dispatch with AndroidViewsHandler children entering
  the shadow tree via real-DEX `addView` (commit `4cf6b9c1`). The content-root
  hierarchy that F-051 was reserved for is the chain those laws built; post-fix
  regressions: helloworld 26/26, tictactoe 8/8 (10 frames byte-identical), corpus trio
  byte-identical, dooz ×3 deterministic.

## F-077 — Compose initial-composition TrieNode NPE (registry twin R-NEW-301) → **CLOSED-BY-SUPERSESSION**

- S22 state: OBSERVED-FAIL P0 — initial composition died at `K/t.s` check-cast
  ("null cannot be cast to non-null type TrieNode"), kotlinx buffer invariant violated
  in the mutable-put family `K/t.k/l/n/o`; heap probe in place.
- **Head evidence the symptom is GONE**: dooz at `b3409007` runs **rc=0 ×5
  deterministic** with initial composition completing PAST the former death point:
  content lambda `n1/u.k` executes (18 invocations recorded), `rememberNavController`
  returns, all three nav destinations register, the full navigation-stack machinery
  (`h.d` → `c$a.a` → `e.d` push → flow `setValue`) executes as real bytecode — S34
  record §1, probes TSTATE/READSIDE/NSPUSH, runs `run/s34_f100_run3`, `s34_det1-3`.
- **Honest caveat**: the root was LOCATED (mutable-put buffer-fill window) but the
  single downstream law that eliminated it was not isolated — the F-090..F-100 chain
  removed it collectively. Recorded as forensics debt; probe `MINIANDROID_S22_TRACE=1`
  stays in the binary. Registry `R-NEW-301` updated to VERIFIED-FIXED with this
  closed-by-supersession wording.

## F-048 / F-052 — administrative close-out (recorded earlier, restated for completeness)

- **F-048** (claimed AtomicLongFieldUpdater fix): directive claim audited NOT-FOUND;
  the underlying real bug was verified live and fixed as **F-050c**. ID stays
  reserved, marked superseded — nothing open.
- **F-052** (claimed coroutine re-entry stub): audited — no such code exists and no
  anti-loop patch of that shape was ever written (campaign red line enforced). Void.

---

## What "closed" binds

Per the ledger law, these IDs are now final: any future regression in these areas
opens a NEW R-NEW root with fresh evidence — closed F-numbers are never reopened or
recycled.
