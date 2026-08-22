# MiniAndroid Runtime

**Version:** 0.2.0-exp074
**Date:** 2026-08-22
**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime

## WHAT IS MINIANROID?

MiniAndroid is a **headless Android APK execution runtime** built from scratch in C++. It parses real APK files, executes real Dalvik (DEX) bytecode, and produces view trees + screenshots — **without an Android emulator, without a JVM, without GPU/OpenGL, and without BIOS virtualization**.

## WHAT IS THE DIFFERENCE FROM A NORMAL ANDROID EMULATOR?

| Feature | Android Emulator | MiniAndroid |
|---------|-----------------|-------------|
| Runs real Android OS | ✅ Yes (full system image) | ❌ No (no Android OS) |
| Runs real APK DEX bytecode | ✅ Yes | ✅ Yes |
| Requires JVM/ART | ✅ Yes | ❌ No (C++ DEX interpreter) |
| Requires GPU/OpenGL | ✅ Yes | ❌ No (CPU software rendering) |
| Requires BIOS virtualization (KVM/HAXM) | ✅ Yes | ❌ No |
| Produces screenshots | ✅ Yes (GPU framebuffer) | ⚠️ Python view-tree renderer (C++ framebuffer BROKEN) |
| Executes multi-DEX APKs | ✅ Yes | ✅ Yes |
| Executes real Telegram APK | ✅ Yes | ✅ Partially (logic yes, visual partial) |
| Executes synthetic test APKs | ✅ Yes | ✅ Yes (11/11 verified) |
| Executes real open-source APKs | ✅ Yes | ❌ No (XML layout inflation not supported) |
| Speed | Slow (full boot) | Fast (<1 second per APK) |
| Deterministic | ❌ No (timing-dependent) | ✅ Yes (byte-identical across runs) |

## CURRENTLY PROVEN CAPABILITIES

| Capability | Status | Evidence |
|-----------|--------|----------|
| APK parsing | ✅ PROVEN | Real Telegram APK (63MB, 5 DEX files) parses correctly |
| DEX bytecode execution | ✅ PROVEN | 578,687 instructions executed in Telegram run |
| Multi-DEX support | ✅ PROVEN | Per-DEX const-string/type/method resolution |
| Activity lifecycle (onCreate) | ✅ PROVEN | Real onCreate bytecode executes |
| View hierarchy construction | ✅ PROVEN | 2,284 view nodes from Telegram |
| TextView/Button/LinearLayout | ✅ PROVEN | 11/11 synthetic apps create real views |
| Text rendering (setText(String)) | ✅ PROVEN | OCR-verified on 11 synthetic apps |
| Click listener registration | ✅ PROVEN | setOnClickListener captured |
| Click dispatch (generic) | ✅ PROVEN | App-agnostic find_all_with_click_listener |
| State mutation (click → setText) | ✅ PROVEN | CounterV2: "Count: 0" → "Clicked!" |
| Controlled network boundary | ✅ PROVEN | sendRequest intercepted, mock response delivered |
| Async Runnable scheduling | ✅ PROVEN | Lambda0/1/2 chain executes |
| Instance field access (iget/iput) | ✅ PROVEN | CounterV2 display field |
| Shadow registry (View/Handler/etc.) | ✅ PROVEN | 8 shadow classes operational |
| OCR verification gate | ✅ PROVEN | Tesseract 5.5.0 on real PNGs |
| Anti-false-positive validators | ✅ PROVEN | Blank-UI detector, screenshot-determinism check |
| 3-run reproducibility (synthetic) | ✅ PROVEN | Byte-identical SHA256s |

## CURRENTLY PARTIAL CAPABILITIES

| Capability | Status | Details |
|-----------|--------|---------|
| Telegram SMS page (CHECKPOINT_M) | ⚠️ PARTIAL | Logic PROVEN (full chain executes), visual NOT PROVEN (broken screenshot) |
| Text resource ID resolution | ⚠️ PARTIAL | setText(int) captured, but ARSC resolver not fully wired |
| Synthetic corpus rendering | ⚠️ PARTIAL | Python renderer works; C++ framebuffer is broken |

## KNOWN LIMITATIONS

| Limitation | Impact | Classification |
|-----------|--------|---------------|
| **C++ framebuffer renderer broken** | screenshot.png is invalid PNG for ALL apps | GENERIC — HIGH priority |
| **XML layout inflation not supported** | Real APKs that use `setContentView(R.layout.*)` fail | GENERIC — HIGHEST priority |
| **`findViewById` returns null** | No views created from XML layouts | GENERIC (depends on above) |
| **No JNI/native method support** | All native methods stubbed | GENERIC — MEDIUM priority |
| **No real SQLite** | Only SharedPreferences implemented | GENERIC — LOW priority |
| **No real networking** | Only controlled network boundary (mock) | GENERIC — LOW priority |
| **No real drawable decoding** | ImageView placeholders are grey | GENERIC — MEDIUM priority |
| **No Fragment/ListActivity support** | Some real APKs can't create their main view | GENERIC — MEDIUM priority |

## VALIDATION CORPUS

### Synthetic Corpus (11 APKs — all PROVEN)

| App | Pattern | OCR Verified |
|-----|---------|-------------|
| HelloWorld | Activity + TextView | ✅ "Hello World" |
| Calculator | LinearLayout + 4 Buttons | ✅ "1", "+", "2" |
| Counter | Button + TextView (state) | ✅ "Count", "+1" |
| CounterV2 | Click listener + state mutation | ✅ "Clicked!" (after click) |
| Notes | EditText + Button (input) | ✅ "Save" |
| UnitConverter | TextViews + EditText (form) | ✅ "Convert", "Miles" |
| TicTacToe | 3x3 Button grid (game) | ✅ "Tic Tac Toe" |
| MemoryGame | 4x4 Button grid (game) | ✅ "Memory" |
| Timer | TextView + Buttons (state) | ✅ "Timer", "Start", "Stop" |
| SimpleList | Multiple TextViews (list) | ✅ "Apples", "Bananas" |
| Settings | Multiple labeled TextViews | ✅ "Settings", "Notifications" |

### Real APK Corpus (5 APKs from F-Droid — all BLOCKED)

| App | Size | Execution Depth | Blocker |
|-----|------|----------------|---------|
| de.duenndns.gmdice | 64KB | ~10% | setContentView(int) not inflated |
| omegacentauri.mobi.simplestopwatch | 172KB | ~15% | Same |
| org.billthefarmer.notes | 217KB | ~70% (802K insns) | 129 view nodes but no text (XML layout) |
| org.debian.eugen.headingcalculator | 65KB | ~5% | Same |
| com.chessclock.android | 124KB | 0% (exit 1) | onCreate not reached |

### Telegram

| Checkpoint Dimension | Status |
|---------------------|--------|
| LOGIC (bytecode chain) | ✅ PROVEN |
| CALLBACK (Lambda2.run) | ✅ PROVEN |
| VIEW (SmsView in view tree) | ✅ PROVEN |
| RENDER (screenshot) | ❌ NOT_PROVEN (broken PNG) |
| OCR | ❌ NOT_PROVEN (never run) |
| REPRODUCIBILITY | ⚠️ PARTIAL (logic yes, visual no) |

## GAME EXPERIMENTS

| Game | Board Rendered | OCR Verified | Click Dispatch | State Mutation |
|------|----------------|-------------|----------------|----------------|
| TicTacToe (3x3) | ✅ | ✅ "Tic Tac Toe" | ⚠️ Not yet (cells have no listeners) | ❌ Not yet |
| MemoryGame (4x4) | ✅ | ✅ "Memory Game" | ⚠️ Not yet | ❌ Not yet |

## WEB/NETWORK EXPERIMENTS

**Status:** NOT STARTED

No WebView or network content test has been attempted yet.

## SQLITE EXPERIMENTS

**Status:** NOT STARTED

No SQLite test has been attempted yet. Only SharedPreferences is implemented.

## SANDBOX EXPERIMENTS

**Status:** NOT STARTED

No sandbox close/reopen persistence test has been attempted yet.

## WINDOWS BUILD

**Status:** NOT STARTED

No Windows build has been created yet. The runtime currently builds and runs on Linux only.

## HOW TO TEST

### Prerequisites
- Linux x86_64
- g++ with C++17 support
- Python 3 with PIL/Pillow
- Tesseract OCR (for OCR verification)

### Build
```bash
cd miniandroid
bash build_exp042.sh
```

### Run a single APK
```bash
./build_exp042/miniandroid_exp042 <apk_path> <output_dir>
```

### Run the synthetic corpus + OCR verification
```bash
python3 /home/z/my-project/scripts/exp073_baseline_ocr.py
```

### Run Telegram regression
```bash
bash run_telegram_test.sh 90
```

## HOW TO REPORT A FAILURE

1. Run the APK: `./build_exp042/miniandroid_exp042 <apk> <output_dir>`
2. Check `output_dir/run.log` for execution traces
3. Check `output_dir/view_tree.json` for view hierarchy
4. Check `output_dir/screenshot.png` (NOTE: C++ renderer is broken — use Python renderer)
5. Run OCR: `tesseract output_dir/exp073_rendered.png - --psm 6`
6. Record: APK name, package, version, APK SHA256, DEX SHA256, execution depth, last method, last PC, blocker classification

## ROADMAP

### Immediate (next experiment)
1. **XML layout inflation** — implement `setContentView(int)` → AXML parsing → view creation. This is THE blocker for all real APKs.
2. **Fix C++ framebuffer renderer** — or deprecate it and always use Python renderer.
3. **Wire ARSC string resolution** — connect Python ARSC parser to view-tree renderer.

### Short-term
4. Re-run Telegram with Python renderer → produce real screenshot → OCR
5. Windows minimal build
6. SQLite support
7. Drawable decoding (PNG/JPEG/WebP)

### Long-term
8. JNI/native method support
9. Fragment/ListActivity support
10. WebView support
11. Full Android API surface coverage

## REGRESSION SUITES

| Suite | Tests | Status |
|-------|-------|--------|
| EXP-052 (invoke/branch/exception) | 6 | ✅ ALL PASS |
| EXP-059 (opcode) | 4 | ✅ ALL PASS |
| EXP-066 (multi-DEX) | 4 | ✅ ALL PASS |

## VERSION HISTORY

| Version | Date | Key Achievement |
|---------|------|-----------------|
| 0.1.0 | 2026-08-14 | Initial APK parsing + DEX execution |
| 0.1.5 | 2026-08-15 | EXP-050: 336 methods, SharedPreferences |
| 0.1.10 | 2026-08-17 | EXP-058: Fragment lifecycle, per-DEX types |
| 0.1.15 | 2026-08-18 | EXP-061: CPU-only Login UI rendering |
| 0.1.20 | 2026-08-19 | EXP-066: Multi-DEX semantic audit |
| 0.1.25 | 2026-08-20 | EXP-069: Generic text input + click dispatch |
| 0.1.30 | 2026-08-21 | EXP-071: Telegram SMS page transition (LOGIC PROVEN, VISUAL PARTIAL) |
| 0.1.35 | 2026-08-21 | EXP-072: Cross-app corpus + OCR verification gate |
| 0.1.40 | 2026-08-22 | EXP-073: 11/11 synthetic apps verified + state mutation PROVEN |
| **0.2.0** | **2026-08-22** | **EXP-074: Honest reconciliation + setText(int) capture + setContentView(int) capture** |
