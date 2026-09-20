#!/usr/bin/env python3
"""S72-W2 corpus pixel measurement + determinism check.
Measures frame_008.png nonwhite + final screenshot nonwhite per run,
compares with S72-WAVE1 baseline, verifies fishrings determinism x3
(RULE 63/124: screenshot sha comparison). No fabrication — every number
from an actual file."""
import zlib, struct, hashlib, glob, os, json

OUT = "/home/z/my-project/run/s72_w2_corpus"
BASELINE = {  # S72_WAVE1.md §2 dashboard (nonwhite px @ 2073600)
    "bouncy": 2073600, "microtimer": 1041200, "unote": 236400,
    "opmt": 213600, "gmdice": 182500, "stopwatch": 22800,
    "tictactoe": 0, "dooz": 197, "fishrings": 0, "tripeaks": 0,
}

def png_nonwhite(p):
    if not os.path.exists(p): return None, None
    d = open(p, "rb").read()
    pos = 8; idat = b""; w = h = 0
    while pos < len(d):
        ln = struct.unpack(">I", d[pos:pos+4])[0]; typ = d[pos+4:pos+8]
        if typ == b"IHDR": w, h = struct.unpack(">II", d[pos+8:pos+16])
        elif typ == b"IDAT": idat += d[pos+8:pos+8+ln]
        pos += 12 + ln
    try: raw = zlib.decompress(idat)
    except Exception: return w*h, None
    n = 0; prev = bytearray(w*3); i = 0
    for y in range(h):
        f = raw[i]; i += 1
        line = bytearray(raw[i:i+w*3]); i += w*3
        if f == 1:
            for x in range(3, len(line)): line[x] = (line[x]+line[x-3]) & 0xFF
        elif f == 2:
            for x in range(len(line)): line[x] = (line[x]+prev[x]) & 0xFF
        elif f == 3:
            for x in range(len(line)):
                a = line[x-3] if x >= 3 else 0
                line[x] = (line[x]+((a+prev[x]) >> 1)) & 0xFF
        elif f == 4:
            for x in range(len(line)):
                a = line[x-3] if x >= 3 else 0; b = prev[x]; c = prev[x-3] if x >= 3 else 0
                p = a+b-c; pa = abs(p-a); pb = abs(p-b); pc = abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x]+pr) & 0xFF
        prev = line
        for x in range(0, len(line), 3):
            if not (line[x] > 245 and line[x+1] > 245 and line[x+2] > 245): n += 1
    return n, w*h

def ppm_nonwhite(p):
    if not os.path.exists(p): return None
    d = open(p, "rb").read()
    parts = d.split(b"\n", 3)
    px = parts[3]
    n = 0
    for i in range(0, len(px), 3):
        if not (px[i] > 245 and px[i+1] > 245 and px[i+2] > 245): n += 1
    return n

DIRNAMES = {  # baseline label -> run dir under OUT
    "bouncy": "bouncy", "microtimer": "dubrowgn.microtimer_8",
    "unote": "app.varlorg.unote_30", "opmt": "opmt_v0.1.2_vc1",
    "gmdice": "de.duenndns.gmdice_8", "stopwatch": "com.github.muellerma.stopwatch_6",
    "tictactoe": "com.emmanuelmess.tictactoe_3", "dooz": "dooz_23_toplevel",
    "fishrings": "fishrings_v1.23_vc6", "tripeaks": "tripeaks_v1.2.1_vc4",
}

rows = []
for name in sorted(BASELINE):
    d = os.path.join(OUT, DIRNAMES[name])
    f8 = os.path.join(d, "frames/frame_008.png")
    shot = os.path.join(d, "screenshot.ppm")
    n8, _ = png_nonwhite(f8)
    ns = ppm_nonwhite(shot)
    rows.append((name, BASELINE[name], n8, ns))

print(f"{'app':<38}{'wave1-baseline':>15}{'now frame_008':>15}{'now screenshot':>15}")
for name, b, n8, ns in rows:
    print(f"{name:<38}{b:>15}{n8 if n8 is not None else '-':>15}{ns if ns is not None else '-':>15}")

print("\n=== fishrings determinism x3 (frame_008 sha + nonwhite) ===")
shas = set()
for i in (1, 2, 3):
    f8 = os.path.join(OUT, f"fishrings_det{i}/frames/frame_008.png")
    if os.path.exists(f8):
        sha = hashlib.sha256(open(f8, "rb").read()).hexdigest()[:16]
        n, _ = png_nonwhite(f8)
        shas.add(sha)
        print(f"run{i}: sha={sha} nonwhite={n}")
print("DETERMINISM:", "BYTE-IDENTICAL x3" if len(shas) == 1 else f"NONDETERMINISTIC ({len(shas)} distinct)")
