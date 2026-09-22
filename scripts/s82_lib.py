#!/usr/bin/env python3
"""s82_lib.py — S82 shared library: per-title compatibility records (§9),
status ladder derivation with evidence gating (§7/§8/§16/§37/§44),
engine runner, F-Droid sourcing, reference handling, disk guard (§39).

LAWS (S82):
  - EXECUTED ≠ VISUALLY_VERIFIED (§54): no status above what evidence proves.
  - Two-color/blank screen with a real reference UI = visual FAILURE (§16).
  - No status without evidence; validator-worthy records only (§44).
  - Session per title; APK SHA256 always; screenshot SHA256 for rendered.
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
REG = f"{ROOT}/docs/corpus/s82/title_registry.json"
RUN = f"{ROOT}/run/s82"
EVID = f"{ROOT}/docs/evidence/s82"
APK_CACHE = "/tmp/my-project/apk_cache/s82"
REF_DIR = f"{RUN}/references"
os.makedirs(APK_CACHE, exist_ok=True)
os.makedirs(REF_DIR, exist_ok=True)
os.makedirs(EVID, exist_ok=True)

LADDER = ["STATE-NOT-LOADED", "STATE-LOADED", "STATE-LAUNCHING", "STATE-ONCREATE",
          "STATE-NONBLANK", "STATE-RENDERED", "STATE-GRAPHICALLY-NONTRIVIAL",
          "STATE-INTERACTIVE", "STATE-STATE-CHANGED",
          "STATE-SEMANTICALLY-CORRELATED", "STATE-VISUALLY-VERIFIED"]


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_registry():
    return json.load(open(REG))


def save_registry(d):
    json.dump(d, open(REG, "w"), indent=1)


def title_by_pkg(reg):
    return {t["PACKAGE"]: t for t in reg["TITLES"]}


# --------------------------------------------------------------- sourcing
def fdroid_apk_url(pkg):
    """resolve latest version via F-Droid v1 API -> (url, vcode, vname) or None"""
    try:
        out = subprocess.run(["curl", "-s", "-m", "25",
                              f"https://f-droid.org/api/v1/packages/{pkg}"],
                             capture_output=True, timeout=30).stdout
        d = json.loads(out)
        p = (d.get("packages") or [{}])[0]
        if not p.get("versionCode"):
            return None
        return (f"https://f-droid.org/repo/{pkg}_{p['versionCode']}.apk",
                p.get("versionCode"), p.get("versionName"))
    except Exception:
        return None


def fdroid_screenshot_urls(pkg, maxn=3):
    """scrape the F-Droid package page for official phoneScreenshots URLs."""
    try:
        out = subprocess.run(["curl", "-s", "-L", "-m", "30",
                              f"https://f-droid.org/en/packages/{pkg}/"],
                             capture_output=True, timeout=40).stdout.decode("utf-8", "ignore")
    except Exception:
        return []
    urls = re.findall(
        r'https://f-droid\.org/repo/[^"\' ]*?phoneScreenshots/[^"\' ]+?\.(?:png|jpg|jpeg|webp)',
        out)
    seen, res = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            res.append(u)
        if len(res) >= maxn:
            break
    return res


def fetch_url(url, dest, timeout=180, min_size=10000):
    if os.path.exists(dest) and os.path.getsize(dest) >= min_size:
        return True
    r = subprocess.run(["curl", "-s", "-L", "-m", str(timeout), "-o", dest, url])
    ok = (r.returncode == 0 and os.path.exists(dest)
          and os.path.getsize(dest) >= min_size)
    if not ok and os.path.exists(dest):
        os.remove(dest)
    return ok


def source_apk(pkg, version_code=None):
    """F-Droid -> APK cache (external, deduped by pkg_vc). Returns dict."""
    rec = {"SOURCE": "F-DROID", "APK_URL": "", "APK_SHA256": "", "APK_PATH": "",
           "VERSION": "", "VERSION_CODE": "", "STATUS": "SOURCE_FAIL"}
    cached = sorted(glob.glob(f"{APK_CACHE}/{pkg}_*.apk"))
    if version_code:
        exact = [c for c in cached if f"{pkg}_{version_code}.apk" in c]
        cached = exact or cached
    if cached:
        rec.update(APK_PATH=cached[0], APK_SHA256=sha256_file(cached[0]),
                   VERSION=cached[0].rsplit("_", 1)[1][:-4], STATUS="SOURCED")
        rec["VERSION_CODE"] = cached[0].rsplit("_", 1)[1][:-4]
        return rec
    got = fdroid_apk_url(pkg)
    if not got:
        rec["STATUS"] = "SOURCE_NOT_RECOVERED"
        return rec
    url, vc, vn = got
    dest = f"{APK_CACHE}/{pkg}_{vc}.apk"
    if not fetch_url(url, dest):
        rec["STATUS"] = "DOWNLOAD_FAIL"
        rec["APK_URL"] = url
        return rec
    rec.update(APK_URL=url, APK_PATH=dest, APK_SHA256=sha256_file(dest),
               VERSION=str(vn), VERSION_CODE=str(vc), STATUS="SOURCED")
    return rec


# --------------------------------------------------------------- execution
def run_engine(apk, outdir, frames=8, frame_delay=300, taps=None, timeout=420):
    """One real engine session. Returns dict with rc, frames, log path, stderr
    excerpt + crash classification. taps = list of (x, y, frame)."""
    os.makedirs(outdir, exist_ok=True)
    log = f"{outdir}.log"
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", str(frame_delay),
           "-o", outdir, apk]
    for (x, y, fr) in (taps or []):
        cmd += ["--tap", f"{x},{y}@{fr}"]
    t0 = time.time()
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=timeout)
        except subprocess.TimeoutExpired:
            rc = -1
    dur = round(time.time() - t0, 1)
    fr = sorted(glob.glob(f"{outdir}/frames/frame_*.png"))
    text = open(log, errors="ignore").read() if os.path.exists(log) else ""
    return {"RUN_RC": rc, "FRAMES": len(fr), "FRAME_PATHS": fr,
            "LOG": log, "DURATION_S": dur, "LOG_TEXT": text}


def classify_log(text):
    """crash/failure classification from the engine log (§7 failure labels)."""
    f = []
    low = text.lower()
    if "oncreate" in low and ("npe" in low or "nullpointer" in low
                              or "unwind" in low or "exception" in low):
        f.append("FAIL-ONCREATE")
    if "nullpointerexception" in low:
        f.append("FAIL-NPE")
    if "uncaught exception" in low or "process.*unwind" in low or rc_hint_crash(text):
        f.append("FAIL-CRASH")
    if "anr" in low:
        f.append("FAIL-ANR")
    if "timeout" in low or "timed out" in low:
        f.append("FAIL-HANG")
    if "resources" in low and "notfound" in low:
        f.append("FAIL-RESOURCE")
    if "notfoundexception" in low:
        f.append("FAIL-RESOURCE")
    if "classnotfound" in low:
        f.append("FAIL-LIFECYCLE")
    if "illegalview" in low or "measure" in low:
        f.append("FAIL-MEASURE")
    if not f and text.strip():
        f.append("FAIL-UNKNOWN")
    return f


def rc_hint_crash(text):
    return "fatal" in text.lower() or "abort" in text.lower()


def frame_to_jpg(png, jpg, quality=72, maxside=540):
    """compress a rendered frame to the evidence JPG policy (<=100KB)."""
    try:
        from PIL import Image
        im = Image.open(png).convert("RGB")
        if max(im.size) > maxside:
            im.thumbnail((maxside, maxside))
        im.save(jpg, "JPEG", quality=quality)
        return os.path.getsize(jpg)
    except Exception:
        return 0


# ------------------------------------------------------- status derivation
def derive_status(visual, run, taps_used, state_change_px, ref_present,
                  ref_comparison):
    """§7 ladder + §8 separation + §16 two-color failure + §44 evidence gates.

    Returns (STATE, graph, graphics, interaction, state_change, fails, notes).
    NEVER grants STATE-VISUALLY-VERIFIED (L5 = human review only, §31).
    """
    frames = run["FRAMES"]
    rc = run["RUN_RC"]
    fails = classify_log(run["LOG_TEXT"])
    uniq = (visual or {}).get("UNIQUE_COLORS", 0)
    nonbg = (visual or {}).get("NON_BACKGROUND_RATIO", 0.0)
    img_px = (visual or {}).get("IMAGE_PIXELS", 0)
    icon_px = (visual or {}).get("ICON_PIXELS", 0)
    text_px = (visual or {}).get("TEXT_PIXELS", 0)
    flags = list((visual or {}).get("FLAGS", []))
    notes = []

    if frames == 0:
        state = "STATE-LOADED" if rc == 0 else "STATE-NOT-LOADED"
        if rc != 0:
            fails = fails or ["FAIL-CRASH"]
        graph = "NONE"
        interaction = "NONE"
        stch = "NONE"
        return state, graph, interaction, stch, fails, flags, notes

    # frames exist -> at least NONBLANK pixels produced
    # §16 tightened: uniq<=2 is a two-color screen UNLESS real text is painted
    # (§1: text-only visible = RENDERED). P9-class blank faces have text_px=0.
    if uniq <= 2 and text_px < 500:
        state = "STATE-NONBLANK"
        graph = "NONE"
        notes.append("TWO_COLOR_SCREEN (§16: visual failure vs any real reference UI)")
        if "FAIL-ONCREATE" in fails:
            pass
        elif not fails:
            fails = ["FAIL-PALETTE"]
        else:
            fails.append("FAIL-PALETTE")
        # §29 honesty: record the interaction attempt even on a dead UI
        interaction = "TAP_DISPATCHED_NO_RESPONSE" if taps_used else "NONE"
        stch = "NONE"
        return state, graph, interaction, stch, fails, flags, notes

    state = "STATE-RENDERED"
    graph = "TEXT_ONLY"
    if uniq >= 8 or nonbg >= 0.02 or icon_px > 0 or img_px > 0:
        state = "STATE-GRAPHICALLY-NONTRIVIAL"
        graph = "NONTRIVIAL"
    interaction = "NONE"
    stch = "NONE"
    if taps_used:
        interaction = "TAP_DISPATCHED"
        if state_change_px and state_change_px > 250:
            interaction = "INPUT_RESPONSE_PX"
            state = max_ladder(state, "STATE-INTERACTIVE")
            stch = "PIXEL_DIFF_PROVEN"
            state = max_ladder(state, "STATE-STATE-CHANGED")
        else:
            notes.append("tap dispatched but no proven state change")
    if ref_present and ref_comparison:
        lvl = ref_comparison.get("LEVEL", 0)
        if lvl >= 3:
            state = max_ladder(state, "STATE-SEMANTICALLY-CORRELATED")
        notes.append(f"reference comparison level {lvl}")
    return state, graph, interaction, stch, fails, flags, notes


def max_ladder(a, b):
    return a if LADDER.index(a) >= LADDER.index(b) else b


# ------------------------------------------------------------- references
def get_reference(pkg, mandatory_url=""):
    """§10: official F-Droid screenshot as reference, with provenance+SHA.
    Returns dict; NEVER fabricates a screenshot."""
    rec = {"STATUS": "REFERENCE_NOT_AVAILABLE", "URL": "", "SHA256": "",
           "SOURCE": "F-Droid official package page", "PATH": ""}
    urls = []
    if mandatory_url:
        urls = [mandatory_url]
    urls += [u for u in fdroid_screenshot_urls(pkg) if u not in urls]
    if not urls:
        return rec
    for u in urls[:2]:
        dest = f"{REF_DIR}/{pkg}__{os.path.basename(u)}"
        if fetch_url(u, dest, min_size=2000):
            rec.update(STATUS="OK", URL=u, SHA256=sha256_file(dest), PATH=dest)
            return rec
    return rec


def palette_of(png):
    """compact palette for §19 comparison (dominant colors + ranges)."""
    try:
        from PIL import Image
        im = Image.open(png).convert("RGB").resize((108, 192))
        px = list(im.getdata())
        from collections import Counter
        c = Counter(px)
        tot = len(px)
        dom = c.most_common(5)
        lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px]
        sat = [(max(p) - min(p)) for p in px]
        return {
            "UNIQUE_COLORS": len(c),
            "DOMINANT": [{"rgb": list(k), "ratio": round(v / tot, 3)} for k, v in dom],
            "LUMINANCE_RANGE": [round(min(lum), 1), round(max(lum), 1)],
            "SATURATION_RANGE": [min(sat), max(sat)],
        }
    except Exception:
        return {}


def compare_reference(ref_png, ma_png):
    """§18/§19/§30: structured comparison — NOT a single pixel-diff score."""
    rp, mp = palette_of(ref_png), palette_of(ma_png)
    if not rp or not mp:
        return {"STATUS": "COMPARISON_FAILED", "LEVEL": 0}
    r_dom = {tuple(d["rgb"]) for d in rp["DOMINANT"][:3]}
    m_dom = {tuple(d["rgb"]) for d in mp["DOMINANT"][:3]}
    dom_overlap = len(r_dom & m_dom) / max(1, len(r_dom))
    color_gap = (rp["UNIQUE_COLORS"] - mp["UNIQUE_COLORS"]) / max(1, rp["UNIQUE_COLORS"])
    level = 0
    if dom_overlap >= 0.34:
        level = 1
    if mp["UNIQUE_COLORS"] >= 8 and color_gap < 0.9:
        level = 2
    if dom_overlap >= 0.66 and mp["UNIQUE_COLORS"] >= 12:
        level = 3
    verdict = "VISUAL_MATCH_CANDIDATE" if level >= 2 else \
              "PARTIAL" if level == 1 else "VISUAL_FAIL"
    return {"STATUS": verdict, "LEVEL": level,
            "REFERENCE_PALETTE": rp, "MINIANDROID_PALETTE": mp,
            "DOMINANT_COLOR_OVERLAP": round(dom_overlap, 2),
            "UNIQUE_COLOR_GAP": round(color_gap, 2)}


def disk_free_gb():
    st = os.statvfs(ROOT)
    return round(st.f_bavail * st.f_frsize / (1 << 30), 2)
