# MiniAndroid — Headless Android APK Execution Runtime

**Version:** 0.3.0-exp080
**Date:** 2026-08-22
**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime
**License:** MIT

## What is MiniAndroid?

MiniAndroid is a **headless Android APK execution runtime** built from scratch in C++. It parses real APK files, executes real Dalvik (DEX) bytecode, and produces view trees + screenshots — **without an Android emulator, without a JVM, without GPU/OpenGL, and without BIOS virtualization**.

## Why is it different from a traditional Android emulator?

| Feature | Android Emulator | MiniAndroid |
|---------|-----------------|-------------|
| Runs real Android OS | ✅ Yes | ❌ No |
| Runs real DEX bytecode | ✅ Yes | ✅ Yes |
| Requires JVM/ART | ✅ Yes | ❌ No (C++ DEX interpreter) |
| Requires GPU | ✅ Yes | ❌ No (CPU software rendering) |
| Requires KVM/HAXM | ✅ Yes | ❌ No |
| Produces screenshots | ✅ GPU framebuffer | ⚠️ Python view-tree renderer (C++ framebuffer broken) |
| Multi-DEX APK support | ✅ Yes | ✅ Yes |
| Deterministic | ❌ No | ✅ Yes |
| Direct object visibility | ❌ No | ✅ Yes (heap inspection) |
| AI-agent interaction | ❌ No | ✅ Yes (click/text dispatch) |
| Speed | Slow (boot) | Fast (<1s per APK) |

**A capability is not considered proven from a screenshot alone.**

## Current Proven Capabilities

| Capability | Status | Evidence |
|-----------|--------|----------|
| APK parsing | PROVEN | Real Telegram APK (83MB, 5 DEX) |
| DEX bytecode execution | PROVEN | 7.2M instructions in Telegram run |
| Multi-DEX support | PROVEN | Per-DEX const-string/type/method resolution |
| Activity lifecycle | PROVEN | Real onCreate bytecode executes |
| View hierarchy | PROVEN | 3077 view nodes from Telegram |
| Click dispatch | PROVEN | App-agnostic find_all_with_click_listener |
| State mutation | PROVEN | CounterV2: "Count: 0" → "Clicked!" |
| Controlled network | PROVEN | sendRequest intercepted, mock response |
| Async Runnable scheduling | PROVEN | Lambda0/1/2 chain executes |
| SharedPreferences | PARTIAL | Saves to disk, isolation untested |
| Synthetic corpus | PROVEN | 11/11 OCR-verified |
| D8 lambda dispatch | PROVEN | $r8$lambda methods match and execute |

## Partial Capabilities

| Capability | Status | Details |
|-----------|--------|---------|
| Telegram SMS page | PARTIAL | LoginActivity created, SmsView exists but no text |
| Real APK rendering | PARTIAL | headingcalculator: AXML inflated, but child views have no text |
| Windows runner | PARTIAL | Python diagnostic tool works, no native .exe |
| Sandbox persistence | PARTIAL | SharedPreferences persists, isolation untested |

## Blocked Capabilities

| Capability | Blocker |
|-----------|---------|
| Valid PNG from C++ renderer | Broken IDAT zlib encoding |
| Real APK text rendering | setContentView(int) → AXML inflation not integrated in C++ runtime |
| onNextPressed override dispatch | BaseFragment stub shadows LoginActivity override |
| SQLite | Not implemented |
| WebView | Not implemented |
| JNI/native methods | All stubbed |
| Jetpack Compose | Different architecture (no View hierarchy) |
| Native Windows .exe | No cross-compiler available |

## Synthetic Corpus (11/11 PROVEN)

All synthetic APKs pass the full EXECUTE → RENDER → OCR gate:
HelloWorld, Calculator, Counter, CounterV2 (state mutation), Notes, UnitConverter, TicTacToe, MemoryGame, Timer, SimpleList, Settings.

## Real APK Results

| App | Source | Depth | Nodes | Text | OCR | Status |
|-----|--------|-------|-------|------|-----|--------|
| headingcalculator | F-Droid | 5% | 4 | 0 | FAIL | AXML inflated, no child text |
| gmdice | F-Droid | 5% | 1 | 0 | FAIL | ListActivity path |
| simplestopwatch | F-Droid | 20% | 5 | 0 | FAIL | No setContentView(int) |
| notes | F-Droid | 95% | 123 | 0 | FAIL | Loop: commonmark |
| chessclock | F-Droid | 0% | 0 | 0 | FAIL | onCreate not reached |
| tictactoe | F-Droid | 5% | 3 | 0 | FAIL | Uses libGDX framework |
| unote | F-Droid | 20% | 9 | 0 | FAIL | Obfuscated classes |
| dooz | F-Droid | 20% | 20 | 0 | FAIL | Jetpack Compose |
| bgclock | F-Droid | 95% | 50K | 0 | FAIL | Loop: WebViewAssetLoader |

## Tic-Tac-Toe / Game Testing

**Status:** BLOCKED

- `com.emmanuelmess.tictactoe` uses libGDX (game framework, not standard Android Views)
- frame_000.png saved (blank — no board rendered)
- No clickable views, no text content

## Images

**Status:** NOT PROVEN

- BitmapFactory.decodeResource: STUBBED (returns placeholder)
- No PNG/JPEG/GIF decoding implemented

## Network/Web

**Status:** NOT PROVEN

- Controlled network boundary exists (sendRequest intercepted)
- No WebView support
- No HTTP/socket implementation

## SQLite

**Status:** NOT IMPLEMENTED

- No SQLite/OpenDatabase/CREATE TABLE support in the runtime

## Sandbox

**Status:** PARTIAL

- SharedPreferences: PROVEN (saves to `runtime/data/<package>/shared_prefs/`)
- File I/O: NOT TESTED
- App isolation: NOT TESTED (hardcoded package name)
- Path traversal: NOT TESTED

## Windows

**Status:** PARTIAL

- `tools/miniandroid_windows_runner.py`: Python-based diagnostic tool
- Produces `miniandroid_diagnostic.zip` with all evidence
- Tested on Linux (works)
- **No native .exe** — requires Python runtime
- Cross-compilation not available (no mingw)

## How to Run

### Prerequisites
- Linux x86_64
- g++ with C++17
- Python 3 with PIL/Pillow (for rendering)
- Tesseract OCR (for text verification)

### Build
```bash
cd miniandroid
bash build_exp042.sh
```

### Run an APK
```bash
./build_exp042/miniandroid_exp042 <apk_path> <output_dir>
```

### Windows Diagnostic Tool
```bash
python tools/miniandroid_windows_runner.py <apk_path> <output_dir>
```

## How to Report a Failure

1. Run: `python tools/miniandroid_windows_runner.py <apk> output`
2. Check `output/miniandroid_diagnostic.zip`
3. Upload the ZIP to the issue tracker

## Releases

**No GitHub Release published yet.**

The source tree is the current release. A native Windows .exe is not yet available.

## Validation Methodology

Every capability claim is supported by evidence:
- EXECUTION PROOF: bytecode actually entered and progressed
- CALLBACK PROOF: actual callback method executed with expected arguments
- VIEW PROOF: actual application View hierarchy created
- RENDER PROOF: valid image containing pixels from runtime state
- OCR PROOF: OCR independently detects expected text from the PNG
- INTERACTION PROOF: input changes application state through real bytecode
- REPRODUCIBILITY PROOF: same outcome across clean independent runs

**Never trust a summary. Always verify artifacts.**

## Known Limitations

- C++ framebuffer renderer produces broken PNGs (invalid IDAT)
- Multi-DEX method resolution has edge cases with D8-renamed lambdas
- No JNI/native method support
- No SQLite, WebView, or Compose support
- Real APKs that use `setContentView(R.layout.*)` need AXML inflation (implemented in Python, not yet integrated into C++ runtime)

## Roadmap

1. Fix C++ framebuffer renderer
2. Integrate AXML inflation into C++ runtime
3. Fix polymorphic dispatch for method overrides across class boundaries
4. Implement SQLite support
5. Build native Windows .exe
6. Publish GitHub Release
7. Test more real APKs
