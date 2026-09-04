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
| Time changes state | `--frames`: virtual Looper gate -> DEX `Runnable.run()` -> `step()` -> re-render (`demo_timer_manifest.json`) |
| Screenshots captured | `frames/frame_000..008.png` |
| Multiple frames | 9 frames, all distinct SHA256 |
| GIF | `docs/demo/demo_proof.gif` assembled ONLY from runtime frames (provenance-gated) |

## Identifiers for this evidence set

```
MiniAndroid binary SHA256 (final; virtual-clock Looper + activity <init> fix):
  059b640a431bd3d8c71543940b843cf9db02227e08355ea18bf1395868831c79
demo APK SHA256 (adds the self-reposting postDelayed ticker):
  ffb50bc7826cd9512455443dc8ee6477ceca703fbb964d5706be47ed986022c1
commands:
  ./build/miniandroid run demo/build/miniandroid-demo.apk \
      -o run/demo_evidence --click-count 8          # interaction-driven
  ./build/miniandroid run demo/build/miniandroid-demo.apk \
      -o run/demo_timer_evidence --frames 8 --frame-delay 300   # time-driven
exit code: 0 (both)
frames: click mode 9 (1 launch + 8 clicks); timer mode 8 (1 launch + 7 Looper gates)
```

## Time-driven proof: the app animates ITSELF through Looper time

The demo schedules a self-reposting `Handler.postDelayed(this, 300)` ticker
in `onCreate` — the canonical Android animation pattern. `--frames N`
runs the app with ZERO injected interaction: the runtime advances its
deterministic virtual Looper clock 300 ms per frame and drains whatever
became due, so the app's own DEX ticker is the ONLY state driver:

```
frame 0: count=1 (the ticker's first fire at the post-onCreate idle-settle)
frame k: count=k+1 — each gate fires exactly 1 runnable (the re-posted ticker)
```

The timer-mode frame sequence is BYTE-IDENTICAL to the click-mode sequence
(same frames 0..7 in `demo_timer_manifest.json` and `demo_manifest.json`):
one state machine, two independent drivers — input events and Looper time.

Launch-state mechanism note: earlier evidence described frame 0's `count=1`
as a "built-in post-launch probe click". The probe click (EXP-088 Phase B)
still exists for default journey runs (it advances Telegram's intro), but
in `--click-count` / `--frames` capture modes it is now deliberately
skipped — frame 0's step comes from the app's OWN ticker, which is the
stronger claim: zero runtime-injected interaction in both capture modes.
The pinned framebuffer hash sequence is unchanged.

This batch also fixed a lifecycle fidelity gap the ticker exposed: the
engine allocated the Activity heap object and called onCreate WITHOUT
running the app's declared `<init>()V` — instance-field initializers
(`private boolean auto = true;`) were silently false. Per AOSP
`ActivityThread.performLaunchActivity`, all three activity-launch paths now
run the app's no-arg constructor before onCreate.

## Two hash domains (both deterministic, both documented)

Every frame carries TWO SHA256 values in `demo_manifest.json`:

* `sha256` — the raw **framebuffer** hash: the deterministic render law
  (unchanged across every rebuild that did not touch rendering; matches the
  hashes pinned in earlier evidence).
* `png_sha256` — the SHA256 of the **PNG file bytes** written to disk: the
  hash a visitor can recompute after downloading a frame and compare
  byte-for-byte.

Two independent runs of the same command produce byte-identical PNG files
(verified: file-level hashes equal across runs AND framebuffer hashes equal
across runs and equal to the committed evidence).

Scope note: `sha256` (framebuffer) is the cross-platform identity — it is
the rendering law and must match for every build of the same source. The
PNG file bytes additionally depend on the bundled codec builds (Linux links
the system libpng, Windows pins libpng 1.6.44), so `png_sha256` is pinned
per build lineage; the values documented here are the Linux x64 release
build, which is also what the release clean-extract test re-verifies.

Per-frame state and both hashes (frame 0 includes the built-in post-launch
probe click, hence `count=1` at launch capture; `png=` is the hash of the
PNG file bytes, verifiable on any downloaded frame):

```
frame 0: count=1 pos=(220,370) color=GREEN  fb=e5c8d511651e4276 png=99996cec9444b6cb
frame 1: count=2 pos=(400,660) color=BLUE   fb=5c73aa41728bd18e png=eb900379bd994164  diff=51637px
frame 2: count=3 pos=(580,950) color=YELLOW fb=4359e56ddff842d1 png=121f669037d60775  diff=51632px
frame 3: count=4 pos=(760,80)  color=RED    fb=70dbf13233b36e1e png=07abaedf28b70d9b  diff=51718px
frame 4: count=5 pos=(40,370)  color=GREEN  fb=f6862e1923260904 png=e6fde69e6c04475f  diff=51751px
frame 5: count=6 pos=(220,660) color=BLUE   fb=dbc7814d96bd63be png=776512caf8fcdfe5  diff=51807px
frame 6: count=7 pos=(400,950) color=YELLOW fb=f19bfb287af9b2a9 png=82623ed2dcaf880e  diff=51689px
frame 7: count=8 pos=(580,80)  color=RED    fb=dc929b1f6e21994f png=0b87fd7d06d2f50c  diff=51729px
frame 8: count=9 pos=(760,370) color=GREEN  fb=276ccd7da2dcf943 png=d229046b4a7f9a40  diff=51703px
```

Pixel-vs-state verification (rendered pixels match the app's own status text):
frame 3 claims `pos=(760,80) color=RED`; the red-pixel bounding box in
`frames/frame_003.png` is (762,219)-(918,375) — x matches the claimed margin,
y is the same stage-relative offset as every other frame.

Deterministic replay: three independent clean runs produced byte-identical
frame SHA256 sequences (`e5c8d511651e4276`, `5c73aa41728bd18e`, ...).

## Visual proof assets (generated ONLY from the frames above)

`scripts/make_demo_proof.py` rebuilds both assets. It first runs a
provenance gate — every input frame PNG must hash to its committed
`png_sha256` and every framebuffer hash must match the committed manifest —
and refuses to produce anything on any mismatch. The app-area pixels are
cropped/scaled runtime output only; the scripts add text exclusively in
documentation bands around the frames.

| Asset | SHA256 (first 16) | Content |
|---|---|---|
| `docs/demo/demo_proof.gif` | `43790411790b641a` | all 9 runtime frames, 540x560, 700 ms/frame |
| `docs/demo/demo_frames.png` | `114c799fc117cc98` | labeled contact sheet: STATE 0..4 (frames 0..4) |

## Committed artifacts

| File | Role |
|---|---|
| `docs/demo/demo_frames.png` | labeled STATE 0..4 contact sheet built from runtime frames |
| `docs/demo/demo_proof.gif` | 9-frame animation assembled only from runtime frames |
| `docs/demo/demo_manifest.json` | full per-frame machine evidence (framebuffer + PNG hashes) |
| `scripts/make_demo_proof.py` | provenance-gated generator for the visual assets |
| `demo/` | demo app source + build + validation fixture |
| `miniandroid/run/demo_evidence/` | full-resolution runtime frames (local, regenerated by the command above) |

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
