#!/usr/bin/env python3
# s27_w4_matrix.py — builds evidence/s27/s27w4_matrix.tsv from the S27-W4
# run dirs (canonical-flag production runs + the forensics chain), mirroring
# the s27w3_matrix.tsv shape.
import hashlib
import json
import os

BASE = "/home/z/my-project/miniandroid/evidence/s27"
OUT = os.path.join(BASE, "s27w4_matrix.tsv")

ROWS = [
    ("org.ecos.logic.flip_a_coin_3", "w4_diag",
     "production", "PRE-LAW forensics: [DEX-MEASURE] CL.onMeasure "
     "AT_MOST(1080)xAT_MOST(1920) -> 0x0; R-NEW-438 takeover heals the ROOT "
     "from frame 2 (census 406 1080x1920) but the CHILDREN stay 0x0"),
    ("org.ecos.logic.flip_a_coin_3", "w4_diag4",
     "production", "THE POISON RECEIPT: [T58-FRAME] view=569/594 "
     "layout(0,0,0,0) caller=ConstraintLayout.onLayout pc=70 — the R445 "
     "DEX onLayout re-dispatch zeroes every child every frame"),
    ("org.ecos.logic.flip_a_coin_3", "w4_law_r1",
     "production", "S27-W4 law: face 6808aa29ff941dae, verdict "
     "REAL_APP_CONTENT, first_divergence=None, census 569 pos=(374,794) "
     "331x331, face region 84324 px"),
    ("org.ecos.logic.flip_a_coin_3", "w4_flip_r1",
     "production", "S27-W4 x3 deterministic 6808aa29ff941dae"),
    ("org.ecos.logic.flip_a_coin_3", "w4_flip_r2", "production", "S27-W4 x3"),
    ("org.ecos.logic.flip_a_coin_3", "w4_flip_r3", "production", "S27-W4 x3"),
    ("com.farmerbb.notepad", "w3_np", "production",
     "canonical flags — hash IDENTICAL to S27-W2 canonical 31ddd4d5b8e6d18e"),
    ("tech.gaskell.diceroller", "w3_dice", "production",
     "canonical flags — IDENTICAL 0de952bf75f89409"),
    ("ru.zxalexis.ugaday", "w3_guess", "production",
     "canonical flags — IDENTICAL 87fe26766fc48d06, rc=0"),
    ("com.itsfrz.tictactoe", "w3_ttt", "production",
     "canonical flags — IDENTICAL d55056a8928a26ff"),
    ("com.minar.randomix", "w4_rnd",
     "production", "ADJUDICATED PROGRESS: canonical 31ddd4d5 was BLANK "
     "(0 non-white px — the DEX AppIntroViewPager.onLayout collapsed the "
     "full-screen pager to 0x0); the law rejected the poison "
     "([S27-W4-FRAME-REJECT] view=1065 over canonical (0,0 1080x1920), "
     "Button over (32,1762 231x126)) — new face 5fef8090 carries the real "
     "AppIntro pager chrome (1080 px, buttons at real positions)"),
    ("name.livitski.games.puzzle.android", "w3_pz", "production",
     "unchanged 35c4e53b — the S27-W3 bisect-attributed pre-existing delta; "
     "0 S27-W4 markers (the law is inert on pz)"),
    ("de.tcrass.minos", "w3_minos", "production",
     "canonical flags — IDENTICAL b5a7a35d5fe0564b"),
    ("com.thehellomaker.helloworldtoast", "w3_hw", "production",
     "canonical flags — IDENTICAL acdd9f05dc9c7ece"),
    ("dk.cocode.chess", "w3_chess", "production",
     "canonical flags — IDENTICAL d602648e8e401895"),
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
                v = line[line.rfind("verdict=") + 8:].split()[0]
    if not v:
        p = os.path.join(BASE, run_dir, "trace_summary.json")
        if os.path.exists(p):
            try:
                d = json.load(open(p))
                fd = d.get("first_divergence") or {}
                v = ("NO-DIVERGENCE " if not fd else "")
                vs = re_findall_verdicts(p)
                if vs:
                    v += vs
            except Exception:
                pass
    return v


def re_findall_verdicts(path):
    import re as _re
    txt = open(path, errors="replace").read()
    vs = sorted(set(_re.findall(r'"verdict": "([A-Z_]+)"', txt)))
    return "+".join(vs)


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
    for apk, run_dir, binary, note in ROWS:
        f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            apk, run_dir, binary, last_frame_hash(run_dir), verdict(run_dir),
            rc(run_dir), events(run_dir), note))
print("wrote", OUT)
with open(OUT) as f:
    print(f.read())
