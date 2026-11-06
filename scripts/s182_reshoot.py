#!/usr/bin/env python3
"""s182_reshoot.py — re-shoot the S180 16-title battery screenshots so the
S182 mosaic carries CURRENT faces for every standing title (sandbox recycle
wiped run_s180_battery/). Reuses s180_corpus_battery machinery; rows go to
evidence/s182_minimal2/S180_RESHOOT.json (S180_BATTERY.json is NOT touched).
"""
import json
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s180_corpus_battery as m  # noqa: E402
import s166_trains as s166       # noqa: E402

OUTJ = BASE / "evidence/s182_minimal2/S180_RESHOOT.json"
rows = json.load(open(OUTJ)) if OUTJ.exists() else {}

TODO = sys.argv[1:] or ["microtimer", "g2048", "opencalc", "tetris",
                        "snake_deluxe", "snakeneon", "ttt_deluxe",
                        "minicraft", "gmdice", "tb", "nc", "tusky",
                        "forkgram", "solitaire", "freebloks", "memory",
                        "klondike", "dooz", "tg"]

for name in TODO:
    if name in rows and rows[name].get("face"):
        print(f"== skip {name} (face {rows[name]['face'][:8]})", flush=True)
        continue
    spec = m.TITLES[name]
    if spec.get("pkg") is None:
        # reuse the pkg learned in S180 (avoid the .staging discover bug)
        s180 = json.load(open(BASE / "evidence/s180_battery/S180_BATTERY.json"))
        prev = (s180.get(name) or {}).get("pkg") if isinstance(
            s180.get(name), dict) else None
        if prev:
            spec["pkg"] = prev
    print(f"=== reshoot {name} ({spec['apk']})", flush=True)
    if name == "dooz":
        row = s166.dooz_run("s182_dz", m.BIN, budget=240,
                            store_root=m.OUT)
    elif name == "tg":
        row = s166.tg_run("s182_tg", m.BIN, store_name="s182_tg_store")
    else:
        row = m.app_run(name, spec)
    row["class"] = m.classify(row, spec)
    rows[name] = row
    json.dump(rows, open(OUTJ, "w"), indent=1, default=str)
    print(f"--- {name}: {row.get('class')} face={row.get('face')} "
          f"uncaught={row.get('uncaught')}", flush=True)

print("\n== S180 reshoot ==")
for k, v in rows.items():
    print(f"{k:12s} {str(v.get('class')):18s} face={v.get('face')} "
          f"uncaught={v.get('uncaught')}")
