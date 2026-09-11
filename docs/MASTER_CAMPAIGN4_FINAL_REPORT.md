# MASTER CAMPAIGN 4 FINAL REPORT

**HEAD:** `f3e992f7` (local == remote, verified)
**REMOTE:** `origin/main` = `f3e992f7` (ls-remote verified); tag `v0.0.3-Chantecler` = `7e18cd72`

**BATTERY:** 88 stages ALL PASS (`logs/battery_c4_final.log`; 85 + F-044 build/run/golden)
**REAL APK:** dooz `d81292cd` (SHA-pinned) re-run; 12-app corpus carried by battery goldens

**ROOTS DISCOVERED:** 2 (F-044 root re-framed and traced to its real cause; F-045 found in the §19 fail-soft sweep)
**ROOTS IMPLEMENTED:** 2 (F-044, F-045)
**ROOTS MICRO-PROVEN:** 1 dedicated (F-044: 7/7 bands, 3-run byte-identical `32b8a456…`); F-045 covered via the f044 arithmetic bands (dedicated band queued as F-049)
**ROOTS REAL-APK-PROVEN:** F-044 (dooz rc 1→0, NPE eliminated, 3-run deterministic); F-045 real-APK-reached
**ROOTS CLOSED:** F-044 family (per-frame context completeness — the return-descriptor was the last leaking per-frame field); family C return-boundary closed
**ROOTS STILL OPEN:** first-frame pump (Compose measure/layout/draw delayed dispatch) — root-located, PENDING

**TOP ROOTS BY IMPACT (measured):**
1. F-044 (C4) — whole-class silent corruption fix (int returns → booleans)
2. F-041 (M6) — exception-dispatch integrity
3. F-040 (M6) — collection-internals init
4. F-042 (M6) — long static fidelity
5. F-045 (C4) — identity hashing

**BIGGEST APK-LOADING IMPROVEMENT:** F-041/F-040 (carried from M6) — F-044 adds the return-integrity class
**BIGGEST DEX IMPROVEMENT:** F-044 (return-opcode interpretation law)
**BIGGEST FRAMEWORK IMPROVEMENT:** F-044 (Compose attach chain completes end-to-end)
**BIGGEST UI IMPROVEMENT:** none this campaign (honest — framebuffer unchanged)
**BIGGEST COMPOSE IMPROVEMENT:** F-044 + F-045 — derived-state dependency-change detection works; attach + dispatcher machinery executes

**BEFORE/AFTER (dooz):**

| Metric | Before (5a139afd) | After (774d6cdd+) |
|---|---|---|
| rc | 1 | 0 |
| app-boundary NPE | 1 (Intrinsics @0x0112) | 0 |
| onAttachedToWindow | died at 0x0112 | ran to last instruction |
| post-attach machinery | none | AndroidUiDispatcher + J$c + frame-clock chain |
| non-white pixels | 0 | 0 (honest — first-frame pump PENDING) |
| 3-run determinism | deterministic BLANK | deterministic (byte-identical) |

**DOOZ:** OLD FRONTIER = app-boundary NPE (stale derived state); **NEW FRONTIER = Compose first-frame pump**; **CURRENT ROOT = dispatcher/delayed-dispatch law (PENDING)**; **VISIBLE UI = NOT YET**; **NON-WHITE PIXELS = 0** (SHA `31ddd4d5…`, deterministic BLANK — never claimed as success)

**GITHUB ISSUES:** audited (9 open at campaign start)
**FIXED/SYNCED:** #9 campaign status anchor; #8 evidence table; #1–#7 per-EXP status classifications (HISTORICAL/PROVEN per §29, with evidence)
**REVALIDATION REQUIRED:** K-26 Telegram golden re-acquisition
**REMAINING:** first-frame pump (next P0); F-046..F-049 candidates queued

**RELEASE:** TAG `v0.0.3-Chantecler` @ `7e18cd72`
**ASSETS:** linux-x64 tar.gz (`0460173373d6…`), SHA256SUMS_v0.0.3.txt (Windows honestly omitted — no cross-toolchain)
**SHA256:** packaged binary `aefb1042cfe8…`; demo APK `5b273c2ef1…`; validator PASS
**README:** UPDATED (Latest Verified Progress; §50 dooz wording; stale claims fixed)
**CHANGELOG:** UPDATED (v0.0.3)
**ROOT DOCUMENTS:** UPDATED (audit ledger, roadmap, impact report, NEW: completeness matrix, discovery guide/evidence, release doc)
**REMOTE:** PUSHED (`f3e992f7` verified)

**THE FINAL QUESTION (§51) — do all roots need implementing?**
- **MUST IMPLEMENT:** first-frame pump (blocks every Compose app's UI).
- **HIGH VALUE:** F-046 service-registry completion; F-047 bit methods; F-049 ihc band.
- **CONDITIONAL:** Arrays inventory breadth; resource qualifiers; Canvas corners; IntentFilter matching — on corpus demand only.
- **SPECIALIZED:** JNI/ELF loader; Room adapters; text line-breaking.
- **DEFER:** audio default build; GLES wiring (no corpus demand).
- **REJECTED CLAIMS:** SnapshotKt.readError frontier; "Snapshot v0 next"; observer-scope-pairing framing (all superseded by live DEX evidence — the real defect was F-044).
