# GP — S225-M wave LANDED: the uncommitted mandate diff recovered, gated, and tested (28/28 + new 22-row law battery); 6-pin gate ALL HOLD byte-exact on `e60821d52375ecf7`

**Reviewed HEAD:** `a4516511` (binary `e60821d52375ecf7`). Provenance gate per this mandate's §0: repo `Sh-TB/MiniAndroid-Compatibility-Runtime`, branch `main`, HEAD was `3f9042db` with a **dirty diff of 434 insertions / 158 deletions across 6 files** — the S225-M wave this session's crash left uncommitted. That diff is now recovered, fixed, gated, tested, committed and pushed.

## 1. IMPLEMENTED — the recovered wave (mandate §2/§3/§4/§6)

1. **§2 diagnostics races — FIXED (synchronized ingestion).** `TraceEngine::runtime_event()` now runs identity assignment + ring buffer + JSONL stream under ONE mutex (`rt_mu_`); emitters are no longer assumed main-thread-only (the per-thread JNIEnv law means GL/native/worker emitters are real). The terminal `std::cerr` sink runs OUTSIDE the lock — the documented ownership rule: no global lock held while writing user-visible output, so a slow terminal can never stall the ring's lock holder. Stage machine + divergence-candidate writes moved into the same critical section (they were shared state written from the same emitters).
2. **§2 stream-join law — NEW.** `TraceEngine::process_run_id()` publishes the boot trace's run_id; every graphics row now carries `run_id` + calling `thread`. A blank/garbled frame row is joinable to the exact resource/native/GL transition that produced it — the cross-stream correlation §2 demanded.
3. **§3 dispatch-precedence law — FIXED (finding 23).** `JNIBridge::register_native` REFUSES a later `HOST_COMPATIBILITY_STUB` when a `REAL_NATIVE_LIBRARY` owns the (class, method) key — a stub can no longer shadow a real native or report success for required initialization that did not occur. The upgrade direction (STUB → REAL) stays allowed; non-stub overwrites stay last-writer-wins with `reregistrations_` recorded; violations recorded in `precedence_violations_` (+ stderr `[GP585-PRECEDENCE]`). Introspection: `impl_type_of()`.
4. **§3 marshal honesty — FIXED (finding 24).** `NativeCallContext::arg()` keeps the legacy synthetic `INT(0)` face (every existing handler keeps its ABI) but RECORDS the miss in `marshal_errors`; new handlers get `try_arg()` (explicit nullptr face) and `validate_arity()` (one-call structured arity gate). No silent zero substitution anymore.
5. **§4 DT_STRTAB — FIXED (finding 20).** `list_dt_needed` now treats `DT_STRTAB`'s `d_val` as the VIRTUAL ADDRESS it is: mapped through the PT_LOAD table (`p_vaddr → p_offset`), bounded fallback face when no segment maps it, every read bounded by buffer + `DT_STRSZ`. The old VA==file-offset assumption held only for first-LOAD-segment pre-linked `.so`s.
6. **§6 pthread registry — FIXED (findings 6+7).** `pthread_shadow.c` rewritten around a locked-section law: lookup + state write + real-attr call atomic under `g_slots_mu` (kills the close-vs-use window where a caller touched a slot after unlock that `shadow_close` had swap-removed — the pointer-escape-after-unlock hazard §6 named). POSIX error semantics: `settype/gettype` on an UNKNOWN key answer `EINVAL` (was silent success — every setter degraded to a no-op with wrong synchronization semantics), exhausted registry answers `ENOMEM`, real-attr failure propagates.

## 2. TESTED — the mandate's regression-test requirement

`tests/s225m_wave_law_test.cpp` — **22 rows, all PASS**, linked against `pthread_shadow.o` (the real interposition object):
* PREC-1..6: real owns the key; stub does NOT shadow; refused registration does not replace; violation recorded; STUB→REAL upgrade wins; REAL→REAL last-writer-wins recorded.
* MARSH-1..5: legacy synthetic face unchanged; miss recorded; `try_arg` nullptr face; `validate_arity` min/exact gate + structured record; exact-arity pass.
* ELF-VA-1..2: a **synthetic ELF64 whose strtab VA (0x4260) ≠ file offset (0x260)** via PT_LOAD bias 0x4000 resolves DT_NEEDED through the mapping face; the legacy VA==offset layout still resolves via the bounded fallback.
* PTH-1..7: UNKNOWN key EINVAL ×2; init/settype/gettype round-trip; destroy; use-after-destroy EINVAL.

**`make test-all`: 28/28** (27 prior + this battery). Build fix en route: the recovered diff carried a duplicate `registered_count()` declaration (jni_bridge.h:214 vs pre-existing :690) — removed the added copy; the whole-file compile is clean.

## 3. GATED — golden pins before/after (mandate §7)

6-pin gate ALL HOLD **byte-exact** on the new binary `e60821d52375ecf7`: bouncy `8a6c24ac8a7d718e` / unote `3b8dcb0adbbc17a9` / dooz `a0fae9072313e2d1` / gmdice `3891679dff449331` ×2 identical / microtimer `b39665f68f3938e6` / ttt `7354c1b231cd581d` ×3 identical. 0 uncaught, 0 in-flight, no noise-suspect PNGs. The S225-M laws are byte-inert for the pins (expected: diagnostics/registration-contract changes, no rendering-path change) — the wave is regression-free by measurement, not assertion.

## 4. Residual honesty

* The pending-exception channel and local-ref arena remain the documented process-global one-channel law (per-thread exception state is the named follow-up wave).
* §5 (view/resource contract tests: WRAP_CONTENT, ConstraintLayout, GridView, ListView recycling, LayoutInflater attachToRoot matrix, resource qualifiers) and §6's Handler/Looper APK fixture remain OPEN — not claimed.
* The TSAN run was not performed this wave (single-host, no TSAN toolchain in the sandbox); the deterministic laws above are the equivalent recorded stress contracts, per the mandate's "state why" rule.

Next: the #582 native-execution census (route matrix + first-divergence per small native APK) — the immediate deliverable named on the living audit.
