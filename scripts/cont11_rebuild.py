#!/usr/bin/env python3
"""cont11_rebuild.py — rebuild the batch-20 verdict ledger from on-disk run
dirs (the screening script's incremental JSON was overwritten per chunk).
Re-derives: install, screenshot sha16, png content metrics, verdict,
uncaught count, and stores per-app paths for later forensics."""
import hashlib, json, os, re, struct, zlib

BASE = "/home/z/my-project"
OUT_JSON = f"{BASE}/evidence/cont11/batch20_ledger.json"
RUN = f"{BASE}/run/w7"

LABELS = ["bouncy","fishrings","tripeaks","tictactoe_em","opmt",
          "secuso_memory","stacktower","quelltext_mem","andstatus2048","solitaire_tb",
          "alexcalc","bmi","compose_stopwatch","smt_calc","tananaev_calc",
          "mueller_stopwatch","fossify_math","deskclock","etar","textpad"]

APK_OF = {
    "bouncy": "upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk",
    "fishrings": "upload/canonical_apks/fishrings_v1.23_vc6.apk",
    "tripeaks": "upload/canonical_apks/tripeaks_v1.2.1_vc4.apk",
    "tictactoe_em": "upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk",
    "opmt": "upload/canonical_apks/opmt_v0.1.2_vc1.apk",
    "secuso_memory": "upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk",
    "stacktower": "upload/canonical_apks/stack.tower3d_1.apk",
    "quelltext_mem": "upload/cont73_apks/eu.quelltext.memory_7.apk",
    "andstatus2048": "upload/cont73_apks/org.andstatus.game2048_47.apk",
    "solitaire_tb": "upload/fdroid_batch/de.tobiasbielefeld.solitaire_71.apk",
    "alexcalc": "upload/cont11_apks/alexcalc_20.apk",
    "bmi": "upload/cont11_apks/bmi_402.apk",
    "compose_stopwatch": "upload/cont54_refetch/com.justdeax.composeStopwatch_1009011.apk",
    "smt_calc": "upload/cont54_refetch/com.simplemobiletools.calculator_8.apk",
    "tananaev_calc": "upload/cont54_refetch/com.tananaev.calculator_11.apk",
    "mueller_stopwatch": "upload/canonical_apks/com.github.muellerma.stopwatch_6.apk",
    "fossify_math": "upload/fdroid_batch/org.fossify.math_10.apk",
    "deskclock": "upload/fdroid_batch/com.best.deskclock_2037.apk",
    "etar": "upload/fdroid_batch/ws.xsoh.etar_57.apk",
    "textpad": "upload/fdroid_batch/com.maxistar.textpad_63.apk",
}

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def png_metrics(path):
    if not os.path.exists(path):
        return None
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
        return {"error": f"png-{bitd}-{ctype}", "w": w, "h": h}
    raw = zlib.decompress(idat)
    bpp = 4 if ctype == 6 else 3
    stride = w * bpp
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
    colors = {}
    for i in range(0, len(out), bpp):
        key = bytes(out[i:i+3])
        colors[key] = colors.get(key, 0) + 1
    bg = max(colors.values())
    return {"w": w, "h": h, "distinct_colors": len(colors),
            "content_px": w*h - bg, "content_frac": round((w*h-bg)/(w*h), 4)}

def classify(png):
    if png is None: return "NO_SCREENSHOT"
    if "error" in png: return "UNPARSEABLE"
    if png["content_frac"] > 0.05 and png["distinct_colors"] > 32: return "REAL_APP_CONTENT"
    if png["distinct_colors"] > 4: return "PARTIAL_CONTENT"
    return "DEFAULT_BACKGROUND_ONLY"

if __name__ == "__main__":
    recs = []
    for label in LABELS:
        rd = f"{RUN}/{label}_run1"
        shot = f"{rd}/screenshot.png"
        log = f"{rd}/run.log"
        r = {"label": label, "apk": os.path.basename(APK_OF[label]),
             "apk_sha256": sha256(f"{BASE}/{APK_OF[label]}")}
        if os.path.exists(shot):
            r["screenshot_sha16"] = hashlib.sha256(open(shot,"rb").read()).hexdigest()[:16]
            r["png"] = png_metrics(shot)
        else:
            r["png"] = None
        r["verdict"] = classify(r.get("png"))
        if os.path.exists(log):
            t = open(log, errors="replace").read()
            r["uncaught"] = t.count("EXC-UNCAUGHT-TOP")
            exc = re.search(r"EXC-UNCAUGHT-TOP\] (?:\[EXC-UNCAUGHT-TOP\] )?([A-Za-z0-9_.$/;]+)", t)
            r["first_uncaught_cls"] = exc.group(1) if exc else None
        recs.append(r)
    json.dump({"directive": "20-by-20 apps+games (user 2025-10-22)",
               "binary_sha16": "aed46450c103f2ea",
               "dooz_anchor_check": "d602648e8e401895 x3",
               "records": recs}, open(OUT_JSON, "w"), indent=1)
    vc = {}
    for r in recs: vc[r["verdict"]] = vc.get(r["verdict"], 0) + 1
    for r in recs:
        print(f"{r['label']:20s} {r['verdict']:26s} sha={r.get('screenshot_sha16','-')} "
              f"uncaught={r.get('uncaught','-')}")
    print("counts:", json.dumps(vc))
