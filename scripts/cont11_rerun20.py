#!/usr/bin/env python3
"""cont11_rerun20.py — post-fix batch re-run (same 20 APKs, fresh runs on the
existing stores; chunked calls append via --labels and MERGE into the ledger
JSON). Re-derives verdicts exactly like the screening pass."""
import hashlib, json, os, re, shutil, struct, subprocess, sys, zlib

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"
OUT_DIR = f"{BASE}/run/w7"
LEDGER = f"{BASE}/evidence/cont11/batch20_ledger.json"

PKG_OF = {
    "bouncy": "com.dozingcatsoftware.bouncy",
    "fishrings": "eu.veldsoft.fish.rings",
    "tripeaks": "eu.veldsoft.tri.peaks",
    "tictactoe_em": "com.emmanuelmess.tictactoe",
    "opmt": "one.scarecrow.games.OPMT",
    "secuso_memory": "org.secuso.privacyfriendlymemory",
    "stacktower": "stack.tower3d",
    "quelltext_mem": "eu.quelltext.memory",
    "andstatus2048": "org.andstatus.game2048",
    "solitaire_tb": "de.tobiasbielefeld.solitaire",
    "alexcalc": "net.alexbarry.calc_android",
    "bmi": "com.zola.bmi",
    "compose_stopwatch": "com.justdeax.composeStopwatch",
    "smt_calc": "com.simplemobiletools.calculator",
    "tananaev_calc": "com.tananaev.calculator",
    "mueller_stopwatch": "com.github.muellerma.stopwatch",
    "fossify_math": "org.fossify.math",
    "deskclock": "com.best.deskclock",
    "etar": "ws.xsoh.etar",
    "textpad": "com.maxistar.textpad",
}

def sha16(p):
    if not os.path.exists(p): return None
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def png_metrics(path):
    if not os.path.exists(path): return None
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n": return {"error": "not-png"}
    pos, w, h, bitd, ctype = 8, 0, 0, 0, 0
    idat = b""
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+ln]
        if typ == b"IHDR": w, h, bitd, ctype = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT": idat += chunk
        elif typ == b"IEND": break
        pos += 12 + ln
    if bitd != 8 or ctype not in (2, 6): return {"error": f"png-{bitd}-{ctype}"}
    raw = zlib.decompress(idat)
    bpp = 4 if ctype == 6 else 3
    stride = w * bpp
    out = bytearray(w * h * bpp)
    prev = bytearray(stride); p = 0
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
    colors = {}
    for i in range(0, len(out), bpp):
        colors[bytes(out[i:i+3])] = colors.get(bytes(out[i:i+3]), 0) + 1
    bg = max(colors.values())
    return {"w": w, "h": h, "distinct_colors": len(colors),
            "content_px": w*h - bg, "content_frac": round((w*h-bg)/(w*h), 4)}

def classify(png):
    if png is None: return "NO_SCREENSHOT"
    if "error" in png: return "UNPARSEABLE"
    if png["content_frac"] > 0.05 and png["distinct_colors"] > 32: return "REAL_APP_CONTENT"
    if png["distinct_colors"] > 4: return "PARTIAL_CONTENT"
    return "DEFAULT_BACKGROUND_ONLY"

def run_one(label):
    pkg = PKG_OF[label]
    store = f"{OUT_DIR}/store_{label}"
    out = f"{OUT_DIR}/{label}_fix1"
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out, exist_ok=True)
    env = dict(os.environ)
    for k in list(env):
        if k.startswith("MINIANDROID_"): env.pop(k)
    try:
        subprocess.run([BIN, "run", "--package", pkg, "--data-root", store,
                        "--execution-mode", "real-dalvik", "-o", out,
                        "--max-seconds", "120", "--frames", "40"],
                       stdout=open(f"{out}/run.log", "w"),
                       stderr=subprocess.STDOUT, env=env, timeout=360)
    except subprocess.TimeoutExpired:
        pass
    log = open(f"{out}/run.log", errors="replace").read() if os.path.exists(f"{out}/run.log") else ""
    r = {"label": label, "sha16": sha16(f"{out}/screenshot.png"),
         "png": png_metrics(f"{out}/screenshot.png")}
    r["verdict"] = classify(r["png"])
    r["uncaught"] = log.count("EXC-UNCAUGHT-TOP")
    return r

if __name__ == "__main__":
    ledger = json.load(open(LEDGER))
    recs = {r["label"]: r for r in ledger["records"]}
    sel = sys.argv[1:] or list(PKG_OF)
    for label in sel:
        r = run_one(label)
        recs[label]["fix1"] = {k: r[k] for k in ("sha16", "verdict", "uncaught")}
        recs[label]["fix1"]["png"] = r["png"]
        print(f"{label:20s} {r['verdict']:26s} sha={r['sha16']} uncaught={r['uncaught']}", flush=True)
    ledger["records"] = list(recs.values())
    vc = {}
    for r in recs.values():
        v = r.get("fix1", {}).get("verdict", r.get("verdict", "?"))
        vc[v] = vc.get(v, 0) + 1
    print("FIX1 verdict counts:", json.dumps(vc))
    json.dump(ledger, open(LEDGER, "w"), indent=1)
