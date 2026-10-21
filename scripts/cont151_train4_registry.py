#!/usr/bin/env python3
"""cont151_train4_registry.py — TRAIN 4 (CONT-151) registry update.
Adds F-NEW-477 (dooz content-draw terminal: T0 registry query NULL 12/12) and
appends the TRAIN 4 decode chain to F-NEW-473. Syncs main + mirror."""
import json

F477_EVIDENCE = (
    "CONT-151 TRAIN 4 (binary f6b272ea, dooz v23): the blank-face content-draw "
    "terminal is now ROOT-CAUSED one level below CONT-150's named levers. "
    "Chain, every link runtime-verified: (1) Lpz0;.M0 (node draw) fetches the "
    "content draw-block via T0(4); (2) T0 first queries the registry via "
    "Lqz0;.g (contains-style has-query) — returns FALSE 12/12 windows (RET-"
    "TRACE: Lpz0;.T0 -> NULL 12/12, METHOD-TRACE shape A exits via the "
    "chain-walk-null path, shape B via U0 compare-null path); (3) M0 pc37 "
    "`if-eqz v1 -> 119` skips the entire content step 12/12 -> ZERO canvas "
    "primitives. (4) The INSERT side RUNS: Lqz0;.a 65 entries (callers "
    "Lkz0;.e <- Lel0;.d node-binding cascade <- Lt4;.<init>), but with "
    "hash-shaped keys (a1 in {-1,-32770,-2400282,-295178,...}) across "
    "per-instance containers (Lg4;/Lc70;/Lcz;/Lcz0;/Lh8;/Ljw;/Loq;/Lp31;/Lgj;"
    "/Lg70;...), while the draw-time query asks key 4 — the insert/query "
    "key-space semantics of the Lqz0; static ScatterMap util family is the "
    "precisely-named next lever (S36/S37 ScatterSet law heritage). "
    "(5) Exonerations (all runtime-verified, engine faithful): Lxk0;.h1 and "
    "Lug0;.h1 are LAYOUT-BOUNDS OVERLAY draws (getShowLayoutBounds gate — "
    "0x0a=move-result law; exit to return-void is correct upstream behavior "
    "when bounds are off); the Lpz0;.r1 exits are upstream-faithful null-"
    "modifier paths (exonerated by fnew476_probe 5/5 invoke-arg fidelity); "
    "Lel0;.x() layer-holder caching (y-flag write-back) executes its real "
    "dex logic; node layer-holder .x set only for late-tree nodes by "
    "Lel0;.<init>(106) — upstream-faithful. VERDICT: no engine bug found in "
    "this train's surface; the gap is the app-side registry key semantics."
)

F473_APPEND = (
    " || CONT-151 TRAIN 4: content-draw terminal re-anchored to the Lqz0; "
    "registry query (see F-NEW-477): T0(4) NULL 12/12 -> M0 skips content; "
    "inserts run 65x with hash keys vs query key 4 (key-space mismatch = "
    "next lever). Layout-bounds overlays identified (Lxk0;.h1 / Lug0;.h1 — "
    "both correctly gated by getShowLayoutBounds); draw-window census "
    "complete: transforms flow (Ly3;.f x24), overlays skip, content absent."
)

for path in ("root_registry.json", "canonical/root_cause_registry.json"):
    r = json.load(open(path))
    ids = {e.get("id") for e in r}
    assert "F-NEW-477" not in ids, f"F-NEW-477 already in {path}"
    r.append({
        "id": "F-NEW-477",
        "title": ("F-NEW-477 — dooz content-draw terminal: T0(4) registry "
                  "query NULL 12/12 -> Lpz0;.M0 skips content step; Lqz0; "
                  "insert(hash-keys 65x) vs query(key 4) key-space law"),
        "status": "CLASSIFIED",
        "priority": "P0",
        "layer": "compose-draw",
        "evidence": F477_EVIDENCE,
        "opened": "CONT-151 TRAIN 4",
    })
    for e in r:
        if e.get("id") == "F-NEW-473":
            ev = e.get("evidence")
            if not isinstance(ev, str):
                ev = json.dumps(ev, ensure_ascii=False) if ev is not None else ""
            e["evidence"] = ev + F473_APPEND
    json.dump(r, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(r)} roots")
ids_a = {e["id"] for e in json.load(open("root_registry.json"))}
ids_b = {e["id"] for e in json.load(open("canonical/root_cause_registry.json"))}
print("main==mirror:", ids_a == ids_b)
