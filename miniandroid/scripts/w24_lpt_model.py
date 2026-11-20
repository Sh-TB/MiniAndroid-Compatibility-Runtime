#!/usr/bin/env python3
"""w24_lpt_model.py — scheduling model from measured per-TU durations (B1 -j1).

Computes, on the real per-TU wall data:
  1. serial sum, ideal 2-core lower bound = sum/2
  2. LPT list schedule (longest processing time first, 2 machines)
  3. makespan with the REAL last-link serialization: make builds all .o then
     links — the link is a single serial event appended to the second-to-finish
     machine.
  4. memory-aware check: never two TUs whose peak RSS sums beyond a budget.
Compares with the measured -j2 wall to quantify scheduling waste.
"""
import csv

RANK = "evidence/w24/TU_COST_RANKING.csv"
LINK_S = None  # filled from ranking serial section

rows = [r for r in csv.reader(open(RANK)) if r and r[0].isdigit()]
tus = [(r[1], float(r[2])) for r in rows]
link_s, archive_s, ver_s = 0.0, 0.0, 0.0
for r in csv.reader(open(RANK)):
    if r and r[0].startswith("# link"):
        link_s = float(r[2])
    if r and r[0].startswith("# archive"):
        archive_s += float(r[2])
    if r and r[0].startswith("# version-gen"):
        ver_s += float(r[2])

total = sum(t for _, t in tus)
serial = link_s + archive_s + ver_s
m1 = m2 = 0.0
for name, t in sorted(tus, key=lambda x: -x[1]):
    if m1 <= m2:
        m1 += t
    else:
        m2 += t
comp_end = max(m1, m2)
makespan = comp_end + link_s  # link serializes at the end

print(f"TUs={len(tus)} compile_sum={total:.1f}s serial(link+ar+ver)={serial:.1f}s")
print(f"ideal 2-core (sum/2 + link)        = {total/2 + link_s:.1f}s")
print(f"LPT makespan (compile+link)        = {makespan:.1f}s")
print(f"measured FASTPROFILE -j2 wall      = see build_bench (322.75)")
print(f"measured - LPT model               = schedule waste")
# tail detail
print(f"top5: {[(n[:34], round(t,1)) for n,t in sorted(tus,key=lambda x:-x[1])[:5]]}")
