# STATUS — UNIFIED_007 (auto-generated from evidence)

Grades are extracted from artifacts on disk by `scripts/u007_status_gen.py`.
Vocabulary: PROVEN / PARTIAL / FAILED / NOT_PROVEN / BLOCKED.

## golden_real_app

- **launch_screenshot_nonwhite**: 182628
- **taps_executed**: 1
- **real_apk**: gmdice.apk (de.duenndns.gmdice, F-Droid)
- **inflated_views**: 10
- **onclick_dex_chain**: [PROVEN] PROVEN (GameMasterDice.onClick → DiceSet.getDiceSet → StandardDiceSet → selectDice → DiceCache.populate)
- **visible_state_change**: [FAILED] FAILED — remaining blocker: instance-array value integrity across iget-object/array-length after iput (button_ids loop skipped); attempted fixes: clinit gate widened, Activity <init> execution, array-length heap lookup

## dooz

- **apk**: dooz.apk (io.github.yamin8000.dooz)
- **launch**: [PROVEN] PROVEN (exit 0, DEX parsed)
- **ui**: [BLOCKED] BLOCKED — Jetpack Compose app (no XML layouts; composition/@Composable/Material drawing not implemented)
- **evidence**: run/u007_dooz_evidence/dooz_01_launch.png (blank = honest stop point)
- **dooz_02_real_ui**: [PROVEN] NOT_PROVEN
- **dooz_03_after_touch**: [PROVEN] NOT_PROVEN
- **dooz_04_next_state**: [PROVEN] NOT_PROVEN
- **dooz_05_result**: [PROVEN] NOT_PROVEN

## telegram

- **apk**: Telegram 10.14.5 arm64 (real, never-seen-version compat)
- **telegram_01_launch**: [PROVEN] PROVEN
- **telegram_02_after_start_click**: [PROVEN] PROVEN
- **telegram_03_login_screen**: [PROVEN] PROVEN
- **telegram_04_after_next**: [PROVEN] PROVEN
- **telegram_05_final_state**: [PROVEN] PROVEN
- **chain**: [PROVEN] PROVEN — click StartMessaging → LoginActivity; phone input → onNextPressed → TL_auth_sendCode → controlled mock response → RequestDelegate → fillNextCodeParams → setPage(VIEW_CODE_SMS=2) → SmsView rendered; mock ONLY at network boundary
- **string_values**: [PARTIAL] PARTIAL — ARSC names resolve, Telegram config-value fallback shows resource names (SentSmsCodeTitle) instead of strings

## arsc

- **parser**: src/resources/arsc_parser.cpp (RES_TABLE/PACKAGE/TYPE/SPEC + string pools UTF-8/16 + sparse entries)
- **gmdice**: [PROVEN] PROVEN — packages=1 global_strings=67 type_chunks=14 entry_configs=99 named_ids=73 types=8
- **resolution_chain**: [PROVEN] PROVEN — resource id → name → findViewById(0x7f080005)→view_id matched → setOnClickListener → dispatch
- **config_matching**: [PARTIAL] PARTIAL — single best-config resolution; full config-bucket matching (locale/density) not implemented
- **telegram_values**: [PARTIAL] PARTIAL — see telegram.string_values

## layout

- **inflater**: [PROVEN] PROVEN — AXML→ViewShadow tree (LinearLayout/TextView/Button/ListView/EditText), real geometry (measured_*)
- **evidence**: gmdice: 10 views inflated from res/layout/act_gmdice.xml; simplestopwatch: 11 views; headingcalc: 3 views
- **measure_layout_draw**: [PROVEN] PROVEN — use_measured path consumes inflater geometry in stage_render_frame
- **hierarchy_dump**: [PROVEN] PROVEN — [EXP092-RENDER] per-node class/text/children/depth/pos/size

## fonts

- **pipeline**: FriBidi → HarfBuzz → FreeType → alpha-blit (src/fonts/text_shaper.cpp, used by runtime render loop)
- **fa_string**: [PROVEN] PROVEN — سلام دنیا shaped (joined forms, RTL right-aligned)
- **mixed_bidi**: [PROVEN] PROVEN — Hello دنیا correct visual order
- **fa_digits**: [PROVEN] PROVEN — ۱۲۳۴۵ rendered
- **emoji_fallback**: [PROVEN] PROVEN — .notdef → NotoColorEmoji CBDT color bitmaps (Android font-chain semantics)
- **in_runtime**: [PROVEN] PROVEN — all corpus UI text + Telegram screens render via the same TextShaper
- **proof_sha256**: fad39aa17eb7ad55

## images

- **png**: [PROVEN] PROVEN — PNGDecoder (RGB/RGBA/gray/palette/PLTE+tRNS/interlace) used for APK drawables
- **webp_jpeg**: [PROVEN] PROVEN — libwebp + libjpeg decoders (EXP-097)
- **lottie**: [PROVEN] PROVEN — rlottie wired (EXP-097/098, Telegram SMS icon)
- **from_apk_assets**: [PROVEN] PROVEN — ImageView drawable path resolved via ARSC → APK entry → decode → draw_image

## backgrounds

- **view_bg_color**: [PROVEN] PROVEN — setBackgroundColor(int) captured + drawn (CM-020)
- **button_default**: [PROVEN] PROVEN — AOSP-style default button background
- **edittext_stroke**: [PROVEN] PROVEN — bordered box (CM-019)
- **fullscreen_webview_case**: [PROVEN] PROVEN — bgclock renders 2,073,600-px frame (100% coverage)

## touch

- **hit_testing**: [PROVEN] PROVEN — deepest-visible-view hit test at (x,y) → clickable ancestor walk
- **motionevent_record**: [PROVEN] PROVEN — per-tap x/y/target_id/class/listener to stderr + touch_audit_v1 JSON
- **dispatch**: [PROVEN] PROVEN — dispatch_click → real DEX onClick (gmdice: 8+ frame deep chain)
- **duplicate_view_guard**: [PROVEN] PROVEN — tap skipped when hit-test target ≠ enumerated candidate (old bug class guarded)
- **per_tap_screenshot**: [PROVEN] PROVEN — journey step_NN_after_tap.png + journey.json manifest

## audio

- **decoders**: [PROVEN] PROVEN — libmpg123 (MP3) + libsndfile (WAV/OGG/FLAC), real ffmpeg-generated fixtures
- **mediaplayer_state_machine**: [PROVEN] PROVEN — AOSP transition table; PLAYBACK_COMPLETED fixed: fired once per pass, onCompletion invoked, re-armed by seekTo(0)/replay
- **soundpool**: [PROVEN] PROVEN — load/play/pause/resume/stop stream states
- **audiotrack**: [PROVEN] PROVEN — write→PLAYING, stop drains buffer
- **test_result**: 47 PASS / 0 FAIL (exit 0)

## 3d

- **software_renderer**: [PROVEN] PROVEN — mesh→rotate→perspective→cull→depthsort→shade→raster
- **yaw_frames**: [PROVEN] PROVEN — 6 frames at 0/60/120/180/240/300°, all pairwise diffs meaningful (fresh counters per pair — counter-reset bug fixed)
- **metrics**: /home/z/my-project/repo/miniandroid/run/u007_3d/frame_metrics.json
- **real_3d_apk**: [BLOCKED] BLOCKED — no GLES bridge in runtime (exact blocker: android.opengl.GLESv*.so JNI surface absent); software 3D proof stands alone

## browser

- **persistent_job_model**: [PROVEN] PROVEN — QUEUED/RUNNING/WAITING/CAPTCHA_REQUIRED/FAILED/COMPLETED/CANCELLED/STALLED, server-side JSON store
- **refresh_safe**: [PROVEN] PROVEN — SIGKILL restart restores verbatim state
- **captcha_policy**: [PROVEN] PROVEN — pauses at CAPTCHA_REQUIRED, never bypasses
- **stalled_detection**: [PROVEN] PROVEN — no-progress timeout marks STALLED
- **test**: 10 PASS / 0 FAIL (scripts/u007_job_server_test.py)

## api

- **endpoints**: [PROVEN] PROVEN — POST /api/jobs (201), GET /api/jobs/{id}, /status, /logs, /artifacts, POST /{id}/cancel, GET /api/jobs, /health
- **live_logs**: [PROVEN] PROVEN — APK running → inflate → Status → artifact milestones stream
- **implementation**: tools/u007_job_server.cpp (POSIX sockets, zero deps)

## crash

- **package**: [PROVEN] PROVEN — crash.log per run (session/errors/recent), record_error in trace_engine, exception path returns structured result
- **known_limitation**: [PARTIAL] PC/opcode/thread-level core-dump style report is PARTIAL (no signal handler dumps)

## hang

- **detection**: [PROVEN] PROVEN — STALLED status in job server (no-progress timeout)
- **runtime_watchdog**: [PARTIAL] PARTIAL — instruction-budget aborts exist; wall-clock watchdog not separate

## corpus

