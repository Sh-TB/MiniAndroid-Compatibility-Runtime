#!/usr/bin/env python3
"""w24_hdr_consumers.py — consumer count for one header from HEADER_COST_RANKING.csv."""
import csv
import sys

target = sys.argv[1]
for r in csv.reader(open("evidence/w24/HEADER_COST_RANKING.csv")):
    if r and r[0] == target:
        print(r[1])
        sys.exit(0)
print("0")
