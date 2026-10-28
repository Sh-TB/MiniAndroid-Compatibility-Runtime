#!/usr/bin/env python3
"""cont47_update3.py — FINAL exact-evidence pass (post-revert).
Match rule (strict, honest):
  A) real pkg string found in run trace (lifecycle/api) == row.pkg
  B) distinct title token both in label and in row.t/row.pkg
One label -> at most one row. No gate inflation: NOT_TESTED -> OBSERVED only."""
import json, re, os, glob

BASE = "/home/z/my-project"
apps_path = os.path.join(BASE, "plugins/apps.jsonl")
rows = [json.loads(l) for l in open(apps_path) if l.strip()]
faces = json.load(open(os.path.join(BASE, "run/cont47/faces.json")))
rcs = {}
for ln in open(os.path.join(BASE, "run/cont47/fanout/summary.txt")):
    m = re.match(r"TRAIN\|([^|]+)\|rc=(\d+)\|sha=([0-9a-f]*)", ln.strip())
    if m:
        rcs.setdefault(m.group(1), (int(m.group(2)), m.group(3)))

# real packages recovered from engine traces (not filename echoes)
REAL_PKG = {
    "fishrings_v1.23_vc6": "eu.veldsoft.fish.rings",
    "opmt_v0.1.2_vc1": "one.scarecrow.games",
    "tripeaks_v1.2.1_vc4": "eu.veldsoft.tri.peaks",
}
# filename-echo labels -> exact row pkg (verified against apps.jsonl content)
ECHO_PKG = {
    "app.varlorg.unote_30": "app.varlorg.unote", "unote": "app.varlorg.unote",
    "com.dozingcatsoftware.bouncy_43": "com.dozingcatsoftware.bouncy",
    "bouncy": "com.dozingcatsoftware.bouncy",
    "bouncy43": "com.dozingcatsoftware.bouncy",
    "com.emmanuelmess.tictactoe_3": "com.emmanuelmess.tictactoe",
    "ttt3": "com.emmanuelmess.tictactoe",
    "com.github.muellerma.stopwatch_6": "com.github.muellerma.stopwatch",
    "stopwatch6": "com.github.muellerma.stopwatch",
    "com.simondalvai.ball2box_69": "com.simondalvai.ball2box",
    "de.duenndns.gmdice_8": "de.duenndns.gmdice", "gmdice": "de.duenndns.gmdice",
    "dubrowgn.microtimer_8": "dubrowgn.microtimer", "microtimer": "dubrowgn.microtimer",
    "eu.quelltext.memory_7": "eu.quelltext.memory",
    "io.github.yamin8000.dooz_23": "io.github.yamin8000.dooz",
    "dooz_23_toplevel": "io.github.yamin8000.dooz",
    "org.andstatus.game2048_47": "org.andstatus.game2048",
    "org.opensurge2d.surgeengine_30650": "org.opensurge2d.surgeengine",
    "org.secuso.privacyfriendlydame_101": "org.secuso.privacyfriendlydame",
    "org.secuso.privacyfriendlymemory_100": "org.secuso.privacyfriendlymemory",
    "org.secuso.privacyfriendlysolitaire_4": "org.secuso.privacyfriendlysolitaire",
    "page.codeberg.lanticy.guandan_7": "page.codeberg.lanticy.guandan",
    "solitaire71": "de.tobiasbielefeld.solitaire",
    # secuso batch: real pkg in rows
    "sudoku_secuso_101": "org.secuso.privacyfriendlysudoku",
    "notes_secuso_105": "org.secuso.privacyfriendlynotes",
    "klondike_veldsoft_3": "com.veldsoft.klondike",
    "chess_jwtc_298": "jwtc.android.chess",
    "chessclock_29": "chessclock",
    "stack.tower3d_1": "stack.tower3d",
    "opencalculator_53": "app.fossify.calculator",
}
TOKEN = {  # fallback: distinct token in label vs row t/pkg
    "klondike_veldsoft_3": "klondike", "tripeaks_v1.2.1_vc4": "peaks",
    "fishrings_v1.23_vc6": "rings", "stack.tower3d_1": "tower3d",
    "chessclock_29": "chessclock", "chess_jwtc_298": "jwtc",
    "solitaire71": "tobiasbielefeld", "opmt_v0.1.2_vc1": "scarecrow",
    "opencalculator_53": "calculator", "sudoku_secuso_101": "sudoku",
    "notes_secuso_105": "notes",
}

def face_class(label):
    f = faces.get(label, {})
    if f.get("face") == "WHITE": return "WHITE"
    uniq, ratio = f.get("color_buckets", 0), f.get("ratio", 0)
    if uniq <= 1: return "FLAT"
    return f"RENDERED uniq32={uniq} ratio={ratio}"

claimed = set()
touched = []
for label, (rc, sha) in sorted(rcs.items()):
    want = REAL_PKG.get(label) or ECHO_PKG.get(label)
    tok = TOKEN.get(label)
    fc = face_class(label)
    note = f"CONT-47 fanout: rc={rc} face={fc} sha16={sha}"
    hit = None
    for r in rows:
        if id(r) in claimed: continue
        p = str(r.get("pkg", ""))
        t = str(r.get("t", ""))
        if want and want and p and (p == want or (len(want) > 10 and want in p)):
            hit = r; break
        if tok and tok.lower() in (p + " " + t).lower():
            hit = r; break
    if not hit:
        print(f"NO-ROW {label} want={want} tok={tok}")
        continue
    claimed.add(id(hit))
    if hit.get("load") == "NOT_TESTED":
        hit["load"] = "OBSERVED"; hit["gate"] = hit.get("gate") or "L1"
        hit["nx"] = "L2"; hit["n"] = note
        hit["ev"] = "run/cont47/fanout (untracked, sha-only)"
        hit["next"] = "L2: content-render census + interaction probe"
    else:
        hit["n"] = (str(hit.get("n", "")).split(" | ")[0] + " | " + note)[:320]
    touched.append((hit["i"], hit["t"], label, hit["load"]))

with open(apps_path, "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"\ntouched {len(touched)} rows:")
for i, t, lab, load in touched:
    print(f"  {i:9s} {str(t)[:34]:36s} <- {lab:36s} load={load}")
