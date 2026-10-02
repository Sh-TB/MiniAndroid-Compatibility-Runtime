# CAMPAIGN_STATE — MiniAndroid-Compatibility-Runtime

HEAD at state creation: 9112e4dd (+ F-NEW-228 wave commit)
Date: 2026-10-02

## LAWS READ

CONSTITUTION_V2 (evidence/regression/lifecycle/rendering/screenshot/registry/disk laws),
MASTER ROADMAP, source-first law, issue-per-problem law, FRAME_CAPTURE_TRUTH (12-item
proof chain), FRAMEWORK_CHROME_ONLY ≠ REAL_APP_CONTENT, F084 freeze, DEX register law,
class-init honesty, REC-MISS 7-class, no-package-specific-fixes, bounded logging,
reuse-first/source-first, AOSP sources consulted this session:
android-14.0.0_r2 `core/java/android/widget/TableLayout.java` (L433-476, L527-529) +
`core/java/android/widget/LinearLayout.java` (measureVertical L808-1040).

## MASTER MERGED CHECKLIST (user directive: merge ALL leftover lists)

Sources merged: previous-session leftovers + §A–§P zones + new mega-campaign
Families A–W (audit) + Platform/README/Release audit (Phases 0–21) + "228 رو کامل بکن".

| # | Item | Source | Status |
|---|------|--------|--------|
| 1 | F-NEW-228 weight-pass completion (user: "228 رو کامل بکن") | §I/§P + Persian directive | DONE this session (IMPLEMENTED+TESTED ×3) |
| 2 | F-NEW-229 CL MATCH_PARENT spec law (opencalc button width) | new, session-registered | OBSERVED — next attack |
| 3 | F-NEW-230 golden provenance/config gap (4 stale goldens + white-frame golden) | new, session-registered | OBSERVED — re-bank with repro blocks |
| 4 | F-NEW-221 R8 merged-class ctor/dispatch deep leg | leftover | OPEN |
| 5 | F-NEW-217 kotlinx resume protocol (dame leg) | leftover | OPEN |
| 6 | F-NEW-204..207 P1 audit batch | leftover | OPEN |
| 7 | F-NEW-192 | leftover | OPEN |
| 8 | secuso grey-face provenance (§I next frontier; now white-face at HEAD — F-NEW-230) | leftover | OPEN |
| 9 | §28 final deliverable refresh | leftover | PARTIAL (issue #354 comment 5951761853 exists) |
| 10 | Families A–W semantic audit (mega-campaign §5–27) | new campaign | NOT STARTED (A–H partially covered by F-NEW-222..227 wave) |
| 11 | Real-APK matrix refresh (§29) | new campaign | PARTIAL (v10_results_latest.json banked) |
| 12 | Platform impact: installed-APK filesystem model proof (Phases 5–8) | platform audit | NOT STARTED |
| 13 | Agent APK-inspection skill feasibility (Phase 8) | platform audit | NOT STARTED |
| 14 | README/front-page audit + proposed structure (Phases 10–12, 19) | platform audit | NOT STARTED |
| 15 | Version/release audit + release candidate (Phases 13–14) | platform audit | NOT STARTED |
| 16 | Independent real-APK regression matrix ×3 (Phase 11) | both | PARTIAL (this session's battery) |
| 17 | Final registry/worklog/evidence reconciliation (Phase 12 / §38) | both | RUNNING (this file) |

## LIVE STATE

- HEAD: 9112e4dd + F-NEW-228 wave (layout_inflater.cpp)
- Registry: 525 roots (F-NEW-228 IMPLEMENTED+TESTED; F-NEW-229/230 OBSERVED)
- laws130: 51/51 PASS on patched build
- Golden gate (×3, 1080x1920): dooz d602648e8e401895 MATCH; microtimer da73010a37dd0189
  MATCH; unote 4f1a9e4e8f64fae8 MATCH; ssw/headingcalc/secuso/whatsapp = baseline-equal
  (banked goldens stale — F-NEW-230); opencalc NEW e364b001ee7abd66 ×3 deterministic.
- opencalc frame: 64.7% #303030 button field + 34.5% #6fa8dc display; rows
  126+352×5 equal (AOSP), last row ends exactly at y=1920.
- Disk free at session start: 7.5G; run/ artifacts kept ≤ ~60MB this session.

## NEXT TARGETS (priority order)

1. F-NEW-229 (opencalc full button width — CL spec routing trace).
2. F-NEW-230 (re-bank goldens with repro blocks; blank-golden gate).
3. Families I/J (View/geometry + ViewTree law tests against real APKs).
4. Platform audit Phases 5–8 (installed-APK filesystem proof).
5. README/release audit (Phases 10–21).
