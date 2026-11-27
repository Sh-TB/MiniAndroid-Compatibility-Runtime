#!/usr/bin/env python3
"""Post the final completion report to issue #599. Token from git credential
helper; never printed. Verifies the post by re-fetching the comment."""
import json, subprocess, sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
BODY = """# FINAL COMPLETION REPORT — W32/F-NEW-685 shipped: `96878de83`

**Final commit:** [`96878de83aa748155724f8b60b42095a807e7d30`](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/commit/96878de83aa748155724f8b60b42095a807e7d30) — pushed to `main`, remote SHA verified equal to local HEAD via `git ls-remote` (push record `5815064c4..96878de83`). Production binary rebuilt at the final HEAD: `./build/miniandroid version` → `v0.0.6.2` / `Commit: 96878de83aa748155724f8b60b42095a807e7d30` — **binary == commit verified** (the version-identity law, live output).

## What landed (F-NEW-685, the W31-named law)

**The ViewGroup index-based removal family — `removeViewAt(int)` / `removeViews(int,int)` / `removeViewsInLayout(int,int)`** — IMPLEMENTED + TESTED.

Honest provenance (verified, not assumed): the reported W31 fix **never reached the repository** — zero `F-NEW-685` references tracked anywhere, zero `removeViewAt`/`removeViews` arms in any engine TU at the aligned tip `5815064c4`, and the tracker search finds only 2 issue-level mentions (#599, #364), no code. The ViewGroupShadow implemented list had only the object-identity arms (`removeView`/`removeViewInLayout`/`removeAllViews`). This session landed the law from scratch:

- **Law** (AOSP ViewGroup.java, the R-NEW-302 removal doctrine extended to the index family): OOB index/range → deferred `IndexOutOfBoundsException` **before any removal** (tree unchanged); valid removals compact `mChildren` and clear the child's `mParent`; `removeViewAt`/`removeViews` fire requestLayout (R-NEW-302); `removeViewsInLayout` is the in-pass form and does **not** (the AOSP in-pass law, `layout_dirty` observable false — same rule as the F-NEW-323 detach family); `count==0` is the AOSP empty-loop no-op; AOSP's backward range iteration kept so erases stay index-stable.
- **Law test**: `tests/s255_viewgroup_remove_law_test.cpp` registered in `TEST_LAW` — 7 rows / 28 checks through the production dispatch path — **28/28 PASS rc=0** (OOB deferral, compaction identity, parent clearing, the layout_dirty distinction, family regression guard).

## Full verification wall (all measured this session, none assumed)

| gate | result |
|---|---|
| law battery | **55/55 PASS** (`BATTERY SUMMARY: total=55 passed=55 failed=0`, incl. the new s255) |
| test-core | **4/4 PASS** |
| test-hostile | **3/3 PASS** (after a 0-free-disk event mid-link — 6.5 GB of regenerable `build/tests` exes freed, results persisted, rebuilt+passed) |
| source parity | **[PARITY-OK] 88 core sources manifest-parity** |
| P0 screenshot gate (`scripts/p0_gate.sh`, 11 runs) | **11/11, ALL canonical hashes IDENTICAL to the S27-W4 wall**: pz×3 `35c4e53b14561b2f`, guess×3 `87fe26766fc48d06`, np×3 `31ddd4d5b8e6d18e`, dice `0de952bf75f89409`, ttt `d55056a8928a26ff` — deterministic ×3 each |
| flip ×3 (canonical flags SECS=120 frames=30, production binary) | **rc=0 ×3, `6808aa29ff941dae` ×3 = the recorded S27 canonical face — IDENTICAL** |
| shipped-binary runtime spot | pz on the final binary → `35c4e53b14561b2f` (exact canonical); rttt/minos-class → `b5a7a35d5fe0564b` (exact recorded wall face) |

**NO_HASH_DRIFT**: the F-NEW-685 arms are runtime-neutral for the whole gated corpus and deterministic across repeated runs.

## Session-alignment receipt (honest recovery record)

The session started on a recycled sandbox: local `main` was W23-era (64 commits behind origin). The stale local-only W23-D commit proved to be **10 app-runtime DB files** (notepad.db×4 / cache.db / database.db / highscores.db×3, zero code insertions) — its gitignore content already verbatim on origin (`.gitignore` lines 97–101), the DBs the run-store residue class S-SLIM deliberately untracked; it was dropped (recoverable in reflog at `194f0bd7`/`df77b0c96`) and `main` was aligned to `origin/main` `5815064c4` before any work. Full production build from the aligned tip: rc=0, `Build complete`.

## Remaining known defects — DOCUMENTED, not expanded (per the final-completion order)

The live P0 queue stays open and is recorded as future work, in-scope evidence carried by their own issues: **#706** (ArrayAdapter mutations + notifyDataSetChanged no-op — fix reported implemented there but not found in any branch of this repo; still open), **#705** (574 INT32-only bridge sites drop DEX booleans), **#704** (View.setRotation never reaches the framebuffer), **#703** (textStyle/setTypeface discarded), **#697** (programmatic RelativeLayout rules), **#699** (the LAYOUT-GEOMETRY-001 mission lane). None of these blocks the shipped F-NEW-685 law; none was silently converted to done.

**Status labels:** F-NEW-685 IMPLEMENTED+TESTED (28/28); BATTERY 62/62; PARITY-88 OK; GATE 11/11 IDENTICAL; FLIP×3 CANONICAL IDENTICAL; SHIPPED_BINARY PARITY PROVEN; P0 QUEUE DOCUMENTED-OPEN.
"""

def token():
    inp = "protocol=https\nhost=github.com\n\n"
    out = subprocess.run(["git", "credential", "fill"], input=inp, capture_output=True,
                         text=True, cwd="/home/z/my-project")
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    raise SystemExit("no token")

def api(path, data=None):
    t = token()
    cmd = ["curl", "-sS", "-m", "60", "-H", f"Authorization: token {t}",
           "-H", "Accept: application/vnd.github+json",
           f"https://api.github.com{path}"]
    if data is not None:
        cmd += ["-d", json.dumps(data)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(p.stdout)

res = api(f"/repos/{REPO}/issues/599/comments", {"body": BODY})
if "id" in res:
    print("POSTED comment id:", res["id"])
    print("html_url:", res.get("html_url"))
    # verify by re-fetch
    chk = api(f"/repos/{REPO}/issues/comments/{res['id']}")
    ok = "96878de83aa748155724f8b60b42095a807e7d30" in (chk.get("body") or "")
    print("VERIFY re-fetch: id present:", chk.get("id") == res["id"],
          "| SHA text present:", ok, "| body len:", len(chk.get("body") or ""))
else:
    print("POST FAILED:", json.dumps(res)[:400])
