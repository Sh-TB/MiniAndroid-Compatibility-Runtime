#!/usr/bin/env python3
"""CONT-18 T-01 (PHASE 0): collect static baseline facts — no engine changes.

Records: HEAD SHA, binary SHA, source-tree sha256 (git HEAD tree), registry
SHA + counts, APK SHAs for every validation target, toolchain versions.
Writes evidence/cont18/t01_static_facts.json
"""
import hashlib, json, subprocess, os, time

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"
OUT = f"{BASE}/evidence/cont18/t01_static_facts.json"


def sha256_16(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def git(*args):
    return subprocess.run(["git", "-C", BASE, *args], capture_output=True,
                          text=True).stdout.strip()


def main():
    facts = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    facts["git_head"] = git("rev-parse", "HEAD")
    facts["git_head_short"] = git("rev-parse", "--short=8", "HEAD")
    facts["git_tree"] = git("rev-parse", "HEAD^{tree}")
    facts["git_uncommitted"] = subprocess.run(
        ["git", "-C", BASE, "status", "--porcelain"],
        capture_output=True, text=True).stdout.strip()
    facts["git_unpushed"] = git("log", "origin/main..HEAD", "--oneline")
    facts["git_remote"] = git("remote", "get-url", "origin")

    facts["binary_sha16"] = sha256_16(BIN)
    facts["binary_path"] = BIN
    facts["binary_size"] = os.path.getsize(BIN) if os.path.exists(BIN) else None

    # CONT-18 brief states CONT-17 binary = e752b6d9c669558a; repo records say
    # a8761a482a186eac (= CONT-16 recorded SHA). Record the discrepancy.
    facts["brief_stated_cont17_binary"] = "e752b6d9c669558a"
    facts["brief_stated_sha_found_in_repo"] = False
    facts["recorded_cont17_binary"] = "a8761a482a186eac"
    facts["binary_matches_recorded_cont17"] = (
        facts["binary_sha16"] == facts["recorded_cont17_binary"])

    reg_path = f"{BASE}/root_registry.json"
    facts["registry_sha16"] = sha256_16(reg_path)
    try:
        reg = json.load(open(reg_path))
        facts["registry_total"] = reg.get("total")
        facts["registry_total_roots"] = reg.get("total_roots")
        facts["registry_status_counts"] = reg.get("status_counts")
    except Exception as e:
        facts["registry_error"] = str(e)

    apks = {
        "dooz": f"{BASE}/upload/canonical_apks/dooz_23_toplevel.apk",
        "microtimer": f"{BASE}/upload/canonical_apks/dubrowgn.microtimer_8.apk",
        "unote": f"{BASE}/upload/canonical_apks/app.varlorg.unote_30.apk",
        "gmdice": f"{BASE}/upload/canonical_apks/de.duenndns.gmdice_8.apk",
        "opencalc": f"{BASE}/upload/opencalculator_53.apk",
        "chess": f"{BASE}/upload/chess_jwtc_298.apk",
        "telegram": f"{BASE}/upload/telegram_official.apk",
        "f266_probe": f"{BASE}/run/w8/f266.apk",
        "f259_probe": f"{BASE}/run/w7/f259.apk",
        "f259g_probe": f"{BASE}/run/w7/f259g.apk",
        "fcol_probe": f"{BASE}/run/w7/fcol.apk",
        "f084_probe": f"{BASE}/run/w7/f084.apk",
    }
    facts["apk_shas"] = {k: sha256_16(v) for k, v in apks.items()}
    facts["apk_paths"] = apks

    # probe APK paths that may live elsewhere (f084)
    if facts["apk_shas"]["f084_probe"] is None:
        for cand in [f"{BASE}/fixtures/f084_loop_probe/apk/f084_loop.apk",
                     f"{BASE}/fixtures/f084_loop_probe/f084.apk"]:
            if os.path.exists(cand):
                facts["apk_shas"]["f084_probe"] = sha256_16(cand)
                facts["apk_paths"]["f084_probe"] = cand
                break
    found084 = facts["apk_shas"]["f084_probe"] is not None
    if not found084:
        hits = subprocess.run(["bash", "-c",
            f"ls {BASE}/fixtures/f084_loop_probe/"], capture_output=True,
            text=True).stdout
        facts["f084_dir_listing"] = hits.strip()

    for tool in ["clang++", "make", "python3"]:
        try:
            v = subprocess.run([tool, "--version"], capture_output=True,
                               text=True).stdout.splitlines()[0]
            facts[f"toolchain_{tool}"] = v
        except Exception:
            facts[f"toolchain_{tool}"] = "NOT FOUND"

    facts["command_lines"] = {
        "run": f"{BIN} run --package <pkg> --data-root <store> --trace --max-seconds 120 --frames 40 -o <outdir>",
        "probes": "python3 scripts/cont16_probe_run.py run/cont18/probes f266 f259 f259g fcol",
        "anchors": "bash scripts/cont18_anchors.sh",
        "negatives": "python3 scripts/s41_gatea_negative.py",
        "skill": "python3 scripts/skill_selftest.py",
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(facts, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(json.dumps({k: facts[k] for k in [
        "git_head_short", "binary_sha16",
        "binary_matches_recorded_cont17", "registry_total",
        "registry_sha16"]}, indent=2))
    print("apk_shas:", json.dumps(facts["apk_shas"], indent=2))
    print("uncommitted:", repr(facts["git_uncommitted"][:200]))
    print("unpushed:", repr(facts["git_unpushed"][:100]))


if __name__ == "__main__":
    main()
