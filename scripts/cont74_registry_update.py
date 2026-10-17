#!/usr/bin/env python3
"""CONT-74 registry update — issue #364 FOUNDATION-7 residual.

Changes (no id collisions, metadata recomputed):
  F-NEW-377  (NEW, ROOT-CAUSED-FIXED, P1) tail-join path containment on the
             /storage/emulated/0 and /system/fonts branches — the two
             tail-join branches F-NEW-375's fence did not cover.
             Runtime-proven escape (c74esc probe read its own sandbox bytes
             back through /storage/emulated/0/../../../data/data/<self>/
             files/own.txt), fixed by reusing path_contained at both
             branches; 3/3 post-fix probe runs all DENIED with the volume
             positive control intact; c72priv fence 13/13 unchanged;
             negatives 19/19, reinstall 8/8, goldens 4/4, wall rows
             dooz/opencalc/unote 9/9 MATCH at binary 2b3bf0bab3770c50.
"""
import json
from collections import Counter

PATH = "/home/z/my-project/root_registry.json"
r = json.load(open(PATH))
roots = r["roots"]
by_id = {x["id"]: x for x in roots}
assert len(by_id) == len(roots), "duplicate ids in registry"
assert "F-NEW-377" not in by_id, "F-NEW-377 already registered"

roots.append({
    "id": "F-NEW-377",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": (
        "PATH CONTAINMENT MISSING ON THE VOLUME + SYSTEM-FONT TAIL-JOIN "
        "BRANCHES (issue #364 FOUNDATION-7 residual, F-NEW-375's fence did "
        "not cover them) — FIXED by the tail-join containment law: both "
        "branches now run the F-NEW-375 path_contained fence on the joined "
        "host path against their backing directory. Runtime-proven escape "
        "before the fix: the c74esc probe read its own sandbox bytes back "
        "through /storage/emulated/0/../../../data/data/<self>/files/own.txt "
        "(three .. exit the volume backing because it EXISTS — reachable "
        "today, not theoretical); the /system/fonts spelling was "
        "resolve-ALLOWED but IO-unreachable only while <store>/system is "
        "absent (the virtual system image must not turn that into a live "
        "escape)."
    ),
    "layer": "storage path resolver (miniandroid/src/storage/data_root.cpp "
             "resolve_android_path: VIRTUAL_EXTERNAL + SYSTEM_IMAGE branches)",
    "root_cause": (
        "F-NEW-375 (CONT-72) fenced four of the six risky branches named by "
        "FOUNDATION 3/7: relative-.. (lexical containment), /data/data, "
        "/data/user, /data/user_de (caller identity), and the volume "
        "SIBLING-PREFIX boundary (0evil). The two remaining tail-join "
        "branches joined a caller-controlled tail under a backing directory "
        "with NO containment check: (a) volume: host = backing + rest where "
        "rest may contain ../ sequences — the backing directory EXISTS from "
        "boot, so a three-.. tail (/storage/emulated/0/../../../data/data/"
        "<any-pkg>/files/x) resolves OUTSIDE the app namespace and READS "
        "another package's private bytes (c74esc: own marker read back, "
        "len=13, rc=0, no PATH-LAW DENY line = resolve layer allowed it); "
        "(b) font: host = <root>/system/fonts/<tail> with allowed=true — "
        "currently IO-unreachable only because <store>/system does not "
        "exist (POSIX resolves .. component-wise and dies at the missing "
        "component), so the fence had to land BEFORE the virtual system "
        "image turns the spelling into a live escape."
    ),
    "fix": (
        "data_root.cpp: (a) VIRTUAL_EXTERNAL branch — vol_host containment "
        "check path_contained(backing, vol_host) before allowed=true; "
        "(b) SYSTEM_IMAGE branch — font_host containment check "
        "path_contained(font_base, font_host) before allowed=true. Same "
        "helper, same law family as F-NEW-375 (no new concept). DENIED "
        "spellings surface the canonical AOSP FileNotFoundException face "
        "via the existing PATH-LAW path."
    ),
    "evidence": (
        "CONT-74 (issue #364): probe fixtures/cont74_escape_probe "
        "(com.probe.c74esc, self-contained marker round-trip). PRE-FIX at "
        "binary 1ecb1949e5fa59cf: VOL-ESC LEAK len=13 + VOL-ESC2 LEAK "
        "len=13 (read own C74-OWN-BYTES back through three-.. spellings, "
        "no PATH-LAW DENY). POST-FIX at binary 2b3bf0bab3770c50 x3: all "
        "rows DENIED (PATH-LAW DENIED lines present for all four escape/"
        "negative spellings), volume positive control VOL-OK round-trip "
        "intact, /etc/passwd negative intact. Regression: c72priv fence "
        "13/13 OK (F-NEW-375 behavior unchanged), negatives 19/19, "
        "reinstall 8/8, goldens 4/4, wall rows dooz 31ddd4d5b8e6d18e x3 + "
        "opencalc f25b754c4565c38b x3 + unote 90a67cc1ddda57b7 x3 = 9/9 "
        "MATCH zero drift, s82 validator PASS."
    ),
    "fanout": (
        "ANY app using File IO on the virtual external volume with a "
        "caller-influenced tail; the whole cross-package isolation story "
        "(the same law family as F-NEW-375). 2 branches, 1 helper, "
        "resolver-wide coverage now complete for every tail-join shape."
    ),
    "upstream_source": (
        "AOSP frameworks/base core/java/android/os/Environment + "
        "ContextImpl (external volume canonicalization); "
        "developer.android.com/privacy-and-security/risks/path-traversal; "
        "JLS/POSIX path-resolution semantics (.. is component-wise)."
    ),
})

r["summary"]["total_roots"] = len(roots)
r["summary"]["total"] = len(roots)
by_status = Counter(x["status"] for x in roots)
r["summary"]["by_status"] = dict(by_status)
open_ids = [x["id"] for x in roots if x["status"] not in (
    "ROOT-CAUSED-FIXED", "SUPERSEDED-BY-EVIDENCE", "CLOSED", "NOT_APPLICABLE",
    "REJECTED", "FIXED")]
r["summary"]["open_frontiers"] = open_ids
r["summary"]["last_updated"] = (
    "CONT-74: F-NEW-377 ROOT-CAUSED-FIXED (tail-join path containment on "
    "the volume + system-font branches — the FOUNDATION-7 residual F-NEW-375 "
    "did not cover). Runtime-proven escape (c74esc three-.. volume read of "
    "own sandbox bytes, len=13) closed by the same path_contained law; "
    "post-fix probe x3 all DENIED with volume positive control intact; "
    "c72priv fence 13/13, negatives 19/19, reinstall 8/8, goldens 4/4, wall "
    "9/9 MATCH (dooz/opencalc/unote) at binary 2b3bf0bab3770c50. Registry "
    "682→683."
)

json.dump(r, open(PATH, "w"), indent=1, ensure_ascii=False)
print("registry updated: 682 ->", len(roots))
print("F-NEW-377 registered ROOT-CAUSED-FIXED P1")

# mirror to canonical
cp = "/home/z/my-project/canonical/root_cause_registry.json"
import shutil
shutil.copyfile(PATH, cp)
print("mirrored to", cp)
