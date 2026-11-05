#!/usr/bin/env python3
"""s169_w8_probe.py — S169: TB Room storage-migration family forensics
on MY line (W7 binary f7291fea, seed+skip fair envs = S168 tb_new state).

Phase: capture the console rows around the Room death chain
(K9StoragePersister.loadValues -> DBUtil rethrow "Storage database upgrade
failed!" -> Koin InstanceCreationException) and the SQLITE-SHADOW query/
execSQL rows feeding it."""
import json
import os
import re
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s167_w6_gates as g

g.OUT = BASE / "run_s169_w8"
g.OUT.mkdir(parents=True, exist_ok=True)
g.EVID = BASE / "evidence/s169_w8"
g.EVID.mkdir(parents=True, exist_ok=True)

SEED_SKIP = {"MINIANDROID_APP_DATA_SEED": "1",
             "MINIANDROID_PROVIDER_SKIP":
                 "FirebaseInitProvider,MlKitInitProvider"}


def main():
    apk, pkg = g.APKS["tb"]
    store = g.OUT / "store_tb"
    for k in g.CLEAN_ENVS:
        os.environ.pop(k, None)
    os.environ.update(SEED_SKIP)
    row = g.app_run(g.NEW, "w8_tb", apk, store, pkg,
                    max_seconds=100, frames=8)
    for k in list(SEED_SKIP):
        os.environ.pop(k, None)
    print(f"[w8_tb] face={row['screenshot_face']} wall={row['wall_s']}s "
          f"uncaught={row['uncaught']} ndfe={row['ndfe']} "
          f"pixels={row.get('app_owned_pixels')}", flush=True)

    cons = g.OUT / "w8_tb.err"
    txt = cons.read_text(errors="replace")

    census = {
        "upgrade_failed": txt.count("Storage database upgrade failed"),
        "sqliteshadow_rows": txt.count("[SQLITE-SHADOW]"),
        "sqliteshadow_open": txt.count("[SQLITE-SHADOW] opened"),
        "sqliteshadow_create": txt.count("[SQLITE-SHADOW] create"),
        "sqliteshadow_exec_err": len(re.findall(
            r"\[SQLITE-SHADOW\].*(?:rc=|err=|failed)", txt)),
        "k9_storage_rows": len(re.findall(r"K9StoragePersister", txt)),
        "dbutil_rows": len(re.findall(r"DBUtil", txt)),
        "identity_hash_rows": len(re.findall(
            r"room_master_table|identity_hash|IdentityHash", txt)),
        "ice": txt.count("InstanceCreationException"),
        "ndfe": txt.count("NoDefinitionFoundException"),
        "pragma_rows": len(re.findall(r"PRAGMA|pragma", txt)),
        "room_rows": len(re.findall(r"RoomOpenHelper|room\.Room", txt)),
        "uncaught": txt.count("UNCAUGHT"),
    }
    print("census:", json.dumps(census, indent=1))

    # key rows for the ledger
    def grab(pat, n=6):
        return [l[:220] for l in re.findall(rf".*{pat}.*", txt)[:n]]

    ledger = {
        "census": census,
        "upgrade_failed_rows": grab("Storage database upgrade failed", 4),
        "sqliteshadow_first": [l[:220] for l in txt.splitlines()
                               if "[SQLITE-SHADOW]" in l][:14],
        "ice_first": grab("InstanceCreationException", 6),
        "room_master_rows": grab("room_master_table|identity_hash", 8),
        "migration_rows": grab("Migration|migration", 8),
        "execsql_err_rows": [l[:220] for l in txt.splitlines()
                             if "[SQLITE-SHADOW]" in l and
                             ("rc=" in l or "err=" in l or "failed" in l)][:10],
    }
    g.save("S169_W8_PROBE.json", {"w8_tb": row, "ledger": ledger,
                                  "console": str(cons)})
    for k, v in ledger.items():
        print(f"--- {k} ---")
        if isinstance(v, list):
            for l in v[:6]:
                print("   ", l)
        else:
            print("   ", json.dumps(v, indent=1)[:400])


if __name__ == "__main__":
    main()
