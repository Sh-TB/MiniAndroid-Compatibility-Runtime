#!/usr/bin/env python3
"""s124_post.py — post the S124 THEME-BASE report to #354 (and #353)."""
import json
import os
import urllib.request

T = open("/tmp/.gh_token").read().strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
B = "https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s124_theme_base/"

BODY = """## S124 — THEME / TEMPLATE LOADING BASE (the original-framework law chain)

**Directive:** every app carries a theme/template structure — build the loading base on the **original framework** (research it first, from source); never label a black/white frame as "rendered"; re-test Telegram/WhatsApp load progress.

### 1. What was researched (the original framework itself, fetched from AOSP main)
- `libs/androidfw/AssetManager2.cpp` — **Theme::ApplyStyle**: a Theme is a sorted key→entry array; applying a style merges its bag through the parent chain; a normal apply never overrides an existing key, a forced apply overwrites, undefined removes. **Theme::GetAttribute**: `?attr` values hop to the attribute they name (≤20 hops). **ResolveAttributeReference**: references deref through the manager.
- `libs/androidfw/AttributeResolution.cpp` — the per-attribute priority chain, quoted from source: *"we prioritize values coming from, first XML attributes, then XML style, then default style, and finally the theme."*
- `core/res/res/values/public-final.xml` — frozen defStyleAttr ids (buttonStyle 0x01010048, textViewStyle 0x01010084, editTextStyle 0x0101006e, …), never guessed from memory.
- `libs/androidfw/include/androidfw/ResourceTypes.h` — ResTable_type SPARSE (0x01) / OFFSET16 (0x02) encodings + ResTable_sparseTypeEntry {idx, offset/4}.

### 2. What was built (generic engine, zero package checks)
- **`theme_engine.h` — a real Theme object**: apply_style(force) overlay merging, attr-hop lookups, package-routed reference deref — the AOSP Theme port.
- **ThemeOverlay law**: a view tag's `android:theme` re-themes its whole subtree (push/pop scope in the inflater).
- **View-ctor defStyleAttr tier**: 14 framework widgets now inherit their themed widget template (background / textColor / textSize / padding / textStyle) exactly at the AOSP priority slot (XML > style= > defStyleAttr > theme).
- **FW-PACKAGE router**: a real **framework-res resources.arsc** (package 0x01, Android 16 — core theme ids frozen since API 21, verified against public-final.xml) loads as the second package. App themes climbing into `Theme.Material`/`Theme.AppCompat` now resolve the REAL framework bags. Effect: dooz `Theme.Dooz` went from **0 → 355 theme keys**; the whole framework color/widget-style system is live.
- **Parser laws fixed en route** (found by parsing the real framework table): ResTable_type flags live at byte 9; SPARSE `{u16 idx, u16 offset<<2}` + OFFSET16 (`u16 offset*4`, 0xffff=NO_ENTRY) dense arrays with per-encoding hostile-table bounds; sparse `entry_index` = the sparse idx; **staged duplicate-id package chunks skipped** (framework-res = 1 real + 6 staged chunks, all id 0x01 — indexing them corrupted every resolution).

### 3. Verification (all evidence below, 460px, English-only)
- Heading Calculator: **3-run byte-identical** (a169346e), full themed render; the app's own colors resolve lawfully.
- FlappyCow: start screen **byte-identical to the S123 golden (13cf4746) ×3** — zero regression; Play tap → Game launch chain (G08) proven on the final binary.
- gmdice / unote / microtimer: coherent themed renders (the visible deltas ARE the lawful framework theme values now flowing — e.g. window backgrounds that previously fell back to a flavor-misdetected dark now use the real chain).
- notes / sudoku: **defStyleAttr tier active** (2 widget template bags applied per screen).
- Cross-check honesty: opencalculator's near-blank state is **A/B byte-identical pre/post S124** (eb16ab5c) — pre-existing SlidingUpPanelLayout idiom frontier, not a regression.

### 4. Telegram / WhatsApp load progress (honest labels — NOT claimed as renders)
- **Telegram** (48 frames): last frame = **3 grey colors — this is NOT a render**. Load depth: LaunchActivity dispatches, LocationController init completes, and Telegram's themed-icon engine (**SvgHelper** SVG parsing, ~24M+ instructions) executes — same-config parity with the pre-S124 binary (8 uncaught; the earlier 47-uncaught figure was a longer-run artifact). Frontier: themed-icon → pixel chain.
- **WhatsApp** (24 frames): last frame = **2 colors (black/white) — this is NOT a render**. Frontier unchanged and A/B-proven: AppContext.set injection + INVOKE_RETURN (app-idiom, theme-independent).
- dooz: theme base fully loaded (355 keys); the first frame is still blank — the documented Compose Recomposer frontier (R-NEW-344). No claim of visual progress.

### 5. Evidence images
1. Themed calculator (deterministic render): {B}s124_calc1_themed_render.jpg
2. FlappyCow start screen (S123 golden match ×3): {B}s124_flappy1_start_screen_golden.jpg
3. gmdice themed menu: {B}s124_gmdice1_themed_menu.jpg
4. unote menu: {B}s124_unote1_menu.jpg
5. microtimer keypad: {B}s124_microtimer1_keypad.jpg
6. notes (defStyleAttr tier active): {B}s124_notes1_defstyle.jpg
7. dooz honest blank frontier: {B}s124_dooz1_blank_frontier.jpg
8. Telegram honest grey frontier (not a render): {B}s124_telegram1_grey_frontier.jpg
9. WhatsApp honest black/white frontier (not a render): {B}s124_whatsapp1_blackwhite_frontier.jpg

Commit: 88ba2f6d (pushed to main).

---
**Standing note (per directive):** these are 460px JPG confirmation stills (≤100KB) rendered by the MiniAndroid compatibility runtime from the real APK bytecode — each frame is produced by executing the app's own DEX code and drawing the resulting view tree. A frame shown here means that screen executed and painted in the runtime; it does not mean the app is 100% identical to a physical device (fonts, animations, GPU effects and native-code paths still differ). Blank/grey/black-white frames are labeled exactly as what they are — load frontiers, not renders.
"""

for issue in (354, 353):
    body = BODY.replace("{B}", B)
    payload = json.dumps({"body": body}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
        data=payload, method="POST",
        headers={"Authorization": f"Bearer {T}", "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    print(f"posted to #{issue}: comment {r['id']}")
