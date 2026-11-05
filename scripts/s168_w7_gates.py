#!/usr/bin/env python3
"""s168_w7_gates.py — S168: W7 (law F-C4-572 SecureRandom real-stream)
verification gates on MY line (HEAD 653fb0a5 + w7_laws.patch ea55443a).

REF = S167 W6 standing binary 53fa8392640d1279 (insurance)
NEW = build/miniandroid f7291feaaf778c0f (S167 tree + w7_laws.patch)

Phases (argv[1]):
  tb          Thunderbird clean A/B (NDFE census — the W7 headline claim)
  tbseed      TB A/B under SEED_SKIP fair envs + ALL forensic probes on NEW
  anchors_mg  microtimer (pin) + g2048 delta
  anchors_oc  opencalc delta
  dooz        dooz settle A/B (S156 fresh-store law)
  verdict     composite verdict JSON
"""
import json
import os
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s167_w6_gates as g
import s165_trains as t
import s166_trains as s166

# rebind module globals — functions resolve these at call time
g.REF = BASE / ("upload/_ma_local_backup/"
                "miniandroid_s167_w6stack_53fa8392640d1279.bin")
g.NEW = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s168_w7"
g.OUT.mkdir(parents=True, exist_ok=True)
g.EVID = BASE / "evidence/s168_w7"
g.EVID.mkdir(parents=True, exist_ok=True)

PROBES = {"MINIANDROID_F572_DIAG": "1",       # [F-C4-572] nextBytes rows
          "MINIANDROID_F572_PROBE": "1",      # [F572-CONTAINS-*] rows
          "MINIANDROID_F566_FIELD_DIAG": "1",  # F566-IGET/IPUT + W6-INCL
          "MINIANDROID_W6_CTOR_PROBE": "1",   # W6-CTOR rows
          "MINIANDROID_F566_ITER_DIAG": "1",  # F566-LI/HP rows
          "MINIANDROID_W6_CLASSEQ_PROBE": "1"}  # W6-CLASSEQ rows


def tb_seed_probes():
    """TB A/B under SEED_SKIP; NEW arm also carries all forensic probes
    (env-gated read-only — zero behavior change, S167 probe law)."""
    apk, pkg = g.APKS["tb"]
    store = g.OUT / "store_tb"
    pair = {}
    for tag, b, envs in (("tb_ref", g.REF, g.SEED_SKIP),
                         ("tb_new", g.NEW,
                          dict(g.SEED_SKIP, **PROBES))):
        for k in g.CLEAN_ENVS:
            os.environ.pop(k, None)
        os.environ.update(envs)
        pair[tag] = g.app_run(b, tag, apk, store, pkg,
                              max_seconds=100, frames=8)
        print(f"[{tag}] face={pair[tag]['screenshot_face']} "
              f"wall={pair[tag]['wall_s']}s uncaught={pair[tag]['uncaught']} "
              f"ndfe={pair[tag]['ndfe']} "
              f"pixels={pair[tag].get('app_owned_pixels')}", flush=True)
    for k in list(g.SEED_SKIP) + list(PROBES):
        os.environ.pop(k, None)
    # probe census on the NEW console
    cons = g.OUT / "tb_new.err"
    if cons.exists():
        txt = cons.read_text(errors="replace")
        pair["probe_census"] = {
            "f572_nextbytes": txt.count("[F-C4-572]"),
            "f572_contains_enter": txt.count("[F572-CONTAINS-ENTER]"),
            "f572_contains_ret_true": txt.count(
                "[F572-CONTAINS-RET] path=ident"),
            "f572_contains_ret_false": txt.count(
                "[F572-CONTAINS-RET] path=final-false"),
            "f566_iget_includes": txt.count("[F566-IGET] includes"),
            "w6_incl_rows": txt.count("[W6-INCL]"),
            "ndfe": txt.count("NoDefinitionFoundException"),
            "ice": txt.count("IllegalStateException"),
            "uncaught_rows": txt.count("UNCAUGHT"),
            "addlast_rows": txt.count("addLast"),
        }
        # first 3 probe rows of each family for the ledger
        for fam, pref in (("f572", "[F-C4-572]"),
                          ("contains", "[F572-CONTAINS-ENTER]"),
                          ("incl", "[W6-INCL]")):
            rows = [l for l in txt.splitlines() if l.startswith(pref)][:3]
            pair[f"probe_rows_{fam}"] = rows
    return pair


if __name__ == "__main__":
    phase = sys.argv[1]
    if phase == "tb":
        pair = g.tb_pair()
        g.save("S168_W7_TB.json", pair)
    elif phase == "tbseed":
        pair = tb_seed_probes()
        g.save("S168_W7_TB_SEED_PROBES.json", pair)
    elif phase == "anchors_mg":
        rows = {"microtimer": g.anchor_pair("microtimer"),
                "g2048": g.anchor_pair("g2048")}
        g.save("S168_W7_GATES.json", {"anchors": rows})
    elif phase == "anchors_oc":
        rows = {"opencalc": g.anchor_pair("opencalc")}
        g.save("S168_W7_GATES.json", {"anchors": rows})
    elif phase == "dooz":
        ctl = s166.dooz_run("w7_dz_ctl", g.REF, store_root=g.OUT)
        print(json.dumps(ctl), flush=True)
        g.save("S168_W7_TRAINS.json", {"w7_dz_ctl": ctl})
        fix = s166.dooz_run("w7_dz_fix", g.NEW, store_root=g.OUT)
        print(json.dumps(fix), flush=True)
        g.save("S168_W7_TRAINS.json",
               {"w7_dz_fix": fix,
                "w7_dz_summary": s166.pair_summary(ctl, fix)})
    elif phase == "verdict":
        tb = json.load(open(g.EVID / "S168_W7_TB_SEED_PROBES.json"))
        gates = json.load(open(g.EVID / "S168_W7_GATES.json"))
        anchors = gates["anchors"]
        tr = json.load(open(g.EVID / "S168_W7_TRAINS.json"))
        verdict = {
            "ref_bin": t.sha16(g.REF), "new_bin": t.sha16(g.NEW),
            "w7_patch_sha16": "ea55443a44263012 (claim-exact)",
            "anchors_all_inert": all(v.get("delta_inert")
                                     for v in anchors.values()),
            "microtimer_pin": all(v.get("pin_match") for v in
                                  anchors.values() if "pin_match" in v),
            "dooz": tr.get("w7_dz_summary", {}),
            "tb_ref": {k: tb["tb_ref"].get(k) for k in
                       ("wall_s", "uncaught", "ndfe", "app_owned_pixels",
                        "final_state")},
            "tb_new": {k: tb["tb_new"].get(k) for k in
                       ("wall_s", "uncaught", "ndfe", "app_owned_pixels",
                        "final_state")},
            "probe_census": tb.get("probe_census", {}),
        }
        g.save("S168_W7_VERDICT.json", verdict)
        print(json.dumps(verdict, indent=1, default=str)[:1500])
    else:
        print("unknown phase", phase)
        sys.exit(2)
