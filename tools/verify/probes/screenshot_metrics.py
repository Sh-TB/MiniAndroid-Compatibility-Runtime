"""Screenshot metrics probe (brief §23/§24): state-based pixel statistics.
Metrics are DIAGNOSTIC, not success (no PNG-only success law)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))               # <repo>/tools/verify/probes
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # repo root
def run(run_dir=None):
    try:
        from PIL import Image
    except ImportError:
        return {"error": "PIL unavailable"}
    base = os.path.join(REPO, "miniandroid")
    if not run_dir:
        # newest run dir with a screenshot
        cands = []
        for d in os.listdir(os.path.join(base, "run")):
            p = os.path.join(base, "run", d, "screenshot.png")
            if os.path.exists(p):
                cands.append((os.path.getmtime(p), p))
        if not cands:
            return {"error": "no screenshots"}
        path = max(cands)[1]
    else:
        path = os.path.join(base, "run", run_dir, "screenshot.png")
        if not os.path.exists(path):
            return {"error": f"no screenshot in {run_dir}"}
    im = Image.open(path).convert("RGB")
    px = list(im.getdata())
    n = len(px)
    nonwhite = [p for p in px if not (p[0] > 248 and p[1] > 248 and p[2] > 248)]
    colors = set(nonwhite)
    if nonwhite:
        xs = [i % im.width for i, p in enumerate(px) if p in colors] if len(colors) < 200000 else []
        bbox = None
    import hashlib
    return {"path": os.path.relpath(path, base), "width": im.width, "height": im.height,
            "channels": 3, "nonzero_nonwhite_px": len(nonwhite),
            "unique_colors": len(colors),
            "mean_rgb": [round(sum(c[i] for c in px) / n, 2) for i in range(3)],
            "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}
