# MINIANDROID CAPABILITY MATRIX

> **Canonical for per-capability status** (S95-CTRL, 2026-09-25).
> Generated-style view over committed evidence; validated by
> `tools/validate_control_system.py` against
> [TICKET_REGISTRY.json](TICKET_REGISTRY.json) and
> [evidence/canonical/registry.json](evidence/canonical/registry.json).
> Status vocabulary: `DONE / VERIFIED / IMPLEMENTED / TESTED / OBSERVED /
> PARTIAL / BLOCKED / PENDING / SUPERSEDED` (+ ticket vocabulary
> `ROOT_CAUSE_FOUND / UNTESTED / UNKNOWN / CLOSED`).
> EVIDENCE column uses E0–E6 levels (see TICKET_REGISTRY.json).

Legend for SOURCE AUTHORITY: the upstream project whose behavior defines the
capability (consult before implementing — CONSTITUTION_V2 §170).

## Core execution

| Capability | Status | Evidence | Tests | APK count | Source authority | Open tickets | Fan-out | Last verified |
|---|---|---|---|---|---|---|---|---|
| APK ZIP container parse | DONE | E4 | battery | 148 | AOSP ApkAssets | — | HIGH | d5946533 |
| AXML manifest parse | DONE | E4 | battery | 148 | AOSP | — | HIGH | d5946533 |
| ARSC resources + qualifiers | PARTIAL | E4 | battery; density laws | 148 | AOSP AssetManager2 | GFX-004 | HIGH | d5946533 |
| DEX parse + resolve | DONE | E4 | battery semantic stages | 148 | AOSP ART | — | HIGH | d5946533 |
| Interpreter (invoke/array/exception laws) | DONE | E5 | 96-stage family; f102/f103 | 148 | AOSP ART | DEX-001 | HIGH | d5946533 |
| Lifecycle (Activity/Application/Fragment) | TESTED | E5 | lifecycle_controller; F-NEW-172 | 12+ interactive | AOSP ActivityThread | — | HIGH | d5946533 |
| Reflection meta-laws | TESTED | E2 | f103_* | — | libcore | DEX-002 | MEDIUM | d5946533 |

## UI / layout / input

| Capability | Status | Evidence | Tests | APK count | Source authority | Open tickets | Fan-out | Last verified |
|---|---|---|---|---|---|---|---|---|
| View measure/layout/draw | DONE | E5 | goldens | 51 rendered titles | AOSP View root | — | HIGH | d5946533 |
| Touch dispatch (click) | TESTED | E5 | tictactoe_golden 9/9; HITPROBE | 12 interactive | AOSP | — | HIGH | d5946533 |
| Long-press | TESTED | E4 | EXT-02 12/12 | 1 | AOSP | — | LOW | d5946533 |
| LinearLayout weights | ROOT_CAUSE_FOUND | E4 | fixture pending | 1 (dodge) | AOSP LinearLayout | GFX-002 | MEDIUM | d5946533 |
| Button minimum sizes (48/88dip) | TESTED | E4 | golden re-derived | 3 (bobball/dodge/bouncy) | AOSP styles_material | — | MEDIUM | d5946533 |
| Custom-view onDraw dispatch | ROOT_CAUSE_FOUND | E4 | simplestopwatch | 1 | AOSP View.draw | GFX-001 | MEDIUM | d5946533 |
| Dialog family | TESTED | E4 | s82_dialog_gate ×2 | — | AOSP | — | MEDIUM | d5946533 |
| RecyclerView/ScrollView | PARTIAL | E4 | corpus-dependent | — | androidx | — | MEDIUM | d5946533 |

## Graphics

| Capability | Status | Evidence | Tests | APK count | Source authority | Open tickets | Fan-out | Last verified |
|---|---|---|---|---|---|---|---|---|
| Software raster (Canvas/Paint) | DONE | E5 | battery goldens | 51 | Skia | — | HIGH | d5946533 |
| Clip stack save/restore | TESTED | E2/E4 | battery law tests | — | SkCanvas | — | MEDIUM | d5946533 |
| Density selection at decode | TESTED | E4 | s95_vector | 4 | AOSP BitmapFactory; glide | — | HIGH | d5946533 |
| Vector/adaptive/state-list drawables | TESTED | E4 | s95_vector (9 checks) | 3 | AOSP VectorDrawable | — | HIGH | d5946533 |
| NinePatch | UNTESTED | E0 | fixture pending | 0 | cdroid; AOSP | GFX-004 | HIGH | — |
| GIF decode (animated) | OBSERVED | E4 | disposal fixture pending | 12 | wuffs; Pillow; go | GFX-003 | HIGH | d5946533 |
| Bitmap decode PNG/JPEG/WebP | TESTED | E4 | GATE H IoU | 51 | libpng/libjpeg/libwebp | — | HIGH | d5946533 |
| SurfaceView chain | TESTED | E4 | F-NEW-164..170 | 2 | AOSP SurfaceView | — | MEDIUM | d5946533 |
| Shaders/color filters | UNTESTED | E0 | fixture pending | 0 | Skia | GFX-006 | UNKNOWN | — |
| Theme resolution (default dark, text colors) | TESTED | E4 | GATE H; golden | 11 (S95 set) | AOSP themes/colors material | — | HIGH | d5946533 |

## Text

| Capability | Status | Evidence | Tests | APK count | Source authority | Open tickets | Fan-out | Last verified |
|---|---|---|---|---|---|---|---|---|
| Latin render (FreeType) | DONE | E5 | EXT-01 typography 9/9 | 51 | FreeType | — | HIGH | d5946533 |
| Theme text-color chain | TESTED | E4 | GATE H | 11 | AOSP | — | HIGH | d5946533 |
| Complex-script shaping | PARTIAL | E2 | shaping gate pending | 0 | harfbuzz; minikin | TEXT-001 | HIGH-potential | — |
| Bidi/RTL | UNTESTED | E0 | fixture pending | 0 | fribidi | TEXT-002 | UNKNOWN | — |
| Glyph-truth verify (OCR-grade) | OBSERVED | E4 | tamper battery red-set | 1 | tesseract | GFX-005 | LOW | d5946533 |

## Animation

| Capability | Status | Evidence | Tests | APK count | Source authority | Open tickets | Fan-out | Last verified |
|---|---|---|---|---|---|---|---|---|
| Choreographer/postDelayed clock | TESTED | E5 | S95 determinism ×3 | 2 games | AOSP Choreographer | — | HIGH | d5946533 |
| AnimationDrawable timing | UNTESTED | E0 | CDroid cts port pending | 0 | AOSP | — | MEDIUM | — |

## Media

| Capability | Status | Evidence | Tests | APK count | Source authority | Open tickets | Fan-out | Last verified |
|---|---|---|---|---|---|---|---|---|
| MediaPlayer/SoundPool/AudioTrack states | IMPLEMENTED (APK-level UNTESTED) | E2 | audio_engine units | 0 | AOSP MediaPlayer | AUDIO-001/002 | MEDIUM-potential | — |
| Real codecs (MP3/WAV/OGG/FLAC) | IMPLEMENTED (APK-level UNTESTED) | E2 | codec units | 0 | mpg123; libsndfile | AUDIO-001 | MEDIUM | — |
| Video pipeline | UNKNOWN | E0 | — | 0 | Media3; ffmpeg | VIDEO-001 | HIGH-potential | — |

## Network

| Capability | Status | Evidence | Tests | APK count | Source authority | Open tickets | Fan-out | Last verified |
|---|---|---|---|---|---|---|---|---|
| Network API shadow tracking | DONE (instrument) | E4 | android_shadows record | corpus-wide | — | — | HIGH | d5946533 |
| Real HTTP(S)/DNS/TCP/TLS | OBSERVED (gap) | E4 | curl subset pending | 0 real | curl; openssl; asio | NET-001 | **HIGHEST** | d5946533 |
| Internet diagnostic target | PENDING | E0 | — | 0 | — | NET-002 | INSTRUMENT | — |

## Storage

| Capability | Status | Evidence | Tests | APK count | Source authority | Open tickets | Fan-out | Last verified |
|---|---|---|---|---|---|---|---|---|
| File sandbox | DONE | E4 | F-104 chain | corpus | AOSP ContextImpl | — | HIGH | d5946533 |
| SharedPreferences | DONE | E4 | battery | corpus | AOSP | — | HIGH | d5946533 |
| SQLite Room law | TESTED | E2/E4 | F-026+F-027 | fixtures | sqlite; room | STORE-001 | MEDIUM | d5946533 |
| SQLite transactions/locking | UNTESTED | E0 | corpus port pending | 0 | sqlite | STORE-001 | MEDIUM | — |

## Concurrency

| Capability | Status | Evidence | Tests | APK count | Source authority | Open tickets | Fan-out | Last verified |
|---|---|---|---|---|---|---|---|---|
| Locks/atomics shadows | PARTIAL | E2 | shadow units | — | OpenJDK | CONC-002 | MEDIUM | — |
| Coroutine scheduling | UNTESTED | E0 | fixture pending | 0 | kotlinx.coroutines | CONC-001 | HIGH-potential | — |

## AndroidX / Compose / Native / Web

| Capability | Status | Evidence | Tests | APK count | Source authority | Open tickets | Fan-out | Last verified |
|---|---|---|---|---|---|---|---|---|
| AppCompat/Fragment chains | PARTIAL | E4 | F-NEW-171..174 | corpus | androidx | — | HIGH | d5946533 |
| Compose composition | BLOCKED frontier | E4 | idiom triage | 2 (dooz, Telegram) | Compose; ART | COMPOSE-001, DEX-001 | HIGH | d5946533 |
| JNI bridge / loadLibrary | PARTIAL | E2 | hello-JNI pending | 0 | AOSP core/jni | JNI-001 | MEDIUM | — |
| WebView callbacks | UNTESTED | E3 | callback-order fixture | 0 | AOSP WebView; AwContents | WEB-002 | MEDIUM | — |
| Simple browser target | PENDING | E0 | reuse matrix first | 0 | litehtml; lexbor | WEB-001 | INSTRUMENT | — |

## Verification infrastructure

| Capability | Status | Evidence | Tests | Source authority | Notes |
|---|---|---|---|---|---|
| Canonical battery gate | DONE | 99/99 ALL PASS | run_test_battery.sh | — | zero-skip; toolchain bootstrap + SHA-pinned fixtures |
| Screenshot provenance/hash chain | DONE | E5 | S92/S93 law set | — | anti-false-visual-claim rules in force |
| Semantic verdict ladder (15 states) | DONE | E4/E5 | s93 battery family | — | LOADED→…→VISUALLY_VERIFIED |
| Source-first lookup (§170) | DONE | 122 repos, 48 laws | source_lookup.py | — | automatic consultation law |
| Control-system validation | DONE | this matrix | tools/validate_control_system.py | — | README/matrix/queue/ticket consistency gate |

## Instant contributor view

- **Where help is needed most (highest fan-out open):** NET-001 (P0),
  GFX-003 GIF disposal (12 titles), GFX-001/GFX-002 (named, fixture-ready),
  TEXT-001 shaping wire-up, CONC-001 coroutine fixture.
- **Good first tasks:** GFX-004 NinePatch fixture, TEXT-002 RTL fixture,
  STORE-001 sqlite fixture tests, NET-002 diagnostic app skeleton.
- **Closed recently (do not redo):** bobball/minicraft/mini-tetris/hotdeath
  parent records; WRONG_COLOR family; Button-minHeight measure law;
  default-theme laws.
