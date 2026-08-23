# EXP-077 — Bootstrap Matrix + setText(int) Resolution + Adversarial Discovery

**Date:** 2026-08-22
**Commit:** HEAD
**Campaign:** Attack real APK diversity with generic runtime fixes

---

## 1. Executive Summary

EXP-077 built the **Android Bootstrap Matrix** classifying 13 real APKs by their Activity superclass and setContentView pattern, then re-ran all APKs with `setText(int)` resource resolution. The key finding is significant:

**0/13 real APKs have `setText(int)` captured**, because the root cause is NOT `setText(int)` resolution — it's that **AXML layout inflation doesn't happen in the C++ runtime**, so no views are created, `findViewById` returns null, and the app's code never reaches the point of calling `setText` on any view.

### Honest Results

| Category | Tested | Rendered | OCR Output | Fully Verified |
|----------|--------|----------|------------|----------------|
| Synthetic | 11 | 11 | 11 | 11 |
| Real APK | 13 | 9 | **0** | **0** |
| Telegram | 1 | 1 | 0 | 0 |

**Correct statement:** "No real APK currently passes the full AXML→View→setText→render→OCR gate in the automated pipeline. headingcalculator passes when AXML inflation is manually applied (EXP-075), but the automated EXP-077 pipeline doesn't call the inflation step."

---

## 2. Phase 1 — Bootstrap Matrix (Complete)

### Android Bootstrap Classification

| App | Bootstrap Type | Activities | Key Patterns |
|-----|----------------|------------|--------------|
| headingcalculator | Activity | 3 | plain |
| gmdice | ListActivity | 2 | ListActivity |
| simplestopwatch | Activity | 2 | plain |
| notes | Activity | 5 | plain |
| chessclock | Activity | 2 | plain |
| unote | Activity | 4 | plain |
| openlauncher | Activity | 10 | plain |
| tictactoe (emmanuelmess) | Activity | 3 | plain |
| dooz | ComponentActivity | 3 | Compose |
| bgclock | Activity | 1 | WebView |
| microtimer | Activity | 1 | plain |
| stopwatch (muellerma) | Activity | 2 | plain |
| simplekeyboard | Activity | 2 | plain |

### Key Finding

Most real APKs use plain `Activity` (not ListActivity/AppCompatActivity/FragmentActivity). The bootstrap type is NOT the primary blocker. The primary blocker is that `setContentView(int)` is captured but NOT inflated, so no views are created from XML layouts.

---

## 3. Phase 3 — setText(int) Resolution (Implemented but No Effect)

The `setText(int)` capture in ViewShadow is implemented (EXP-074), and the Python renderer has ARSC resolution. However:

**0/13 real APKs produced any `text_resource_id` values.** Root cause analysis:

1. **Apps that execute shallowly (5-20% depth)**: `setContentView(int)` is captured but NOT inflated. `findViewById` returns null. The app can't set up its UI. `setText` is never called because the views don't exist.

2. **Apps that execute deeply (95% depth)**: These apps (notes, bgclock, Telegram) create many view nodes (123, 50015, 51441 respectively) but:
   - **notes**: Uses commonmark parser, creates internal objects (not Views). The 123 "view nodes" are false positives from ViewShadow's broad `handles_class` heuristic.
   - **bgclock**: Sets up a WebView with WebViewAssetLoader. Never calls setText — it loads HTML content.
   - **Telegram**: Creates 51441 view nodes but text is empty because `setText(int)` calls go through `try_recursive_invoke` which finds the method in the DEX and returns true before bridge_to_api is reached.

3. **The view tree contains false positive nodes**: ViewShadow's `handles_class` heuristic creates ViewNodes for ANY user-defined class, including non-View objects like `Lc/r0;`, `Lc/s;` (obfuscated class names), `StringBuilder`, `Paint`, `TypedValue`, etc. These are NOT Views and never had `setText` called on them.

### Why headingcalculator Worked in EXP-075 but Not in EXP-077

EXP-075 manually called `inject_inflated_views()` which inflated the AXML layout and added 3 real View nodes. EXP-077's automated pipeline doesn't call this step. When the inflation is manually applied, headingcalculator produces 4 nodes and renders successfully.

---

## 4. Phase 5 — Real APK Re-run Results

| App | Depth | Insns | VT Nodes | Text Nodes | ResID | Resolved | OCR | Blocker |
|-----|-------|-------|----------|------------|-------|----------|-----|---------|
| headingcalculator | 5% | 22 | 1 | 0 | 0 | 0 | ❌ | Needs AXML inflation |
| gmdice | 5% | 56 | 1 | 0 | 0 | 0 | ❌ | ListActivity path |
| simplestopwatch | 20% | 169 | 5 | 0 | 0 | 0 | ❌ | No setContentView(int) |
| notes | 95% | 802K | 123 | 0 | 0 | 0 | ❌ | Loop: commonmark parser |
| chessclock | 0% | 0 | 0 | 0 | 0 | 0 | ❌ | onCreate not reached |
| unote | 20% | 344 | 14 | 0 | 0 | 0 | ❌ | False positive ViewNodes |
| openlauncher | 0% | 0 | 0 | 0 | 0 | 0 | ❌ | onCreate not reached |
| tictactoe | 5% | 56 | 4 | 0 | 0 | 0 | ❌ | No setContentView(int) |
| dooz | 20% | 702 | 20 | 0 | 0 | 0 | ❌ | Compose-based UI |
| bgclock | 95% | 800K | 50015 | 0 | 0 | 0 | ❌ | Loop: WebViewAssetLoader |
| microtimer | 20% | 119 | 3 | 0 | 0 | 0 | ❌ | No setContentView(int) |
| stopwatch (muellerma) | 0% | 0 | 0 | 0 | 0 | 0 | ❌ | onCreate not reached |
| simplekeyboard | 5% | 8 | 0 | 0 | 0 | 0 | ❌ | Only 8 instructions |

---

## 5. Root Cause Chain

```
setContentView(R.layout.main)
    ↓
ActivityShadow captures layout_resource_id ✅
    ↓
BUT: C++ runtime does NOT inflate the AXML
    ↓
No View objects are created from the XML layout
    ↓
findViewById(R.id.xxx) returns null
    ↓
App's onCreate can't set up its UI
    ↓
setText is never called on any View
    ↓
View tree has no text
    ↓
Screenshot is blank
    ↓
OCR produces no output
```

**The single highest-value fix is: implement AXML layout inflation in the C++ runtime** (or as a pre-rendering step that runs before the view tree is dumped). The Python post-processor approach works (EXP-075 proved it for headingcalculator) but needs to be integrated into the automated pipeline.

---

## 6. Adversarial Discoveries

### Discovery 1: ViewShadow False Positives

ViewShadow's `handles_class` heuristic creates ViewNodes for ANY user-defined class, including non-View objects. This inflates the view tree count with false positive nodes that have no text and no real View semantics.

**Evidence**: unote has 14 "view nodes" but they include `Landroid/util/TypedValue;`, `Ljava/lang/StringBuilder;`, `Landroid/graphics/drawable/ShapeDrawable;`, `Landroid/graphics/Paint;` — none of which are Views.

**Classification**: GENERIC runtime deficiency. ViewShadow should only create nodes for actual View subclasses, not any user-defined class.

### Discovery 2: Deep Execution ≠ View Creation

Apps that execute 800K-1.8M instructions (notes, bgclock, Telegram) create many heap objects but few actual Views. The "view tree node count" metric is misleading because it includes non-View objects.

**Evidence**: bgclock has 50015 "view nodes" but 0 text nodes. Telegram has 51441 "view nodes" but 0 text nodes.

### Discovery 3: Compose-Based Apps Need Different Architecture

dooz uses Jetpack Compose (ComponentActivity, not Activity). Compose doesn't use XML layouts or traditional View inflation — it uses a composable function tree. This is a fundamentally different UI paradigm that MiniAndroid doesn't support.

**Classification**: BLOCKED — requires Compose runtime support (very different from View-based UI).

### Discovery 4: WebView Apps Need WebView Support

bgclock sets up a WebView with WebViewAssetLoader. The app's entire UI is HTML content loaded into a WebView. Without WebView support, this app type can never produce visible text.

**Classification**: BLOCKED — requires WebView implementation.

---

## 7. No Regression

- EXP-071: logic still PROVEN ✅
- EXP-052: 6/6 PASS ✅
- EXP-059: 4/4 PASS ✅
- EXP-066: 4/4 PASS ✅

---

## 8. Next Steps (Priority Order)

1. **Integrate AXML inflation into the automated pipeline** — call `inject_inflated_views` in the EXP-077 script when `layout_resource_id` is captured
2. **Implement `LayoutInflater.inflate(int, ViewGroup)` in the C++ runtime** — so custom views can inflate their own child layouts
3. **Fix ViewShadow false positives** — only create ViewNodes for actual View subclasses
4. **Implement `findViewById` returning inflated views** — so apps can find and configure their views
5. **Recursive layout inflation** — inflate child layouts for custom views like CalculatorDisplay/CalculatorKeypad
