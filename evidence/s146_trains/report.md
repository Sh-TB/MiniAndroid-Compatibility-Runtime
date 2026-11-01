# S146 — LIGHT TRAIN 64: the compose tap chain, decoded to the instruction

Date: 2026-11-01 · Directive: «ادامه بده 30 70 گیت هاب سورس کد اینترنت» · Base: 2c16d1a0 (S145) · Binary: ae97daf4 → **c620f6e0e7ec54f8** (diag-only probes, render-neutral)

## 1. TRAIN-64 (THE GAME dooz) — what the tap actually does now

Ground truth re-pinned from the internet per the directive:
- **dooz v1.0.23 source from GitHub** (`codeload.github.com/yamin8000/Dooz`, tag `1.0.23`): the board cell `DoozItem` is `Box.size.clip.background.**clickable(enabled, onClick)**` — **not** `pointerInput{detectTapGestures}`.
- **compose VERBATIM from Google Maven** (`reference/compose_167/`, 42 .kt kept in-repo): dooz's shape matches **compose 1.9.x** (`PointerInputEventHandler` fun interface exists in 1.9.4, absent in 1.6.7/1.7.0/1.8.0). The standing "1.6.7" label for this app is **retired**.
- clickable (foundation 1.9.4): `ClickableNode.createPointerInputNodeIfNeeded() = SuspendingPointerInputModifierNode { detectTapAndPress(onPress, onTap = { if (enabled) onClick() }) }`.

Class map (R8, pinned by signature+behavior this session): `Ljr1;`=SuspendPointerInputElement, `Lor1;`=SuspendingPointerInputModifierNodeImpl, `Lj6;`=the `{ detectTapAndPress(...) }` handler lambda, `Lu71;`=PointerInputChange, `Lne;`=BaseContinuationImpl, `Lzc1;`=ContinuationImpl, `Lzh;`=CancellableContinuationImpl, `Lor;`=CoroutineDispatcher, `Lss1;`=awaitEachGesture-level machine. **Retired mislabels**: `Liw0;` is the mutableVector backing list (NOT the filter); the `Lpv;` empty handler singleton is LEGAL (1.9.4's deprecated node ctor passes `PointerInputEventHandler {} // Empty Lambda, not used`).

**The chain is ALIVE end-to-end to the coroutine machinery** (all proven with runtime traces in `run/s146_train64/`):
1. DOWN+UP reach the clickable's inner node (`Lor1;#14115`) at all 3 passes (`Lor1;.J` = onPointerEvent).
2. Lazy launch (`pointerInputJob==null` → `launch(UNDISPATCHED)`) ran on the DOWN; the real handler `Lj6;` was born with the node (the 5th `[LOR1-CTOR]` line).
3. `dispatchPointerEvent` (`Lor1;.M0`) offered the event per pass; pass-Main matched; `offerPointerEvent` → `Lzh;.g` (resume) on the awaiter.
4. `Lzh;.q` (dispatchResume) took the **immediate/unconfined path** (`isDispatchNeeded=false` → `Lbo;.O`), never the dispatcher enqueue — explains S145's "[QUEUE] zero enqueues" honestly.
5. `Lne;.g` (BaseContinuationImpl.resumeWith) looped 12×, `invokeSuspend` ran on the machine chain (`Lq80;`/`Lss1;`/`Li6;`); the UP-Main offer hit the second-scope awaiter `#30029`.
6. The change objects are **clean** (DOWN pressed=1/prev=0, UP pressed=0/prev=1, consumed=0/0, type=Touch) and `changedToUp` evaluated **TRUE** where reached (`[T64-NEZ] nonzero=1`).

**The death, instruction-pinned**: `Lss1;.q` runs exactly ONE invoke per resume — the next await — **the gesture predicate (`isChangedToDown`) is never evaluated**. Zero `consume()` writes ever (`o/p` stay 0) ⇒ `awaitFirstDown` never returns ⇒ no `waitForUpOrCancellation` ⇒ no `onTap` ⇒ no `onClick` ⇒ the board never flips. The machines re-await because the **suspend-lambda state-machine label does not persist across the engine's resume chain** (label re-reads 0 / the await re-issues).

Fix direction (TRAIN-67): continuation-instance identity + label persistence in the interpreter. This single fix unlocks the dooz cell click AND every M3 clickable (opencalc buttons).

Diagnostics added (all env-gated, bounded, diag-only): `MINIANDROID_T64_CHANGE_TRACE` (`[T64-R]/[T64-W]/[T64-POS]/[T64-Q]/[T64-G]`), `[T64-C]` ctor-arg dump (under `MINIANDROID_KR1_CALL_TRACE`), `[T64-NEZ]` branch decision. Probe corrections: name-based `[PTE-DISPATCH]` is blind post-R8; earlier "i=isInitiallyConsumed=1" was a probe register-nibble bug — the ctor dump (23 slots) proved isInit=0 and `i` = PointerType.

## 2. TRAIN-64R — every old program re-tested (user directive «هر برنامه قدیمی رو تست بکن»)

- **Anchor wall 6/6 BYTE-EXACT** on the new binary: opencalc `63020bc7…` / chess `3f7e6707…` / dooz `851cc176…` / microtimer `bbd350b6…` / unote `7481e9b4…` / tower3d `11a38a5a…`.
- **Game family 7/7 EXACT-TO-PIN**: g2048 / tetris / snakedeluxe / minicraft / gmem / snakeneon / sqlnotes — all equal to the S145 pins. The probes are render-neutral; the games stay green («بازی هم یادت رفته» honored).

## 3. TRAIN-64T — Telegram SQLite re-check (x41)

Fresh store, 3 runs (40/40/60 frames): **SQLiteException 0 in all runs**, `[TG-SQLITE]` 20 natives over real sqlite3 + opendb OK, REAL `cache4.db` integrity=ok (independent python sqlite3), **user_version 178→179, schema objects 234→235** — the app's own schema code advanced another version on this engine. Face `bf5c9ef920aa32d7` ×3 (fresh-store law; the S145 face came from a seeded store). **The x41 fix HOLDS.**

## 4. TRAIN-64S — second SQLite program persistence

sqlnotes: writer run (INSERT ×2 → "Notes: 2") + **cold re-open** (zero taps, second process) reads rows=2 → renders "Notes: 2" + "[1] Note #1 (tap = DELETE)" + "[2] Note #2 (tap = DELETE)". Cross-process real-sqlite persistence re-proven. The 70%-milestone SQLite pair (telegram + sqlnotes) is green.

## 5. Artifacts

- `evidence/s146_trains/light_trains_64.json` — the full record
- `run/s146_train64/` — tap1…tap21 traces, tg_run1-3, sn_run1-2 (large traces not committed)
- `scripts/s146_train64_liw0_disasm.py` — targeted class/method disassembler
- `reference/compose_167/` — the VERBATIM compose 1.9.4/1.6.7 sources (kept in-repo so the next session survives sandbox recycle)
- `miniandroid/src/dex/dalvik_engine.cpp` — T64 diag probes only; no behavior change
