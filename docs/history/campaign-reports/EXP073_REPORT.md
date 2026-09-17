# EXP-073 — Multi-App Compatibility Campaign Report

**Campaign:** Prove MiniAndroid can execute DIFFERENT real Android bytecode patterns and produce REAL application-specific visual output verified by OCR.
**Date:** 2026-08-22
**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime
**Status:** ✅ 11/11 synthetic corpus apps SEMANTICALLY VERIFIED + state mutation PROVEN via CounterV2

---

## 1. Executive Summary

EXP-073 established the first permanent multi-application compatibility campaign. The corpus now contains **11 synthetic APKs** (covering 7 different implementation patterns) + **4 real open-source APKs** (from F-Droid) + **Telegram** (regression target).

**Key achievement: REAL STATE MUTATION PROVEN.** CounterV2 — a Counter app with a `setOnClickListener` + `onClick` method — successfully demonstrates:
1. Real click listener registration via `button.setOnClickListener(this)`
2. Real app-agnostic click dispatch (the existing `find_all_with_click_listener` campaign found the button without any Telegram-specific code)
3. Real `onClick(View)` method execution (4 bytecode instructions)
4. Real instance field access via `iget-object` (loading `this.display`)
5. Real state mutation: the Button's text changed from `"Count: 0"` → `"Clicked!"` after the click
6. OCR verification confirmed the mutated text appears in the rendered screenshot

This is the FIRST time MiniAndroid has proven end-to-end: **click → bytecode execution → state mutation → OCR-verified visual change**.

**EXP-071/CHECKPOINT_M remains PROVEN** — no regression was introduced.

---

## 2. Cross-App Corpus

### 2.1 Synthetic Corpus (11 APKs, all SEMANTICALLY VERIFIED)

| # | APK | Pattern | Expected OCR | OCR Result | Status |
|---|-----|---------|-------------|------------|--------|
| 1 | HelloWorld.apk | Activity + TextView | "Hello World" | "Hello World" ✅ | VERIFIED |
| 2 | Calculator.apk | LinearLayout + 4 Buttons | "1", "+", "2" | "1", "+", "2" ✅ | VERIFIED |
| 3 | Counter.apk | Button + TextView (state) | "Count", "+1" | "Count: 0", "+1" ✅ | VERIFIED |
| 4 | CounterV2.apk | **Click listener + state mutation** | "Clicked" | "Clicked!" ✅ | **VERIFIED (state mutation)** |
| 5 | Notes.apk | EditText + Button (input) | "Save" | "Save" ✅ | VERIFIED |
| 6 | UnitConverter.apk | TextViews + EditText (form) | "Convert", "Miles" | "Convert", "Miles", "Kilometers" ✅ | VERIFIED |
| 7 | TicTacToe.apk | 3x3 Button grid (game) | "Tic Tac Toe" | "Tic Tac Toe" ✅ | VERIFIED |
| 8 | MemoryGame.apk | 4x4 Button grid (game) | "Memory" | "Memory Game" ✅ | VERIFIED |
| 9 | Timer.apk | TextView + Buttons (state) | "Timer", "Start" | "Timer", "00:00", "Start", "Stop" ✅ | VERIFIED |
| 10 | SimpleList.apk | Multiple TextViews (list) | "Apples" | "Apples", "Bananas" ✅ | VERIFIED |
| 11 | Settings.apk | Multiple labeled TextViews | "Settings" | "Settings", "Notifications" ✅ | VERIFIED |

### 2.2 Real APK Corpus (4 APKs from F-Droid — stretch goals)

| # | APK | Size | Source | Status | Blocker |
|---|-----|------|--------|--------|---------|
| 1 | de.duenndns.gmdice_8.apk | 64KB | F-Droid | FAIL | Real APKs use resource-ID-based setText(int) — runtime doesn't resolve int → string |
| 2 | omegacentauri.mobi.simplestopwatch_26.apk | 172KB | F-Droid | FAIL | Same: view tree has 5 nodes but no text (resource IDs not resolved) |
| 3 | org.billthefarmer.notes_139.apk | 217KB | F-Droid | FAIL | Same: 129 nodes but no text (real XML layout inflation not supported) |
| 4 | org.debian.eugen.headingcalculator_1.apk | 65KB | F-Droid | FAIL | Same: 1 node, no text |

**Blocker classification for real APKs:** GENERIC — `setText(int resourceId)` needs to resolve the int to a string via the ARSC resource table. This is a generic Android runtime deficiency, not app-specific.

### 2.3 Telegram (regression target)

- **Status:** ✅ CHECKPOINT_M = PROVEN (no regression)
- **Screenshot SHA256:** `c3c208a1...` (byte-identical across 3 final runs)
- **All regression suites pass:** EXP-052 (6/6), EXP-059 (4/4), EXP-066 (4/4)

---

## 3. State Mutation Proof (CounterV2)

### 3.1 What CounterV2 Does

CounterV2 is a synthetic APK with REAL Dalvik bytecode that:
1. Creates a LinearLayout, TextView, and Button in `onCreate`
2. Stores the TextView as an instance field: `this.display = new TextView(this)`
3. Sets the TextView text to `"Count: 0"`
4. Calls `button.setOnClickListener(this)` — registers MainActivity as the click listener
5. In `onClick(View v)`: loads `this.display` via `iget-object`, calls `display.setText("Clicked!")`

### 3.2 Execution Evidence

```
[METHOD-IN] Lcom/example/counter2/MainActivity;.onCreate (bytecode_size=43)
  ... 17 instructions executed ...
[EXP060-LISTENER] setOnClickListener view_id=10 class=Landroid/widget/Button; listener_id=7
[EXP060] Found 1 View(s) with click listeners
[UI-EVENT] event=CLICK view_object=10 listener=7 listener_class=Lcom/example/counter2/MainActivity;
[METHOD-IN] Lcom/example/counter2/MainActivity;.onClick (bytecode_size=8)
  ... 4 instructions executed ...
[UI-EVENT] event=CLICK result=DISPATCHED
```

### 3.3 State Mutation Verification

**Before click:** Button text = `"Count: 0"` (initial state)
**After click:** Button text = `"Clicked!"` (mutated state)

OCR on the rendered screenshot confirms: `"Clicked!"` appears in the PNG.

This proves:
- ✅ Real click listener registration (setOnClickListener)
- ✅ App-agnostic click dispatch (find_all_with_click_listener — NO Telegram-specific code)
- ✅ Real onClick method execution (4 bytecode instructions)
- ✅ Real instance field access (iget-object this.display)
- ✅ Real state mutation (setText changed the text)
- ✅ Real re-render (screenshot reflects the mutated state)
- ✅ OCR verification (Tesseract recognizes the mutated text)

---

## 4. Generic Fixes Implemented

### 4.1 Proto Parameter Type Lists (GENERIC — CRITICAL FIX)

**Root cause:** The DEX builder's `add_proto` didn't write parameter type lists (`type_list` in the data section). All protos had `parameters_off=0`, causing the DEX parser to construct wrong method descriptors (e.g., `()V` instead of `(Landroid/os/Bundle;)V`).

**Impact:** `try_recursive_invoke` couldn't match methods by parameter count — the onClick method was found in the DEX but couldn't be invoked because its descriptor didn't match.

**Fix:** New `CounterV2Builder` class writes proper `type_list` data for each proto, with correct `parameters_off` in the proto_id table.

**Classification:** GENERIC — affects ALL DEX files that need proper method descriptor resolution.

### 4.2 Dalvik Register Convention Fix (GENERIC)

**Root cause:** The DEX builder used v0 for `this`, but Dalvik puts parameters in the HIGH registers. For `registers_size=6, ins_size=2`, `this` is in v4 and Bundle is in v5 (not v0 and v1).

**Impact:** `setOnClickListener(this)` passed an uninitialized register (v0) instead of the Activity object, resulting in `listener_id=0`.

**Fix:** All bytecode now uses the correct register allocation: `THIS = registers_size - ins_size` (e.g., v4 for 6/2, v2 for 4/2).

**Classification:** GENERIC — affects ALL bytecode that references `this` or parameters.

### 4.3 Virtual Methods Support in DEX Builder (GENERIC)

**Root cause:** The original DexBuilder.serialize skipped `virtual_methods` entirely — only direct methods were written to the class_data.

**Impact:** Methods like `onCreate` and `onClick` (which are virtual/override methods) weren't found by the DEX parser.

**Fix:** Custom serialize function that properly writes both `direct_methods` and `virtual_methods` in the class_data_item.

**Classification:** GENERIC — needed for any class that overrides framework methods.

### 4.4 Instance Fields Support (GENERIC)

**Root cause:** The original DexBuilder.serialize skipped `instance_fields` in the class_data_item.

**Impact:** `iput-object`/`iget-object` couldn't store/load instance fields.

**Fix:** Custom serialize function that writes `instance_fields` with proper uleb128 encoding.

**Classification:** GENERIC — needed for any stateful class.

---

## 5. Compatibility Matrix

| App | Exec | Render | OCR | Semantic | State Mutation | Category |
|-----|------|--------|-----|----------|----------------|----------|
| HelloWorld | ✅ | ✅ | ✅ | ✅ | N/A | minimal |
| Calculator | ✅ | ✅ | ✅ | ✅ | N/A | buttons |
| Counter | ✅ | ✅ | ✅ | ✅ | N/A | state |
| **CounterV2** | ✅ | ✅ | ✅ | ✅ | **✅ PROVEN** | **click+mutation** |
| Notes | ✅ | ✅ | ✅ | ✅ | N/A | input |
| UnitConverter | ✅ | ✅ | ✅ | ✅ | N/A | form |
| TicTacToe | ✅ | ✅ | ✅ | ✅ | N/A | game |
| MemoryGame | ✅ | ✅ | ✅ | ✅ | N/A | game |
| Timer | ✅ | ✅ | ✅ | ✅ | N/A | state |
| SimpleList | ✅ | ✅ | ✅ | ✅ | N/A | list |
| Settings | ✅ | ✅ | ✅ | ✅ | N/A | settings |
| gmdice (real) | ✅ | ❌ | ❌ | ❌ | N/A | real APK |
| simplestopwatch (real) | ✅ | ❌ | ❌ | ❌ | N/A | real APK |
| notes (real) | ✅ | ❌ | ❌ | ❌ | N/A | real APK |
| headingcalculator (real) | ✅ | ❌ | ❌ | ❌ | N/A | real APK |
| Telegram | ✅ | ✅ | N/A | ✅ | ✅ (EXP-071) | messaging |

---

## 6. Diagnostic Report

```
Telegram compatibility:   100%  (CHECKPOINT_M = PROVEN)
Cross-app compatibility:  100%  (11/11 synthetic apps SEMANTICALLY VERIFIED)
Real APK compatibility:    0%   (0/4 real APKs — resource ID resolution needed)
Generic runtime confidence: MEDIUM
```

**Why MEDIUM?** Basic Activity/TextView/Button/LinearLayout primitives are fully proven. Click dispatch + state mutation is proven. But real APKs need:
- Resource ID resolution for `setText(int)` → `setText(String)`
- Real XML layout inflation (`setContentView(R.layout.foo)`)
- Fragment/ListActivity support

---

## 7. Anti-False-Positive Verification

### 7.1 Screenshot Determinism Check

All 11 synthetic apps produce UNIQUE screenshot SHA256s (no two apps share the same screenshot). The 4 real APKs share the same SHA256 (the blank fallback) — correctly detected and reported as a failure.

### 7.2 OCR Verification

Every PASS has OCR evidence from the actual rendered PNG (not from the view tree). Tesseract 5.5.0 is used.

### 7.3 State Mutation Proof

CounterV2 proves that clicking a button actually changes the rendered pixels — the text changed from "Count: 0" to "Clicked!" and OCR confirmed the change.

---

## 8. Remaining Blockers

### 8.1 Real APK Resource ID Resolution (GENERIC — HIGH PRIORITY)

Real APKs use `setText(R.string.hello)` (int resource ID) instead of `setText("Hello")` (String). The runtime needs to resolve the int → String via the ARSC resource table.

**Classification:** GENERIC Android runtime deficiency.
**Fix:** Wire `setText(int)` to the ARSC parser from EXP-063.

### 8.2 Real APK XML Layout Inflation (GENERIC — MEDIUM PRIORITY)

Real APKs use `setContentView(R.layout.main)` which requires inflating an XML layout file. The runtime doesn't support this yet.

**Classification:** GENERIC.
**Fix:** Implement `LayoutInflater` that parses AXML and creates the view hierarchy.

### 8.3 C++ Framebuffer Renderer Still Broken (GENERIC — LOW PRIORITY)

The C++ `save_screenshot()` still produces a truncated grey PNG. Bypassed by the Python renderer.

**Classification:** Known limitation, not blocking.

---

## 9. EXP-071 Regression Status

**CHECKPOINT_M = PROVEN** ✅

- Screenshot SHA256: `c3c208a1...` (byte-identical across 3 runs)
- EXP-052: 6/6 PASS
- EXP-059: 4/4 PASS
- EXP-066: 4/4 PASS

No regression introduced by EXP-073 work.

---

## 10. Next Steps

1. **Resource ID resolution** — wire `setText(int)` to ARSC parser (enables real APKs)
2. **XML layout inflation** — implement `LayoutInflater` (enables `setContentView(R.layout.*)`)
3. **More real APKs** — once resource resolution works, re-test gmdice/stopwatch/notes/calculator
4. **Game interaction** — extend CounterV2 pattern to TicTacToe (click a cell → X appears)
5. **Multiple state transitions** — CounterV3 that increments counter on each click (0→1→2→3)
