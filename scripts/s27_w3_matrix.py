#!/usr/bin/env python3
# s27_w3_matrix.py — builds evidence/s27/s27w3_matrix.tsv from the S27-W3
# run dirs (canonical-flag production runs), mirroring the s27w2_matrix.tsv
# shape. Frame files stay local; the TSV carries the hashes.
import hashlib
import json
import os

BASE = "/home/z/my-project/miniandroid/evidence/s27"
OUT = os.path.join(BASE, "s27w3_matrix.tsv")

ROWS = [
    # (run_dir, apk, note)
    ("w3_base_r1", "org.ecos.logic.flip_a_coin_3",
     "BASELINE reproduction on PRE-FIX binary (dev -O0 build, flags "
     "--max-seconds 12): census ContentFrameLayout children=0, verdict "
     "DEFAULT_BACKGROUND_ONLY, rc=1 - the S27-W3 blocker measured"),
    ("w3_fix_r2", "org.ecos.logic.flip_a_coin_3",
     "S27-W3 law on dev binary: ADOPT fires, census 858 children=1, "
     "verdict REAL_APP_CONTENT, rc=0"),
    ("w3_np", "com.farmerbb.notepad",
     "canonical flags p0_gate (90s frames30 trace)"),
    ("w3_dice", "tech.gaskell.diceroller",
     "canonical flags p0_gate (120s frames30)"),
    ("w3_guess", "ru.zxalexis.ugaday",
     "canonical flags p0_gate (120s frames30)"),
    ("w3_ttt", "com.itsfrz.tictactoe",
     "canonical flags p0_gate (120s frames30)"),
    ("w3_pz", "name.livitski.games.puzzle.android",
     "canonical flags p0_gate (200s frames50 tap 197,112@25) - face delta "
     "vs S27-W2 canonical, see bisect"),
    ("w3_rnd", "com.minar.randomix",
     "canonical flags (120s frames30)"),
    ("w3_minos", "de.tcrass.minos",
     "canonical flags (120s frames30)"),
    ("w3_hw", "com.thehellomaker.helloworldtoast",
     "canonical flags (120s frames30)"),
    ("w3_chess", "dk.cocode.chess",
     "canonical flags (120s frames30)"),
    ("w3_flip_r1", "org.ecos.logic.flip_a_coin_3",
     "S27-W3 x3 face b492ee85799fb2cb deterministic - NEW face (was "
     "b270ff04 DEFAULT_BACKGROUND_ONLY)"),
    ("w3_flip_r2", "org.ecos.logic.flip_a_coin_3", "S27-W3 x3"),
    ("w3_flip_r3", "org.ecos.logic.flip_a_coin_3", "S27-W3 x3"),
]


def last_frame_hash(run_dir):
    p = os.path.join(BASE, run_dir, "screenshot.png")
    if not os.path.exists(p):
        return ""
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def verdict(run_dir):
    p = os.path.join(BASE, run_dir, "stderr.log")
    v = ""
    if os.path.exists(p):
        for line in open(p, errors="replace"):
            if "verdict=" in line:
                i = line.rfind("verdict=")
                v = line[i + 8:].split()[0]
    return v


def rc(run_dir):
    p = os.path.join(BASE, run_dir, "rc.txt")
    if os.path.exists(p):
        return open(p).read().strip()
    return ""


def events(run_dir):
    p = os.path.join(BASE, run_dir, "trace_summary.json")
    if os.path.exists(p):
        try:
            return str(json.load(open(p)).get("events_total"))
        except Exception:
            return ""
    return ""


with open(OUT, "w") as f:
    f.write("apk\trun_dir\tbinary\tlast_frame_hash16\tverdict\trc\tevents\tnote\n")
    for run_dir, apk, note in ROWS:
        binary = ("dev-O0" if run_dir in ("w3_base_r1", "w3_fix_r2")
                  else "production")
        f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            apk, run_dir, binary, last_frame_hash(run_dir), verdict(run_dir),
            rc(run_dir), events(run_dir), note))
print("wrote", OUT)
with open(OUT) as f:
    print(f.read())
