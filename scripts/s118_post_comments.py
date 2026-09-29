#!/usr/bin/env python3
"""S118 — post the complete-the-incomplete wave report to GitHub (English only)."""
import json, os, urllib.request

TOKEN = open('/tmp/.gh_token').read().strip()
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'

def gh(path, body=None, method='GET'):
    url = f'https://api.github.com/repos/{REPO}/{path}'
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'Bearer {TOKEN}')
    req.add_header('Accept', 'application/vnd.github+json')
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

BODY = """## S118 — COMPLETE-THE-INCOMPLETE wave (Telegram deprioritized per directive)

Directive: stop Telegram work for now; **finish every incomplete app and game** with the
standing rules (generic laws only — no per-app patches), then report. This wave shipped
**11 generic laws** in the WebView/HTML5 engine, zero package checks.

### New laws (S118)

| # | law | spec | what it fixed |
|---|-----|------|---------------|
| 1 | **QuickJS job pump** | embedder contract | async/await continuations drain at every quiescence point (script end, DOMContentLoaded, per tick). Without an explicit drain **no promise ever resumed** — every async app stalled silently |
| 2 | **fetch() + Response** | WHATWG Fetch | real HTTPS GET over the S100 NET-001 OpenSSL client; Response.status/ok/url/text()/json() |
| 3 | **crypto.subtle.digest + TextEncoder/TextDecoder** | WebCrypto / Encoding | OpenSSL EVP SHA-1/256/384/512; UTF-8 byte codecs |
| 4 | **SVG shape geometry rect** | SVG2 SVGGeometryElement | getBoundingClientRect() on path/rect/circle/… answers the stroke-inclusive bbox in viewport coords (viewBox affine == the S117 paint affine) — zero-box shapes used to answer garbage |
| 5 | **SVG intrinsic ratio** | SVG2 §7.2 | auto width + definite height → width = height × viewBox ratio |
| 6 | **flex-direction defaults to row** | CSS Flexbox §4 | the engine read a missing direction as column — every `display:flex` container stacked on the wrong axis |
| 7 | **justify-content:center axis law** | CSS Flexbox §9.2 | the free space shift moves the MAIN axis (X for rows) — it was cross-wired to Y |
| 8 | **flex cross-axis stretch** | CSS Flexbox §9.4.4 | auto-height row members fill a definite cross size (align-items default) |
| 9 | **invalid at computed-value time** | CSS Custom Properties §3.1 | undefined `var()` with no fallback → width:auto/shrink — never the containing-block size |
| 10 | **:nth-child family** | CSS Selectors §6.6.5 | first/last/nth/nth-last-child, full an+b grammar (odd/even/integers) |
| 11 | **forced synchronous layout** + SVG stroke-width CSS-length resolution + box-shadow calc() token balance + Gaussian-ish shadow falloff + element-subtree querySelector scoping | HTML reflow / SVG2 / CSS Backgrounds §6.1 | geometry reads before first paint run the pipeline; stroked icons no longer hairline; glows fade like the spec model |

### Results (honest labels)

- **weather (org.asafonov.weather)** — was NEAR_BLANK → **EXECUTED + LIVE NETWORK FETCH**:
  the app signed its request (TextEncoder → crypto.subtle.digest SHA-256 → key/time/hash URL
  params), fetched `https://isengard.su/api/v1/weather/?place=…` over real TLS, got **HTTP 200
  with 7023 bytes**, and rendered the **city name "Moscow" from the live API response** —
  the first real HTTP round-trip inside the HTML5 engine.
  Evidence: [weather_moscow_live.jpg](../blob/main/evidence/s118_complete/weather_moscow_live.jpg) (3.9 KB).
  Frontier (open, honest): the forecast rows (hourly/daily lists) still do not paint —
  next wave.
- **accelerace** — was blank/stub → **RENDERED (scene)**: centered road strip, street-light
  dots, score header — the whole scene now lays out through laws 5–9.
  Evidence: [accelerace_scene.jpg](../blob/main/evidence/s118_complete/accelerace_scene.jpg) (6.6 KB).
  Frontier (open, honest): the car's yellow stroke layer paints (14.9M px verified in the
  surface) but is still not visible in the captured frame — a stacking/surface subtlety
  remains; car animation next wave.
- **mykanji** — full GUI re-verified at the new laws; the answer buttons lay out
  flex-correct now. 3 native-side errors remain (appcompat SupportMenuInflater XML-pull
  NPE — native frontier, not a WebView regression).
  Evidence: [mykanji_fullgui.jpg](../blob/main/evidence/s118_complete/mykanji_fullgui.jpg) (15 KB).
- **Gates**: ballbreak `25e72190…` and dooz `84c6d4a5…` **byte-identical** — the native
  path is untouched. blockbuster/mykanji images re-baselined by the corrected CSS laws
  (blockbuster gate evidence: [blockbuster_gate.jpg](../blob/main/evidence/s118_complete/blockbuster_gate.jpg)).

Commit: 09f5000f. All images ≤ 15 KB, English only, PPM stays off GitHub.
"""

for num in (353, 354):
    gh(f'issues/{num}/comments', {'body': BODY}, 'POST')
    print(f'posted comment on #{num}')
print('done')
