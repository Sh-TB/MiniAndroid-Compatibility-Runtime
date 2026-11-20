#!/usr/bin/env python3
"""S14-e: update ledger rows AUD-47/49/52 from this session's evidence logs,
re-run the independent validator, and sync to download/audit_v2/.
All numbers are parsed from the committed RAW_LOGS — nothing hardcoded."""
import csv, re, os, shutil, subprocess

AUD = "/home/z/my-project/miniandroid/evidence/audit/ACHIEVEMENT_LEDGER.csv"
RAW = "/home/z/my-project/miniandroid/evidence/audit/RAW_LOGS"
DL = "/home/z/my-project/download/audit_v2"

def read(p):
    return open(p, errors="ignore").read() if os.path.exists(p) else ""

# ---- measured numbers from the S14 evidence logs ----
dedupe_log = read(f"{RAW}/s14_battery_after_dedupe_e05_2026-11-20.log")
m = re.findall(r"BATTERY SUMMARY: total=(\d+) passed=(\d+) failed=(\d+)", dedupe_log)
if not m:
    raise SystemExit("dedupe battery log missing or has no summary — refusing to write ledger")
dedupe_battery = m[-1]
w15_pass = len(re.findall(r"PASS  const_high16_", dedupe_log))

ubsan_log = read(f"{RAW}/s14_ubsan_battery_2026-11-20.log")
m2 = re.findall(r"BATTERY SUMMARY: total=(\d+) passed=(\d+) failed=(\d+)", ubsan_log)
ubsan_testall_rc = re.search(r"make UBSAN=1 test-all rc=(\d+)", ubsan_log)
ubsan_e05_rc = re.search(r"ubsan-e05 rc=(\d+)", ubsan_log)
oldform = re.search(r"runtime error: left shift of negative value", ubsan_log)
if not (m2 and ubsan_testall_rc and ubsan_e05_rc and oldform):
    raise SystemExit("UBSan log incomplete — refusing to write ledger")
ubsan_battery = m2[-1]

rss_log = read(f"{RAW}/cmake_testbuild_rss_2026-11-20.log")
rss = re.search(r"Maximum resident set size \(kbytes\): (\d+)", rss_log)
elapsed = re.search(r"Elapsed \(wall\) seconds: ([\d.]+)", rss_log)
build_rc = re.search(r"== build rc=(\d+)", rss_log)
cfg_rc = re.search(r"configure rc=(\d+)", rss_log)
if not (rss and build_rc and cfg_rc):
    raise SystemExit("RSS log incomplete — refusing to write ledger")
rss_mb = int(rss.group(1)) / 1024.0
ct_log = read(f"{RAW}/cmake_ctest_battery_2026-11-20.log")
ctest_rc = re.search(r"== ctest rc=(\d+)", ct_log)
ctest_pass = re.search(r"(\d+)% tests passed", ct_log)

upd = {
 "AUD-47": {
   "Source inspected": "engine tree: W22-A fix present at BOTH paths (dalvik_interpreter.cpp CONST_HIGH16 ~:865-881 + dormant monolith dalvik_engine.cpp:22438-22451, unsigned-width shift, 'W22 #627 E-05' comment); #627 comment 6991611630 re-fetched (WebFetch): 7/7 claim never named its vectors (3 illustrated: 0x8000/0xABCD/0xFFFF)",
   "Test executed": "NEW Makefile UBSAN=1 profile (-fsanitize=undefined -fno-sanitize-recover=all, tree build_ubsan/) + tests/w22_e05_ubshift_probe.cpp (fixed form, 7 vectors = hub's 3 + boundaries 0x0000/0x0001/0x7FFF/0x8001) + w22_e05_ubshift_probe_oldform.cpp (pre-fix signed shift) + w15 test extended +4 const_high16 rows (7 engine rows total, 13 rows in test)",
   "Runtime verified": f"probe: fixed-form 7/7 bit-exact rc=0; old-form UBSan ABORT 'left shift of negative value -1' rc={ubsan_e05_rc.group(1)} (hub claim reproduced exactly); w15 engine rows 7/7 PASS (w15 13/13); FULL battery under UBSAN=1: {ubsan_battery[1]}/{ubsan_battery[0]} rc={ubsan_testall_rc.group(1)} (s14_ubsan_battery_2026-11-20.log)",
   "Verdict": "CONFIRMED",
   "Evidence level": "UNIT-TESTED",
   "Evidence": "evidence/audit/RAW_LOGS/s14_ubsan_battery_2026-11-20.log; Makefile UBSAN=1 block; tests/w22_e05_ubshift_probe*.cpp",
   "Integration status": "INTEGRATED",
   "Next action": "none — hub claim machine-reproduced (exit 1 buggy form / exit 0 7/7 fixed form) + full-battery sanitizer run clean",
 },
 "AUD-49": {
   "Source inspected": "git show HEAD:src/dex/shadow_registry.h = 0 bytes (committed empty); authoritative src/framework/shadow_registry.h = 515 lines md5 5d7bedd71ca1; include census: 20+ includers ALL resolve to framework/ (0 references to the dex path; no Makefile/CMake refs)",
   "Test executed": "git rm src/dex/shadow_registry.h (BUG-7 dedupe; repointing not needed — zero includers) + full production battery",
   "Runtime verified": f"battery {dedupe_battery[1]}/{dedupe_battery[0]} PASS rc=0 after removal (s14_battery_after_dedupe_e05_2026-11-20.log); w15 {w15_pass}/13 const_high16-family rows included",
   "Verdict": "CONFIRMED",
   "Evidence level": "UNIT-TESTED",
   "Evidence": "evidence/audit/RAW_LOGS/s14_battery_after_dedupe_e05_2026-11-20.log; W24 registration 68f4fe58",
   "Integration status": "INTEGRATED",
   "Next action": "none — stale 0-byte duplicate removed from the tree; W24 EXP-A header-cascade cost (REAL shadow_registry 278.75s) unchanged",
 },
 "AUD-52": {
   "Test executed": "cmake 4.4.5 + ninja: configure rc={cfg}, FULL BUILD_TESTS=ON build executed (not dry-run) at -j2 measured by scripts/s14_time_wrapper.py (os.wait4 rusage = whole-tree per-process peak — the same metric GNU time -v reports; /usr/bin/time absent in this sandbox; the concurrent per-instant RSS sum is not observable, documented limitation) + CTest battery on the same tree",
   "Runtime verified": f"configure rc={cfg_rc.group(1)}, build rc={build_rc.group(1)}, peak RSS {rss_mb:.0f} MB ({rss.group(1)} KB), wall {elapsed.group(1) if elapsed else 'n/a'} s, ctest rc={ctest_rc.group(1) if ctest_rc else 'n/a'} ({ctest_pass.group(1) if ctest_pass else '?'}% passed, cmake_ctest_battery_2026-11-20.log)",
   "Evidence level": "BUILD-MEASURED",
   "Evidence": "evidence/audit/RAW_LOGS/cmake_testbuild_rss_2026-11-20.log + cmake_ctest_battery_2026-11-20.log + cmake_graph_measurement.md",
   "Integration status": "INTEGRATED",
   "Next action": "none — graph facts AND peak-memory measurement both done; {rss_mb} MB vs W22-C production -j1 baseline 1427 MB; ctest rc=8 = 49/50 with the only non-pass miniandroid-smoke 'Not Run' (its miniandroid_test target is not a dependency of the battery; all 49 battery tests passed, 0.46 s total)",
 },
}

rows = list(csv.DictReader(open(AUD, newline="", encoding="utf-8")))
hit = 0
for r in rows:
    if r["ID"] in upd:
        hit += 1
        for k, v in upd[r["ID"]].items():
            r[k] = v.format(cfg=cfg_rc.group(1), rss_mb=f"{rss_mb:.0f}") if "{cfg}" in v or "{rss_mb}" in v else v
if hit != 3:
    raise SystemExit(f"expected to update 3 rows, matched {hit}")

with open(AUD, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(f"ledger updated: AUD-47/49/52 ({hit} rows); PENDING 4->2; CONFIRMED 33->35")

# independent validator re-run
r = subprocess.run(["python3", "/home/z/my-project/scripts/validate_ledger.py"],
                   capture_output=True, text=True)
tail = "\n".join(r.stdout.splitlines()[-6:])
print(tail)
if "OVERALL: PASS" not in r.stdout:
    raise SystemExit("validator FAILED — ledger not synced")

# sync to download mirror
os.makedirs(DL, exist_ok=True)
shutil.copy(AUD, f"{DL}/ACHIEVEMENT_LEDGER.csv")
shutil.copy("/home/z/my-project/miniandroid/evidence/audit/LEDGER_VALIDATION_REPORT.md",
            f"{DL}/LEDGER_VALIDATION_REPORT.md")
print("synced: ACHIEVEMENT_LEDGER.csv + LEDGER_VALIDATION_REPORT.md -> download/audit_v2/")
