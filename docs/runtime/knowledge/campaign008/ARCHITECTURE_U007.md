# ARCHITECTURE — UNIFIED_007 runtime

```
 APK (zip)
  ├─ AndroidManifest.xml ──► manifest_reader ──► activity/package metadata
  ├─ classes*.dex ─────────► dex_parser ──► dalvik_engine (bytecode interpreter)
  │                             │  execute_method_internal → opcode dispatch loop
  │                             │  heap (HeapObject store) + static_field_storage_
  │                             │  shadow bridges: Activity/View/Handler/Collection…
  ├─ resources.arsc ────────► arsc_parser ──► ResourceRuntime
  │                             │  RES_TABLE → PACKAGE → TYPE(chunks) → ENTRY → CONFIG
  │                             │  resolve(id) / find_id(pkg,type,name) / list_type
  ├─ res/layout/*.xml ─────► axml_parser ──► layout_inflater
  │                             │  AXML element tree → ViewShadow::ViewNode tree
  │                             │  android:id ↔ ARSC ids, textSize/dp→px, styles
  └─ res/drawable* ────────► PNGDecoder / WebP / JPEG / rlottie → RGBA
                                (resolved via ARSC name → APK entry → decode)

 runtime (execution_engine)
  ├─ stage_load_apk → stage_parse_dex → stage_initialize_runtime
  ├─ stage_execute_application_real_dalvik
  │    ├─ Application.onCreate (EXP-093)
  │    ├─ heap_.allocate(Activity) → <clinit> → <init>     [U007: REAL instance creation]
  │    ├─ Activity.onCreate → setContentView(resId) → REAL inflation [U007]
  │    ├─ onStart → onResume                               [U007: full lifecycle]
  │    ├─ Handler queue drain (posted Runnables execute)
  │    ├─ phase_b: enumerate clickables → dispatch clicks  (Telegram chain)
  │    │    └─ journey_capture() per stage: telegram_01..05 evidence
  │    └─ Handler drain #2
  ├─ stage_render_frame
  │    ├─ view-tree traversal (measured geometry from inflater)
  │    ├─ backgrounds: bg_color / button default / EditText stroke
  │    ├─ text: TextShaper.shape() → glyph rasters → alpha blit  [U007]
  │    │    FriBidi (bidi order) → HarfBuzz (advances/joining) → FreeType
  │    │    .notdef → NotoColorEmoji CBDT color fallback         [U007]
  │    └─ images: decoded APK drawables + Lottie frames
  ├─ stage_capture_output → screenshot.png/ppm + reports
  └─ run_touch_journey (CLI --journey)
       hit_test(x,y) → clickable ancestor → MotionEvent audit →
       dispatch_click → Handler drain → re-render → per-tap PNG [U007]

 audio subsystem [U007]
   decode_audio_file: MP3→mpg123, WAV/OGG/FLAC→libsndfile
   MediaPlayer: AOSP transition table; playhead → PLAYBACK_COMPLETED
                (fires once, on_completion hook, re-armed by seek/replay)
   SoundPool: load→play→pause/resume/stop streams
   AudioTrack: write→PLAYING, stop→drain

 job server [U007]
   POSIX-socket HTTP/1.1 · nlohmann-json store (write-temp+rename)
   QUEUED→RUNNING→(CAPTCHA_REQUIRED|COMPLETED|FAILED|CANCELLED|STALLED)
   worker runs the real CLI as child process, logs milestones live
```

## Key UNIFIED_007 bug fixes (each proven by regression)

1. **Glyph-advance collapse** — BitmapFont under-counted widths → replaced by
   HarfBuzz advances for every rendered string (gmdice/Telegram before/after).
2. **array-length after iput/iget** — register-carried length lost across
   heap round-trip → heap `__array_length__` is now authoritative.
3. **<clinit> org.telegram-only gate** — every other app's static state was
   uninitialized → gate widened to all non-framework classes.
4. **Activity <init> never executed** — instance fields (button_ids) null →
   constructor now runs at instantiation, before onCreate.
5. **onStart/onResume never dispatched** — listener/timer registration in
   those callbacks was lost → full AOSP lifecycle order implemented.
6. **PLAYBACK_COMPLETED** — state machine now transitions position-accurately
   exactly once per pass, invokes onCompletion, re-arms on seek/replay.
7. **3D counter reset** — pairwise diffs computed with fresh counters only.
8. **HTTP body split-read** — Content-Length-aware read loop (job server).
