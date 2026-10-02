#!/usr/bin/env python3
"""SECONDARY CAMPAIGN — issue #354 progress comment: V1-V11 batch."""
import json, subprocess, sys

BODY = """
## SECONDARY CAMPAIGN — WHITE/BLACK/INCOMPLETE RENDER ROOTS — V1–V11 done/remaining

Parallel compatibility audit (F-NEW-173 investigation untouched). Directive honored: no visual issue closed on process success; every verdict now requires **real ViewTree + content root + measure + layout + authoritative draw + draw provenance + app-content pixels INSIDE the authoritative content bounds**.

### PHASE V1+V7 — FALSE-SUCCESS GATE + FRAMEBUFFER/CAPTURE (F-NEW-193 FIXED)
- **Content-bounds pixel ownership**: FrameRenderCensus now records the laid-out content-root rect; the capture classifies EVERY non-dominant pixel **inside** (AUTHORITATIVE_APP_CONTENT) vs **outside** (WINDOW_CHROME) — bounds come from the real measure/layout, zero fixed-pixel heuristics. Dominant = WINDOW_BACKGROUND; trace_overlay.png = DIAGNOSTIC_OVERLAY (separate file, S135 sha law).
- **REAL_APP_CONTENT now requires app-owned pixels INSIDE content bounds > 0** (in addition to root/measure/layout/draw/provenance). Census JSON carries `app_owned_pixels_inside_content_bounds` / `window_chrome_pixels` / `verdict_regions_law`.
- **PHASE V2**: a failed `setContentView(res)` inflation (root==0) is now `RESOURCE_INFLATION_FAILED` (census `inflation_failed` via `ActivityShadow.last_inflate_failed`, `[V2-INFLATE-FAILED]` evidence) — the old "keeping legacy default screen" silent path is GONE. A failed real APK inflation can never be a synthetic success.

### PHASE V3+V8 — ONE AUTHORITATIVE LAYOUT + RENDERER DUPLICATION (audit doc: `docs/SECONDARY_CAMPAIGN_V3_V8_AUTHORITY_AUDIT.md`)
- **Layout authority**: `LayoutInflater::measure_layout` is the ONLY layout engine reachable from real APK frames. `ViewRenderer::measure_view` = **ZERO call sites** (REFERENCE_ONLY dead code); `software_renderer.h` LayoutNode structs unused; ResourceRuntime::inflater IS the same engine; DEX onMeasure/onLayout = sub-authority/notify-only inside it (F10/R-NEW-347/21-P1-5). No two engines rewrite ViewNode geometry. Residual V3-R1 registered (F-096 one-time memoized dispatch — contractually downstream).
- **Renderer duplication**: `cmd_run` → ExecutionEngine is THE only screenshot-producing path. ApplicationRuntime (own save_screenshot) = unreachable from cmd_run → REFERENCE_ONLY; synthetic api::View = DIAGNOSTIC_ONLY (suppressed in REAL_DALVIK, verified 21-P0-3); TraceOverlay = DIAGNOSTIC_ONLY (copy-after-write, `authoritative_sha != trace_sha` by construction).

### PHASE V4 — GENERIC VIEW INFLATION (F-NEW-194 FIXED)
- Unknown short XML tags: the silent `Landroid/view/View;` leaf degradation is GONE. Generic **DEX-EXISTENCE law**: unknown tags resolve against `Landroid/{widget,view,webkit}/` + `Lcom/android/internal/widget/` by APK DEX class existence (`DexClassExistsHook`, Factory-law propagation through ResourceRuntime); non-matches recorded as EXPLICIT evidence (`[V4-TAG]` + inflater warning). No known-names list dependence for bundled platform-family classes. Wave corpus: 0 triggers (honest absence).

### PHASE V5 — IMAGE PIPELINE (F-NEW-196 FIXED)
- Explicit provenance states on every image event: **IMAGE_RESOURCE** (resid) / **IMAGE_APK_PATH** (entry path) / **IMAGE_DIRECT_PIXELS** (BitmapStore raw pixels — a valid bitmap is never dropped for lacking an APK path). Canvas drawBitmap replay stamped IMAGE_DIRECT_PIXELS. Unsupported sources keep the bounded `[P1-2-IMAGE-BLOCKED]` evidence (Forkgram r81/ni wrapper-drawable events recorded live).

### PHASE V6 — VIEW CONTEXT IDENTITY (F-NEW-195 FIXED)
- `View.getContext()` NEVER-NULL activity fallback is now **observable**: bounded per-view counter `fallback_ctx_events` + `[V6-CTX-FALLBACK]` evidence line (view/class/target). Missing ctor-captured context is an event, not a silent conversion. Wave corpus: 0 triggers.

### PHASE V9 — REUSABLE LIBRARY AUDIT (doc: `docs/SECONDARY_CAMPAIGN_V9_LIBRARY_AUDIT.md`)
7 candidates × 8 criteria (LOC removable / RAM / CPU / headless / license / semantic mismatch / integration / testability): **QuickJS KEEP** (integrated+proven), **Wuffs ADOPT-CANDIDATE** (GIF disposal — only strictly-better upstream; EXECUTED_GIFS regression set), **rlottie PENDING** (demand-gated via BitmapStore), **Skia / libarsc-ARSCLib / Yoga / Filament REJECTED** with measured reasons (law-carrier parsers, measure/spec mismatch per S132, census compose-from-scratch law, PortableGL coverage). LOC ledger: true reduction now 0 (ViewRenderer 685 LOC REFERENCE_ONLY — no-blind-delete); post-Wuffs −119 net.

### PHASE V10 — FIVE-APP VISUAL GATE (3 deterministic runs each, full stage record)
| App | SHA16 ×3 | Verdict | Class | Evidence |
|---|---|---|---|---|
| **Forkgram Classic** | `cf4c41e62ceb6557` | **REAL_APP_CONTENT** | **OBSERVED** | 31 nodes/depth 7, app_draw_ops 11, **117,133 app px INSIDE bounds**, chrome 0, 204 colors (theme bg + white cards + #85caff accents) |
| 2048 (andstatus) | `31ddd4d5b8e6d18e` | NO_ROOT | BLOCKED | `effective_content_root_()==0` — WhatsApp empty-shell class |
| Dame (blidraughts) | `b5a7a35d5fe0564b` | DEFAULT_BACKGROUND_ONLY | BLOCKED | first_missing_stage=**APP_DRAW_OPS**, 2-node tree |
| Droidify | `b5a7a35d5fe0564b` | DEFAULT_BACKGROUND_ONLY | BLOCKED | same shared-SHA class — refined attribution → **F-NEW-197** |
| OpenCalculator | `b5a7a35d5fe0564b` | DEFAULT_BACKGROUND_ONLY | BLOCKED | same APP_DRAW_OPS family |

White/black frames stay OPEN (F-NEW-197 registered): the phase-15 "shared empty-shell SHA" class is now two machine-readable states — APP_DRAW_OPS-starved root (dame/droidify/opencalc) vs NO_ROOT (game2048).

### PHASE V11 — REGRESSION
**laws130 51/51 · dooz `d602648e8e401895` ×3 · simplestopwatch `10446aaf0cd642cc` ×3 · headingcalc `be1cea9cf994b26a` ×3 · microtimer `da73010a37dd0189` ×3 · WhatsApp `31ddd4d5b8e6d18e` ×3 — BYTE-IDENTICAL, exact golden match, ZERO regressions.** All V-laws are generic semantic laws — zero package/APK/screenshot/title-specific branches.

### Registry
F-NEW-193 (V1/V2/V7 verdict+bounds law) · F-NEW-194 (V4 generic-tag law) · F-NEW-195 (V6 context-observability) · F-NEW-196 (V5 provenance states) · **F-NEW-197 (five-app white-screen frontier, P0)** — **registry 487→492 roots; root_registry.json bidirectional sync restored (recovered F-NEW-190/191/192 copies).**

### REMAINING (done/remaining scorecard)
- **Done this directive: 11/11 phases** (V1–V11) — 4 false-success mechanisms closed, 2 audit docs, 5-app gate with in-bounds proof, zero golden drift.
- **Remaining**: F-NEW-197 (exact next root: the dame/droidify/opencalc APP_DRAW_OPS view-build chain, then game2048 NO_ROOT); the deep DI-lattice family (F-NEW-169/173) gating the WhatsApp fragment-host faces; F-NEW-192 (elevation/translationZ, P2).
"""


def gh_token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None


def main():
    token = gh_token()
    if not token:
        print("NO TOKEN"); sys.exit(1)
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/354/comments",
        "-H", f"Authorization: token {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"body": BODY}),
    ], capture_output=True, text=True)
    try:
        resp = r.json()
        print("posted:", resp.get("id"), resp.get("html_url"))
    except Exception:
        print("FAIL", r.stdout[:300])


if __name__ == "__main__":
    main()
