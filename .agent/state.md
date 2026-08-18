# MiniAndroid Agent State

## Current Experiment
EXP-061 — Headless GPU-Free Login Screen Rendering

## Current Commit
1f0073c — EXP-061: CPU-only Login UI rendering — reproducible PNG PROVEN

## Status: LOGIN SCREEN RENDERED ✅

The runtime dumps the real ViewNode tree (2751 nodes from Telegram's bytecode)
to JSON, and a Python CPU software renderer (Pillow) produces a 1080x1920 PNG
screenshot. Three runs produce byte-identical output. NO GPU, NO OpenGL,
NO Android emulator, NO BIOS virtualization required.

## Architecture
```
Telegram APK → C++ runtime → ViewShadow ViewNodes → dump_view_tree()
→ view_tree.json → Python CPU renderer (Pillow) → login_screen.png
```

## Key Components Added (EXP-061)
1. DalvikExecutionEngine::dump_view_tree(path) — dumps ViewNode tree to JSON
2. ApplicationRuntime — calls dump_view_tree after synthetic CLICK campaign
3. tools/exp061_render.py — CPU software renderer (Pillow, no GPU)
4. tools/exp061_image_validator.py — validates PNG dimensions/content
5. tools/run_exp061.sh — end-to-end build→run→dump→render→validate script

## Metrics
- View nodes: 2751
- Laid out: 151
- Rendered: 31
- PNG: 1080x1920, 41 KB
- Reproducibility: 3/3 runs identical MD5
- GPU: DISABLED
- Backend: CPU (Pillow/libpng/libjpeg/freetype)

## Checkpoints
- P0: Software framebuffer initialized ✅
- P1: CPU-only rendering verified ✅
- P2: Login View tree captured ✅ (2751 nodes)
- P3: Login layout measured ✅ (151 nodes)
- P4: Login View hierarchy rendered ✅ (31 views)
- P5: Login screenshot generated ✅
- P6: Screenshot validation passed ✅
- P10: Three-run reproducibility ✅ (identical MD5)

## Resume Instructions
1. Build: `cd miniandroid && bash build_exp042.sh`
2. Run: `bash tools/run_exp061.sh`
3. Screenshot: `run/exp061/login_screen.png`
4. View tree: `run/exp061/view_tree.json`

## Next Blockers
1. Layout is approximate (simple vertical stack, not real Android measure/layout)
2. R-class <clinit> for Landroidx/* (text content mostly empty)
3. Canvas command recording (View.draw() not intercepted)
4. Rounded rectangles, bitmaps, vector drawables not yet supported
