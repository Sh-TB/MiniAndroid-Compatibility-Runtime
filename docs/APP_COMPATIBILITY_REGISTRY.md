# MiniAndroid App Compatibility Registry

**Last updated:** 2026-08-22 (EXP-076)
**Total apps tested:** 25
**Git commit:** HEAD

## Honest Compatibility Summary

| Category | Total | Rendered | OCR Output | Fully Verified |
|----------|-------|----------|------------|----------------|
| Synthetic corpus | 11 | 11 | 11 | 11 |
| Real APKs (F-Droid) | 13 | 9 | 1 | 1 |
| Telegram | 1 | 1 | 0 | 0 |
| **TOTAL** | **25** | **21** | **12** | **12** |

**Correct statement:** "At least one real APK has passed the real XML→View→render→OCR gate. The majority of real APKs execute but produce empty screenshots because their text comes from resource resolution and XML layout inflation that is not yet fully wired."

## Per-App Results

### Synthetic Corpus (11/11 OCR-verified — these prove the runtime CAN render)

| App | Category | Depth | Insns | Render | OCR | Text |
|-----|----------|-------|-------|--------|-----|------|
| HelloWorld | synthetic | 5% | 7 | PASS | "Hello World" |
| Calculator | synthetic | 5% | 30 | PASS | "1", "+", "2" |
| Counter | synthetic | 5% | 15 | PASS | "Count", "+1" |
| CounterV2 | synthetic | 5% | 17 | PASS | "Clicked!" (state mutation) |
| Notes | synthetic | 5% | 20 | PASS | "Save" |
| UnitConverter | synthetic | 5% | 35 | PASS | "Convert", "Miles" |
| TicTacToe | synthetic | 5% | 55 | PASS | "Tic Tac Toe" |
| MemoryGame | synthetic | 5% | 90 | PASS | "Memory" |
| Timer | synthetic | 5% | 25 | PASS | "Timer", "Start", "Stop" |
| SimpleList | synthetic | 5% | 35 | PASS | "Apples", "Bananas" |
| Settings | synthetic | 5% | 40 | PASS | "Settings" |

### Real APKs from F-Droid (1/13 OCR-verified)

| App | Package | Size | Depth | Insns | setContentView(int) | Inflated | Render | OCR | Blocker |
|-----|---------|------|-------|-------|---------------------|----------|--------|-----|---------|
| headingcalculator | org.debian.eugen.headingcalculator | 65KB | 5% | 22 | ✅ 0x7f030002 | 3 nodes | PASS | ✅ | — |
| gmdice | de.duenndns.gmdice | 64KB | 5% | 56 | ❌ | 0 | PASS | EMPTY | ListActivity path |
| simplestopwatch | omegacentauri.mobi.simplestopwatch | 172KB | 20% | 169 | ❌ | 0 | PASS | EMPTY | No setContentView(int) |
| notes | org.billthefarmer.notes | 217KB | 95% | 802K | ❌ | 0 | PASS | EMPTY | Loop: LocaleController |
| chessclock | com.chessclock.android | 124KB | 0% | 0 | ❌ | 0 | NO_VIEW | NOT_REACHED | onCreate not reached |
| unote | app.varlorg.unote | 163KB | 20% | 344 | ❌ | 0 | PASS | EMPTY | No setContentView(int) |
| openlauncher | com.benny.openlauncher | 3.5MB | 0% | 0 | ❌ | 0 | NO_VIEW | NOT_REACHED | onCreate not reached |
| tictactoe | com.emmanuelmess.tictactoe | 4.5MB | 5% | 56 | ❌ | 0 | PASS | EMPTY | No setContentView(int) |
| dooz | io.github.yamin8000.dooz | 1.7MB | 20% | 702 | ❌ | 0 | PASS | EMPTY | Compose-based UI |
| bgclock | nl.hansdezwart.bgclock | 1.0MB | 95% | 800K | ❌ | 0 | PASS | EMPTY | Loop: WebViewAssetLoader |
| microtimer | dubrowgn.microtimer | 209KB | 20% | 119 | ❌ | 0 | PASS | EMPTY | No setContentView(int) |
| stopwatch | com.github.muellerma.stopwatch | 738KB | 0% | 0 | ❌ | 0 | NO_VIEW | NOT_REACHED | onCreate not reached |
| simplekeyboard | rkr.simplekeyboard.inputmethod | 662KB | 5% | 8 | ❌ | 0 | FAIL | NOT_REACHED | 8 instructions only |

### Telegram (regression target)

| App | Size | Depth | Insns | Render | OCR | Blocker |
|-----|------|-------|-------|--------|-----|---------|
| Telegram | 83MB | 95% | 1.8M | PASS | EMPTY | Loop: PathParser.createNodesFromPathData |

## Execution Depth Analysis

| Depth | Count | Apps |
|-------|-------|------|
| 0% (onCreate not reached) | 4 | chessclock, openlauncher, stopwatch(muellerma), simplekeyboard |
| 5% (minimal execution) | 9 | All synthetic apps + gmdice, headingcalculator, tictactoe |
| 20% (partial execution) | 5 | simplestopwatch, unote, dooz, microtimer |
| 95% (deep execution) | 3 | notes(802K insns), bgclock(800K insns), Telegram(1.8M insns) |

## Key Findings

1. **Deep execution ≠ visible output.** Three apps (notes, bgclock, Telegram) execute 800K-1.8M instructions but produce empty screenshots. They reach deep into the bytecode but the view tree has no text because:
   - Text comes from `setText(int resourceId)` which isn't resolved
   - Layout inflation (`setContentView(R.layout.*)`) isn't captured for these apps
   - Some apps use Jetpack Compose (dooz) or ListActivity (gmdice) which have different paths

2. **Only headingcalculator passes the full gate.** It's the only real APK where `setContentView(int)` is captured, AXML is inflated, and OCR produces output.

3. **Synthetic apps prove the runtime works.** All 11 synthetic apps pass because they use programmatic `setText(String)` which doesn't require resource resolution. The gap is in resource/AXML handling, not in the DEX interpreter.

4. **No regression.** Telegram still executes 1.8M instructions with the same behavior as before. No generic fix was broken.

## Verification Status

```
AUTOMATED_STATUS = computed by this script
HUMAN_VERIFIED = UNKNOWN (not yet verified by a human on a Windows build)
```

Every PASS above is an automated PASS. No app has been human-verified yet.

## Blocker Classification

| Blocker | Type | Affected Apps | Fix Priority |
|--------|------|---------------|--------------|
| setContentView(int) not captured | GENERIC | All real APKs except headingcalculator | HIGH |
| ListActivity setContentView path | GENERIC | gmdice | MEDIUM |
| Jetpack Compose UI | GENERIC | dooz | LOW (very different architecture) |
| Loop detector catches | PRE-EXISTING | notes, bgclock, Telegram | LOW (not blocking) |
| onCreate not reached | APP-SPECIFIC | chessclock, openlauncher, stopwatch, simplekeyboard | MEDIUM |
