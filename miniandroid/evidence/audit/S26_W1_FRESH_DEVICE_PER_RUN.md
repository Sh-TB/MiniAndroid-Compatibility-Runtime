# S26-W1 — the fresh-device-per-run law (randomix determinism root-cause closure) — 2026-11-22

**Base: S26-A revalidation tip (`c7565dbb`). This closes the S26-A NEW-FINDING: randomix's run-to-run nondeterminism.**

## 1. Root cause (measured, first-divergence method)

Binary diff of the S26-A traces (`randomix_r0` reached the blank face `31ddd4d5`; `randomix_r1/r2` stayed at boot `b5a7a35d`), with timing/RSS/ASLR-pointer noise normalized, puts the FIRST behavioral divergence at `RandomixApplication.onCreate`: in r1 the engine logs `[PREFS] Loaded com.minar.randomix_preferences.xml` — it found and loaded a prefs file LEFT IN THE WORKSPACE by the previous run (r0 wrote it via the `[PREFS] Saved` commit path). The app's own init flow (first-run vs returning-user) branches on that state — same binary, same APK, different workspace state → different face. The determinism contract was violated by CROSS-RUN STATE LEAKAGE through the persisted per-package data families (`<root>/data/data/<pkg>` shared_prefs etc.), not by any thread/oid/scheduling nondeterminism: the divergence is fully explained by the file the previous run left behind.

## 2. The law (S26-W1, implemented)

**Fresh-device-per-run**: `Storage::set_context_package()` — the single identity-bind choke point (`dalvik_bridge` caller binds the manifest package before any app code) — now RESETS the package's three persisted data families (`data/data/<pkg>`, `data/user_de/0/<pkg>`, `storage/emulated/0/Android/data/<pkg>`) before the eager AOSP dir-family creation, so every run starts from a fresh install. Defensive guards: wipe skipped for an empty or traversal-containing package; `remove_all` with `error_code`; one honest `[DATA-ROOT] fresh-data-per-run: reset <pkg> (removed N entries)` line on both streams. Opt-out: `--keep-app-data` (new CLI flag → `Storage::set_fresh_data_per_run(false)`) for operators who need persistence across runs. Mid-run persistence is UNTOUCHED (a run's own writes still work: dice's 5-frame animation set and notepad's in-run DataStore flow are byte-stable below).

## 3. Measurement (final S26-W1 binary)

- **randomix ×4**: `d1..d4` ALL IDENTICAL — face set `{31ddd4d5, b5a7a35d}` ×4, `prefs_loaded=0` ×4, `fresh-data-per-run: reset` ×2/run, verdict DEFAULT_BACKGROUND_ONLY ×4. **The S24 golden blank face `31ddd4d5` is RESTORED deterministically** (the S25/S26-A b5a7a35d-only runs were the returning-user leak path).
- **Regression wall (all canonical last frames byte-identical)**: six-pin np `31ddd4d5b8e6d18e` ✓, dice `0de952bf75f89409` ✓ (full 5-face animation set unchanged: `0ab178b9,0de952bf,0efd9882,46b07062,beabbef0`), pz `6375a3a3813af176` ✓ (the S24-attributed face), guess `87fe26766fc48d06` ✓, ttt `d55056a8928a26ff` ✓; flip ×2 `b270ff04` with the full S25 marker set (ADOPT=1, setPresenter=1, EXP060-LISTENER=1, honest VectorDrawable IMAGE-BLOCKED=1 per run); minos ×2 `b5a7a35d` (EventBus path stable); HelloWorldToast `acdd9f05` ✓; chess `d602648e` ✓.
- **Law battery**: `evidence/s26/s26w1_law_battery.log` (53 tests, per-test build→run→delete; summary at the file tail).

## 4. Files

`src/storage/data_root.h` (law docs + `set_fresh_data_per_run`/`fresh_data_per_run`), `src/storage/data_root.cpp` (the wipe at the bind), `src/main.cpp` (`--keep-app-data`). Evidence: `evidence/s26/randomix_d1..d4`, `w1_np/dice/pz/guess/ttt`, `w1_f1/f2/m1/m2`, `w1_HelloWorldToast-1.4.0-android`, `w1_dk.cocode.chess_5022`, `s26w1_build.log`, `s26w1_law_battery.log`; loop script `scripts/s26_law_loop.sh`; matrix `evidence/s26/s26w1_matrix.tsv`.

**Status vocabulary**: ROOT-CAUSED (cross-run state leakage, first-divergence measured) / IMPLEMENTED (S26-W1 fresh-device-per-run + opt-out) / TESTED (randomix ×4 deterministic; regression wall 11 apps canonical-identical; law battery) / RESTORED (randomix S24 golden `31ddd4d5`).
