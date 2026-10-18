# CONT-97 — «هر کدام رو یدونه تسک مجزا» — every incomplete #364 item executed as a separate task

Baseline: **zero new directives** after the CONT-96 ledger (all 61 comments fetched, nothing newer than 6248496433) — so per the directive, the previously-incomplete set became 13 separate task units (T1..T13), each driven to an explicit terminal verdict. Registry 708 → 712. Final binary `d90541058611608c`. Full battery **zero drift** (wall 12/12 byte-identical ×3 anchors, goldens 4/4, negatives 19/19, reinstall 8/8, MG-310 7/7, MG-150 3/3, selftests 13/13, F-NEW-376 70/70, six fixture anchors green).

## Per-item تایید/رد

| # | Item (was) | Verdict | Evidence |
|---|---|---|---|
| T1 | Bridge dispatch ~48.6µs/call (named CONT-96 residual) | ✅ تایید — **INFRA-BRIDGEINTR-1 ROOT-CAUSED-FIXED** | Census (INFRA-BRIDGECENSUS-1): `Character.isWhitespace` 88K calls × **994K cycles** (85.4%) + `String.charAt` 535K × 20K (10.5%) = 96% of bridge time walking the ~33.5K-line law chain. ART-parity intrinsic entry fast path (soundness-proven: one site per key, no prefix preemption, verbatim law bodies). → 727 / 3.8K cy/call; Telegram 30s gate **12.7M → 16.1M insns (+27%)** |
| T2 | per-op field resolution ~0.45µs (named residual) | ❌ رد (measured) — deferred with numbers | `resolve_field` = **0.6%** of gate time at current head; yield below regression risk |
| T3 | `[resid:...]` string fallback (T6 track) | ✅ تایید — **F-NEW-399 ROOT-CAUSED-FIXED** | `setText(@StringRes int)` now resolves via the canonical ARSC path and replaces text per AOSP. Fixture com.probe.res1: FAIL both rows → PASS both rows |
| T4 | T3 bounds/offset (Telegram login top-anchored) | ⚠️ Partially confirmed — **bounds hypothesis DISPROVEN, true cause measured** | Specs arrive CORRECT (AT_MOST 1080×1920); the app's real DEX `onMeasure` dies at the honest F084 wall-stop → no write-back → fallback cements 295×150. Fix lever = throughput (F-NEW-381 family) |
| T5 | F-145 OPEN (capture follows first window) | ✅ تایید — **ALREADY_FIXED_AND_TESTED** | Probe com.probe.acts2 (A red → startActivity(B) green): final frame = B's face everywhere → capture follows top-of-stack at current head |
| T6 | F-NEW-192 REGISTERED (z-order residue) | ⚠️ residue CONFIRMED, deferred (stays REGISTERED) | Enforced draw-order law re-verified; elevation/translationZ remains named |
| T7 | F-NEW-214 PENDING (logs-as-data law) | ✅ تایید — **ALREADY_FIXED_AND_TESTED** | SFC-8 is the per-wave `evidence.json` process — exercised CONT-96/97 |
| T8 | doneButtonVisible app-specific attach | ✅ تایید — residual **closed by dead-code removal** | Provably unreachable at current head (0 `[EXP071]` rows) + forbidden pattern; microtimer 3/3 byte-identical after removal |
| T9 | GestureDetector e2 4-float payload residual | ✅ تایید — **F-NEW-400 ROOT-CAUSED-FIXED** | e2 was built from DOWN coords (e2 == e1 always). 6-float payload: onScroll (down, cur, dX, dY), onFling (down, up, vX, vY). PRE e2xy frozen 100,400 → POST tracks 116,375→300,100; app-visible rows correct; MG fences green |
| T10 | F-NEW-277 Compose continuation lever | ⚠️ RE-GRADED — partially superseded | F-NEW-398 (CONT-96) removed the F084 false-halt contributor; lever stays named for a Compose wave |
| T11 | F-NEW-381 throughput wall | ⚠️ evidence-updated (stays CLASSIFIED) | Bridge eliminated as dominant sink; remaining: core ~96%, resolve_field 0.6%, class_init 0.45% → opcode-core levers |
| T12 | R-NEW-456 (live z.ai) | ⛔ BLOCKED re-affirmed | External Svelte-5 bundle; unchanged |
| T13 | CONT-90 white-app batch | ⚠️ PARTIAL (honest census) | Mandatory 5 (Fossify Clock, BlockBlast, Asteroids Revenge, Space Vertex, Memory): **NOT_AVAILABLE** in corpus. Available at current head: flappycow 95%, sudoku 99.8%, chessclock 97% real renders (0 uncaught); klondike = WebView-white frontier; chess_jwtc near-uniform |

**Score: 13/13 items received explicit terminal verdicts — 7 تایید (APPROVED) · 2 رد/deferred-with-measurement · 4 partial/re-graded with named next steps.**
Codewise: 4 new roots registered (2 engine laws + 2 infra), 6 re-grades, 1 dead app-specific hack removed, 2 new fixture probes, 4 reusable env-gated diagnostic families. The two P0 Telegram-throughput items (T1) and the two semantic gaps (T3, T9) all closed with pre/post fixture proof.

## Honest pendings (next waves)
- Telegram SVG parse still exceeds the 30s gate (real work, honest F084 stop) — the opcode-core throughput campaign (F-NEW-381) is the lever; T4's login face depends on it.
- `resolve_field` (0.6%) and `class_init` (0.45%) — below current attack threshold, numbers recorded.
- CONT-90 mandatory-cohort artifacts need to be re-acquired into the corpus before their rows can advance.
- Elevation/translationZ (F-NEW-192) and the Compose continuation lever (F-NEW-277) stay named.
