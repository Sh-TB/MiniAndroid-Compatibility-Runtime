#!/usr/bin/env python3
"""s100_apk_profile.py — Per-APK capability profile foundation (S98 §14/§27,
S100 §21). Static analysis ONLY (honest): scans the APK's DEX files for
framework type descriptors and maps them to capabilities through
docs/CAPABILITY_REGISTRY.json's api_prefixes; the closure is the transitive
dependency set. Static references are NEVER claimed as runtime usage —
observed capabilities are only recorded when supplied via --observed.

Usage:
  python3 tools/s100_apk_profile.py APK [APK...] --out docs/S100_APK_PROFILES.json
  python3 tools/s100_apk_profile.py APK --observed graphics.basic,framework.input
"""
import json
import os
import re
import sys
import zipfile
import hashlib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(REPO, "docs", "CAPABILITY_REGISTRY.json")

DESC_RE = re.compile(rb"L[a-zA-Z0-9_/$-]+;")


def load_registry():
    with open(REG) as f:
        return json.load(f)


def dex_descriptors(apk_path):
    descs = set()
    with zipfile.ZipFile(apk_path) as z:
        for name in z.namelist():
            if name.startswith("classes") and name.endswith(".dex"):
                data = z.read(name)
                for m in DESC_RE.finditer(data):
                    try:
                        descs.add(m.group(0).decode())
                    except UnicodeDecodeError:
                        pass
    return descs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_path = None
    observed_arg = None
    argv = sys.argv[1:]
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]
    if "--observed" in argv:
        observed_arg = argv[argv.index("--observed") + 1]

    reg = load_registry()
    caps = {c["id"]: c for c in reg["capabilities"]}
    # provides-alias: a capability's provides[] names sub-facilities owned by
    # that same capability (e.g. network.http provides network.tls) — resolve
    # requires targets through them so the closure walks the real graph.
    provides_owner = {}
    for cid, c in caps.items():
        for p in c.get("provides", []):
            provides_owner[p] = cid

    profiles = []
    for apk in args:
        if not os.path.exists(apk):
            print(f"SKIP missing {apk}")
            continue
        descs = dex_descriptors(apk)
        static_caps = set()
        evidence_refs = {}
        for cid, c in caps.items():
            for prefix in c.get("api_prefixes", []):
                hits = [d for d in descs if d.startswith(prefix)]
                if hits:
                    static_caps.add(cid)
                    evidence_refs[cid] = len(hits)
        # transitive closure
        closure = set()
        frontier = list(static_caps)
        while frontier:
            cid = frontier.pop()
            if cid in closure:
                continue
            closure.add(cid)
            for req in caps[cid].get("requires", []):
                owner = provides_owner.get(req, req)
                if owner not in closure:
                    frontier.append(owner)
        observed = set()
        if observed_arg:
            observed = set(observed_arg.split(","))
        profiles.append({
            "apk": os.path.basename(apk),
            "apk_sha256_16": hashlib.sha256(open(apk, "rb").read()).hexdigest()[:16],
            "apk_bytes": os.path.getsize(apk),
            "dex_type_descriptors": len(descs),
            "static_capabilities": sorted(static_caps),
            "static_api_ref_counts": evidence_refs,
            "resolved_closure": sorted(closure),
            "observed_capabilities": sorted(observed) if observed else
                "not recorded this run (static != observed — S98 §14 law)",
            "cold_capabilities_avoided": sorted(
                cid for cid in static_caps if not caps[cid]["hot"]),
        })
        print(f"PROFILED {os.path.basename(apk)}: "
              f"static={len(static_caps)} closure={len(closure)} "
              f"cold={len([c for c in static_caps if not caps[c]['hot']])}")

    if out_path and profiles:
        with open(out_path, "w") as f:
            json.dump({"schema": "miniandroid.apk.profile/1.0",
                       "law": "static != observed; closure = transitive deps",
                       "profiles": profiles}, f, indent=2)
        print("WROTE", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
