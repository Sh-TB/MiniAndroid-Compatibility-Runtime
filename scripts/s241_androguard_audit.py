#!/usr/bin/env python3
"""#570 external-tool lane, S241: androguard 4.1.4 — the INDEPENDENT DEX
audit of the corpus APKs (the L0 cross-check the issue asked for)."""
import json, sys
from androguard.core.apk import APK

OUT = {}
APKS = {
    "a2048": "/tmp/a2048_test.apk",
    "opensudoku": "/home/z/my-project/upload/opensudoku_v4113.apk",
    "opensudoku_fdroid": None,
}
try:
    APKS["opensudoku_fdroid"] = None  # the F-Droid pin may be absent this round
except Exception:
    pass

for name, path in APKS.items():
    if not path:
        continue
    try:
        a = APK(path)
        entry = {
            "package": a.get_package(),
            "version_code": a.get_androidversion_code(),
            "min_sdk": a.get_min_sdk_version(),
            "target_sdk": a.get_target_sdk_version(),
            "activities": len(a.get_activities()),
            "services": len(a.get_services()),
            "permissions": len(a.get_permissions()),
            "is_valid_apk": a.is_valid_APK(),
        }
        # native libs (the abis cross-check vs the runtime preflight)
        entry["native_libs"] = sorted(set(
            l.split("/")[1] for l in a.get_files()
            if l.startswith("lib/") and l.endswith(".so")))[:6]
        OUT[name] = entry
    except Exception as e:
        OUT[name] = {"error": str(e)[:120]}

json.dump(OUT, open("/home/z/my-project/w_s241_androguard.json", "w"), indent=1)
for k, v in OUT.items():
    print(k, "->", json.dumps(v)[:180])
