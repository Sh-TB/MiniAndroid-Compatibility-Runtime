#!/usr/bin/env python3
"""cont47_repair.py — fix the 3 misattributed notes from update3."""
import json

p = "/home/z/my-project/plugins/apps.jsonl"
rows = [json.loads(l) for l in open(p) if l.strip()]

def strip_note(row):
    parts = str(row.get("n", "")).split(" | ")
    row["n"] = " | ".join(x for x in parts if "CONT-47 fanout" not in x)

sudoku_note = notes_note = calc_note = None
for r in rows:
    if r["i"] == "GAME-040" and r["pkg"] == "com.galaxyrio.sudokusolver" and "CONT-47 fanout" in r["n"]:
        n = r["n"]; sudoku_note = "CONT-47 fanout:" + n.split("CONT-47 fanout:")[1]
        strip_note(r)
    if r["i"] == "APP-096" and r["pkg"] == "dev.cipher.notes" and "CONT-47 fanout" in r["n"]:
        strip_note(r)
    if r["i"] == "APP-028" and r["pkg"] == "com.vagujhelyigergely.calculatorm3" and "CONT-47 fanout" in r["n"]:
        strip_note(r)
    if r["i"] == "GAME-070" and r["pkg"] == "org.secuso.privacyfriendlysudoku":
        r["n"] = (str(r["n"]).split(" | ")[0] + " | " +
                  "CONT-47 fanout: rc=1 face=RENDERED uniq32=9 ratio=0.9979 sha16=be640e39e82901c9")[:320]
    if r["i"] == "APP-010" and r["t"] == "OpenCalculator":
        r["n"] = (str(r["n"]).split(" | ")[0] + " | " +
                  "CONT-47 fanout: rc=1 face=RENDERED uniq32=21 ratio=0.5857 sha16=63020bc7334048fe")[:320]

with open(p, "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("repaired: GAME-040/APP-096/APP-028 stripped; GAME-070/APP-010 attributed")
