#!/usr/bin/env python3
"""
g10_phase0_baseline.py — G10 Phase 0: selected real-APK subset baseline.

NO code changes before this baseline. For every selected APK:
  1. BASE run  : miniandroid run <apk> -o <out>/base      (default device cfg)
  2. CLICK run : miniandroid run <apk> -o <out>/click --click-test
  3. Pixel audit of screenshot (background-diff coverage)
  4. Measure/layout record from view_tree.json:
       root ViewGroup -> child hierarchy -> measured dims -> layout bounds
       -> draw result (pixel evidence)

Selected corpus (7, per G10 Rule 1):
  F8 failures (required): microtimer, billthefarmer notes, headingcalculator
  Structurally different, same mechanism guards: gmdice, simplestopwatch,
  unote, chessclock

Output: docs/evidence/g10_evidence/phase0_baseline.json + per-APK tree dumps.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MA = REPO / "miniandroid"
BIN = MA / "build" / "miniandroid"
DL = MA / "download"
OUT = REPO / "docs" / "evidence" / "g10_evidence"

SUBSET = [
    # (name, local path relative to miniandroid/, why selected)
    ("microtimer", "download/exp076_corpus/dubrowgn.microtimer_8.apk",
     "F8 keypad collapsed to left column (G09)"),
    ("billthefarmer_notes", "download/exp073_real_apps/org.billthefarmer.notes_139.apk",
     "F8 ListView rows collapsed top-left (G09)"),
    ("headingcalculator", "download/exp073_real_apps/org.debian.eugen.headingcalculator_1.apk",
     "F8/F9 custom views measured 1080x0, no draw (G09)"),
    ("gmdice", "download/exp073_real_apps/de.duenndns.gmdice_8.apk",
     "RENDERED guard - ScrollView/LinearLayout/CheckBox (G09)"),
    ("simplestopwatch", "download/exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk",
     "RENDERED guard - buttons/rows (G09)"),
    ("unote", "download/exp076_corpus/app.varlorg.unote_30.apk",
     "RENDERED guard - ListView/toolbar/FAB (G09)"),
    ("chessclock", "download/exp073_real_apps/com.chessclock.android_29.apk",
     "PARTIAL guard - null texts, LinearLayout (G09)"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def pixel_audit(png: Path) -> dict:
    """Same audit basis as G09 g09_screenshot_audit: decode PNG, measure
    non-uniform coverage against the dominant border color."""
    try:
        import zlib, struct
        data = png.read_bytes()
        pos = 8
        w = h = 0
        idat = b""
        pal = None
        trns = None
        ctype = 0
        bitd = 8
        while pos < len(data):
            ln = struct.unpack(">I", data[pos:pos+4])[0]
            typ = data[pos+4:pos+8]
            chunk = data[pos+8:pos+8+ln]
            if typ == b"IHDR":
                w, h, bitd, ctype = struct.unpack(">IIBB", chunk[:10])
            elif typ == b"PLTE":
                pal = chunk
            elif typ == b"IDAT":
                idat += chunk
            elif typ == b"IEND":
                break
            pos += 12 + ln
        raw = zlib.decompress(idat)
        ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype, 4)
        stride = w * ch + 1
        # un-filter (all 5 PNG filter types)
        out = bytearray(w * h * ch)
        prev = bytearray(w * ch)
        for row in range(h):
            off = row * stride
            ft = raw[off]
            line = bytearray(raw[off+1:off+1+w*ch])
            if ft == 1:
                for i in range(ch, len(line)):
                    line[i] = (line[i] + line[i-ch]) & 0xff
            elif ft == 2:
                for i in range(len(line)):
                    line[i] = (line[i] + prev[i]) & 0xff
            elif ft == 3:
                for i in range(len(line)):
                    a = line[i-ch] if i >= ch else 0
                    line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xff
            elif ft == 4:
                for i in range(len(line)):
                    a = line[i-ch] if i >= ch else 0
                    b = prev[i]
                    c = prev[i-ch] if i >= ch else 0
                    p = a + b - c
                    pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    line[i] = (line[i] + pr) & 0xff
            out[row*w*ch:(row+1)*w*ch] = line
            prev = line
        def px(x, y):
            o = (y*w + x) * ch
            if ctype == 3:
                return tuple(pal[out[o]*3:out[o]*3+3])
            return tuple(out[o:o+3])
        # background = 4 corner pixels
        bg = [px(0,0), px(w-1,0), px(0,h-1), px(w-1,h-1)]
        from collections import Counter
        bgc = Counter(bg).most_common(1)[0][0]
        step = 6
        total = changed = 0
        xs, ys = [], []
        for y in range(0, h, step):
            for x in range(0, w, step):
                total += 1
                p = px(x, y)
                if max(abs(p[i]-bgc[i]) for i in range(3)) > 16:
                    changed += 1
                    xs.append(x); ys.append(y)
        bbox = [min(xs), min(ys), max(xs), max(ys)] if xs else None
        return {"w": w, "h": h, "bg": list(bgc),
                "nonbg_pct": round(100*changed/max(1,total), 2),
                "content_bbox": bbox}
    except Exception as e:
        return {"error": str(e)}


def tree_record(vt: dict) -> dict:
    """Extract root ViewGroup chain + key measured/bounds info."""
    nodes = vt.get("nodes", vt if isinstance(vt, list) else [])
    byid = {n.get("object_id"): n for n in nodes}
    if not nodes:
        return {"error": "no nodes"}
    children_map = {n.get("object_id"): n.get("parent_id") for n in nodes}
    roots = [n for n in nodes if n.get("parent_id") not in byid]
    def desc(n, depth=0, maxdepth=4):
        if depth > maxdepth:
            return None
        cls = (n.get("class") or "").split(";")[-2].split("/")[-1] if ";" in (n.get("class") or "") else (n.get("class") or "")
        rec = {"c": cls, "w": n.get("width"), "h": n.get("height"),
               "x": n.get("x"), "y": n.get("y")}
        t = (n.get("text") or "")[:24]
        if t: rec["t"] = t
        kids = []
        for cid in (n.get("children") or [])[:24]:
            c = byid.get(cid)
            if c: kids.append(desc(c, depth+1, maxdepth))
        rec["kids"] = [k for k in kids if k]
        return rec
    return {"node_count": len(nodes), "roots": [desc(r) for r in roots]}


def run_apk(apk: Path, outdir: Path, extra: list) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([str(BIN), "run", str(apk), "-o", str(outdir)] + extra,
                          capture_output=True, text=True, timeout=180)
    log = proc.stdout + proc.stderr
    (outdir / "console.log").write_text(log)
    return {
        "rc": proc.returncode,
        "status": "SUCCESS" if "Status: SUCCESS" in log else
                  ("PARTIAL" if "Status:" in log else "CRASH"),
        "screenshot": (outdir / "screenshot.png").exists(),
        "view_tree": (outdir / "view_tree.json").exists(),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for name, rel, why in SUBSET:
        apk = MA / rel
        rec = {"apk": name, "path": rel, "selected_because": why}
        if not apk.exists():
            rec["error"] = "apk missing from restored cache"
            results.append(rec)
            print(f"[MISS] {name}")
            continue
        rec["sha256"] = sha256(apk)
        out = Path("/tmp/g10_runs") / name
        import shutil
        shutil.rmtree(out, ignore_errors=True)
        base = run_apk(apk, out / "base", [])
        rec["base"] = base
        if base["screenshot"]:
            rec["pixel_audit"] = pixel_audit(out / "base" / "screenshot.png")
        vt = out / "base" / "view_tree.json"
        if vt.exists():
            try:
                rec["tree"] = tree_record(json.loads(vt.read_text()))
                shutil.copy(vt, OUT / f"{name}_view_tree.json")
            except Exception as e:
                rec["tree"] = {"error": str(e)}
        else:
            rec["tree"] = None
        if base["status"] in ("SUCCESS", "PARTIAL"):
            click = run_apk(apk, out / "click", ["--click-test"])
            rec["click"] = click
            cjson = out / "click" / "click_test_report.json"
            if cjson.exists():
                try:
                    cj = json.loads(cjson.read_text())
                    rec["click_report"] = {
                        k: cj[k] for k in ("present", "clickable", "dispatched",
                                           "state_changed") if k in cj}
                except Exception:
                    pass
        results.append(rec)
        print(f"[{base['status']:>7}] {name}: px={rec.get('pixel_audit',{}).get('nonbg_pct','?')}% "
              f"bbox={rec.get('pixel_audit',{}).get('content_bbox')} "
              f"nodes={rec.get('tree',{}).get('node_count') if rec.get('tree') else 0}")
    (OUT / "phase0_baseline.json").write_text(json.dumps(results, indent=1))
    print(f"\nwritten: {OUT/'phase0_baseline.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
