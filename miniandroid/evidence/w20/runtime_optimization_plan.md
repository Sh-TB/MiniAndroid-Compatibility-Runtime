# W20 runtime optimization plan (P0 Phase 3-5) — PENDING MEASUREMENT
Order (blocked on the Phase-1 baseline + Phase-2 instrumented ranking):
1. Method/class resolution cache with invalidation on class-load
   (invalidation semantics required — no stale-cache correctness trade).
2. Bitmap decode memoization keyed by (resid, density) — BitmapStore hit
   path (decode_and_register re-entry).
3. Incremental state-list re-pick: only nodes whose state flags changed
   re-pick (WS9 arms already store the flags — the dirty-bit plumbing is
   the missing piece).
Each change: focused bench -> 43+5 battery -> affected APK screenshot-hash
parity -> only then adoption. No app-specific shortcuts.
