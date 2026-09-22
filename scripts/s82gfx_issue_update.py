#!/usr/bin/env python3
"""S82-GFX-REVOLUTION — GitHub issue updates (comments only, no body
rewrites of other agents' content). Token: one-shot in-memory read from
.secrets/gh_token; NEVER logged, never committed (§ law)."""
import json
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = open("/home/z/my-project/.secrets/gh_token").read().strip()


def comment(issue, body):
    url = f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"
    data = json.dumps({"body": body}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "miniandroid-s82gfx",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())
    print(f"#{issue} commented -> {out.get('html_url')}")


C229 = """## S82-GFX-REVOLUTION — first-divergence results (decoder/ImageView EXONERATED; new root cause F-NEW-158 FIXED)

Provenance instrument (`MINIANDROID_GFX_PROVENANCE`, §6 evidence-bit chain) + golden fixture ladder (§5, aapt2-linked real resources):

| fixture | asserts | verdict @ HEAD |
|---|---|---|
| l1_quadrant | RGBA PNG quadrants r/g/b/k + alpha checker → screenshot | PASS |
| l2_colortypes | PNG color types 0/2/3/4/6 + palette tRNS | PASS (1103 unique colors on screen) |
| l3_density | ARSC config pick mdpi..xxxhdpi + density scale | PASS (xxhdpi-v4 selected, scaled) |
| l4_xmldrawables | shape/gradient/layer-list/selector bg | PASS after F-NEW-158 fix |
| l0_solid | programmatic ColorDrawable/TextView/Button | PASS after F-NEW-158 fix |
| l5_canvas | drawRect fill/stroke + clip + path + text | PASS |
| l6_glsurface | GLSurfaceView clear color | FAIL (documented F-NEW-157 frontier) |

**Reading per §6 law:** `IMAGE_DECODED_VS_RENDERED_GAP` is NOT in the decoder, NOT in density selection, NOT in the ImageView→Canvas path — all proven to pixels. The proven graphics root cause was **F-NEW-158 PROGRAMMATIC-BACKGROUND-DROP** (setBackground(Drawable)/setBackgroundResource(resid) silently dropped; resid parked in `image_resource_id`), now ROOT_CAUSED_FIXED with regression 26/26 + pixel goldens 24/24 exact.

Canonical docs: `docs/knowledge/graphics/` + `docs/audit/GRAPHICS_GAP_MATRIX.json`. Fanout probe re-ran real titles with the fix (GAME-004 unique colors 111→201; lifecycle-crashed titles unaffected — graphics fixes cannot reach F-NEW-156 unwinds, per §25 order law)."""

C227 = """## S82-GFX-REVOLUTION — F-NEW-156 sub-cluster re-traced: F-NEW-159 (null framework receivers)

Fanout probe re-ran the mandatory + app set at HEAD with pixel provenance. Exact NPE signatures behind the APP BOUNDARY unwind (crash-family evidence, `run/s82gfx/fanout/*.log`):

- `Lj/u;.b` → `Ljava/lang/NullPointerException;` **LocaleList.toLanguageTags on a null object reference** (TimeLimit MAND-002, MainActivity.onCreate)
- **WindowInsetsController.setSystemBarsAppearance on a null object reference** (TimeLimit MAND-002; APP-001 family)

Registered as **F-NEW-159 NULL-FRAMEWORK-RECEIVER NPE** (sub-cluster of this family; fanout ⊂ the 35 titles). Candidate law attack: shadow `LocaleList` (Configuration chain) + `WindowInsetsController` (Window chain) per AOSP semantics, then regression this fanout subset. Graphics-layer fixes (F-NEW-158, also landed this wave) correctly do NOT unlock these titles — lifecycle first (§25)."""

C24 = """## S82-GFX-REVOLUTION progress (wave 3 under this umbrella)

- Pixel provenance instrument shipped: `MINIANDROID_GFX_PROVENANCE` — per-image evidence-bit chain (ASSET_FOUND→…→SCREENSHOT_CAPTURED) + per-frame census; Git-friendly JSON.
- Golden fixture ladder L0..L6 built (real aapt2 resources, deterministic): 6/7 PASS at HEAD; l6 GL = documented F-NEW-157 frontier.
- **F-NEW-158 PROGRAMMATIC-BACKGROUND-DROP root-caused + fixed** (first divergence: DRAW_CALLED=0 at bg stage; two concrete defects in setBackground(Drawable)/setBackgroundResource(resid)). Regression: foundation battery 26/26 rc=0 + pixel goldens 24/24 exact.
- **F-NEW-159 NULL-FRAMEWORK-RECEIVER NPE registered** (LocaleList/WindowInsetsController null receivers → onCreate unwind; F-NEW-156 sub-cluster, ×2 re-traced).
- Graphics family fingerprint scan of the 41 executed APKs → `docs/corpus/s82/graphics_families.json` (13 families; streaming/hash-cached scan tool).
- Canonical outputs: `docs/knowledge/graphics/{GRAPHICS_PIPELINE,GRAPHICS_ROOT_CAUSES,PIXEL_PROVENANCE,GRAPHICS_FIX_FANOUT}.md` + `docs/audit/GRAPHICS_GAP_MATRIX.json` (complements, not duplicates, this index).
- Honest counters unchanged except evidence: EXECUTED 41, RENDERED ladder-level proof gained on fixtures; GAME-004 palette delta recorded in title record (111→201 unique colors) — no status inflation, no auto-L5."""


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "229"):
        comment(229, C229)
    if which in ("all", "227"):
        comment(227, C227)
    if which in ("all", "24"):
        comment(24, C24)


if __name__ == "__main__":
    main()
