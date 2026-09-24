#!/usr/bin/env python3
"""S94 Phase C-3: retry misses with corrected paths; README fallback for engines."""
import hashlib
import json
import urllib.request
from pathlib import Path

BASE = Path("/home/z/my-project/run/s94/source_mining")
UA = {"User-Agent": "miniandroid-s94-miner/1.0"}

RETRY = {
    "servo/servo": [
        {"path": "components/compositing/compositor.rs", "symbols": ["composite"], "alts": ["components/compositing/compositor.rs"]},
        {"path": "components/layout_thread.rs", "symbols": ["layout"], "alts": ["components/layout_thread.rs"]},
    ],
    "facebook/shimmer-android": [
        {"path": "shimmer/src/main/java/com/facebook/shimmer/ShimmerFrameLayout.java", "symbols": ["ShimmerDrawable", "onDraw"],
         "alts": ["shimmer/src/main/java/com/facebook/shimmer/ShimmerFrameLayout.java"]},
    ],
    "korlibs/korge": [
        {"path": "korge/src/korlibs/korge/view/Views.kt", "symbols": ["render"], "alts": [
            "korge/src/korlibs/korge/view/Views.kt"]},
    ],
    "axmolengine/axmol": [
        {"path": "cocos/CCDirector.cpp", "symbols": ["drawScene", "mainLoop"], "alts": [
            "cocos/cocos/2d/CCDirector.cpp", "cocos/2d/CCDirector.cpp", "extensions/cocos/CCDirector.cpp"]},
    ],
    "defold/defold": [
        {"path": "engine/render/src/render.cpp", "symbols": ["RenderListDispatch"], "alts": [
            "engine/render/src/render/render.cpp", "engine/render/src/render.cpp"]},
    ],
    "maplibre/maplibre-gl-native": [
        {"path": "src/mbgl/text/glyph_atlas.cpp", "symbols": ["addGlyphs", "texture"], "alts": [
            "src/mbgl/text/glyph_atlas.cpp", "src/mbgl/text/glyph_atlas_fragment.cpp",
            "src/mbgl/text/glyph.cpp"]},
    ],
    "kornelski/dssim": [
        {"path": "src/lib.rs", "symbols": ["dssim"], "alts": ["src/lib.rs"]},
    ],
    "reg-viz/reg-suit": [
        {"path": "packages/reg-suit-core/src/core/screenshot_diff_reporter.ts", "symbols": ["diff"], "alts": [
            "packages/reg-suit-core/src/index.ts", "packages/reg-suit-core/src/core/screenshot_diff_reporter.ts"]},
    ],
    "OpenImageIO/oiio": [
        {"path": "src/libOpenImageIO/imagebufalgo_compare.cpp", "symbols": ["compare", "isnan"], "alts": [
            "src/libOpenImageIO/imagebufalgo_compare.cpp"]},
    ],
    "facebook/litho": [
        {"path": "litho-core/src/main/java/com/facebook/litho/ComponentTree.java", "symbols": ["layout", "draw"], "alts": [
            "litho-core/src/main/java/com/facebook/litho/ComponentTree.java"]},
    ],
    "chrisbanes/PhotoView": [
        {"path": "photoview/src/main/java/uk/co/chrisbanes/photoview/PhotoView.kt", "symbols": ["attacher"], "alts": [
            "photoview/src/main/java/uk/co/chrisbanes/photoview/PhotoView.kt",
            "library/src/main/java/uk/co/chrisbanes/photoview/PhotoViewAttacher.java"]},
    ],
    "godotengine/godot-demo-projects": [
        {"path": "README.md", "symbols": ["demo"], "alts": []},
    ],
    "hajimehoshi/ebiten": [
        {"path": "game.go", "symbols": ["Update", "Draw"], "alts": ["game.go"]},
    ],
    "canvg/canvg": [
        {"path": "src/index.ts", "symbols": ["Canvas", "render"], "alts": ["src/index.ts"]},
    ],
    "appium": [],
}


def fetch_raw(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


def locate_symbols(text, symbols):
    lines = text.splitlines()
    return {s: [i + 1 for i, l in enumerate(lines) if s in l][:10] for s in symbols
            if any(s in l for l in lines)}


def main():
    repos_doc = json.loads((BASE / "repositories.json").read_text())
    recs = {r["repository"]: r for r in repos_doc["repositories"]}
    doc = json.loads((BASE / "rawfetch_results.json").read_text())
    by_repo = {r["repository"]: r for r in doc["results"]}
    fixed = 0
    for repo, files in RETRY.items():
        if not files:
            continue
        rec = by_repo.get(repo)
        if rec is None:
            rec = {"repository": repo, "family_note": "retry round", "files": []}
            by_repo[repo] = rec
        for f in files:
            attempts = [f["path"]] + [a for a in f.get("alts", []) if a != f["path"]]
            sha = recs.get(repo, {}).get("head_sha")
            got = used = None
            for a in attempts:
                if not sha:
                    break
                data = fetch_raw(f"https://raw.githubusercontent.com/{repo}/{sha}/{a}")
                if data:
                    got, used = data, f"{repo}@{sha[:12]}:{a}"
                    break
            entry = {"path": f["path"], "symbols": f.get("symbols", []), "law": ""}
            if got is None:
                # README fallback for engine repos
                rd = fetch_raw(f"https://raw.githubusercontent.com/{repo}/{sha}/README.md") if sha else None
                if rd:
                    entry.update({"status": "README_ONLY", "fetch_source": f"{repo}@{sha[:12]}:README.md",
                                  "bytes": len(rd), "sha256": hashlib.sha256(rd).hexdigest()})
                else:
                    entry.update({"status": "NOT_FOUND", "attempts": attempts})
            else:
                text = got.decode("utf-8", "replace")
                entry.update({"status": "OK", "fetch_source": used, "bytes": len(got),
                              "sha256": hashlib.sha256(got).hexdigest(),
                              "symbol_line_hits": locate_symbols(text, f.get("symbols", []))})
                fixed += 1
            # replace or append
            for i, e in enumerate(rec["files"]):
                if e["path"] == f["path"]:
                    rec["files"][i] = entry
                    break
            else:
                rec["files"].append(entry)
    doc["results"] = sorted(by_repo.values(), key=lambda r: r["repository"])
    (BASE / "rawfetch_results.json").write_text(json.dumps(doc, indent=1))
    ok = sum(1 for r in doc["results"] for f in r["files"] if f.get("status") == "OK")
    print(f"retry fixed={fixed} total_ok={ok}")


if __name__ == "__main__":
    main()
