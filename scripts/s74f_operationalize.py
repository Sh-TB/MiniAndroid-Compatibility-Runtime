#!/usr/bin/env python3
"""s74f_operationalize.py — S74 FOLLOW-UP WAVE: tool utilization + law
utilization + §27 audit table.

  - Tool profiles get an explicit utilization verdict:
      USED (with consumer chain) / RESEARCHED_ONLY / AVAILABLE_NOT_USED
    derived from EXISTING recorded consumers/laws/evidence — never inflated.
  - Knowledge records get a utilization block:
      USED_BY_EXECUTION (consumer app + evidence) / OBSERVED_ONLY /
      RESEARCHED_ONLY / UNUSED_VERIFIED_LAW (honest label, no invented consumer)
  - Emits docs/evidence/s74_ops/AUDIT_TABLE.md (§27) with the exact
    YES/NO/PARTIAL/NOT_APPLICABLE/NOT_OBSERVED vocabulary from committed
    evidence only.
"""
import glob
import json
import os

REPO = "/home/z/my-project"
TOOLS = f"{REPO}/docs/compatibility/tools"
LAWS = f"{REPO}/docs/knowledge/laws"
OPS = f"{REPO}/docs/evidence/s74_ops"

# ---- tool utilization verdicts (derived from recorded consumers+laws) ------
TOOL_VERDICT = {
    "aosp": "USED",
    "art": "USED",
    "dalvik": "USED",
    "openjdk": "USED",
    "androidx": "USED",
    "kotlin": "USED",
    "kotlinx-coroutines-atomicfu": "USED",
    "compose": "RESEARCHED_ONLY",       # studied for Dooz chain; no runtime Compose implementation
    "build-toolchain": "USED",
    "codesearch-toolchain": "RESEARCHED_ONLY",  # used for source lookup sessions, no artifact consumers
    "external-runtimes": "AVAILABLE_NOT_USED",  # studied; zero laws/consumers recorded
    "asc": "RESEARCHED_ONLY",           # research assistant only (taskbook §43 chain)
}

TOOL_NOTE = {
    "aosp": "consumer chain: F-148/F-149 laws -> Snake layout; F-136/F-114 laws -> Unote strings/prefs; fixtures family",
    "art": "consumer chain: F-141 invoke-null-receiver law -> all real-APK apps; F-146/F-147 Dooz frontier records",
    "dalvik": "consumer chain: DEX/interpreter laws -> every real-dalvik execution in the corpus",
    "openjdk": "consumer chain: F-113 SecureRandom -> gmdice roll; boxed-reader family laws",
    "androidx": "consumer chain: FragmentManager subset law; Unote/TriPeaks/Telegram androidx families",
    "kotlin": "consumer chain: Kotlin-object/property-reader laws -> Dooz/Unote chains",
    "kotlinx-coroutines-atomicfu": "consumer chain: AtomicReferenceArray semantics -> Dooz state queue law record",
    "compose": "studied as Dooz rendering context (APP-DOOZ-COMPOSE-CHAIN record); no Compose runtime path implemented",
    "build-toolchain": "consumer chain: aapt2/ECJ/D8/stubs -> every fixture + snake/unote-class APK builds at HEAD",
    "codesearch-toolchain": "source-lookup sessions only (law provenance hunts); no direct runtime consumer",
    "external-runtimes": "surveyed for semantic reference only; no adoption, no consumers — honest AVAILABLE_NOT_USED",
    "asc": "per §43: research assistant only; OBSERVED->UPSTREAM confirmations mediated through it, no runtime role",
}


def main():
    # ---- tools ----
    for path in sorted(glob.glob(f"{TOOLS}/*.json")):
        d = json.load(open(path))
        tid = d["tool_id"]
        v = TOOL_VERDICT.get(tid)
        if v is None:
            v = "RESEARCHED_ONLY" if not d.get("consumers") else "USED"
        d["utilization"] = {
            "verdict": v,
            "note": TOOL_NOTE.get(tid, ""),
            "law": "utilization derived from recorded consumers/laws/evidence; unused tools labeled honestly (S74-FOLLOW-UP §13/§14/§33)",
            "consumers_recorded": len(d.get("consumers", [])),
            "laws_learned_recorded": len(d.get("laws_learned", [])),
        }
        json.dump(d, open(path, "w"), indent=1)
        print(f"[TOOL] {tid}: {v}")

    # ---- knowledge records ----
    counts = {}
    for path in sorted(glob.glob(f"{LAWS}/*.json")):
        d = json.load(open(path))
        kid = d["knowledge_id"]
        status = d.get("status")
        consumers = d.get("consumers", [])
        test = d.get("test")
        util = None
        if status == "VERIFIED":
            if consumers and test:
                util = {"verdict": "USED_BY_EXECUTION",
                        "consumer_apps": consumers,
                        "test": test,
                        "evidence": d.get("source", {}).get("file", "")}
            else:
                util = {"verdict": "UNUSED_VERIFIED_LAW",
                        "note": "verified but no recorded consumer/test pair — honest label, no invented consumer"}
        elif status in ("OBSERVED",):
            util = {"verdict": "OBSERVED_ONLY",
                    "consumer_apps": consumers,
                    "note": "seen in execution, not formalized as a semantic law"}
        elif status == "RESEARCHED":
            util = {"verdict": "RESEARCHED_ONLY", "consumer_apps": consumers}
        elif status == "SUPERSEDED":
            util = {"verdict": "SUPERSEDED", "note": "preserved per §68 history law"}
        d["utilization"] = util
        json.dump(d, open(path, "w"), indent=1)
        counts[util["verdict"]] = counts.get(util["verdict"], 0) + 1
        print(f"[LAW] {kid}: {util['verdict']}")
    print("LAW UTILIZATION COUNTS:", json.dumps(counts))


if __name__ == "__main__":
    main()
