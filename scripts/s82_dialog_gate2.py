#!/usr/bin/env python3
"""s82_dialog_gate2.py — targeted deep scan of string-table candidates for
AlertDialog$Builder items-family callers (framework or appcompat), then run
the VF-DIALOG-ITEMS retest session on the best real caller."""
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s82_lib as L  # noqa
from s82_dialog_gate import dex_scan_setitems, run_dialog_session  # noqa

OUT = f"{L.RUN}/cached_gates"
CANDIDATES = [
    "app.varlorg.unote_30.apk", "app.halma_15.apk",
    "com.clavierhaus.gnubg_102.apk", "com.hfut.schedule_2724.apk",
    "com.newsblur_289.apk", "com.vovagorodok.blichess_29.apk",
    "com.vovagorodok.blidraughts_3.apk", "cos.premy.mines_16.apk",
    "crypto.o0o0o0o0o.games.blackjack_4.apk",
    "de.taz.android.app.free_20102900.apk",
    "de.tobiasbielefeld.solitaire_71.apk", "eu.veldsoft.no.thanks_1.apk",
    "foehnix.widget_40.apk", "io.github.aoc_normal_1.apk",
    "io.github.hathibelagal.mykanji_7.apk",
    "org.secuso.privacyfriendlybattleship_101.apk",
    "ru.wohlsoft.thextech.fdroid_1030703.apk",
    "se.tube42.p9.android_11.apk", "site.leos.apps.lespas_118.apk",
    "com.emmanuelmess.tictactoe_3.apk",
    "rkr.simplekeyboard.inputmethod_145.apk", "unote.apk",
]

PRIORITY = ["de.tobiasbielefeld.solitaire_71.apk", "app.halma_15.apk",
            "eu.veldsoft.no.thanks_1.apk", "cos.premy.mines_16.apk",
            "crypto.o0o0o0o0o.games.blackjack_4.apk",
            "org.secuso.privacyfriendlybattleship_101.apk",
            "io.github.hathibelagal.mykanji_7.apk"]


def main():
    report_p = f"{OUT}/gates_report.json"
    report = json.load(open(report_p)) if os.path.exists(report_p) else {"GATES": {}}
    report.setdefault("GATES", {})
    scan_p = f"{OUT}/dialog_deep_scan.json"
    scan = json.load(open(scan_p)) if os.path.exists(scan_p) else {}

    todo = [c for c in CANDIDATES if c not in scan]
    for name in todo:
        apk = f"{L.APK_CACHE}/{name}"
        if not os.path.exists(apk):
            apk = f"/tmp/my-project/apk_cache/{name}"
        if not os.path.exists(apk):
            scan[name] = {"error": "missing"}
            continue
        print("deep scan", name, flush=True)
        scan[name] = dex_scan_setitems(apk)
        json.dump(scan, open(scan_p, "w"), indent=1)

    callers = {k: v for k, v in scan.items() if v.get("callers")}
    report["DIALOG_SCAN_DEEP"] = scan
    print("deep callers:", {k: v.get("methods") for k, v in callers.items()})

    if report["GATES"].get("DIALOG"):
        print("dialog retest already recorded")
        json.dump(report, open(report_p, "w"), indent=1)
        return

    pick = None
    for name in PRIORITY:
        if name in callers:
            pick = name
            break
    if not pick and callers:
        pick = sorted(callers)[0]
    if pick:
        apk = f"{L.APK_CACHE}/{pick}"
        if not os.path.exists(apk):
            apk = f"/tmp/my-project/apk_cache/{pick}"
        label = "dialog_retest_" + pick.replace(".apk", "").split("_")[0]
        r = run_dialog_session(apk, label, taps=((540, 960, 3), (540, 960, 5), (540, 500, 7)))
        r["GATE"] = "VF-DIALOG-ITEMS_REAL_TITLE"
        r["APK_NAME"] = pick
        r["SETITEMS_CALLERS"] = callers[pick]["callers"]
        r["METHODS"] = callers[pick].get("methods")
        report["GATES"]["DIALOG"] = [r]
        print("dialog retest:", pick, "frames", r.get("FRAMES"),
              "diff", r.get("PIXEL_DIFF_TAP"))
    else:
        report["GATES"]["DIALOG"] = [{"STATUS": "NO_REAL_ITEMS_CALLER_FOUND_IN_DEEP_SCAN"}]
        print("no real items caller among deep-scanned candidates")
    json.dump(report, open(report_p, "w"), indent=1)


if __name__ == "__main__":
    main()
