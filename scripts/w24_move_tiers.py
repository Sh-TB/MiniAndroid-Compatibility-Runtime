#!/usr/bin/env python3
"""w24_move_tiers.py — relocate the W24 tier block (lines 39-117) to after the
DEV=1 BUILDDIR override so $(BUILDDIR) in the := lists expands to the FINAL
build directory. Parse-order bug: BUILDDIR is defined at line 166, AFTER the
block, so the immediate-expansion lists captured empty prefixes."""
import io

P = "/home/z/my-project/miniandroid/Makefile"
lines = open(P).readlines()
block = lines[38:117]  # 0-based: lines 39..117
assert block[0].startswith("# W24 EXP-A"), block[0]
assert block[-1].strip() == "endif", block[-1]
assert "$(W24_TIER1_PIC): CXXFLAGS += -O1" in block[-2], block[-2]

# insertion point: after the DEV=1 endif that follows "BUILDDIR := build_dev"
dev_idx = next(i for i, l in enumerate(lines) if "BUILDDIR := build_dev" in l)
ins = dev_idx + 1
assert lines[ins].strip() == "endif", lines[ins]
at = ins + 1

rest = lines[:38] + lines[117:]
new = rest[:at] + ["\n"] + block + rest[at:]
open(P, "w").writelines(new)
print("moved %d lines from 39 to after line %d (DEV override)" % (len(block), ins + 1))
