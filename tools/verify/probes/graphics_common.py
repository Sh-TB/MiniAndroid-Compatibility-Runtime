#!/usr/bin/env python3
"""graphics_common.py — S92 shared evidence layer (REUSE-FIRST).

Loads the evidence the MiniAndroid runtime ALREADY produces per run
(no new runtime mechanism duplicated):

  <run_dir>/screenshot.png          final capture
  <run_dir>/frames/frame_*.png      per-interaction frames
  <run_dir>/frames/manifest.json    per-frame click evidence (changed px, state)
  <run_dir>/view_tree.json          full hierarchy: bounds/visibility/clickable
                                    /image_resource_id/text per node
  <run_dir>/gfx_provenance.json     per-image chain ASSET_FOUND -> ... ->
                                    DRAW_CALLED (+GL chain), frame census,
                                    FIRST_DIVERGENCE  (env-gated at runtime)
  <run_dir>/click_audit.jsonl       JSONL per-click target/dispatch records
                                    (env-gated at runtime)

plus the APK itself (asset ground truth: res/** bitmaps, manifest package).

S92 law: none of these alone is success. The verifier CROSS-CORRELATES them.
"""
import hashlib
import json
import os
import re
import struct
import zipfile

# ---------------------------------------------------------------------------
# generic helpers
# ---------------------------------------------------------------------------

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def load_jsonl(path):
    out = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# run evidence bundle
# ---------------------------------------------------------------------------

class RunEvidence:
    """All evidence found under one run output directory."""

    def __init__(self, run_dir):
        self.run_dir = run_dir
        self.exists = os.path.isdir(run_dir)
        self.screenshot = None
        self.frames = []            # [(frame_name, path)]
        self.frames_manifest = None
        self.view_tree = None
        self.provenance = None
        self.click_audit = []
        self.report_json = None
        self._scan()

    def _scan(self):
        if not self.exists:
            return
        shot = os.path.join(self.run_dir, "screenshot.png")
        if os.path.isfile(shot):
            self.screenshot = shot
        fdir = os.path.join(self.run_dir, "frames")
        if os.path.isdir(fdir):
            for name in sorted(os.listdir(fdir)):
                if re.fullmatch(r"frame_\d+\.png", name):
                    self.frames.append((name, os.path.join(fdir, name)))
            mpath = os.path.join(fdir, "manifest.json")
            if os.path.isfile(mpath):
                self.frames_manifest = load_json(mpath)
        vt = os.path.join(self.run_dir, "view_tree.json")
        if os.path.isfile(vt):
            self.view_tree = load_json(vt)
        for cand in ("gfx_provenance.json", "provenance.json"):
            p = os.path.join(self.run_dir, cand)
            if os.path.isfile(p):
                self.provenance = load_json(p)
                break
        ca = os.path.join(self.run_dir, "click_audit.jsonl")
        if os.path.isfile(ca):
            self.click_audit = load_jsonl(ca)
        for cand in ("report.json", "run_report.json"):
            p = os.path.join(self.run_dir, cand)
            if os.path.isfile(p):
                self.report_json = load_json(p)
                break

    def evidence_inventory(self):
        return {
            "screenshot": self.screenshot is not None,
            "frame_count": len(self.frames),
            "frames_manifest": self.frames_manifest is not None,
            "view_tree": self.view_tree is not None,
            "gfx_provenance": self.provenance is not None,
            "click_audit_records": len(self.click_audit),
            "report_json": self.report_json is not None,
        }


# ---------------------------------------------------------------------------
# ViewTree helpers
# ---------------------------------------------------------------------------

def view_nodes(view_tree):
    if not view_tree or "nodes" not in view_tree:
        return []
    return view_tree["nodes"]


def node_bounds(n):
    return (n.get("x", 0), n.get("y", 0),
            n.get("width", 0), n.get("height", 0))


def visible_nodes(nodes):
    return [n for n in nodes if n.get("visibility", 0) == 0]


def clickable_nodes(nodes):
    return [n for n in nodes
            if n.get("clickable") or n.get("has_click_listener")]


def image_nodes(nodes):
    """Nodes that carry an image resource binding (ImageView-family or
    image_resource_id set)."""
    out = []
    for n in nodes:
        rid = n.get("image_resource_id", 0)
        cls = n.get("class", "")
        if rid or "ImageView" in cls:
            out.append(n)
    return out


def classify_renderer_family(nodes, provenance, report=None):
    """S92 0.4 renderer-family classification from runtime evidence.

    Returns (family, signals). One of:
      view-xml, canvas-custom-view, surfaceview, glsurfaceview, webview,
      compose, mixed, unknown
    """
    signals = []
    classes = {n.get("class", "") for n in nodes}
    origins = set()
    if provenance:
        for ev in provenance.get("events", []):
            origins.add(ev.get("origin", ""))
    fam = "unknown"
    has_gl = any("GLSurfaceView" in c for c in classes) or \
        "glsurfaceview-frame" in origins
    has_surface = any("SurfaceView" in c for c in classes)
    has_web = any("WebView" in c for c in classes)
    has_compose = any(("ComposeView" in c) or ("androidx.compose" in c)
                      for c in classes)
    canvas_draws = any("canvas" in o for o in origins)
    custom_canvas = any(
        "View;" in c and not c.startswith("Landroid/") and
        not c.startswith("Ljava/") for c in classes)
    if has_gl:
        fam = "glsurfaceview"
    elif has_surface and has_gl:
        fam = "mixed"
    elif has_surface:
        fam = "surfaceview"
    elif has_compose:
        fam = "compose"
    elif has_web:
        fam = "webview"
    elif canvas_draws or (custom_canvas and not any(
            "ImageView" in c for c in classes)):
        fam = "canvas-custom-view"
    else:
        fam = "view-xml"
    if has_gl:
        signals.append("GLSurfaceView-class-or-gl-frame-event")
    if has_surface:
        signals.append("SurfaceView-class")
    if has_web:
        signals.append("WebView-class")
    if has_compose:
        signals.append("compose-class")
    if canvas_draws:
        signals.append("canvas-drawBitmap-origin-events")
    if custom_canvas:
        signals.append("app-custom-View-subclass")
    return fam, signals


# ---------------------------------------------------------------------------
# PNG decode (asset ground truth from the APK) — minimal, deterministic
# ---------------------------------------------------------------------------

def png_dims(data):
    if len(data) >= 33 and data[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", data[16:24])
        return w, h
    return None


def apk_assets(apk_path, prefix_res=True):
    """Raster asset inventory from the APK zip.

    Returns list of dicts: path, sha256, size, dims (PNG only), density_bucket.
    Non-PNG (webp/jpg/gif/xml) recorded with dims=None.
    """
    out = []
    if not apk_path or not os.path.isfile(apk_path):
        return out
    bucket_re = re.compile(r"res/(drawable|mipmap)(?:-([a-z0-9]+))?/")
    with zipfile.ZipFile(apk_path) as z:
        for info in z.infolist():
            name = info.filename
            if not name.startswith("res/"):
                continue
            if not re.search(r"\.(png|webp|jpg|jpeg|gif)$", name):
                continue
            data = z.read(name)
            rec = {
                "path": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
                "dims": png_dims(data) if name.endswith(".png") else None,
                "kind": name.rsplit(".", 1)[-1],
            }
            m = bucket_re.match(name)
            if m:
                rec["dir"] = m.group(1)
                rec["bucket"] = m.group(2) or ""
            out.append(rec)
    return out


def apk_extract_asset(apk_path, res_path):
    try:
        with zipfile.ZipFile(apk_path) as z:
            return z.read(res_path)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# contract I/O
# ---------------------------------------------------------------------------

CONTRACT_DIR_CANDIDATES = [
    "registry/visual_contracts",
    "docs/evidence/visual_contracts",   # legacy fallback (never written)
]


def find_contract(repo_root, package):
    for d in CONTRACT_DIR_CANDIDATES:
        p = os.path.join(repo_root, d, f"{package}.json")
        if os.path.isfile(p):
            return load_json(p)
    return None
