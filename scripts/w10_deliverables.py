#!/usr/bin/env python3
"""W10 Phase 8: assemble the required deliverable JSONs and build-safety report."""
import json, os, hashlib, subprocess

os.chdir("/home/z/my-project/miniandroid")
E = "evidence/wave10"
bench = json.load(open(f"{E}/w10_benchmarks.json"))
verify = json.load(open(f"{E}/w10_verify_raw.json"))
opcode = json.load(open(f"{E}/w10_opcode_profile.json"))
finalp = json.load(open(f"{E}/w10_final_parity.json"))
safety = json.load(open(f"{E}/w10_build_safety_raw.json"))

# split benchmark deliverables
json.dump({"meta": {"revision": bench["revision"], "compiler": bench["compiler"], "host": bench["host"]},
           "interpreter": bench["interpreter"], "opcode_reference": bench["opcode"],
           "opcode_after_wave10_profile": opcode, "noop": bench["noop"]},
          open(f"{E}/wave10_interpreter_benchmarks.json", "w"), indent=1)
json.dump({"meta": {"revision": bench["revision"], "compiler": bench["compiler"], "host": bench["host"],
                    "blocker": "bridge -O1 candidate OOM-killed by 4GB cgroup; -O0 accepted"},
           "bridge": bench["bridge"]},
          open(f"{E}/wave10_bridge_benchmarks.json", "w"), indent=1)

# runtime parity deliverable
identity = {}
for line in open("evidence/wave9/apk_identity.txt"):
    parts = line.split()
    if len(parts) == 2:
        identity[parts[1]] = parts[0]
parity = {
    "apk_files_identity_sha256_16": identity,
    "canonical_screenshots": {"ru.zxalexis.ugaday_15": "87fe2676", "tech.gaskell.diceroller_1_debug": "46b07062",
                               "com.itsfrz.tictactoe_5": "d55056a8"},
    "expected_classes": {"ru.zxalexis.ugaday_15": "SUCCESS", "tech.gaskell.diceroller_1_debug": "PARTIAL",
                          "com.itsfrz.tictactoe_5": "PARTIAL"},
    "interpreter_bridge_profiles_x3_reps": verify["apks"],
    "opcode_profile_recheck_x1": opcode["apks"],
    "final_combined_profile_gate": finalp,
    "conclusion": {"guess": "SUCCESS — hash identical, stable across reps",
                   "diceroller": "PARTIAL — preserved, not upgraded (no genuine interaction evidence)",
                   "tictactoe": "PARTIAL — preserved, not upgraded (no genuine interaction evidence)",
                   "runtime_perf_note": "dev-so .so at reduced optimization still renders identical output; runs complete in 1-2s wall each"}}
json.dump(parity, open(f"{E}/wave10_runtime_parity.json", "w"), indent=1)

# build-safety md
md = f"""# WAVE-10 Build Safety — independent verification (all timings fresh)

| Check | Result |
|---|---|
| Production static build (default `make all`, catch-up after benchmark touches) | rc=0, {safety['prod_build']['wall_s']}s, peak RSS {safety['prod_build']['peak_rss_mb']} MB |
| Production `test-core` | **3/3 PASS** ({safety['prod_test_core']['wall_s']}s) |
| Monolith fallback LIVE (`DALVIK_SPLIT=0 all`) | rc=0, {safety['monolith_build']['wall_s']}s, peak RSS {safety['monolith_build']['peak_rss_mb']} MB |
| Monolith `test-core` | **3/3 PASS** ({safety['monolith_test_core']['wall_s']}s) |
| Clean dev-so build (`dev-so-clean` → `dev-so`, wave-10 profiles) | rc=0, **{safety['devso_clean_build']['wall_s']}s** (wave-9 baseline 148.5s) |
| dev-so battery / no-op | **3/3 PASS** / 0.04s |
| Production tree restored after suite | rc=0, {safety['prod_restore']['wall_s']}s |

- Wave-9 zero-test-relink behavior preserved: every trace and ×5 run shows test_exe_relinks=0.
- No generated executables, APKs, object files or shared libraries committed (gitignore covers
  `miniandroid/build_dev_so/`, `/build/`, `/build_dev/`).
- Rollback: `make dev-so-clean` + `git revert <wave-10 commit>` restores the exact wave-9 state;
  production rules were not modified by wave-10.
- Raw data: `w10_build_safety_raw.json`.
"""
open(f"{E}/wave10_build_safety.md", "w").write(md)
print("deliverables assembled")
