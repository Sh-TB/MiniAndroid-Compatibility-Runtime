# MiniAndroid Demo — Real APK Execution Proof

This directory contains a minimal, fully open-source Android application built
specifically to prove that MiniAndroid executes a real APK end-to-end:

```
APK install -> Activity.onCreate (real DEX bytecode) -> programmatic View
hierarchy -> setContentView -> rendered frame -> dispatched click -> DEX
onClick -> state change (counter, position, color, text) -> re-render
```

Every piece of state is encoded in VISIBLE UI, so a screenshot is
self-evidencing:

* a title `TextView` — "Hello MiniAndroid!"
* a status `TextView` — "count=N pos=(x,y) color=NAME"
* a colored box `View` — moves and changes color on every click
* a `Button` — the interaction that drives all state changes

The UI is built programmatically in Java/DEX on purpose: it exercises the
deepest runtime path (real bytecode driving the View API) and needs no
resource compilation step.

## Building the APK

No Android SDK is required. The toolchain is three official open-source
releases (download them once, see `build_demo_apk.sh` for the exact paths):

| Tool | Purpose | License | Source |
|---|---|---|---|
| ECJ 3.33.0 | Java compiler | EPL-2.0 | eclipse.org / Maven Central `org.eclipse.jdt:ecj` |
| D8 (R8) 8.13.23 | .class -> classes.dex | Apache-2.0 (AOSP) | Google Maven `com.android.tools:r8` |
| android.jar (API 34) | compile-time platform stubs | Apache-2.0 (AOSP) | Google `dl.google.com/android/repository/platform-34-ext7_r03.zip` |

```bash
bash demo/build_demo_apk.sh    # produces demo/build/miniandroid-demo.apk
```

## Running the proof

```bash
./build/miniandroid run demo/build/miniandroid-demo.apk \
    -o run/demo_evidence --click-count 8
```

`--click-count N` dispatches N sequential clicks (round-robin over all views
with a registered `OnClickListener`), re-renders through the standard frame
pipeline after each click, and writes:

```
frames/frame_000.png      launch UI, no interaction
frames/frame_001..N.png   UI after each dispatched click
frames/manifest.json      per-frame evidence (see below)
```

`frames/manifest.json` records, for every frame: the clicked view id/class,
pixel-diff count vs the previous frame, the framebuffer SHA256, and the
app's own visible text state (`count=... pos=... color=...` read back from
the ViewShadow tree). The state transitions come entirely from the APK's own
DEX bytecode reacting to the dispatched clicks.

## What the evidence shows

A valid evidence run must show all of the following (all machine-checkable
from `frames/manifest.json`):

1. Every click dispatched (`clicks_dispatched == click_count_requested`).
2. Every frame hash distinct (state actually changed).
3. The app's status text advances exactly as the DEX logic dictates:
   `count` increments, `pos` cycles through a 5x4 grid, `color` cycles
   red -> green -> blue -> yellow.
4. The rendered pixels match the claimed state (the 160x160 box has the
   claimed color at the claimed position).
5. Re-running from a clean output directory reproduces the identical
   SHA256 sequence (deterministic replay).
