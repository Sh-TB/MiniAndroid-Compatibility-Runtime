# Comment texts for GitHub evidence posting — EXACT texts from the COMMENT_BLOCKED report.
# Data-only module. No token handling here.

ISSUE_TITLE = "MiniAndroid campaign evidence — verified achievements (REUSE-FIRST campaign, 2026-09-05)"

ISSUE_BODY = """Dedicated evidence anchor for the REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE / REUSE-FIRST MAXIMUM PROGRESS campaign (session 2026-09-05).

This issue collects the campaign's verified achievements as focused comments, each with commit SHA, quantitative result, affected files/modules, and evidence path from the repository's committed records:

- `CURRENT_HEAD_BASELINE.md`
- `docs/CAMPAIGN_FINAL_REPORT_REUSE_FIRST_PROGRESS.md`
- `docs/research/GITHUB_EVIDENCE_INDEX.md`
- `docs/research/GITHUB_RESEARCH_INDEX.md`
- `docs/research/REUSE_REDUCTION_REPORT.md`
- `docs/research/WINEDROID_DEEP_STUDY.md`
- `docs/evidence/GOLDEN_HELLOWORLD.md`, `docs/evidence/tictactoe_golden/`, `docs/evidence/PUSH_BLOCKED.json`

Status vocabulary: implemented / tested / observed / researched / pending. Nothing below is claimed beyond what the committed evidence records support.

Comment index:
1. Campaign baseline & repository state
2. Clean rebuild + 11/11 battery gate
3. Real resource-backed Hello World (aapt2, binary resources.arsc, binary AXML, @string resolution, strings absent from DEX, deterministic replay)
4. Tic-Tac-Toe real UI (9/9 clicks, X-WINS, deterministic replay)
5. WineDroid reuse + MUTF-8 findings (FIND-REUSE-001)
6. UTF-16LE→UTF-8 consolidation + manifest surrogate bug fixed (FIND-REUSE-002)
7. SLEB128 consolidation + UB hardening (FIND-REUSE-003)
8. ResStringPool consolidation (FIND-REUSE-004)
9. −294 production LOC / code-minimization scoreboard (§28)
10. Corpus pixel-identical validation (gmdice, simplestopwatch, microtimer)
11. Research index / coverage + evidence summary
"""

COMMENTS = [
("1. Campaign baseline & repository state", """**Campaign baseline — REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE / REUSE-FIRST MAXIMUM PROGRESS (2026-09-05)** [implemented, observed]

- Campaign HEAD: `4d822256`; current local `main` HEAD: `1b86da8a` (includes PUSH_BLOCKED re-verification docs commit).
- Origin: https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime — remote `main` = `ad95d92876a355a719d2a8959053f8a47c2b1e79`, UNRELATED to the local rebuilt history (remote = original 394-commit line; local = workspace superproject line with the project under `MiniAndroid-Compatibility-Runtime/`).
- 33 local commits unpushed (PUSH_BLOCKED — no credentials in the build environment; exact error recorded in `docs/evidence/PUSH_BLOCKED.json`). The remote 394-commit line is preserved via local branch `archive/origin-main-ad95d928` for a future push.
- Remote-only file `miniandroid/run/exp096_evidence/metrics.json` was recovered from remote objects into the local tree (`3c39f1fa`) — nothing was lost in the history rebuild.
- Every number in this comment series was re-executed THIS campaign from `make clean`; nothing is inherited from prior reports (§1 law of `CURRENT_HEAD_BASELINE.md`).

Evidence: `CURRENT_HEAD_BASELINE.md`, `docs/evidence/PUSH_BLOCKED.json`, `docs/CAMPAIGN_FINAL_REPORT_REUSE_FIRST_PROGRESS.md`. Pending: push + comment posting until credentials exist."""),

("2. Clean rebuild + 11/11 battery gate", """**Clean rebuild + one-command battery gate: 11/11 stages ALL PASS** [implemented, tested]

Command (verbatim, from workspace root): `make clean && bash scripts/run_test_battery.sh` → **BATTERY GATE: ALL PASS (11 stages)** — build · 3 links · 3 semantic groups (long/cmp/conv 14 · switch parse-neg 25 · pass3 bridge 57 = **96/96**) · MUTF-8 battery **10/10** · both golden gates (helloworld 26/26, tictactoe 8/8). Runtime binary 60,183,232 bytes, built zero-skip from clean.

The gate is self-verifying (PASS 0 / FAIL 0 is impossible) and replaces ~8 ad-hoc re-validation commands with one zero-skip law (`scripts/run_test_battery.sh`, commit `9e7c0e9b`).

Evidence: `CURRENT_HEAD_BASELINE.md` (§Record + verbatim commands), `docs/CAMPAIGN_FINAL_REPORT_REUSE_FIRST_PROGRESS.md` §Verified execution."""),

("3. Real resource-backed Hello World (aapt2 / ARSC / AXML / §36.E)", """**Real resource-backed Hello World — §36.E discriminator permanent (commit `a3c3aded`)** [implemented, tested, observed]

The fixture is now built by the REAL Android toolchain — **aapt2 8.13.2-14304508** (Google Maven, Apache-2.0) + ECJ 3.x (MIT) + D8/r8 8.3.37 (Apache-2.0) + android-34 stubs — replacing any hand-written binary AXML/ARSC generator with **ZERO new binary-format-writer LOC in MiniAndroid** (researched→reused, per `docs/research/GITHUB_RESEARCH_INDEX.md` aapt2 row).

Verified from the APK bytes themselves (`validate_helloworld_golden.sh`, **26/26 checks, zero skipped**, up from 18):
- APK SHA256 (deterministic build): `3cf76fb7b2cb2c02d608966fe97c4644e4abab90b9f3c550e937ffdb827b4d15`
- DEX SHA256: `039e18ed62cfd76ee0dda83beb1c0ff16e53b9df207fb85b00f3b26655d3a24f`
- Screenshot 1080×1920 SHA256: `a61f5b224ace9fd7e9ff4e3c50dec44cf5ffa84843cce161e8fc4950cc24ad66`
- All three display strings ("Hello, MiniAndroid!", "real APK - real DEX - real render", "OK") present in **real binary `resources.arsc`** and **ABSENT from `classes.dex`** (string-pool byte search — permanent §36.E gate; `docs/evidence/helloworld_golden/reschain_report.txt`)
- Layout + manifest are aapt2-compiled **binary AXML** (RES_XML type `0x0003`); runtime log shows `[U007-RES] ResourceRuntime loaded … named_ids=8 types=3`, `[ARSC-VALUES] strings=3` — real **@string/@id resource resolution** through `setContentView(R.layout.activity_main)` → AXML inflation → ARSC-first lookup → `findViewById` → `setText(int)`
- Deterministic replay: run A vs run B **byte-identical** (`cmp`); fixture APK builds byte-deterministic (aapt2/repackager pin 1980-01-01 zip epochs)

Full §27 real chain exercised end-to-end with no bypasses: APK load → manifest parse → Activity.onCreate → DEX execution → inflation → resource resolution → measure/layout → FreeType/HarfBuzz/FriBidi shaping → Canvas draw → PNG. Evidence: `docs/evidence/GOLDEN_HELLOWORLD.md` (§28 record + §36.E)."""),

("4. Tic-Tac-Toe real UI", """**Tic-Tac-Toe golden — real UI, real DEX interaction, deterministic replay (commit `de5f370e`, revalidated ×2 this campaign)** [implemented, tested, observed]

`tictactoe_golden` **8/8 checks PASS** at the current HEAD:
- **9/9 clicks** delivered through real DEX click listeners (real state machine, not scripted drawing)
- State transitions verified on-screen: "X to move" → "O to move" → **"X WINS"**
- Board state: 4 X + 3 O marks, marks in cells 2..8 only, each glyph >100 px ink (visible-pixels law, §16)
- **10-frame sequence byte-identical across two independent runs** (deterministic rendering law)

Satisfies §29/§16 on this HEAD: one real APK LOAD → EXECUTE → UI → RENDER → SCREENSHOT with explicit interaction testing. Evidence: `docs/evidence/tictactoe_golden/`, `docs/CAMPAIGN_FINAL_REPORT_REUSE_FIRST_PROGRESS.md` §Verified execution row "Real APK receives real input"."""),

("5. WineDroid reuse + MUTF-8 findings (FIND-REUSE-001)", """**WineDroid reuse: MUTF-8/ULEB128 corruption FIXED, ONE canonical primitive (FIND-REUSE-001, commit `2c8bf2da`; discriminators commit `9e7c0e9b`)** [researched → implemented, tested]

Studied https://github.com/rickbergs/winedroid @ a784c0b (Apache-2.0, behavioral reference only) — 20-mechanism catalog in `docs/research/WINEDROID_DEEP_STUDY.md`. (sohzm/winedroid is a DIFFERENT project — rejected, never substituted.)

Real bug fixed: `string_data_item.utf16_size` (code units) was treated as a **byte count**, truncating every non-ASCII DEX string; encoded NUL left undecoded; ULEB128 had no 5-byte cap (**UB on hostile input**). Replaced 3 duplicated readers with ONE primitive `src/dex/mutf8.{h,cpp}` adapted from WineDroid mechanisms WINEDROID-004/005 — ≈ −68 LOC and a single repair point.

Two more WineDroid mechanisms pinned as permanent executable discriminators inside `semantic_pass3_bridge_test.cpp` (57-case group, reusing its helpers — ≈ −120 LOC of harness duplication prevented): **007 absent-arg determinism**, **011 switch payload-is-data**. Battery: MUTF-8 windows 7/7 at landing, now 10/10; full gate 96 semantic + goldens green; golden screenshots byte-identical.

Evidence: `docs/research/WINEDROID_DEEP_STUDY.md`, `tests/mutf8_string_pool_test.cpp`, `docs/research/REUSE_REDUCTION_REPORT.md`."""),

("6. UTF-16LE→UTF-8 consolidation + manifest surrogate bug (FIND-REUSE-002)", """**FIND-REUSE-002: UTF-16LE→UTF-8 encoders 5 copies → 1; real manifest surrogate bug discovered and FIXED (commit `e69bc496`)** [implemented, tested]

Five duplicated encoders consolidated into ONE `mutf8::utf16le_to_utf8` + exported `mutf8::append_utf8`, per the AOSP String.cpp law (surrogate pairs combine, unpaired → U+FFFD):
- `arsc_parser.cpp` (26 L) · `axml_parser.cpp` (22 L) · `manifest_reader.cpp` (21 L) · `dalvik_engine.cpp` `utf8_of` (12 L) · `mutf8.cpp` private `append_utf8`

**Bug found and fixed as a side effect:** `manifest_reader.cpp` had no surrogate handling → non-BMP manifest strings were double-encoded. ≈ −94 LOC net; 1 repair point instead of 5.

The battery caught **2 defects in the new canonical code itself** pre-landing (signed-shift UB in SLEB; UTF-16 unpaired-with-invalid-tail) — the no-dead-tests law paying for itself. Tests: `tests/mutf8_string_pool_test.cpp` T8–T12, 10/10 windows; corpus pixels byte-identical after rewiring. Evidence: `docs/research/REUSE_REDUCTION_REPORT.md` session addendum, `docs/research/GITHUB_RESEARCH_INDEX.md` AOSP String.cpp row."""),

("7. SLEB128 consolidation + UB hardening (FIND-REUSE-003)", """**FIND-REUSE-003: SLEB128 readers 2 copies → 1; undefined behavior eliminated (commit `e69bc496`)** [implemented, tested]

Two 28-line inline SLEB128 reader pairs in `dalvik_engine.cpp` (exception dispatch + `find_catch_handler_for_pc`) — both UB-prone on the 5-byte hostile encoding — consolidated into ONE hardened `mutf8::read_sleb128` (5th-byte law enforced). Legacy truncation return-0 semantics preserved **verbatim** so behavior is bit-compatible (FIND-EXC-TRUNC follow-up queued honestly). ≈ −56 LOC; 10 SLEB128 test vectors in the MUTF-8 battery (10/10 PASS).

Status: implemented + tested; FIND-EXC-TRUNC (semantic audit of legacy truncation edge cases) remains queued, not claimed. Evidence: `docs/research/REUSE_REDUCTION_REPORT.md`, `docs/CAMPAIGN_FINAL_REPORT_REUSE_FIRST_PROGRESS.md` §New findings."""),

("8. ResStringPool consolidation (FIND-REUSE-004)", """**FIND-REUSE-004: ONE canonical ResStringPool decoder — ARSC + AXML + manifest 3 copies → 1 (commit `4d822256`)** [implemented, tested]

`resources/string_pool.{h,cpp}` now implements the AOSP androidfw law once: offsets-table indexing (kills the sequential-walk misalignment class), decodeLength 1-or-2-byte form, malformed input → empty string. Replaced:
- `ArscParser::parse_string_pool` (58 L) · `AxmlParser::parse_string_pool` (52 L) · `ManifestReader::parse_string_pool` (65 L, the BLOCKER-006 sequential-walk instance); orphaned `ManifestReader::decode_string_length` removed

≈ −158 LOC net; **BLOCKER-006 bug class structurally dead** (there is no second walker left to misalign). Verified: `make clean` + full battery 11/11 after landing; corpus pixel-identity ×3 consecutive. Evidence: `docs/research/REUSE_REDUCTION_REPORT.md`, `docs/research/GITHUB_RESEARCH_INDEX.md` androidfw ResStringPool row."""),

("9. −294 production LOC / code-minimization scoreboard (§28)", """**§28 code-minimization scoreboard: functionality UP, duplicated LOC DOWN — −294 production LOC (git-verified per commit)** [implemented, tested]

| Metric | Before | After |
|---|---|---|
| UTF-16LE→UTF-8 encoder copies | 5 (1 buggy) | **1** (`mutf8::utf16le_to_utf8`) |
| SLEB128 reader copies | 2 (both UB-prone) | **1** (`mutf8::read_sleb128`, hardened) |
| ResStringPool chunk-parser copies | 3 (BLOCKER-006 class) | **1** (`resources/string_pool.cpp`) |
| MUTF-8/ULEB128 copies | 3 | **1** |
| Production LOC | — | **−294** (e69bc496 −136; 4d822256 −158, excluding aapt2-integration script lines) |
| Binary-format writer LOC written from scratch | — | **0** (aapt2 reused) |
| Regression test volume | mutf8 7 windows; golden 18 checks | **mutf8 10 windows; golden 26 checks** |
| Bug fixes as consolidation side effects | — | manifest non-BMP double-encoding FIXED; BLOCKER-006 class dead; SLEB UB dead |

Honest maintenance leads recorded but NOT implemented: BitmapFont vs TextShaper dual text path (standing R4), `dalvik_engine.cpp` 813 KB hotspot, dead experiment chain `dex_interpreter{,_v2,exp018}` (~160 KB, zero live refs). Evidence: `docs/research/REUSE_REDUCTION_REPORT.md` §28, `docs/CAMPAIGN_FINAL_REPORT_REUSE_FIRST_PROGRESS.md` §Code reduction."""),

("10. Corpus pixel-identical validation", """**Real-corpus validation: pixel byte-identity across every consolidation (3 consecutive rounds)** [tested, observed]

Corpus APKs (registry `miniandroid/tests/corpus/apks.json`, SHA256 F-Droid hash match, zero-APK-in-repo policy — cache outside repo):
- **simplestopwatch** — exit 0 + screenshot [tested]
- **gmdice** — exit 0 + screenshot; visually verified: history list + hints + button bar [tested, observed]
- **microtimer** — exit 0 + screenshot [tested]

Acceptance law: after EACH consolidation (FIND-REUSE-002/003, FIND-REUSE-004) the full corpus was re-run from `make clean` and **rendered pixels were byte-identical** — refactorings changed no observable output. Determinism extends to fixture builds themselves (aapt2/repackager pin 1980-01-01 zip epochs → APK builds byte-deterministic).

Known gap recorded honestly, not a regression: FIND-GRAVITY-VERTICAL — LinearLayout container gravity top-aligns on the vertical axis vs AOSP (visible in old AND new goldens; queued P0-9). Evidence: `CURRENT_HEAD_BASELINE.md` §Corpus, `docs/research/REUSE_REDUCTION_REPORT.md` §Verification discipline, `docs/CAMPAIGN_FINAL_REPORT_REUSE_FIRST_PROGRESS.md`."""),

("11. Research index / coverage + evidence summary", """**§26 research index & §20 evidence summary — 36 repositories, append-only institutional memory (commit `4468e3b9`; index rows `31789f6e`)** [researched, implemented (partial), pending (push)]

`docs/research/GITHUB_RESEARCH_INDEX.md` — every repository exactly once, status vocabulary enforced:
- **REUSED-IMPLEMENTED:** WineDroid MUTF-8/ULEB128 laws (FIND-REUSE-001), aapt2 8.13.2 (canonical resource compiler — zero hand-written format-writer LOC), D8 8.3.37, ECJ 3.x, androidfw ResStringPool law (FIND-REUSE-004), AOSP String.cpp utf16_to_utf8 law (FIND-REUSE-002), FreeType/HarfBuzz/FriBidi (UNIFIED_007)
- **REUSED-DISCRIMINATOR:** WineDroid 007/011 as executable tests; AOSP Framework gravity/sp laws pinned by goldens (EXT-AOSP-001/002)
- **REFERENCE:** AOSP ART (semantics oracle, laws extracted never copied), frameworks/base, AOSP Native, Cuttlefish, AVF, crosvm, Waydroid, VineOS, DroidVM, JADX, Apktool, droidsaw, libarsc, ARSCLib, bundletool, dexterpreter, Robolectric/Paparazzi/Roborazzi/Shot/Dropshots, Android-Dex, Skydnir
- **REJECTED (with reasons kept):** RRO overlay model, AOT C-emission pipeline, VM/container architectures (MiniAndroid must NOT become a VM), sohzm/winedroid (different project)
- **Honest unavailable records:** sim-use REPOSITORY_UNAVAILABLE (two consecutive sessions); AndroidRecomp / ReSource / Reveree URL_UNVERIFIED — never guessed

§38 double success criteria: (A) knowledge transfer completed (WineDroid 004/005 implemented, 007/011 pinned); (B) real APK LOAD→EXECUTE→UI→RENDER→SCREENSHOT with explicit interaction — **both goldens revalidated deterministic at current HEAD**. Prior-campaign goldens: helloworld `738ac50` (screenshot SHA `93b42621…`, 18/18 at the time), tictactoe `de5f370e`.

Full evidence map: `docs/research/GITHUB_EVIDENCE_INDEX.md` §Achievement→commit→evidence table (11 rows). Remaining blockers, stated honestly: PUSH_BLOCKED (33 commits awaiting credentials), COMMENT_BLOCKED (this text), FIND-GRAVITY-VERTICAL open, BitmapFont retirement open, res/font corpus coverage open, Telegram-class apps BLOCKED (prior record stands).

Evidence of record until credentials exist — commits: `a3c3aded`, `e69bc496`, `4d822256`, `4468e3b9`, `31789f6e`, `1b86da8a`, `2c8bf2da`, `9e7c0e9b`, `3c39f1fa` (+ prior `738ac50`, `de5f370e`)."""),
]
