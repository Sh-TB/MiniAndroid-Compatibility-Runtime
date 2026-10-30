#!/usr/bin/env python3
# S138 census: pixel truth + traces for the three s138 runs (ZERO-LOG:
# prints numbers/shas only; evidence JSON will carry these).
import os, sys, collections, hashlib, re, json

RUNS = {
    "dooz_pmc": "run/s138_dooz_pmc",
    "freebloks": "run/s138_freebloks",
    "tg_forkgram": "run/s138_tg_forkgram",
    "tg_official_anchor": "run/s138_tg_official_anchor",
}

def png_probe(path):
    try:
        from PIL import Image
        im = Image.open(path).convert("RGB")
        w, h = im.size
        im2 = im.resize((min(w, 270), int(h * min(w, 270) / w)))
        cnt = collections.Counter(im2.getdata())
        return {"w": w, "h": h, "distinct": len(cnt),
                "top5": [[c, n] for c, n in cnt.most_common(5)]}
    except Exception as e:
        return {"error": str(e)}

def sha16(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    except Exception:
        return None

def log_top(log, pat, n=6):
    if not os.path.exists(log):
        return []
    c = collections.Counter()
    rx = re.compile(pat)
    for line in open(log, errors="replace"):
        m = rx.search(line)
        if m:
            c[m.group(1)] += 1
    return c.most_common(n)

out = {}
for name, d in RUNS.items():
    e = {}
    shot = os.path.join(d, "screenshot.png")
    e["screenshot_sha16"] = sha16(shot)
    e["pixels"] = png_probe(shot) if os.path.exists(shot) else None
    fdir = os.path.join(d, "frames")
    e["frames_saved"] = len([f for f in os.listdir(fdir) if f.endswith(".png")]) if os.path.isdir(fdir) else 0
    e["files"] = sorted(os.listdir(d))
    out[name] = e

# dooz pmc specifics
pmc = "run/s138_dooz_pmc/pmc.log"
if os.path.exists(pmc):
    enters = []
    for i, line in enumerate(open(pmc, errors="replace"), 1):
        if "[PMC] ENTER" in line:
            enters.append([i, line.strip()])
    out["dooz_pmc"]["pmc_enters"] = enters
    out["dooz_pmc"]["uncaught_top"] = log_top(
        pmc, r"uncaught[^:]*:? ([A-Za-z0-9_.$]+(?:Exception|Error))") or \
        log_top(pmc, r"\[SYNTH-EXC\] (\S+)")

# freebloks: canvas op census + throw top
co = "run/s138_freebloks/canvas_ops.jsonl"
if os.path.exists(co):
    ops = collections.Counter()
    total = 0
    for line in open(co, errors="replace"):
        total += 1
        f = line.split("|")
        if len(f) > 2:
            ops[f[1].strip()] += 1
    out["freebloks"]["canvas_ops_total"] = total
    out["freebloks"]["canvas_ops_top"] = ops.most_common(8)
tl = "run/s138_freebloks/throw.log"
out["freebloks"]["exc_top"] = log_top(tl, r"([A-Za-z0-9_.$]+(?:Exception|Error))")[:8]

# telegram: log activity + exceptions
tg = "run/s138_tg_forkgram/tg.log"
out["tg_forkgram"]["exc_top"] = log_top(tg, r"([A-Za-z0-9_.$]+(?:Exception|Error))")[:8]
out["tg_forkgram"]["r570_classes"] = log_top(tg, r"req_cls=(\S+)")
if os.path.exists(tg):
    lastlog = [l.rstrip() for l in open(tg, errors="replace") if l.startswith("LOG/")]
    out["tg_forkgram"]["last_log_lines"] = lastlog[-8:]

print(json.dumps(out, indent=1, ensure_ascii=False)[:9000])
