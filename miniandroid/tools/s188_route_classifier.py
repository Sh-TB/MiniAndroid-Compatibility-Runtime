#!/usr/bin/env python3
"""s188_route_classifier.py — S188 Phase C: per-APK route profile.

THE ALLEY LAW (user directive, S188 §1):
  The runtime must determine, BEFORE execution, which alley (route) an
  application takes.
    * A Java/View application must NOT pass through the HTML5 alley.
    * An application that plays MKV must go through the MKV alley — forcing
      it through MP4 (or any substitute) is forbidden and can never be
      credited as success.
  Static detection here is HONEST: it records what the APK contains. It is
  never treated as runtime observation (UNOBSERVED != PASS, S188 §13).

Usage:
  python3 tools/s188_route_classifier.py APK [--out DIR]
  python3 tools/s188_route_classifier.py --all MANIFEST.json --out DIR

Output: <out>/<pkg>.json  (schema S188_APK_ROUTE_PROFILE_V1)
"""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Marker table: DEX type descriptors that identify subsystems the app links.
# ---------------------------------------------------------------------------
DEX_MARKERS = {
    "LIBGDX": ["Lcom/badlogic/gdx/"],
    "LIBGDX_BOX2D": ["Lcom/badlogic/gdx/physics/box2d/"],
    "SDL": ["Lorg/libsdl/app/SDLActivity;"],
    "COMPOSE": ["Landroidx/compose/runtime/Composer;", "Landroidx/compose/ui/"],
    "APPCOMPAT": ["Landroidx/appcompat/app/AppCompatActivity;",
                  "Landroidx/appcompat/"],
    "RECYCLERVIEW": ["Landroidx/recyclerview/widget/RecyclerView;",
                     "Landroidx/recyclerview/"],
    "FRAGMENT": ["Landroidx/fragment/app/Fragment;", "Landroidx/fragment/"],
    "VIEWPAGER": ["Landroidx/viewpager/widget/ViewPager;", "Landroidx/viewpager2/"],
    "WEBVIEW": ["Landroid/webkit/WebView;"],
    "CORDOVA": ["Lorg/apache/cordova/CordovaActivity;", "Lorg/apache/cordova/"],
    "MEDIA_PLAYER": ["Landroid/media/MediaPlayer;", "Landroid/media/MediaExtractor;",
                     "Landroid/media/MediaCodec;"],
    "MEDIA3_EXO": ["Landroidx/media3/", "Lcom/google/android/exoplayer2/"],
    "SQLITE": ["Landroid/database/sqlite/SQLiteDatabase;",
               "Landroid/database/sqlite/"],
    "GLSURFACEVIEW": ["Landroid/opengl/GLSurfaceView;"],
    "SURFACEVIEW": ["Landroid/view/SurfaceView;"],
    "KOTLIN": ["Lkotlin/jvm/internal/"],
    "FLUTTER": ["Lio/flutter/embedding/engine/FlutterJNI;",
                "Lio/flutter/"],
    "TEXT_TOAST_DEFAULT": ["Landroid/widget/TextView;"],
}

NATIVE_ENGINE_LIB_MARKERS = {
    # Named engines first — a named engine is a precise alley, not a guess.
    "GODOT": ["libgodot"],
    "NATIVE_GAME_ENGINE": ["libsurge", "libthextech", "liballegro",
                           "libpython"],
}

MEDIA_EXTS = {".mkv": "MATROSKA", ".mp4": "MP4", ".webm": "WEBM",
              ".m4v": "M4V", ".3gp": "3GP", ".ogg": "OGG", ".wav": "WAV"}
HTML_MARKERS = ("index.html", "www/", "cordova", "file:///android_asset/")

DESC_RE = re.compile(rb"L[a-zA-Z0-9_/$-]+;")
PKG_RE = re.compile(rb"(?:[\x20-\x7e]\x00){3,}")  # UTF-16LE printable runs


def dex_descriptors(apk):
    descs = set()
    with zipfile.ZipFile(apk) as z:
        for name in z.namelist():
            if name.startswith("classes") and name.endswith(".dex"):
                for m in DESC_RE.finditer(z.read(name)):
                    try:
                        descs.add(m.group(0).decode())
                    except UnicodeDecodeError:
                        pass
    return descs


def manifest_strings(apk):
    """Extract printable strings from the binary AndroidManifest (AXML)."""
    try:
        with zipfile.ZipFile(apk) as z:
            data = z.read("AndroidManifest.xml")
    except KeyError:
        return []
    out = set()
    for m in PKG_RE.finditer(data):
        try:
            out.add(m.group(0).decode("utf-16-le"))
        except UnicodeDecodeError:
            pass
    # UTF-8 style AXML string pools
    for m in re.finditer(rb"[\x20-\x7e]{4,}", data):
        out.add(m.group(0).decode("ascii", "ignore"))
    return sorted(out)


def inventory(apk):
    inv = {"native_libs": [], "asset_count": 0, "media_assets": [],
           "html_assets": [], "layouts": 0, "values_strings_xml": 0}
    with zipfile.ZipFile(apk) as z:
        for n in z.namelist():
            if n.startswith("lib/") and n.endswith(".so"):
                inv["native_libs"].append(n)
            elif n.startswith("assets/"):
                inv["asset_count"] += 1
                low = n.lower()
                ext = Path(low).suffix
                if ext in MEDIA_EXTS:
                    inv["media_assets"].append(
                        {"path": n, "container": MEDIA_EXTS[ext]})
                for hm in HTML_MARKERS:
                    if hm in low:
                        inv["html_assets"].append(n)
                        break
            elif n.startswith("res/layout"):
                inv["layouts"] += 1
            elif "values" in n and n.endswith("strings.xml"):
                inv["values_strings_xml"] += 1
    inv["native_libs"].sort()
    return inv


def classify(pkg, apk_path, descs, strings, inv):
    """Route decision per S188 §1 — evidence-driven, substitution-aware."""
    has = lambda marker_set: any(
        any(mk in d for d in descs) for mk in DEX_MARKERS[marker_set])

    routes, caps, forbidden, subst = [], [], [], []

    def add(route, evidence, primary_rank=None):
        routes.append({"route": route, "evidence": evidence})

    # --- Native game routes -------------------------------------------------
    if has("LIBGDX"):
        ev = ["dex:Lcom/badlogic/gdx/"]
        if any("libgdx" in l for l in inv["native_libs"]):
            ev.append("lib:libgdx.so")
        add("LIBGDX", ev)
        caps.append({"cap": "NATIVE_LIB_LOAD", "evidence": ev})
        caps.append({"cap": "JNI", "evidence": ev})
        caps.append({"cap": "EGL_GLES", "evidence": ["libGDX renders via GL"]})
        caps.append({"cap": "ASSET_MANAGER", "evidence": ["libGDX FileHandle"]})
    if has("SDL"):
        add("SDL", ["dex:Lorg/libsdl/app/SDLActivity;"])
        caps.append({"cap": "SDL_NATIVE", "evidence": ["SDLActivity in DEX"]})
    if has("FLUTTER"):
        add("FLUTTER", ["dex:Lio/flutter/"])
        caps.append({"cap": "FLUTTER_ENGINE", "evidence":
                     ["FlutterJNI/embedding in DEX + flutter_assets"]})
    for route, marks in NATIVE_ENGINE_LIB_MARKERS.items():
        hit = [l for l in inv["native_libs"]
               if any(m in l for m in marks)]
        if hit:
            add(route, ["lib:" + l for l in hit[:3]])
            if route == "GODOT":
                caps.append({"cap": "GODOT_ENGINE_SUPPORT",
                             "evidence": ["lib:" + l for l in hit[:2]]})

    # --- HTML5 alley: ONLY for apps that truly are web-packaged -------------
    has_webview_cls = has("WEBVIEW")
    html_assets = inv["html_assets"]
    packaged_html = bool(html_assets) and (has("CORDOVA") or any(
        "index.html" in a for a in html_assets))
    if packaged_html:
        add("WEBVIEW_HTML5_PACKAGED", ["assets:" + html_assets[0]])
        caps.append({"cap": "WEBVIEW_ENGINE", "evidence": html_assets[:3]})
    elif has_webview_cls:
        # WebView used as a component (per-node route), NOT the app's alley.
        add("WEBVIEW_NODE", ["dex:Landroid/webkit/WebView;"])
        caps.append({"cap": "WEBVIEW_ENGINE",
                     "evidence": ["WebView component in DEX"]})

    # --- Java/View alleys ----------------------------------------------------
    if has("COMPOSE"):
        add("COMPOSE", ["dex:Landroidx/compose/"])
        caps.append({"cap": "COMPOSE_RUNTIME", "evidence": ["compose in DEX"]})
    view_ev = []
    if has("APPCOMPAT"):
        view_ev.append("dex:Landroidx/appcompat/")
        caps.append({"cap": "APPCOMPAT", "evidence": view_ev})
    if has("RECYCLERVIEW"):
        view_ev.append("dex:Landroidx/recyclerview/")
        caps.append({"cap": "ADAPTER_RECYCLE", "evidence": view_ev})
    if has("FRAGMENT"):
        view_ev.append("dex:Landroidx/fragment/")
    if has("GLSURFACEVIEW"):
        view_ev.append("dex:Landroid/opengl/GLSurfaceView;")
    if inv["layouts"]:
        view_ev.append(f"res/layouts={inv['layouts']}")
    if view_ev or not routes:
        add("VIEW", view_ev or ["default Dalvik Activity route"])

    # --- Media alley ---------------------------------------------------------
    # MEDIA is the app's alley ONLY if it ships playable content (media assets).
    # MediaPlayer for sound effects inside a game is a supporting capability,
    # NOT an alley — a game must not be routed through the media alley.
    media = has("MEDIA_PLAYER") or has("MEDIA3_EXO")
    if media:
        ev = []
        if has("MEDIA3_EXO"):
            ev.append("dex:media3/exoplayer")
        if has("MEDIA_PLAYER"):
            ev.append("dex:Landroid/media/MediaPlayer|MediaCodec")
        if inv["media_assets"]:
            ev.append("ships playable content: " +
                      inv["media_assets"][0]["path"])
        add("MEDIA", ev)

    # --- Capabilities from inventory ----------------------------------------
    if has("SQLITE"):
        caps.append({"cap": "SQLITE_VEND", "evidence": ["dex:sqlite"]})
    if inv["values_strings_xml"]:
        caps.append({"cap": "RESOURCE_ARSC_STRINGS",
                     "evidence": [f"strings.xml x{inv['values_strings_xml']}"]})

    # --- THE ALLEY LAW: forbidden routes & forbidden substitutions ----------
    if not has_webview_cls and not packaged_html:
        forbidden.append({
            "route": "WEBVIEW_HTML5_PACKAGED",
            "reason": ("no WebView classes and no HTML assets in APK — a Java "
                       "application must NOT pass through the HTML5 alley")})
    if not has("LIBGDX"):
        forbidden.append({"route": "LIBGDX",
                          "reason": "no libGDX classes in DEX"})
    if not has("SDL"):
        forbidden.append({"route": "SDL",
                          "reason": "no SDLActivity in DEX"})
    if not has("FLUTTER"):
        forbidden.append({"route": "FLUTTER",
                          "reason": "no Flutter embedding classes in DEX"})
    mkv = [m for m in inv["media_assets"] if m["container"] == "MATROSKA"]
    if mkv:
        caps.append({"cap": "MEDIA_DEMUX_MKV", "evidence":
                     [m["path"] for m in mkv[:3]]})
        subst.append({"required": "MEDIA_DEMUX_MKV",
                      "forbidden_substitute": "MEDIA_DEMUX_MP4",
                      "reason": ("app ships MKV content — playing MP4 instead "
                                 "is a wrong alley, never creditable")})
    if media and not mkv and not any(
            m["container"] == "MP4" for m in inv["media_assets"]):
        caps.append({"cap": "MEDIA_DEMUX_PER_ASSET",
                     "evidence": ["media classes present; container set must "
                                  "match actual assets, never substituted"]})

    # --- Primary route ranking (S188 §1 examples) ---------------------------
    # MEDIA ranks above VIEW only when the app actually ships playable content;
    # a game with MediaPlayer SFX keeps VIEW as its alley.
    media_is_alley = media and bool(inv["media_assets"])
    RANK = ["LIBGDX", "SDL", "GODOT", "FLUTTER", "NATIVE_GAME_ENGINE",
            "WEBVIEW_HTML5_PACKAGED", "COMPOSE",
            "MEDIA", "VIEW", "WEBVIEW_NODE"]
    if not media_is_alley:
        RANK = [r for r in RANK if r != "MEDIA"]
    present = [r["route"] for r in routes]
    primary = next((r for r in RANK if r in present), "VIEW")
    for r in routes:
        r["primary"] = (r["route"] == primary)

    return {
        "routes_detected": routes,
        "primary_route": primary,
        "routes_forbidden": forbidden,
        "substitutions_forbidden": subst,
        "required_capabilities": caps,
    }


def profile(apk_path):
    apk_path = Path(apk_path)
    pkg = apk_path.stem
    h = hashlib.sha256()
    with open(apk_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    descs = dex_descriptors(apk_path)
    strings = manifest_strings(apk_path)
    inv = inventory(apk_path)
    decision = classify(pkg, apk_path, descs, strings, inv)
    return {
        "schema": "S188_APK_ROUTE_PROFILE_V1",
        "pkg": pkg,
        "apk": str(apk_path),
        "apk_sha256_16": h.hexdigest()[:16],
        "static_analysis": {
            "honest": True,
            "note": ("static detection only — runtime observation required "
                     "before ANY impact credit (UNOBSERVED != PASS, S188 §13)"),
        },
        "routes_detected": decision["routes_detected"],
        "primary_route": decision["primary_route"],
        "routes_forbidden": decision["routes_forbidden"],
        "substitutions_forbidden": decision["substitutions_forbidden"],
        "required_capabilities": decision["required_capabilities"],
        "inventory": inv,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("apk", nargs="?")
    ap.add_argument("--all", help="manifest JSON with results[].path/pkg")
    ap.add_argument("--out", default="reports/apk_routes")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    jobs = []
    if args.all:
        man = json.load(open(args.all))
        rows = man if isinstance(man, list) else man.get("results", [])
        for r in rows:
            p = r.get("path")
            if r.get("status") in ("OK", "CACHED") and p and Path(p).exists():
                jobs.append(p)
    elif args.apk:
        jobs.append(args.apk)
    if not jobs:
        print("no APKs to profile", file=sys.stderr)
        return 1

    summary = []
    for p in jobs:
        prof = profile(p)
        op = out / f"{prof['pkg']}.json"
        with open(op, "w") as f:
            json.dump(prof, f, indent=1)
        summary.append({"pkg": prof["pkg"], "primary": prof["primary_route"],
                        "routes": [r["route"] for r in prof["routes_detected"]],
                        "caps": [c["cap"] for c in prof["required_capabilities"]]})
        print(f"{prof['pkg']:45s} PRIMARY={prof['primary_route']:22s} "
              f"routes={[r['route'] for r in prof['routes_detected']]}")
    with open(out / "_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=1)
    print(f"\n{len(summary)} route profiles -> {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
