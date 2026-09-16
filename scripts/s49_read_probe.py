#!/usr/bin/env python3
"""S49 — read the 19x64 bit-visualization matrix from the probe screenshot
and compare against the JVM/OpenJDK ground truth computed in-process here."""
import sys
from PIL import Image

im = Image.open(sys.argv[1] if len(sys.argv) > 1 else
                "/tmp/s49_r361/probe6_out/screenshot.png").convert("RGB")
W, H = im.size

def read_row(r):
    bits = []
    for b in range(64):
        cx = 30 + b * 16 + 7
        cy = 20 + r * 96 + 40
        if cx >= W or cy >= H:
            return None
        px = im.getpixel((cx, cy))
        if px[1] > 120 and px[0] < 100:
            bits.append(1)
        elif px[0] < 90 and px[1] < 90 and px[2] < 90:
            bits.append(0)
        else:
            return None  # not a stripe pixel
    v = 0
    for i, bit in enumerate(bits):  # LSB left
        if bit:
            v |= (1 << i)
    return v

rows = [read_row(r) for r in range(19)]
names = (["L1w" + str(s) for s in range(8)] + ["L2half"] +
         ["L3g" + str(o) for o in range(0, 64, 8)] + ["L4match", "L4empty"])

# ---- ground truth (pure python ints == JVM semantics for these ops) ----
def s64(v):
    v &= (1 << 64) - 1
    return v - (1 << 64) if v >= (1 << 63) else v

EMPTY = 0x8080808080808080
BC = 0x0101010101010101
HIGH = 0x8080808080808080
H2S = [0x7F, 0x01, 0x38, 0x56, 0x22, 0x66, 0x0F, 0x4C]
FILL_SLOTS = [1, 6, 3, 4]
FILL_H2S = [0x38, 0x7F, 0x56, 0x0F]

exp = []
# L1: one word, slots 0..7
data = EMPTY
for slot in range(8):
    b = (slot & 7) << 3
    data = (data & (~(0xFF << b) & (1 << 64) - 1)) | ((H2S[slot] << b) & ((1 << 64) - 1))
    exp.append(data & ((1 << 64) - 1))
# L2: half fill
half = bytearray([0x80] * 8)
d2 = EMPTY
for k in range(4):
    s = FILL_SLOTS[k]
    b = (s & 7) << 3
    d2 = (d2 & (~(0xFF << b) & (1 << 64) - 1)) | ((FILL_H2S[k] << b) & ((1 << 64) - 1))
    half[s] = FILL_H2S[k]
exp.append(d2)
# L3: group straddle — d2 words = half bytes (word0 = bytes0..7, word1 mirror)
halfbytes = half  # word1 mirror = same bytes
for off in range(0, 64, 8):
    bit = off          # bit shift inside window; word0>>bit | word1<<(64-bit) & mask
    w0 = halfbytes[0] | (halfbytes[1] << 8) | (halfbytes[2] << 16) | (halfbytes[3] << 24) | \
         (halfbytes[4] << 32) | (halfbytes[5] << 40) | (halfbytes[6] << 48) | (halfbytes[7] << 56)
    w1 = w0  # mirrored
    g0 = w0 >> bit
    g1 = (w1 << (64 - bit)) & ((1 << 64) - 1)
    mask = ((1 << bit) - 1) if bit else (1 << 64) - 1
    g = (g0 | (g1 & mask)) & ((1 << 64) - 1)
    # window bytes = half[off/8 .. off/8+7] wrapped — the mirror makes w1==w0 so
    # the straddle at bit b covers bytes [b/8..7] then [0..b/8-1]
    sb = off // 8
    win = [halfbytes[(sb + i) % 8] for i in range(8)]
    gexp = win[0] | (win[1] << 8) | (win[2] << 16) | (win[3] << 24) | \
           (win[4] << 32) | (win[5] << 40) | (win[6] << 48) | (win[7] << 56)
    exp.append(gexp)
# L4: SWAR match/empty on half word
g = d2
x = g ^ ((0x38 * BC) & ((1 << 64) - 1))
m = ((x - BC) & (~x & ((1 << 64) - 1)) & HIGH) & ((1 << 64) - 1)
exp.append(m & ((1 << 64) - 1))
e = ((~g & ((1 << 64) - 1)) & ((g << 6) & ((1 << 64) - 1)) & HIGH) & ((1 << 64) - 1)
exp.append(e)

mismatches = 0
for i, name in enumerate(names):
    a, e = rows[i], exp[i]
    if a is None:
        print(f"{name:9s} UNREADABLE")
        mismatches += 1
        continue
    ok = (a & ((1 << 64) - 1)) == (e & ((1 << 64) - 1))
    if not ok:
        mismatches += 1
        print(f"{name:9s} MISMATCH")
        print(f"    engine = 0x{a:016X}")
        print(f"    truth  = 0x{e:016X}")
        # find divergent bytes
        db = [f"byte{k}=eng:0x{(a >> (8*k)) & 0xFF:02X} exp:0x{(e >> (8*k)) & 0xFF:02X}"
              for k in range(8) if ((a >> (8*k)) & 0xFF) != ((e >> (8*k)) & 0xFF)]
        print("    " + " ".join(db))
    else:
        print(f"{name:9s} OK 0x{a:016X}")
print(f"\nmismatches: {mismatches}/19")
