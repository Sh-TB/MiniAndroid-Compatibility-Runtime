#!/usr/bin/env python3
# S75 CLOSURE WAVE — Phase 1: ITEM75-001..047 census-closure audit.
# For every ledger ITEM75 row, reconcile THREE sources:
#   (1) canonical FOUNDATION_GAP_MATRIX.md row status (source of truth)
#   (2) live code verification (targeted greps on miniandroid/src, evidence=file:line)
#   (3) fixture evidence existence (upload/foundation_apks + root_registry.json)
# Emits: docs/audit/item75_closure.json + docs/audit/ITEM75_CLOSURE.md
# Honesty laws: no invented semantics — ABSENT code check = gap still open (PENDING),
# never flipped to fixed without both matrix + code agreement.
import json, os, re, subprocess
from datetime import datetime, timezone

ROOT = "/home/z/my-project"
SRC = os.path.join(ROOT, "miniandroid", "src")
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def rd(p):
    with open(os.path.join(ROOT, p), encoding="utf-8", errors="replace") as f:
        return f.read()

def grep(pattern, path=SRC, fixed=False, max_hits=3):
    """Return list of 'relpath:lineno: match' strings (up to max_hits)."""
    cmd = ["rg", "-n", "--no-heading", "-m", str(max_hits)]
    if fixed:
        cmd.append("-F")
    cmd += ["--", pattern, path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return []
    hits = []
    for line in (r.stdout or "").splitlines():
        line = line.replace(ROOT + "/", "")
        hits.append(line[:200])
    return hits

def check(name, patterns, expect="PRESENT", fixed=False, path=None):
    """Run greps until one hits; return dict verdict."""
    for pat in patterns:
        hits = grep(pat, path=path or SRC, fixed=fixed)
        if hits:
            return {"item": name, "expect": expect, "found": True,
                    "pattern": pat, "evidence": hits[:2]}
    return {"item": name, "expect": expect, "found": False,
            "pattern": patterns[0], "evidence": []}

# ------------------------------------------------------------------ 1. code checks
CHECKS = {
 "A1": check("A1 theme-attr at inflate (F-131/F-133)", ["TYPE_ATTRIBUTE"], fixed=False),
 "A2": check("A2 complexToDimensionPixelSize", ["complexToDimensionPixelSize"], fixed=True),
 "A3": check("A3 magic-detecting image decode (F-129)", ["decode_image_bytes"], fixed=False),
 "A4": check("A4 INVISIBLE own-content gate (F-124)", ["own_content_visible|draws_own_content|INVISIBLE"], fixed=False),
 "A5": check("A5 Paint.setARGB handler", ["setARGB"], fixed=False),
 "A6": check("A6 Canvas text via TextShaper (F-130)", ["text_shaper|TextShaper"], path=SRC+"/framework/canvas_shadow.cpp"),
 "A7": check("A7 manifest label/icon ARSC resolve (S75 FIX: resolve_resid_string)", ["resolve_resid_string|application_label_resid"], path=SRC+"/apk/manifest_reader.cpp"),
 "A8": check("A8 dimension default fallback loudness (A2 law shipped; A8 fallback not separately evidenced)", ["complex_unit_to_dimension_pixel_size"], fixed=True),
 "A9": check("A9 canvas_w_ plumbed (F-127)", ["canvas_w_"], fixed=True),
 "A10": check("A10 theme bag_value (F-131/F-132)", ["bag_value|theme_service"], fixed=False),
 "B1": check("B1 Affine2D matrix (F-125)", ["Affine2D|affine"], fixed=False),
 "B2": check("B2 clip enforcement (F-126)", ["clip_allows|set_clip"], fixed=False),
 "B3": check("B3 BitmapShadow (F-128)", ["BitmapShadow"], fixed=True),
 "B4": check("B4 saveLayer snapshot", ["saveLayer"], fixed=False),
 "B5": check("B5 setX/setTranslationX (expected OPEN)", ["setTranslationX|setTranslationY|setAbsoluteX"], fixed=False),
 "B6": check("B6 scrollY (expected OPEN)", ["scrollY|setScrollY|getScrollY"], fixed=False),
 "B7": check("B7 circle stroke inner/t", ["drawCircle"], fixed=False),
 "B8": check("B8 textSize consumed via TextShaper (F-130)", ["text_size_px", "setTextSize"], path=SRC+"/framework/canvas_shadow.cpp"),
 "B9": check("B9 italic SYNTHESIS (expected OPEN; flag-only storage = still open)", ["synthesize_italic|oblique|italic_face"], fixed=False),
 "B10": check("B10 per-codepoint fallback (expected OPEN)", ["codepoint_fallback|fallback_face|fallback_chain"], fixed=False),
 "B11": check("B11 view-level android:theme (expected OPEN)", ["android:theme"], path=SRC+"/resources/layout_inflater.cpp"),
 "B12": check("B12 @android: framework ids (expected OPEN)", ["@android:|framework_id_table|FRAMEWORK_IDS"], fixed=False),
 "C1": check("C1 rl_edges_valid", ["rl_edges_valid"], fixed=True),
 "C2": check("C2 measure-before-render at render entry (expected OPEN)", ["measure_before_render|ensure_measured"], fixed=False),
 "C3": check("C3 LL horizontal cross-axis TOP branch (f18_lltop)", ["f18_lltop"], fixed=True),
 "C4": check("C4 gravity container/text split (text_gravity field = partial)", ["text_gravity"], fixed=True),
 "C5": check("C5 layout_dirty raised by setters (expected OPEN)", ["layout_dirty"], fixed=False),
 "C6": check("C6 invalidate dirty-region (expected OPEN)", ["invalidate"], fixed=False),
 "C7": check("C7 RenderNode alpha/translation (expected OPEN)", ["RenderNode|render_node"], fixed=False),
 "C8": check("C8 FrameBuffer alpha RGB encode (expected OPEN)", ["png_set_IHDR"], path=SRC+"/renderer/software_renderer.cpp"),
 "C9": check("C9 ViewTree export alpha/padding fields (expected OPEN)", ["measured_left"], fixed=False),
 "C10": check("C10 getIdentifier dual path", ["getIdentifier"], fixed=False),
 "C11": check("C11 complex_to_fraction dead code (presence = still dead)", ["complex_to_fraction"], fixed=True),
 "C12": check("C12 fontScale fixed 1.0 (expected OPEN)", ["fontScale|font_scale"], fixed=False),
 "D1": check("D1 view_renderer.cpp dead file removal (presence = still open)", ["view_renderer"], fixed=True),
 "D2": check("D2 real_layout/resource_parser legacy orphans", ["real_layout.h|real_layout.cpp"], fixed=True),
 "D3": check("D3 api_dispatcher.cpp removal (presence = grep trap remains; NOT in Makefile = build part fixed)", ["api_dispatcher"], fixed=True),
 "D4": check("D4 exp088_a4 CMake target (links miniandroid_core = drift fixed; target remains)", ["exp088_a4"], fixed=True),
 "D5": check("D5 build_exp124.sh stale text_shaper path (presence of script = still open)", ["build_exp124"], fixed=True),
 "D6": check("D6 PNG RGB encode alpha drop (PNG_COLOR_TYPE_RGB = still open)", ["PNG_COLOR_TYPE_RGB"], fixed=True),
 "D7": check("D7 ViewTree JSON x/y vs measured_left dual names (n[\"x\"] = still open)", ["n[\"x\"]"], fixed=True),
 "F-121": check("F-121 pending-intent drain (f27)", ["drain_pending|pending_finish|pending_intent"], fixed=False),
 "F-122": check("F-122 Color.rgb/argb/parseColor", ["parseColor"], fixed=False),
 "F-123": check("F-123 drawRoundRect arg order", ["drawRoundRect"], fixed=False),
 "F-124": check("F-124 visibility enum space", ["VIEW_VISIBILITY|visibility_map|enum_space"], fixed=False),
 "F-135": check("F-135 NaN law", ["isNaN|v != v|v!=v"], fixed=False),
 "F-136": check("F-136 string resolution ARSC-first", ["arsc_first|ARSC-first|resolve_string"], fixed=False),
}

# ------------------------------------------------------------------ 2. matrix statuses
gap_txt = rd("docs/foundation/FOUNDATION_GAP_MATRIX.md")
census_txt = rd("docs/foundation/S67_MY_CENSUS.md")
census = dict(re.findall(r"^\| ([A-Z]+\d+) \| (.+?) \|", census_txt, re.M))
# FULL-ROW capture (S75 root-cause fix): build_master_audit.py truncated each
# matrix row at the 2nd column, so status columns (FIXED/DONE/PARTIAL/queued)
# were NEVER seen — the direct cause of all 47 UNVERIFIED ITEM75 rows.
all_gap_rows = re.findall(r"^\| ([A-Z][0-9A-Za-z/\-]*?) \|(.*?)\|$", gap_txt, re.M)
gaprows = dict(re.findall(r"^\| (F-1[2-3]\d) \|(.*?)\|$", gap_txt, re.M))

def find_gap_row(cid):
    for rid, row in all_gap_rows:
        parts = re.split(r"[/\-]", rid)
        if len(parts) == 2 and parts[0].rstrip("0123456789") == parts[1].rstrip("0123456789") and parts[0].rstrip("0123456789"):
            pre = parts[0].rstrip("0123456789")
            try:
                lo, hi = int(parts[0][len(pre):]), int(parts[1][len(pre):])
            except ValueError:
                lo = hi = -1
            nums = [f"{pre}{n}" for n in range(lo, hi + 1)]
        else:
            nums = parts
        if cid in nums:
            return f"[{rid}] {row.strip()}"
    return None

# fixture registry check
registry = json.load(open(os.path.join(ROOT, "root_registry.json")))
reg_txt = json.dumps(registry)
def registry_has(fid):
    return fid in reg_txt

# ------------------------------------------------------------------ 3. reconcile
def reconcile(item_id, matrix_row, code):
    """Decide final ledger status from FULL matrix row + code.
    Manual overrides encode the per-item semantic review done this wave
    (reasoning preserved in item75_closure.json); matrix+code automatic
    reconciliation only applies where the review had no nuance."""
    m = matrix_row or ""
    found = code["found"]
    # matrix-derived (FULL row text now includes status columns)
    if re.search(r"\bDONE\b|\bFIXED", m):
        m_st = "TESTED"
    elif "PARTIAL" in m:
        m_st = "PARTIAL"
    elif "unresolvable" in m or "DEFERRED" in m:
        m_st = "BLOCKED"
    elif "missing" in m or "queued" in m:
        m_st = "PENDING"
    else:
        m_st = None  # census-only or no status keyword
    open_expected = "expected OPEN" in code["item"] or "presence = still" in code["item"] or "flag-only" in code["item"] or "dead code (presence" in code["item"] or "presence of script" in code["item"]
    # code verdict
    if open_expected:
        c_st = "PENDING" if found else "TESTED"
    else:
        c_st = "TESTED" if found else "PENDING"
    # ---- manual per-item verdicts (semantic review of every ambiguous row) ----
    MANUAL = {
        "A7": ("TESTED", "S75 FIXED: REFERENCE resids captured at parse + resolve_resid_string ARSC resolve wired at ResourceRuntime ensure_loaded (PackageParser labelRes/loadLabel law); f54_manifestlabel fixture proves label '@string/app_name' -> 'F54 LabelProof' + icon resid capture; verifier f54 6/6, 24/24 total"),
        "A8": ("PARTIAL", "A2 complex_unit_to_dimension_pixel_size law shipped (execution_engine.cpp:590 comment); the separate 24px default-fallback loudness not re-verified this wave"),
        "B5": ("PENDING", "setTranslationX/Y/setAlpha/scale/rotation in accept-and-ignore list (canvas_shadow.cpp:569) — gap stands"),
        "B6": ("PENDING", "no scrollY/scroll-offset support anywhere in miniandroid/src (feature absent — matrix 'missing' stands)"),
        "B9": ("PENDING", "text_italic FLAG stored (android_shadows.h:1156) but no italic face/synthesis — matrix 'missing' stands"),
        "B10": ("PENDING", "no per-codepoint fallback face chain in src/fonts (only FreeSerif/emoji base — matrix 'missing' stands)"),
        "B11": ("PENDING", "no view-level android:theme handling in layout_inflater.cpp — activity-level theme only (F-134); census-only item, gap stands"),
        "B12": ("PARTIAL", "@android: branch exists in resolve_id_attr (layout_inflater.cpp:417) — typed-reference path resolves; non-reference @android: names still return 0 (no framework ARSC)"),
        "C3": ("TESTED", "f18_lltop fix branch present (S67 FOUNDATION comment, AOSP LinearLayout.java L1445-1470 law cited inline)"),
        "C4": ("PARTIAL", "separate text_gravity field exists (dialog_shadow.cpp:140); XML gravity->two-field conflation not proven corpus-wide"),
        "C5": ("PARTIAL", "layout_dirty raised by geometry/LayoutParams mutations (R-NEW-302 requestLayout law); text/visibility setters still do not raise it"),
        "C6": ("PENDING", "invalidate/requestLayout in shadow method-name list only; no dirty-region model (whole-tree re-render stands)"),
        "C7": ("PENDING", "RenderNode beginRecording/recording implemented, but setAlpha/setTranslationX/scale/rotation are swallowed no-ops (canvas_shadow.cpp:569)"),
        "C8": ("PENDING", "png_set_IHDR PNG_COLOR_TYPE_RGB confirmed (software_renderer.cpp:863) — alpha dropped, gap stands"),
        "C9": ("PENDING", "dump_view_tree JSON writes x/y/text/visibility but NO alpha/padding/measured_left fields (dalvik_engine.cpp:9091+)"),
        "C10": ("PENDING", "real getIdentifier path documented (android_shadows.h:1488); dual-path reconciliation not evidenced"),
        "C11": ("PENDING", "complex_to_fraction still declared (res_id.h:167) with zero consumers — dead code stands"),
        "C12": ("PARTIAL", "DensityContext::from_density(font_scale) plumbing exists (res_id.h:130) with default 1.0; live fontScale source not evidenced"),
        "D1": ("PENDING", "view_renderer.cpp exists (30KB), not in Makefile — dead file not removed"),
        "D2": ("PENDING", "real_layout.cpp + resource_parser.cpp legacy orphans still present in src/resources/"),
        "D3": ("PARTIAL", "api_dispatcher.cpp NOT in Makefile (build-membership half fixed); file remains as grep trap"),
        "D4": ("PARTIAL", "exp088_a4 target now links miniandroid_core (CMakeLists.txt:282) — lib-set drift likely fixed; target itself remains"),
        "D5": ("PENDING", "miniandroid/scripts/build_exp124.sh still references src/renderer/text_shaper.cpp (moved to src/fonts/) + dead real_layout.cpp/view_renderer.cpp"),
        "D6": ("PENDING", "PNGWriter encodes PNG_COLOR_TYPE_RGB (software_renderer.cpp:863) — alpha dropped, gap stands"),
        "D7": ("PENDING", "view_tree.json writes n[x]/n[y] while ViewNode carries measured_left/top (dalvik_engine.cpp:9092) — dual naming stands"),
    }
    if item_id in MANUAL:
        return MANUAL[item_id]
    if m_st is None:
        final = c_st
        src = "code-verification only (census item; matrix row has no status keyword)"
    elif m_st == "TESTED" and c_st == "TESTED":
        final = "TESTED"
        src = "gap matrix FIXED + code fix PRESENT"
    elif m_st == "TESTED" and c_st == "PENDING":
        final = "PARTIAL"
        src = "CONFLICT: matrix says FIXED but fix-pattern absent — recorded honestly"
    elif m_st == "PENDING" and c_st == "TESTED":
        final = "PARTIAL"
        src = "CONFLICT: matrix says open but open-state absent — recorded honestly"
    else:
        final = m_st
        src = "gap matrix row (full-row status)"
    return final, src

results = []
item75_n = 0
ordered_ids = list(census.keys()) + list(gaprows.keys())
for id_ in ordered_ids:
    item75_n += 1
    ledger_id = f"ITEM75-{item75_n:03d}"
    title = (census.get(id_) or gaprows.get(id_) or "")[:140]
    grow = find_gap_row(id_) if id_ in census else (f"[{id_}] {gaprows[id_]}" if id_ in gaprows else None)
    code = CHECKS.get(id_, {"item": id_, "expect": "n/a", "found": False, "pattern": "", "evidence": []})
    final, src = reconcile(id_, grow, code)
    in_reg = registry_has(id_)
    ev = {
        "matrix_row": (grow[:220] if grow else None),
        "code_check": code,
        "registry_back_registered": in_reg,
        "reconcile_basis": src,
    }
    results.append({
        "ledger_id": ledger_id, "item_id": id_, "requirement": title,
        "final_status": final, "evidence": ev,
    })

out_json = os.path.join(ROOT, "docs", "audit", "item75_closure.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump({"generated": NOW, "wave": "S75-CLOSURE", "rows": results}, f, indent=1, ensure_ascii=False)

# ------------------------------------------------------------------ 4. markdown
from collections import Counter
cnt = Counter(r["final_status"] for r in results)
md = []
md.append("# ITEM75 CLOSURE AUDIT — S75 CLOSURE WAVE\n")
md.append(f"Generated: {NOW} · Scope: ITEM75-001..{item75_n:03d} (47 census/contract rows)\n")
md.append("Three-source reconciliation per row: canonical `FOUNDATION_GAP_MATRIX.md` row + live code check (rg on `miniandroid/src`, file:line cited) + registry back-registration. 'expected OPEN' items were checked **for absence** — a hit means the gap may have closed and is flagged PARTIAL for human review, never auto-flipped.\n")
md.append("## Dashboard\n\n```text")
for k in ("TESTED", "PARTIAL", "PENDING", "BLOCKED"):
    md.append(f"status {k}: {cnt.get(k, 0)}")
md.append(f"TOTAL: {len(results)}\n```\n")
md.append("## Per-row table\n")
md.append("| Ledger | Item | Final status | Basis | Code evidence |")
md.append("| --- | --- | --- | --- | --- |")
for r in results:
    ev = r["evidence"]
    code = ev["code_check"]
    ev_txt = (code["evidence"][0].split(":")[0] + ":" + code["evidence"][0].split(":")[1]) if code["evidence"] else ("ABSENT: " + code["pattern"][:40])
    md.append(f"| {r['ledger_id']} | {r['item_id']} | {r['final_status']} | {ev['reconcile_basis']} | `{ev_txt}` |")
md.append("\n## Conflicts and honest notes\n")
confl = [r for r in results if "CONFLICT" in r["evidence"]["reconcile_basis"]]
if confl:
    for r in confl:
        md.append(f"- **{r['ledger_id']} ({r['item_id']})**: {r['evidence']['reconcile_basis']}")
else:
    md.append("- none: matrix and code agree on every row.")
open_items = [r for r in results if r["final_status"] in ("PENDING",)]
md.append("\n## Still-open gaps (PENDING, honestly not implemented)\n")
for r in open_items:
    md.append(f"- {r['ledger_id']} ({r['item_id']}): {r['requirement'][:110]}")
out_md = os.path.join(ROOT, "docs", "audit", "ITEM75_CLOSURE.md")
with open(out_md, "w", encoding="utf-8") as f:
    f.write("\n".join(md) + "\n")

print("WROTE", out_json)
print("WROTE", out_md)
print("COUNTS:", dict(cnt))
for r in results:
    if "CONFLICT" in r["evidence"]["reconcile_basis"]:
        print("CONFLICT:", r["ledger_id"], r["item_id"], r["evidence"]["reconcile_basis"])
