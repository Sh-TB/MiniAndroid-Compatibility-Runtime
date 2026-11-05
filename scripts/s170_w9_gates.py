#!/usr/bin/env python3
"""s170_w9_gates.py — S170: verify the coder's W8+W9 chain (#522 + #525)
on MY line. Main source = byte-identical to coder chain
(69c871e4 + w8_laws 5562609d0c3e30f3 + w9_laws b708b8460eac637c);
S169's duplicate setVersion source superseded by F-C4-574 (same root,
same site — two independent lines converged).

REF = S169 standing 991d8923 (my setVersion law only),
NEW = 4bb7c4d4 (w8+w9 chain build).

Phases: four_title / anchors_mg / anchors_oc / dooz / tg / verdict.
"""
import json
import os
import re
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s167_w6_gates as g
import s165_trains as t
import s166_trains as s166

g.REF = BASE / ("upload/_ma_local_backup/"
                "miniandroid_s169_setver_991d89239e69c679.bin")
g.NEW = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s170_w9"
g.OUT.mkdir(parents=True, exist_ok=True)
g.EVID = BASE / "evidence/s170_w9"
g.EVID.mkdir(parents=True, exist_ok=True)

# 4APP four-title set (S168 caveat resolved: NC/TK/CB now pin-matched local)
FOUR = {
    "tb": (BASE / "upload/net.thunderbird.android_33.apk",
           "net.thunderbird.android"),
    "nc": (BASE / "upload/com.nextcloud.client_350000290.apk",
           "com.nextcloud.client"),
    "tk": (BASE / "upload/com.keylesspalace.tusky_145.apk",
           "com.keylesspalace.tusky"),
    "cb": (BASE / "upload/fdroid_batch/org.connectbot_11101000.apk",
           "org.connectbot"),
}
SEED_SKIP = {"MINIANDROID_APP_DATA_SEED": "1",
             "MINIANDROID_PROVIDER_SKIP":
                 "FirebaseInitProvider,MlKitInitProvider"}


def save_anchors(rows):
    """Nested-merge (S167 lesson)."""
    out = g.EVID / "S170_W9_GATES.json"
    cur = {}
    if out.exists():
        try:
            cur = json.load(open(out))
        except Exception:
            cur = {}
    cur.setdefault("anchors", {}).update(rows)
    json.dump(cur, open(out, "w"), indent=1, default=str)
    print("evidence ->", out)


def census(tag, app):
    """Per-app acceptance census off the console (coder VERIFY greps)."""
    con = g.OUT / f"{tag}.err"
    if not con.exists():
        return {}
    txt = con.read_text(errors="replace")
    c = {
        "vme": txt.count("VirtualMachineError"),
        "f578": txt.count("F-C4-578"),
        "f574": txt.count("F-C4-574"),
        "upgrade_failed": txt.count("Storage database upgrade failed"),
        "converter_iae": txt.count("A required type converter"),
        "gson_iae": txt.count("Only combinations of"),
        "ule": txt.count("UnsatisfiedLinkError"),
        "f581": txt.count("F-C4-581"),
        "f582": txt.count("F-C4-582"),
        "f583": txt.count("F-C4-583"),
        "f584": txt.count("F-C4-584"),
        "f585": txt.count("F-C4-585"),
        "f586": txt.count("F-C4-586"),
        "ndfe": txt.count("NoDefinitionFoundException"),
        "uncaught": txt.count("UNCAUGHT"),
    }
    m = re.search(r"RegisterNatives: (\d+) methods for org/conscrypt/"
                  r"NativeCrypto", txt)
    c["register_natives"] = int(m.group(1)) if m else 0
    pbq = [l[:160] for l in txt.splitlines() if "F-C4-578" in l][:3]
    if pbq:
        c["pbq_lines"] = pbq
    rn = [l[:160] for l in txt.splitlines() if "RegisterNatives" in l][:2]
    if rn:
        c["regnat_lines"] = rn
    return c


def four_title(only=None):
    """All four titles, REF vs NEW back-to-back (seed+skip fair baseline)."""
    rows = {}
    for name, (apk, pkg) in FOUR.items():
        if only and name != only:
            continue
        store = g.OUT / f"store_{name}"
        pair = {}
        for tag, b in ((f"{name}_ref", g.REF), (f"{name}_new", g.NEW)):
            for k in g.CLEAN_ENVS:
                os.environ.pop(k, None)
            os.environ.update(SEED_SKIP)
            pair[tag] = g.app_run(b, tag, apk, store, pkg,
                                  max_seconds=100, frames=8)
            pair[tag]["census"] = census(tag, name)
            r = pair[tag]
            print(f"[{tag}] face={r['screenshot_face']} wall={r['wall_s']}s "
                  f"uncaught={r['uncaught']} ndfe={r['ndfe']} "
                  f"pixels={r.get('app_owned_pixels')} "
                  f"state={r.get('final_state')}", flush=True)
            print("   census:", json.dumps(
                {k: v for k, v in r["census"].items()
                 if not k.endswith("_lines")}), flush=True)
        for k in SEED_SKIP:
            os.environ.pop(k, None)
        rows[name] = pair
        g.save("S170_W9_FOURTITLE.json", {name: pair})
    return rows


if __name__ == "__main__":
    phase = sys.argv[1]
    if phase == "four_title":
        four_title(sys.argv[2] if len(sys.argv) > 2 else None)
    elif phase == "anchors_mg":
        rows = {"microtimer": g.anchor_pair("microtimer"),
                "g2048": g.anchor_pair("g2048")}
        save_anchors(rows)
    elif phase == "anchors_oc":
        save_anchors({"opencalc": g.anchor_pair("opencalc")})
    elif phase == "dooz":
        ctl = s166.dooz_run("w9_dz_ctl", g.REF, store_root=g.OUT)
        print(json.dumps(ctl))
        save_anchors({"w9_dz_ctl": ctl})
        fix = s166.dooz_run("w9_dz_fix", g.NEW, store_root=g.OUT)
        print(json.dumps(fix))
        save_anchors({"w9_dz_fix": fix,
                      "w9_dz_summary": s166.pair_summary(ctl, fix)})
    elif phase == "tg":
        ctl = s166.tg_run("w9_tg_ctl", g.REF, store_name="s170_tg")
        print(json.dumps(ctl))
        save_anchors({"w9_tg_ctl": ctl})
        fix = s166.tg_run("w9_tg_fix", g.NEW, store_name="s170_tg")
        print(json.dumps(fix))
        save_anchors({"w9_tg_fix": fix,
                      "w9_tg_summary": s166.pair_summary(ctl, fix)})
    elif phase == "verdict":
        ft = json.load(open(g.EVID / "S170_W9_FOURTITLE.json"))
        gt = json.load(open(g.EVID / "S170_W9_GATES.json"))
        an = gt.get("anchors", {})
        verdict = {
            "ref_bin": t.sha16(g.REF), "new_bin": t.sha16(g.NEW),
            "chain": {"base": "69c871e4 (S168)",
                      "w8_laws_sha16": "5562609d0c3e30f3",
                      "w9_laws_sha16": "b708b8460eac637c"},
            "acceptance": {
                name: {
                    "ref": {k: ft[name][f"{name}_ref"]["census"].get(k)
                            for k in ("vme", "f578", "f574", "upgrade_failed",
                                      "converter_iae", "gson_iae", "ule",
                                      "f581", "register_natives", "ndfe",
                                      "uncaught")},
                    "new": {k: ft[name][f"{name}_new"]["census"].get(k)
                            for k in ("vme", "f578", "f574", "upgrade_failed",
                                      "converter_iae", "gson_iae", "ule",
                                      "f581", "register_natives", "ndfe",
                                      "uncaught")},
                    "ref_state": ft[name][f"{name}_ref"].get("final_state"),
                    "new_state": ft[name][f"{name}_new"].get("final_state"),
                    "face_equal": (ft[name][f"{name}_ref"]["screenshot_face"]
                                   == ft[name][f"{name}_new"]["screenshot_face"]),
                } for name in ("tb", "nc", "tk", "cb")},
            "anchors": {k: {kk: vv for kk, vv in v.items()
                            if kk in ("delta_inert", "pin_match",
                                      "screenshot_face")}
                        for k, v in an.items()
                        if isinstance(v, dict) and "delta_inert" in v},
        }
        g.save("S170_W9_VERDICT.json", verdict)
        print(json.dumps(verdict, indent=1, default=str)[:2400])
