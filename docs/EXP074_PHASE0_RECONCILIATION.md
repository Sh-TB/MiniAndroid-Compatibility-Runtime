# EXP-074 PHASE 0 — CHECKPOINT_M Reconciliation Report

**Date:** 2026-08-22
**Purpose:** Honest assessment of the EXP-071 "CHECKPOINT_M = PROVEN" claim against actual artifacts.

## Executive Summary

The EXP-071 "PROVEN" label was **PARTIALLY OVERSTATED**. The bytecode execution chain is real and reproducible, but the screenshot evidence is a **broken PNG stub** produced by the C++ framebuffer renderer. No OCR was ever run on the screenshot. The visual proof does not exist.

## Honest Classification

| Checkpoint Dimension | Status | Evidence |
|---------------------|--------|----------|
| CHECKPOINT_M_LOGIC | ✅ **PROVEN** | run.log contains real METHOD-IN entries for the full execution chain |
| CHECKPOINT_M_CALLBACK | ✅ **PROVEN** | Lambda2.run(response, null) dispatched with mock TL_auth_sentCode |
| CHECKPOINT_M_VIEW | ✅ **PROVEN** | view_tree.json has 2284 nodes, 53 SmsView nodes |
| CHECKPOINT_M_RENDER | ❌ **NOT_PROVEN** | screenshot.png is a broken PNG (invalid IDAT zlib data, PIL cannot open) |
| CHECKPOINT_M_OCR | ❌ **NOT_PROVEN** | OCR produces empty output (broken PNG). No OCR was ever run before. |
| CHECKPOINT_M_REPRODUCIBILITY | ⚠️ **PARTIAL** | Logic reproducible (3/3 same instruction counts). Visual NOT reproducible (same broken stub). |

## The Broken Screenshot

The `screenshot.png` file in all 6 EXP-071 run directories:
- **Size:** 1,152,862 bytes (looks like a real screenshot)
- **SHA256:** `c3c208a169a7dadd21b199e6e9f42d919393f5d1951762cdd5841f18fb98136a`
- **PNG structure:** Valid PNG signature + IHDR, but IDAT chunk contains `01 00 00 ff ff 00 e1 e1 e1...` (NOT valid zlib-compressed data)
- **PIL verdict:** "cannot identify image file"
- **Tesseract OCR:** empty output

This is the **same broken C++ framebuffer renderer** identified in EXP-072, which produces a truncated grey stub for EVERY app (HelloWorld, Calculator, Counter, and Telegram all produce the same SHA256).

## What IS Real

The following evidence IS real and reproducible:
1. **Bytecode execution chain** — run.log has METHOD-IN entries for every step
2. **View tree** — view_tree.json has 2284 real nodes including 53 SmsView-class nodes
3. **Semantic counts** — TL_auth_sendCode=4, fillNextCodeParams=5, LoginActivitySmsView=318 (all identical across 3 runs)
4. **onHide analysis** — 21 finite METHOD-IN entries (harmless lifecycle behavior)

## What IS NOT Real

1. **Screenshot** — broken PNG stub, not a real render of the SMS page
2. **OCR** — never run; no text was ever extracted from the screenshot
3. **Visual proof of SMS page** — the screenshot does not show the SMS page; it shows a grey rectangle

## Missing Artifacts

The following artifacts claimed in the EXP-071 report do NOT exist:
- `run/exp071/sms_view_tree.json` — NOT FOUND
- `run/exp071/login_sms.png` — NOT FOUND

## RENDERER_BACKEND Classification

```
RENDERER_BACKEND = NATIVE_FRAMEBUFFER (BROKEN)
```

The C++ `SoftwareRenderer::perform_draw()` looks for heap objects with class name `"android.widget.TextView"` (Java format), but the heap stores objects with DEX descriptor `"Landroid/widget/TextView;"`. The lookup finds nothing, so the framebuffer remains solid grey. Additionally, `PNGWriter::write_png()` produces a truncated PNG with invalid IDAT data.

The Python view-tree renderer (used in EXP-072 for synthetic apps) produces REAL PNGs that PIL can open and Tesseract can OCR. But it was never applied to the Telegram run.

## Corrective Action

1. **Retroactively apply the Python renderer to EXP-071 view trees** — render view_tree.json to a real PNG and OCR it
2. **Fix or deprecate the C++ framebuffer renderer** — it has been broken since at least EXP-061
3. **Re-run 3 Telegram runs with the Python renderer** — produce real screenshots + OCR
4. **Update CHECKPOINT_M status** — logic is PROVEN, visual is NOT YET PROVEN

## Conclusion

**CHECKPOINT_M = PARTIALLY PROVEN**

- Logic: ✅ PROVEN
- Callback: ✅ PROVEN
- View: ✅ PROVEN
- Render: ❌ NOT PROVEN (broken PNG)
- OCR: ❌ NOT PROVEN (never run)
- Reproducibility: ⚠️ PARTIAL (logic yes, visual no)

The "PROVEN" label in the EXP-071 final report was overstated. The bytecode work is real, but the visual proof does not exist. This must be corrected.
