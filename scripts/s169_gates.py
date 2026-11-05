#!/usr/bin/env python3
"""s169_gates.py — S169 regression gates for the setVersion REAL-PRAGMA law.
REF = W7 standing f7291fea, NEW = 991d8923 (S167 tree + w7 + sqlite law).
Phases: anchors_mg / anchors_oc / dooz / tg / verdict."""
import json
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s167_w6_gates as g
import s165_trains as t
import s166_trains as s166

g.REF = BASE / ("upload/_ma_local_backup/"
                "miniandroid_s168_w7_f7291feaaf778c0f.bin")
g.NEW = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s169_w8"
g.OUT.mkdir(parents=True, exist_ok=True)
g.EVID = BASE / "evidence/s169_w8"
g.EVID.mkdir(parents=True, exist_ok=True)


def save_anchors(rows):
    """Nested-merge into the anchors dict — the S167 lesson: the flat
    g.save() update() REPLACED the anchors key, losing microtimer/g2048."""
    out = g.EVID / "S169_W8_GATES.json"
    cur = {}
    if out.exists():
        try:
            cur = json.load(open(out))
        except Exception:
            cur = {}
    cur.setdefault("anchors", {}).update(rows)
    json.dump(cur, open(out, "w"), indent=1, default=str)
    print("evidence ->", out)


if __name__ == "__main__":
    phase = sys.argv[1]
    if phase == "anchors_mg":
        rows = {"microtimer": g.anchor_pair("microtimer"),
                "g2048": g.anchor_pair("g2048")}
        save_anchors(rows)
    elif phase == "anchors_oc":
        save_anchors({"opencalc": g.anchor_pair("opencalc")})
    elif phase == "dooz":
        ctl = s166.dooz_run("w8_dz_ctl", g.REF, store_root=g.OUT)
        print(json.dumps(ctl), flush=True)
        g.save("S169_W8_TRAINS.json", {"w8_dz_ctl": ctl})
        fix = s166.dooz_run("w8_dz_fix", g.NEW, store_root=g.OUT)
        print(json.dumps(fix), flush=True)
        g.save("S169_W8_TRAINS.json",
               {"w8_dz_fix": fix,
                "w8_dz_summary": s166.pair_summary(ctl, fix)})
    elif phase == "tg":
        ctl = s166.tg_run("w8_tg_ctl", g.REF, store_name="s169_tg")
        print(json.dumps(ctl), flush=True)
        g.save("S169_W8_TRAINS.json", {"w8_tg_ctl": ctl})
        fix = s166.tg_run("w8_tg_fix", g.NEW, store_name="s169_tg")
        print(json.dumps(fix), flush=True)
        g.save("S169_W8_TRAINS.json",
               {"w8_tg_fix": fix,
                "w8_tg_summary": s166.pair_summary(ctl, fix)})
    elif phase == "verdict":
        ab = json.load(open(g.EVID / "S169_W8_SETVER_AB.json"))
        gates = json.load(open(g.EVID / "S169_W8_GATES.json"))
        anchors = gates["anchors"]
        tr = json.load(open(g.EVID / "S169_W8_TRAINS.json"))
        verdict = {
            "ref_bin": t.sha16(g.REF), "new_bin": t.sha16(g.NEW),
            "law": "SQLiteDatabase.setVersion -> real PRAGMA user_version "
                   "(W8 S169; was REC-MISS zero-handlers)",
            "anchors_all_inert": all(v.get("delta_inert")
                                     for v in anchors.values()),
            "microtimer_pin": all(v.get("pin_match") for v in
                                  anchors.values() if "pin_match" in v),
            "dooz": tr.get("w8_dz_summary", {}),
            "tg": tr.get("w8_tg_summary", {}),
            "tb_ref": {k: ab["w8_ref"].get(k) for k in
                       ("wall_s", "uncaught", "ndfe", "pixels",
                        "census") if k in ab["w8_ref"]},
            "tb_new": {k: ab["w8_new"].get(k) for k in
                       ("wall_s", "uncaught", "ndfe", "pixels",
                        "census") if k in ab["w8_new"]},
        }
        g.save("S169_W8_VERDICT.json", verdict)
        print(json.dumps(verdict, indent=1, default=str)[:1800])
