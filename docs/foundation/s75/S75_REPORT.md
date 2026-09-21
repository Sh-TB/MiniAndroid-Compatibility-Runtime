# S75 CLOSURE WAVE REPORT — ledger truth closure + queued P0 fix + queued-lead probes

Generated: 2026-09-21 · HEAD at wave start: c67230be (== origin/main, clean tree) ·
Engine: rebuilt from HEAD, then rebuilt again with the S75 A7 fix (make -j2, clean).

## 0. Mandate

User directive (S75): "continue the work; every remaining incomplete command
must be executed; start all of them; make a big list." The big list was built
from the S74-FINAL master ledger (59 UNVERIFIED + 5 PARTIAL + 1 BLOCKED rows),
the S74 follow-up report §6 continuation list, and the queued leads in the
S73/S74 reports. Eight phases were planned and executed (worklog S75-MAIN).

## 1. What this wave did (phases)

| Phase | Scope | Outcome |
|---|---|---|
| 0 | Toolchain bootstrap (aapt2/ecj/r8/stubs) + engine rebuild at HEAD | binary 82.6 MB, clean build |
| 1 | ITEM75 closure audit: all 47 UNVERIFIED census/contract rows reconciled against (a) canonical gap-matrix FULL rows, (b) live code greps (file:line cited), (c) registry back-registration | 19 TESTED / 11 PARTIAL / 17 PENDING, 0 matrix-code conflicts; ROOT CAUSE of the former blanket UNVERIFIED found and fixed: the ledger builder's row regex truncated each matrix row at column 2, so FIXED/DONE/PARTIAL status columns were NEVER seen |
| 2 | Ledger truth refresh | CRITICAL-001/005/006 → OBSERVED (remediations executed+verified in S74-FINAL); CAM-S74OPS → OBSERVED (checkpoints posted, 14/14 links render-verified); TOOL rows RESEARCHED_ONLY → OBSERVED (verdicts exist, evidence-cited); KNOW RESEARCHED-stage rows → PARTIAL (lifecycle honestly stopped at research); REQ-HIST-062 (publish+verify stage) now captured — ledger 374 → 375 rows, UNVERIFIED 59 → 4 |
| 3 | **A7 runtime fix** (the only remaining P0 "law known, no code" item) | IMPLEMENTED + FIXTURE-PROVEN (§2) |
| 4 | R-NEW-388 re-verification (queued "measure-before-render law") | registry record CONFIRMED at HEAD via fresh probes (f14 generic laws hold exactly; TriPeaks real APK still splash-blocked); **no code change made** — implementing against a stale claim would violate constitution #6/#8 (docs/foundation/s75/R-NEW-388_HEAD_REVERIFY.md) |
| 5 | Queued-lead runtime probes: dooz F-146/F-147, gmdice roll, snake restart | all three reproduced at HEAD with NEW detail (§3) |
| 6 | Full regression | battery 26/26 rc=0 (25 + new f54); verifier 24/24 PASS; Level C snake replay **BYTE-IDENTICAL 90/90**; compatibility-graph validator PASS |
| 7 | Docs + registry + ledger + publish | A7 → FIXED-S75 in registry (397 roots unchanged); gap matrix A7 row closed; F-146/F-147 evidence appended; this report; worklog; commits+push |

## 2. A7 — manifest label/icon resolve through ARSC (the wave's code change)

Census gap A7 (S67): "Manifest label REFERENCE → literal '@0x…'; icon not
parsed at all." Law (AOSP PackageParser.parseApplication + ApplicationInfo
.loadLabel): label/icon are REFERENCE resids on the info object; the STRING
resolves through the app's Resources (ARSC), never by stringifying the
reference.

Implementation (minimal, law-cited):
- `manifest_reader.h/.cpp`: ManifestInfo gains `application_label_resid` /
  `application_icon_resid`; the `<application>` handler captures
  REFERENCE-typed label/icon (the "@0x…" literal degrade is removed —
  application_label stays empty until resolved); static
  `ManifestReader::resolve_resid_string(resid, arsc)` = one ARSC hop,
  nullopt on miss (failure REPORTED, never invented).
- `apk_parser.h/.cpp`: ApkInfo carries the label + resids (identity fields).
- `execution_engine.cpp`: resolution wired at the ResourceRuntime
  `ensure_loaded` site — the exact point the app's ARSC becomes available
  (AOSP: Resources-side, not manifest-side). Resolved label logged via
  `[A7]` lines; resolution miss logged honestly.

Proof (f54_manifestlabel fixture, deterministic 1x1 icon PNG):
- manifest `android:label="@string/app_name"` + `android:icon="@drawable/app_icon"`
- engine.log: `[A7] application label resolved through ARSC: "F54 LabelProof"
  (resid @0x7f040001)` + `application icon resid @0x7f010000 captured`
- verifier (extended with engine.log gate): f54 **6/6 asserts PASS**
  (ViewTree text "F54 LabelProof", background pixels, both [A7] log lines)
- battery 26/26 rc=0 on the A7 binary; Level C snake replay byte-identical
  90/90 → the A7 change is render-neutral by direct evidence.
- Scope honesty: bitmap/Drawable ICON DECODE is NOT claimed — the icon resid
  is captured and logged (the "parsed at all" half of the gap); decode is a
  separate capability (DRAWABLE-LAW family).

## 3. Queued-lead probes (all at HEAD c67230be, fresh runs)

### 3a. dooz F-146/F-147 (docs/evidence/s75/dooz_f146_probe/)
- Both escapes reproduced with MINIANDROID_F141_DIAG=1: `Lg8;.a pc=569`
  (recv v4:t8/o0 NULL_REF, invoked `Ljava/lang/Object;.getClass`) and
  `MainActivity.onCreate pc=228` → both "deferred frame unwind + propagate",
  uncaught — exactly the F-146/F-147 records.
- **NEW OBSERVATION** (recorded, not claimed as law): at the F-147 site the
  receiver register is **p0 (the frame's `this`) itself NULL** — consistent
  with F-147 being a secondary effect of the F-146 coroutine unwind rather
  than an independent ViewGroup bug. Upstream producer trace remains OPEN.
- Black region 23,472 px, bbox (0,0)–(488,47) — byte-consistent with the
  S73 reclassification (engine-default face, NOT dooz content). ViewTree =
  App + 2 View + Lg10 + 2 Loc1 (Compose chain, no game content).

### 3b. gmdice roll visibility (docs/evidence/s75/gmdice_roll/)
- Fresh lobby face matches the historical record: 182,628 non-white px.
- `--click-count 2`: clicks dispatched on the real listener path
  (view_id 39, `Landroid/widget/Button;` "3D20", click_kind=listener) —
  frames byte-identical (frame_000 sha == frame_002 sha,
  changed_pixels_vs_previous=0) → the roll render is still NOT visible at
  HEAD. The queued lead is reproduced with sharper detail: the listener
  fires; the ListView roll output never draws. Lead stays OPEN.

### 3c. snake restart-after-game-over (docs/evidence/s75/snake_restart_probe/)
- The S73 C4B design re-run at HEAD via scripts/s75_snake_restart_probe.py
  (the 23-tap autonomous schedule recovered from the committed run_01
  gameplay_trace.json; extended verbatim with D@90 → L@91 → U@92 →
  START@99; 108 frames).
- Reproduced exactly: self-collision game-over at **frame 94** (S73 record:
  frame 94); replay health: 91 moves, 24 turns, 1 capture.
- **Restart via START@99 after game-over: still NOT OBSERVED** — the honest
  open REMAINS OPEN at the current binary (S73 hypothesis unchanged: the
  restart path may be Dialog-based and was not exercised).

## 4. Regression (Phase 6)

| Gate | Result |
|---|---|
| Foundation battery (build+run, post-A7 binary) | 26/26 rc=0 (25 historical + f54) |
| Pixel/semantic verifier | 24/24 PASS (f54 6/6 included) |
| Level C snake fidelity replay (committed schedule vs stored evidence) | **BYTE-IDENTICAL 90/90** |
| Compatibility graph validator | PASS (apps/tools/capabilities/knowledge/registry/index/matrix all green) |

## 5. Honest gaps / not done (nothing silently dropped)

- **17 PENDING foundation gaps** remain open and are now individually
  evidenced with code-level citations (ITEM75_CLOSURE.md): B5/B6/B9/B10/B11,
  C6–C11, D1/D2/D5/D6/D7 — each row cites why it stands (feature absent /
  RGB encode confirmed / dead files present, …).
- **4 UNVERIFIED ledger rows** are UNVERIFIABLE BY CONSTRUCTION and stay
  honestly so: CAM-S74ADD, CRITICAL-002/003/004 (sources do not exist;
  inventing them is forbidden).
- Telegram BLOCKED (init NPE engine-default face) and Stopwatch
  (service-only, no Activity face) unchanged — inherent, not actionable
  this wave.
- GitHub issue comments for the S75 findings were NOT posted this session
  (GH_TOKEN unavailable per constitution §52 — token never stored); the
  posting step is one command away for a tokened session.
- R-NEW-389 (bouncy top-band 81-px divergence) and the P1 tail
  (B4 layer isolation, C5/C6 dirty model, C7–C12, D-family) unchanged.

## 6. Artifacts index

- docs/audit/ITEM75_CLOSURE.md + item75_closure.json (47-row per-item audit)
- docs/audit/MASTER_CHECKLIST.md + master_audit.json (375-row ledger, rebuilt)
- docs/foundation/s75/R-NEW-388_HEAD_REVERIFY.md
- docs/foundation/s75/S75_REPORT.md (this file)
- docs/evidence/s75/{rnew388_f14,rnew388_tripeaks,dooz_f146_probe,gmdice_roll,snake_restart_probe,snake_fidelity_probe}/
- miniandroid/tests/fixtures_foundation/f54_manifestlabel/ + upload/foundation_apks/f54_manifestlabel.apk
- scripts/audit/item75_closure.py; scripts/s75_registry_update.py;
  scripts/s75_snake_restart_probe.py; scripts/s75_fidelity_probe.py
- Code: manifest_reader.h/.cpp, apk_parser.h/.cpp, execution_engine.cpp (A7)
