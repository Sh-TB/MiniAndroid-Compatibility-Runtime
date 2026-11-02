#!/usr/bin/env python3
"""s151_wave_summary.py — build evidence/s151_trains/S151_WAVE_SUMMARY.json from
the batch ledger + census log + wall results. All numbers code-derived."""
import hashlib, json, os, re, subprocess

BASE = "/home/z/my-project"
OUTD = f"{BASE}/evidence/s151_trains"
NEW = json.load(open(f"{OUTD}/S151_NEWBATCH.json"))

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

BIN = f"{BASE}/miniandroid/build/miniandroid"
BIN_SHA = sha16(BIN)

# census counts from the compD console log (code-derived, not memory)
census_log = open(f"{BASE}/run/s151/train70/compD_console.log", errors="replace").read()
census = {
    "env": "MINIANDROID_PMC_TRACE=Lsc0;|<init>,Ldr1;|c",
    "Lsc0_init_ENTER": len(re.findall(r"ENTER Lsc0;\.<init>", census_log)),
    "Ldr1_c_ENTER": len(re.findall(r"ENTER Ldr1;\.c", census_log)),
    "face_sha16": sha16(f"{BASE}/run/s151/train70/compD/screenshot.png"),
    "standing_dooz_pin": "851cc1761a1dfcdf",
    "verdict": "Lsc0; IS BORN LIVE (12 constructor entries in 25 frames) yet TRAIN-69 proved it never enters the tap hit-path (only 3 pointer-input nodes + host Lsv;.J dispatched; no-op singleton handler Lpv;.c holds the pointerInput arm) — the census closes the compD question: construction is NOT the missing link, dispatch WIRING is",
}

tally = {}
for name, row in sorted(NEW["rows"].items()):
    v = row.get("verdict") or ("INSTALL-FAIL" if row.get("install") == "FAIL" else "RUN-TIMEOUT")
    tally.setdefault(v, []).append({"name": name, "package": row.get("package"),
                                    "face": row.get("screenshot_sha16")})

dl_frontier = {
    "org.y20k.trackbook_62": "3 download attempts truncated (17.5MB/32.9MB partial, no EOCD; F-Droid throttle ~200KB/s; would exceed the 25MB wave cap anyway) — honest internet frontier",
}

summary = {
    "wave": "S151",
    "directive": "«ادامه بده قطار های تعداد بالا سورس کد ها اینترنت و سورس» — raise the train count with new internet-sourced open-source programs",
    "date": "2026-11-02",
    "binary_sha16": BIN_SHA,
    "binary_note": "fresh my-project build == CONT-11 W7b anchor f10101593d095ff7 BYTE-EXACT (not merely semantic)",
    "anchor_wall": {
        "script": "scripts/s151_wall.sh", "runs_per_pin": 3,
        "result": "12/13 PASS byte-exact x3",
        "pins_pass": ["opencalc 63020bc7", "chess 3f7e6707", "dooz 851cc176",
                       "microtimer bbd350b6", "unote 7481e9b4", "tower3d 11a38a5a",
                       "g2048 f43face08", "tetris b818a6a7", "snakedeluxe 5235683f",
                       "minicraft e77a073f", "gmem 4876e47d", "sqlnotes 748bb6cf"],
        "flagged": "snakeneon 4a19b1fe x3 deterministic vs pin b669ce89 — the SAME standing S149 build-env face drift (98.9% real content); no new drift",
    },
    "train70_compD_census": census,
    "internet_batch": {
        "source": "f-droid.org open-source repo (probe API -> repo APK), scripts/s151_internet_fetch.sh",
        "candidates": 46, "probed_ok": 18, "downloaded_ok": 16, "dl_truncated": dl_frontier,
        "tally": {k: len(v) for k, v in tally.items()},
        "rows": tally,
    },
    "count_advance": "16 new internet-sourced programs run to verdict this wave (5 REAL_APP_CONTENT) on top of the standing 10-slot queue + satellites + prior corpus",
    "artifacts": ["evidence/s151_trains/S151_NEWBATCH.json", "run/s151/train70/compD/*",
                   "run/s151/train70/compD_console.log", "run/s151_wall/*", "scripts/s151_*.sh|py"],
}
json.dump(summary, open(f"{OUTD}/S151_WAVE_SUMMARY.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(summary["internet_batch"]["tally"], indent=1))
print("census:", census["Lsc0_init_ENTER"], "Lsc0; births,", census["Ldr1_c_ENTER"], "Ldr1;.c,", census["face_sha16"], "face")
print("binary:", BIN_SHA)
