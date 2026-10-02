#!/usr/bin/env python3
"""SECONDARY CAMPAIGN V-waves — registry append + sync + worklist regen."""
import json, sys
from pathlib import Path

CANON = Path("/home/z/my-project/canonical/root_cause_registry.json")
ROOT_REG = Path("/home/z/my-project/root_registry.json")

NEW = [
    {
        "id": "F-NEW-193",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "visual-verdict/frame-truth",
        "title": "SECONDARY CAMPAIGN V1/V2/V7 false-success family: the verdict chain could not (a) separate pixels INSIDE the authoritative content bounds from window chrome outside them, (b) distinguish a FAILED setContentView(res) inflation from an absent one (failed inflation silently kept the legacy default screen), and (c) carried no per-region capture record (chrome/background/content/overlay). A status-bar band or stray decor pixels inside a valid-root frame could ride into REAL_APP_CONTENT.",
        "law": "V1/V7: verdict requires REAL ViewTree reached + content root identified + measure executed + layout executed + authoritative draw executed + app-owned pixels INSIDE the laid-out content-root rect > 0; non-dominant pixels outside the content rect = WINDOW_CHROME and can never count as app content; dominant = WINDOW_BACKGROUND; trace_overlay.png = DIAGNOSTIC_OVERLAY (separate file, S135 sha law). V2: a real APK inflation that produces no root sets RESOURCE_INFLATION_FAILED (ActivityShadow.last_inflate_failed -> census inflation_failed) — the legacy default screen is NOT app content and never upgrades the verdict.",
        "evidence": "FrameRenderCensus + content_bounds (l,t,r,b) from the laid-out root node; capture loop classifies inside/outside per pixel (no fixed heuristics — bounds come from the real measure/layout). Forkgram census: verdict=REAL_APP_CONTENT, app_owned_pixels_inside_content_bounds=117133, window_chrome_pixels=0, bounds valid; goldens dooz d602648e8e401895 / ssw 10446aaf0cd642cc / headingcalc be1cea9cf994b26a / microtimer da73010a37dd0189 / whatsapp 31ddd4d5b8e6d18e x3 BYTE-IDENTICAL (pixel-neutral laws); laws130 51/51.",
        "fix": "execution_engine.h census fields inflation_failed + content_bounds_valid/l/t/r/b; execution_engine.cpp stage_render_frame_impl records root laid-out rect + consumes ActivityShadow.last_inflate_failed; stage_capture_output RESOURCE_INFLATION_FAILED verdict + region-classified census JSON (window_chrome_pixels, window_background_px, app_owned_pixels_inside_content_bounds, verdict_regions_law); android_shadows.cpp inflate failure/success markers [V2-INFLATE-FAILED].",
        "wave": "SECONDARY-V1V2V7",
    },
    {
        "id": "F-NEW-194",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "inflation/generic-view-identity",
        "title": "V4 generic-tag silent degradation: ANY unknown short XML tag silently inflated as a generic Landroid/view/View; leaf — real class identity lost (a platform/custom ViewGroup became a content-less leaf; container measure/layout semantics dropped) with NO evidence the degradation happened.",
        "law": "AOSP LayoutInflater.createViewFromTag: a short tag is a platform widget name. Generic DEX-EXISTENCE law: unknown short tags resolve against Landroid/{widget,view,webkit}/ and Lcom/android/internal/widget/ BY APK DEX CLASS EXISTENCE (is_dex_defined_class — the bundled dex is the authority); when nothing matches, the generic-View degradation is recorded as EXPLICIT evidence (inflater warning + [V4-TAG] line), never silent. No hardcoded widget list extension needed for bundled platform-family classes.",
        "evidence": "LayoutInflater::inflate_element V4 block + DexClassExistsHook (Factory-law propagation through ResourceRuntime: set_dex_class_exists_hook + apply on ensure_loaded); engine hook install at stage entry. Wave corpus: 0 unknown-tag triggers (all tags KNOWN-mapped or dotted — honest absence); hook verified installed on every inflater recreation path.",
        "fix": "layout_inflater.h DexClassExistsHook + resource_runtime.h pass-through (Factory law) + execution_engine.cpp install; inflate_element resolution + evidence block.",
        "wave": "SECONDARY-V4",
    },
    {
        "id": "F-NEW-195",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "context-identity/observability",
        "title": "V6 silent context-fallback conversion: View.getContext() with a MISSING constructor-captured Context silently answered the activity context — an identity conversion that can surface much later as white UI (View->Context->Resources->Theme->Drawable chain) with ZERO evidence the fallback fired.",
        "law": "Observable-identity law: the NEVER-NULL fallback to the activity context is recorded per-view (bounded counter ViewNode.fallback_ctx_events) with an explicit [V6-CTX-FALLBACK] evidence line naming the view, its class and the fallback target; the ctor-captured path keeps the real heap-class descriptor (F-NEW-184).",
        "evidence": "android_shadows.cpp getContext block: bounded counter + evidence line before the activity-context return; Wave corpus runs: 0 fallback triggers recorded (honest absence — all queried views had ctor-captured contexts); counter available in ViewNode for census consumers.",
        "fix": "ViewNode.fallback_ctx_events field + getContext evidence block.",
        "wave": "SECONDARY-V6",
    },
    {
        "id": "F-NEW-196",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "image-pipeline/provenance",
        "title": "V5 provenance states were IMPLICIT: the three pixel-source classes (resource-resolved, APK-path, raw pixels) existed in the pipeline but carried no canonical name in the provenance record — a bitmap dropped for lacking an APK path could not be told apart from a resource image in evidence.",
        "law": "Every image provenance event carries ONE explicit state: IMAGE_RESOURCE (resid != 0), IMAGE_APK_PATH (entry path), IMAGE_DIRECT_PIXELS (raw BitmapStore pixels — canvas replay/decoders; a valid bitmap is NEVER dropped merely for lacking an APK path; unsupported sources emit the bounded [P1-2-IMAGE-BLOCKED] evidence).",
        "evidence": "gfx_provenance.h record_image derives provenance_state from (resid, path, pixel-presence); record_canvas_bitmap stamps IMAGE_DIRECT_PIXELS; P1-2 setter contract (F-NEW-185b) unchanged. Forkgram evidence: [P1-2-IMAGE-BLOCKED] wrapper-drawable events recorded honestly (r81/ni wrappers).",
        "fix": "gfx_provenance.h provenance_state field (derived in-record, no signature churn).",
        "wave": "SECONDARY-V5",
    },
    {
        "id": "F-NEW-197",
        "status": "REGISTERED",
        "priority": "P0",
        "layer": "white-screen family",
        "title": "V10 five-app gate white/black frontier (fresh census attribution): Dame (blidraughts), Droidify, OpenCalculator all reach auth_root_valid + measure + layout + draw-walk but stop at first_missing_stage=APP_DRAW_OPS with a 2-node visited tree (root+1 child) — the app's real view-building never reaches the authoritative walk. game2048 stops earlier: NO_ROOT (effective_content_root_()==0, setContentView never lands). This refines the phase-15 'shared empty-shell SHA' class into two machine-readable states: APP_DRAW_OPS-starved root (dame/droidify/opencalc, SHA b5a7a35d5fe0564b shared) vs NO_ROOT (game2048, SHA 31ddd4d5b8e6d18e = WhatsApp empty-shell class).",
        "law": "No-fake-success: DEFAULT_BACKGROUND_ONLY / NO_ROOT verdicts stay OPEN until real app-content evidence exists; next attack = trace the app-side view construction chain (dame/droidify/opencalc: why the built tree never gains app ops; game2048: why setContentView landed no root).",
        "evidence": "scripts/v10_five_app_gate.py — 5 apps x3 deterministic runs: forkgram cf4c41e62ceb6557 REAL_APP_CONTENT x3 (OBSERVED, 117133 app px in-bounds, 204 colors), game2048/dame/droidify/opencalc BLOCKED with census first_missing_stage; results /tmp/v10/v10_results.json.",
        "fix": "OPEN — next-root material (V3-R1 F-096 one-time dispatch containment + app-side view-build chains queued).",
        "wave": "SECONDARY-V10",
    },
]

def load(p):
    d = json.loads(p.read_text())
    return d, (d["roots"] if isinstance(d, dict) else d)

for path in (CANON, ROOT_REG):
    if not path.exists():
        print(f"skip missing {path}")
        continue
    d, roots = load(path)
    have = {r.get("id") for r in roots}
    added = 0
    for n in NEW:
        if n["id"] not in have:
            roots.append(n)
            added += 1
    if isinstance(d, dict):
        d["roots"] = roots
        d["total"] = len(roots)
        d["total_roots"] = len(roots)
        from collections import Counter
        d["status_counts"] = dict(Counter(r.get("status", "?") for r in roots))
        d["generated"] = "2026-10-02T00:00:00Z"
    path.write_text(json.dumps(d, indent=1) if isinstance(d, dict) else json.dumps(roots, indent=1))
    print(f"{path}: +{added} -> {len(roots)} roots")

# root_registry.json shape check (may be a list at top level)
d2 = json.loads(ROOT_REG.read_text())
print("root_registry top-level:", type(d2).__name__,
      len(d2) if isinstance(d2, list) else list(d2.keys())[:6])
