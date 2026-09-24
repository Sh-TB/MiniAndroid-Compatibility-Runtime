#!/usr/bin/env python3
"""S94 Phase C-1: shallow-clone medium repositories and harvest deep evidence.

Per cloned repo:
  - cloned HEAD sha (provenance pin)
  - top-level + depth-2 directory tree
  - content-discovered key files (rglob patterns): bytes, sha256,
    symbol inventory (class/struct names, on* callbacks, key method hits)
  - auto-discovered test dirs and file counts

Clones live in run/s94/source_mining/clones/ (gitignored).
"""
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/home/z/my-project/run/s94/source_mining")
CLONES = BASE / "clones"
OUT = BASE / "clones_harvest.json"

# repo -> {globs: rglob file patterns, symbols: substrings to line-locate}
CLONE_SPECS = {
    "houstudio/cdroid": {
        "globs": ["**/view.cpp", "**/view.h", "**/textview.*", "**/button.*", "**/imageview.*",
                  "**/viewgroup.*", "**/drawable.cpp", "**/drawable.h", "**/*ninepatch*",
                  "**/*ripple*", "**/*animationdrawable*", "**/*statelistedrawable*",
                  "**/canvas.*", "**/staticlayout.*", "**/dynamiclayout.*", "**/textlayout.*",
                  "**/layout.cpp", "**/AnimationDrawable*", "**/ColorDrawable*", "**/vector*"],
        "symbols": ["onDraw", "onMeasure", "onLayout", "onTouchEvent", "invalidate",
                    "NinePatch", "stretch", "draw(Canvas", "setTextSize", "measureText",
                    "requestLayout", "setAlpha", "setColorFilter", "onStateChange"],
    },
    "mapbox/pixelmatch": {
        "globs": ["index.js", "*.d.ts", "test/**/*.{js,json,png}"],
        "symbols": ["antialias", "maxDelta", "threshold", "colorDelta", "includeAA"],
    },
    "JohannesBuchner/imagehash": {
        "globs": ["imagehash.py", "tests/*.py"],
        "symbols": ["average_hash", "phash", "dhash", "whash", "hex_to_hash"],
    },
    "americanexpress/jest-image-snapshot": {
        "globs": ["src/**/*.js"],
        "symbols": ["toMatchImageSnapshot", "pixelmatch", "diffThreshold", "getSnapshotFilename"],
    },
    "pedrovgs/Shot": {
        "globs": ["shot/src/main/java/**/*.scala", "shot/src/main/java/**/*.java"],
        "symbols": ["compareScreenshot", "ScreenshotComposer", "Bitmap"],
    },
    "ndtp/android-testify": {
        "globs": ["library/src/main/java/**/*.kt", "library/src/main/java/**/*.java"],
        "symbols": ["assertSame", "capture", "ScreenshotRule", "exclude", "baseline"],
    },
    "takahirom/roborazzi": {
        "globs": ["roborazzi/src/main/java/**/*.kt"],
        "symbols": ["captureRoboImage", "record", "verify", "ImageLoader", "compare"],
    },
    "cashapp/paparazzi": {
        "globs": ["paparazzi/src/main/java/**/*.kt"],
        "symbols": ["SnapshotHandler", "verify", "LayoutLibProjectDependency", "takeSnapshots"],
    },
    "airbnb/lottie-android": {
        "globs": ["lottie/src/main/java/**/LottieDrawable.java", "lottie/src/main/java/**/LottieComposition.java",
                  "lottie/src/main/java/**/BaseKeyframeAnimation.java", "lottie/src/main/java/**/LottieAnimationView.java"],
        "symbols": ["setProgress", "getFrame", "setMinFrame", "invalidateSelf", "onAnimationUpdate"],
    },
    "google/flexbox-layout": {
        "globs": ["flexbox/src/main/java/**/*.java"],
        "symbols": ["onMeasure", "onLayout", "FlexboxLayout", "measureHorizontal", "measureVertical"],
    },
    "RazrFalcon/resvg": {
        "globs": ["crates/resvg/src/**/*.rs", "Cargo.toml"],
        "symbols": ["render", "fit_to", "crop", "size", "ScreenSize"],
    },
    "memononen/nanosvg": {
        "globs": ["src/nanosvg.h", "src/nanosvgrast.h", "src/nanosvg.cc"],
        "symbols": ["nsvgParseFromFile", "nsvgRasterize", "nsvg__rasterize", "scale"],
    },
    "memononen/nanovg": {
        "globs": ["src/nanovg.c", "src/nanovg.h"],
        "symbols": ["nvgBeginFrame", "nvgEndFrame", "nvgFill", "nvgScissor", "nvgText"],
    },
    "fribidi/fribidi": {
        "globs": ["lib/fribidi.c", "lib/fribidi-bidi.c", "test/*.c"],
        "symbols": ["fribidi_get_par_embedding_levels", "fribidi_log2vis", "FRIBIDI_FLAG"],
    },
    "facebook/yoga": {
        "globs": ["yoga/**/*.cpp", "yoga/**/*.h"],
        "symbols": ["CalculateLayout", "YGNodeCalculateLayout", "resolveDimension", "performLayout"],
    },
    "pnggroup/libpng": {
        "globs": ["pngrutil.c", "png.c", "pngtest.c", "pngread.c"],
        "symbols": ["png_read_row", "png_set_strip_alpha", "png_do_read_transformations", "png_handle_tRNS"],
    },
    "libjpeg-turbo/libjpeg-turbo": {
        "globs": ["jdmarker.c", "jdatasrc.c", "jdapimin.c", "turbojpeg.c"],
        "symbols": ["jpeg_read_header", "jpeg_start_decompress", "read_markers", "exif"],
    },
    "webmproject/libwebp": {
        "globs": ["src/dec/*.c", "src/dec/*.h"],
        "symbols": ["WebPDecode", "VP8Decode", "DecodeAlphaData", "ParseHeadersInternal"],
    },
    "harfbuzz/harfbuzz": {
        "globs": ["src/hb-ot-shape.cc", "src/hb-buffer.cc", "src/hb-ft.cc",
                  "test/shape/data/in-house/tests/*.tests"],
        "symbols": ["hb_ot_shape_internal", "hb_buffer_t", "hb_ft_get_glyph_h_advances", "output_glyph"],
    },
    "google/wuffs": {
        "globs": ["release/c/wuffs-v0.4.c"],
        "symbols": ["wuffs_gif__decoder", "disposal", "wuffs_png__decoder"],
    },
}


def run(cmd, cwd=None, timeout=900):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def clone(repo):
    dest = CLONES / repo.split("/")[1]
    if dest.exists() and (dest / ".git").exists():
        return dest, "cached"
    CLONES.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    r = run(["git", "clone", "--depth", "1", "--single-branch",
             f"https://github.com/{repo}.git", str(dest)])
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-200:])
    return dest, f"cloned {time.time()-t0:.0f}s"


def sha256_file(p: Path):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_tree(root: Path, depth=2, cap=120):
    out, q = [], [(root, 0)]
    while q:
        d, lv = q.pop(0)
        if lv > depth or len(out) >= cap:
            continue
        try:
            kids = sorted([p for p in d.iterdir() if p.is_dir() and ".git" not in p.parts])
        except OSError:
            continue
        for k in kids:
            out.append(str(k.relative_to(root)))
            q.append((k, lv + 1))
    return out


SYMBOL_CLASS_RE = re.compile(r"\b(?:class|struct|interface|object)\s+([A-Z][A-Za-z0-9_]+)")
SYMBOL_FN_RE = re.compile(r"\b(?:def|fun|void|bool|int|long|float|double|String)\s+(on[A-Z][A-Za-z0-9_]*)\(")


def file_evidence(p: Path, symbols):
    ev = {"path": str(p.relative_to(CURRENT_ROOT)), "bytes": p.stat().st_size,
          "sha256": sha256_file(p)}
    try:
        text = p.read_text(errors="replace")
        lines = text.splitlines()
        classes = sorted({m.group(1) for m in SYMBOL_CLASS_RE.finditer(text)})[:40]
        callbacks = sorted({m.group(1) for m in SYMBOL_FN_RE.finditer(text)})[:40]
        ev["classes_structs"] = classes
        ev["on_callbacks"] = callbacks
        hits = {}
        for sym in symbols:
            idxs = [i + 1 for i, l in enumerate(lines) if sym in l][:10]
            if idxs:
                hits[sym] = idxs
        ev["symbol_line_hits"] = hits
    except Exception as e:
        ev["read_error"] = str(e)[:80]
    return ev


CURRENT_ROOT = None


def harvest(repo, spec):
    global CURRENT_ROOT
    root, note = clone(repo)
    CURRENT_ROOT = root
    head = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
    files, seen = [], set()
    for pat in spec.get("globs", []):
        matches = [p for p in root.rglob(pat.replace("? ", "")) if p.is_file()][:40]
        for p in matches:
            rel = str(p.relative_to(root))
            if rel in seen:
                continue
            seen.add(rel)
            files.append(p)
    rec = {"repository": repo, "clone_head_sha": head, "clone_note": note,
           "top_level": sorted(p.name for p in root.iterdir() if not p.name.startswith(".git"))[:80],
           "dir_tree_d2": dir_tree(root),
           "files": [file_evidence(p, spec.get("symbols", [])) for p in files],
           "test_dirs": {}}
    for d in root.iterdir():
        if d.is_dir() and ("test" in d.name.lower() or "fixture" in d.name.lower() or "golden" in d.name.lower()):
            n = sum(1 for p in d.rglob("*") if p.is_file())
            rec["test_dirs"][str(d.relative_to(root))] = n
    return rec


def main():
    results = []
    for repo, spec in CLONE_SPECS.items():
        t0 = time.time()
        try:
            rec = harvest(repo, spec)
            print(f"  OK   {repo:44s} files={len(rec['files']):3d} testdirs={len(rec['test_dirs'])} ({time.time()-t0:.0f}s)", flush=True)
            results.append(rec)
            (BASE / "clones_harvest.json").write_text(json.dumps(
                {"generated_at": datetime.now(timezone.utc).isoformat(), "clones": results}, indent=1))
        except Exception as e:
            print(f"  FAIL {repo}: {str(e)[:120]}", flush=True)
            results.append({"repository": repo, "error": str(e)[:200]})
    print(f"wrote {BASE/'clones_harvest.json'}")


if __name__ == "__main__":
    main()
