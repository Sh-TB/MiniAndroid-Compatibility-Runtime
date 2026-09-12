#!/usr/bin/env python3
"""
scripts/maintenance/master_phase0.py — MASTER CAMPAIGN §2: current-HEAD real-APK baseline matrix.

For every runnable frozen-corpus APK (base set + campaign additions):
  1. BASE run    : miniandroid run <apk> -o <out>/base  -> Status, screenshot.png
  2. TRACE run   : U007_LAYOUT_DEBUG=2                  -> per-view measure/layout tree
  3. Pixel audit : non-bg %, content bbox
  4. Raw logs kept for offline first-failing-layer triage (§3)

No fixture logic, no package-name branches: everything runs through the ONE
canonical runtime entry point with default device configuration.
"""
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

REPO = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MA = REPO / "miniandroid"
BIN = MA / "build" / "miniandroid"
OUT = REPO / "docs" / "evidence" / "master_campaign" / "phase0"

# Every frozen APK on disk at campaign start (SHAs verified at fetch/restore
# time; see master_campaign/registry_additions.json). No substitutions.
CORPUS = [
    ("headingcalculator", "download/exp073_real_apps/org.debian.eugen.headingcalculator_1.apk"),
    ("microtimer", "download/exp076_corpus/dubrowgn.microtimer_8.apk"),
    ("billthefarmer_notes", "download/exp073_real_apps/org.billthefarmer.notes_139.apk"),
    ("muellerma_stopwatch", "download/exp076_corpus/com.github.muellerma.stopwatch_6.apk"),
    ("simplestopwatch", "download/exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk"),
    ("gmdice", "download/exp073_real_apps/de.duenndns.gmdice_8.apk"),
    ("unote", "download/exp076_corpus/app.varlorg.unote_30.apk"),
    ("chessclock", "download/exp073_real_apps/com.chessclock.android_29.apk"),
    ("tictactoe", "download/tictactoe.apk"),
    ("openlauncher", "download/exp076_corpus/com.benny.openlauncher_39.apk"),
    ("dooz", "download/exp076_corpus/io.github.yamin8000.dooz_18.apk"),
    ("bgclock", "download/exp076_corpus/nl.hansdezwart.bgclock_2.apk"),
    ("simplekeyboard", "download/exp076_corpus/rkr.simplekeyboard.inputmethod_145.apk"),
    ("kiss", "download/g04_corpus/fr.neamar.kiss_224.apk"),
    ("bouncy", "download/master_campaign/com.dozingcatsoftware.bouncy_43.apk"),
    ("scope", "download/master_campaign/org.billthefarmer.scope_140.apk"),
]

PIXEL_RE = None


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def pixel_audit(png: Path):
    try:
        import struct, zlib
        data = png.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        pos, w, h, bd, ct = 8, 0, 0, 0, 0
        idat = b""
        while pos < len(data):
            ln = struct.unpack(">I", data[pos:pos + 4])[0]
            typ = data[pos + 4:pos + 8]
            chunk = data[pos + 8:pos + 8 + ln]
            if typ == b"IHDR":
                w, h, bd, ct = struct.unpack(">IIBB", chunk[:10])
            elif typ == b"IDAT":
                idat += chunk
            elif typ == b"IEND":
                break
            pos += 12 + ln
        raw = zlib.decompress(idat)
        ch = {0: 1, 2: 3, 4: 2, 6: 4}.get(ct, 3)
        stride = w * ch
        # un-filter
        out = bytearray()
        prev = bytearray(stride)
        i = 0
        for y in range(h):
            f = raw[i]; i += 1
            line = bytearray(raw[i:i + stride]); i += stride
            if f == 1:
                for x in range(ch, stride):
                    line[x] = (line[x] + line[x - ch]) & 0xFF
            elif f == 2:
                for x in range(stride):
                    line[x] = (line[x] + prev[x]) & 0xFF
            elif f == 3:
                for x in range(stride):
                    a = line[x - ch] if x >= ch else 0
                    line[x] = (line[x] + ((a + prev[x]) >> 1)) & 0xFF
            elif f == 4:
                for x in range(stride):
                    a = line[x - ch] if x >= ch else 0
                    b = prev[x]
                    c = prev[x - ch] if x >= ch else 0
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    line[x] = (line[x] + pr) & 0xFF
            out += line
            prev = line
        # background = color of top-left pixel
        bg = tuple(out[0:ch])
        nonbg = 0
        x0, y0, x1, y1 = w, h, -1, -1
        step = ch  # every pixel
        for y in range(h):
            row = y * stride
            for x in range(w):
                o = row + x * ch
                px = tuple(out[o:o + ch])[:3]
                if abs(px[0] - bg[0]) + abs(px[1] - bg[1]) + abs(px[2] - bg[2]) > 24:
                    nonbg += 1
                    if x < x0: x0 = x
                    if y < y0: y0 = y
                    if x > x1: x1 = x
                    if y > y1: y1 = y
        return {"w": w, "h": h, "bg": list(bg[:3]),
                "nonbg_pct": round(100.0 * nonbg / (w * h), 4),
                "content_bbox": [x0, y0, x1, y1] if x1 >= 0 else None}
    except Exception as e:
        return {"error": str(e)}


def run_apk(apk: Path, outdir: Path, extra: list[str], env_extra: dict | None = None) -> dict:
    import os
    outdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    t0 = time.time()
    try:
        proc = subprocess.run([str(BIN), "run", str(apk), "-o", str(outdir)] + extra,
                              capture_output=True, text=True, timeout=150, env=env)
        log = proc.stdout + proc.stderr
        rc = proc.returncode
    except subprocess.TimeoutExpired as e:
        log = (e.stdout or "") + (e.stderr or "")
        rc = -9
    dt = time.time() - t0
    (outdir / "console.log").write_text(log)
    m = re.search(r"^Status: (\w+)", log, re.M)
    status = m.group(1) if m else ("CRASH" if rc else "UNKNOWN")
    return {
        "rc": rc, "status": status, "seconds": round(dt, 2),
        "screenshot_sha256": sha256(outdir / "screenshot.png")
        if (outdir / "screenshot.png").exists() else None,
    }


def view_tree_stats(log: str) -> dict:
    rows = re.findall(r"\[U007-LAYOUT\] (\s*)view (\d+) (\S+).*?measured=(\d+)x(\d+)", log)
    if not rows:
        return {"present": False}
    total = len(rows)
    zero = sum(1 for r in rows if r[3] == "0" or r[4] == "0")
    return {"present": True, "views": total, "zero_sized": zero}


def main() -> int:
    import sys
    only = sys.argv[1:] or None
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "screenshots" / "base").mkdir(parents=True, exist_ok=True)
    results = []
    for name, rel in CORPUS:
        if only and name not in only:
            continue
        apk = MA / rel
        if not apk.exists():
            results.append({"apk": name, "error": f"missing: {rel}"})
            print(f"=== {name}: MISSING", flush=True)
            continue
        work = Path("/tmp/master_runs") / name
        print(f"=== {name} ===", flush=True)
        base = run_apk(apk, work / "base", [])
        trace = run_apk(apk, work / "trace", [], env_extra={"U007_LAYOUT_DEBUG": "2"})
        pa = pixel_audit(work / "base" / "screenshot.png") \
            if (work / "base" / "screenshot.png").exists() else None
        rec = {
            "apk": name, "rel": rel,
            "sha256": sha256(apk),
            "base": base,
            "trace": {"status": trace["status"]},
            "view_tree": view_tree_stats(
                (work / "trace" / "console.log").read_text(errors="replace"))
            if (work / "trace" / "console.log").exists() else {"present": False},
            "pixel": pa,
        }
        shot = work / "base" / "screenshot.png"
        if shot.exists():
            import shutil
            shutil.copy(shot, OUT / "screenshots" / "base" / f"{name}.png")
        (OUT / f"{name}.result.json").write_text(json.dumps(rec, indent=2) + "\n")
        results.append(rec)
        print(f"  base={base['status']} rc={base['rc']} "
              f"nonbg={pa['nonbg_pct'] if pa else '?'}% "
              f"views={rec['view_tree'].get('views') if rec['view_tree'].get('present') else '-'}",
              flush=True)
    (OUT / "phase0_summary.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"summary -> {OUT}/phase0_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
