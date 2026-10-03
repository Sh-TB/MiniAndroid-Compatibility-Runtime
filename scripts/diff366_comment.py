#!/usr/bin/env python3
"""DIFFERENTIAL-366 — post the completion ledger to GitHub Issue #366.
Same-Issue completion protocol (.agent/CODER_REQUEST_PROTOCOL.md §2):
every requirement row as STATUS — RESULT — EVIDENCE."""
import json, subprocess, sys

BODY = r"""
# DIFFERENTIAL EXECUTION — COMPLETION LEDGER (same-Issue protocol)

CURRENT HEAD `204aed6bdec7325daf8f7360517d4ef74333d086` (results commit `3a67c801`).
RUNTIME BUILD: `miniandroid/build/miniandroid` sha256-16 `4b2db3540575b1c4`, REAL_DALVIK.
Canonical report: **`docs/DIFFERENTIAL_WORKING_VS_WHITE.md`** (+ 3 JSONLs). Pipeline scripts
persisted: `scripts/diff366_{fetch,screen,final,report}.py`. Evidence: `evidence/diff366/`.

## Answer to the Issue's question

**All five white apps are Case A** — installed correctly, executed from the installed
`base.apk` identity (source APK physically hidden, `pkgaudit` live re-hash match), manifest+DEX
parsed, launcher Activity resolved, lifecycle reached `RESUMED` — and fail **later and
differently**: 5 distinct first divergences (VIEWTREE/ATTACH, COMPOSE, NATIVE/JNI, FRAGMENT,
ANDROIDX-LIFECYCLE). Installation / package identity / resource / asset / file / stream / FD /
decode loading is **innocent in all nine apps**.

## 1–2. Exact apps (4 Working + 5 White)

- **STATUS: TESTED (working set re-proven at HEAD)** — OpenCalc `com.darkempire78.opencalculator`,
  uNote `app.varlorg.unote`, MicroTimer `dubrowgn.microtimer`, **Bouncy `com.dozingcatsoftware.bouncy`**.
  — EVIDENCE: F-NEW-233 verdict `REAL_APP_CONTENT`, 7–36 app draw ops, 302k–1,029k app-owned pixels;
  screenshot SHAs `e364b001ee7abd66` / `4f1a9e4e8f64fae8` / `da73010a37dd0189` / `b6dde6074bf47264`.
- **STATUS: TESTED (white set, S115 population)** — Fossify Clock `org.fossify.clock` (#202),
  BlockBlast `com.sidhant.blockblast` (#86), Asteroids Revenge `com.game.asteroids_revenge` (#109),
  Space Vertex `fr.arnaudguyon.spacevertex` (#96), Memory `com.sanskritbasics.memory` (#67).
  — EVIDENCE: 12 S115 candidates screened on CURRENT HEAD (12/12 still BLANK,
  `evidence/diff366/screen/`); corrupt-fetch/PARTIAL/splash-only classes excluded; 5 selected
  spanning distinct root families; all 1-unique-color frames (`31ddd4d5b8e6d18e` ×3,
  `9d8c64b1f9f908b4`, `0666775d14475766`).
- **REGRESSION RECORDED (request §2)** — Chess `jwtc.android.chess`: golden `b5a7a35d5fe0564b`
  byte-stable ×3 at HEAD but frame 100% white (0 app draw ops, `DEFAULT_BACKGROUND_ONLY`;
  `start;.onCreate` NPE pc=9; RecyclerView children=0). Historical "working" was a
  **determinism gate, not a pixel gate**. dooz control same class (COMPOSE, 2 nodes, 0 draw ops).
  Chess replaced by Bouncy. **STATUS: REGRESSED-CLASSIFICATION — EVIDENCE: run logs +
  frame census in `evidence/diff366/final/chess_jwtc.android.chess/`.**

## 3–7. Install identity, launch, lifecycle (all 9 + 2 controls)

- **STATUS: VERIFIED** — source SHA == installed `base.apk` SHA (11/11 `sha_match=True`),
  `pkgaudit` live re-hash equal, source APK moved to `run/diff366/hidden_sources/` before every
  run, runs launched in `INSTALLED-PACKAGE MODE` (codePath = store base.apk).
  — EVIDENCE: `docs/DIFFERENTIAL_WORKING_VS_WHITE.jsonl` fields `source_sha`/`installed_sha`;
  per-app `pkgaudit` JSON in run logs; §3 table of the report.
- **STATUS: TESTED** — lifecycle: all five whites reach `RESUMED` (3–6 transitions);
  working apps same. — EVIDENCE: `lifecycle_trace.json` + `trace.jsonl`
  (`RUN_START→APK_LOADED→MANIFEST_PARSED→DEX_PARSED→CLASSES_LOADED→ACTIVITY_RESOLVED→
  APPLICATION_CREATE→…→LIFECYCLE_STATE RESUMED`) per `evidence/diff366/final/<app>/run1/`.

## 10. First Divergence per app (the differential core)

- **STATUS: VERIFIED (each with log-line proof)**
  - `org.fossify.clock` — **VIEWTREE/ATTACH**: authoritative WINDOW_ROOT absent at frame time
    (`[F-NEW-233] NO_ROOT / WINDOW_ROOT`, `[F-NEW-232] deferred-UI pending queue_size=1`), after
    EventBusException unwinding `App.onCreate` + `Ln/h;.inflate` NPE (null XmlPullParser);
    setContentView HAD linked root=2192 under decor=1133.
  - `com.sidhant.blockblast` — **COMPOSE**: `[UC009-ATTACH-DIAG] ComposeView NOT in class index`,
    tree frozen at 1 node, attach ok=false.
  - `com.game.asteroids_revenge` — **NATIVE/JNI** (trigger: null-semantics §18):
    `[REC-MISS] Arrays;.toString` returned null → kotlin Intrinsics NPE →
    `GodotActivity;.onCreate` unwound at pc=0x3a → APP BOUNDARY; GodotView never created
    (tree=2 decor nodes). Engine streamed `_cl_` assets before dying (loading worked).
  - `fr.arnaudguyon.spacevertex` — **FRAGMENT**: `Class.forName("kotlin.internal…implementations")
    .newInstance()` null → NPE; re-dispatch dies on androidx Fragment ISE
    ("HomeFragment must be a public static class…", `Landroidx/fragment/app/a;.b pc=232`);
    decor attaches ok (12 nodes) but content never inflates (1 draw op = window background).
  - `com.sanskritbasics.memory` — **ANDROIDX LIFECYCLE**: null-receiver `.getClass` NPE in
    androidx WindowInsets compat (`s0$k.<clinit>`→`s0.v/.u`) during
    `ActionBarOverlayLayout.<init>`, killing `MainActivity.onCreate` ×3; app content
    (WebView 1080×1920) IS inflated and walked but emits 0 draw ops.
  — EVIDENCE: `docs/DIFFERENTIAL_FIRST_DIVERGENCES.jsonl`; report §5.

## 11. Working-vs-White matrix

- **STATUS: VERIFIED** — 27-stage matrix × 11 apps: `run/diff366/stage_matrices.json`;
  compact matrix in report §4. Boundary = `app_draw_ops>0 ∧ app-owned pixels>0`.
  Whites split NO_ROOT (fossifyclock/blockblast/asteroids: measure never ran) vs
  DEFAULT_BACKGROUND_ONLY (spacevertex/memory: walk ran, only window background painted).

## 12–13. Why each Working works / why each White fails

- **STATUS: VERIFIED (causal, per-app, runtime-evidence-backed)** — report §6 (working:
  OpenCalc = absorbed provider exception + full inflate/measure/draw chain + atomic prefs;
  uNote = plain-widget path with ZERO uncaught exceptions + SQLite; MicroTimer = programmatic
  UI + file family + WAL; Bouncy = custom Views + 12 asset OPENs incl. openFd REAL fds
  fd=4..7 + honest missing-asset FNFE caught by the app + libGDX native-load failure
  absorbed inside app frames) and §7 (whites, 22-question verdicts).

## 14. Generic root causes

- **STATUS: OBSERVED** — five distinct generic gaps, zero package-specific anything:
  (1) java.util/java.lang shadow null-contracts (`Arrays.toString`, `Class.forName` chain)
  converted to lethal NPEs by kotlin Intrinsics; (2) androidx WindowInsets compat static-init
  null-receiver; (3) androidx Fragment instance-state recreation law; (4) ComposeView
  materialization (#344 family); (5) Godot native surface (S-2). Loading layer proven innocent.

## 15. Fixes

- **STATUS: PENDING (by design)** — this request is diagnose-first (§13). No patch applied;
  no regression run needed; goldens byte-identical ×3 at HEAD as side-proof. Five ranked
  generic fix candidates with AOSP laws + fan-out predictions: report §12.

## 16–17. Screenshot + trace SHAs

- **STATUS: VERIFIED** — per-app screenshot SHA-256, pixel metrics (unique colors / non-bg /
  entropy) and trace_summary SHAs in `docs/DIFFERENTIAL_WORKING_VS_WHITE.jsonl`
  (`screenshot_sha`, `trace_sha`); working frames proven app-owned via F-NEW-233 census
  (`app_owned_pixels` 302,400–1,029,909); white capture path proven healthy (same capture
  pipeline produced the 4 working frames; `window_background_px=2,073,600` full-HD background).

## 18. 3-run results

- **STATUS: VERIFIED** — 4 working + 5 white, runs 1–3 byte-identical each (report §10);
  first divergence identical across runs; **no NONDETERMINISTIC divergence**.

## 19. Regression results

- **STATUS: OBSERVED** — no fix applied; the 5 canonical goldens re-verified byte-identical
  ×3 during pipeline bring-up. Chess reclassification recorded as the campaign's regression
  finding (above).

## 20. Artifacts

- **STATUS: IMPLEMENTED** — `docs/DIFFERENTIAL_WORKING_VS_WHITE.{md,jsonl}`,
  `docs/DIFFERENTIAL_FIRST_DIVERGENCES.jsonl`, `docs/DIFFERENTIAL_EVIDENCE_INDEX.jsonl`,
  `run/diff366/stage_matrices.json`, `evidence/diff366/{screen,final}/` (11 apps × up to 3
  runs × 10 artifacts, distilled 296→34 MB), `run/diff366/hidden_sources/`, 4 persisted
  scripts. Commit `3a67c801`.

## 21. Blockers

- **STATUS: OBSERVED** — none blocking this report. Remaining open population: the other 7
  screened-but-unselected S115 candidates (evidence retained).

## 22. Continuation items

- **STATUS: PENDING** — generic-fix campaign in leverage order (report §12): shadow
  null-contracts → WindowInsets compat → Fragment recreation → ComposeView → Godot surface;
  chess start.onCreate NPE + RecyclerView-binding frontier; E5 (post-fix 9-app rerun +
  regression + provenance) after the first fix lands.

**Evidence level: E4** (runtime + state change + consumer + output per app; 3-run
reproducibility ×9; trace-SHA provenance). E5 reserved for the post-fix rerun cycle.
"""

def gh_token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None

def main():
    token = gh_token()
    if not token:
        print("NO TOKEN"); sys.exit(1)
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/366/comments",
        "-H", f"Authorization: token {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"body": BODY}),
    ], capture_output=True, text=True)
    try:
        resp = r.json()
        print("posted:", resp.get("id"), resp.get("html_url"))
    except Exception:
        print("FAIL", r.stdout[:300])

if __name__ == "__main__":
    main()
