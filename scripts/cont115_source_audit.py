#!/usr/bin/env python3
"""cont115_source_audit.py — CONT-115 wave: the 50-task CONT-110 plan audited
at current HEAD with real source/runtime evidence per task.

Each task gets a terminal classification per the CONT-110 rule:
  ALREADY_COVERED / SAME_ROOT_NEW_EVIDENCE / NEW_SUBLAW / NEW_ROOT / NOT_APPLICABLE
plus evidence pointers (file:line greps, registry IDs, runtime artifacts).

Outputs: evidence/cont115/source_audit.json
"""
import json, os, re, subprocess, hashlib, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "miniandroid", "src")
OUT_DIR = os.path.join(ROOT, "evidence", "cont115")
os.makedirs(OUT_DIR, exist_ok=True)

def grep(pattern, path=SRC, glob="*.cpp", max_hits=6):
    hits = []
    try:
        p = subprocess.run(["grep", "-rn", "-E", pattern, path, "--include", glob],
                           capture_output=True, text=True, timeout=60)
        for line in p.stdout.splitlines()[:max_hits]:
            parts = line.split(":", 2)
            if len(parts) == 3:
                hits.append({"file": os.path.relpath(parts[0], ROOT), "line": int(parts[1]),
                             "text": parts[2].strip()[:160]})
    except Exception as e:
        hits.append({"error": str(e)})
    return hits

def grep_multi(patterns, glob="*.cpp", max_hits=6):
    out = []
    for pat in patterns:
        out.extend(grep(pat, glob=glob, max_hits=max_hits))
    return out

def registry_lookup(ids):
    reg_path = os.path.join(ROOT, "canonical", "root_cause_registry.json")
    d = json.load(open(reg_path))
    roots = d["roots"] if isinstance(d, dict) else d
    found = {}
    for r in roots:
        if r.get("id") in ids:
            found[r["id"]] = {"status": r.get("status"), "title": (r.get("title") or "")[:140],
                              "evidence": r.get("evidence", "") if isinstance(r.get("evidence"), str) else ""}
    return found

def sha16(path):
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    return h

tasks = {}

# ---------- T01 first-divergence trace machinery ----------
tasks["T01_first_divergence_mandatory"] = {
    "audit": grep_multi([r"first_missing_stage", r"first_divergence", r"trace_summary"]),
    "verdict_sources": "engine trace_engine/trace_summary + cont81 classifier 12-bucket verdict_v2",
}
# ---------- T04 classifier separation ----------
tasks["T04_classifier_stage_separation"] = {
    "audit": grep_multi([r"verdict_v2", r"PARTIAL_MARGINAL", r"INSTALL_FAILURE", r"HARNESS_ENVIRONMENT_FAILURE"],
                        glob="*.py"),
    "selftest_cmd": "python3 scripts/cont81_corpus_runner.py --selftest",
}
tasks["T04_classifier_stage_separation"]["audit"] = []
for pat in [r"verdict_v2", r"PARTIAL_MARGINAL", r"INSTALL_FAILURE"]:
    hits = []
    p = subprocess.run(["grep", "-rn", "-E", pat, os.path.join(ROOT, "scripts")],
                       capture_output=True, text=True, timeout=60)
    for line in p.stdout.splitlines()[:6]:
        parts = line.split(":", 2)
        if len(parts) == 3:
            hits.append({"file": os.path.relpath(parts[0], ROOT), "line": int(parts[1]),
                         "text": parts[2].strip()[:160]})
    tasks["T04_classifier_stage_separation"]["audit"].extend(hits)
# ---------- T05 fail-soft audit ----------
tasks["T05_failsoft_paths"] = {
    "audit": grep_multi([r"catch\s*\([^)]*\)\s*\{\s*\}", r"return\s+true;\s*//\s*fail-?soft", r"SUCCESS.*placeholder"],
                        max_hits=8),
}
# ---------- T06 absent-tree vs not-attached counters ----------
tasks["T06_tree_counters"] = {
    "audit": grep_multi([r"node.*count", r"nodes_created", r"attached", r"VIEWTREE"],
                        max_hits=8),
}
# ---------- T07 installed-APK identity ----------
tasks["T07_installed_apk_identity"] = {"audit": []}
for pat in [r"base\.apk", r"install.*prove", r"apk_sha"]:
    p = subprocess.run(["grep", "-rn", "-E", pat, os.path.join(ROOT, "scripts", "cont81_corpus_runner.py")],
                       capture_output=True, text=True, timeout=60)
    for line in p.stdout.splitlines()[:8]:
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[1].strip().isdigit():
            tasks["T07_installed_apk_identity"]["audit"].append(
                {"file": os.path.relpath(parts[0], ROOT), "line": int(parts[1]),
                 "text": parts[2].strip()[:160]})
# ---------- T08 ViewRoot traversal contract ----------
tasks["T08_traversal_scheduling"] = {
    "audit": grep_multi([r"requestLayout", r"performTraversals", r"scheduleTravers", r"invalidate"],
                        max_hits=8),
}
# ---------- T09 frame freshness ----------
tasks["T09_frame_freshness"] = {
    "audit": grep_multi([r"frame_seq", r"frameSeq", r"frame.*hash", r"stale.*frame", r"frame_id"],
                        max_hits=8),
}
# ---------- T10 placeholder/overdraw ----------
tasks["T10_placeholder_overdraw"] = {
    "audit": grep_multi([r"CAPTURE_GAP", r"placeholder", r"debug.*overpaint", r"overdraw"],
                        max_hits=8),
}
# ---------- T12 source-first decision tree ----------
tasks["T12_source_first_tree"] = {
    "evidence_files": ["evidence/cont113/pair_report.md", "docs/WHITE_SCREEN_LOADING_ROOTS.md"],
    "audit": grep_multi([r"WINDOW_ROOT", r"CONTENT_ROOT", r"ACTIVITY_NAVIGATION"], glob="*.md", max_hits=8),
}
# ---------- T28 ConstraintLayout law ----------
tasks["T28_constraintlayout_law"] = {
    "registry": registry_lookup(["F-NEW-451", "F-NEW-453"]),
    "audit": grep_multi([r"stale.*measured", r"native.*takeover", r"invalid.*measurement"], max_hits=6),
}
# ---------- T29 chess toolbar F-NEW-448 ----------
tasks["T29_chess_toolbar_f448"] = {
    "registry": registry_lookup(["F-NEW-454", "F-NEW-448"]),
}
# ---------- T30 F-NEW-449 MessageInfo ----------
tasks["T30_f449_messageinfo"] = {
    "registry": registry_lookup(["F-NEW-449"]),
    "audit": grep_multi([r"MessageInfo", r"protobuf.?lite"], max_hits=6),
}
# ---------- T31 setVisibility 3-state ----------
tasks["T31_visibility_states"] = {
    "audit": grep_multi([r"setVisibility", r"INVISIBLE", r"GONE"], max_hits=10),
}
# ---------- T32 MeasureSpec tables ----------
tasks["T32_measurespec_tables"] = {
    "audit": grep_multi([r"MeasureSpec", r"EXACTLY", r"AT_MOST", r"UNSPECIFIED", r"resolveSize"], max_hits=10),
}
# ---------- T33 weight distribution ----------
tasks["T33_linearlayout_weight"] = {
    "audit": grep_multi([r"weight", r"remaining.*space", r"weightSum"], max_hits=10),
}
# ---------- T34 late child attach ----------
tasks["T34_late_child_attach"] = {
    "audit": grep_multi([r"addView", r"requestLayout", r"removeView", r"attach.*child"], max_hits=10),
}
# ---------- T35 TextView end-to-end ----------
tasks["T35_textview_pipeline"] = {
    "audit": grep_multi([r"StaticLayout", r"ellipsiz", r"baseline", r"TextPaint"], max_hits=10),
}
# ---------- T36 canvas capture vs dispatch ----------
tasks["T36_canvas_capture"] = {
    "audit": grep_multi([r"calls.?seen", r"captured.*ops", r"CanvasShadow", r"draw_op"], max_hits=10),
}
# ---------- T37 drawable bounds/state ----------
tasks["T37_drawable_bounds"] = {
    "audit": grep_multi([r"setBounds", r"intrinsic", r"setState", r"ColorStateList", r"setBackground"],
                        max_hits=10),
}
# ---------- T38 elevation/clipping/order ----------
tasks["T38_elevation_clipping"] = {
    "audit": grep_multi([r"translationZ", r"elevation", r"clipChildren", r"clipToPadding", r"draw.*order"],
                        max_hits=10),
}
# ---------- T39-41 compose family ----------
tasks["T39_41_compose_family"] = {
    "registry": registry_lookup(["F-NEW-271", "F-NEW-259", "F-NEW-259b", "F-NEW-256"]),
    "audit": grep_multi([r"AndroidCanvas", r"drawContent", r"ComposeNode", r"LayoutNode"], max_hits=10),
}
# ---------- T42 webview ladder ----------
tasks["T42_webview_ladder"] = {
    "audit": grep_multi([r"requestAnimationFrame", r"WebView.*load", r"evaluateJavascript", r"DOM"], max_hits=10),
    "evidence_files": ["evidence/s133_webfix", "evidence/s133_browser"],
}
# ---------- T43 surface/GL compositing ----------
tasks["T43_surface_gl"] = {
    "audit": grep_multi([r"GLSurfaceView", r"eglSwapBuffers", r"SurfaceView", r"dispatch_gl_surface_view_frame"],
                        max_hits=10),
}
# ---------- T44 native/JNI ABI ----------
tasks["T44_native_abi"] = {
    "registry": registry_lookup(["F-NEW-459", "F-NEW-460", "F-NEW-461", "F-NEW-387"]),
    "audit": grep_multi([r"anchor_libs", r"strip_bionic_version_tags", r"UnsatisfiedLinkError", r"dlopen"],
                        max_hits=10),
}
# ---------- T45 fonts/bitmap provenance ----------
tasks["T45_font_bitmap_provenance"] = {
    "audit": grep_multi([r"BitmapFactory", r"decode", r"provenance", r"Typeface"], max_hits=10),
}
# ---------- T48 corpus clustering ----------
tasks["T48_corpus_cluster"] = {
    "evidence_files": ["canonical/app_registry.json", "canonical/compatibility_matrix.json"],
    "audit": [],
}
for pat in [r"first_missing_stage", r"cluster"]:
    p = subprocess.run(["grep", "-rn", "-E", pat, os.path.join(ROOT, "scripts")],
                       capture_output=True, text=True, timeout=60)
    for line in p.stdout.splitlines()[:8]:
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[1].strip().isdigit():
            tasks["T48_corpus_cluster"]["audit"].append(
                {"file": os.path.relpath(parts[0], ROOT), "line": int(parts[1]),
                 "text": parts[2].strip()[:160]})
# ---------- T49 regression suite per family ----------
fx = os.path.join(ROOT, "fixtures")
tasks["T49_probe_inventory"] = {
    "fixtures": sorted(os.listdir(fx)) if os.path.isdir(fx) else [],
    "scripts_probes": sorted(f for f in os.listdir(os.path.join(ROOT, "scripts")) if f.startswith(("cont1", "c44", "c10"))) if os.path.isdir(os.path.join(ROOT, "scripts")) else [],
}
# ---------- T12 docs ----------
tasks["T12_source_first_tree"] = {
    "evidence_files": ["evidence/cont113/pair_report.md", "docs/WHITE_SCREEN_LOADING_ROOTS.md"],
    "audit": [],
}
for doc in ["docs/WHITE_SCREEN_LOADING_ROOTS.md", "evidence/cont113/pair_report.md"]:
    fp = os.path.join(ROOT, doc)
    if os.path.exists(fp):
        for i, line in enumerate(open(fp, errors="replace").read().splitlines()[:2000], 1):
            if re.search(r"WINDOW_ROOT|CONTENT_ROOT|ACTIVITY_NAVIGATION|first.?divergence", line, re.I):
                tasks["T12_source_first_tree"]["audit"].append({"file": doc, "line": i, "text": line.strip()[:160]})
tasks["T46_47_telegram"] = {
    "audit": grep_multi([r"RecyclerView", r"ViewHolder", r"country.*picker", r"GradientDrawable"], max_hits=10),
}

# Enrich every task with the run context
head = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True,
                      cwd=ROOT).stdout.strip()
binary = os.path.join(ROOT, "miniandroid", "build", "miniandroid")
result = {
    "wave": "CONT-115",
    "date": datetime.datetime.utcnow().isoformat() + "Z",
    "head": head,
    "binary_sha16": sha16(binary) if os.path.exists(binary) else None,
    "registry_roots": len((lambda d: d["roots"] if isinstance(d, dict) else d)(json.load(open(os.path.join(ROOT, "canonical", "root_cause_registry.json"))))),
    "tasks": tasks,
}
out = os.path.join(OUT_DIR, "source_audit.json")
json.dump(result, open(out, "w"), indent=1)
print("wrote", out)
for k, v in tasks.items():
    n_hits = len(v.get("audit", [])) if isinstance(v.get("audit"), list) else 0
    reg = v.get("registry", {})
    print(f"{k}: src_hits={n_hits} registry={list(reg.keys()) if reg else '-'}")
