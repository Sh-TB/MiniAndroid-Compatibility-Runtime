# MiniAndroid STUB_DEBT Ledger

**Last updated:** 2026-08-22 (post-EXP-072 cross-app validation)
**Maintained by:** MiniAndroid agent
**Purpose:** Track every stubbed, faked, or partially-implemented behaviour that could become technical debt. Items here are NOT bugs — they are conscious simplifications. Each item should eventually be either fully implemented or formally accepted as a permanent limitation.

## EXP-072 NEW ENTRIES (cross-app validation revealed these)

### EXP-072-A: C++ framebuffer renderer is broken (PARTIAL → bypassed)

The C++ `SoftwareRenderer::perform_draw()` looks for heap objects with class name `"android.widget.TextView"` (Java format), but the heap stores objects with DEX descriptor `"Landroid/widget/TextView;"`. The lookup finds nothing, so the framebuffer remains solid grey.

Additionally, `PNGWriter::write_png()` produces a TRUNCATED PNG (4535 bytes instead of ~1.15 MB for a 480×800 RGB image). Despite this, `file` reports it as a valid PNG, and the SHA256 is deterministic.

**Impact:** All apps produced the SAME screenshot SHA256 (`c3c208a1...`) — a hardcoded stub. This was a major anti-false-positive violation caught by EXP-072.

**Status:** BYPASSED — EXP-072 introduces a Python view-tree renderer (`scripts/exp072_ocr_verify.py`) that reads `view_tree.json` and produces real PNGs. The C++ renderer is still called but its output (`screenshot.png`) is ignored in favor of the Python renderer's output (`exp072_rendered.png`).

**Action:** Either fix the C++ renderer (match DEX-format class descriptors) OR deprecate it entirely.

### EXP-072-B: Bytecode encoding bug in DEX builder (FIXED)

The `DexBuilder` in `tools/exp052_exception_tests.py` was placing the opcode in the HIGH byte of each 16-bit code unit: `(OP << 8) | operand`. But the runtime's opcode dispatch reads `op = bytecode[pc] & 0xFF` (LOW byte). This silently mis-executed bytecode.

**Impact:** EXP-052 regression tests passed DESPITE the wrong encoding because they only checked for THROW/HALT markers, not register values. This is a **false-positive regression** — tests that pass without testing the right thing.

**Status:** FIXED in EXP-072. The new builder (`scripts/exp072_build_corpus.py`) uses the correct encoding: opcode in LOW byte.

**Action:** Backport the fix to `tools/exp052_exception_tests.py` (or update the EXP-052 tests to also verify register values).

### EXP-072-C: Synthetic click campaign is Telegram-specific (STUB)

The `EXP060-CLICK` synthetic click campaign looks for views with class name containing `FragmentFloatingButton` (Telegram-specific). For non-Telegram apps, it finds 0 clickable views and reports `NO_LOGIN`.

**Impact:** Calculator's "=" button and Counter's "+1" button are NOT clicked. Input/state mutation is NOT tested in the cross-app corpus.

**Status:** OPEN. Tracked as Candidate 0 in `miniandroid/.agent/blockers.md`.

**Action:** Make the click campaign app-agnostic — find ANY view with `has_click_listener=true` in the view tree.



## Convention

Each item is classified as one of:

- **STUB** — method/opcode is a no-op (returns default value, does nothing). The call site still proceeds.
- **FAKE** — method returns a hardcoded synthetic value that mimics real behaviour but is not derived from real state.
- **PARTIAL** — method executes some real logic but skips parts (e.g., only the happy path is implemented).
- **DETECTOR** — method/loop is detected and force-stopped by the 50K-iteration loop detector.
- **PERMANENT** — accepted as a permanent limitation of the headless runtime (e.g., no real GPU).

---

## 1. Loops caught by the 50K-iteration detector (DETECTOR)

These are NOT stubbed — the runtime executes real bytecode, but a 50K-iteration limit force-stops the loop. The runtime continues past the stop.

| Method | PC | Reason | Blocker? | Notes |
|---|---|---|---|---|
| `LocaleController.getLocaleFileStrings` | 0x38 | Locale strings file not in APK | NO | Pre-existing. Does not prevent EXP-071. |
| `FragmentFloatingButton.onFactorChanged` | 0x3e | Factor animation never completes | NO | Pre-existing. Does not prevent EXP-071. |
| `AnimatedPhoneNumberEditText.setHintText` | (varies) | `DynamicAnimation.cancel()` loops | NO | Stubbed-and-captured in EXP-065. |
| `AndroidUtilities.replaceTags` | (varies) | String processing loop | NO | Stubbed. |
| `EmojiInputFilter` / `HelperInternal19` / `SkippingHelper19` / `AppCompatTextViewAutoSizeHelper` constructors | (varies) | Constructor loops | NO | Stubbed. |

**Action:** None required. The detector is doing its job. If any of these loops become blockers, they should be properly stubbed in `bridge_to_api`.

---

## 2. onHide lifecycle chain (PERMANENT — NOT STUB_DEBT)

**Status:** Verified during EXP-071 S12 PHASE 6. NOT a stub. NOT a recursion. NOT a blocker.

The 21 onHide METHOD-IN entries observed during EXP-071 final runs are NORMAL Telegram lifecycle behaviour:
- `BoolAnimator.setValue` triggers onHide as an animation callback when the page transitions.
- Each onHide returns immediately (`SlideView.onHide` has `bytecode_size=1` = `return-void`).
- The chain is finite (21 total, no recursion).

**Action:** None. This is NOT STUB_DEBT. The S12 commit's classification stands.

---

## 3. Network boundary (FAKE — controlled)

The `ConnectionsManager.sendRequest` boundary is INTENTIONALLY mocked. The mock is generic (dispatches based on the request type), not Telegram-specific. Real network I/O is NOT implemented.

| Request type | Mock response | Notes |
|---|---|---|
| `TLRPC$TL_help_getNearestDc` | `TL_nearestDc{country="US"}` | Hardcoded country. |
| `TLRPC$TL_auth_sendCode` | `TL_auth_sentCode{resp_id=3465}` | Hardcoded resp_id. |
| (any other) | null | Caller may HALT if it dereferences null. |

**Action:** Required for future apps that make other network requests. See Candidate 6 in `miniandroid/.agent/blockers.md`.

---

## 4. Layout / rendering (PARTIAL / PERMANENT)

| Area | Status | Notes |
|---|---|---|
| `View.measure(int, int)` | PARTIAL | Heuristic positioning only. No MATCH_PARENT/WRAP_CONTENT/weight/margin semantics. |
| `View.layout(int, int, int, int)` | PARTIAL | Simple vertical stack. |
| `View.draw(Canvas)` | PARTIAL | Canvas command recording is captured; rendering uses Pillow (CPU). |
| GPU / OpenGL | PERMANENT | Not supported. Headless runtime. |
| `BitmapFactory.decodeResource(int)` | STUB | Returns a 1×1 placeholder bitmap. |
| `BitmapDrawable` | STUB | Gray rectangle. |
| `VectorDrawable` (XML) | STUB | Not parsed. |
| `ColorDrawable` | PARTIAL | Solid color fills work. |
| `Resources.getColor(int)` | FAKE | Returns default black (0xFF000000). 165 color resources available but not resolved. |

**Action:** Candidate 1 (drawable decoding) and Candidate 2 (color resolution) in `miniandroid/.agent/blockers.md`.

---

## 5. JNI / native methods (STUB)

All `native` methods in the DEX are stubbed. `dlopen`/`dlsym` for `.so` files inside the APK is NOT implemented.

| Native call | Stub return | Notes |
|---|---|---|
| Any `native` method | 0 / null / void | Same as STUB. |

**Action:** Candidate 5 in `miniandroid/.agent/blockers.md`.

---

## 6. Java standard library (STUB / PARTIAL)

| Class | Status | Notes |
|---|---|---|
| `java.net.Socket` / `HttpURLConnection` | STUB | Not implemented. |
| `java.sql.*` (SQLite) | STUB | Only `SharedPreferences` is implemented. |
| `java.io.File` | PARTIAL | Basic operations only. |
| `java.lang.reflect.*` | STUB | `Class.forName` works for DEX classes; `getMethod` returns stub. |
| `java.util.HashMap` | PARTIAL | Map semantics work; no `entrySet` iteration. |
| `java.util.ArrayList` | PARTIAL | List semantics work; `Iterator` is stubbed. |

---

## 7. Code hygiene items (cleanup TBD, non-fatal)

These are merge artifacts and minor warnings. They do NOT affect runtime behaviour.

| File | Line | Issue | Severity |
|---|---|---|---|
| `dalvik_engine.h` | 1650 | `apk_path_` redeclaration warning | Low (non-fatal) |
| `android_shadows.cpp` | 475 | `ready` variable shadowing in `HandlerShadow::drain_ready` | Low (non-fatal) |

**Action:** Cleanup in a future code-hygiene commit. NOT blocking any experiment.

---

## 8. Session count discrepancy (DOCUMENTATION)

EXP-071 was planned as 12 sessions (S1–S12). The actual commit history has S1–S7 (on origin) and S10–S12 (on local). Sessions **S8 and S9 were bundled into the S10 commit** (`3702803`).

The S10 commit message documents three fixes ("THREE CRITICAL FIXES"): Per-DEX const-string (would have been S8), unzip asset path prefix (would have been S9), and try_shadow_dispatch two-pass (S10). All three fixes are recoverable as logical units via `git log -p 3702803`.

GitHub issue #7 has retroactive comments for S8 and S9 that document this consolidation. This is NOT lost work — it is documented work.

---

## 9. Run log non-determinism (PERMANENT)

`run.log` files differ across runs because they contain timestamps. This is expected and is NOT a defect. The reproducibility proof is based on the byte-identical SHA256s of `screenshot.png` and `view_tree.json`, NOT on `run.log`.

---

## Audit checklist

Before declaring any future experiment PROVEN:

- [ ] Verify the screenshot SHA256 matches across at least 3 runs.
- [ ] Verify the view_tree.json SHA256 matches across at least 3 runs.
- [ ] Verify the semantic proof (METHOD-IN entries) by `grep` on the run.log.
- [ ] Run the EXP-052 + EXP-059 + EXP-066 regression suites.
- [ ] Check no new STUB_DEBT was introduced.
- [ ] Update this ledger.
- [ ] Update `miniandroid/.agent/state.md` and `miniandroid/.agent/blockers.md`.
- [ ] Post a session comment on the relevant GitHub issue.

---
