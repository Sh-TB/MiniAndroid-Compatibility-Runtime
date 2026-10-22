#!/usr/bin/env python3
"""CONT-11 W7 — the 20-by-20 batch directive (user 2025-10-22):

  "۲۰ تا ۲۰ برنامه و بازی" — batches of 20 apps+games; strengthen the base;
  fix generic roots; comment 'problem solved'; move forward.

Batch 1 (this script): 10 games + 10 apps, LAW-001-clean (pure-dex or
x86_64-bearing). One screening run each at the current binary. Per-APK
record: sha256, abi, install verdict, launch, draw ops, uncaught count,
view-tree nodes, screenshot sha16 + content pixel metrics.

Writes evidence/cont11/batch20_screening.json.
"""
import hashlib, json, os, re, shutil, struct, subprocess, sys, zlib

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"
OUT_DIR = f"{BASE}/run/w7"
OUT_JSON = f"{BASE}/evidence/cont11/batch20_screening.json"

# (label, apk_path) — 10 games + 10 apps
BATCH = [
    # --- GAMES (10) ---
    ("bouncy",        f"{BASE}/upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk"),
    ("fishrings",     f"{BASE}/upload/canonical_apks/fishrings_v1.23_vc6.apk"),
    ("tripeaks",      f"{BASE}/upload/canonical_apks/tripeaks_v1.2.1_vc4.apk"),
    ("tictactoe_em",  f"{BASE}/upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk"),
    ("opmt",          f"{BASE}/upload/canonical_apks/opmt_v0.1.2_vc1.apk"),
    ("secuso_memory", f"{BASE}/upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk"),
    ("stacktower",    f"{BASE}/upload/canonical_apks/stack.tower3d_1.apk"),
    ("quelltext_mem", f"{BASE}/upload/cont73_apks/eu.quelltext.memory_7.apk"),
    ("andstatus2048", f"{BASE}/upload/cont73_apks/org.andstatus.game2048_47.apk"),
    ("solitaire_tb",  f"{BASE}/upload/fdroid_batch/de.tobiasbielefeld.solitaire_71.apk"),
    # --- APPS (10) ---
    ("alexcalc",      f"{BASE}/upload/cont11_apks/alexcalc_20.apk"),
    ("bmi",           f"{BASE}/upload/cont11_apks/bmi_402.apk"),
    ("compose_stopwatch", f"{BASE}/upload/cont54_refetch/com.justdeax.composeStopwatch_1009011.apk"),
    ("smt_calc",      f"{BASE}/upload/cont54_refetch/com.simplemobiletools.calculator_8.apk"),
    ("tananaev_calc", f"{BASE}/upload/cont54_refetch/com.tananaev.calculator_11.apk"),
    ("mueller_stopwatch", f"{BASE}/upload/canonical_apks/com.github.muellerma.stopwatch_6.apk"),
    ("fossify_math",  f"{BASE}/upload/fdroid_batch/org.fossify.math_10.apk"),
    ("deskclock",     f"{BASE}/upload/fdroid_batch/com.best.deskclock_2037.apk"),
    ("etar",          f"{BASE}/upload/fdroid_batch/ws.xsoh.etar_57.apk"),
    ("textpad",       f"{BASE}/upload/fdroid_batch/com.maxistar.textpad_63.apk"),
]

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def abi_of(apk):
    out = subprocess.run(["unzip", "-l", apk], capture_output=True, text=True).stdout
    libs = sorted(set(re.findall(r"lib/([a-z0-9_-]+)/", out)))
    if not libs:
        return "PURE_DEX"
    return "MIXED:" + ",".join(libs)

def png_metrics(path):
    """Exact content metrics from the screenshot: size, distinct colors,
    non-background pixel count (background = most common color)."""
    if not os.path.exists(path):
        return None
    try:
        import png as pypng  # pypng if available
    except Exception:
        pypng = None
    # minimal PNG decode via zlib (RGBA 8-bit only) — engine screenshots are RGBA
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return {"error": "not-png"}
    pos, w, h, bitd, ctype = 8, 0, 0, 0, 0
    idat = b""
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+ln]
        if typ == b"IHDR":
            w, h, bitd, ctype = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if bitd != 8 or ctype not in (2, 6):
        return {"error": f"unsupported-png-{bitd}-{ctype}", "w": w, "h": h}
    raw = zlib.decompress(idat)
    bpp = 4 if ctype == 6 else 3
    stride = w * bpp
    # un-filter
    out = bytearray(w * h * bpp)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ft = raw[p]; p += 1
        line = bytearray(raw[p:p+stride]); p += stride
        if ft == 1:
            for i in range(bpp, stride): line[i] = (line[i] + line[i-bpp]) & 0xFF
        elif ft == 2:
            for i in range(stride): line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i-bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i-bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i-bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2*c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y*stride:(y+1)*stride] = line
        prev = line
    # metrics
    colors = {}
    for i in range(0, len(out), bpp):
        key = bytes(out[i:i+3])
        colors[key] = colors.get(key, 0) + 1
    bg = max(colors.values())
    return {"w": w, "h": h, "distinct_colors": len(colors),
            "bg_px": bg, "content_px": w*h - bg,
            "content_frac": round((w*h - bg) / (w*h), 4)}

def classify(png):
    if png is None: return "NO_SCREENSHOT"
    if "error" in png: return "UNPARSEABLE"
    if png["content_frac"] > 0.05 and png["distinct_colors"] > 32: return "REAL_APP_CONTENT"
    if png["distinct_colors"] > 4: return "PARTIAL_CONTENT"
    return "DEFAULT_BACKGROUND_ONLY"

def run_one(label, apk, pkg=None):
    rec = {"label": label, "apk": os.path.basename(apk), "apk_sha256": sha256(apk),
           "abi": abi_of(apk)}
    store = f"{OUT_DIR}/store_{label}"
    shutil.rmtree(store, ignore_errors=True); os.makedirs(store, exist_ok=True)
    try:
        ip = subprocess.run([BIN, "install", apk, "--data-root", store],
                            capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        rec["install"] = "TIMEOUT"; return rec
    blob = ip.stdout + ip.stderr
    if "Installed" not in blob:
        rec["install"] = f"FAIL: {blob[:200]}"; return rec
    rec["install"] = "OK"
    m = re.search(r'"package"\s*:\s*"([^"]+)"', ip.stdout)
    rec["package"] = pkg or (m.group(1) if m else "?")
    out = f"{OUT_DIR}/{label}_run1"
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out, exist_ok=True)
    env = dict(os.environ)
    for k in list(env):
        if k.startswith("MINIANDROID_"): env.pop(k)
    try:
        rp = subprocess.run(
            [BIN, "run", "--package", rec["package"], "--data-root", store,
             "--execution-mode", "real-dalvik", "-o", out, "--dump-view-tree",
             "--trace", "--max-seconds", "120", "--frames", "40"],
            stdout=open(f"{out}/run.log", "w"), stderr=subprocess.STDOUT,
            env=env, timeout=360)
        rec["rc"] = rp.returncode
    except subprocess.TimeoutExpired:
        rec["rc"] = "TIMEOUT"
    log = open(f"{out}/run.log", errors="replace").read() if os.path.exists(f"{out}/run.log") else ""
    rec["screenshot_sha16"] = hashlib.sha256(open(f"{out}/screenshot.png","rb").read()).hexdigest()[:16] if os.path.exists(f"{out}/screenshot.png") else None
    rec["png"] = png_metrics(f"{out}/screenshot.png")
    rec["verdict"] = classify(rec["png"])
    rec["uncaught"] = log.count("EXC-UNCAUGHT-TOP")
    rec["app_boundary"] = log.count("APP BOUNDARY")
    mops = re.findall(r"app_draw_ops[=:]\s*(\d+)", log)
    rec["app_draw_ops"] = int(mops[-1]) if mops else None
    vt = f"{out}/view_tree.txt"
    if os.path.exists(vt):
        lines = open(vt, errors="replace").read().splitlines()
        rec["viewtree_nodes"] = sum(1 for l in lines if l.strip())
        rec["viewtree_head"] = lines[:3]
    # crash fingerprint: first uncaught exception class+message
    exc = re.search(r"EXC-UNCAUGHT-TOP[^\n]*", log)
    if exc: rec["first_uncaught"] = exc.group(0)[:220]
    ca = re.findall(r"Caused by[^\n]*", log)
    if ca: rec["caused_by"] = [c[:200] for c in ca[:3]]
    return rec

if __name__ == "__main__":
    os.makedirs(f"{BASE}/evidence/cont11", exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    sel = sys.argv[1:] if len(sys.argv) > 1 else None
    batch = [(l, a) for l, a in BATCH if sel is None or l in sel]
    print(f"binary: {hashlib.sha256(open(BIN,'rb').read()).hexdigest()[:16]}")
    print(f"batch size: {len(batch)}")
    records = []
    for i, (label, apk) in enumerate(batch, 1):
        print(f"[{i}/{len(batch)}] {label} ...", flush=True)
        try:
            r = run_one(label, apk)
        except Exception as e:
            r = {"label": label, "harness_error": repr(e)[:300]}
        records.append(r)
        print("   ", r.get("verdict", "?"), "| ops:", r.get("app_draw_ops"),
              "| uncaught:", r.get("uncaught"), "| nodes:", r.get("viewtree_nodes"),
              flush=True)
        json.dump({"batch_directive": "20-by-20 apps+games (user 2025-10-22)",
                   "binary_sha16": hashlib.sha256(open(BIN,'rb').read()).hexdigest()[:16],
                   "records": records}, open(OUT_JSON, "w"), indent=1)
    print("=== SUMMARY ===")
    for r in records:
        print(f"{r['label']:20s} {r.get('verdict','?'):26s} ops={r.get('app_draw_ops')} "
              f"uncaught={r.get('uncaught')} nodes={r.get('viewtree_nodes')}")
    vc = {}
    for r in records:
        vc[r.get("verdict", "?")] = vc.get(r.get("verdict", "?"), 0) + 1
    print("verdict counts:", json.dumps(vc))
