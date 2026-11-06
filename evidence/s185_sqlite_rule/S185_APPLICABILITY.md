# S185 — SQLITE-RULE APPLICABILITY SURVEY (2026-11-06)

Two user directives served by this report: (1) repo/tmp bulk audit + cleanup, (2)
"list the programs/games that did not load and tell me which sqlite-law moves can
complete them, then make this a formal rule so Coders understand it."

Formal rule: `docs/SQLITE_RULE.md` (VEND, DON'T REWRITE · LOAD-FIRST · TRACER-THEN-PRUNE ·
NOTHING BULKY IN GIT).

---

## Part 1 — bulk audit (measured, then fixed this session)

### GitHub repo (user reported ">250 MB" — confirmed ~400 MB total footprint)

| layer | before S185 | after S185 | action |
|---|---:|---:|---|
| tracked tree | 260 MB (13,868 files) | **163 MB** (13,077 files) | untracked 8 `run_*` dirs (114 MB); deleted 32.5 MB `tk_new.err`, 7.8 MB console `.bak`, 3.5 MB source-copy-in-evidence |
| evidence images | PNG mosaics 2.7 MB + 19 MB S183b frames-in-git | 4 JPGs ≤100 KB + verdict JSONs | S38 JPG law re-applied |
| foundation JSONs | 22 MB raw | **1.7 MB** `.gz` | dex_census ×5, knowledge_graph, api_matrix, all_issue_comments; readers switched to `gzip.open` |
| `.git` pack | 139 MB (293 versions of dalvik_engine.cpp = 259 MB raw; run dirs in history) | **81.7 MB** (1455 commits kept) | 3-pass `git filter-repo` (--strip-blobs >1 MB, path-purge run_*/history) + force push (bundle backup verified first) |
| remaining >1.5 MB blobs in pack | dozens | **2** — both LIVE files | `dalvik_engine.cpp` 4.1 MB (engine source), `FreeSerif.ttf` 3.5 MB (font fixture) |

### /tmp (user: "why is /tmp so bulky")

860 MB → **59 MB**. Removed: `/tmp/my-project` 392 MB (a full stale copy of this repo),
`/tmp/libgdx_src` 286 MB (libGDX source tree — now re-fetchable: fetch-if-missing block
added to `scripts/s183_build_gdx_host.sh`), `/tmp/abtest` 124 MB (S183 A/B snapshots,
verdicts committed), `/tmp/tectonic` 55 MB (unrelated PDF tool).

### local disk

~3 GB of post-verdict run dirs deleted (`run_s180_battery` 402 MB, `run_s182_minimal2`
238 MB, `run_s166_trains` 135 MB, `run_s181_minimal` 118 MB, `run_s170_w9` 62 MB,
`run_s183_gdx` 56 MB, …). Verdicts/faces were already in `evidence/` or are now
(S183b faces archived as JPG ≤100 KB: emmanuelttt 89 KB, bouncy 19 KB, stacktower3d 9 KB).
`upload/` (3.7 GB, user's APK corpus) untouched.

**S185 LAW (Clause 4):** run dirs, logs, traces, built .so, vend source trees —
never in git; scripts + pinned upstream URLs instead. `run_s170_w9`'s 32.5 MB `.err` is
the cautionary tale: it sat in git for 100+ commits.

---

## Part 2 — the stuck census (what is actually not loaded)

Issue DB refetched this session (`scripts/forensic_fetch.py`): **535 issues, 422 open.**

| bucket | count | meaning |
|---|---:|---|
| `state-not-loaded` | 157 | mostly S82-era intake placeholders (`NOT_TESTED`, "record exists so future work has a home") — a QUEUE, not blockers |
| `fail-oncreate` (open) | 37 | executed, crashed in onCreate — the real stuck set |
| PARTIAL/FAIL in API-NEED ledger | 61 | per-title exception families extracted (S102 census; still the best structured map) |
| REAL-labeled faces (S183 depth census) | 29 | 10 A_RICH · **14 B_STRUCTURED (real UI, ~0 decoded image assets → B6)** · 5 C_TEXT |

### Native/GL cluster — the exact "libgdx64.so case" the user called out

Titles where an app-shipped native library or GL is the wall (each is a sqlite-law case,
not an engine-coding case):

| title | issue | native signature | sqlite-law move |
|---|---|---|---|
| com.emmanuelmess.tictactoe | #11 | libgdx.so bionic DT_NEEDED | **DONE S183b** — host-native rebuild from gdx-parent-1.9.10 |
| stack.tower3d, com.dozingcatsoftware.bouncy | — | libgdx.so / libgdx-box2d.so | **DONE S183b** (same build) |
| se.tube42.p9.android | #225 | `AndroidGraphics.createGLSurfaceView` = same libGDX path | B2: PortableGL-backed GLSurfaceView + existing libgdx64.so |
| org.opensurge2d.surgeengine | #70 | native SDL engine (`.so`) | B1: vend SDL2 host build (same recipe as libGDX) |
| ru.wohlsoft.thextech.fdroid | #58 | native SDL2 engine | B1: vend SDL2 host build |
| com.clavierhaus.gnubg | #72 | native backgammon engine | B1: vend upstream gnubg source |
| com.rocket9labs.boxcars | #76 | native board engine | B1: vend upstream source |
| com.artifex.mupdf.viewer.app | #224 | libmupdf native PDF | B1: vend mupdf host build |
| com.google.android.stardroid | #222 | GL rendering | B2: PortableGL |
| org.telegram.messenger(.web) | #8 family | libtmessages.49.so needs `libjnigraphics/libGLESv2/libEGL/libandroid/libOpenSLES` | B2+B7: PortableGL + OpenAL-soft bridge (DT_NEEDED census: `evidence/s183_audit1112/S183_B1_SCOPE.json`) |

### UI-framework cluster — the highest fan-out (API-NEED ledger, 61 titles)

| family | titles | sqlite-law move (all 100% open-source) |
|---|---:|---|
| savedstate-registry | 18 | port real androidx.savedstate from vendored sources jars (`upstream/*.sources.jar`) |
| lifecycle-adapter | 14 | port real androidx.lifecycle (same) |
| coordinatorlayout | 13 | port real androidx.coordinatorlayout Behavior chain |
| constraint-layout | 9 | port real ConstraintLayout solver (Apache-2.0) |
| compose-runtime | 6 | androidx.compose source port (B3) — largest, schedule after the above |
| appcompat-decor-toolbar / theme-gate | 10 | port real appcompat toolbar/theme plumbing |
| kotlin-reflect / Insets / misc (B5) | — | vend kotlin-reflect; AOSP Insets port (Coder-3 #532 already moving) |

### Priority order (maximum full-loads per unit of work — Clause 2)

1. **B6 real image decode (stb_image / libpng+jpeg-turbo)** — flips ~14 B_STRUCTURED
   REAL faces from flat to decoded-asset content in one engine move.
2. **B2 PortableGL under GLSurfaceView** — unblocks the whole libGDX/GL game cluster
   (#225, #222, and hardens #11-family beyond TEXT).
3. **B1 generalized host-native rebuild recipe** — one documented recipe
   (`s183_build_gdx_host.sh` pattern + DT_NEEDED census via `s183_dt_needed.py`) applied
   per title: #70, #58, #72, #76, #224.
4. **androidx ports by fan-out** — savedstate (18) → lifecycle (14) → coordinatorlayout (13)
   → constraint (9): 54 titles of headroom, sources already vendored.
5. **B7 OpenAL-soft audio bridge** — needed for TG family depth (B2 first).

## Verification status of this report

All numbers measured from live data this session (`git count-objects`, `stat` sums over
`git ls-files`, `scripts/forensic_fetch.py` refetch, PIL-verified JPGs). No claim
upgraded without evidence. Part 2 family counts come from the S102 API-NEED ledger and
remain tied to their per-title log lines there.
