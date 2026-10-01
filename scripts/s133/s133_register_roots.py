#!/usr/bin/env python3
"""s133_register_roots.py — S133 root registration (MINI BROWSER / z.ai
full-page-load + white/grey screen root-cause campaign).

16 measured roots: WEB-001 network document, ES-module, fetch URL/init,
cookie store, rejection visibility, web stubs, inline-block atomic boxes,
<img> replaced element, SVG basic shapes, canvas intrinsic size,
URLSearchParams/getElementsByTagName/document.location surface, resource
forensics instrumentation, and the honest z.ai live residual.
"""
import json

ROOTS = "/home/z/my-project/root_registry.json"

with open(ROOTS) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) else reg
by_id = {r.get("id"): r for r in roots}

def upsert(entry):
    if entry["id"] in by_id:
        by_id[entry["id"]].update(entry)
    else:
        roots.append(entry)

B = "miniandroid/build/minibrowser_v2.0_vc2.apk"

entries = [
 {
  "id": "R-NEW-443",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P0",
  "fg": False,
  "title": "WEB-001 network document law missing: WebView.loadUrl(http/https) kept the honest-placeholder law (no top-level fetch) — the FIRST divergence of every live-site load",
  "evidence": (
      "S133 LAW 0 probe: the S101/S109 asset law loaded file:///android_asset/ only; "
      "http(s) URLs rendered the honest empty placeholder (recorded WEB-001 DESIGNED gap). "
      "FIX (~70 LOC adapter): android_shadows loadUrl http(s) arm reuses mininet::http_get "
      "(S100 NET-001, OpenSSL TLS, redirects, chunked) → status/content-type gate → "
      "WebViewEngine::load_document(final_url, body, apk) — zero new network code (REUSE-FIRST). "
      "LIVE PROOF (browser v2 → https://z.ai/): status=200 redirects=1 final=https://chat.z.ai/ "
      "bytes=15727 type=text/html ms=496 → engine ok. Evidence: evidence/s133_browser/."
  ),
  "missing": "network error-page rendering (DNS/TLS failure UX)",
  "next": "corpus network-WebView class (ballbreak https refs) on-demand",
  "commit": "S133",
 },
 {
  "id": "R-NEW-444",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P0",
  "fg": False,
  "title": "ES-MODULE script law missing: <script type=module> executed with classic goals → SyntaxError: unsupported keyword: export — the FIRST DIVERGENCE of the live z.ai load (the 3.2MB Vue/Svelte SPA bundle died at parse; app never mounted; page white)",
  "evidence": (
      "z.ai chat page: <script type=\"module\" crossorigin src=.../index-BEIsjDOv.js> — engine "
      "collected it as a classic script; QuickJS threw SyntaxError at the top-level export{}. "
      "FIX: (a) html_dom records type=module for inline+external scripts; (b) exec_script "
      "is_module → JS_EVAL_TYPE_MODULE; (c) QuickJS module system wired at runtime ctor: "
      "JS_SetModuleLoaderFunc(s133_module_normalize [bare-specifier honesty + RFC 3986 §5.2 merge "
      "+ §5.2.4 dot-segments], s133_module_loader [fetch_resource substrate → COMPILE_ONLY eval]); "
      "inline modules get base-anchored synthetic names. "
      "PROOF: live z.ai bundle (3,244,563 B) parses+executes (scripts executed 7→10, js_errors at "
      "module 0); app console banner + data boot ran; T15 static-import + T16 dynamic-import "
      "fixtures PASS (assets/mod-a.js + mod-b.js loaded through the loader)."
  ),
  "missing": "import maps for bare specifiers (honest refusal recorded)",
  "next": "import map law on measured need",
  "commit": "S133",
 },
 {
  "id": "R-NEW-445",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P1",
  "fg": False,
  "title": "fetch() relative-URL resolution missing (WHATWG Fetch base-URL law): fetch('/api/config') threw 'bad url' instead of hitting the document origin",
  "evidence": (
      "LIVE z.ai trace: [WV-FETCH] FAILED err=bad url: /api/config (and /api/v1/auths/). "
      "FIX: fetch bridge resolves the spec string through resolve_url (S117 merge + scheme/"
      "root-relative/scheme-relative laws) before transport. PROOF: /api/v1/auths/ 200 (859B, "
      "guest session), /api/config 200 (1092B) on the live site."
  ),
  "missing": "",
  "next": "",
  "commit": "S133",
 },
 {
  "id": "R-NEW-446",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P1",
  "fg": False,
  "title": "fetch(url, init) headers/method ignored (WHATWG Fetch §4.1 init law): Authorization/Content-Type dropped — every authenticated-SPA request degraded",
  "evidence": (
      "z.ai bootstrap builds config={credentials:'include', headers:{Accept,Content-Type,"
      "Accept-Language}} and the app sends Bearer tokens. FIX: init.method normalized (GET only; "
      "non-GET = HONEST visible rejection, never a silent GET) + init.headers (plain-object form) "
      "→ http_get_ex (S100 client extended with per-request extra headers, RFC 7230 §3.2 field "
      "lines). PROOF: live trace shows headers: Accept=application/json Accept-Language=en-US "
      "Content-Type=application/json on every z.ai API call; /api/models 200 (287,571B) once the "
      "cookie law (R-NEW-447) supplied the session token. HONEST RESIDUE: POST body law pending "
      "(recorded as visible rejection)."
  ),
  "missing": "POST body + response Headers object",
  "next": "POST on measured corpus need",
  "commit": "S133",
 },
 {
  "id": "R-NEW-447",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P1",
  "fg": False,
  "title": "HTTP cookie store missing (RFC 6265 §5.3/§5.4): Set-Cookie never stored, Cookie never echoed — the z.ai session flow (token cookie from /api/v1/auths/ gating /api/models) returned 403",
  "evidence": (
      "MEASURED both ways with curl: /api/models 403 WITHOUT the session cookie, 200 WITH it "
      "(the app's own bootstrap comment: token must be in the cookie for models). FIX: mininet "
      "CookieJar — host-scoped store, multi Set-Cookie preserved (header map no longer collapses "
      "them), name=value before first ';' (RFC 6265 §5.2), Cookie echoed on https hops unless an "
      "explicit Cookie header exists. PROOF: live /api/models 403→200 (287,571B) after the auths "
      "hop stored token=<JWT>."
  ),
  "missing": "Domain attribute expansion, persistent cookie file, expiry semantics (session-scope documented)",
  "next": "expiry/persistence when a corpus APK needs cross-launch sessions",
  "commit": "S133",
 },
 {
  "id": "R-NEW-448",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P1",
  "fg": False,
  "title": "Unhandled promise rejections were INVISIBLE (no host rejection tracker) — a whole SPA boot chain died silently (white screen with zero error surface)",
  "evidence": (
      "z.ai boot rejections surfaced only after wiring JS_SetHostPromiseRejectionTracker → "
      "[WV-REJECT] with stack + line/column: TWO 'TypeError: value is not iterable' from the "
      "app bundle became attributable. The tracker is behavior-neutral (reports only) and "
      "permanent engine infrastructure (CONSTITUTION §37)."
  ),
  "missing": "",
  "next": "",
  "commit": "S133",
 },
 {
  "id": "R-NEW-449",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P1",
  "fg": False,
  "title": "Web-API stub family missing: PerformanceObserver/IntersectionObserver/MutationObserver/ResizeObserver/matchMedia/requestIdleCallback — z.ai's first inline telemetry script died at 'PerformanceObserver is not defined' BEFORE its payload ran",
  "evidence": (
      "FIX: web-stubs law (JS polyfill alongside the TextEncoder law): observer ctor family whose "
      "observe() delivers an entries-shaped record (getEntries/getEntriesByType/getEntriesByName → "
      "[]), matchMedia minimal MediaQueryList, requestIdleCallback over setTimeout. Honest "
      "semantics: observer registered, no metrics available. PROOF: the PerformanceObserver "
      "inline error disappeared from the live run; script executions 7→10."
  ),
  "missing": "real metrics (LCP/CLS) — recorded frontier",
  "next": "on measured need",
  "commit": "S133",
 },
 {
  "id": "R-NEW-450",
  "status": "VERIFIED_3RUN",
  "priority": "P1",
  "fg": False,
  "title": "ATOMIC INLINE-BOX law missing (CSS 2.1 §9.2.2): display:inline-block elements text-merged into the parent (never laid out lo=0, never painted) — T02 color chips and T14's 2000-node grid rendered NOTHING (the dominant general-roots divergence from the fixture suite)",
  "evidence": (
      "ROOT CAUSE (T02 WV-BOX trace): [WV-LAYOUT] div .a 500x300 lo=0 — the layout walk merged "
      "inline elements into the parent text run; inline-block boxes with backgrounds/sizes "
      "vanished. FIX: inline_block flag distinct from plain inline; horizontal RUN placement with "
      "WRAP law in layout_stack_once (line cursor re-sync on block siblings); gather_inline stops "
      "at atomic boxes; paint walk paints them; measure_w counts their outer width for "
      "shrink-to-fit parents. PROOF: T02 red/green/blue = 150000/150000/300000 px exact; T14 "
      "2000-cell grid = 196 distinct colors × 10000px; battery ALL PASS (124 stages); "
      "3-run byte-identical (c95affdefb734ffd ×3)."
  ),
  "missing": "vertical-align in mixed text+inline-block lines (approximation: run below text)",
  "next": "baseline alignment law on measured need",
  "commit": "S133",
 },
 {
  "id": "R-NEW-451",
  "status": "VERIFIED",
  "priority": "P1",
  "fg": False,
  "title": "<img> replaced-element law missing: DOM <img> had no fetch, no box, no paint (only JS new Image()/CSS background existed) — T05 fixture image invisible; klondike banner.html family affected",
  "evidence": (
      "FIX: img box from width=/height= attributes (WHATWG §4.8.3) + atomic inline-level "
      "classification (reuses R-NEW-450 run law) + paint branch: src → fetch_resource (network OR "
      "asset, one resource table) → decode_image_bytes → scaled blit (same drawImage law as the "
      "canvas blit). PROOF: T05 red PNG renders (300px wide, exact color (204,0,0); clipped at "
      "viewport bottom by the harness layout — geometry correct); klondike banner.html loads "
      "through the asset law (honest adserver failure recorded)."
  ),
  "missing": "intrinsic-size fallback (no width/height attrs), srcset, alt text paint",
  "next": "intrinsic size on measured need",
  "commit": "S133",
 },
 {
  "id": "R-NEW-452",
  "status": "VERIFIED",
  "priority": "P1",
  "fg": False,
  "title": "Inline SVG BASIC-SHAPES law missing (SVG2 §10.3/§10.4): paint_svg_content painted only <path>/<use> — <circle>/<rect>/<ellipse> rendered nothing (T06 fixture; the S132 Telegram subset measured circle/rect usage)",
  "evidence": (
      "FIX: shape geometry synthesized as EQUIVALENT PATH DATA (rect → M/H/V/Z; circle/ellipse → "
      "48-segment polygon) fed through the EXISTING svg_flatten + scanline fill — zero new raster "
      "code (REUSE-FIRST). PROOF: T06 circle fill 125,057px ≈ π·200² (125,664, viewport edge "
      "rounding), rect 14,280px ≈ 120² — exact geometry law; battery ALL PASS."
  ),
  "missing": "line/polyline/polygon primitives",
  "next": "on measured icon-set need",
  "commit": "S133",
 },
 {
  "id": "R-NEW-453",
  "status": "VERIFIED",
  "priority": "P1",
  "fg": False,
  "title": "Canvas attribute intrinsic-size law missing (WHATWG HTML §4.12.4): parsed <canvas width= height=> kept a 1x1 bitmap AND a 0x0 box — every parse-time fillRect landed on a degenerate surface (T09: draw_calls=2, ZERO pixels)",
  "evidence": (
      "ROOT CAUSE (T09 trace): [WV-CANVAS] box 1000x800 bitmap 1x1 — the JS .width= property "
      "setter sized the bitmap but PARSED attributes never did. FIX: (a) el_getContext sizes the "
      "bitmap from the attributes at FIRST context acquisition (the spec law — draws land on the "
      "real surface); (b) style walk derives the default box (300x150 fallback) when CSS is auto. "
      "PROOF: T09 fillRect magenta 120,300px (400x300 law) + arc cyan 71,200px (r=150 law, "
      "π·150²≈70,686); battery ALL PASS (canvas-game class unregressed)."
  ),
  "missing": "",
  "next": "",
  "commit": "S133",
 },
 {
  "id": "R-NEW-454",
  "status": "IMPLEMENTED",
  "priority": "P1",
  "fg": False,
  "title": "Browser DOM/URL surface family missing for module-class pages: URLSearchParams (30+ z.ai bundle sites), document.getElementsByTagName (z.ai GTM bootstrap), document.location alias (jQuery support checks)",
  "evidence": (
      "FIX: (a) URLSearchParams as a JS polyfill (WHATWG urlencoded subset: string/pair-array/"
      "record init; append/set/get/has/delete/toString/forEach; generator-based entries/keys/"
      "values + Symbol.iterator); (b) getElementsByTagName tree-walk collection (array form, "
      "lowercased tag, '*' law); (c) document.location = window.location alias (HTML §5.2) + "
      "location.protocol reflects the real scheme. PROOF: GTM inline script progressed past "
      "getElementsByTagName (new error site = the dead adserver path); jQuery progressed past "
      "the host check; T17 allSettled fixture PASS."
  ),
  "missing": "HTMLCollection live semantics (array snapshot documented)",
  "next": "on measured need",
  "commit": "S133",
 },
 {
  "id": "R-NEW-455",
  "status": "IMPLEMENTED",
  "priority": "P1",
  "fg": False,
  "title": "Browser resource-forensics instrumentation missing (S133 §4/§5/§31): no per-resource table, no stage traces, no diagnostic artifact dump",
  "evidence": (
      "FIX: (a) Impl::ResourceRecord table — every external fetch (script-exec/module-import/"
      "stylesheet/font-face/img-src/fetch) records id/url/final_url/type/status/bytes/source/"
      "consumer/error/ms, dumped to $WV_DIAG_DIR/webview_resource_trace.json when WV_DIAG=1 "
      "(gated, §31 behavior-neutrality); (b) per-script eval filenames inline-N (minified stack "
      "attribution); (c) [WEB-001]/[WV-RES]/[WV-MODULE]/[WV-FETCH]/[WV-REJECT] stage traces; "
      "(d) scripts/s133_screen_forensics.py — unique colors, entropy, row/col hashes, "
      "repeated-block PERIOD detection, white/black/grey/pattern classification."
  ),
  "missing": "first_divergence.json auto-generation from the stage table",
  "next": "fold into the battery as a diagnostic stage",
  "commit": "S133",
 },
 {
  "id": "R-NEW-456",
  "status": "BLOCKED",
  "priority": "P2",
  "fg": False,
  "title": "LIVE z.ai residual: the Svelte-5 runtime inside the minified app bundle rejects the boot ('TypeError: value is not iterable', twice, unhandled) at bundle line 7 (~48K chars) — the SPA mounts nothing and the page stays the honest white shell",
  "evidence": (
      "Full pipeline state at the residual: NETWORK PASS (200, 1 redirect, 15,727B) / HTML-DOM "
      "PASS / CSS PASS (1,436 rules + 2 fonts) / JS-LOAD PASS (module law R-NEW-444) / JS-DATA "
      "PASS (auths 200 859B, config 200 1092B, models 200 287,571B via R-NEW-445/446/447) / "
      "JS-EXEC PARTIAL (boot chain rejected inside app code) / LAYOUT-PAINT white shell. "
      "3-run byte-identical (f2169ebcaaf069ce ×3). Attribution achieved to bundle line 7 via the "
      "R-NEW-448 tracker; the failing statement is inside the minified Svelte-5 reactivity/"
      "modulepreload region — an engine iterable-shape gap OR app-internal behavior, not "
      "attributable further without per-line replay bisect. Honest BLOCKED per §36B: the exact "
      "residual is identified, recorded, reproducible; NOT claimed as a render."
  ),
  "missing": "minified-code line attribution (replay bisect) or the next engine law",
  "next": "replay-bisect the bundle (newline-split replay + per-line probes) next cycle; jquery DCL path (20s deadline interrupt at Zi, fH not-a-function) queued behind it",
  "commit": "S133",
 },
]

for e in entries:
    upsert(e)

reg["count"] = len(roots)
reg["total"] = len(roots)
with open(ROOTS, "w") as f:
    json.dump(reg, f, indent=1)
print(f"root registry: {len(entries)} S133 entries registered (total {len(roots)})")
