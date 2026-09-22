#!/usr/bin/env python3
"""s82_freeze_registry.py — S82 §3/§4/§25: FREEZE the S81 corpus into the
canonical per-title registry with stable TITLE_IDs.

Identity law: TITLE_ID is independent of GitHub issue numbers and derived
ONLY from the frozen S81 corpus order (deterministic, CORPUS_SEED-pinned):
  GAMES_100[i]  -> GAME-{i+1:03d}
  APPS_100[i]   -> APP-{i+1:03d}
  MANDATORY[0]  -> MAND-001 (P9, §49 Gate A)
  MANDATORY[1]  -> MAND-002 (TimeLimit, §49 Gate B)

Stopwatch/Platformer inventories are marked with their membership: if the
package is already a 200-title member it gets a cross-ref; otherwise it is
recorded as inventory-only (NOT silently dropped — §56 "never silently drop").

Output: docs/corpus/s82/title_registry.json  (canonical machine registry)
        docs/corpus/s82/REGISTRY_FREEZE.md   (human freeze note)
Never regenerates corpus content from memory — reads only frozen S81 files.
"""
import csv
import hashlib
import json
import os
import subprocess
import sys

ROOT = "/home/z/my-project"
S81 = f"{ROOT}/docs/corpus/s81/corpus_index.json"
S81_CSV = f"{ROOT}/docs/corpus/s81/corpus_summary.csv"
OUT_DIR = f"{ROOT}/docs/corpus/s82"
os.makedirs(OUT_DIR, exist_ok=True)

STOPWATCH_CATS = {"stopwatch"}
PLATFORMER_CATS = {"platformer-game"}


def git_head():
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()


def main():
    corpus = json.load(open(S81))
    games = corpus["GAMES_100"]
    apps = corpus["APPS_100"]
    mand = corpus["MANDATORY"]
    stopwatch = corpus["STOPWATCH_INVENTORY"]
    platformer = corpus["PLATFORMER_INVENTORY"]

    assert len(games) == 100, f"GAMES_100 = {len(games)} != 100"
    assert len(apps) == 100, f"APPS_100 = {len(apps)} != 100"

    titles = []

    def rec(tid, ttype, item, extra=None):
        r = {
            "TITLE_ID": tid,
            "TYPE": ttype,
            "NAME": item.get("PACKAGE", ""),
            "PACKAGE": item.get("PACKAGE") or item.get("APP_ID", ""),
            "CATEGORY": item.get("CATEGORY", ""),
            "F_DROID_URL": item.get("F_DROID_URL", ""),
            "SOURCE_URL": item.get("SOURCE_URL", ""),
            "SOURCE_REVISION": "",
            "VERSION": item.get("LATEST_VERSION", item.get("VERSION", "")),
            "VERSION_CODE": item.get("VERSION_CODE", ""),
            "APK_SHA256": "",
            "ISSUE_NUMBER": None,
            "ISSUE_URL": "",
            # status ladder (S82 §7) — lowest honest state until executed
            "STATE": "STATE-NOT-LOADED",
            "EXECUTION": "NOT_TESTED",
            "INTERACTION": "NONE",
            "STATE_CHANGE": "NONE",
            "RENDERING": "NONE",
            "GRAPHICS": "NONE",
            "VISUAL_CORRELATION": "NONE",
            "HUMAN_VERIFICATION": "NOT_REVIEWED",
            "F_IDS": [],
            "VF_IDS": [],
            "REFERENCE": {"STATUS": "PENDING", "URL": "", "SHA256": ""},
            "LAST_TESTED_COMMIT": "",
            "SESSION_ID": "",
            "SCREENSHOT_SHA256": "",
        }
        if extra:
            r.update(extra)
        titles.append(r)
        return r

    for i, g in enumerate(games):
        rec(f"GAME-{i+1:03d}", "game", g)
    for i, a in enumerate(apps):
        rec(f"APP-{i+1:03d}", "app", a)
    for i, m in enumerate(mand):
        rec(f"MAND-{i+1:03d}", "mandatory", m,
            extra={"NOTE": m.get("NOTE", ""),
                   "REFERENCE_SCREENSHOT_URL": m.get("REFERENCE_SCREENSHOT_URL", ""),
                   "SOURCE_URL": m.get("SOURCE_URL", ""),
                   "ISSUE_TRACKER": m.get("ISSUE_TRACKER", ""),
                   "BUILD_METADATA_URL": m.get("BUILD_METADATA_URL", ""),
                   "DESCRIPTION": m.get("DESCRIPTION", "")})

    # inventory membership marking (§3 dedup)
    by_pkg = {t["PACKAGE"]: t for t in titles}
    inv_mark = []
    for inv_name, inv in (("stopwatch", stopwatch), ("platformer", platformer)):
        for it in inv:
            pkg = it.get("PACKAGE") or it.get("APP_ID", "")
            member = by_pkg.get(pkg)
            inv_mark.append({
                "INVENTORY": inv_name, "PACKAGE": pkg,
                "MEMBER_TITLE_ID": member["TITLE_ID"] if member else None,
                "MEMBERSHIP": "corpus-member" if member else "inventory-only",
            })

    # BATCH-01 packages from S81 evidence (re-verification list, §49 Gate C)
    b01 = json.load(open(f"{ROOT}/docs/evidence/s81/batch01_report.json"))
    b01_map = {}
    for r in b01["results"]:
        m = by_pkg.get(r["PACKAGE"])
        b01_map[r["PACKAGE"]] = {
            "TITLE_ID": m["TITLE_ID"] if m else None,
            "S81_STATUS": r.get("STATUS"),
            "S81_APK_SHA256": r.get("APK_SHA256", ""),
            "S81_VERSION": r.get("VERSION"),
            "S81_VERSION_CODE": r.get("VERSION_CODE"),
        }

    # duplicate scan (§3)
    pkgs = [t["PACKAGE"] for t in titles]
    dups = sorted({p for p in pkgs if pkgs.count(p) > 1})

    head = git_head()
    freeze = {
        "WAVE": "S82",
        "FROZEN_FROM": "docs/corpus/s81/corpus_index.json",
        "FROZEN_AT_COMMIT": head,
        "CORPUS_SEED": corpus["CORPUS_SEED"],
        "TITLE_ID_SCHEME": {
            "GAME": "GAME-001..GAME-100 (frozen GAMES_100 order)",
            "APP": "APP-001..APP-100 (frozen APPS_100 order)",
            "MAND": "MAND-001 P9, MAND-002 TimeLimit (§49 gates A/B)",
        },
        "COUNTS": {
            "GAME": 100, "APP": 100, "MAND": len(mand), "TOTAL": len(titles),
        },
        "DUPLICATE_PACKAGES": dups,
        "INVENTORY_MEMBERSHIP": inv_mark,
        "BATCH01_S81_RESULTS": b01_map,
        "STATUS_LADDER": [
            "STATE-NOT-LOADED", "STATE-LOADED", "STATE-LAUNCHING",
            "STATE-ONCREATE", "STATE-NONBLANK", "STATE-RENDERED",
            "STATE-GRAPHICALLY-NONTRIVIAL", "STATE-INTERACTIVE",
            "STATE-STATE-CHANGED", "STATE-SEMANTICALLY-CORRELATED",
            "STATE-VISUALLY-VERIFIED",
        ],
        "FAILURE_LABELS": [
            "FAIL-CRASH", "FAIL-NPE", "FAIL-ONCREATE", "FAIL-HANG", "FAIL-ANR",
            "FAIL-RESOURCE", "FAIL-DRAWABLE", "FAIL-BITMAP", "FAIL-IMAGE",
            "FAIL-ICON", "FAIL-TEXT", "FAIL-FONT", "FAIL-LAYOUT",
            "FAIL-MEASURE", "FAIL-INPUT", "FAIL-STATE", "FAIL-LIFECYCLE",
            "FAIL-CANVAS", "FAIL-PALETTE", "FAIL-COLOR", "FAIL-ANIMATION",
            "FAIL-STORAGE", "FAIL-NETWORK", "FAIL-UNKNOWN",
        ],
        "TITLES": titles,
    }
    path = f"{OUT_DIR}/title_registry.json"
    json.dump(freeze, open(path, "w"), indent=1)

    # human freeze note
    by_type = {"game": 0, "app": 0, "mandatory": 0}
    for t in titles:
        by_type[t["TYPE"]] += 1
    inv_only = [m for m in inv_mark if m["MEMBERSHIP"] == "inventory-only"]
    lines = [
        "# S82 REGISTRY FREEZE (§3/§4)",
        "",
        f"- Frozen from: `docs/corpus/s81/corpus_index.json` (CORPUS_SEED `{corpus['CORPUS_SEED']}`)",
        f"- Frozen at commit: `{head[:12]}`",
        f"- TITLE_RECORDS: {len(titles)} — GAME {by_type['game']} · APP {by_type['app']} · MAND {by_type['mandatory']}",
        f"- Duplicate packages in the 200: {dups if dups else 'NONE'}",
        f"- Inventory packages not in the 200 (recorded, never dropped): "
        f"{[m['PACKAGE'] for m in inv_only] if inv_only else 'NONE (all inventory packages are corpus members)'}",
        "",
        "TITLE_ID is identity, not issue number: issue numbers may change, IDs never do.",
        "MAND-001 = P9 (se.tube42.p9.android) · MAND-002 = TimeLimit (io.timelimit.android.aosp.direct).",
        "",
    ]
    open(f"{OUT_DIR}/REGISTRY_FREEZE.md", "w").write("\n".join(lines))

    print(f"frozen {len(titles)} titles -> {path}")
    print("dups:", dups)
    print("inventory-only:", [m["PACKAGE"] for m in inv_only])
    print("MAND-001:", titles[200]["PACKAGE"], "| MAND-002:", titles[201]["PACKAGE"])
    # quick identity checks
    assert titles[0]["TITLE_ID"] == "GAME-001" and titles[99]["TITLE_ID"] == "GAME-100"
    assert titles[100]["TITLE_ID"] == "APP-001" and titles[199]["TITLE_ID"] == "APP-100"


if __name__ == "__main__":
    main()
