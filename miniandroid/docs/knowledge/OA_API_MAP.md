# Open-Source App API Map

**Last Updated:** 2026-08-26
**Primary Branch HEAD:** `cdfd8fc`

This document tracks which Android APIs are used by real open-source
applications in the MiniAndroid test corpus, and the current MiniAndroid
compatibility status for each.

## Apps in Corpus

| App | Package | Source | APK Size | Status |
|-----|---------|--------|----------|--------|
| Telegram | org.telegram.messenger.web | DrKLO/Telegram | 79 MB | PARTIAL (SMS page proven) |
| uNote | app.varlorg.unote | F-Droid | small | PASS (exit=0, 23K dark px) |
| simplestopwatch | com.github.muellerma.stopwatch | F-Droid | small | PARTIAL (exit=1, screenshot produced) |
| TicTacToe (dooz) | io.github.yamin8000.dooz | F-Droid | small | NOT TESTED on current HEAD |
| OpenLauncher | com.benny.openlauncher | F-Droid | medium | NOT TESTED on current HEAD |
| bgclock | nl.hansdezwart.bgclock | F-Droid | tiny | NOT TESTED on current HEAD |
| microtimer | dubrowgn.microtimer | F-Droid | tiny | NOT TESTED on current HEAD |
| simplekeyboard | rkr.simplekeyboard.inputmethod | F-Droid | small | NOT TESTED on current HEAD |

## API Frequency Map

| API / Class | Apps Using It | MiniAndroid Status | Priority |
|------------|---------------|-------------------|----------|
| Activity.onCreate | ALL | IMPLEMENTED | - |
| setContentView | ALL | IMPLEMENTED | - |
| TextView.setText | ALL | IMPLEMENTED | - |
| Bundle.putString/getString | Telegram, uNote | IMPLEMENTED | - |
| HashMap.get/put | Telegram, uNote | IMPLEMENTED (CollectionShadow) | - |
| Handler.post/postDelayed | Telegram | IMPLEMENTED | - |
| LayoutInflater | Telegram, OpenLauncher | PARTIAL (layout_cache.json) | HIGH |
| Resources.getString | Telegram | IMPLEMENTED (resource_values.json) | - |
| Context.getApplicationContext | ALL | IMPLEMENTED | - |
| Context.getSystemService | Telegram, OpenLauncher | PARTIAL (returns null) | HIGH |
| PackageManager.getPackageInfo | Telegram | PARTIAL | MEDIUM |
| SystemClock.uptimeMillis | Telegram, stopwatch | PARTIAL (wide values fixed) | MEDIUM |
| TelephonyManager | Telegram | PARTIAL (returns null) | LOW |
| ConnectionsManager.sendRequest | Telegram | MOCKED (controlled boundary) | - |
| GLSurfaceView / GL20 | TicTacToe (dooz) | PARTIAL (SoftwareGL20) | HIGH |
| ShapeRenderer | TicTacToe (dooz) | PARTIAL (Coder 2) | HIGH |
| Canvas / Paint | bgclock, stopwatch | IMPLEMENTED | - |
| SharedPreferences | uNote, Telegram | IMPLEMENTED | - |
| TextUtils.isEmpty | ALL | PARTIAL (API bridge) | MEDIUM |
| View.setOnClickListener | ALL | IMPLEMENTED | - |
| View.setVisibility | Telegram | IMPLEMENTED | - |
| MotionEvent | (not yet tested) | NOT IMPLEMENTED | HIGH |
| Intent extras | (not yet tested) | PARTIAL | MEDIUM |
| Build.VERSION | (not yet tested) | NOT IMPLEMENTED | MEDIUM |
| DisplayMetrics | (not yet tested) | NOT IMPLEMENTED | MEDIUM |
| Uri | (not yet tested) | NOT IMPLEMENTED | MEDIUM |
| Base64 | Telegram | NOT IMPLEMENTED | MEDIUM |
| Clipboard | (not yet tested) | NOT IMPLEMENTED | LOW |
| Toast | (not yet tested) | NOT IMPLEMENTED | LOW |
| SparseArray | (not yet tested) | NOT IMPLEMENTED | LOW |
| ArrayMap | (not yet tested) | NOT IMPLEMENTED | LOW |

---

## Corpus Validation Results (2026-08-26, HEAD d00aabf)

| App | Exit | Dark Pixels | Status |
|-----|------|-------------|--------|
| uNote (app.varlorg.unote) | 0 | 23472 | PASS — real UI rendered |
| microtimer (dubrowgn.microtimer) | 0 | 23472 | PASS — real UI rendered |
| simplekeyboard (rkr.simplekeyboard.inputmethod) | 0 | 23472 | PASS — real UI rendered |
| stopwatch (com.github.muellerma.stopwatch) | 1 | 23472 | PARTIAL — UI rendered, exit=1 |
| bgclock (nl.hansdezwart.bgclock) | 0 | 0 | PASS — exit=0, blank clock face |
| openlauncher (com.benny.openlauncher) | 1 | 0 | FAIL — no rendering |
| dooz (io.github.yamin8000.dooz) | 124 | 0 | TIMEOUT — likely infinite loop |
| tictactoe | 0 | 0 | PASS — exit=0, no rendering |

Summary: 5/8 PASS, 1 PARTIAL, 1 FAIL, 1 TIMEOUT.
3 apps render real UI (23472 dark pixels each).
