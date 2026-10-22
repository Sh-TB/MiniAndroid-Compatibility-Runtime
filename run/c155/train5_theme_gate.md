# CONT-155 TRAIN 5 — AppCompat theme-gate (C-type) diagnosis

APK: org.secuso.privacyfriendlytodolist_103 (+leradar, +exodusprivacy same signature).
Binary: 7b6927614ebef26f (post F-NEW-482). Logs: run/c155/t5_*.

## The kill chain (machine-verified links)
1. `AppCompatDelegateImpl.createSubDecor` (app dex, real bytecode) calls
   `obtainStyledAttributes(R.styleable.AppCompatTheme)` → the F-093 producer
   builds a TypedArray of **attrs=127, theme-backed** ([F-NEW-175] log line).
2. The styleable int[] content: **fill-array-data payload@546 byte-verified**
   (raw dex decode: ident=0x0300 ew=4 n=127): first entries
   [0x1010057, 0x10100ae, 0x7f040002, ...]; **0x10100ab (android:windowActionBar)
   and 0x1010033 (android:theme) are ABSENT from the payload** — this APK's
   R$styleable.AppCompatTheme array was rewritten by its build (only 2
   framework attrs remain). The engine faithfully materialized the dex data —
   NOT an engine defect. The index constants remap consistently (AOSP
   hasValue(index) semantics preserved).
3. Theme resolution census (MINIANDROID_F093_DIAG=1): **125/127 MISS, 2 HIT**
   — hits = 0x1010057 (windowNoTitle) + 0x10100ae (windowActionModeOverlay),
   i.e. exactly the attrs the APP's own theme styles define.
4. App-arsc parent chain (scripts/cont155_theme_chain.py, sparse-law walker):
   theme 0x7f1201e9 → 0x7f1202eb → 0x7f1202e9 → 0x7f120081 → 0x7f120080 →
   **0x010302e3 (android:Theme.Material.Light.NoActionBar)** — 5 levels,
   10 app-owned keys, windowActionBar absent at every app level. The app
   does NOT parent into the bundled appcompat styles at all — its chain ends
   at the PLATFORM Material theme.
5. The engine's materialized theme map has 373 keys (S124 diag: bag=373) =
   10 app keys + ~363 keys expanded from the framework chain. **0x10100ab is
   not among them** (the F093 census hit=no) — either the framework
   Material bag in miniandroid/framework_res/resources.arsc lacks
   windowActionBar, or the expansion misses it.
6. `a.hasValue(windowActionBar-slot)` → false → ISE "You need to use a
   Theme.AppCompat theme (or descendant)" → APP-BOUNDARY unwind at
   MainActivity.onCreate → no setContentView → WINDOW_ROOT verdict.

## Honest status
Links 1-4 + 6 are machine-verified end-to-end. Link 5's remaining question —
does the framework Material bag contain 0x10100ab — needs the ENGINE's own
arsc parser as the authority (my python walker handles DENSE/OFFSET16 but the
fw arsc mixes SPARSE-pair chunks; engine-side env-gated dump is the honest
next step). TRAIN 6 owns: env-gated theme-bag dump (read-only diag) →
definitive fix or framework-table repair.

## Fix lever (generic, app-independent)
The theme materialization must answer the compat parent chain exactly as
AOSP AssetManager2 does. If the framework table is the gap, the fix is the
framework-res content; if the expansion drops keys, the fix is the walker.
Either way the lever is the theme engine, never the app.
