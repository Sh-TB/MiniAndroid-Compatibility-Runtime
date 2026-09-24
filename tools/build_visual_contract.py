#!/usr/bin/env python3
"""build_visual_contract.py — S92 visual contract builder (§3, §0.3).

Builds a machine-readable EXPECTED VISUAL CONTRACT for a title from
REAL evidence only (never invented):

  APK zip            -> required_assets (res/** raster files, SHA, dims)
  runtime view_tree  -> required_elements + interaction_targets
                        (bounds/visibility/clickable) [confidence:
                        observed_only]
  upstream source    -> optional source law notes [confidence:
                        source_verified] when provided
  gfx_provenance     -> per-asset decode/draw linkage

Confidence doctrine (§0.3): no source repo -> never higher than
apk_verified; element bounds observed from a MiniAndroid ViewTree are
observed_only unless a source/layout law corroborates them.

Usage:
  python3 tools/build_visual_contract.py --apk PATH --package P --title T \
      [--run-dir DIR] [--source-url URL] [--source-root DIR] \
      [--out registry/visual_contracts/P.json]
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools", "verify"))

from tools.verify.probes import graphics_common as gc          # noqa: E402
from tools.verify.probes import verdict as vd                  # noqa: E402


def build_contract(apk_path, package, title, run_dir=None,
                   source_url=None, source_root=None, screen=(1080, 1920)):
    contract = {
        "schema": "s92.visual_contract.v1",
        "title": title,
        "package": package,
        "apk_sha256": gc.sha256_file(apk_path) if apk_path else None,
        "screen": list(screen),
        "renderer_family": None,       # finalized from run evidence
        "required_elements": [],
        "required_assets": [],
        "required_regions": [],
        "interaction_targets": [],
        "expected_state_changes": [],
        "dynamic_regions": [],
        "source_provenance": {
            "source_url": source_url,
            "source_root": source_root,
            "source_laws": [],
        },
        "confidence": "observed_only",
    }
    # ---- assets from APK (ground truth) -----------------------------------
    assets = gc.apk_assets(apk_path)
    launcher_like = [a for a in assets if "mipmap" in a.get("dir", "") or
                     ("drawable" in a.get("dir", "") and
                      ("icon" in a["path"].lower() or
                       "logo" in a["path"].lower()))]
    for a in assets:
        contract["required_assets"].append({
            "name": a["path"].rsplit("/", 1)[-1],
            "path": a["path"],
            "sha256": a["sha256"],
            "dims": a["dims"],
            "kind": a["kind"],
            "dir": a.get("dir"),
            "bucket": a.get("bucket", ""),
            "confidence": "apk_verified",
            "required": bool(launcher_like and a in launcher_like),
        })
    if assets:
        contract["confidence"] = "apk_verified"

    # ---- elements/targets from run evidence -------------------------------
    if run_dir:
        re_ = gc.RunEvidence(run_dir)
        nodes = gc.view_nodes(re_.view_tree)
        fam, signals = gc.classify_renderer_family(
            nodes, re_.provenance, re_.report_json)
        contract["renderer_family"] = fam
        contract["renderer_signals"] = signals
        for n in gc.visible_nodes(nodes):
            cls = n.get("class", "")
            if not cls:
                continue
            el = {
                "name": cls.split(".")[-1].strip(";").lstrip("L") +
                        (f"[{n.get('text')}]" if n.get("text") else ""),
                "class": cls,
                "resource_id": n.get("android_view_id"),
                "text": n.get("text") or None,
                "expected_bounds": gc.node_bounds(n),
                "visibility": "VISIBLE",
                "confidence": "observed_only",
            }
            contract["required_elements"].append(el)
            if n.get("clickable") or n.get("has_click_listener"):
                contract["interaction_targets"].append({
                    "class": cls,
                    "view_id": n.get("android_view_id"),
                    "text": n.get("text") or None,
                    "bounds": gc.node_bounds(n),
                    "confidence": "observed_only",
                })
    # ---- source laws (optional) -------------------------------------------
    if source_root and os.path.isdir(source_root):
        laws = []
        for root, _dirs, files in os.walk(source_root):
            for f in files:
                if f.endswith(".java"):
                    p = os.path.join(root, f)
                    try:
                        src = open(p, encoding="utf-8", errors="ignore").read()
                    except Exception:
                        continue
                    for needle, law in (
                        ("setImageResource(", "ImageView.setImageResource"),
                        ("setImageDrawable(", "ImageView.setImageDrawable"),
                        ("decodeResource", "BitmapFactory.decodeResource"),
                        ("openRawResource", "Resources.openRawResource"),
                        ("getIdentifier", "Resources.getIdentifier"),
                        ("lockCanvas", "SurfaceView.lockCanvas"),
                        ("onDraw", "View.onDraw"),
                        ("loadUrl", "WebView.loadUrl"),
                    ):
                        if needle in src:
                            laws.append({
                                "file": os.path.relpath(p, source_root),
                                "law": law})
        contract["source_provenance"]["source_laws"] = laws[:40]
        if laws:
            contract["confidence"] = "source_verified"
    return contract


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apk", required=True)
    ap.add_argument("--package", required=True)
    ap.add_argument("--title", default=None)
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--source-url", default=None)
    ap.add_argument("--source-root", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(REPO, "registry", "visual_contracts",
                                f"{a.package}.json")
    c = build_contract(a.apk, a.package, a.title or a.package,
                       run_dir=a.run_dir, source_url=a.source_url,
                       source_root=a.source_root)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(c, f, indent=1, sort_keys=True)
    print(json.dumps({
        "contract": out,
        "package": a.package,
        "assets": len(c["required_assets"]),
        "elements": len(c["required_elements"]),
        "interaction_targets": len(c["interaction_targets"]),
        "renderer_family": c["renderer_family"],
        "confidence": c["confidence"],
    }, indent=1))


if __name__ == "__main__":
    main()
