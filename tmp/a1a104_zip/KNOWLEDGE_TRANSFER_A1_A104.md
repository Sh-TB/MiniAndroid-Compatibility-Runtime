# MiniAndroid Compatibility Runtime — Knowledge Transfer Document
## From A1 to A104 — Complete Engineering Knowledge Base

**Document purpose:** This file transfers ALL engineering knowledge from the 
A1-A104 verification campaign to any new developer (or AI agent) who needs to 
understand, maintain, or extend the MiniAndroid Compatibility Runtime.

**Audience:** A competent C++ developer who has never seen this codebase.
**Goal:** After reading this document, you should be able to:
1. Understand the runtime architecture
2. Know every bug that was found and fixed
3. Know every boundary that remains
4. Reproduce all verification results
5. Continue the work toward A105+

---

## Part 1: What is MiniAndroid Compatibility Runtime?

MiniAndroid is a **pure C++ Android compatibility runtime** (~128K lines of code) 
that takes an APK as input and produces rendered pixels as output — WITHOUT 
using the Android emulator or any Android system image.

The pipeline:
```
APK file
  ↓
APK Parser (zip + manifest + resources.arsc)
  ↓
DEX Parser (multi-DEX class/method extraction)
  ↓
Dalvik Execution Engine (bytecode interpreter)
  ↓
Framework Shadows (Android API stubs)
  ↓
ViewTree (measure → layout → draw)
  ↓
Software Renderer (pixel framebuffer)
  ↓
PNG screenshot
```

**Key principle (Constitution V2 §1):**
> Root Cause > Symptom
> Semantic Contract > Stub Count
> Runtime Evidence > Static Guess
> Fresh Evidence > Stale Evidence
> Reproducible Proof > Successful Exit Code

---

## Part 2: Repository Layout

```
/home/z/my-project/audit/MiniAndroid-Compatibility-Runtime/
├── miniandroid/                    # Main runtime source
│   ├── src/
│   │   ├── dex/
│   │   │   ├── dalvik_engine.cpp   # ~49K lines — the bytecode interpreter
│   │   │   ├── dalvik_engine.h     # Engine class definition
│   │   │   ├── dex_parser.cpp      # DEX file parser
│   │   │   └── class_resolver.cpp  # Multi-DEX class resolution
│   │   ├── framework/
│   │   │   ├── android_shadows.cpp # ~5K lines — View/Map/Collection shadows
│   │   │   ├── android_shadows.h   # Shadow class definitions
│   │   │   ├── canvas_shadow.cpp   # Canvas draw op recording
│   │   │   ├── touch_dispatcher.cpp# AOSP touch event dispatch
│   │   │   └── ...
│   │   ├── runtime/
│   │   │   └── execution_engine.cpp# ~7.5K lines — render traversal, lifecycle
│   │   ├── renderer/
│   │   │   ├── software_renderer.cpp# Framebuffer + draw ops
│   │   │   └── ...
│   │   ├── fonts/
│   │   │   └── text_shaper.cpp     # FreeType + HarfBuzz text rendering
│   │   ├── resources/
│   │   │   ├── arsc_parser.cpp     # resources.arsc binary parser
│   │   │   ├── layout_inflater.cpp# XML layout → ViewNode tree
│   │   │   └── ...
│   │   ├── apk/
│   │   │   └── apk_parser.cpp      # APK (ZIP) parser
│   │   └── main.cpp                # CLI entry point
│   ├── Makefile                    # Build system (g++ -std=c++17)
│   └── build/
│       └── miniandroid             # The compiled binary (~130MB)
├── CONSTITUTION_V2.md              # Engineering laws (READ FIRST)
├── root_registry.json              # 540 root causes catalogued
├── miniandroid/APK_REGISTRY.json  # 22 APK test corpus
└── docs/
    ├── S92_GRAPHICS_VERIFICATION.md# Verification ladder rules
    ├── VERIFIED_EXECUTED_GAMES.md  # Historical verified games list
    └── ...
```

---

## Part 3: How to Build and Run

### Build:
```bash
cd /home/z/my-project/audit/MiniAndroid-Compatibility-Runtime/miniandroid
make -j 1   # Use -j 1 to avoid OOM (dalvik_engine.cpp is huge)
# Binary: miniandroid/build/miniandroid
```

### Run an APK:
```bash
cd /home/z/my-project/audit/MiniAndroid-Compatibility-Runtime
./miniandroid/build/miniandroid run <apk_path> \
    --width 1080 --height 1920 \
    --frames 20 \
    --max-seconds 30 \
    -o <output_dir>
# Screenshot: <output_dir>/screenshot.png
# Frames: <output_dir>/frames/frame_NNN.png
# Report: <output_dir>/report.md
```

### Run with interaction (tap):
```bash
./miniandroid/build/miniandroid run <apk_path> \
    --width 1080 --height 1920 \
    --frames 20 \
    --tap <x>,<y>@<frame_number> \
    -o <output_dir>
```

### Critical: Always use 1080×1920
The layout system uses density 2.0 internally. If you use 540×960, the 
TextShaper draws glyphs at coordinates BEYOND the framebuffer edge (e.g., 
y=1156 when framebuffer height is 960). Always use 1080×1920 unless the 
app explicitly requests a different density.

---

## Part 4: The S92 Verification Ladder

Every app is classified into one of these verdicts (honest, no false promotion):

```
UNEXECUTED          — no screenshot produced
LOADED              — APK parsed, nothing more
LIFECYCLE_VERIFIED  — onCreate/onStart/onResume dispatched
RENDER_STARTED      — renderer initialized
FRAME_CAPTURED      — screenshot exists but flat single-color
VISUALLY_PARTIAL    — few colors, likely just background
VISUALLY_VERIFIED   — multiple colors, real app content
INTERACTION_VERIFIED — tap dispatched, state changed
FULLY_VERIFIED      — + 3-run byte-identical repeatability
```

**Non-negotiables (S92 §0):**
- "screenshot exists" ≠ "graphics loaded" — a flat single-color PNG is 
  FRAME_CAPTURED, NOT VISUALLY_VERIFIED
- "callback fired" ≠ FULLY_VERIFIED — interaction must be proven with 
  pixel diff
- "ViewTree exists" ≠ graphics-verified — pixels are the truth

### Classification logic:
```python
if unique_colors <= 1:
    verdict = "FRAME_CAPTURED"
elif unique_colors <= 3:
    verdict = "VISUALLY_PARTIAL"
elif unique_colors >= 8 and non_dominant_pixels >= 1000:
    verdict = "VISUALLY_VERIFIED"
```

---

## Part 5: Every Patch Applied (A1-A104)

### A1-A50: Compose runtime pipeline setup (dooz focus)
These were early session patches to set up the Compose View pipeline:
- Created ComposeView, AndroidComposeView, WrappedComposition
- Created c1, N/a (Compose internal classes)
- Called LF/A0.a() (Compose setContent)
- **Result:** Compose composition never materialized because Compose runtime 
  internals (SlotTable, Composer, Applier, LayoutNode) were not implemented

### A51-A52: File.getName/getAbsolutePath null receiver guards
- **Bug:** File.getName() called on null receiver → crash
- **Fix:** Added null receiver guard in File shadow methods

### A61: dialog_shadow.cpp null pointer dereference
- **Bug:** `find_node(row_id)->children.push_back(...)` when find_node returns null
- **Fix:** Added `get_or_create_node(row_id)` before accessing children

### A62: Shell injection via popen
- **Bug:** `popen("unzip -p '" + apk_path + "'...")` was vulnerable to injection
- **Fix:** Replaced with in-process ZIP parser (no shell execution)

### A64: Hardcoded /tmp path
- **Bug:** File default path was hardcoded to `/tmp/miniandroid/files`
- **Fix:** Use `Storage::package_data_dir()` instead

### A68: Stale ViewTree after finish()
- **Bug:** After Activity.finish(), the content_view_id was not cleared, 
  so the renderer kept drawing the old ViewTree
- **Fix:** Clear content_view_id after finish() (execution_engine.cpp ~line 7490)

### A91: onPostCreate dispatch (PARTIAL — placed in wrong path)
- **Bug:** Apps like minos create their GameView in onPostCreate, not onCreate. 
  The runtime never dispatched onPostCreate.
- **Fix (A91):** Added onPostCreate dispatch between onActivityCreated and 
  onActivityPostCreated. BUT placed it in Path A (multi-DEX index lookup 
  at line ~2083) instead of Path B (single-DEX at line ~1814).

### A92: Framebuffer resolution mismatch (VERIFICATION TOOLING FIX)
- **Bug:** Running apps with `--width 540 --height 960` produced flat 
  single-color screenshots. The layout system uses density 2.0 internally 
  (1080×1920), but the framebuffer was 540×960. TextShaper draws glyphs 
  at y=1156 — past the y=959 framebuffer edge.
- **Fix:** Use `--width 1080 --height 1920` for all verification runs.
- **Impact:** gmdice flipped 1→113 unique colors; glxy flipped 1→20,421 
  unique colors. Both promoted to VISUALLY_VERIFIED.
- **File:** No source change — this is a CLI usage fix.

### A93: onPostCreate dispatch in wrong code path (FIXED A91's mistake)
- **Bug:** A91 placed the onPostCreate dispatch in Path A (multi-DEX index 
  lookup). Most single-DEX apps (minos, bullseye, blockbuster, every simple 
  game) take Path B (DEX 0 lookup) and never reach the A91 patch.
- **Fix:** Hoisted the onPostCreate dispatch into Path B too. New log marker 
  `[A93-POSTCREATE]`.
- **File:** `miniandroid/src/dex/dalvik_engine.cpp` — added onPostCreate 
  dispatch in the Path B block (line ~1864), between onActivityCreated 
  and onActivityPostCreated.
- **Impact:** minos now reaches createGame() (256 IMPLEMENTED APIs, was 137).

### A94: Display.getWidth/getHeight missing
- **Bug:** minos DisplayUtils.getDisplaySize called Display.getWidth and 
  Display.getHeight which were MISSING (REC-MISS) and returned 0. 
  MazeFactory.createMaze got 0×0 dimensions → empty cell list → 
  Random.nextInt(0) → IllegalArgumentException.
- **Fix:** Added Display.getWidth/getHeight stubs returning 1080/1920 
  (matching the existing getMetrics/getSize device-profile law). Also 
  added Display.getDisplayInfo safety net.
- **File:** `miniandroid/src/dex/dalvik_engine.cpp` — added handler 
  at line ~35665 for getWidth/getHeight on Landroid/view/Display;.

### A95: View.getWidth fallback for pre-layout Runnables
- **Bug:** AOSP View.getWidth() = mRight - mLeft, set during the layout 
  pass. But View.post() Runnables queued during onCreate fire in the 
  post-onCreate drain (BEFORE the first traversal's layout pass runs). 
  minos's GameView ctor reads container.getWidth()=0 → cellSize=0 → 
  cols=0 → MazeFactory.createMaze gets 0×0.
- **Fix:** Added a fallback in ViewShadow.getWidth/getHeight:
  1. If measured_right - measured_left > 0, return that (current law)
  2. Else if measured_width > 0, return measured_width
  3. Else if width == -1 (MATCH_PARENT), resolve to parent's 
     measured_width or screen width (1080)
  4. Else if width > 0, return width
  5. Else 0
- **File:** `miniandroid/src/framework/android_shadows.cpp` — modified 
  the getWidth/getHeight handler at line ~4330.
- **Impact:** minos now reads containerWidth=1080, containerHeight=1920, 
  cols=6, rows=10, cellSize=180. 688 IMPLEMENTED APIs (was 262).

### A101: HashMap.size() always returned 0
- **Bug:** HashMap.size() had a stub that always returned 0, regardless 
  of how many entries were stored. This broke any app that checks 
  Map.size() > 0 before iterating.
- **Fix:** Changed HashMap.size() to count actual "key_" prefixed fields 
  in the heap object.
- **File:** `miniandroid/src/dex/dalvik_engine.cpp` — line ~44238, the 
  HashMap.size() handler now iterates obj->fields and counts entries 
  starting with "key_" (excluding "__" internal fields).

### A102: ArrayDeque/LinkedList not in ArrayList handler's class_name gate
- **Bug:** The ArrayList handler at line ~44793 checked for:
  - class_name == "Ljava/util/ArrayList;"
  - class_name.find("ArrayList") != npos
  - class_name.find("List;") != npos
  
  But java.util.ArrayDeque doesn't match any of these. minos 
  MazeFactory.createMaze uses ArrayDeque as its List. Without this gate, 
  ArrayDeque.add fell through to a generic stub and the maze cells list 
  stayed empty.
- **Fix:** Added ArrayDeque and LinkedList to the class_name gate:
  ```cpp
  if (class_name == "Ljava/util/ArrayList;" ||
      class_name.find("ArrayList") != std::string::npos ||
      class_name.find("List;") != std::string::npos ||
      class_name == "Ljava/util/ArrayDeque;" ||
      class_name.find("ArrayDeque") != std::string::npos ||
      class_name == "Ljava/util/LinkedList;" ||
      class_name.find("LinkedList") != std::string::npos) {
  ```
- **File:** `miniandroid/src/dex/dalvik_engine.cpp` — line ~44793.

### A102 investigation: Map.keySet returns wrong class (OBSERVED — not fixed)
- **Bug:** When Map.keySet() is called, CollectionShadow::dispatch (F-064 
  handler at line ~1036 of android_shadows.cpp) creates a HashSet view 
  with view_elements populated from the source map's entries. The view 
  is allocated via `heap_->allocate("Ljava/util/HashSet;")`.
  
  But when iterator() is later called on the returned view, the 
  receiver's class_descriptor is "Ljava/util/ArrayList;" instead of 
  "Ljava/util/HashSet;". The hasNext() handler then checks 
  state->view_elements which is empty (because the state for the 
  ArrayList-classed obj_id doesn't have the view_elements that were 
  set on the HashSet-classed obj_id).
  
  Result: minos MazeFactory.getUnvisitedNeighbours returns empty Map → 
  Random.nextInt(0) → IAE → 0 pixels.
- **Status:** This is a deep bug in the shadow dispatch layer. minos 
  stays FRAME_CAPTURED with this known root cause documented.

### A103: 3-Run Repeatability Verification
- **Test:** Ran each of the 7 INTERACTION_VERIFIED apps 3 times at 
  1080×1920 with frames=5, max-seconds=15. Computed SHA256 of 
  screenshot.png for each run.
- **Result:** ALL 7 apps produced byte-identical screenshots across 
  3 runs. Combined with INTERACTION_VERIFIED, all 7 satisfy the S92 §24 
  FULLY_VERIFIED contract.
- **Promoted:** 2048, snake_deluxe, tetris, tictactoe_deluxe, minicraft, 
  snakeneon, gmdice → FULLY_VERIFIED

### A104: dooz (TicTacToe) execution — Compose Navigation boundary
- **APK:** io.github.yamin8000.dooz v18 (SHA: d81292cd...)
- **Execution:** 20,166 IMPLEMENTED APIs (largest of any app tested), 
  253 STUBBED, 0 MISSING, 0 ERROR
- **ViewTree:** ComposeView → AndroidComposeView (0 children, 0 draw ops)
- **Screenshot:** 1 unique color (250,250,250 = white background)
- **Root cause:** Compose Navigation's NavHost calls 
  addNavigator("composable", ComposableNavigator()) during composition, 
  but the composition never materializes because the Compose runtime 
  internals (SlotTable, Composer, Applier, LayoutNode) are not implemented.
- **Error:** "Could not find Navigator with name "composable". You 
  must call NavController.addNavigator() for each navigation type."
- **Status:** FRAME_CAPTURED — requires WAVE 8 (Compose runtime, 
  multi-week effort)

---

## Part 6: Final Verification State (A104)

| App | S92 Ladder | Unique Colors | Tap Pixel Change | 3-Run SHA |
|-----|-----------|---------------|-----------------|-----------|
| 2048 | **FULLY_VERIFIED** | 81 | 14.32% @ UP btn | 59ca1526611c4622 ×3 |
| snake_deluxe | **FULLY_VERIFIED** | 132 | 0.81% @ START btn | 34a712689ce66e58 ×3 |
| tetris | **FULLY_VERIFIED** | 135 | 1.85% @ START btn | f360daa244cfca8d ×3 |
| tictactoe_deluxe | **FULLY_VERIFIED** | 227 | 1.76% @ btn 5 | af6094295ecb50e3 ×3 |
| minicraft | **FULLY_VERIFIED** | 128 | 0.20% @ UP btn | b0876952f41e4af2 ×3 |
| snakeneon | **FULLY_VERIFIED** | 61 | 0.91% @ UP btn | cc986d4b4d3ec3f3 ×3 |
| gmdice | **FULLY_VERIFIED** | 113 | 0.81% @ 3D20 btn | f3b483fe7b7cf51b ×3 |
| blockbuster | VISUALLY_VERIFIED | 83 | n/a (WebView) | — |
| glxy | VISUALLY_VERIFIED | 20,421 | n/a (GLSurfaceView) | — |
| dooz | FRAME_CAPTURED | 1 | n/a | — |
| minos | FRAME_CAPTURED | 1 | n/a | — |
| bullseye | FRAME_CAPTURED | 1 | n/a | — |
| battleship | FRAME_CAPTURED | 1 | n/a | — |

**Total: 7 FULLY_VERIFIED + 2 VISUALLY_VERIFIED + 5 FRAME_CAPTURED = 14 apps**

---

## Part 7: Known Boundaries (What Still Doesn't Work)

### 1. Compose Runtime Internals (WAVE 8 — multi-week)
**Affected apps:** dooz, battleship, any Jetpack Compose app
**Root cause:** The Compose runtime internals are not implemented:
- SlotTable (slot management for recomposition)
- Composer (the recompose loop driver)
- Applier (applies composition changes to the LayoutNode tree)
- LayoutNode (the Compose equivalent of View — measure/layout/draw)
**Symptoms:** AndroidComposeView.dispatchDraw has 0 draw ops; the 
composition never materializes.
**Fix approach:** Implement the Compose runtime tree by porting from 
AOSP `androidx.compose.runtime` and `androidx.compose.ui` source.

### 2. AppCompat setContentView(int) inflation (A102+ candidate)
**Affected apps:** bullseye
**Root cause:** AppCompatDelegateImpl.setContentView(resId) inflates the 
layout XML but the inflated root view is NOT added to ContentFrameLayout 
as a child. The U007 inflate path runs (52 views inflated) but they 
aren't attached to the content parent.
**Symptoms:** ViewTree shows FitWindowsLinearLayout → ViewStubCompat + 
ContentFrameLayout(0 children).
**Fix approach:** Trace AppCompatDelegateImpl.setContentView → ensure 
LayoutInflater.inflate adds the inflated root as a child of contentParent.

### 3. Map.keySet view class bug (A102 deep investigation)
**Affected apps:** minos
**Root cause:** When Map.keySet() is called, CollectionShadow creates a 
HashSet view. But when iterator() is called on the returned view, the 
receiver's class_descriptor is "Ljava/util/ArrayList;" instead of 
"Ljava/util/HashSet;". The hasNext() handler then checks 
state->view_elements which is empty.
**Symptoms:** MazeFactory.getUnvisitedNeighbours returns empty Map → 
Random.nextInt(0) → IAE → 0 pixels.
**Fix approach:** Investigate why the heap object's class_descriptor 
changes from HashSet to ArrayList. Likely a heap obj_id reuse issue or 
the iterator() handler at line 914 returning the wrong class.

### 4. WebView HTML5/JS execution (WAVE 10+)
**Affected apps:** blockbuster (partially — renders WebView chrome but 
not the HTML5 game canvas)
**Root cause:** WebView content (HTML5 game) needs JS execution + DOM 
rendering. The runtime has a QuickJS engine but the HTML5/Canvas pipeline 
is partial.
**Fix approach:** Complete the WebView HTML5/Canvas rendering pipeline.

---

## Part 8: Key Architecture Concepts

### 8.1 The Dalvik Execution Engine (dalvik_engine.cpp ~49K lines)
The interpreter executes DEX bytecode opcode-by-opcode. Key components:
- `try_recursive_invoke(class, method, args, ...)` — dispatches a method 
  call. First tries DEX bytecode, then falls back to bridge_to_api.
- `bridge_to_api(class_name, method, args, ...)` — the framework API 
  stub layer. Handles Android framework classes that have no DEX body.
- `try_shadow_dispatch(class_name, method, ...)` — dispatches to the 
  shadow layer (CollectionShadow, ViewShadow, ActivityShadow, etc.).
- `throw_deferred(exc_class, message, ...)` — synthesizes a Java 
  exception. Sets pending_exception_ and either redirects to a catch 
  handler or unwinds the frame.

### 8.2 The Shadow Layer (android_shadows.cpp ~5K lines)
Shadows are C++ objects that model Android framework classes:
- **ActivityShadow** — Activity lifecycle, setContentView, findViewById
- **ViewShadow** — View tree, measure/layout/draw, getWidth/getHeight
- **CanvasShadow** — Canvas draw op recording (drawText, drawRect, etc.)
- **CollectionShadow** — List/Map/Set semantics (ArrayList, HashMap, 
  HashSet, ArrayDeque, etc.)
- **HandlerShadow** — Handler/Looper message queue
- **TouchDispatcher** — AOSP ViewGroup.dispatchTouchEvent claim law

### 8.3 The Render Traversal (execution_engine.cpp ~7.5K lines)
Every frame:
1. **Attach wave** — dispatch onAttachedToWindow on the ViewTree
2. **Measure pass** — onMeasure for each view (DEX bytecode if overridden, 
   else framework default)
3. **Layout pass** — onLayout for each view
4. **Draw pass** — onDraw for each view, recording draw ops on Canvas
5. **Pixel copy** — render the Canvas draw ops to the framebuffer

### 8.4 The Heap (DalvikHeap)
Every Java object is a heap object with:
- `object_id` (uint32_t) — unique identifier
- `class_descriptor` (string) — e.g., "Ljava/util/HashMap;"
- `fields` (map<string, DalvikValue>) — instance fields

DalvikValue can be: INT32, FLOAT, OBJECT_REF, STRING_REF, CLASS_REF, 
BOOLEAN, etc.

### 8.5 The APK Registry
`miniandroid/APK_REGISTRY.json` catalogs 22 test APKs with:
- Package name, version, SHA256, download URL
- Test purpose, status (PROVEN/PARTIAL/FROZEN)
- Storage policy: APKs are NEVER in the repo (zero-APK policy); they 
  live in the external cache (`apk_cache/` directory)

---

## Part 9: How to Reproduce All Verification Results

### Build the binary:
```bash
cd /home/z/my-project/audit/MiniAndroid-Compatibility-Runtime/miniandroid
make -j 1
```

### Download APKs:
```bash
cd /home/z/my-project/audit/MiniAndroid-Compatibility-Runtime
# dooz
curl -L -o apk_cache/dooz_18.apk \
    "https://f-droid.org/repo/io.github.yamin8000.dooz_18.apk"
# Other APKs are in /home/z/my-project/upload/s80_games/ etc.
```

### Run the verification corpus:
```bash
APKS=(
    "2048:/home/z/my-project/upload/s80_games/build_2048/g2048_v1.0_vc1.apk"
    "snake_deluxe:/home/z/my-project/upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk"
    "tetris:/home/z/my-project/upload/s80_games/build_tetris/tetris_v1.0_vc1.apk"
    "tictactoe_deluxe:/home/z/my-project/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk"
    "minicraft:/home/z/my-project/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk"
    "snakeneon:/home/z/my-project/upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk"
    "gmdice:/home/z/my-project/games_test/apks/gmdice.apk"
    "bullseye:/home/z/my-project/games_test/apks/bullseye.apk"
    "battleship:/home/z/my-project/games_test/apks/battleship.apk"
    "blockbuster:/home/z/my-project/games_test/apks/blockbuster.apk"
    "minos:/home/z/my-project/games_test/apks/minos.apk"
    "glxy:/home/z/my-project/games_test/apks/glxy.apk"
    "dooz:apk_cache/dooz_18.apk"
)
for entry in "${APKS[@]}"; do
    name="${entry%%:*}"
    apk="${entry##*:}"
    ./miniandroid/build/miniandroid run "$apk" \
        --width 1080 --height 1920 \
        --frames 5 --max-seconds 15 \
        -o /tmp/verify_${name}
    sha256sum /tmp/verify_${name}/screenshot.png
done
```

### Run 3-run repeatability:
```bash
for run in 1 2 3; do
    ./miniandroid/build/miniandroid run <apk> \
        --width 1080 --height 1920 \
        --frames 5 --max-seconds 15 \
        -o /tmp/repeat_${run}
    sha256sum /tmp/repeat_${run}/screenshot.png
done
# All 3 SHA256s should be identical for FULLY_VERIFIED apps
```

### Run interaction test:
```bash
./miniandroid/build/miniandroid run <apk> \
    --width 1080 --height 1920 \
    --frames 15 --max-seconds 30 \
    --tap <x>,<y>@<frame> \
    -o /tmp/tap_test
# Check G06-TOKEN: PerformClick dispatched=true
# Compare pixel diff between pre-tap and post-tap screenshots
```

---

## Part 10: Key Files to Read First

1. **`CONSTITUTION_V2.md`** — The engineering laws (READ FIRST)
2. **`docs/S92_GRAPHICS_VERIFICATION.md`** — The verification ladder rules
3. **`miniandroid/src/dex/dalvik_engine.cpp`** — The main interpreter 
   (start at `execute_apk_with_activity` at line ~1556)
4. **`miniandroid/src/framework/android_shadows.cpp`** — The shadow layer 
   (start at `CollectionShadow::dispatch` at line ~263)
5. **`miniandroid/src/runtime/execution_engine.cpp`** — The render 
   traversal (start at `stage_render_frame`)
6. **`root_registry.json`** — 540 catalogued root causes
7. **`miniandroid/APK_REGISTRY.json`** — 22 test APKs

---

## Part 11: Common Pitfalls (Lessons Learned)

1. **Always use 1080×1920** — The layout system uses density 2.0. 
   Using 540×960 produces flat screenshots because glyphs are drawn 
   beyond the framebuffer edge.

2. **HashMap.size() must count actual entries** — The original stub 
   returned 0 always, which broke any app that checks `map.size() > 0` 
   before iterating.

3. **Class name gates must include ALL implementations** — ArrayList, 
   ArrayDeque, LinkedList, CopyOnWriteArrayList all implement List. 
   The handler's class_name check must include all of them.

4. **Shadow view objects must preserve their allocated class** — The 
   F-064 keySet view should stay HashSet, not become ArrayList. (This 
   is the A102 deep bug that remains unfixed.)

5. **onPostCreate dispatch must be in BOTH paths** — Path A (multi-DEX) 
   and Path B (single-DEX). A91 only put it in Path A, missing most apps.

6. **View.getWidth() in pre-layout Runnables** — View.post() Runnables 
   fire before the layout pass. getWidth() returns 0 unless you add a 
   fallback to measured_width or MATCH_PARENT resolution.

7. **Reproducible Proof > Successful Exit Code** — A "SUCCESS" status 
   with a flat single-color screenshot is NOT visual verification. 
   Always check pixel diversity.

8. **3-run repeatability is mandatory for FULLY_VERIFIED** — A single 
   run is never FULLY_VERIFIED (S92 §28). You need 3 byte-identical runs.

9. **Fresh Evidence > Stale Evidence** — If the binary changes, 
   re-validate all evidence. Don't carry old forensic results onto a 
   new binary.

10. **Never invent semantics** — If the AOSP contract is unknown, keep 
    it UNKNOWN. Don't guess or fabricate a classification.

---

## Part 12: Next Steps (A105+)

### A105: Fix Map.keySet view class bug
- Investigate why the heap object's class_descriptor changes from 
  HashSet to ArrayList after CollectionShadow::dispatch creates the view
- Likely a heap obj_id reuse issue or the iterator() handler at line 914 
  returning the wrong class
- This would unblock minos (MazeFactory.getUnvisitedNeighbours would 
  return non-empty Map → maze generation proceeds → GameView draws)

### A106: Fix AppCompat setContentView(int) inflation
- Trace AppCompatDelegateImpl.setContentView(resId) → ensure 
  LayoutInflater.inflate adds the inflated root as a child of 
  ContentFrameLayout
- This would unblock bullseye

### A107+: Compose Runtime Internals (WAVE 8)
- Implement SlotTable (slot management for recomposition)
- Implement Composer (the recompose loop driver)
- Implement Applier (applies composition changes to LayoutNode tree)
- Implement LayoutNode (measure/layout/draw)
- This would unblock dooz, battleship, and all Compose apps
- Multi-week effort

### A108+: WebView HTML5/JS pipeline
- Complete the WebView HTML5/Canvas rendering pipeline
- This would fully unblock blockbuster (currently renders WebView 
  chrome but not the HTML5 game canvas)

---

## Appendix A: All Screenshot Proofs

All screenshots are in:
- `/home/z/my-project/download/screenshots_v4/` — Final verification 
  screenshots (13 apps)
- `/home/z/my-project/download/screenshots_final/` — Interaction proof 
  (before/after tap pairs + INTERACTION_PROOF.png mosaic)
- `/home/z/my-project/download/repeatability/` — 3-run repeatability 
  SHA stamps

### Single-file mosaics (all renders in one file):
1. **`/home/z/my-project/download/screenshots_v4/FINAL_MOSAIC_FULLY_VERIFIED.png`**
   — 4×3 grid with verdict bands (green=FULLY, yellow=VISUAL, red=FRAME_CAPTURED)
2. **`/home/z/my-project/download/screenshots_final/INTERACTION_PROOF.png`**
   — Before/After/Diff visualization for all 7 FULLY_VERIFIED apps
3. **`/home/z/my-project/download/screenshots_v4/REPEATABILITY_PROOF.md`**
   — SHA stamps for all 7 apps (3/3 byte-identical)

---

## Appendix B: Git Commit History (Key Commits)

The runtime has 540+ registered root causes in `root_registry.json`. 
Key commits in the A1-A104 campaign:

- **A91:** onPostCreate dispatch (Path A only — partial)
- **A92:** Framebuffer resolution fix (tooling)
- **A93:** onPostCreate dispatch (Path B — complete)
- **A94:** Display.getWidth/getHeight stubs
- **A95:** View.getWidth fallback for pre-layout Runnables
- **A101:** HashMap.size() counts actual entries
- **A102:** ArrayDeque/LinkedList in ArrayList handler gate
- **A103:** 3-run repeatability verification (7 apps FULLY_VERIFIED)
- **A104:** dooz execution — Compose Navigation boundary documented

---

## End of Knowledge Transfer Document

This document captures everything needed to continue the MiniAndroid 
Compatibility Runtime verification campaign from A105 onward. Every 
patch, every bug, every boundary, every verification result is documented 
with file paths, line numbers, and reproduction steps.

**The single most important rule (Constitution V2 §1):**
> Reproducible Proof > Successful Exit Code

Never claim success without pixel-level evidence and SHA-stamped 
reproducibility.
