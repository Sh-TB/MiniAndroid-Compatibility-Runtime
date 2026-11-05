#!/usr/bin/env python3
"""s174_gates.py — S174: corpus-neutrality gates for the CODER's W10 laws
(w10_laws.patch f877c7c0ac27f0a2 applied on main @ 2617445a, binary
d0e8449b476cd8f1). REF = my S172/S173 standing fea1759d."""
import json
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s167_w6_gates as g
import s166_trains as s166

g.REF = BASE / ("upload/_ma_local_backup/"
                "miniandroid_s172_ncgroups_fea1759d58653d41.bin")
g.NEW = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s174_w10coder"
g.EVID = BASE / "evidence/s174_w10coder"
g.OUT.mkdir(parents=True, exist_ok=True)
g.EVID.mkdir(parents=True, exist_ok=True)


def save(name, payload):
    json.dump(payload, open(g.EVID / name, "w"), indent=1, default=str)
    print("evidence ->", g.EVID / name)


if __name__ == "__main__":
    phase = sys.argv[1]
    out = g.EVID / "S174_W10CODER_GATES.json"
    cur = {}
    if out.exists():
        cur = json.load(open(out))
    if phase in ("gates", "gates_anchors"):
        rows = {"microtimer": g.anchor_pair("microtimer"),
                "g2048": g.anchor_pair("g2048"),
                "opencalc": g.anchor_pair("opencalc")}
        cur.setdefault("anchors", {}).update(rows)
        for k, v in rows.items():
            r, n = v[k + "_ref"], v[k + "_new"]
            print(k, r["screenshot_face"], n["screenshot_face"],
                  r["screenshot_face"] == n["screenshot_face"])
    if phase in ("gates", "gates_dooz"):
        ctl = s166.dooz_run("w10c_dz_ctl", g.REF, store_root=g.OUT)
        fix = s166.dooz_run("w10c_dz_fix", g.NEW, store_root=g.OUT)
        cur["w10c_dz_ctl"] = ctl
        cur["w10c_dz_fix"] = fix
        cur["w10c_dz_summary"] = s166.pair_summary(ctl, fix)
        print("dooz:", json.dumps(s166.pair_summary(ctl, fix))[:300])
    if phase in ("gates", "gates_tg"):
        tctl = s166.tg_run("w10c_tg_ctl", g.REF, store_name="s174_tg")
        cur["w10c_tg_ctl"] = tctl
        save("S174_W10CODER_GATES.json", cur)
        tfix = s166.tg_run("w10c_tg_fix", g.NEW, store_name="s174_tg")
        cur["w10c_tg_fix"] = tfix
        cur["w10c_tg_summary"] = s166.pair_summary(tctl, tfix)
        print("tg:", json.dumps(s166.pair_summary(tctl, tfix))[:300])
    save("S174_W10CODER_GATES.json", cur)
