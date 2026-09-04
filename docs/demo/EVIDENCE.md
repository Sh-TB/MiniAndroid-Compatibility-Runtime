# Real APK Execution Proof — Evidence Report (2026-09-04)

This report is the machine-checkable evidence that MiniAndroid executes a real
APK end-to-end: install, lifecycle, DEX bytecode, View hierarchy, rendering,
user interaction, state change, re-render, screenshot capture.

All artifacts referenced here were produced by the MiniAndroid runtime's own
software renderer. No host-side rendering, no pre-rendered animation, no
hardcoded output.

## The proof application

`demo/` — a minimal MIT-licensed Android app (package `com.miniandroid.demo`)
built with the official Android toolchain equivalents (ECJ + AOSP D8, see
`demo/README.md`). Its state model:

* `count` — increments on every click (DEX field + `iput`/`iget`)
* `pos=(x,y)` — the box position cycles a 5x4 grid (`rem-int`, arithmetic)
* `color` — cycles RED -> GREEN -> BLUE -> YELLOW (static `int[]` built by
  `<clinit>` via `new-array` + `fill-array-data`, read via `sget`/`aget`)
* a `Button` whose `View.OnClickListener` is the Activity itself
* a `TextView` whose text is rebuilt from state every click (`StringBuilder`)

## Evidence chain (all machine-checked by `demo/validate_demo_proof.sh`)

| Step | Evidence |
|---|---|
| APK launches | `run` exit code 0, status SUCCESS |
| Activity lifecycle executes | `MainActivity.onCreate` bytecode (122 instructions) fully interpreted |
| Java/DEX code executes | arrays, statics, StringBuilder, arithmetic, virtual dispatch, interfaces |
| UI actually rendered | 1080x1920 PNG from the software renderer with real view tree |
| State changes at runtime | `count`/`pos`/`color` mutate per click |
| Visible object moves | box bbox moves across the stage (FrameLayout margins) |
| Color changes | box pixels cycle 0xFFE53935/0xFF43A047/0xFF1E88E5/0xFFFDD835 |
| Counter advances | status text `count=1..9` rendered on screen |
| Click changes state | `dispatch_click` -> DEX `onClick` -> `step()` -> re-render |
| Screenshots captured | `frames/frame_000..008.png` |
| Multiple frames | 9 frames, all distinct SHA256 |
| GIF | `miniandroid-demo-proof.gif` assembled ONLY from runtime frames |

## Identifiers for this evidence set

```
MiniAndroid binary SHA256 (final, includes the 12x/22s AOSP alignment):
  2016c381357acea025e71d877255bf6feee9e0158bcff909fc2aaeb89e699539
demo APK SHA256:
  c0959a719289735265f8cb0e47a488883c6a6bf39d314b2b783fcdc7ec9ad6e8
command:
  ./build/miniandroid run demo/build/miniandroid-demo.apk \
      -o run/demo_evidence --click-count 8
exit code: 0
frames: 9 (1 launch + 8 clicks), 1080x1920 each
```

Per-frame state and framebuffer hashes (frame 0 includes the built-in
post-launch probe click, hence `count=1` at launch capture):

```
frame 0: count=1 pos=(220,370) color=GREEN  sha=e5c8d511651e4276
frame 1: count=2 pos=(400,660) color=BLUE   sha=5c73aa41728bd18e  diff=51637px
frame 2: count=3 pos=(580,950) color=YELLOW sha=4359e56ddff842d1  diff=51632px
frame 3: count=4 pos=(760,80)  color=RED    sha=70dbf13233b3      diff=51718px
frame 4: count=5 pos=(40,370)  color=GREEN  sha=f6862e1923260904  diff=51751px
frame 5: count=6 pos=(220,660) color=BLUE   sha=dbc7814d96bd63be  diff=51807px
frame 6: count=7 pos=(400,950) color=YELLOW sha=f19bfb287af9b2a9  diff=51689px
frame 7: count=8 pos=(580,80)  color=RED    sha=dc929b1f6e21994f  diff=51729px
frame 8: count=9 pos=(760,370) color=GREEN  sha=276ccd7da2dcf943  diff=51703px
```

Pixel-vs-state verification (rendered pixels match the app's own status text):
frame 3 claims `pos=(760,80) color=RED`; the red-pixel bounding box in
`frames/frame_003.png` is (762,219)-(918,375) — x matches the claimed margin,
y is the same stage-relative offset as every other frame.

Deterministic replay: three independent clean runs produced byte-identical
frame SHA256 sequences (`e5c8d511651e4276`, `5c73aa41728bd18e`, ...).

## Committed artifacts

| File | Role |
|---|---|
| `docs/demo/demo_frames.png` | 9-frame strip (downscaled from the runtime PNGs) |
| `docs/demo/demo_manifest.json` | full per-frame machine evidence |
| `demo/` | demo app source + build + validation fixture |
| `miniandroid/run/demo_evidence/` | full-resolution runtime frames (local) |

## Runtime fixes that this proof required (and their regression status)

1. `onCreate` was invoked without `this` on two entry paths — instance-field
   writes inside `onCreate` were silently dropped (manifest path passed only
   the Bundle; legacy path passed NO arguments with hardcoded register sizes).
   Per AOSP `ActivityThread.performLaunchActivity`, both paths now allocate
   the Activity heap object and pass `[this, savedInstanceState]`.
2. `<clinit>` ran only for `org.telegram.*` classes; every other app's static
   final constants were null. Initialization now follows AOSP
   `ClassLinker::EnsureInitialized` semantics (first active use, with the
   existing framework/library exclusion list and re-entrancy guard).
   `new-instance` now also triggers initialization (it previously did not).
3. `array-length` and every `/2addr` arithmetic opcode read their B register
   from the wrong instruction nibble (`>> 4` instead of `>> 12`, AOSP 12x
   format is `B|A|op`). `array-length v1, v0` read v2; `rem-int/2addr v1, v0`
   read v11.
4. Plain-text manifest parsing broke on standard AAPT-style multi-line tags
   (newline not treated as whitespace), so launcher activities were missed.
5. The whole 12x/22s decode family was split between two nibble conventions:
   conversions, neg/not, wide /2addr, lit16 and move-wide decoded the mirror
   image of AOSP `B|A|op` (and move-wide even read its source from the opcode
   byte). The swapped fixture encoders cancelled the swap inside the test
   suites while real D8 bytecode broke. The engine and all fixture encoders
   are now uniformly AOSP (fix f677443c + test d2b6b9a1); all three semantic
   suites re-verified green (14/14, 55/55, 25/25).

Regression status (13-APK open-source corpus, OLD vs NEW binary, same
command, screenshot SHA256 compared):

* 12/13 identical (exit code, status, screenshot hash) — including the
  `simplestopwatch` golden (`2a12587a...` on both binaries).
* 1 improvement: `microtimer` previously bailed out of `onCreate` early
  (blank screen, 10 interpreted method entries); with the `this` fix it now
  runs its full `onCreate` (120 method entries) and renders its real view
  tree (LinearLayout + ScrollView + buttons + custom `RoTimeControl` view).
* Pre-existing `stopwatchmuellerma` PARTIAL status unchanged on both binaries.
