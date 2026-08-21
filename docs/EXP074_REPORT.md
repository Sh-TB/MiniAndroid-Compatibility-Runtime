# EXP-074 — Runtime Integrity Reconciliation + Real SMS Frame + Cross-App Validation

**Date:** 2026-08-22
**Campaign:** Honest reconciliation of CHECKPOINT_M + real APK blocker investigation + generic fixes
**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime

---

## 1. Executive Summary

EXP-074 performed an **honest reconciliation** of the EXP-071 "CHECKPOINT_M = PROVEN" claim. The finding is significant:

**The "PROVEN" label was PARTIALLY OVERSTATED.** The bytecode execution chain is real and reproducible, but the screenshot evidence is a **broken PNG stub** produced by the C++ framebuffer renderer. No OCR was ever run on the screenshot. The visual proof of the SMS page does not exist.

### Honest CHECKPOINT_M Classification

| Dimension | Status | Evidence |
|-----------|--------|----------|
| CHECKPOINT_M_LOGIC | ✅ **PROVEN** | Full bytecode chain executes: onCreate → onConfirm → Lambda0/1 → onNextPressed → TL_auth_sendCode → sendRequest → Lambda2 → fillNextCodeParams |
| CHECKPOINT_M_CALLBACK | ✅ **PROVEN** | Lambda2.run(response, null) dispatched with mock TL_auth_sentCode |
| CHECKPOINT_M_VIEW | ✅ **PROVEN** | view_tree.json has 2284 nodes, 53 SmsView-class nodes, 6 LoginActivitySmsView instances |
| CHECKPOINT_M_RENDER | ❌ **NOT_PROVEN** | screenshot.png is a broken PNG (invalid IDAT zlib data, PIL cannot open, Tesseract produces empty OCR) |
| CHECKPOINT_M_OCR | ❌ **NOT_PROVEN** | OCR was never run. The screenshot is unreadable. |
| CHECKPOINT_M_REPRODUCIBILITY | ⚠️ **PARTIAL** | Logic is reproducible (3/3 same instruction counts). Visual is NOT reproducible (same broken stub every time). |

### The Broken Screenshot

The `screenshot.png` in ALL 6 EXP-071 run directories:
- **SHA256:** `c3c208a169a7dadd...` — identical across all runs AND identical to HelloWorld/Calculator/Counter from EXP-072
- **PNG structure:** Valid signature + IHDR, but IDAT contains `01 00 00 ff ff 00 e1 e1...` (NOT valid zlib data)
- **PIL verdict:** "cannot identify image file"
- **Tesseract OCR:** empty output
- **Root cause:** C++ `SoftwareRenderer::perform_draw()` looks for Java-format class names but the heap uses DEX descriptors. `PNGWriter::write_png()` produces truncated IDAT data.

### RENDERER_BACKEND Classification

```
RENDERER_BACKEND = NATIVE_FRAMEBUFFER (BROKEN)
```

The Python view-tree renderer (used for synthetic apps in EXP-072/073) produces REAL PNGs that PIL can open and Tesseract can OCR. But it was never applied to Telegram.

---

## 2. Phase 0 — CHECKPOINT_M Reconciliation (Complete)

### Findings

1. **No `sms_view_tree.json` artifact exists** — claimed in the EXP-071 report but never created.
2. **No `login_sms.png` artifact exists** — claimed but never created.
3. **The `screenshot.png` is a broken stub** — same SHA256 as the broken stub produced for all other apps.
4. **The view_tree.json IS real** — contains 2284 nodes with real SmsView nodes.
5. **The run.log IS real** — contains the full execution chain with METHOD-IN markers.
6. **The SmsView nodes have NO text** — the view objects were created but their text fields were never populated by `fillNextCodeParams`.

### Conclusion

The EXP-071 campaign proved the **bytecode execution chain** but did NOT prove the **visual SMS page render**. The "PROVEN" label should be corrected to "PARTIALLY PROVEN — logic proven, visual not proven."

---

## 3. Phase 1 — onHide Loop Forensics (Assessed)

### Finding

The onHide calls are **finite** (21 total across the run). They are normal Telegram lifecycle callbacks triggered by `BoolAnimator.setValue` during page transitions. Each onHide returns immediately (`SlideView.onHide` has `bytecode_size=1` = `return-void`).

The actual HALT events are:
- `LocaleController.getLocaleFileStrings (PC=0x38)` — caught by 50K-iteration loop detector
- `FragmentFloatingButton.onFactorChanged (PC=0x3e)` — caught by loop detector

**Classification:** onHide is harmless finite lifecycle behaviour. NOT a runtime bug. NOT STUB_DEBT. The runtime exits with code 0 and produces the view tree correctly.

The `FireworksOverlay.<clinit>` mentioned by the user is likely a static initializer that runs during class loading but does not prevent the runtime from completing.

---

## 4. Phase 8 — Real APK setText(int) Blocker (Investigated + Partially Fixed)

### Root Cause Investigation

Real APKs fail because of a chain of missing capabilities:

1. `setContentView(int layoutResId)` → **NO-OP** in ActivityShadow (only handles View arg, not int arg)
2. `findViewById(int viewId)` → **returns null** because no layout was inflated
3. `setText(int stringResId)` → **returns empty string** because the int was not resolved to a string

### Fixes Implemented

1. **`setText(int)` capture** — ViewShadow now captures `text_resource_id` when `setText(int)` is called. The Python renderer can resolve it via the ARSC parser.
2. **`setContentView(int)` capture** — ActivityShadow now captures `layout_resource_id_` when `setContentView(int)` is called. The layout is not yet inflated but the resource ID is recorded for diagnostics.

### Why the Fix Didn't Enable Real APKs

The real blocker is **XML layout inflation**. Real APKs call `setContentView(R.layout.main)` which requires:
1. Parsing the AXML binary XML from `res/layout/*.xml` in the APK
2. Creating View objects from the XML elements
3. Resolving view IDs from the ARSC resource table
4. Wiring `findViewById` to return the created views

This is a significant feature that requires C++ AXML parsing or a Python post-processor. The AXML parser exists (`tools/exp067_axml_parser.py`) but is Python-only.

### Blocker Classification

| Blocker | Classification | Status |
|--------|---------------|--------|
| `setText(int stringResId)` | GENERIC | ✅ Captured (Python resolver available) |
| `setContentView(int layoutResId)` | GENERIC | ⚠️ Captured but not inflated |
| `findViewById(int viewId)` | GENERIC | ❌ Returns null (no views created) |
| XML layout inflation | GENERIC | ❌ NOT IMPLEMENTED (highest priority) |

---

## 5. Phase 9 — App-Agnostic Click Dispatch (Verified)

The existing `find_all_with_click_listener` campaign is already app-agnostic — it searches for ANY view with `has_click_listener=true`, not just Telegram's `FragmentFloatingButton`.

**Proven in EXP-073:** CounterV2's `setOnClickListener(this)` + `onClick(View)` was successfully dispatched through the generic click campaign, proving state mutation ("Count: 0" → "Clicked!").

No changes needed for Phase 9 — the generic click dispatch is already working.

---

## 6. Compatibility Matrix (Honest)

### Synthetic Corpus (11 apps)

| App | Exec | Render | OCR | State Mutation | Status |
|-----|------|--------|-----|----------------|--------|
| HelloWorld | ✅ | ✅ | ✅ | N/A | PROVEN |
| Calculator | ✅ | ✅ | ✅ | N/A | PROVEN |
| Counter | ✅ | ✅ | ✅ | N/A | PROVEN |
| CounterV2 | ✅ | ✅ | ✅ | ✅ | PROVEN |
| Notes | ✅ | ✅ | ✅ | N/A | PROVEN |
| UnitConverter | ✅ | ✅ | ✅ | N/A | PROVEN |
| TicTacToe | ✅ | ✅ | ✅ | N/A | PROVEN |
| MemoryGame | ✅ | ✅ | ✅ | N/A | PROVEN |
| Timer | ✅ | ✅ | ✅ | N/A | PROVEN |
| SimpleList | ✅ | ✅ | ✅ | N/A | PROVEN |
| Settings | ✅ | ✅ | ✅ | N/A | PROVEN |

### Real APK Corpus (5 apps from F-Droid)

| App | Exec | Render | OCR | Blocker | Execution Depth |
|-----|------|--------|-----|---------|-----------------|
| gmdice | ✅ | ❌ | ❌ | setContentView(int) not inflated | ~10% (onCreate runs, no views created) |
| simplestopwatch | ✅ | ❌ | ❌ | Same | ~15% |
| notes | ✅ | ❌ | ❌ | Same | ~70% (802K instructions, 129 view nodes but no text) |
| headingcalculator | ✅ | ❌ | ❌ | Same | ~5% |
| chessclock | ❌ | ❌ | ❌ | onCreate not reached | 0% |

### Telegram

| Checkpoint | Status |
|-----------|--------|
| LOGIC | ✅ PROVEN |
| CALLBACK | ✅ PROVEN |
| VIEW | ✅ PROVEN |
| RENDER | ❌ NOT_PROVEN (broken PNG) |
| OCR | ❌ NOT_PROVEN (never run) |
| REPRODUCIBILITY | ⚠️ PARTIAL |

---

## 7. Regression Status

- **EXP-052:** 6/6 PASS ✅
- **EXP-059:** 4/4 PASS ✅
- **EXP-066:** 4/4 PASS ✅
- **Synthetic corpus:** 11/11 SEMANTICALLY VERIFIED ✅ (no regression from setText(int) change)
- **Telegram logic:** Still executes the full chain ✅

---

## 8. Remaining Blockers (Priority Order)

### 1. XML Layout Inflation (GENERIC — HIGHEST PRIORITY)

`setContentView(R.layout.main)` needs to:
1. Parse AXML from APK
2. Create View hierarchy from XML elements
3. Wire `findViewById` to return created views

This is THE blocker preventing all real APKs from working. It's completely generic.

### 2. C++ Framebuffer Renderer Fix (GENERIC — HIGH PRIORITY)

The C++ `save_screenshot()` produces broken PNGs. Either fix the renderer or deprecate it in favor of the Python view-tree renderer.

### 3. Text Resource ID Resolution (GENERIC — MEDIUM PRIORITY)

The `setText(int)` capture is implemented but the Python ARSC resolver needs to be wired into the renderer pipeline. The ARSC parser exists but only finds global string pool entries, not per-package string resources.

### 4. SmsView Text Population (TELEGRAM-SPECIFIC — LOW PRIORITY)

The SmsView nodes exist but have no text. `fillNextCodeParams` was called but didn't set visible text on the SmsView's child TextViews. This is a Telegram-specific issue, not a generic blocker.

---

## 9. Next Steps

1. **Implement XML layout inflation** — the single highest-value generic fix. Wire `setContentView(int)` to parse AXML and create views.
2. **Fix the C++ framebuffer renderer** — or officially deprecate it and always use the Python renderer.
3. **Wire ARSC string resolution** — connect the Python ARSC parser to the view-tree renderer.
4. **Re-run Telegram with Python renderer** — produce a REAL screenshot and OCR it.
5. **Windows release** — build a minimal Windows executable.
6. **README update** — honestly reflect current capabilities.
