#!/usr/bin/env python3
"""CONT-21 / Issue #384 ARCH-001 — Phase A (inventory) + Phase B (execution-path proof).

For each family representative:
  Phase A: APK sha256, size, ABI list, package/version (engine analyze).
  Phase B: canonical runtime run (1080x1920, frames 5, 15s), screenshot sha16,
           PNG content metrics, first-divergence harvest from run.log.

Outputs:
  run/cont21/family/<target>/        per-target run artifacts
  run/cont21/family_inventory.json   Phase A table
  run/cont21/family_paths.json       Phase B table
"""
import hashlib, json, os, re, struct, subprocess, sys, zipfile
from collections import Counter

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"
OUTROOT = f"{BASE}/run/cont21/family"
os.makedirs(OUTROOT, exist_ok=True)

# target -> (family, apk path)
TARGETS = [
    ("opencalc",     "F1-base-view",   f"{BASE}/upload/opencalculator_53.apk"),
    ("stopwatch",    "F1-base-view",   f"{BASE}/upload/canonical_apks/com.github.muellerma.stopwatch_6.apk"),
    ("chessclock",   "F1-base-view",   f"{BASE}/upload/chessclock_29.apk"),
    ("unote",        "F1-base-view",   f"{BASE}/upload/canonical_apks/app.varlorg.unote_30.apk"),
    ("microtimer",   "F1-base-view",   f"{BASE}/upload/canonical_apks/dubrowgn.microtimer_8.apk"),
    ("tictactoe",    "F2-2d-canvas",   f"{BASE}/upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk"),
    ("g2048",        "F2-2d-canvas",   f"{BASE}/upload/s80_games/build_2048/g2048_v1.0_vc1.apk"),
    ("fishrings",    "F3-game-loop",   f"{BASE}/upload/canonical_apks/fishrings_v1.23_vc6.apk"),
    ("flappycow",    "F3-game-loop",   f"{BASE}/upload/flappycow_rebuilt.apk"),
    ("bouncy",       "F3-game-loop",   f"{BASE}/upload/canonical_apks/bouncy.apk"),
    ("forkgram",     "F4-messaging",   f"{BASE}/upload/forkgram_709208.apk"),
    ("telegram",     "F4-messaging",   f"{BASE}/upload/telegram_official.apk"),
    ("dooz",         "F6-compose",     f"{BASE}/upload/canonical_apks/dooz_23_toplevel.apk"),
    ("minibrowser",  "F7-webview",     f"{BASE}/upload/s133_browser/build/minibrowser_v2.0_vc2.apk"),
]
# F5 social/media: no representative in corpus — recorded honestly in the matrix.

def sha256_16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def apk_abis(p):
    try:
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            abis = sorted({n.split("/")[1] for n in names
                           if n.startswith("lib/") and "/" in n})
            return abis
    except Exception as e:
        return [f"ERR:{e}"]

def png_metrics(path):
    with open(path, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return {"sha16": sha[:16], "error": "not-png"}
    w, h = struct.unpack(">II", data[16:24])
    ctype = data[25]
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype, 4)
    idat = b""
    i = 8
    while i < len(data):
        ln = struct.unpack(">I", data[i:i+4])[0]
        if data[i+4:i+8] == b"IDAT":
            idat += data[i+8:i+8+ln]
        i += 12 + ln
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(data)).convert("RGB")
        cnt = Counter(im.getdata())
        dom_color, dom_n = cnt.most_common(1)[0]
        return {"sha16": sha[:16], "w": w, "h": h,
                "unique_colors": len(cnt),
                "dominant_color": "#%02x%02x%02x" % dom_color,
                "dominant_px": dom_n,
                "nondominant_px": w * h - dom_n,
                "nondom_share": round((w * h - dom_n) / (w * h), 4)}
    except Exception as e:
        return {"sha16": sha[:16], "w": w, "h": h, "error": str(e)[:80]}

def phase_a():
    inv = []
    for t, fam, apk in TARGETS:
        row = {"target": t, "family": fam, "apk": os.path.basename(apk),
               "apk_sha256": sha256_16(apk),
               "size_bytes": os.path.getsize(apk),
               "abis": apk_abis(apk)}
        r = subprocess.run([BIN, "analyze", apk], capture_output=True,
                           text=True, timeout=240)
        m = re.search(r'"package_name"\s*:\s*"([^"]+)"', r.stdout)
        mv = re.search(r'"version_name"\s*:\s*"([^"]+)"', r.stdout)
        ma = re.search(r'"main_activity_full"\s*:\s*"([^"]+)"', r.stdout)
        row["package"] = m.group(1) if m else None
        row["version"] = mv.group(1) if mv else None
        row["main_activity"] = ma.group(1) if ma else None
        inv.append(row)
        print(f"A {t:12s} {row['apk_sha256'][:16]} pkg={row['package']} abi={row['abis']}")
    return inv

DIVERGENCE_PATTERNS = [
    r"\[SYNTH-EXC\][^\n]{0,140}",
    r"\[F\d+[^\]]*\][^\n]{0,140}",
    r"uncaught[^\n]{0,140}",
    r"APP BOUNDARY[^\n]{0,140}",
    r"Status\s*:\s*\w+",
    r"Uncaught exception[^\n]{0,140}",
    r"Exception[^\n]{0,120}",
    r"activity[^\n]{0,100}",
    r"onCreate[^\n]{0,100}",
]

def phase_b(target, apk):
    o = f"{OUTROOT}/{target}"
    os.system(f"rm -rf {o} && mkdir -p {o}")
    cmd = [BIN, "run", apk, "--width", "1080", "--height", "1920",
           "--frames", "5", "--max-seconds", "15", "-o", o]
    with open(f"{o}/run.log", "w") as f:
        try:
            r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT,
                               timeout=300)
            rc = r.returncode
        except subprocess.TimeoutExpired:
            rc = "TIMEOUT"
    log = open(f"{o}/run.log", errors="replace").read()
    shots = [p for p in os.listdir(o) if p.endswith(".png")]
    metrics = {}
    if "screenshot.png" in shots:
        metrics = png_metrics(f"{o}/screenshot.png")
    hits = []
    seen = set()
    for pat in DIVERGENCE_PATTERNS:
        for m in re.finditer(pat, log):
            line = m.group(0)[:150]
            if line not in seen:
                seen.add(line)
                hits.append(line)
            if len(hits) > 40:
                break
    lifecycle = {
        "activity_created": bool(re.search(r"Activity.*(creat|Created|lifecycle)", log, re.I)),
        "onCreate_called": "onCreate" in log,
        "onResume_called": "onResume" in log,
        "frames_present": bool(re.search(r"frame|doFrame|Choreographer", log, re.I)),
        "draw_ops": (lambda m: int(m.group(1)) if m else None)(
            re.search(r"app_draw_ops[=: ]+(\d+)", log)),
    }
    return {"target": target, "rc": rc,
            "screenshot": metrics, "first_divergences": hits[:40],
            "lifecycle": lifecycle,
            "log_lines": len(log.splitlines())}

def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "AB"
    if "A" in what:
        inv = phase_a()
        json.dump(inv, open(f"{OUTROOT.rsplit('/family',1)[0]}/family_inventory.json", "w"), indent=1)
    if "B" in what:
        only = sys.argv[2] if len(sys.argv) > 2 else None
        rows = []
        for t, fam, apk in TARGETS:
            if only and t != only:
                continue
            row = phase_b(t, apk)
            row["family"] = fam
            rows.append(row)
            sc = row["screenshot"]
            print(f"B {t:12s} rc={row['rc']} sha={sc.get('sha16','?')[:16]} "
                  f"colors={sc.get('unique_colors','?')} nondom={sc.get('nondominant_px','?')} "
                  f"div={len(row['first_divergences'])}")
        outp = f"{OUTROOT.rsplit('/family',1)[0]}/family_paths.json"
        existing = json.load(open(outp)) if os.path.exists(outp) and only else []
        existing = [r for r in existing if r["target"] != (only or "")]
        json.dump(existing + rows, open(outp, "w"), indent=1)

if __name__ == "__main__":
    main()
