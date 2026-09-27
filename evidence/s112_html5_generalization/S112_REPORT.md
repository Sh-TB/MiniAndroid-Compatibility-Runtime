# S112 — HTML5/WebView GENERALIZATION WAVE (user directive: does the Breakout fix affect other HTML5 apps/games?)

Directive: post the Breakout achievement image + test whether the HTML5/WebView
execution capability GENERALIZES to other Android apps/games; report honestly.

## Verdict

| APK | kind | engine | result | proof |
|---|---|---|---|---|
| me.lecaro.breakout (Breakout 71) | HTML5 game (Capacitor) | WebView+QuickJS | **RENDERS** — 9th achievement anchor, byte-identical `568342fb` through ROOT-054..057 | evidence/s109_webview/breakout_fix52_run1/screenshot.png |
| io.github.hathibelagal.mykanji | HTML5 APP (plain WebView over local HTML) | WebView+QuickJS | **RENDERS** — `loadUrl engine ok: doc=assets/index.html bytes=3406`, scripts executed=3, js_errors=0, document text painted (224 unique colors) | mykanji_run1/screenshot.png |
| com.vovagorodok.blidraughts | HTML5 game (Capacitor) | WebView+QuickJS | **NOT YET** — 4 roots fixed this wave (054-057), app's own version gate PASSED, Bridge builds to MessageHandler; blocked inside R8-transformed androidx.webkit feature registry (ROOT-058, open) | blidraughts_run7/screenshot.png = honest blank frame |

## New generic roots (no package checks — every WebView-family APK gets the same answers)

| root | bug (engine truth) | law applied |
|---|---|---|
| ROOT-054 | WebView provider metadata carried versionName "1.0.0" → blidraughts' own gate `parseInt(versionName.split(".")[0]) < MIN_VERSION` showed its "Update required!" dialog (the APK audits #74 reopen reason) | WebView provider identity = PLATFORM BUILD METADATA (same class as Build.VERSION.SDK_INT=34); provider id com.android.webview, API-34-era version 120.0.6099.144, env-overridable |
| ROOT-055 | View.getLayoutParams answered void/null → real-DEX CoordinatorLayout.prepareChildren NPE'd on findAnchorView → BridgeActivity catch → no_webview fallback | AOSP law: inflated/added views NEVER have null LayoutParams — materialize the PARENT-TYPE params (CoordinatorLayout.LayoutParams, anchorId=NO_ID, both field spellings anchorId/mAnchorId) |
| ROOT-056 | findViewById(0) matched the ROOT node (unset-id views matched by position) → "View can not be anchored to the parent CoordinatorLayout" ISE | AOSP law: View.NO_ID lookups (id ≤ 0) answer null, no search |
| ROOT-057 | CookieManager.getInstance() generic-missed → CapacitorCordovaCookieManager.<init> NPE → MockCordovaWebViewImpl.init + Bridge$Builder.create unwind → APP BOUNDARY | AOSP law: the WebView provider ships its cookie manager — process-wide singleton, empty honest store (getCookie null, hasCookies false) |

## Regression gates — ZERO pixel drift through all 4 root fixes

| title | shot SHA-16 | anchor | match |
|---|---|---|---|
| breakout (HTML5) | 568342fb901a75ab | S111 | byte-identical |
| ballbreak | fe797c19ba1920ed | S107 | byte-identical |
| dooz | a2ba4a4942152926 | S107 | byte-identical |

## mykanji run facts (the generalization proof)

| fact | value |
|---|---|
| APK | io.github.hathibelagal.mykanji vc7 (F-Droid) |
| WebView | created (o146), loadUrl `file:///android_asset/index.html` → engine ok, 3406 bytes |
| JS | scripts executed=3, js_errors=0, raf_pending=2 |
| pixels | 1080x1920, 224 unique colors, black text body (~3.4k px) + gray UI — real document render |
| residual errors | 4 (menu-inflater/Toolbar margins family — APP-POLICY/UI chrome, next wave) |

## blidraughts honest chain (S112)

1. version gate PASSED (ROOT-054: parseInt("120") ≥ MIN_VERSION — the "Update required!" dialog is GONE)
2. layout NPE FIXED (ROOT-055) → prepareChildren completes
3. anchor ISE FIXED (ROOT-056)
4. CookieManager NPE FIXED (ROOT-057) → Bridge init proceeds through cordova PluginManager → BridgeWebViewClient → CapConfig
5. BLOCKED: androidx.webkit feature registry — R8 transformed WebViewFeature enum into a String-constant holder; the real-DEX isSupported(String) loop over the static ConditionallySupportedFeature collection finds zero name matches → its own RuntimeException "Unknown feature WEB_MESSAGE_LISTENER" → APP-BOUNDARY. ROOT-058 (open): app-DEX static-init gap for R8-transformed androidx.webkit registries.

## Method notes

- APKs re-fetched from F-Droid (suggested version codes: blidraughts 3, mykanji 7, breakout 29826425).
- Runs: foreground, timeout 280s, evidence dirs evidence/s112_html5_generalization/*_run{1,3,4,5,6,7}.
- DEX ground truth read via scripts/s112_dexdump.py (real classes.dex parse) — the isSupported bytecode decode is in scripts/s112_decode_issupported.py.
- No per-app patches: all 4 roots are platform laws answered identically to every caller.
