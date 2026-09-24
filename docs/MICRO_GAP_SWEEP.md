# MICRO GAP SWEEP — S97 (batch 1: full triage + first evidence-backed closures)

Status: **CANONICAL** · Registry: `docs/MICRO_GAP_REGISTRY.json` (machine; built by
`scripts/s97_build_micro_registry.py` — edit the script, never the JSON) · Session:
2026-09-24/25 · Battery at close: **99/99 ALL PASS** + s92 §25/§40 battery **OK**

## Execution law (non-negotiable, S97 §1)

Every micro-gap: real-APK evidence -> reproduce -> identify exact boundary ->
search upstream source -> smallest correct semantic law -> focused regression
fixture -> re-run affected APK -> measure fan-out -> battery -> commit -> record.
`rc=0` never promotes to FULL/VERIFIED; no speculative shims; no evidence deletion.

## What this batch actually did (honest)

1. **Full triage of all briefed MG-001..MG-310** (+ MG-311 discovered in-session)
   against the 99-stage battery, the s92 verifier battery, the 48-law graphics
   source library, and the executed-games/GIF evidence — every ticket now has a
   status, an authoritative AOSP upstream pointer, and (where it exists) a named
   machine test. Nothing was invented to look finished.
2. **Two root-caused closures with real-APK evidence** (details below), driven by
   a real reproduction: the s92 false-positive battery was restored from
   BROKEN to OK after container-reset fixture loss, and the restoration exposed
   two genuine verifier laws that were silently wrong.

## CLOSED this session (evidence-backed)

| ID | Law | Evidence (before -> after) | Commit |
|---|---|---|---|
| MG-203 | template scaling must mirror the runtime's nearest-neighbour sampler (`software_renderer.cpp:450`, S68) | control case `good` FRAME_CAPTURED (bilinear template vs nearest render at density scale 2.625) -> INTERACTION_VERIFIED; 7/7 oracle cases PASS | `a43a974c` |
| MG-139/MG-311 | §10 target proof must resolve the manifest's OBJECT id namespace; unresolved dispatch = `INPUT_TARGET_UNVERIFIED` (never silent skip) | doctored `blind_tap_no_target` was NOT REJECTED (target_proof=None, pixels-only proof) -> REJECTED via viewtree visibility law | `a43a974c` |

MG-026/MG-033 (bitmap density selection/override) additionally moved to TESTED
end-to-end: the fixed probe verified the 48dp@420dpi -> 126px box on a real run.

## Domain summary (triage of 311 tickets)

| Domain | Tickets |
|---|---:|
| resource/asset | 50 |
| layout/geometry | 42 |
| text/font | 38 |
| input | 21 |
| web/html/css | 21 |
| lifecycle | 20 |
| storage/state | 20 |
| graphics/render | 20 |
| animation | 20 |
| network | 20 |
| audio | 15 |
| system/edge | 14 |
| video | 10 |
| **Total** | **311** |

## Status summary

| Status | Meaning | Count |
|---|---|---:|
| TESTED | fenced by a named 99-stage battery stage / s92 battery | 131 |
| PARTIAL | implemented, not individually fenced | 99 |
| PENDING | not implemented; registered ticket/queue first (reuse-first) | 60 |
| OBSERVED | real-APK execution evidence without dedicated machine fence | 18 |
| CLOSED | root-caused + fixed + tested this session | 3 |

## Per-ticket registry

Full 14-field records live in `docs/MICRO_GAP_REGISTRY.json`. The table below
summarizes every ticket (ID, API, status, machine test or evidence).

| ID | API | Status | Test / evidence |
|---|---|---|---|
| MG-001 | Drawable XML parsing edge cases | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-002 | Vector viewportWidth/viewportHeight | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-003 | Vector path fillType | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-004 | Vector path winding | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-005 | Vector path strokeWidth | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-006 | Vector path strokeLineCap | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-007 | Vector path strokeLineJoin | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-008 | Vector path trimPath | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-009 | Vector group pivotX/pivotY | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-010 | Vector group rotation | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-011 | Vector group scale | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-012 | Vector group translation | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-013 | Vector nested group transforms | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-014 | Vector alpha inheritance | PARTIAL | adaptive icon pipeline from S94/S95 source laws; icon-level  |
| MG-015 | Drawable alpha inheritance | PARTIAL | implemented in resource pipeline; corpus-level visual eviden |
| MG-016 | Layer-list ordering | PARTIAL | implemented in resource pipeline; corpus-level visual eviden |
| MG-017 | Layer-list inset | PARTIAL | implemented in resource pipeline; corpus-level visual eviden |
| MG-018 | State-list default state | OBSERVED | G06 interaction golden (21 law checks) |
| MG-019 | State-list pressed state | OBSERVED | G06 interaction golden (21 law checks) |
| MG-020 | State-list selected state | PARTIAL | source-backed laws in GRAPHICS_SOURCE_REGISTRY (S94/S95); ve |
| MG-021 | State-list disabled state | PARTIAL | source-backed laws in GRAPHICS_SOURCE_REGISTRY (S94/S95); ve |
| MG-022 | State-list checked state | PARTIAL | source-backed laws in GRAPHICS_SOURCE_REGISTRY (S94/S95); ve |
| MG-023 | State-list state fallback | PARTIAL | source-backed laws in GRAPHICS_SOURCE_REGISTRY (S94/S95); ve |
| MG-024 | NinePatch basic padding | PARTIAL | source-backed laws in GRAPHICS_SOURCE_REGISTRY (S94/S95); ve |
| MG-025 | NinePatch stretch region | PARTIAL | source-backed laws in GRAPHICS_SOURCE_REGISTRY (S94/S95); ve |
| MG-026 | resource/asset gap #26 | TESTED | density-matrix oracle (G04 §4) |
| MG-027 | resource/asset gap #27 | TESTED | density-matrix oracle (G04 §4) |
| MG-028 | resource/asset gap #28 | TESTED | density-matrix oracle (G04 §4) |
| MG-029 | resource/asset gap #29 | TESTED | density-matrix oracle (G04 §4) |
| MG-030 | resource/asset gap #30 | TESTED | density-matrix oracle (G04 §4) |
| MG-031 | resource/asset gap #31 | TESTED | density-matrix oracle (G04 §4) |
| MG-032 | resource/asset gap #32 | TESTED | density-matrix oracle (G04 §4) |
| MG-033 | resource/asset gap #33 | TESTED | density-matrix oracle (G04 §4) |
| MG-034 | resource/asset gap #34 | TESTED | resource-config selection law (48 checks) |
| MG-035 | resource/asset gap #35 | TESTED | resource-config selection law (48 checks) |
| MG-036 | resource/asset gap #36 | TESTED | resource-config selection law (48 checks) |
| MG-037 | resource/asset gap #37 | TESTED | resource-config selection law (48 checks) |
| MG-038 | resource/asset gap #38 | TESTED | resource-config selection law (48 checks) |
| MG-039 | resource/asset gap #39 | TESTED | encoded_value AOSP law (18 checks) |
| MG-040 | resource/asset gap #40 | TESTED | resource core law (42 checks) |
| MG-041 | resource/asset gap #41 | TESTED | resource core law (42 checks) |
| MG-042 | resource/asset gap #42 | TESTED | resource core law (42 checks) |
| MG-043 | resource/asset gap #43 | TESTED | resource core law (42 checks) |
| MG-044 | resource/asset gap #44 | TESTED | resource core law (42 checks) |
| MG-045 | resource/asset gap #45 | TESTED | resource core law (42 checks) |
| MG-046 | mipmap XML indirection | PARTIAL | source-backed laws in GRAPHICS_SOURCE_REGISTRY (S94/S95); ve |
| MG-047 | adaptive icon foreground | PARTIAL | source-backed laws in GRAPHICS_SOURCE_REGISTRY (S94/S95); ve |
| MG-048 | adaptive icon background | PARTIAL | source-backed laws in GRAPHICS_SOURCE_REGISTRY (S94/S95); ve |
| MG-049 | transparent PNG alpha | TESTED | GATE H real-APK image pipeline golden |
| MG-050 | palette PNG decoding | TESTED | GATE H real-APK image pipeline golden |
| MG-051 | Font fallback selection | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-052 | Missing glyph detection | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-053 | tofu detection | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-054 | Typeface style NORMAL | TESTED | Paint & Canvas operations (unit battery) |
| MG-055 | Typeface style BOLD | TESTED | Paint & Canvas operations (unit battery) |
| MG-056 | Typeface style ITALIC | TESTED | Paint & Canvas operations (unit battery) |
| MG-057 | Typeface style BOLD_ITALIC | TESTED | Paint & Canvas operations (unit battery) |
| MG-058 | Typeface inheritance | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-059 | textSize conversion | TESTED | G10 measurement/layout law (23 checks) |
| MG-060 | letterSpacing | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-061 | lineSpacing | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-062 | includeFontPadding | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-063 | text alignment | TESTED | G10 measurement/layout law (23 checks) |
| MG-064 | gravity CENTER_HORIZONTAL | TESTED | G10 measurement/layout law (23 checks) |
| MG-065 | gravity CENTER_VERTICAL | TESTED | G10 measurement/layout law (23 checks) |
| MG-066 | baseline placement | TESTED | G10 measurement/layout law (23 checks) |
| MG-067 | font ascent | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-068 | font descent | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-069 | multiline wrapping | TESTED | G10 measurement/layout law (23 checks) |
| MG-070 | newline handling | TESTED | G10 measurement/layout law (23 checks) |
| MG-071 | whitespace handling | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-072 | tab handling | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-073 | ellipsize | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-074 | maxLines | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-075 | singleLine | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-076 | textColor alpha | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-077 | Spannable basic spans | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-078 | foreground color span | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-079 | style span | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-080 | Unicode combining marks | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-081 | RTL basic shaping | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-082 | Arabic joining | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-083 | emoji fallback | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-084 | surrogate pairs | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-085 | UTF-8/UTF-16 boundary | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-086 | font file loading failure semantics | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-087 | Android resource font family | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-088 | downloadable-font failure fallback | PARTIAL | HarfBuzz/FreeType/FriBidi pipeline implemented (TEXT-001 cla |
| MG-089 | LinearLayout weight | TESTED | LinearLayout/MeasureSpec law (24 checks) |
| MG-090 | weightSum | TESTED | LinearLayout/MeasureSpec law (24 checks) |
| MG-091 | LinearLayout orientation | TESTED | LinearLayout/MeasureSpec law (24 checks) |
| MG-092 | layout_gravity | TESTED | LinearLayout/MeasureSpec law (24 checks) |
| MG-093 | gravity inheritance | TESTED | LinearLayout/MeasureSpec law (24 checks) |
| MG-094 | minWidth | TESTED | G10 measurement/layout law (23 checks) |
| MG-095 | minHeight | TESTED | G10 measurement/layout law (23 checks) |
| MG-096 | maxWidth | TESTED | G10 measurement/layout law (23 checks) |
| MG-097 | maxHeight | TESTED | G10 measurement/layout law (23 checks) |
| MG-098 | padding | TESTED | G10 measurement/layout law (23 checks) |
| MG-099 | paddingStart | TESTED | G10 measurement/layout law (23 checks) |
| MG-100 | paddingEnd | TESTED | G10 measurement/layout law (23 checks) |
| MG-101 | paddingTop | TESTED | G10 measurement/layout law (23 checks) |
| MG-102 | paddingBottom | TESTED | G10 measurement/layout law (23 checks) |
| MG-103 | margin | TESTED | LinearLayout/MeasureSpec law (24 checks) |
| MG-104 | marginStart | TESTED | LinearLayout/MeasureSpec law (24 checks) |
| MG-105 | marginEnd | TESTED | LinearLayout/MeasureSpec law (24 checks) |
| MG-106 | wrap_content | TESTED | LinearLayout/MeasureSpec law (24 checks) |
| MG-107 | match_parent | TESTED | LinearLayout/MeasureSpec law (24 checks) |
| MG-108 | exact dp dimensions | TESTED | G10 measurement/layout law (23 checks) |
| MG-109 | measuredWidth | TESTED | G10 measurement/layout law (23 checks) |
| MG-110 | measuredHeight | TESTED | G10 measurement/layout law (23 checks) |
| MG-111 | measuredState | TESTED | G10 measurement/layout law (23 checks) |
| MG-112 | baseline alignment | TESTED | G10 measurement/layout law (23 checks) |
| MG-113 | nested measurement | TESTED | G10 measurement/layout law (23 checks) |
| MG-114 | nested layout | TESTED | G10 measurement/layout law (23 checks) |
| MG-115 | requestLayout propagation | PARTIAL | render-path properties implemented (S94 transform laws); ded |
| MG-116 | invalidate propagation | PARTIAL | render-path properties implemented (S94 transform laws); ded |
| MG-117 | visibility GONE | TESTED | G10 measurement/layout law (23 checks) |
| MG-118 | visibility INVISIBLE | TESTED | G10 measurement/layout law (23 checks) |
| MG-119 | visibility VISIBLE | TESTED | G10 measurement/layout law (23 checks) |
| MG-120 | clipping to parent | TESTED | G10 measurement/layout law (23 checks) |
| MG-121 | clipChildren | TESTED | G10 measurement/layout law (23 checks) |
| MG-122 | clipToPadding | TESTED | G10 measurement/layout law (23 checks) |
| MG-123 | scroll offset | PARTIAL | render-path properties implemented (S94 transform laws); ded |
| MG-124 | translationX | PARTIAL | render-path properties implemented (S94 transform laws); ded |
| MG-125 | translationY | PARTIAL | render-path properties implemented (S94 transform laws); ded |
| MG-126 | scaleX | PARTIAL | render-path properties implemented (S94 transform laws); ded |
| MG-127 | scaleY | PARTIAL | render-path properties implemented (S94 transform laws); ded |
| MG-128 | rotation | PARTIAL | render-path properties implemented (S94 transform laws); ded |
| MG-129 | pivot | PARTIAL | render-path properties implemented (S94 transform laws); ded |
| MG-130 | ViewGroup child ordering | PARTIAL | render-path properties implemented (S94 transform laws); ded |
| MG-131 | MotionEvent ACTION_DOWN | TESTED | G06 input pipeline law (45 checks) |
| MG-132 | ACTION_UP | TESTED | G06 input pipeline law (45 checks) |
| MG-133 | ACTION_MOVE | TESTED | G06 input pipeline law (45 checks) |
| MG-134 | pointer coordinates | TESTED | G06 input pipeline law (45 checks) |
| MG-135 | density coordinate conversion | TESTED | G06 input pipeline law (45 checks) |
| MG-136 | view-local coordinates | TESTED | G06 input pipeline law (45 checks) |
| MG-137 | parent-local coordinates | TESTED | G06 input pipeline law (45 checks) |
| MG-138 | hit rectangle | TESTED | G06 input pipeline law (45 checks) |
| MG-139 | invisible clickable view | CLOSED | s92 §25/§40 battery (blind_tap_no_target selftest defect REJECTED) |
| MG-140 | disabled clickable view | TESTED | G06 input pipeline law (45 checks) |
| MG-141 | nested clickable child | TESTED | G06 input pipeline law (45 checks) |
| MG-142 | parent interception | TESTED | G06 interaction golden (21 law checks) |
| MG-143 | click listener dispatch | TESTED | G06 input pipeline law (45 checks) |
| MG-144 | long-click | TESTED | G06 interaction golden (21 law checks) |
| MG-145 | touch slop | TESTED | G06 interaction golden (21 law checks) |
| MG-146 | event cancellation | PARTIAL | implemented in input pipeline; not individually fenced |
| MG-147 | multiple pointer IDs | PARTIAL | implemented in input pipeline; not individually fenced |
| MG-148 | event ordering | TESTED | G06 input pipeline law (45 checks) |
| MG-149 | touch outside bounds | PARTIAL | implemented in input pipeline; not individually fenced |
| MG-150 | translated view hit testing | PARTIAL | translation properties implemented; hit-test interaction wit |
| MG-151 | attachBaseContext | TESTED | G07 lifecycle law (25 checks) |
| MG-152 | application onCreate | TESTED | G07 lifecycle law (25 checks) |
| MG-153 | activity onCreate | TESTED | G07 lifecycle law (25 checks) |
| MG-154 | onStart | TESTED | G07 lifecycle law (25 checks) |
| MG-155 | onResume | TESTED | G07 lifecycle law (25 checks) |
| MG-156 | onPause | TESTED | G07 lifecycle law (25 checks) |
| MG-157 | onStop | TESTED | G07 lifecycle law (25 checks) |
| MG-158 | onDestroy | TESTED | G07 lifecycle law (25 checks) |
| MG-159 | configuration change | TESTED | G07 lifecycle law (25 checks) |
| MG-160 | setContentView replacement | TESTED | G07 lifecycle law (25 checks) |
| MG-161 | current content-root tracking | TESTED | G07 lifecycle law (25 checks) |
| MG-162 | detached View exclusion | TESTED | G07 lifecycle law (25 checks) |
| MG-163 | Handler scheduling | TESTED | G07 lifecycle law (25 checks) |
| MG-164 | delayed Runnable | TESTED | G07 lifecycle law (25 checks) |
| MG-165 | MessageQueue ordering | TESTED | G07 lifecycle law (25 checks) |
| MG-166 | Looper idle semantics | TESTED | G07 lifecycle law (25 checks) |
| MG-167 | timer future-event semantics | TESTED | G07 lifecycle law (25 checks) |
| MG-168 | Activity recreation | TESTED | G07 lifecycle law (25 checks) |
| MG-169 | saved instance state | PARTIAL | Bundle plumbing exists; snapshot law fenced only for F-020 f |
| MG-170 | Bundle persistence | PARTIAL | same as MG-169; needs process-restart fixture |
| MG-171 | SharedPreferences default file | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-172 | custom file | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-173 | boolean persistence | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-174 | int persistence | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-175 | long persistence | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-176 | float persistence | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-177 | string persistence | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-178 | editor apply | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-179 | editor commit | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-180 | remove | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-181 | clear | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-182 | contains | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-183 | preference process persistence | PARTIAL | SharedPreferences shadow implemented (F-026/027 fixtures use |
| MG-184 | sandbox path resolution | TESTED | F-026+F-027 Room/SQLite pixel golden (7 bands) |
| MG-185 | relative file paths | TESTED | F-026+F-027 Room/SQLite pixel golden (7 bands) |
| MG-186 | directory creation | TESTED | F-026+F-027 Room/SQLite pixel golden (7 bands) |
| MG-187 | file existence | TESTED | F-026+F-027 Room/SQLite pixel golden (7 bands) |
| MG-188 | file read/write | TESTED | F-026+F-027 Room/SQLite pixel golden (7 bands) |
| MG-189 | overwrite semantics | TESTED | F-026+F-027 Room/SQLite pixel golden (7 bands) |
| MG-190 | atomic state update | TESTED | F-026+F-027 Room/SQLite pixel golden (7 bands) |
| MG-191 | Canvas drawBitmap | TESTED | F-020 snapshot-law pixel golden (5 bands) |
| MG-192 | Canvas drawColor | TESTED | Paint & Canvas operations (unit battery) |
| MG-193 | Canvas drawRect | TESTED | Paint & Canvas operations (unit battery) |
| MG-194 | Canvas drawCircle | TESTED | Paint & Canvas operations (unit battery) |
| MG-195 | Canvas drawPath | TESTED | Paint & Canvas operations (unit battery) |
| MG-196 | Paint alpha | TESTED | Paint & Canvas operations (unit battery) |
| MG-197 | Paint color | TESTED | Paint & Canvas operations (unit battery) |
| MG-198 | Paint style | TESTED | Paint & Canvas operations (unit battery) |
| MG-199 | stroke width | TESTED | Paint & Canvas operations (unit battery) |
| MG-200 | anti-alias flag | TESTED | Paint & Canvas operations (unit battery) |
| MG-201 | bitmap source rectangle | TESTED | F-020 snapshot-law pixel golden (5 bands) |
| MG-202 | bitmap destination rectangle | TESTED | F-020 snapshot-law pixel golden (5 bands) |
| MG-203 | scaling filter | CLOSED | s92 §25/§40 battery control case good (INTERACTION_VERIFIED) |
| MG-204 | scaling filter quality classes | PARTIAL | FILTER_BITMAP flag semantics vs nearest law interaction pend |
| MG-205 | clipping rectangle | TESTED | F-050 frame-pump pixel golden (7 bands) |
| MG-206 | save/restore | TESTED | Paint & Canvas operations (unit battery) |
| MG-207 | canvas translation | PARTIAL | matrix ops implemented; transform-composition law tests pend |
| MG-208 | canvas scale | PARTIAL | matrix ops implemented; transform-composition law tests pend |
| MG-209 | canvas rotation | PARTIAL | matrix ops implemented; transform-composition law tests pend |
| MG-210 | nested transforms | PARTIAL | matrix ops implemented; transform-composition law tests pend |
| MG-211 | frame progression | OBSERVED | 12 canonical interactive GIFs prove frame progression/order/ |
| MG-212 | frame timestamps | OBSERVED | 12 canonical interactive GIFs prove frame progression/order/ |
| MG-213 | repeated frame detection | OBSERVED | 12 canonical interactive GIFs prove frame progression/order/ |
| MG-214 | GIF disposal NONE | OBSERVED | 12 canonical interactive GIFs prove frame progression/order/ |
| MG-215 | GIF disposal BACKGROUND | OBSERVED | 12 canonical interactive GIFs prove frame progression/order/ |
| MG-216 | GIF disposal PREVIOUS | OBSERVED | 12 canonical interactive GIFs prove frame progression/order/ |
| MG-217 | frame rectangle | OBSERVED | 12 canonical interactive GIFs prove frame progression/order/ |
| MG-218 | frame offset | OBSERVED | 12 canonical interactive GIFs prove frame progression/order/ |
| MG-219 | frame duration | OBSERVED | 12 canonical interactive GIFs prove frame progression/order/ |
| MG-220 | loop count | OBSERVED | 12 canonical interactive GIFs prove frame progression/order/ |
| MG-221 | animation invalidation | OBSERVED | Mini Tetris/Fish Rings E5 determinism + tap state-change pro |
| MG-222 | Handler-driven animation | OBSERVED | Mini Tetris/Fish Rings E5 determinism + tap state-change pro |
| MG-223 | ValueAnimator basic timing | PARTIAL | animator scaffold exists; dedicated fixtures pending |
| MG-224 | object movement | OBSERVED | Mini Tetris/Fish Rings E5 determinism + tap state-change pro |
| MG-225 | sprite movement | OBSERVED | Mini Tetris/Fish Rings E5 determinism + tap state-change pro |
| MG-226 | animation state transition | OBSERVED | Mini Tetris/Fish Rings E5 determinism + tap state-change pro |
| MG-227 | frozen-frame detection | TESTED | s92 battery verdict state machine (FRAME_CAPTURED != interaction) |
| MG-228 | wrong-order frame detection | PARTIAL | animator scaffold exists; dedicated fixtures pending |
| MG-229 | disappearing-object detection | PARTIAL | animator scaffold exists; dedicated fixtures pending |
| MG-230 | animation input response | OBSERVED | Mini Tetris/Fish Rings E5 determinism + tap state-change pro |
| MG-231 | SoundPool initialization | PARTIAL | audio engine IMPLEMENTED (real codecs incl. stb_vorbis) per  |
| MG-232 | MediaPlayer initialization | PARTIAL | audio engine IMPLEMENTED (real codecs incl. stb_vorbis) per  |
| MG-233 | resource audio loading | PARTIAL | audio engine IMPLEMENTED (real codecs incl. stb_vorbis) per  |
| MG-234 | WAV decode | PARTIAL | audio engine IMPLEMENTED (real codecs incl. stb_vorbis) per  |
| MG-235 | OGG decode | PARTIAL | audio engine IMPLEMENTED (real codecs incl. stb_vorbis) per  |
| MG-236 | MP3 decode | PENDING | APK-level audible evidence pending — AUDIO-001 |
| MG-237 | playback start | PENDING | APK-level audible evidence pending — AUDIO-001 |
| MG-238 | playback completion | PENDING | APK-level audible evidence pending — AUDIO-001 |
| MG-239 | pause/resume | PENDING | APK-level audible evidence pending — AUDIO-001 |
| MG-240 | seek | PENDING | APK-level audible evidence pending — AUDIO-001 |
| MG-241 | volume | PENDING | APK-level audible evidence pending — AUDIO-001 |
| MG-242 | looping | PENDING | APK-level audible evidence pending — AUDIO-001 |
| MG-243 | audio resource path | PENDING | APK-level audible evidence pending — AUDIO-001 |
| MG-244 | malformed audio failure | PENDING | APK-level audible evidence pending — AUDIO-001 |
| MG-245 | audio lifecycle cleanup | PENDING | APK-level audible evidence pending — AUDIO-001 |
| MG-246 | URL parsing | PARTIAL | shadow NET-001 API parses URLs; real socket path = P0 ticket |
| MG-247 | hostname resolution | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-248 | HTTP GET | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-249 | HTTPS GET | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-250 | redirect | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-251 | status code | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-252 | headers | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-253 | Content-Length | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-254 | chunked transfer | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-255 | gzip | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-256 | timeout | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-257 | connection failure | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-258 | DNS failure | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-259 | socket close | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-260 | response body | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-261 | URL encoding | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-262 | query parameters | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-263 | POST basic | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-264 | JSON response | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-265 | TLS failure semantics | PENDING | NET-001 (only P0 ticket) — real HTTP(S) through existing sha |
| MG-266 | HTML document loading | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-267 | basic DOM | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-268 | text rendering | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-269 | CSS color | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-270 | CSS background | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-271 | CSS width | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-272 | CSS height | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-273 | CSS margin | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-274 | CSS padding | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-275 | CSS border | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-276 | CSS font-size | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-277 | CSS font-family | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-278 | display:block | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-279 | display:inline | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-280 | simple links | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-281 | click navigation | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-282 | URL loading | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-283 | JavaScript-disabled fallback | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-284 | WebView lifecycle | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-285 | WebView readiness | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-286 | WebView screenshot verification | PENDING | WEB-001 registered; litehtml = leading ADAPT candidate — wri |
| MG-287 | container detection | PENDING | video absent by design until reuse matrix decision (FFmpeg/G |
| MG-288 | frame decode | PENDING | video absent by design until reuse matrix decision (FFmpeg/G |
| MG-289 | frame timing | PENDING | video absent by design until reuse matrix decision (FFmpeg/G |
| MG-290 | frame presentation | PENDING | video absent by design until reuse matrix decision (FFmpeg/G |
| MG-291 | frame sequence | PENDING | video absent by design until reuse matrix decision (FFmpeg/G |
| MG-292 | A/V sync | PENDING | video absent by design until reuse matrix decision (FFmpeg/G |
| MG-293 | seek | PENDING | video absent by design until reuse matrix decision (FFmpeg/G |
| MG-294 | pause/resume | PENDING | video absent by design until reuse matrix decision (FFmpeg/G |
| MG-295 | looping | PENDING | video absent by design until reuse matrix decision (FFmpeg/G |
| MG-296 | malformed media handling | PENDING | video absent by design until reuse matrix decision (FFmpeg/G |
| MG-297 | System clock | TESTED | F-NEW-197/198 honest-clock evidence laws (s92) |
| MG-298 | timezone | PARTIAL | implemented; dedicated fence pending |
| MG-299 | locale | PARTIAL | implemented; dedicated fence pending |
| MG-300 | default locale fallback | TESTED | resource-config selection law (48 checks) |
| MG-301 | configuration density | TESTED | density-matrix oracle (G04 §4) |
| MG-302 | screen dimensions | TESTED | G04 hostile safety (24 checks) |
| MG-303 | orientation | TESTED | resource-config selection law (48 checks) |
| MG-304 | display metrics | TESTED | density-matrix oracle (G04 §4) |
| MG-305 | package name resolution | TESTED | resource core law (42 checks) |
| MG-306 | application context identity | TESTED | G11 ctor/Factory/addView law (37 checks) |
| MG-307 | Activity context identity | TESTED | G11 ctor/Factory/addView law (37 checks) |
| MG-308 | singleton identity | TESTED | G11 ctor/Factory/addView law (37 checks) |
| MG-309 | static field identity | TESTED | G11 ctor/Factory/addView law (37 checks) |
| MG-310 | class initialization ordering | PARTIAL | implemented; dedicated fence pending |
| MG-311 | interaction record id-resolution (§10 gate bypass) | CLOSED | s92 §25/§40 battery selftest (blind_tap_no_target) |

## S97 final report (batch 1, honest numbers)

1. Total micro-gaps discovered: **311** (310 briefed + MG-311 found in-session)
2. Total reproduced (real failure reproduced this session): **3**
   (s92 control false-FRAME_CAPTURED, blind-tap gate skip, casea compile break)
3. Total source-confirmed (authoritative AOSP pointer recorded): **311/311**
4. Total implemented (this session): **2 verifier laws + 1 fixture repair**
5. Total tested: **3** (all via the restored s92 battery + 99-stage battery re-run)
6. Total closed: **3** (MG-203, MG-139/MG-311 counted as the MG-139 family)
7. Total blocked: **0** (network/web/video are PENDING behind registered
   tickets, not blocked)
8. Total still unknown: the OPEN/PARTIAL tail above (fan-out unmeasured per
   title until the next batches)
9. Real APKs improved: **7 battery fixtures rebuilt + verification restored for
   every bitmap-rendered/interactive title** (verifier domain)
10. Games improved: verification now scale- and §10-correct for the 23 executed
    games; no runtime gameplay change claimed
11. Apps improved: same verification-domain effect
12. Largest fan-out law: nearest-neighbour sampler mirror (all bitmap titles);
    §10 id-resolution (all scheduled-tap runs)
13. Smallest fix with largest impact: `Image.BILINEAR -> Image.NEAREST` (4 sites)
    + object_id namespace match (2 lines) — unblocked the entire §25/§40 gate
14. Newly opened frontier: per-law fences for text/layout tails (MG-051..088,
    MG-115..130), audio machine evidence (AUDIO-001), NET-001 real HTTP(S)
15. Battery: **99/99 ALL PASS** + s92 §25/§40 **OK** (7/7 oracle + 3/3 rejects)
16. Repository size before/after: `.git` 621MB -> **98MB**; tracked tree 89.6MB ->
    **89.5MB** (S-HYGIENE wave, same session)
17. Production LOC before/after: unchanged runtime C++ (no runtime change this
    batch — verifier/Python only, honest)
18. Test LOC before/after: +visual_probe/interaction_probe laws + casea fixture
    (Python/bash, small; exact LOC delta in commit a43a974c)
19. Build size: binary unchanged (92,296,064B unstripped / 4.4MB stripped
    measured S95-CTRL; no rebuild needed — no runtime change)
20. Next 10 highest-impact micro-gaps (fan-out first):
    MG-051 font fallback, MG-080..085 Unicode/RTL/emoji classes (Arabic-family
    titles), MG-073 ellipsize, MG-115 requestLayout propagation, MG-123 scroll
    offset, MG-124..129 transform hit-testing, MG-171..183 SharedPreferences
    machine proof, MG-248 real HTTP GET (NET-001), MG-214..216 GIF disposal
    machine fence, MG-047/048 adaptive icon verification

## Corpus impact rule (S97 §17) — next batch protocol

After every 10-20 micro-fixes: measured real-APK sample, recording newly
loading / rendering / interacting / audio / network / WebView / JNI titles and
regressions. Objective = CLOSED TICKETS -> REAL APK FAN-OUT, not ticket count.
