#!/usr/bin/env python3
"""s169_w8_fix.py — S169: TB A/B for the setVersion REAL-PRAGMA law.
REF = W7 standing f7291fea (no law), NEW = 991d8923 (law + SQLDBG probes).
NEW arm carries MINIANDROID_SQLDBG=1 (read-only forensics)."""
import json
import os
import re
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s167_w6_gates as g
import s165_trains as t

g.REF = BASE / ("upload/_ma_local_backup/"
                "miniandroid_s168_w7_f7291feaaf778c0f.bin")
g.NEW = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s169_w8"
g.OUT.mkdir(parents=True, exist_ok=True)
g.EVID = BASE / "evidence/s169_w8"
g.EVID.mkdir(parents=True, exist_ok=True)

SQLDBG = {"MINIANDROID_SQLDBG": "1"}
SEED_SKIP = {"MINIANDROID_APP_DATA_SEED": "1",
             "MINIANDROID_PROVIDER_SKIP":
                 "FirebaseInitProvider,MlKitInitProvider"}


def run_arm(tag, b, envs):
    apk, pkg = g.APKS["tb"]
    store = g.OUT / "store_tb2"
    for k in g.CLEAN_ENVS:
        os.environ.pop(k, None)
    os.environ.update(envs)
    row = g.app_run(b, tag, apk, store, pkg, max_seconds=100, frames=8)
    for k in list(envs):
        os.environ.pop(k, None)
    print(f"[{tag}] face={row['screenshot_face']} wall={row['wall_s']}s "
          f"uncaught={row['uncaught']} ndfe={row['ndfe']} "
          f"pixels={row.get('app_owned_pixels')} "
          f"api={row.get('api_calls')}", flush=True)
    cons = g.OUT / f"{tag}.err"
    if cons.exists():
        txt = cons.read_text(errors="replace")
        row["census"] = {
            "upgrade_failed": txt.count("Storage database upgrade failed"),
            "ice": txt.count("InstanceCreationException"),
            "ndfe": txt.count("NoDefinitionFoundException"),
            "uncaught": txt.count("UNCAUGHT"),
            "standalone_opens": txt.count("[SQLITE-SHADOW] standalone-open"),
            "setversion_err": txt.count("[SQLITE-SHADOW] setVersion rc="),
            "sqldbg_rows": txt.count("[SQLDBG]"),
            "sqldbg_not_handled": txt.count("[SQLDBG] db NOT_HANDLED"),
        }
        row["sqldbg_methods"] = sorted(set(re.findall(
            r"\[SQLDBG\] db (\S+) oid", txt)))[:20]
        row["sqldbg_nh_methods"] = sorted(set(re.findall(
            r"\[SQLDBG\] db NOT_HANDLED (\S+) oid", txt)))[:20]
        rows = [l[:200] for l in txt.splitlines()
                if l.startswith("[SQLDBG]")][:14]
        row["sqldbg_first_rows"] = rows
        opens = [l[:200] for l in txt.splitlines()
                 if "[SQLITE-SHADOW] standalone-open" in l][:6]
        row["opens"] = opens
    return row


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "pair"
    if phase == "pair":
        ref = run_arm("w8_ref", g.REF, dict(SEED_SKIP))
        new = run_arm("w8_new", g.NEW, dict(SEED_SKIP, **SQLDBG))
        out = {"w8_ref": ref, "w8_new": new,
               "bins": {"ref": t.sha16(g.REF), "new": t.sha16(g.NEW)}}
        g.save("S169_W8_SETVER_AB.json", out)
        print("census ref :", json.dumps(ref["census"]))
        print("census new :", json.dumps(new["census"]))
        print("NH methods :", new.get("sqldbg_nh_methods"))
        for l in (new.get("sqldbg_first_rows") or [])[:14]:
            print("   ", l)
