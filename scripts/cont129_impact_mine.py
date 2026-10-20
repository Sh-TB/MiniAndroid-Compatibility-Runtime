#!/usr/bin/env python3
"""CONT-129 impact miner: registry status histogram + fix fan-out + per-app face timeline."""
import json, re, glob, os, collections

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/run/c129"
os.makedirs(OUT, exist_ok=True)

# ---------- 1. Registry status histogram ----------
reg = json.load(open(f"{ROOT}/canonical/root_cause_registry.json"))
hist = collections.Counter(r.get("status", "?") for r in reg)
print("== REGISTRY HISTOGRAM (n=%d) ==" % len(reg))
for k, v in hist.most_common():
    print(f"  {k}: {v}")

# terminal vs open accounting
TERMINAL_GOOD = {"ROOT-CAUSED-FIXED", "ALREADY_FIXED_AND_TESTED", "ALREADY_TRACKED_OR_DUPLICATE",
                 "STALE_OR_SUPERSEDED", "NOT_APPLICABLE", "REJECTED_WITH_REASON", "CLASSIFIED", "LANDING"}
fixed = hist.get("ROOT-CAUSED-FIXED", 0)
print(f"  ROOT-CAUSED-FIXED total: {fixed}")

# ---------- 2. Fix -> app fan-out (mine evidence strings of fixed roots) ----------
APPS = ["dooz", "telegram", "klondike", "chess", "unote", "sudoku", "tictactoe", "tower3d",
        "opencalc", "microtimer", "stopwatch", "bouncy", "tripeaks", "fishrings", "gmdice",
        "memory", "opmt", "chessclock", "flappycow", "forkgram", "whatsapp", "notes",
        "mykanji", "weather", "blockbuster", "accelerace"]
fan = []
for r in reg:
    if r.get("status") == "ROOT-CAUSED-FIXED":
        evr = r.get("evidence")
        if not isinstance(evr, str):
            evr = json.dumps(evr, ensure_ascii=False) if evr is not None else ""
        ev = (evr or "") + " " + (r.get("title") or "")
        hits = [a for a in APPS if a.lower() in ev.lower()]
        fan.append((r["id"], len(hits), hits[:6]))
fan.sort(key=lambda x: -x[1])
print("\n== TOP FIXES BY APP FAN-OUT (ROOT-CAUSED-FIXED) ==")
for fid, n, hits in fan[:15]:
    print(f"  {fid}: {n} apps -> {hits}")

# ---------- 3. Face timeline from evidence waves ----------
# anchor name -> list of (wave, face16)
ANCHOR_NAMES = {"dooz": r"dooz[\": ]+([0-9a-f]{16})",
                "klondike": r"klondike[\": ]+([0-9a-f]{16})",
                "unote": r"unote[\": ]+([0-9a-f]{16})",
                "chess": r"chess[\": ]+([0-9a-f]{16})",
                "telegram": r"telegram[\": ]+([0-9a-f]{16})",
                "tower3d": r"tower3d[\": ]+([0-9a-f]{16})",
                "opencalc": r"opencalc[\": ]+([0-9a-f]{16})",
                "microtimer": r"microtimer[\": ]+([0-9a-f]{16})",
                "sudoku": r"sudoku[\": ]+([0-9a-f]{16})"}
timeline = collections.defaultdict(list)
wave_files = sorted(glob.glob(f"{ROOT}/evidence/s*/*evidence*.json"))
seen_waves = set()
for wf in wave_files:
    wave = os.path.basename(os.path.dirname(wf))
    try:
        txt = open(wf, errors="replace").read()
    except Exception:
        continue
    for app, pat in ANCHOR_NAMES.items():
        for m in re.finditer(pat, txt, re.I):
            f16 = m.group(1)
            if f16 not in [t[1] for t in timeline[app]]:
                timeline[app].append((wave, f16))
            break
print("\n== FACE TIMELINE (anchor apps, first->last observed) ==")
for app in sorted(timeline):
    seq = timeline[app]
    print(f"  {app}: {' -> '.join(f'{w}:{f}' for w, f in seq)}")

json.dump({"registry_histogram": dict(hist), "registry_total": len(reg),
           "root_cause_fixed": fixed,
           "fix_fanout_top": [{"id": f[0], "apps": f[1], "names": f[2]} for f in fan[:30]],
           "face_timeline": {k: v for k, v in timeline.items()}},
          open(f"{OUT}/impact_mine.json", "w"), indent=1)
print(f"\nwrote {OUT}/impact_mine.json")
