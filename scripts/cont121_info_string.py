#!/usr/bin/env python3
"""CONT-121 W-01: extract p3.d's info-string raw MUTF-8 bytes from the dex,
analyze surrogate content, and simulate n2.r's chunk decoder under
(A) JVM UTF-16 unit law vs (B) miniandroid current law (bytes/cp mixing).
"""
import os, struct, sys, zipfile

dex_path = "run/c121/classes_extracted.dex"
data = open(dex_path, "rb").read()

# Use androguard to find p3.d's const-string index at pc 0xd8
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex
a, d, dx = AnalyzeDex(dex_path)

PB = "Lcom/google/android/gms/internal/play_billing/"
cls = d.get_class(PB + "p3;")
target = None
for m in cls.get_methods():
    if m.get_name() == "d":
        target = m
        break
str_idx = None
off = 0
for ins in target.get_code().get_bc().get_instructions():
    if off == 0xd8:
        op = ins.get_name()
        print("const-string op:", op, ins.get_output()[:60])
        # get the string index from operands
        operands = ins.get_operands()
        for opd in operands:
            if len(opd) >= 3 and isinstance(opd[2], int):
                str_idx = opd[2]
            elif len(opd) == 2 and isinstance(opd[1], int):
                str_idx = opd[1]
        break
    off += ins.get_length()
print("string idx:", str_idx)

# Get the raw string data item offset from string_ids
string_ids_off = struct.unpack_from("<I", data, 0x3c)[0]
str_data_off = struct.unpack_from("<I", data, string_ids_off + str_idx * 4)[0]

# read uleb128 len
def uleb(off):
    r = 0; sh = 0
    while True:
        b = data[off]; off += 1
        r |= (b & 0x7F) << sh
        if not (b & 0x80): break
        sh += 7
    return r, off

declared, pos = uleb(str_data_off)
# raw MUTF-8 bytes until NUL
end = data.index(0, pos)
raw = data[pos:end]
print(f"declared utf16 units: {declared}, raw MUTF-8 bytes: {len(raw)}")

# analyze: CESU-8 3-byte sequences in surrogate range
hi_cnt = lo_cnt = pair_cnt = other3 = ascii_ = two = 0
units = []  # decode per JVM law: each 3-byte surrogate seq = 1 unit
i = 0
seqs = []
while i < len(raw):
    b1 = raw[i]
    if b1 < 0x80:
        units.append(b1); ascii_ += 1; i += 1
    elif (b1 & 0xE0) == 0xC0:
        cp = ((b1 & 0x1F) << 6) | (raw[i+1] & 0x3F)
        units.append(cp); two += 1; i += 2
    elif (b1 & 0xF0) == 0xE0:
        cp = ((b1 & 0x0F) << 12) | ((raw[i+1] & 0x3F) << 6) | (raw[i+2] & 0x3F)
        if 0xD800 <= cp <= 0xDFFF:
            units.append(cp)
            if cp <= 0xDBFF: hi_cnt += 1
            else: lo_cnt += 1
        else:
            units.append(cp); other3 += 1
        seqs.append(hex(cp))
        i += 3
    else:
        print("4-byte seq?? at", i)
        break
print(f"ascii={ascii_} 2byte={two} 3byte-other={other3} hi_sur={hi_cnt} lo_sur={lo_cnt}")
print("first 40 surrogate-range seqs:", [s for s in seqs if s in [hex(x) for x in units if 0xD800<=x<=0xDFFF]][:40])

# pairing check: adjacent high followed by low?
pairs = 0; lones = 0
j = 0
unit_seq = units
while j < len(unit_seq):
    if 0xD800 <= unit_seq[j] <= 0xDBFF:
        if j+1 < len(unit_seq) and 0xDC00 <= unit_seq[j+1] <= 0xDFFF:
            pairs += 1; j += 2; continue
        lones += 1
    j += 1
print(f"proper high+low pairs: {pairs}, lone highs: {lones}")
print(f"JVM utf16 unit count: {len(unit_seq)}  (declared: {declared})")

# astral code points under combining law
astral = 0
j = 0
comb = []
while j < len(unit_seq):
    u = unit_seq[j]
    if 0xD800 <= u <= 0xDBFF and j+1 < len(unit_seq) and 0xDC00 <= unit_seq[j+1] <= 0xDFFF:
        cp = 0x10000 + ((u - 0xD800) << 10) + (unit_seq[j+1] - 0xDC00)
        comb.append(cp); astral += 1; j += 2
    else:
        comb.append(u); j += 1
print(f"combining law: astral={astral}, code-point count={len(comb)}")
print(f"miniandroid length() today = UTF-8 BYTES = {len(raw)}")

json.dump({"units": units, "comb": comb},
          open("run/c121/info_string_analysis.json", "w"))
print("saved run/c121/info_string_analysis.json")
