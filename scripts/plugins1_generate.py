#!/usr/bin/env python3
"""PLUGINS-1 generator: standard per-app triage registry (plugins/apps.jsonl).

User law: any agent/human must onboard with MINIMAL tokens/time and know
exactly (a) where the problem is, (b) why it did not run, (c) what to do next.
One line per app in apps.jsonl; grep the id -> whole diagnosis.
Data source: canonical/app_registry.json + canonical/game_registry.json
(single canonical location — no parallel copies, per #386).
"""
import json, hashlib, subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CP_NAMES = {
    "L0": "APK accepted", "L1": "runtime executes", "L2": "lifecycle",
    "L3": "view tree", "L4": "rendering", "L5": "input",
    "L6": "state changes", "L7": "multi-feature interaction",
}

def gate_nx(cp):
    gate, nx = None, None
    for k in sorted(CP_NAMES):
        if cp.get(k):
            gate = k
        elif nx is None:
            nx = k
    return gate or "L0", nx

def next_action(status, nx, note):
    if nx:
        return "advance %s (%s)" % (nx, CP_NAMES[nx])
    if status == "VERIFIED":
        return "hold golden wall; regression-watch"
    if status == "BLOCKED":
        return "unblock per note"
    return "probe per note"

def emit_line(rec, fam):
    gate, nx = gate_nx(rec.get("checkpoints", {}))
    note = (rec.get("note") or "").strip()
    if len(note) > 260:
        note = note[:257] + "..."
    refs = rec.get("evidence_refs") or []
    out = {
        "i": rec.get("id"), "t": rec.get("title"), "pkg": rec.get("package"),
        "fam": fam, "load": rec.get("status"), "gate": gate, "nx": nx,
        "n": note, "ev": refs[0] if refs else "", "next": next_action(rec.get("status"), nx, note),
    }
    return out

def main():
    apps = json.load(open("canonical/app_registry.json"))
    games = json.load(open("canonical/game_registry.json"))
    lines = [emit_line(r, "app") for r in apps["apps"]] + \
            [emit_line(r, "game") for r in games["games"]]

    os.makedirs("plugins", exist_ok=True)
    with open("plugins/apps.jsonl", "w", encoding="utf-8") as f:
        for rec in lines:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=False) + "\n")

    from collections import Counter
    by_load = Counter(r["load"] for r in lines)
    by_nx = Counter(r["nx"] for r in lines if r["nx"])
    index = {
        "schema": "miniandroid.plugins.v1",
        "onboarding": ["1) grep 'id' plugins/apps.jsonl -> one line = whole diagnosis",
                       "2) nx field = WHERE it is stuck (checkpoint law in _schema)",
                       "3) next field = WHAT to do; n field = WHY (evidence-backed note)"],
        "generated_from": ["canonical/app_registry.json", "canonical/game_registry.json"],
        "registered": len(lines),
        "corpus_total": 202,
        "registration_gap": 202 - len(lines),
        "by_load": dict(by_load),
        "stuck_at": dict(by_nx),
        "raw_logs": "NOT_STORED_IN_GIT",
        "artifact_manifest": "plugins/_artifacts_manifest.json",
    }
    json.dump(index, open("plugins/_index.json", "w"), ensure_ascii=False, indent=1)

    schema = {
        "$schema": "miniandroid.plugins.v1",
        "checkpoint_law": json.load(open("canonical/app_registry.json"))["checkpoint_law"],
        "checkpoint_names": CP_NAMES,
        "status_vocabulary": apps.get("status_vocabulary", []),
        "fields": {
            "i": "app/game id (canonical registry id)",
            "t": "title", "pkg": "android package",
            "fam": "app | game",
            "load": "status from canonical registry vocabulary",
            "gate": "highest passing checkpoint (WHERE it got)",
            "nx": "first failing checkpoint (WHERE exactly the problem is)",
            "n": "evidence-backed note: WHY it fails / what was observed",
            "ev": "evidence pointer (paths/issues) — raw logs are NEVER in git",
            "next": "WHAT to do next (derived from nx + status)",
        },
        "laws": [
            "one line per app — grep-able, token-minimal onboarding",
            "raw logs and APKs are NEVER committed (see .gitignore + #386)",
            "canonical data stays in canonical/ — this is the triage projection",
            "every claim must carry an evidence pointer",
        ],
    }
    json.dump(schema, open("plugins/_schema.plugin.json", "w"), ensure_ascii=False, indent=1)

    # artifacts manifest for the dirty files being untracked
    dirty = ["1", "gate_a_probe.apk", "run/c116_tg_aput.log", "run/c116_tg_fna.log",
             "run/c116_tg_s36.log", "run/c152/dooz_gh_trace.log", "run/c155/t2_oz0a.log",
             "run/c154/c154_applogs.tar.gz", "run/c156/canon/forkgram.log",
             "run/s88/corpus/profiles.json", "run/cont105/tg_pre.log"]
    kinds = {"1": "raw-log-dump", "gate_a_probe.apk": "apk-binary"}
    man = []
    for p in dirty:
        if not os.path.exists(p):
            continue
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        kind = kinds.get(p, "apk-binary" if p.endswith(".apk") else "raw-log-dump")
        man.append({"file": p, "bytes": os.path.getsize(p), "sha256": h.hexdigest(),
                    "kind": kind,
                    "reason": "violates .gitignore law (*.apk, /run/ external-artifacts, *.log) — #386"})
    for apk in subprocess.check_output(
            ["git", "ls-files"], text=True).splitlines():
        if apk.endswith(".apk") and apk != "gate_a_probe.apk" and apk not in dirty:
            man.append({"file": apk, "bytes": os.path.getsize(apk),
                        "sha256": hashlib.sha256(open(apk, "rb").read()).hexdigest(),
                        "kind": "apk-binary",
                        "reason": "violates ZERO-APK law — #386; rebuild via fixture scripts"})
    json.dump({"schema": "miniandroid.artifacts.v1", "policy":
               "physical copies preserved offline; regenerate via provenance recipes; NEVER re-commit",
               "artifacts": man},
              open("plugins/_artifacts_manifest.json", "w"), ensure_ascii=False, indent=1)

    print("apps.jsonl lines:", len(lines))
    print("by_load:", dict(by_load))
    print("stuck_at:", dict(by_nx))
    print("artifacts untracked:", len(man),
          "total MB: %.1f" % (sum(m["bytes"] for m in man) / 1e6))

if __name__ == "__main__":
    main()
