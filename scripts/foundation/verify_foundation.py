#!/usr/bin/env python3
# scripts/foundation/verify_foundation.py — S67 independent pixel+trace verifier.
# Anti-false-success law: rc=0 / PNG-exists / nonwhite>0 are NOT proof.
# This harness re-opens each PNG (PIL), decodes pixels independently, asserts
# expected geometry/colors per fixture, and asserts ViewTree/state semantics.
import json, hashlib, os, sys
from PIL import Image

OUT = "/home/z/my-project/docs/evidence/foundation/fixtures"
RED, GREEN, BLUE, BLACK, WHITE = (255,0,0), (0,255,0), (0,0,255), (0,0,0), (255,255,255)
# S69 F-135: OK row color of f52_nanlaw (0xFF1B8A44 over white, opaque)
NAN_OK = (27, 138, 68)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def px(img, x, y):
    r, g, b = img.convert("RGB").getpixel((x, y))
    return (r, g, b)

def close(a, b, tol=2):
    return all(abs(x - y) <= tol for x, y in zip(a, b))

def nonwhite_stats(img):
    g = img.convert("RGB")
    w, h = g.size
    data = g.getdata()
    nw = sum(1 for p in data if p != WHITE)
    bbox = None
    pxs = g.load()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if pxs[x, y] != WHITE:
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
    if maxx >= 0:
        bbox = [minx, miny, maxx, maxy]
    return nw, bbox

def load_view_tree(run):
    p = os.path.join(OUT, run, "view_tree.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)

def vt_texts(tree):
    out = []
    nodes = tree.get("nodes", tree) if isinstance(tree, dict) else tree
    def walk(n):
        if isinstance(n, dict):
            t = n.get("text")
            if t: out.append(str(t))
            for c in n.get("children", []) or []:
                walk(c)
        elif isinstance(n, list):
            for c in n: walk(c)
    walk(nodes)
    return out

def vt_find(tree, cls_sub):
    res = []
    nodes = tree.get("nodes", tree) if isinstance(tree, dict) else tree
    def walk(n):
        if isinstance(n, dict):
            if cls_sub in str(n.get("class", "")):
                res.append(n)
            for c in n.get("children", []) or []:
                walk(c)
        elif isinstance(n, list):
            for c in n: walk(c)
    walk(nodes)
    return res

def run_fixture(name, pixel_asserts, extra_checks=None):
    """pixel_asserts: list of (x, y, expected_rgb, label)."""
    run = os.path.join(OUT, name)
    png = os.path.join(run, "screenshot.png")
    rec = {"fixture": name, "screenshot": png, "asserts": [], "status": "PASS"}
    if not os.path.exists(png):
        rec["status"] = "NO_VISUAL_PROOF"
        rec["error"] = "screenshot.png missing"
        return rec
    img = Image.open(png)
    img.load()
    rec["width"], rec["height"] = img.size
    rec["screenshot_sha256"] = sha256(png)
    nw, bbox = nonwhite_stats(img)
    rec["nonwhite"] = nw
    rec["bbox"] = bbox
    for (x, y, exp, label) in pixel_asserts:
        got = px(img, x, y)
        ok = close(got, exp)
        rec["asserts"].append({"label": label, "at": [x, y], "expected": list(exp),
                               "actual": list(got), "ok": ok})
        if not ok:
            rec["status"] = "FAIL"
    if nw == 0 and name != "f06_invisible":
        # A4 law: f06's correct render IS a blank frame (INVISIBLE view must
        # not draw) — an all-white frame is the EXPECTED outcome there.
        rec["status"] = "FAIL"
        rec["error"] = "frame is all-white (no content)"
    if extra_checks:
        for chk in extra_checks:
            try:
                ok, detail = chk(run, img)
            except Exception as e:
                ok, detail = False, f"exception: {e}"
            rec["asserts"].append({"label": chk.__name__, "ok": ok, "detail": detail})
            if not ok:
                rec["status"] = "FAIL"
    return rec

# ---------- extra semantic checks ----------
def chk_nonwhite_in(img_region_box, min_px):
    def _c(run, img):
        region = img.convert("RGB").crop(img_region_box)
        cnt = sum(1 for p in region.getdata() if p != WHITE)
        return (cnt >= min_px, f"nonwhite in {img_region_box} = {cnt} (min {min_px})")
    return _c

def chk_viewtree_text(expected_sub):
    def _c(run, img):
        t = load_view_tree(run)
        if t is None:
            return (False, "view_tree.json missing")
        texts = vt_texts(t)
        hit = [s for s in texts if expected_sub in s]
        return (bool(hit), f"texts={texts[:6]} expected~'{expected_sub}'")
    return _c

def chk_viewtree_geom(cls_sub, x, y, w, h, tol=1):
    def _c(run_, img):
        t = load_view_tree(run_)
        if t is None:
            return (False, "view_tree.json missing")
        cands = vt_find(t, cls_sub)
        for n in cands:
            try:
                nx, ny, nw_, nh_ = (int(n["x"]), int(n["y"]), int(n["width"]), int(n["height"]))
            except Exception:
                continue
            if abs(nx-x)<=tol and abs(ny-y)<=tol and abs(nw_-w)<=tol and abs(nh_-h)<=tol:
                return (True, f"{cls_sub} at ({nx},{ny},{nw_},{nh_})")
        return (False, f"{cls_sub} candidates={[(n.get('x'),n.get('y'),n.get('width'),n.get('height')) for n in cands]} expected=({x},{y},{w},{h})")
    return _c

def chk_click_report(min_changed_px):
    def _c(run_, img):
        p = os.path.join(OUT, run_, "click_test_report.json")
        if not os.path.exists(p):
            return (False, "click_test_report.json missing")
        rep = json.load(open(p))
        per = rep.get("per_view", [])
        if not per:
            return (False, "no clicks dispatched")
        best = max(v.get("changed_px", 0) for v in per)
        any_state = any(v.get("state_changed") for v in per)
        return (best >= min_changed_px and any_state,
                f"changed_px={best} state_changed={any_state}")
    return _c

FIXTURES = {
 "f01_color": [
    (540, 240, RED, "band1 red"), (540, 720, GREEN, "band2 green"),
    (540, 1200, BLUE, "band3 blue"), (540, 1680, BLACK, "band4 black"),
    (5, 478, RED, "band1 edge-left"), (5, 482, GREEN, "band2 edge-left (boundary@480)"),
 ],
 "f03_alpha": [
    (540, 200, (255,128,128), "50% red over white (upper)"),
    (540, 1700, WHITE, "lower stays white"),
    (5, 958, (255,128,128), "alpha band extends to y=959"),
    (5, 962, WHITE, "alpha band ends at y=960"),
 ],
 "f04_text": [],  # text checks via extra
 "f05_persian": [],  # recorded honestly (bbox+SHA); shaping law assessed separately
 "f11_linear": [
    (540, 320, (170,0,0), "third1 AA0000"), (540, 960, (0,170,0), "third2 00AA00"),
    (540, 1600, (0,0,170), "third3 0000AA"),
    (5, 639, (170,0,0), "boundary 640 -1px red"), (5, 641, (0,170,0), "boundary 640 +1px green"),
    (5, 1279, (0,170,0), "boundary 1280 -1px green"), (5, 1281, (0,0,170), "boundary 1280 +1px blue"),
 ],
 "f13_frame": [
    (100, 100, RED, "TL red"), (540, 960, GREEN, "center green"),
    (980, 1820, BLUE, "BR blue"), (540, 60, (32,32,32), "bg 202020"),
 ],
 "f14_relative": [
    (930, 150, RED, "anchor top-right red"), (150, 450, GREEN, "below+alignParentLeft green"),
    (450, 450, BLUE, "toRightOf blue"), (540, 960, (0,255,255), "centerInParent cyan"),
 ],
 "f31_resources": [
    (540, 100, (0,105,92), "bg @color/brand 00695C"),
 ],
 "f21_button": [
    (100, 100, WHITE, "bg white top-left"),
    (540, 960, (111,168,220), "default Button fill at center (Material default)"),
 ],
 "f27_nav": [], "f38_identity": [], "f45_exceptions": [],
 "f06_invisible": [
    (10, 10, WHITE, "INVISIBLE view must not draw (A4+F-124)"),
    (540, 960, WHITE, "INVISIBLE view area stays white"),
 ],
 "f18_lltop": [
    (100, 200, RED, "layout_gravity=top child at top of horizontal LL"),
    (100, 390, RED, "still inside 400px-tall child"),
    (100, 420, WHITE, "below child bottom (LL height 1920 → child ends at 400)"),
 ],
 "f32_dimen": [
    (540, 130, (18,52,86), "probe view #123456 at top (262px tall)"),
    (540, 500, WHITE, "below probe view"),
 ],
 "f08_canvasops": [
    (200, 80, (255,0,0), "drawRect fill red"),
    (140, 280, (0,0,255), "drawCircle fill blue"),
    (420, 200, (0,150,0), "drawCircle stroke ring top (F-122: Color.rgb)"),
    (400, 500, (0,0,0), "drawLine black"),
    (450, 1300, (128,0,128), "translate+drawRect purple"),
    (200, 1350, (0,0,200), "Paint.setARGB blue (A5)"),
    (660, 1350, (180,120,60), "drawRoundRect brown center (F-123 arg law)"),
    (100, 1030, (0,180,180), "clipRect region gets teal fill"),
    (500, 1030, (255,255,255), "clipRect ENFORCED: no leak outside clip (S68)"),
    (700, 1170, (255,255,255), "rotate APPLIED: rect rotated away from origin (S68 law)"),
    (130, 1665, (255,140,0), "scale(2,2) APPLIED: probe at doubled coords (S68 law)"),
    (60, 830, (255,255,255), "scale(2,2) APPLIED: pre-scale coords empty (S68 law)"),
 ],
 "f05b_persian2": [],
 "f48_bitmap": [
    (70, 60, (255,0,0), "decodeResource PNG drawn red (BitmapStore law)"),
    (260, 85, (0,200,0), "createBitmap+eraseColor green"),
    (320, 222, (0,200,0), "createScaledBitmap 240x45 green"),
    (65, 225, (0,200,0), "createBitmap crop 50x50 green"),
    (600, 500, WHITE, "no bleed below bitmap rows"),
 ],
 "f49_canstext": [],
 "f51_themeattr": [
    (390, 196, (35,69,103), "?attr/customColor from theme bag (A1)"),
    (390, 590, (0,150,136), "?android:attr/colorAccent LIGHT flavor (A10)"),
    (390, 983, (32,32,32), "?android:attr/textColorPrimary state-list law"),
 ],
 "f52_nanlaw": [
    (540, 50,   NAN_OK,  "Double.isNaN(NaN)==true (OpenJDK :1031)"),
    (540, 150,  NAN_OK,  "Double.isNaN(1.5)==false (not NaN)"),
    (540, 250,  NAN_OK,  "Double.isInfinite(+Inf)==true (:1048)"),
    (540, 350,  NAN_OK,  "Double.isInfinite(-Inf)==true"),
    (540, 450,  NAN_OK,  "Float.isNaN(NaN)==true (Float.java:631)"),
    (540, 550,  NAN_OK,  "Double.compare(1.0,2.0)==-1"),
    (540, 650,  NAN_OK,  "Double.compare(NaN,1.0)==+1 (bits law)"),
    (540, 750,  NAN_OK,  "Float.compare(+0.0,-0.0)==+1 (±0.0 law)"),
    (540, 850,  NAN_OK,  "Float.compare(2.0,2.0)==0"),
 ],
 "f50_imagefmt": [
    (150, 75, (255,0,255), "JPEG drawable decoded (A3: no silent drop)"),
    (150, 590, (0,255,255), "WebP drawable decoded"),
    (150, 983, (255,128,0), "palette PNG decoded exactly"),
    (150, 1377, (128,128,128), "grayscale PNG decoded exactly"),
    (150, 1770, (204,204,204), "GIF = explicit placeholder 0xCC (named failure)"),
 ],
}

EXTRAS = {}
EXTRAS.update({
 "f04_text": [chk_nonwhite_in((0, 0, 600, 300), 200), chk_viewtree_text("Hello 12345")],
 "f05_persian": [chk_nonwhite_in((0, 0, 900, 500), 100)],
 "f31_resources": [chk_nonwhite_in((0, 0, 900, 300), 200), chk_viewtree_text("Resource String Works")],
 "f21_button": [chk_click_report(500)],
 "f27_nav": [chk_click_report(100)],
 "f38_identity": [chk_viewtree_text("IDENT=true,false,v=42")],
 "f45_exceptions": [chk_viewtree_text("EXC=CAUGHT_AIOOBE")],
 "f06_invisible": [chk_viewtree_geom("View", 0, 0, 1080, 800)],
 "f32_dimen": [chk_viewtree_text("PX=263")],
 "f08_canvasops": [chk_nonwhite_in((0, 400, 900, 600), 300)],
 "f05b_persian2": [chk_nonwhite_in((0, 0, 1080, 400), 2000)],
 "f49_canstext": [chk_nonwhite_in((40, 60, 500, 180), 200),
                  chk_nonwhite_in((40, 240, 600, 360), 200),
                  chk_nonwhite_in((40, 420, 500, 520), 100)],
 "f11_linear": [chk_viewtree_geom("FrameLayout", 0, 0, 1080, 640),
                chk_viewtree_geom("FrameLayout", 0, 640, 1080, 640),
                chk_viewtree_geom("FrameLayout", 0, 1280, 1080, 640)],
 "f13_frame": [chk_viewtree_geom("View", 0, 0, 200, 200),
               chk_viewtree_geom("View", 440, 860, 200, 200),
               chk_viewtree_geom("View", 880, 1720, 200, 200)],
 "f14_relative": [chk_viewtree_geom("View", 780, 0, 300, 300),
                  chk_viewtree_geom("View", 0, 300, 300, 300),
                  chk_viewtree_geom("View", 300, 300, 200, 200),
                  chk_viewtree_geom("View", 340, 760, 400, 400)],
})

def main():
    only = sys.argv[1:] if len(sys.argv) > 1 else list(FIXTURES)
    results = []
    for name in only:
        rec = run_fixture(name, FIXTURES.get(name, []), EXTRAS.get(name))
        results.append(rec)
        print(f"[{rec['status']:>16}] {name}: {len([a for a in rec['asserts'] if a.get('ok')])} ok / "
              f"{len([a for a in rec['asserts'] if not a.get('ok')])} failed  "
              f"({rec.get('width','?')}x{rec.get('height','?')}, nonwhite={rec.get('nonwhite','?')}, "
              f"sha={rec.get('screenshot_sha256','?')[:12]})")
    out = os.path.join(OUT, "VERIFICATION.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=1)
    print(f"\nWrote {out}")
    npass = sum(1 for r in results if r["status"] == "PASS")
    print(f"SUMMARY: {npass}/{len(results)} PASS")
    return 0 if npass == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
