# CONT-7 EXECUTION LEDGER — CURRENT-HEAD RECONCILIATION + UNSAFE/SEMAPHORE ROOT FIX

HEAD at execution: `e172fd7b` (working tree CONT-7) · FINAL BINARY SHA16: `382e595771901c00`
SKILL VERSION: manifest at docs/execution-skill/skill_manifest.json · SKILL SELFTEST: **13/13 PASS**
LAW-001: WIRED as gate law 0 (16-verdict contract 1.1, pre-install scope check) — verified this wave

## 1. SECTION 8 ANSWER — Unsafe dispatch (PROVEN VERIFIED_CURRENT)

The externally reported chain (`Unsafe.getObjectVolatile → REC-MISS → null volatile state → Semaphore ISE`, depth 36) **does not reproduce at current HEAD** — it predates the current dispatch wiring. Live proof with new bounded diagnostics (MINIANDROID_R337_TRACE=1):

```
[R337-UNSAFE] get obj=253 off=16 key="Ltp1;->_state$volatile" -> REF o171 caller=Ltp1;.j
[R337-UNSAFE] cas obj=761 off=80 cur=REF o372 exp=o372 upd=o883  (real CAS on real state)
```

The absent-DEX → bridge_to_api → R337 shadow law (directive §9's desired semantic law) is ALREADY the implemented generic behavior: `try_recursive_invoke` DEX-miss → `[REC-MISS]` diagnostic → hierarchy walk → `bridge_to_api` → `try_shadow_dispatch` → family handlers. No fix needed; the null-volatile face was fixed by earlier waves (R-NEW-337/345/395 + F-NEW-160 field identity). Recorded VERIFIED_CURRENT with instrumentation, not re-fixed (no duplicate root).

## 2. THE LIVE ROOT — F-NEW-251 (ROOT-CAUSED-FIXED, generic)

The dooz ISE ("The number of released permits cannot be greater than 1", `Lek1;.b pc=268`, depth 37, 17 in-flight errors) was NOT the Unsafe dispatch — it was **split-brain heap field storage**:

* interpreter iput/iget + Unsafe R337 → S134 qualified key `Lek1;->_availablePermits$volatile`
* AtomicShadow `Atomic*FieldUpdater` family (M4 F-028d) → **bare name** `availablePermits$volatile`

Two slots for one logical field: lock moved the qualified slot 1→0; the release entry `getAndIncrement` read the STALE bare slot (pre=1), wrote a parallel slot, and the kotlinx decomposed-permits guard then read the qualified slot and fired. Branch evaluation was proven FAITHFUL at runtime (`[C7-IF] if-le pc=249 v4=0 v5=1 taken → 260`) — the STATE diverged, not the branch.

**Fix (one point, generic)**: `DalvikHeap` field-key resolver (engine-installed): every bare-name heap field access from ANY layer resolves through the DEX instance-field tables of the class chain to the interpreter's qualified slot; engine-synthetic fields (`__*`, `array[i]`), framework-owned objects and non-DEX names keep bare keys (S134 law preserved).

**A/B (§12)**: BASE errors=17, ISE ×17 → PATCH ISE occurrences = **0**, errors=6. dooz 3-run byte-identical `d602648e8e401895` = the recorded dooz anchor SHA (zero visual drift, determinism preserved). NOT called "fixed" beyond evidence: dooz verdict stays DEFAULT_BACKGROUND_ONLY (honest) — the next face is a separate root (F-NEW-252).

## 3. SEPARATE ROOTS (§13 discipline)

* **F-NEW-252 (CLASSIFIED, P1)**: Compose Snapshot tracking IAE "Only add dependencies during a tracking" (`Lng0;.a pc=2 → Lel0;.Y pc=26 → Lt4;.dispatchDraw pc=148`) — the dooz draw frontier now; source-first next wave with a synthetic tracking-block probe. NOT fixed this wave.
* Dispatchers.Main ("Module with the Main dispatcher is missing") — not yet reached at HEAD (the run dies earlier); remains a tracked frontier.

## 4. REGRESSION BATTERY (§23) — ALL GREEN at binary 382e595771901c00

| Gate | Result |
|---|---|
| Anchors ×3 | 5/5 BYTE-IDENTICAL: opencalc `e364b001`, chess `b5a7a35d`, dooz `d602648e`, microtimer `da73010a`, unote `4f1a9e4e` |
| User goldens | 4/4 PASS (2048 / snakedeluxe / minicraft REAL_APP_CONTENT, helloworld L6) |
| Gate A probe | 97 PASS / 0 FAIL / 2 INFO |
| Negatives | 19/19 PASS |
| Reinstall matrix | 8/8 PASS |
| Uninstall proof | ALL PASS |
| Skill self-test | 13/13 PASS |

## 5. GOLDEN ABI CENSUS (§5 — from ACTUAL APK bytes, never package names)

`evidence/cont7/golden_abi_census.json` — ELF machines verified from real `lib/<abi>/*.so` headers:
dooz **MIXED** (183=AArch64, 3=x86, 40=ARM ELF32) IN-SCOPE via x86_64 · chess **MIXED** (183, 3, 40, 62=x86-64) IN-SCOPE · minicraft / snakedeluxe / sudokusolver / microtimer / unote / opencalc **PURE_DEX** IN-SCOPE. Zero ARM-only titles in the recorded set → zero census flips.

## 6. HONEST LIMITATIONS (NOT COMPLETE)

* **PENDING**: §6 acquisition of ≥12 new in-scope APKs (games/apps/Compose/storage-heavy) — NOT run this wave; the LAW-001 gate (16-verdict contract) and SKIP statistics bucket are ready to classify them. Acquire next wave from F-Droid/upstream releases, SHA-pin, run the full §6 protocol.
* **PENDING**: second independent APK live proof for F-NEW-251 fan-out (the law is heap-central; per-APK wiring is not required, but the directive's second-APK A/B is still owed).
* **PENDING**: §4 full 25-item achievement reconciliation → recorded as continuation work (the control-system files are marked HISTORICAL in-repo; CAMPAIGN_STATE.md is the live source; no contradiction found in the read subset).
* **PENDING**: R8 class-identity matrix (§14) — the dooz evidence STRENGTHENS conclusion A (R8 names are valid; the bug was generic field identity), but the 2-Compose-APK causal matrix is owed.
* **CLASSIFIED, open**: F-NEW-252 (Snapshot tracking), F-NEW-250 (serialization), Dispatchers.Main, and the ranked P0-P3 closeout set from CONT-5.
* External KB (§18): not imported this wave (no root added from it); F-NEW-251 originated from local runtime evidence only.
