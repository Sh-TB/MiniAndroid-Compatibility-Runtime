#!/usr/bin/env python3
"""
g11g12_phase0.py — G11/G12 Phase 0: current-HEAD baseline evidence for the
selected 8-APK subset. NO engine changes. For each APK:

  1. BASE run   : miniandroid run <apk> -o <out>/base
                  -> status, screenshot.png (SHA-256), console.log
  2. TRACE run  : U007_LAYOUT_DEBUG=2 -> per-view measure/layout tree
  3. Constructor-surface audit: scan console.log for constructor/inflate
     evidence lines ([U007-INFLATE], [U007-MEASURE], [EXP093-APP], ...)
  4. Pixel audit: non-bg %, content bbox from screenshot

Output: docs/evidence/g11g12_evidence/phase0/
  - phase0_baseline.json      (per-APK structured record)
  - <apk>_trace.log           (U007 lines)
  - screenshots/base/<apk>.png
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
OUT = REPO / "docs" / "evidence" / "g11g12_evidence" / "phase0"

# RULE-2 subset: mandatory 6 (per G11/G12 §2) + 2 guards. Same set before/after.
SUBSET = [
    ("headingcalculator", "download/exp073_real_apps/org.debian.eugen.headingcalculator_1.apk"),
    ("microtimer", "download/exp076_corpus/dubrowgn.microtimer_8.apk"),
    ("billthefarmer_notes", "download/exp073_real_apps/org.billthefarmer.notes_139.apk"),
    ("muellerma_stopwatch", "download/exp076_corpus/com.github.muellerma.stopwatch_6.apk"),
    ("simplestopwatch", "download/exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk"),
    ("gmdice", "download/exp073_real_apps/de.duenndns.gmdice_8.apk"),
    ("unote", "download/exp076_corpus/app.varlorg.unote_30.apk"),
    ("chessclock", "download/exp073_real_apps/com.chessclock.android_29.apk"),
]

LINE = re.compile(
    r"\[U007-LAYOUT\] (?P<indent>\s*)view (?P<vid>\d+) (?P<cls>\S+) "
    r"id_name=(?P<idn>\S*) lp=(?P<lpw>-?\d+)/(?P<lph>-?\d+) weight=(?P<w>-?[\d.]+) "
    r"orient=(?P<orient>-?\d+) measured=(?P<mw>\d+)x(?P<mh>\d+) text_size=(?P<ts>[\d.]+) "
    r"lines=(?P<ln>-?\d+) below='(?P<below>[^']*)' above='(?P<above>[^']*)' "
    r"right_of='(?P<ro>[^']*)' left_of='(?P<lo>[^']*)' cgrav=(?P<cg>0x[0-9a-fA-F]+|\d+) "
    r"text='(?P<text>.*)'")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def parse_trace(log: str):
    rows = []
    for m in LINE.finditer(log):
        d = m.groupdict()
        rows.append({
            "depth": len(m.group("indent")) // 2,
            "vid": int(d["vid"]),
            "class": d["cls"].split("/")[-1].rstrip(";").lstrip("L"),
            "class_full": d["cls"],
            "id_name": d["idn"], "lp": f"{d['lpw']}/{d['lph']}",
            "weight": float(d["w"]), "orient": int(d["orient"]),
            "measured": f"{d['mw']}x{d['mh']}",
            "text": d["text"][:40],
        })
    return rows


def read_png_pixels(path: Path):
    """Minimal PNG reader (8-bit RGB/RGBA, non-interlaced) — same law as
    g09_screenshot_audit.py (un-filter + RGB normalization)."""
    import struct, zlib
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w, h, bitd, ctype = 8, b"", 0, 0, 0, 0
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bitd, ctype = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    stride = w * ch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, out


def pixel_audit(png: Path) -> dict:
    try:
        w, h, ch, out = read_png_pixels(png)
        # background = most common color
        from collections import Counter
        cnt = Counter()
        for i in range(0, len(out), ch):
            cnt[bytes(out[i:i + 3])] += 1
        bg = cnt.most_common(1)[0][0]
        nonbg = 0
        minx, miny, maxx, maxy = w, h, -1, -1
        total = 0
        for i in range(0, len(out), ch):
            total += 1
            c = bytes(out[i:i + 3])
            if c != bg:
                nonbg += 1
                v = i // ch
                x, y = v % w, v // w
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
        bbox = None if maxx < 0 else [minx, miny, maxx, maxy]
        return {"w": w, "h": h, "bg": list(bg), "nonbg_pct":
                round(100.0 * nonbg / max(total, 1), 3),
                "content_bbox": bbox}
    except Exception as e:  # noqa: BLE001
        return {"error": repr(e)}


DIAG_PATTERNS = ["[U007-INFLATE]", "[U007-MEASURE]", "[EXP093-APP]",
                 "[EXP079-DIRECT]", "[U007-RES]"]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "screenshots" / "base").mkdir(parents=True, exist_ok=True)
    env = {"U007_LAYOUT_DEBUG": "2", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    results = []
    for name, rel in SUBSET:
        apk = MA / rel
        outdir = Path("/tmp/g11g12_runs") / name
        base_out = outdir / "base"
        base_out.mkdir(parents=True, exist_ok=True)

        proc = subprocess.run([str(BIN), "run", str(apk), "-o", str(base_out)],
                              capture_output=True, text=True, timeout=180)
        base_log = proc.stdout + proc.stderr
        (base_out / "console.log").write_text(base_log)
        status = "SUCCESS" if "Status: SUCCESS" in base_log else (
            "PARTIAL" if "Status:" in base_log else "CRASH")

        # trace run (fresh outdir to avoid overwrite)
        trace_out = outdir / "trace"
        trace_out.mkdir(parents=True, exist_ok=True)
        tproc = subprocess.run([str(BIN), "run", str(apk), "-o", str(trace_out)],
                               capture_output=True, text=True, timeout=180, env=env)
        tlog = tproc.stdout + tproc.stderr
        trace_rows = parse_trace(tlog)
        (OUT / f"{name}_trace.log").write_text(
            "\n".join(l for l in tlog.splitlines() if "U007-" in l) or "(no trace)")

        shot = base_out / "screenshot.png"
        audit = pixel_audit(shot) if shot.exists() else {"error": "missing"}
        if shot.exists():
            (OUT / "screenshots" / "base" / f"{name}.png").write_bytes(shot.read_bytes())
            shot_sha = sha256(shot)
        else:
            shot_sha = None

        diag = {p: sum(1 for l in (base_log + tlog).splitlines()
                       if l.startswith(p)) for p in DIAG_PATTERNS}

        rec = {
            "apk": name, "path": rel,
            "sha256": sha256(apk),
            "base_status": status,
            "screenshot_sha256": shot_sha,
            "pixel_audit": audit,
            "trace_rows": len(trace_rows),
            "tree": trace_rows,
            "diag_counts": diag,
        }
        results.append(rec)
        nchild = trace_rows[0].get("measured") if trace_rows else "n/a"
        print(f"[{name:22s}] status={status:8s} trace_rows={len(trace_rows):3d} "
              f"root={nchild:9s} px={audit.get('nonbg_pct','?')}% "
              f"bbox={audit.get('content_bbox','?')}")
    (OUT / "phase0_baseline.json").write_text(json.dumps(results, indent=1))
    print(f"\nwritten: {OUT / 'phase0_baseline.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
