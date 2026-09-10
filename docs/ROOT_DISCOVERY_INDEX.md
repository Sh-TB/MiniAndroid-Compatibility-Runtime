# ROOT DISCOVERY INDEX — MASTER CAMPAIGN 3/M8 (2026-09-10)

Discovery trail for the M8 session (continuation of Campaign-4 at remote
HEAD 6ff11eb2). Protocol per campaign §8: every root carries hypothesis →
live trace → upstream verification → generic fix → proof.

## Session discovery chain (chronological, LIVE evidence)

1. **State reconciliation.** Local main was 10 commits BEHIND remote
   (fast-forwarded to 6ff11eb2 = M7/Campaign-4 final: battery 88/88,
   F-040..F-045 landed). The directive summary's "F-046..F-052 fixed"
   claim matched NO commit on any HEAD — rejected per evidence law
   (see ROOT_IMPACT_MATRIX.md reconciliation table).

2. **Probe runs at HEAD.** dooz deep run (14.6 MB trace, rc=0, 0
   non-white): `AndroidComposeView children=0 size=(0x105)` +
   `[REC-MISS] Landroid/view/Choreographer;.getInstance caller=LJ$a;.c`
   + ZERO doFrame dispatches in the entire trace.

3. **F-050a root-located.** DEX disassembly of LJ$a.c (CurrentThread),
   LK.u (AndroidUiFrameClock.withFrameNanos): both paths end in
   `Choreographer.postFrameCallback`; the frame callback J$c.doFrame is
   the ONLY resume path for withFrameNanos. The runtime had no
   Choreographer family → the callback was dropped → first frame parked.

4. **F-050b landed en route.** The ISE that killed the await was
   message-blind; implementing the OpenJDK Throwable detailMessage law
   exposed the exact message.

5. **F-050c root-located.** Message = "unexpected close status: -1".
   Upstream (kotlinx.coroutines BufferedChannel.kt, fetched via GitHub
   code search + raw): statuses {0,1,2,3} << 60; -1 ⇒ arithmetic-shr of a
   NEGATIVE packed state. ATOMIC-OP forensics:
   `getAndIncrement pre=0x0` → next read `pre=0xffffffffffffffff` — the
   prefix-match delta bug wrote oldv-1.

6. **F-050d root-located.** Post-fix the cancellation persisted
   ("Channel was cancelled"). Stack capture
   (snapshot_top_first): J$c.run → J.O → W1/N.run → g0.t → LB0/b.x
   (cancelConsumed) → LY1/b.c. g0.t disassembly: the channel iterator's
   resume path does `sget Boolean.TRUE` (R8 valueOf rewrite) →
   SGET-MISS → NULL → unboxed false → consume loop exits → cancel.

7. **Next frontier root-located, NOT fixed (Job-active law).** With all
   three fixed, the frame callback is STILL removed before the pump fires
   — now via the coroutine-cancellation cascade (LE1/a.y →
   Choreographer.removeFrameCallback through K$a invokeOnCancellation).
   The Recomposer's frame-await job collapses to inactive. This is the
   M9 battle (roadmap item 10).

## Probe record (2026-09-10, HEAD 6ff11eb2 + M8 fixes)

| Probe | rc | 3-run SHA | Non-white | Frontier |
|---|---|---|---|---|
| dooz (MINIANDROID_DISPATCH_ATTACH=1) | 0 | 31ddd4d5… (identical) | 0 (deterministic BLANK — never claimed as visual success) | Job-active cancellation of the frame await |
| TicTacToe (real com.emmanuelmess) | 0 | 31ddd4d5… (identical) | 0 | T3/BLANK — libGDX GLSurfaceView boundary (historical, unchanged) |
| Telegram | — | — | — | BLOCKED: official dl serves a 1.2 MB stub installer (sha 480263f8…); pinned 82 MB v10.14.5 (193ad551) not reacquirable from any reachable source; fetch correctly rejected (zero-skip law) |
| f050_frame_pump fixture | 0 | byte-identical ×3 | 7 bands | 7/7 GREEN (visual proof) |

Battery: **91/91 ALL PASS** (88 + 3 F-050 stages) —
logs/battery_m8_full.log.
