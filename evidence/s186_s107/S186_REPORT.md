# S186 — evidence-method change + s107 root-cause + full incomplete census (2026-11-06)

User directive: stop archiving per-frame PNGs of games that never loaded (s75 6 MB /
s73 >10 MB of frames, no full load); state plainly whether dooz executed (s76 has the
GIF but the execution was never reported); tictactoedeluxe bulk; investigate why the
s107 battery is "all white/black two-tone" and apply the sqlite rule; then find EVERY
incomplete title on GitHub, audit their progress, and complete them.

Formal law reference: `docs/SQLITE_RULE.md` + issue #536.

---

## 1. Evidence-method change (measured, then enforced)

**New law (`.gitignore` S186): no per-frame PNG archives and no raw traces in git.**
Evidence = verdict JSON + final face JPG ≤100 KB (+ one GIF ≤1 MB only for titles
that fully load). One loaded title's motion GIF proves more than 150 frames of a
title that never rendered.

| dir | before | after purge | what was removed |
|---|---|---|---|
| docs/evidence/s75 | 5.9 MB / 266 files | **26 files** | 91 snake_fidelity_probe frames + 109 snake_restart_probe frames (zhangman.github.snake NEVER loaded) + 0.72 MB api_trace + 0.48 MB method_trace |
| docs/evidence/s76 | 5.9 MB / 273 files | **17 files** | 258 snake_dialog_restart frames (run_a_dialog + run_b_restart) |
| docs/evidence/s73_snake_autoplay | 3.1 MB / 151 files | **22 files** | 147 autoplay frames (the GIF stays — that title renders) |
| repo-wide | **1160 frame/trace files = 20.5 MB** | purged from git | incl. evidence/diff366 58, s114 49, s113 30, batch367 20, s151 16, hc_provenance 15 |

Tree now 158.9 MB tracked (from 163 MB post-S185).

## 2. dooz — execution status (the user asked point-blank)

**dooz EXECUTES and is one of the strongest titles in the campaign — this is
measured, not claimed:**

- S183 graphics-depth census: verdict **REAL_APP_CONTENT, tier A_RICH, 677 unique
  colors, 11.75% non-background, 3.14% gradient** (`evidence/s183_audit1112/S183_GRAPHICS_DEPTH.json`).
- Determinism: face **a0fae9072313e2d1** reproduced BYTE-EXACT twice (S179 pin +
  S183 settle-law re-run). A one-off "white 31ddd4d5" mismatch was traced to a
  simplified 40s invocation without the S156 settle law — A/B proved invocation
  error, not regression.
- The s76 `report.md` says "SUCCESS ✅ APIs Called 0, Execution Time 0ms, Errors 27"
  — that is the OLD auto-generator's output and is meaningless by today's
  verification bar. It should not be cited as dooz evidence; the S183 census JSON
  is the current verdict. Canonical face: `docs/evidence/canonical/io.github.yamin8000.dooz.jpg`.

**tictactoedeluxe (com.miniandroid.tictactoedeluxe)**: tracked footprint measured —
canonical GIF **0.05 MB**, batch367_rerun dir **0.4 MB** (46 files, now frame-free).
It was never a bulk offender; it is one of the 10 A_RICH faces. No action needed
beyond the repo-wide frame purge.

## 3. s107_games — why "all white and black two-tone" (quantified + root-caused)

Face census of all 129 s107 titles (scripts/s186_s107_census.py →
`S107_FACE_CENSUS.json`, S183 tier definitions):

| tier | count | meaning |
|---|---:|---|
| FLAT_TWO_TONE_OR_BLANK | **43** | the user's «سفید و سیاه دو رنگ» — exactly right |
| C_TEXT_ON_FLAT | 76 | text rendered on flat background, nothing else |
| B_STRUCTURED | 10 | real UI, flat fills |
| A_RICH | **0** | not one s107 title reached rich graphics |

Root-cause attribution (evidence-based, no invention):

- 10 of the 129 have per-title exception families in the API-NEED ledger
  (firestrike, raumballer, boxcars, memory, blidraughts, minesweeper, jwtc chess,
  solitaire_cg, pf-dame, pf-solitaire) — the savedstate/lifecycle/coordinatorlayout
  androidx families documented there.
- **Fresh A/B re-run on the current post-S183b engine** (scripts/s186_rerun_sample.py,
  exact s182 battery invocation law → `S186_RERUN.json`):
  - **com.dozingcatsoftware.bouncy** (s107-era: B_STRUCTURED): face **dd0c14257fa1f2af
    = BYTE-EXACT match with the S182 battery pin** on a rebuilt-from-source binary
    (104.8 MB, 0 errors — sandbox had wiped the build tree). 9,613 colors, 49.8%
    non-background. REAL render confirmed; remaining nonfatal = the APK's own bionic
    `libgdx-box2d.so` load (SharedLibraryLoadRuntimeException at Box2D.<clinit>) —
    **GATE A did not substitute the existing host libgdx-box2d64.so this run** = the
    concrete next sqlite-law fix (host lib exists since S183b).
  - **com.adilhanney.ricochlime** (s107-era: C_TEXT): still **pure white** (1 color).
    Crash chain = RuntimeException at obfuscated `v2.h.<init>` / `u2.c.onCreate`
    escaping the app boundary in MainActivity.onCreate → the **#227
    APP-BOUNDARY-UNWIND family** (Compose init) = B3 law territory, untouched by the
    current laws. NOTE: its white face sha16 collides with the S183 white-face value
    (identical pure-white images hash identically).

**Conclusion for the user:** the s107 two-tone faces were NOT one bug — they are
~6 distinct blockers (androidx lifecycle/savedstate storms, compose boundary unwind,
kotlin-reflect, native .so loads, GL, missing framework classes). The S183b
sqlite-law work already moved one of them forward (bouncy class of libGDX titles);
the rest map 1:1 onto the SQLITE_RULE playbook families below.

## 4. S185 strip casualties — found and fixed (honest note)

The S185 `--strip-blobs-bigger-than 1MB` history pass silently removed **6 LIVE
files** from the worktree (only dalvik_engine.cpp/FreeSerif.ttf/View.java had been
re-added): quickjs.c (1.7 MB), gap_map.json, 2 inventory JSONs, 2 androidx sources
jars. Detected this session when the engine failed to rebuild ("No rule to make
target build/quickjs/quickjs.o"). All 6 restored **from the old head 90df39ae**
(still locally reachable); quickjs.c restored as the EXACT old blob (a0455519 —
a patched fork, NOT vanilla upstream 21f072e8 — hash check caught it). Engine
rebuilt clean. **Lesson recorded: any future blob-size filter MUST run against an
explicit live-file allowlist first.**

## 5. Every incomplete title on GitHub — census + progress audit

(`scripts/s186_incomplete_census.py` → `S186_INCOMPLETE_CENSUS.json`; issues refetched:
535 total, 422 open.)

| bucket | count |
|---|---:|
| META_TRACKER (laws/waves/family trackers) | 222 |
| INTAKE_QUEUE (state-not-loaded placeholders, NOT_TESTED) | 157 |
| **REAL STUCK: EXECUTED_CRASHED** | **37** |
| REAL STUCK: LOADED_PARTIAL / EXECUTED_PARTIAL | 6 |
| **REAL STUCK total** | **43** |

**Progress audit: 42 of 43 REAL-STUCK issues untouched since ≤2026-09-22** (only #227,
the APP-BOUNDARY-UNWIND family tracker, moved on 2026-11-02). The APP-001..014 batch
(#125–#138) has been sitting for 6 weeks. The user's suspicion — "many half-finished
titles, nobody completing them" — is confirmed with dates.

### Completion plan (SQLITE_RULE playbook, priority by unblocks-per-work)

| # | family law | titles unblocked | concrete move |
|---|---|---|---|
| 1 | **B6 real image decode** (stb_image is ALREADY vendored in miniandroid/third_party) | ~14 B_STRUCTURED faces + 76 C_TEXT gains | wire BitmapFactory → stb_image decode path; A/B on the 14 B-tier faces |
| 2 | **box2d GATE A completion** | bouncy-class games (bouncy CONFIRMED renders; physics pending) | make loadLibrary("gdx-box2d") hit tools/native_host/libgdx-box2d64.so in GATE A |
| 3 | **B2 PortableGL** (ALREADY vendored: third_party/portablegl.h) | #225 p9, #222 stardroid, GL games | back GLSurfaceView with PortableGL framebuffer → screenshot path |
| 4 | **B3 compose APP-BOUNDARY-UNWIND law** (#227) | ricochlime + compose set | port real androidx.compose runtime pieces from the restored sources jars |
| 5 | **androidx fan-out ports** | savedstate 18 / lifecycle 14 / coordinatorlayout 13 / constraint 9 | per-family ports from upstream/*.sources.jar (jar s43/s44 restored this session) |
| 6 | **B1 native rebuild recipe per title** | #70 opensurge, #58 thextech, #72 gnubg, #76 boxcars, #224 mupdf | s183_build_gdx_host.sh pattern per upstream |
| 7 | **B7 OpenAL-soft audio bridge** | TG family depth | thin JNI bridge over real OpenAL soft |

Re-battery protocol (next session): re-fetch the 129 s107 APKs (F-Droid; the /tmp
corpus died with the sandbox), run the s182 invocation law over all of them on the
rebuilt binary, classify faces with the census script — this produces the honest
before/after matrix per family law.

## Verification

All numbers from live commands this session: PIL pixel census (129 faces), git
stat-sums, `make` exit 0 with symbol-checked binary, PIL-verified rerun faces
(bouncy dd0c1425 byte-exact vs S182 pin), issue DB refetched via
scripts/forensic_fetch.py. No verdict upgraded without evidence.
