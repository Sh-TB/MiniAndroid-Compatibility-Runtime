#!/usr/bin/env python3
"""F-NEW-231: flip REGISTERED -> IMPLEMENTED+TESTED with the proof summary."""
import json, sys

REG = "/home/z/my-project/root_registry.json"

PROOF = (
    "PROOF 2026-10-02 (scripts/f231_proof.sh; evidence/f231_installed_access/): "
    "APP opencalculator_53 (sha 2642613868a8a80f...) + GAME bouncy/canonical_apks "
    "(sha ffda0d9cb0b1b2aa...). Chain per APK: install SUCCESS -> identity-only "
    "discovery (list-packages) -> analyze on INSTALLED base.apk (package/version/"
    "MainActivity correct) -> dex on INSTALLED base.apk (app 8593 strings/1495 "
    "classes; game 15414 strings/1347 classes) -> ORIGINAL APK MOVED AWAY -> "
    "run --package x3: opencalc e364b001ee7abd66 x3 rc=000 (matches the F-NEW-228 "
    "golden; 297 colors, 64.7% button field + 34.5% display = REAL_APP_CONTENT); "
    "bouncy b6dde6074bf47264 x3 (145 colors pinball palette = real game content; "
    "rc=111 PARTIAL end-of-run exception, identical face on the sideload path — "
    "not an installed-mode regression). Provenance: lifecycle_trace \"apk\" = "
    "<store>/data/app/<pkg>/base.apk in every run (runtime operated on the "
    "INSTALLED representation, sideload path hidden). Integrity: installed "
    "base.apk sha == package.json apkSha256 == source sha. Ten platform claims "
    "all PASS (install-success/state-created/deterministic-mapping/agent-"
    "discoverable/agent-readable/no-Android-OS/no-root/environment-provided/"
    "reusable/second-APK-retested)."
)

TEN_CLAIMS = {
    "install_success": "PASS (2/2 APKs)",
    "installed_state_created": "PASS (base.apk + package.json + /data/data dirs)",
    "deterministic_mapping": "PASS (data/app/<pkg>/base.apk)",
    "agent_discovery": "PASS (list-packages JSON from data-root)",
    "agent_readable_inspection": "PASS (analyze+dex on installed base.apk)",
    "no_full_android_os": "PASS (pure runtime, no device/emulator)",
    "no_root_required": "PASS (user-owned store)",
    "environment_provided": "PASS (install/list-packages/run --package built-in)",
    "reusable": "PASS (generic package store, any APK)",
    "second_apk_retest": "PASS (game bouncy after app opencalc)",
}


def main():
    with open(REG) as f:
        reg = json.load(f)
    for r in reg["roots"]:
        if r["id"] == "F-NEW-231":
            r["status"] = "IMPLEMENTED+TESTED"
            r["evidence"] = r["evidence"] + " | " + PROOF
            r["ten_claims"] = TEN_CLAIMS
            break
    else:
        print("F-NEW-231 not found"); return 1
    reg["status_counts"] = {}
    for r in reg["roots"]:
        reg["status_counts"][r.get("status", "?")] = (
            reg["status_counts"].get(r.get("status", "?"), 0) + 1)
    with open(REG, "w") as f:
        json.dump(reg, f, indent=1)
    print("F-NEW-231 -> IMPLEMENTED+TESTED; roots:", reg["count"])


if __name__ == "__main__":
    sys.exit(main())
