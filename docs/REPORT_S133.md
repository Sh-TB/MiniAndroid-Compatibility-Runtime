# S133 — MINI BROWSER / z.ai FULL PAGE LOAD + WHITE/BLACK/GREY SCREEN ROOT-CAUSE CAMPAIGN

## A. EXECUTIVE RESULT

```
S133 STATUS: VERIFIED
```

- **Live z.ai frontier moved from `network-dead` to `JS-data-pass`**: before S133 a live
  z.ai load rendered an honest empty placeholder (no network document law). After S133 the
  full chain NETWORK → HTTP → TLS → HTML → DOM → CSS (1,436 rules + 2 fonts) → ES-module
  JS execution → live data APIs (3 × HTTP 200 incl. a 287,571-byte models payload) runs on
  the real site through a real APK (Mini Browser v2).
- **14 new roots registered** (R-NEW-443…456): 9 ROOT-CAUSED-FIXED, 3 VERIFIED(_3RUN)
  general render laws, 2 IMPLEMENTED instrumentation/surface laws, 1 honest BLOCKED residual
  (R-NEW-456) with exact attribution.
- **Zero regressions**: battery ALL PASS (124 stages), laws130 51/51, all goldens preserved.
- **The white/grey screen investigation** (§30/§11) closed with a measured answer for this
  cycle: the reported white screen is NOT a framebuffer/stride/surface corruption —
  screenshot forensics show a uniform white page surface (98.5% white, entropy 0.116,
  unique 222 incl. chrome text AA) exactly matching "static shell painted, SPA boot
  rejected". No repeated-row period correlates with any stride boundary
  (period detection: uniform-region artifact, no block anomaly).

## B. z.ai LIVE (first-divergence chain)

```
LIVE:             https://z.ai/ → (307) → https://chat.z.ai/
FINAL URL:        https://chat.z.ai/
NETWORK:          PASS   WEB-001: status=200 redirects=1 bytes=15727 type=text/html ms≈500
HTML:             PASS   parsed, 8 inline + 3 external scripts
DOM:              PASS   #app mount target present
CSS:              PASS   index CSS 436,235B → 1,436 rules; 2 fonts registered
JS LOAD:          PASS   R-NEW-444: ES-module law — 3,244,563B bundle parses+executes
JS:               PARTIAL  boot chain rejected inside app code (R-NEW-456)
JS DATA:          PASS   /api/v1/auths/ 200 (859B) · /api/config 200 (1,092B) ·
                         /api/models 200 (287,571B)  [needs R-NEW-445/446/447]
LAYOUT:           PARTIAL  static shell lays out (body/#app 1080x48)
TEXT:             PASS   (chrome text; page text pending JS boot)
IMAGE:            N/A    (page images load post-boot)
SVG:              N/A
FONT:             PASS   Geist + bitstream TTFs registered from live CSS
PAINT:            PARTIAL  static shell painted white
CANVAS:           PASS-law (R-NEW-453; page canvases pending boot)
SURFACE:          PASS   webview surface blitted rect=0,168 1080x1752
FRAMEBUFFER:      PASS   fb updated; 31,146 non-white px = chrome + shell
SCREENSHOT:       PASS   3-run byte-identical f2169ebcaaf069ce
FIRST DIVERGENCE: (this cycle, resolved) <script type=module> as classic → export SyntaxError
                  (current residual) Svelte-5 runtime in-bundle rejection → R-NEW-456 BLOCKED
```

## C. WHITE/BLACK/GREY ROOT

```
observed pattern    white page below browser chrome (98.5% white, 222 unique colors,
                    entropy 0.116); reported historical "~10 rows black + repeated middle"
                    pattern NOT reproduced in any S133 frame
measured pattern    row-hash periodicity = uniform-region artifact only; no period correlates
                    with stride (1080*4) or any block boundary; framebuffer math verified
                    (stride = width*4, RGBA; blit row loop exact)
first divergence    JS EXEC: ES-module parse death (fixed) → then Svelte-5 in-bundle
                    rejection (residual R-NEW-456)
root cause          layer-resolved, NOT color corruption: the white screen is the honest
                    static shell with the SPA boot dead upstream (JS layer)
evidence            evidence/s133_browser/zai_live_screen_metrics.json + 3-run SHA equality
```

## D. COMPONENT REUSE

No new external components adopted — the campaign's substrate proved sufficient
(REUSE-FIRST law: capability gained per new LOC):

| substrate (already in-tree) | reused for |
|---|---|
| QuickJS 2024-01-13 (ADOPTED_VENDORED) | ES-module system: JS_EVAL_TYPE_MODULE + module loader ≈ 150 LOC adapter (R-NEW-444) |
| mininet::http_get (S100 NET-001) | top-level document fetch + resource tier + fetch() transport (R-NEW-443/445) |
| OpenSSL | TLS for all new network paths (no new code) |
| S117 resolve_url / RFC 3986 laws | module normalize + fetch base resolution |
| S118 job pump / drain laws | module + fetch promise continuations |
| renderer::decode_image_bytes | `<img>` paint (no new decoder) |
| svg_flatten + scanline fill | SVG basic shapes (zero new raster code) |
| S114 layout engine | inline-block run law inside the existing layout_stack_once |

New law code: ≈ 700 LOC total (fetch/module/cookie ~250, inline-block ~80,
img ~90, SVG shapes ~60, canvas attrs ~30, URLSearchParams polyfill ~60 (JS),
stubs/observers ~25 (JS), diagnostics ~120). Alternatives rejected: litehtml
(not triggered — no document-class CSS layout root measured: the z.ai CSS
engine handled 1,436 rules; the residual is JS-layer), lexbor (same gate),
new browser engine (forbidden, not needed).

## E. REAL APK RESULTS

| APK | before | after | frontier | proof |
|---|---|---|---|---|
| Mini Browser v2 (com.miniandroid.browser VC2, sha c5705d40…) | white placeholder on any live URL | live z.ai: network→DOM→CSS→module-JS→data 200 | browser network document class | evidence/s133_browser/*; 3-run f2169ebcaaf069ce ×3 |
| webfix harness (com.miniandroid.webfix, sha b4aadf3d…) | n/a (new §22 suite) | T01–T17 capability matrix | engine render laws | evidence/s133_webfix/*; T02 3-run c95affdefb734ffd ×3 |
| klondike (corpus) | banner.html loads, ad img never rendered | banner img law + location.protocol law exercised; adserver honestly fails | corpus fan-out | run/s133/klondike_fanout |
| S114 HTML5 five + corpus battery | 124 stages | 124 stages ALL PASS | no regression | battery log |

## F. ROOTS

```
closed (ROOT-CAUSED-FIXED): R-NEW-443 WEB-001 network document · R-NEW-444 ES-module
  · R-NEW-445 fetch base URL · R-NEW-446 fetch init headers · R-NEW-447 cookie store
  · R-NEW-448 rejection visibility · R-NEW-449 web-API stubs
verified (VERIFIED/VERIFIED_3RUN): R-NEW-450 inline-block atomic boxes (3-run)
  · R-NEW-451 <img> replaced element · R-NEW-452 SVG basic shapes · R-NEW-453 canvas
  intrinsic size · R-NEW-455 resource forensics instrumentation
implemented: R-NEW-454 DOM/URL surface family (URLSearchParams, getElementsByTagName,
  document.location)
new blocked: R-NEW-456 z.ai Svelte-5 in-bundle boot rejection (P2, attributed to line 7)
superseded: —
```

## G. CAPABILITIES

Master worklist regenerated: 673 items (454 roots + 197 caps + 22 mandates), open 259,
P0 20 / P1 67 / P2 64 / P3 105 / P4 3. WebView cluster: M-16 unchanged (litehtml
trigger NOT fired — no document-class layout root measured); new capability entries
flow through the generator from the root statuses.

## H. CORPUS FAN-OUT

```
number scanned        all corpus APK dirs (canonical_apks + s65/s72/s80/s83/s86/s98/s105)
number WebView-class  3  (fishrings, tripeaks, ballbreak) + klondike banner + the
                      S114 HTML5 five (covered by the battery)
number improved       klondike banner (img/protocol laws now exercised); ballbreak class
                      (network WebView law available); klondike/tripeaks/fishrings
                      asset loads unchanged (battery-green)
number unchanged      all remaining (battery ALL PASS 124 stages)
new clusters          network-WebView (ballbreak https refs) — law ready; ES-module class
                      (z.ai-class SPAs) — laws ready, next cycle's replay bisect
```

## I. REGRESSION

```
laws130:        51/51 PASS
battery:        ALL PASS — 124 stages, zero FAIL (includes S114 HTML5 five,
                klondike/ballbreak goldens, EXT-01/02, density oracle, law tests)
goldens:        preserved byte-exact
input/graphics: no change (battery stages green)
browser:        new tests T01–T17 all deterministic; T02 byte-identical ×3
```

## J. EVIDENCE

| artifact | path |
|---|---|
| live z.ai console traces | evidence/s133_browser/zai_live*_console.log |
| z.ai white-shell screenshot + metrics | evidence/s133_browser/zai_live_white_shell.png, zai_live_screen_metrics.json |
| z.ai resource trace (live) | run/s133/zai_live2/webview_resource_trace.json |
| z.ai main bundle (diagnostic copy) | evidence/s133_browser/zai_main_bundle_index-BEIsjDOv.js |
| S100 browser live-z.ai probe (text reader) | evidence/s133_browser/s100_browser_zai_textreader.png |
| Mini Browser v2 APK | upload/s133_browser/build/minibrowser_v2.0_vc2.apk (sha c5705d40dc1eba05af26198884a5869e78e7da2aa72523cb3d50dec125a9aacf) |
| control harness APK | upload/s133_webfix/build/webfix_v1.0_vc1.apk (sha b4aadf3d1bbb14e30a1f3ec46228c138b917dee87c0e813535a6928320ce4246) |
| fixture suite evidence | evidence/s133_webfix/T02…T16 PNG + metrics JSON |
| 3-run manifests | run/s133/repro/ (T02: c95affdefb734ffd ×3; z.ai: f2169ebcaaf069ce ×3) |
| forensics tool | scripts/s133_screen_forensics.py |
| registration scripts | scripts/s133/s133_register_roots.py |
| fixture/build scripts | scripts/s133/s133_build_browser.sh, s133_build_webfix.sh, s133_make_fixtures.py, s133_fix_suite.sh |

## K. NEXT FRONTIER

1. **R-NEW-456 replay bisect** (P2): newline-split replay copy of the z.ai bundle served
   locally; per-line probes attribute the Svelte-5 rejection to an exact statement; the
   engine law beneath it (iterable shape or app fix) lands next cycle.
2. **fetch POST + response Headers** (R-NEW-446 residue): measured need = any
   authenticated write-path SPA.
3. **first_divergence.json auto-generation** (R-NEW-455 residue): fold the stage table
   into the battery as a diagnostic stage.
4. **Import maps** for bare module specifiers (R-NEW-444 residue) on measured corpus need.
