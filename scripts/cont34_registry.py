#!/usr/bin/env python3
# cont34_registry.py — add F-NEW-293 to root_registry.json (601 -> 602),
# dedup-checked.
import json

REG = "/home/z/my-project/root_registry.json"
with open(REG) as f:
    r = json.load(f)

ids = [x.get("id") for x in r["roots"]]
assert "F-NEW-293" not in ids, "F-NEW-293 already present — dedup check failed"
assert ids[-1] == "F-NEW-292", f"unexpected tail: {ids[-1]}"

e293 = {
    "id": "F-NEW-293",
    "status": "ROOT_CAUSED_FIXED",
    "title": "GATE A REVERSE-MAPPING ANCHOR GAP: logical_android_path compared an ABSOLUTE host "
             "path against prefixes built from the DEFAULT RELATIVE app-data root literal "
             "('runtime/data' — M3 FINDING-012 back-compat; set_app_data_root absolutizes only on an "
             "explicit override), so the mapping silently no-oped and every Context dir getter minted "
             "its File with the HOST spelling 'runtime/data/data/data/<pkg>/files'. The app-visible "
             "namespace law (AOSP ContextImpl: the application NEVER sees a host path) was violated "
             "for the entire dir-getter family whenever --data-root was not passed, and each "
             "downstream consumer re-anchored the relative host spelling by its OWN law — "
             "resolve_android_path under package_data_dir(), getAbsolutePath/getAbsoluteFile (R-NEW-390) "
             "under app_data_root() — multiplying the prefix (runtime/data/data/data/<pkg>/runtime/"
             "data/… DataStore ENOENT face; three different anchors for one logical file).",
    "priority": "P1",
    "layer": "storage/data-root-gate-a",
    "root_cause": "FIRST DIVERGENCE PROVEN AT RUNTIME (2026-10-10, run/cont34: probe fnew293 PRE x3 on "
                  "binary 859557953a3b144c == the CONT-33 record; composeStopwatch v1.9.1 vc1009011 "
                  "sha256 dbf937ebbe7c0b3d baseline reproduced 9afb2bd2606f303e x3 with the mangled "
                  "DataStore faces x10/run): fnew293 rows DIR-FILES-LOGICAL/DIR-CACHE-LOGICAL answered "
                  "the DOUBLE prefix runtime/data/data/data/<pkg>/runtime/data/data/data/<pkg>/files "
                  "(host leak at the getter + R-NEW-390 re-anchor), FILE-JOIN-LOGICAL answered the "
                  "SINGLE host prefix on the DataStore join shape, NO-HOST-LEAK leak=true. Decode: "
                  "data_root.cpp map_prefix matched h=fs::absolute(host_path) against "
                  "fs::path(g_app_data_root)/… where the root stays the RELATIVE literal when neither "
                  "--data-root nor MINIANDROID_DATA_ROOT is set (main.cpp:914 applies the override "
                  "only when present). ART law: the app-visible spelling is the AOSP logical one "
                  "(/data/user/0/<pkg>/files, alias /data/data/<pkg>/files); the physical mapping "
                  "happens inside resolve_android_path at open time.",
    "fix": "ONE semantic root in logical_android_path (data_root.cpp): canonicalize the ANCHOR exactly "
           "like the host side — fs::absolute(g_app_data_root) before building the prefix table (both "
           "sides of the comparison resolve against the SAME process anchor, the CWD the relative root "
           "already resolves against at every use). No name dispatch, no per-app branches; covers the "
           "whole dir-getter family through the two GATE A call sites (get_or_create_dir_file + "
           "getFileStreamPath). Probe fixtures/fnew293_probe (real aapt2/ECJ/D8): DIR-FILES-LOGICAL/"
           "DIR-CACHE-LOGICAL = the app-visible namespace law; FILE-JOIN-LOGICAL = the exact DataStore "
           "join shape; RT-CREATE-EXISTS (delete-then-create, deterministic across runs) + RT-WRITE-READ "
           "(write → fresh-File read-back same bytes) = the filesDir round-trip; DS-DIR-MKDIRS = the "
           "datastore/ dir law across two independently minted Files; NO-HOST-LEAK = the explicit leak "
           "guard. PRE x3 on 859557953a3b144c: SUMMARY FAIL (3 pass, 4 fail; created=true only on the "
           "fresh store, honestly recorded). POST x3 on 702813ff2d5d8be8: SUMMARY PASS 7/0 with "
           "/data/data/<pkg>/files spellings. Target x3: every app-visible path logical, the mangled "
           "faces 10→0/run (the one remaining ENOENT is the FIRST-RUN DataStore read — faithful: the "
           "file does not exist until the app writes it), frame UNCHANGED 9afb2bd2606f303e x3 "
           "(zero-render-drift fix; physical backings for host-side consumers untouched).",
    "evidence": "evidence/cont34/VIRTUAL_PATH_FRONTIER.md; run/cont34/f293_pre_r1..4, f293_post_r1..3, "
                "csw_base_r1..3, csw_post_r1..3, regression/",
}

r["roots"].append(e293)

if "status_counts" in r:
    sc = r["status_counts"]
    sc["ROOT_CAUSED_FIXED"] = sc.get("ROOT_CAUSED_FIXED", 0) + 1

with open(REG, "w") as f:
    json.dump(r, f, indent=1, ensure_ascii=False)
print("registry now", len(r["roots"]), "roots (601 -> 602)")
