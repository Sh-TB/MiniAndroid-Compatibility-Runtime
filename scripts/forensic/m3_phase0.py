#!/usr/bin/env python3
"""
scripts/forensic/m3_phase0.py — MASTER CAMPAIGN 3 §1/§2: baseline frontier re-run at c0f178a7.

Canonical-entry-point only (no fixture logic, no package branches).
Per APK:
  run A       : miniandroid run <apk> -o <out>/base      -> Status, screenshot
  run B       : identical rerun                          -> determinism pair
  trace run   : U007_LAYOUT_DEBUG=2                      -> per-view tree
  pixel audit : non-bg %, content bbox
  log scan    : first-failure signals for §18 forensics
Resumable: existing <name>.result.json records are kept (delete to re-run).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MA = REPO / "miniandroid"
BIN = MA / "build" / "miniandroid"
OUT = REPO / "docs" / "evidence" / "m3_campaign" / "phase0"

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
    ("survivalmanual", "download/master_campaign/org.ligi.survivalmanual_500.apk"),
    ("coffee", "download/master_campaign/com.github.muellerma.coffee_47.apk"),
    ("diary", "download/master_campaign/org.billtharmer.diary_1105.apk"),
    ("secuso_todo", "download/master_campaign/org.secuso.privacyfriendlytodolist_103.apk"),
]
# fix diary path typo guard
CORPUS = [(n, r.replace("billtharmer", "billthefarmer")) for n, r in CORPUS]


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
        bg = tuple(out[0:ch])
        nonbg = 0
        x0, y0, x1, y1 = w, h, -1, -1
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


def run_apk(apk: Path, outdir: Path, env_extra: dict | None = None) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    t0 = time.time()
    try:
        proc = subprocess.run([str(BIN), "run", str(apk), "-o", str(outdir)],
                              capture_output=True, text=True, timeout=150, env=env)
        log = proc.stdout + proc.stderr
        rc = proc.returncode
    except subprocess.TimeoutExpired as e:
        so, se = e.stdout or b"", e.stderr or b""
        if isinstance(so, bytes):
            so = so.decode(errors="replace")
        if isinstance(se, bytes):
            se = se.decode(errors="replace")
        log = so + se
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


def log_signals(log: str) -> dict:
    """§18 groundwork: compact first-failure signals from the run console."""
    sig = {}
    for pat, key in [
        (r"^\[BOOT\].*$", "boot"),
        (r"^\[CLASS\].*$", "class"),
        (r"^\[CLINIT\].*$", "clinit"),
        (r"^\[CTOR\].*$", "ctor"),
        (r"^\[ACTIVITY\].*$", "activity"),
        (r"^\[VIEW\].*$", "view"),
        (r"^Status: (\w+)", "status"),
    ]:
        m = re.findall(pat, log, re.M)
        if m:
            sig[key] = m if key == "status" else len(m)
    exc = re.findall(r"(Exception|Error)[:\s]", log)
    sig["exception_mentions"] = len(exc)
    last = [l for l in log.splitlines() if l.strip()]
    sig["last_line"] = last[-1][:160] if last else ""
    return sig


def main() -> int:
    only = sys.argv[1:] or None
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "screenshots" / "base").mkdir(parents=True, exist_ok=True)
    results_path = OUT / "phase0_summary.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else []
    done = {r["apk"] for r in results}
    for name, rel in CORPUS:
        if only and name not in only:
            continue
        if name in done:
            print(f"=== {name}: CACHED", flush=True)
            continue
        apk = MA / rel
        if not apk.exists():
            results.append({"apk": name, "error": f"missing: {rel}"})
            print(f"=== {name}: MISSING", flush=True)
            continue
        work = Path("/tmp/m3_runs") / name
        print(f"=== {name} ===", flush=True)
        base = run_apk(apk, work / "base")
        rerun = run_apk(apk, work / "rerun")
        trace = run_apk(apk, work / "trace", env_extra={"U007_LAYOUT_DEBUG": "2"})
        pa = pixel_audit(work / "base" / "screenshot.png") \
            if (work / "base" / "screenshot.png").exists() else None
        log = (work / "base" / "console.log").read_text(errors="replace") \
            if (work / "base" / "console.log").exists() else ""
        rec = {
            "apk": name, "rel": rel,
            "sha256": sha256(apk),
            "base": base,
            "rerun": rerun,
            "deterministic_2x": base["screenshot_sha256"] is not None and
                                base["screenshot_sha256"] == rerun["screenshot_sha256"],
            "trace": {"status": trace["status"]},
            "view_tree": view_tree_stats(
                (work / "trace" / "console.log").read_text(errors="replace"))
            if (work / "trace" / "console.log").exists() else {"present": False},
            "pixel": pa,
            "signals": log_signals(log),
        }
        shot = work / "base" / "screenshot.png"
        if shot.exists():
            import shutil
            shutil.copy(shot, OUT / "screenshots" / "base" / f"{name}.png")
        results = [r for r in results if r.get("apk") != name] + [rec]
        results_path.write_text(json.dumps(results, indent=2) + "\n")
        print(f"  base={base['status']} rc={base['rc']} "
              f"nonbg={pa['nonbg_pct'] if pa else '?'}% "
              f"det2x={rec['deterministic_2x']} "
              f"views={rec['view_tree'].get('views') if rec['view_tree'].get('present') else '-'}",
              flush=True)
    print(f"summary -> {results_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
