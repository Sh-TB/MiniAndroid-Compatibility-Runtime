"""Prepared Issue #8 evidence comments for the G31–G48 typography campaign.

PERSISTENCE STATUS (honest): the sandbox reset wiped /home/z/.gh_token, so
PUSH and COMMENT are BLOCKED for this session. These payloads are final;
when a token is provided, run:

    python3 scripts/post_typography_comments.py

The poster reads the token from /home/z/.gh_token (mode 600), never prints
it, and appends the returned comment URLs to scripts/comment_urls.json.
"""
import json
import ssl
import sys
import urllib.request
import urllib.error

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"
TOKEN_PATH = "/home/z/.gh_token"
ISSUE = 8
RESULTS_PATH = "/home/z/my-project/scripts/comment_urls.json"

COMMENTS = [
    {
        "id": "G31-G32-FONT-SOURCE-RESOLUTION",
        "body": """## G31/G32 — REAL FONT SOURCE + RESOLUTION (PASS, `verified`)

Gates G31/G32 of the typography campaign closed at commit `ea51d96a` (on `d2d4469a` diagnostics).

**APK evidence (frozen EXT-01 bytes, scripts/dump_axml_attrs.py):** layout = single TextView with
`fontFamily='monospace'` (STRING), `lineSpacingMultiplier=2.0` (FLOAT 0x40000000),
`elegantTextHeight=true`, `textAppearance=@android:style/TextAppearance.Large` (0x01030042), NO
`android:textSize`; no font files bundled in the APK.

**AOSP law (frameworks/base@android-14.0.0_r50 + android-15.0.0_r2, fetched this session):**
`data/fonts/fonts.xml` L253-255: family monospace → `DroidSansMono.ttf` (byte-identical file
across API 34/35/36, SHA-256 `db19a1fdaba41cc4a2fec0330e5c15e71c6dd68a3ef074f4f28268828b45c862`).
`core/res/res/values/styles.xml` L862-864: `TextAppearance.Large` → textSize 22sp.

**ARSC config law fix (AssetManager2/ResourceTypes.cpp@android-14.0.0_r50):**
aapt2 dump ground truth — layout/activity_main variants `() res/v9.xml, (v16) res/UD.xml,
(v21) res/02.xml`. MiniAndroid bugs fixed: (1) device config `size=0` gated the ENTIRE
isBetterThan body off, (2) `apk_path_for` ignored config matching and took the first `res/`
string. Now the AOSP law picks the v16 variant (fontFamily active; elegantTextHeight lives
only in v21 which the version law never reaches — recorded).

Runtime evidence at this HEAD:
```
FONT_RESOLUTION source=SYSTEM family=monospace font=DroidSansMono.ttf (AOSP fonts.xml law)
```
Diagnostics committed: scripts/dump_axml_attrs.py, scripts/ttf_metrics.py, scripts/typography_measure.py,
tests/font_pipeline_probe.cpp, tests/probe_arsc_layout.cpp, docs/evidence/G31_FONT_SOURCE.md.
BEFORE numbers preserved: docs/evidence/external_hello_golden/typography_before.json.""",
    },
    {
        "id": "G36-G37-G46-G47-LAWS",
        "body": """## G36/G37/G46/G47 — FONT METRICS, BASELINE, TEXT SIZE, LINE SPACING LAWS (PASS, `verified`)

Commits `598e2432` (FontMetrics+line-box law), `b9e6e66f` (TextAppearance law),
`98794ed0` (line-spacing plumbing). Every constant is transferred AOSP law — zero tuned values.

- **G46 (the primary blocker)**: `TextAppearance.Large` was parsed by NOTHING → renderer fell
  back to 14dp×2.625=36.75px with a proportional face. Law chain now implemented and logged:
  styles.xml@android-14 L862-864 (22sp) → TextView.java L4346/L4470 (appearance applies absent
  explicit textSize) → TypedValue.complexToDimensionPixelSize rounding →
  `[G46-TEXTAPPEARANCE] TextAppearance.Large textSize=22sp -> 58px (scaledDensity=2.625)`.
- **G36/G37**: Paint.FontMetrics (ascent/descent = hhea-scaled, ints CEILed per Paint.cpp JNI;
  top/bottom = OS/2 win extents; leading = bottom-descent+top-ascent) and StaticLayout.out()
  L1236-1259 per-line law (first line above=fm.top with includeFontPadding, extra=(below-above)*
  (mult-1)+add for non-last lines, v += (below-above)+extra). Ad-hoc "+5% leading" and
  "size×1.2" laws REMOVED.
- **G47**: lineSpacingMultiplier=2.0 (FLOAT bits), lineSpacingExtra, includeFontPadding,
  elegantTextHeight parsed into ViewShadow node state and plumbed into BOTH the measure pass
  and the render walk (single source of truth — fonts::layout_text).

Measured BEFORE → AFTER → reference (1080-scale unless noted):
- text block width: 0.3843 → 0.6231 → 0.6433
- text block height: 0.0906 → 0.2458 → 0.2474
- line spacing (top-to-top): 46px → 138px → 137–144px (middle gaps within 1px)
- font: DejaVu Sans (proportional, family dropped) → Droid Sans Mono @58px → Droid Sans Mono

Known residual recorded (NOT tuned away): the reference's first-line baseline gap is +6px vs
MiniAndroid (device fm.top≠fm.ascent behavior; MiniAndroid's top==ascent for this font because
usWinAscent 1901 ≈ hhea 1900).""",
    },
    {
        "id": "G48-GOLDEN-REGRESSION",
        "body": """## G48 — TYPOGRAPHY GOLDEN: GOLDEN-01 PASSES 9/9 STATIC CHECKS (`visually-proven`)

Commit `f2717ab6`. Evidence: docs/evidence/G48_TYPOGRAPHY_GOLDEN.md + external_hello_golden/
typography_golden.json + miniandroid_typography.png + font_pipeline_probe_58px.txt.

Comparator `scripts/compare_ext01_typography.py` (Rule 10 — per-quantity, never one number;
dynamic device values (ANDROID_ID/version/API) excluded by design, static typography fully
validated):

```
PASS  background identical (black)
PASS  ink present
PASS  4-line band structure
PASS  horizontal centering within 3%
PASS  vertical centering within 6%
PASS  text block width ratio within 10%    (3.14%)
PASS  text block height ratio within 10%   (0.64%)
PASS  line spacing ratio within 10%        (1.58%)
PASS  monospace advance ratio within 10%   (3.03%)
GOLDEN-01 TYPOGRAPHY GOLDEN: PASS (9/9 static checks)
```

Determinism (Rule 12): 3 independent runs → PNG byte-identical, SHA-256
`142238fd92b69e11d3407526de95cad29bf46e3f4191767d09a24379fbe0bbf2` (1080×1920).

Regression battery at the same HEAD — `scripts/run_test_battery.sh` extended to 16 stages,
**BATTERY GATE: ALL PASS (16 stages)**: build; semantic 14+25+57=96/96; MUTF-8 14/14;
helloworld_golden 26/26; tictactoe_golden 8/8; EXT-01 run + typography golden 9/9; corpus
fetch (hash-verified) + runs: simplestopwatch / gmdice / microtimer all SUCCESS.

Gate discipline: G43 (non-ASCII), G44 (shaping), G45 (bidi), G38 (fallback) are
`implemented; not exercised by primary fixture` — implemented in the live pipeline
(FriBidi→HarfBuzz→FreeType) but NOT claimed as compatibility; external fixtures queued.
Status claims: researched / observed / tested / runtime-proven / visually-proven as marked
per gate in G32_G48_TYPOGRAPHY_GATES.md.""",
    },
]


def api_request(url, method="GET", payload=None):
    with open(TOKEN_PATH, "r", encoding="utf-8") as fh:
        token = fh.read().strip()
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "miniandroid-campaign-evidence")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace").replace(token, "<token>")
        return e.code, {"error": detail}
    except Exception as e:
        return 0, {"error": f"{type(e).__name__}: {e}"}


def main():
    status, me = api_request("https://api.github.com/user")
    if status != 200:
        print(f"AUTH_VERIFY_FAILED: HTTP {status}")
        return 1
    login = me.get("login")
    print(f"GitHub authentication: SUCCESS (login={login})")
    try:
        results = json.load(open(RESULTS_PATH)) if RESULTS_PATH else {}
    except Exception:
        results = {}
    if isinstance(results, list):
        results = {"comments": results}
    results.setdefault("comments", [])
    ok = True
    for c in COMMENTS:
        status, resp = api_request(
            f"{API}/issues/{ISSUE}/comments", method="POST",
            payload={"body": c["body"]})
        if status == 201:
            url = resp.get("html_url", "")
            cid = resp.get("id")
            print(f"POSTED {c['id']}: {url} (comment id {cid})")
            results["comments"].append({"id": c["id"], "comment_id": cid,
                                        "url": url})
        else:
            ok = False
            print(f"FAILED {c['id']}: HTTP {status}: {str(resp)[:200]}")
    if RESULTS_PATH:
        json.dump(results, open(RESULTS_PATH, "w"), indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
