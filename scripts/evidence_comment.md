## MASTER-3 RECONCILIATION PASS — EVIDENCE DIRECTORY (DIRECT URLs)

Audit executed per the reconciliation instructions: Phase 0 HEAD truth → Phase 1 full §0–§103 audit → Phase 2–5 body update (886 items, 501 regression-proven) → Phase 6 graph/registry → Phase 7 second-order audit → Phase 8 continued implementation. **Issue #9 body now reflects repository truth.**

### 1. HEAD / baseline truth
- HEAD at audit: `a8655a04` (branch `main`, tree clean, remote synced) — lineage: `eadaf695` → `1ab35251` (F-016 implementation landed by the prior session, verified here) → `cb5680f2` (F-016 battery stages + F-017) → `a8655a04` (§6 invariant count law).
- Toolchain restored after container reset via the AE gate: https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/scripts/bootstrap_toolchain.sh (aapt2 2.20-14304508 hash-verified from Google Maven).
- Corpus restored hash-verified (frozen URLs; HelloWorldSelfAware APK re-restored with exact SHA-256 `009b4671…` match per its frozen fixture document).

### 2. Regression battery (final, at HEAD a8655a04)
- `bash scripts/run_test_battery.sh` → **63/64 PASS, 1 honest FAIL**: DIRECT https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/scripts/run_test_battery.sh
- The single FAIL is the F-012 stage's rc-law: blocked by **FINDING-018** (second-run `rawQueryWithFactory` → legacy cursor fallback → silent null read → Kotlin Intrinsics NPE → F-016-honest PARTIAL). The F-012 golden's persistence law (row counts 1/2/1/2) and byte-determinism laws (A≡C, B≡D, 92 frames each) **PASS**.
- New F-016 stages: fixture build, default-mode honesty (unwind+PARTIAL+crash.log), strict-mode process death (CRASH + onStart/onResume dispatch refused).

### 3. New implementations (this session)
- **FINDING-016 (Family G, exceptions)** — implementation verified + battery-guarded: real Dalvik mid-stack unwind, APP-BOUNDARY escape law, default PARTIAL + nonzero rc, `MINIANDROID_EXC_STRICT=1` → CRASH latch refusing further DEX dispatch. Fixture: https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/tree/main/miniandroid/tests/fixtures/f016_exception_honesty
- **FINDING-017 (Family L + DEX guard)** — root cause: (a) missing `java.util.concurrent.locks` shadows; (b) active-cycle guard keyed `(class,method)` only, colliding Room's FIVE `Lm/a` (Kotlin SynchronizedLazyImpl) instances. Fixes: `LocksShadow` (https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/miniandroid/src/framework/locks_shadow.cpp — readLock()/writeLock() same-object non-null identity, deterministic lock/unlock/tryLock, loud newCondition boundary) + receiver-oid in the active-cycle key (dalvik_engine.cpp). Proof: microtimer 3-tap → SUCCESS + exactly 1 alarm row (was 0 under real unwind, masked before by FRAME-2).
- **FINDING-018** — registered, root-located: Room factory-cursor path misses DatabaseShadow on the second-open wrapper → legacy cursor fallback → silent null at invalid positions (violates the Android Cursor law) → null entity poisons the display adapter. Minimal fix direction documented in the registry.

### 4. Registry + evidence files (DIRECT)
- FINDINGS_REGISTRY (F-001..F-018): https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/docs/evidence/m3_campaign/FINDINGS_REGISTRY.md
- Phase-0 corpus truth (20 APKs, SHA-256, 2× determinism): https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/docs/evidence/m3_campaign/phase0/phase0_summary.json
- Commits: https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/commit/1ab35251 · https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/commit/cb5680f2 · https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/commit/a8655a04

### 5. Reconciliation statistics
- Families audited: 103 sections / 38 checkbox families + 65 process/matrix sections.
- Checkboxes audited: **886** (all `[ ]` placeholders replaced by factual states).
- Checked `[x]` (regression-proven at HEAD): **501**. Tagged-but-unchecked (T/V-partial/A/I/R/D/~/open): **385**.
- Genuinely unresolved (with inline root cause): dooz AndroidX SavedStateHandlesProvider (M2, F-011 residual); F-018 second-run cursor law (X3); Room UPDATE/DELETE law tests (FORGOTTEN P1); Math.random/Random determinism law (AD, FORGOTTEN P1); HashMap iteration-order law (E5); permission-model formalization (AB); native-method inventory (AH/AI); check-cast full law (B4); ellipsize/maxLines/spans boundaries (U2).

### 6. Second-order audit (Phase 7) — executed live
- F-016 (exception law) → ran microtimer guard → exposed F-017 (locks + lazy identity) → fixed → ran full battery → exposed the §6 invariant delta → documented per AZ → exposed F-018 (cursor law) → registered. The BG protocol ran end-to-end and is now battery-guarded at each step.
