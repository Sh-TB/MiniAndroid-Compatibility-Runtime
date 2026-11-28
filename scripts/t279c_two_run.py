#!/usr/bin/env python3
"""T279-CONT — two-run campaign for the 10 PENDING titles (8 restored S182
PARTIAL APKs + com.nononsenseapps.notepad), the same protocol/laws as
t279_two_run.py: two independent runs each (fresh store, separate rundirs)
+ two identical --click-test interaction runs for games. Incremental JSON:
run_t279_cont/T279_CONT_BATTERY.json.
"""
import json
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s165_trains as t
import t279_two_run as tr

# tag: (apk_rel, secs, kind, interactive)
TITLES = {
    "aeropayout": ("upload/fdroid_batch/com.aeropayout.game_12.apk", 45, "game", True),
    "awagam": ("upload/fdroid_batch/com.awagam.android_5.apk", 45, "game", True),
    "pfludo": ("upload/fdroid_batch/org.secuso.privacyfriendlyludo_100.apk", 45, "game", True),
    "quicksettingssound": ("upload/fdroid_batch/com.curryplayer.quicksettingssoundprofile_11.apk", 60, "app", False),
    "lrceditor": ("upload/fdroid_batch/com.cg.lrceditor_57.apk", 60, "app", False),
    "floatdeck": ("upload/fdroid_batch/app.floatdeck_8.apk", 60, "app", False),
    "webstack": ("upload/fdroid_batch/com.chiranth7.webstack_6.apk", 60, "app", False),
    "dmfstasks": ("upload/fdroid_batch/org.dmfs.tasks_82200.apk", 60, "app", False),
    "nonotepad": ("upload/fdroid_batch/com.nononsenseapps.notepad_72700.apk", 60, "app", False),
}
tr.TITLES = TITLES
tr.BIN = BASE / "miniandroid/build/miniandroid"
tr.OUT = BASE / "run_t279_cont"
tr.OUT.mkdir(parents=True, exist_ok=True)
tr.EJSON = tr.OUT / "T279_CONT_BATTERY.json"

if __name__ == "__main__":
    tr.main()
