# CONT-73 RESULT — F-NEW-376 FIXED ON REMOTE + TEN-APP SHARED-HARNESS TRIAGE LEDGER

Direct answer to the CONT-73 request (6208489127) and the independent audit (6218720139). This wave's commits are `5a0d5f1b` (law + evidence + triage + hygiene) on top of `befb9cca`.

## 1. Synced HEAD + tree state + binary

- Start of wave: local tree was a stale CONT-10-W6 snapshot (`e99c2fbd`) in a reset container; it was **fast-forwarded 162 commits to `befb9cca` == origin/main BEFORE any work** — the audit's premise (remote had no F-NEW-376 fix) was accepted, and the lost session's uncommitted local claims were re-done from the synced tree rather than trusted.
- This wave's HEAD: `5a0d5f1b` (pushed; secret guard PASS).
- Runtime binary sha256-16: `1ecb1949e5fa59cf` — delta vs the CONT-72 record binary `19d090e78c5d8e23` = `miniandroid/src/main.cpp` installer law ONLY.
- Working tree after commit: clean except sandbox-state files the gates legitimately refresh (`probe_store/` probe results, skill selftest report) — no source, fixture, or evidence deltas left uncommitted.

## 2. F-NEW-376 — staged-generation install atomicity law (ROOT-CAUSED-FIXED, P1)

**The law (one canonical commit point):** the COMPLETE new generation — `base.apk` + `package.json` + `lib/<abi>/` + `native_libs.json` — is built under `<store>/data/app/.staging/<pkg>.<pid>`; the staged bytes are sha-verified against the source; then the generation commits by a directory switch:
- **fresh install:** ONE `rename(staging → live)` — the whole commit is atomic.
- **update:** park old → `.trash/<pkg>.<pid>`, promote new, drop parked. POSIX `rename()` cannot atomically replace a non-empty directory (ENOTEMPTY), so the two-rename window is unavoidable — and is **closed by rollback**: any promotion failure renames the parked old generation back to live; if rollback itself fails, the wave hard-errors and reports the preserved trash path. Both window behaviors are fault-injection-proven below.
- The staged record is **byte-identical after promotion** (shared `record_json_body` writer describes the LIVE location; no post-promotion rewrite). Readers (`run --package`, `list-packages`, `pkgaudit`, `pkginspect`) resolve only committed generations; `.staging`/`.trash` are hidden from listing. Data-dir scaffolding moved post-commit.

**Deterministic fault-injection capability (env-gated, generic):** `MINIANDROID_INSTALL_FAULT=stage_copy|stage_hash|record_write|lib_extract|promote|promote_mid|cleanup`. `stage_hash` injects a REAL byte flip into the staged copy (the integrity gate must catch it — positive control, not a simulated skip).

**Battery: 70/70 PASS** (`scripts/cont73_fault_injection.py`), boundaries × paths × invariants:

| Boundary | Update (V1→V2) | Fresh |
|---|---|---|
| parse/validate (garbage APK) | rc≠0, V1 intact + RUNS | rc≠0, no state |
| stage_copy | rc≠0, live==V1 sha + vc=1 record, V1 RUNS | rc≠0, no generation, run refuses |
| stage_hash (real flip caught) | same invariant | same |
| record_write | same | same |
| lib_extract | same | same |
| promote | same (live untouched) | same |
| promote_mid (park→rollback) | **old generation ROLLED BACK + RUNS** | n/a (no parked gen) |
| cleanup | rc=0, live==V2 + vc=2 agree, V2 RUNS; parked V1 left in .trash with an explicit WARN (documented behavior) | same commit semantics |
| success | rc=0, V2 sha + vc=2 agree, `[C72-VERSION] code=V2` executed | same |

Every row asserts the **no-mixed-generation invariant** (base.apk sha vs record versionCode pairing) and **list hygiene** (`.staging`/`.trash` never listed). Probe pair: `run/cont72/c72priv_v1.apk` `0c56006b7cb42c92` (vc1) / `c72priv_v2.apk` `1e99e4db786d3c74` (vc2), same package `com.probe.c72priv`, real aapt2/ECJ/D8. The battery itself caught one implementation gap before any evidence claim (the `promote` hook fell through on the update branch; fixed, re-run, 70/70).

**Gate battery at `1ecb1949e5fa59cf`** (audit item 1 — exact exit codes/faces at the CURRENT binary, cont71 expectations, not the stale cont68 set):
- `cont71_gate.sh` wall: **13 rows × 3 = 39/39 MATCH** — csw `d3c26b73ee21e571`, dooz `31ddd4d5b8e6d18e`, flappycow `13cf47464d9787f4`, g2048 `f43face08299ffc6`, gmdice `3891679dff449331`, microtimer `bbd350b6c14fbd52`, opencalc `f25b754c4565c38b`, simplecalc `2ac5d8d0cbf9552a`, tanana `afe0bd8dd4d09ca6`, tttdeluxe `db1d633d77b5819a`, unote `90a67cc1ddda57b7`, dooz180 `c94da5a928ea213b`, memory warm `c559b630dd8f0f0f` (sideload-path runs: rc=1 on budget expiry is the recorded norm for budget rows, rc=0 for the others — all faces byte-identical). Zero drift from an installer-only delta, by construction AND verified.
- Gate A probe rebuilt (`gate_a_probe.apk 1792540b…`, native lib `ad413625925ed8e5` == record): **98 PASS / 1 INFO / 0 FAIL**; **negatives 19/19** (after the canonical probe prelude — without it the recorded 9/19 env-state artifact reproduces, as documented in CONT-72); **reinstall 8/8**; **goldens 4/4**; **skill 13/13**; **validator PASS**; projection regenerated id-for-id (682 roots).

## 3. Ten-app shared-harness triage (Batches A + B, current HEAD)

One shared store (`run/cont73/triage_store`), per app: install via the NEW staged path + one bounded warm probe (`--frames 5 --max-seconds 90`). Census = the gate-standard pixel_metrics law + F-NEW-233 frame-truth lines. Row format per the request:

| # | package | apk_sha16 | version | ABI/ELF | binary | checkpoint / first divergence | exact trace | shared root ID | status | screenshot sha / pixels | next action |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | eu.quelltext.memory | `4dd3957983e3c3f3` | 1.7 (vc7) | none (WebView) | `1ecb1949e5fa59cf` | BOOT 7/7 capture_output ok; no exception | — | — | **REAL_APP_CONTENT** (new first-triage face) | `35295a57f6c898ab` / nonbg 11.9%, 204 colors | record as baseline |
| 2 | com.chessclock.android | `5ca6f2c54c05efe7` | 2.11.2 (vc29) | none | same | clock face rendered; BOOT 7/7 ok | none | F-NEW-363 (verified current) | **REAL_APP_CONTENT == recorded face** | `fe3ae1167c9e968c` / nonbg 8.8%, 248 colors | none |
| 3 | com.simondalvai.ball2box | `aef33b17a0ae3c90` | 4.1.9 (vc69) | **ARM-only** (arm64-v8a, armeabi-v7a) | same | Godot fragment created (`FullScreenGodotApp`); native Godot engine never boots on x86 | uniform (48,48,48) surface | UPP-001 family | **PREREQUISITE_MISMATCH** | `b5a7a35d5fe0564b` / nonbg 0.0, 1 color | blocked on binary translation; not a renderer bug |
| 4 | org.opensurge2d.surgeengine | `c1020c5a1e594b21` | 6.1.3.0-fdroid (vc30650) | **ARM-only** | same | `AllegroActivity: nativeOnCreate failed` (honest refusal logged) | refusal line recorded | UPP-001 family | **PREREQUISITE_MISMATCH** | `31ddd4d5b8e6d18e` / nonbg 0.0 | blocked on binary translation |
| 5 | page.codeberg.lanticy.guandan | `ccc74b5948154e7f` | 1.2.2 (vc7) | x86+x86_64 (`libandroidx.graphics.path.so` — androidx helper, NOT a game engine) | same | window root EXISTS (app-owned dark-green (8,36,26) surface); `verdict=DEFAULT_BACKGROUND_ONLY, first_missing_stage=APP_DRAW_OPS` | `R350-FORNAME` kotlin-reflect CNFE | **shared candidate R350 (below)** + F-NEW-256/265/277 draw frontier | **DEFAULT_BACKGROUND_ONLY** | `4e58f3a378891497` / nonbg 0.0 | fold into recorded draw frontier |
| 6 | org.secuso.privacyfriendlysudoku | `1aff917f4ac9952b` | 3.2.6 (vc101) | none | same | board rendered; BOOT 7/7 ok | F275-SVCINFO NameNotFoundException — CAUGHT by AppCompatDelegate (lawful contract) | — | **REAL_APP_CONTENT** (new face) | `be640e39e82901c9` / nonbg 3.7%, 183 colors | record as baseline |
| 7 | org.secuso.privacyfriendlymemory | `82f83d9ea572240a` | 1.1.3-google (vc100) | none | same | grid rendered (COLD first launch in fresh store) | recorded-benign rows | F-NEW-369 (verified current) | **REAL_APP_CONTENT == recorded TRUE-COLD face** | `3a3ba8734b662e55` / nonbg 22.9%, 239 colors | none |
| 8 | org.secuso.privacyfriendlydame | `41727c0121fef8ab` | 1.3.4 (vc101) | none | same | board rendered; BOOT 7/7 ok | F275-SVCINFO — CAUGHT (lawful) | — | **REAL_APP_CONTENT** (new face) | `70033bc03f0392ed` / nonbg 3.0%, 220 colors | record as baseline |
| 9 | org.secuso.privacyfriendlysolitaire | `b0e2adf991f94982` | 1.1 (vc4) | x86+x86_64 (`libgdx.so` extracted; NOT dlopen'd in the bounded first-launch window — face from the View path) | same | cards rendered; BOOT 7/7 ok | none | — | **REAL_APP_CONTENT** (new face) | `aa53f6f172621982` / nonbg 3.0%, 222 colors | baseline; libgdx lazy-load path unexercised (honest note) |
| 10 | org.andstatus.game2048 | `2d6707624623fe88` | 1.16.2 (vc47) | x86+x86_64 (androidx.graphics.path helper) | same | `verdict=NO_ROOT, first_missing_stage=WINDOW_ROOT` — content view never created | `R350-FORNAME` kotlin-reflect CNFE + f141-null-recv NPE in `Lmb;.<clinit>` (caught by catch-all) | **shared candidate R350 (below)** | **DEFAULT_BACKGROUND_ONLY** | `31ddd4d5b8e6d18e` / nonbg 0.0 | candidate root recorded |

**Scoreboard: 6 REAL_APP_CONTENT (2 byte-identical to recorded faces — F-NEW-363/F-NEW-369 verified current), 2 PREREQUISITE_MISMATCH (native engines, honest refusals), 2 DEFAULT_BACKGROUND_ONLY with a named shared candidate.** All ten APKs were present locally — no absent-target rows, no substitutions needed.

## 4. Shared root, falsified hypotheses, root IDs reused

- **Shared candidate (new, recorded, NOT fixed this wave):** `R350-FORNAME` — `kotlin-reflect ReflectionFactoryImpl ClassNotFoundException` at `Lkotlin/jvm/internal/Reflection;.<clinit>` appears in BOTH blank candidates (Guandan, AndStatus2048) and correlates with the missing `WINDOW_ROOT`/`APP_DRAW_OPS` stage. Recorded as triage evidence only — per the request, no shared fix is claimed without a minimal positive+negative fixture, which is the named next lever.
- **Falsified / bounded hypotheses:** (a) "install atomicity can be fixed by record-write ordering" — false in general; POSIX cannot atomically replace a non-empty directory, the atomicity unit is the generation directory (proven); (b) ball2box/opensurge blanks are NOT renderer bugs — ARM-only native engines, prerequisite mismatch (audit's own provisional conclusion, now with exact refusal evidence); (c) the secuso F275-SVCINFO NameNotFoundException rows are NOT defects — caught by the appcompat caller (EXC-PROPAGATE handler rows).
- **Root IDs reused (no new issues):** F-NEW-376 (this wave's fix), F-NEW-256/265/277 (compose draw frontier, Guandan folded in), UPP-001 family (ARM-only blockers), F-NEW-363/F-NEW-369 (verified current by rows 2/7), MG-116 (per CONT-72, untouched).

## 5–7. Diff scope, pixel evidence, fixture + fan-out

- **Diff scope:** `miniandroid/src/main.cpp` ONLY (installer law) + new scripts/fixtures/evidence. No rendering-path changes; the 39/39 wall at the new binary proves zero behavioral drift on the run path.
- **Pixel evidence:** every row carries its screenshot sha16 + nonbg% + unique colors; the mosaic (10 tiles) is committed as `evidence/cont73/cont73_mosaic.png` (sha16 `9ed75bf809c1536d`) and uploaded byte-verified: **https://d.uguu.se/uanqCzok.png**.
- **Fixture + negative controls:** the fault-injection fixture (`scripts/cont73_fault_injection.py`, 70 assertions) IS the installer fixture — 9 boundaries × fresh/update, with a real-corruption positive control (`stage_hash`), garbage-APK parse control, NOT_INSTALLED run refusals, list-hygiene negatives, and the no-mixed-state invariant. Fan-out: the law covers every install/update path and every store consumer; the triage harness (`scripts/cont73_triage.py` + `cont73_census.py`) is re-runnable for any future batch.

## 8. Explicit pending items

- **kotlin-reflect clinit candidate (R350-FORNAME):** decode + fixture-first fix for the `Reflection;.<clinit>` bootstrap chain (blocks WINDOW_ROOT/APP_DRAW_OPS for Guandan + AndStatus2048).
- **UPP-001 binary translation:** Ball2Box (Godot) and OpenSurge (Allegro) remain ARM-only-blocked; x86 builds would be instant triage candidates.
- **F-NEW-277 continuation handoff** (CONT-72's recorded next lever for the compose draw frontier) — unchanged, evidence-driven when its own probe supports it.
- **F-NEW-376 residual honesty:** `cleanup`-fault leaves the parked OLD generation in `.trash` (new generation committed and live) — documented WARN; a reaper on the next successful install is a possible hardening, not a correctness gap.
- **Two independent renames are not a transaction:** the park→promote window is closed by ROLLBACK on every error path (fault-proven), documented as the POSIX-bounded design; a single-file authoritative pointer (symlink generation switch) is the only further-tightening design if ever needed on this filesystem layout.

No new issue opened; all results live here in #364.
