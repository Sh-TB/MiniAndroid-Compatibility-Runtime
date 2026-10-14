#!/usr/bin/env python3
"""cont19_metrics.py — Phase 2 graphical proof metrics for the cont19 battery.
Reads run/cont19/battery/<target>_r1/screenshot.png and emits unique-color
count, dominant color share, non-dominant pixels, size, sha256.
Also records APK sha256 identities for the baseline table."""
import hashlib, json, os, struct, zlib, collections, sys

BASE = "/home/z/my-project"
OUT = os.path.join(BASE, "run/cont19/battery")

def png_metrics(path):
    with open(path, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    # parse PNG IHDR
    w = h = 0
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", data[16:24])
    # decode pixels via zlib + unfilter (handle RGBA8/RGB8 common cases)
    idat = b""
    i = 8
    while i < len(data):
        ln = struct.unpack(">I", data[i:i+4])[0]
        typ = data[i+4:i+8]
        if typ == b"IDAT":
            idat += data[i+8:i+8+ln]
        i += 12 + ln
    colors = 0
    nondom = 0
    dom_share = 1.0
    try:
        raw = zlib.decompress(idat)
        bpp = 4  # assume RGBA8; fall back below if needed
        # read color type from IHDR
        ctype = data[25]
        bpp = {0:1, 2:3, 3:1, 4:2, 6:4}[ctype]
        stride = w * bpp
        prev = bytearray(stride)
        cur = bytearray(stride)
        pos = 0
        cnt = collections.Counter()
        for y in range(h):
            ft = raw[pos]; pos += 1
            cur[:] = raw[pos:pos+stride]; pos += stride
            if ft == 1:
                for x in range(bpp, stride): cur[x] = (cur[x] + cur[x-bpp]) & 0xFF
            elif ft == 2:
                for x in range(stride): cur[x] = (cur[x] + prev[x]) & 0xFF
            elif ft == 3:
                for x in range(stride):
                    a = cur[x-bpp] if x >= bpp else 0
                    cur[x] = (cur[x] + ((a + prev[x]) >> 1)) & 0xFF
            elif ft == 4:
                for x in range(stride):
                    a = cur[x-bpp] if x >= bpp else 0
                    b = prev[x]
                    c = prev[x-bpp] if x >= bpp else 0
                    p = a + b - c
                    pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    cur[x] = (cur[x] + pr) & 0xFF
            px = bytes(cur)
            for x in range(0, stride, bpp):
                cnt[px[x:x+bpp]] += 1
            prev, cur = cur, prev
        colors = len(cnt)
        total = w * h
        dom_share = cnt.most_common(1)[0][1] / total if cnt else 1.0
        nondom = total - cnt.most_common(1)[0][1] if cnt else 0
    except Exception as e:
        return {"error": str(e), "sha256": sha}
    return {"w": w, "h": h, "unique_colors": colors,
            "dominant_share": round(dom_share, 4),
            "nondominant_px": nondom, "sha256": sha}

targets = sys.argv[1:] or [
    "g2048", "tetris", "snake_deluxe", "snakeneon",
    "tictactoe_deluxe", "minicraft", "gmdice", "dooz",
]
res = {}
for t in targets:
    p = os.path.join(OUT, t, "screenshot.png")
    if os.path.exists(p):
        res[t] = png_metrics(p)
        print(t, json.dumps(res[t]))
    else:
        print(t, "NO SCREENSHOT", p)

apks = {
    "g2048": "upload/s80_games/build_2048/g2048_v1.0_vc1.apk",
    "tetris": "upload/s80_games/build_tetris/tetris_v1.0_vc1.apk",
    "snake_deluxe": "upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk",
    "snakeneon": "upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk",
    "tictactoe_deluxe": "upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk",
    "minicraft": "upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk",
    "gmdice": "upload/canonical_apks/de.duenndns.gmdice_8.apk",
    "dooz": "upload/canonical_apks/dooz_23_toplevel.apk",
}
ids = {}
for k, rel in apks.items():
    fp = os.path.join(BASE, rel)
    if os.path.exists(fp):
        with open(fp, "rb") as f:
            ids[k] = {"apk_path": rel,
                      "apk_sha256": hashlib.sha256(f.read()).hexdigest()}
        print("APK", k, ids[k]["apk_sha256"])
json.dump({"metrics": res, "apk_identity": ids},
          open(os.path.join(OUT, "cont19_metrics.json"), "w"), indent=1)
print("saved", os.path.join(OUT, "cont19_metrics.json"))
