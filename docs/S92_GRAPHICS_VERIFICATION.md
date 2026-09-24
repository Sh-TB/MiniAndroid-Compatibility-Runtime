# S92 — GRAPHICS VERIFICATION SUBSYSTEM

**Status: OPERATIONAL (pilot-complete, deployed after false-positive battery).**

S92 answers one question with evidence: *when MiniAndroid says an APK ran
with complete graphics, is that TRUE on the screen a human would see?*

The verifier is built to be able to say **NO**. Its deployment gate is that
it demonstrably rejects every deliberately-incomplete case in its battery
(S92 §25/§40). This document reflects the MEASURED state of that subsystem
after the pilot runs of 2026-09-24 — not the plan for it.

---

## 0. The three truth levels

| Level | Meaning | Gate |
|---|---|---|
| `EXECUTED` | the APK's bytecode ran without fatal exit | lifecycle evidence |
| `VISUALLY_RENDERED` | required pixels actually reached the captured frame | asset provenance × ViewTree × pixel probe triangulation |
| `FULLY_VERIFIED` | + interaction targets visible and input-proofed, expected state + visual change measured, 3-run repeatable, evidence complete | hard contract (§24) |

Laws encoded (each one earned by an observed false-positive):
- **0.1** functional success ≠ visual success — a blind tap on coordinates
  can hit an invisible object; visibility must be proven separately.
- **0.2** "screenshot exists" ≠ "graphics loaded" — a PNG carries no proof
  of resource resolution, decode, binding, draw, or presentation.
- **0.3** source-first — contracts come from the APK + its own runtime
  evidence; invented UI is forbidden; confidence degrades to
  `observed_only` when no upstream source corroborates.

---

## 1. What was reused vs built (§1 recon outcome)

Reused, unchanged: the runtime CLI (`run`, `--frames`, `--tap`, `--tap
x,y@frame`, `--dump-view-tree`), `GfxProvenance`
(`MINIANDROID_GFX_PROVENANCE=`), ClickAudit (`MINIANDROID_CLICK_AUDIT=`),
the ViewShadow/touch_dispatcher hit-test, `tools/verify/probes/`
evidence inventory.

Built in S92:

| Deliverable (§37) | Path | Purpose |
|---|---|---|
| orchestrator | `tools/verify_graphics.py` | verify-run + §40 selftest |
| visual contracts | `tools/build_visual_contract.py`, `registry/visual_contracts/` | §3 expected-visual contracts (APK zip + runtime evidence) |
| probes | `tools/verify/probes/{asset,geometry,interaction,visual}_probe.py`, `verdict.py` | §4–§14 chains |
| verdicts | `registry/graphics_verdicts/` | one strict JSON verdict per title-run (§38) |
| battery | `fixtures/s92battery/` + `ORACLE.json`, `scripts/s92_gen_fixtures.py`, `scripts/s92_run_battery.py` | §25/§40 false-positive battery |
| pilot | `scripts/s92_run_pilot.py` | §26/§27 real-corpus pilot |
| repeatability + §32 audit | `scripts/s92_repeatability_audit.py` | §28 3-run law, §32 S91 claim re-audit |
| registry reclassification | `scripts/s92_registry_reclassify.py` | §32/§33 canonical registry update with trail |

---

## 2. Runtime laws added (source-first, each A/B-proven)

### F-NEW-196 — current-window ViewTree law
AOSP view debugging (`dumpViewHierarchy`) walks the LIVE window's tree from
the attached root; it never lists views detached by a later
`setContentView`. The legacy dump iterated ALL heap objects, so after a
scene switch the dump still contained the dead scene — splash-only
captures could pass geometry checks against dead nodes. Dump is now a BFS
from `ActivityShadow.content_view_id()` with the node-source law recorded
in the dump header (`node_source: content-root-walk`).

### F-NEW-197 — idle-settle never fast-forwards the Looper clock
AOSP `MessageQueue.next()` law: an idle Looper BLOCKS in
`nativePollOnce(timeout = next-when − now)`; it can never observe its own
future. The historical `HandlerShadow::settle()` jumped the virtual clock
+1e9 ms after onCreate, so a 5000 ms splash Timer scheduled in onCreate
fired before frame 0 — the runtime's launch evidence showed the
POST-timer scene (battery case-d failed; Fish Rings' real splash could
never be observed). New law: the post-onCreate drain is DUE-ONLY
(delay-0 posts dispatch — EXP-088 A/B preserved); postDelayed /
Timer.schedule entries fire only at deterministic clock gates
(`--frames` advance, tap-state advances, poll-timeout fast-forward).
Golden impact handled honestly: the G07 lifecycle golden froze the old
settle-jump ("Ticks: 1 at frame 0") and was re-derived from the law
("Ticks: 0 at launch; chain 0→1→2→3; tick 1 at the exact 250 ms gate").

### F-NEW-198 — end-of-window evidence law
AOSP harness law (UiAutomator/screencap semantics): a run's screenshot and
view hierarchy represent the screen state WHEN OBSERVATION ENDS. Under the
honest clock, timer-driven apps legally change scene mid-window, so the
early capture (kept: it is the untouched frame-1 baseline the click-test
law depends on) described a scene that no longer existed at the end.
`screenshot.png` + `view_tree.json` are re-captured after every
interaction/frame stage (`final_pass` skips the R-NEW-340 compose pump —
record, don't advance). Measured: 30-frame splash run's screenshot now
matches `frames/frame_029.png` byte-mean exactly (253.4 vs 253.4).

### F-NEW-199 — interaction manifest records
Evidence law: a frames manifest whose only tap record is a stderr log is
not machine-verifiable. Scheduled taps (`--tap x,y@frame`) now append
runtime-authored records to `manifest["interactions"]`: boundary frame,
tap point, `target_view_id` (0 = hit-test miss), the dispatcher's DOWN
record, and the after-frame index. This is what made the §11 pre/post
proof mechanically checkable for Fish Rings (below).

---

## 3. The verification pipeline (per run)

```
APK zip ──► required_assets (res/**, SHA, dims)  ─┐
runtime view_tree ──► required_elements,          ├─► visual contract
  interaction_targets (observed_only)             ┘
run evidence: screenshot.png, frames/manifest.json, view_tree.json,
  gfx_provenance.json, click_audit.jsonl
        │
        ▼
 stages: apk_load, lifecycle, scene(§13), renderer_initialized,
   frame_output, assets_resolved/decoded/rendered(§4-§6),
   geometry(§7), visual(triangulated §14),
   input_target_visibility(§10), input, state_change, visual_change(§11),
   repeatability(§28), evidence_complete(§39)
        │
        ▼
 strict state machine (§23): UNEXECUTED → LOADED → LIFECYCLE_VERIFIED →
   RENDER_STARTED → FRAME_CAPTURED → VISUALLY_PARTIAL → VISUALLY_VERIFIED →
   INTERACTION_VERIFIED → FULLY_VERIFIED | FAILED | BLOCKED | UNKNOWN
```

- **Asset provenance chain (§4)**: `APK → RESOURCE_RESOLVED → OPENED →
  DECODED → BOUND_TO_VIEW → DRAW_CALLED → PIXELS_FOUND`, per asset, with a
  24-failure-mode taxonomy (§6) and density law check (§16): a decoded PNG
  that lands at the wrong display box is `DENSITY_MISMATCH`, not PASS.
- **Geometry (§7)**: expected vs actual x/y/w/h deltas against a documented
  tolerance `max(GEOMETRY_TOLERANCE_PX, FRAC·size)`; "present somewhere" is
  not acceptance.
- **Pixel probe (§8/§9)**: multi-technique — template NCC, alpha-aware
  compare, color histogram, edge signature — because a 64×64 icon matching
  at 3 pixels is NOT presence.
- **Input-target protection (§10)**: before any tap counts, the target must
  prove identity, visibility==VISIBLE, screen intersection, and pixel
  content in its region; otherwise `INPUT_TARGET_UNVERIFIED` and the
  callback's state change cannot promote the run.
- **Interaction proof (§11)**: BEFORE frame + target proof + DOWN record +
  AFTER frame + independent pixel delta, all cross-checked against the
  runtime's own counts.

---

## 4. Measured results

### 4.1 §25/§40 false-positive battery — 7/7 PASS + selftest 3/3

| Case | Oracle | Verdict outcome | Battery |
|---|---|---|---|
| casea_covered_button | REJECT (covered button + blind tap) | FAILED (scene/frame_output/assets_rendered/visual) | PASS |
| casec_corrupt_png | ACCEPT control | VISUALLY_VERIFIED, fails=[] | PASS |
| cased_splash | REJECT_SHORT_WINDOW (6-frame window < 5 s splash) | FAILED — scene FAIL, geometry PARTIAL | PASS |
| casee_not_clickable | REJECT_INTERACTION (visible, not clickable) | LIFECYCLE_VERIFIED (no interaction promotion) | PASS |
| casef_silent_callback | REJECT_VISUAL_CHANGE (callback without pixels) | VISUALLY_VERIFIED (never FULL) | PASS |
| caseg_density | MEASURE (xxhdpi density) | density_checks=[PASS], measured honestly | PASS |
| good | ACCEPT control | VISUALLY_VERIFIED | PASS |
| selftest: blanked_asset_region | reject doctored evidence | FRAME_CAPTURED, fails=[assets_rendered, visual] | REJECTED |
| selftest: shifted_geometry | reject doctored evidence | FRAME_CAPTURED, fails=[geometry, visual] | REJECTED |
| selftest: blind_tap_no_target | reject doctored evidence | VISUALLY_PARTIAL | REJECTED |

`run/s92battery/BATTERY_RESULT.json` — `battery_ok: true`.

### 4.2 §26/§27 pilot — 16 diverse real titles, REAL execution

| Title | family | S92 verdict | failing stages |
|---|---|---|---|
| org.bobstuff.bobball | view-xml | VISUALLY_VERIFIED | — |
| app.varlorg.unote | view-xml | VISUALLY_VERIFIED | — |
| eu.veldsoft.fish.rings (+tap 184,184@40) | view-xml | INTERACTION_VERIFIED | — |
| com.miniandroid.snakedeluxe (+tap) | canvas-custom-view | INTERACTION_VERIFIED | — |
| com.miniandroid.g2048 (+tap) | canvas-custom-view | INTERACTION_VERIFIED | — |
| com.miniandroid.tictactoedeluxe (+tap) | canvas-custom-view | INTERACTION_VERIFIED | — |
| com.miniandroid.minicraft (+tap) | canvas-custom-view | INTERACTION_VERIFIED | — |
| ca.rmen.nounours | surfaceview | VISUALLY_PARTIAL | — |
| com.dozingcatsoftware.dodge | canvas-custom-view | VISUALLY_PARTIAL | geometry PARTIAL |
| com.dozingcatsoftware.bouncy | view-xml | VISUALLY_PARTIAL | geometry PARTIAL |
| com.miniandroid.tetris (+tap) | canvas-custom-view | VISUALLY_PARTIAL | visual_change (tap dispatched, no pixel change) |
| com.trianguloy.urlchecker | view-xml | VISUALLY_PARTIAL | — |
| de.duenndns.gmdice | view-xml | VISUALLY_PARTIAL | — |
| com.smorgasbork.hotdeath | view-xml | FRAME_CAPTURED | assets_rendered, visual |
| com.emmanuelmess.tictactoe | view-xml | FAILED | scene, frame_output, visual |
| com.chessclock.android | view-xml | FAILED | scene |

Highlights:
- **Fish Rings §11 proof, independently re-run**: tap target proven visible
  → DOWN dispatched (target=31) → repaint → **4,312 pixels changed**
  (frame 39 vs 41), matching the S91 measured correction exactly. Now
  machine-verified from the manifest, not narrative.
- **Fish Rings density finding**: 8/9 assets render; `C5.png` is
  `DENSITY_MISMATCH` — decoded 600×424 @160dpi drawn into a box the
  density law predicts at [1575,1113] but found at [709,735,110,78].
  This is S92 §16 catching, with numbers, the class of density/scale bug
  the mission brief predicted as a top real-world failure cause.
- **tictactoe FAILED**: `GdxRuntimeException` unwinds
  `AndroidGraphics.<init>` ← `AndroidApplication.init`; screen = uniform
  white (std 0.0), ViewTree 1 node. The 2021-era GIF claim does not
  survive an honest re-run.
- **chessclock FAILED**: NPE escapes `ChessClock.onCreate`
  `[APP-BOUNDARY]`; ViewTree has 15 nodes but the screen is uniform dark
  (2 colors) — ViewTree PASS × Pixels FAIL ⇒ §14 VISUAL_FAIL.

### 4.3 §28 3-run repeatability — 7/7 REPEATABLE

bobball, unote, fishrings, snake-deluxe, tictactoedeluxe, g2048,
minicraft: verdict level identical across 3 same-environment runs
(`3RUN_REPEATABLE`). Zero NONDETERMINISTIC cases.

### 4.4 §32 S91 claims audit — 12/12 reclassified, zero evidence deleted

| Package | S91 claim | S92 fresh verdict | disposition |
|---|---|---|---|
| com.miniandroid.snakedeluxe | VERIFIED-INTERACTIVE | INTERACTION_VERIFIED | candidate promotion (§29 pending) |
| com.miniandroid.g2048 | VERIFIED-INTERACTIVE | INTERACTION_VERIFIED | candidate promotion |
| com.miniandroid.tictactoedeluxe | VERIFIED-INTERACTIVE | INTERACTION_VERIFIED | candidate promotion |
| com.miniandroid.minicraft | VERIFIED-INTERACTIVE | INTERACTION_VERIFIED | candidate promotion |
| org.bobstuff.bobball | VERIFIED-INTERACTIVE | VISUALLY_VERIFIED | candidate promotion |
| ca.rmen.nounours | VERIFIED-INTERACTIVE | VISUALLY_PARTIAL | **downgrade** |
| com.dozingcatsoftware.dodge | VERIFIED-INTERACTIVE | VISUALLY_PARTIAL | **downgrade** |
| com.miniandroid.tetris | VERIFIED-INTERACTIVE | VISUALLY_PARTIAL | **downgrade** |
| com.dozingcatsoftware.bouncy | VERIFIED-INTERACTIVE | VISUALLY_PARTIAL | **downgrade** |
| com.trianguloy.urlchecker | VERIFIED-INTERACTIVE | VISUALLY_PARTIAL | **downgrade** |
| com.smorgasbork.hotdeath | VERIFIED-INTERACTIVE | FRAME_CAPTURED | **downgrade** |
| com.emmanuelmess.tictactoe | VERIFIED-INTERACTIVE | FAILED | **downgrade** |

Every canonical record keeps
`s92_reclassification{previous_status, fresh_verdict, reason,
verdict_file, run_dir, session}` — the audit trail is in
`run/s92pilot/REPEATABILITY_AND_CLAIMS.json` and
`docs/evidence/canonical/registry.json` (validator PASS re-run after the
edit). Downgrades are corrections, not regressions: the GIF artifacts and
their SHAs remain canonical evidence of what those runs showed.

### 4.5 §30 regression — 96/96

`scripts/test/run_test_battery.sh`: **ALL PASS (96 stages)** with
F-NEW-196/197/198 live, including the EXT-01/EXT-02 external-APK goldens
(fixtures re-fetched SHA-exact `009b4671…`, `121d479c…` after the
container reset) and the G07 lifecycle golden re-derived from the new
clock law (17/18 checks re-passed after the law-conforming update).

---

## 5. Known limits (honest frontier)

- `FULLY_VERIFIED` was never emitted in the pilot: §24's hard contract
  (17 conditions incl. renderer-family-specific checks and 3-run
  repeatability per title) requires more than any single run provides.
  Candidate levels are recorded; §29 human review gates public promotion.
- Repeatability §28 compares verdict LEVELS across runs; byte-level
  frame-SHA equality is recorded but not required (screen content is
  deterministic, PNG encoding may vary run-to-run via provenance
  finalize ordering).
- The renderer-family classifier is observational (signals from
  provenance + ViewTree), not a guarantee: bouncy reports view-xml for
  what upstream builds as GLSurfaceView — the surface it actually renders
  through in this environment. Family-specific GL checks (§17) stay
  NOT_APPLICABLE unless GL provenance events exist, per the
  explicit-NOT_APPLICABLE law.
- Asset contracts are built from the APK's own `res/**` + runtime
  evidence (`apk_verified` / `observed_only`); no upstream source repo
  was consulted for the pilot titles this session, so no
  `source_verified` contract exists yet.
- `FRAME_CAPTURED` (hotdeath) means frames exist but required assets
  failed to render — the gap analysis (which res/** failed and why) is
  the next root-cause wave, not a solved item.

## 6. Exit-criteria self-assessment (§45, measured)

- ≥10 diverse real APKs executed with full evidence: **16** (11 external
  F-Droid + 5 in-house), real frames + real taps + real traces.
- ≥1 known-good title independently verified: bobball, unote (+5
  candidates).
- ≥1 suspicious title correctly downgraded or fixed: **6 downgrades +
  1 FAILED** (tictactoe) with named root causes.
- ≥1 deliberate false-complete case rejected: **4** (casea, cased,
  casee, casef) + 3 doctored-evidence selftest rejections.
- 3-run repeatability: **7/7**.
- Regression battery: **96/96**; S92 battery **7/7 + selftest 3/3**.
- Canonical registry updated with audit trail; validator PASS.
- Evidence all SHA-pinned; no APKs committed; verdicts are machine-
  readable JSON (§38) with only PASS/FAIL/PARTIAL/NOT_APPLICABLE/UNKNOWN
  stage values.

## 7. How to re-run everything

```
# false-positive battery (§25/§40)
python3 scripts/s92_run_battery.py

# pilot (§26/§27) — real APKs, real taps
python3 scripts/s92_fetch_pilot_apks.py     # SHA-pinned re-fetch
python3 scripts/s92_run_pilot.py            # all 16; or pass case names

# 3-run repeatability + S91 claim audit (§28/§32)
python3 scripts/s92_repeatability_audit.py
python3 scripts/s92_registry_reclassify.py  # applies §32 trail to registry

# verifier standalone
python3 tools/verify_graphics.py verify-run --run-dir R --apk A \
    --contract registry/visual_contracts/P.json --package P --out V.json
python3 tools/verify_graphics.py selftest --run-dir GOOD --apk A
```
