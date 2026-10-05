#!/usr/bin/env python3
"""unknown_apk_preflight.py — CONT-3 Phase 2: the operational unknown-APK
preflight gate.

#375 requires an operational gate whose real workflow determines, for an
unknown APK: package identity + APK SHA, min/target SDK, requested
permissions and actual outcomes, native ABI requirements, components,
resource/graphics/media/network/input/storage prerequisites, environment
capability matches/mismatches (docs/ENVIRONMENT_PROFILE.json), install and
launch outcome, the first observed runtime divergence, and whether the case
is an environment prerequisite or a genuine runtime root.

VERDICT CLASSES (the #375 contract + LAW-001):
  ABI_OUT_OF_SCOPE      LAW-001 FIRST TEST LAW: APK's native lib trees contain
                        no x86/x86_64 ABI (ARM32/ARM64/other only) — OUT OF
                        CURRENT SCOPE, SKIP bucket, checked BEFORE install/
                        launch, NEVER counted as a runtime failure
  PREFLIGHT_PASS        every prerequisite matched; launch + frame + no divergence
  ENVIRONMENT_BLOCKED   ABI / SDK / hardware-feature prerequisite the host
                        profile cannot satisfy (proven, honest)
  INSTALL_BLOCKED       install step failed (parse ok, install refused/errored)
  SECURITY_BLOCKED      permission/signature/security contract failure
  IDENTITY_BLOCKED      package identity mismatch / corrupt identity records
  SERVICE_BLOCKED       required service/component missing at runtime
  EXECUTION_BLOCKED     interpreter/engine could not execute (parse-level DEX)
  RESOURCE_BLOCKED      required resource/table entries missing
  GRAPHICS_BLOCKED      graphics prerequisite unmet (GLES/Vulkan version)
  MEDIA_BLOCKED         required codec/media capability absent
  NETWORK_BLOCKED       network prerequisite and no host route
  INPUT_BLOCKED         required input modality unimplemented
  CAPTURE_ONLY          process + frames captured but no app callbacks/state
  RUNTIME_ROOT          first divergence is a genuine runtime root (app throw
                        with caller chain), prerequisites all matched
  UNKNOWN               malformed/unparseable input — nothing provable

Every emission also carries `verdict_class` (PASS | SKIP | FINDING | BLOCKED)
plus `in_current_test_scope` / `counts_as_failure` so statistics can keep the
ABI skip bucket separate from failures (LAW-001b honest statistics).

Machine-readable contract (shared with docs/execution-skill): JSON with the
fields the SKILL.md operations table consumes. The skill runs THE SAME
driver (no separate verdict implementation).

Usage:
  unknown_apk_preflight.py <apk> [--data-root DIR] [--json OUT.json] [--max-seconds S]
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(BASE, "miniandroid", "build", "miniandroid")
ENV_PROFILE = os.path.join(BASE, "docs", "ENVIRONMENT_PROFILE.json")

ALL_VERDICTS = [
    "ABI_OUT_OF_SCOPE",  # LAW-001 FIRST TEST LAW (16-verdict contract, 1.1)
    "PREFLIGHT_PASS", "ENVIRONMENT_BLOCKED", "INSTALL_BLOCKED",
    "SECURITY_BLOCKED", "IDENTITY_BLOCKED", "SERVICE_BLOCKED",
    "EXECUTION_BLOCKED", "RESOURCE_BLOCKED", "GRAPHICS_BLOCKED",
    "MEDIA_BLOCKED", "NETWORK_BLOCKED", "INPUT_BLOCKED", "CAPTURE_ONLY",
    "RUNTIME_ROOT", "UNKNOWN",
]

# LAW-001b honest-statistics buckets: every verdict maps to exactly one
# statistics class; only BLOCKED inflates the could-not-run count.
VERDICT_CLASS = {
    "ABI_OUT_OF_SCOPE": "SKIP",     # out of current ABI scope — never a failure
    "PREFLIGHT_PASS": "PASS",
    "RUNTIME_ROOT": "FINDING",       # genuine runtime root = work item, not env noise
    "CAPTURE_ONLY": "FINDING",
    "UNKNOWN": "FINDING",            # malformed input — nothing provable either way
}
# verdicts not in VERDICT_CLASS are BLOCKED (install/identity/security/service/
# execution/resource/graphics/media/network/input/environment).

# ENV-005 + LAW-001: the host executes x86_64 native code only; pure-DEX APKs
# (no lib/ tree) are ABI-neutral and always in scope.
EXECUTABLE_ABIS = ["x86_64"]
# LAW-001 scope set: an APK whose native trees intersect this set (or that has
# no native trees at all) is IN SCOPE.
IN_SCOPE_NATIVE_ABIS = {"x86", "x86_64"}

# Graphics ceiling from ENV-006 (software PortableGL backend).
SUPPORTED_GLES = 2  # GLES 2.0-class backend; GLES3+ requests degrade honestly


def sha256_16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def run_cli(args, timeout=240):
    try:
        p = subprocess.run([BIN] + args, capture_output=True, text=True,
                           timeout=timeout, cwd=BASE)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"


def parse_manifest(apk_path, text):
    """Pull minSdk/targetSdk/permissions/features/ABIs out of CLI output.
    The analyze CLI emits a JSON report (package_name/min_sdk/target_sdk)."""
    out = {
        "package": None, "min_sdk": None, "target_sdk": None,
        "permissions": [], "features": [], "abis": [],
        "activities": 0, "services": 0, "receivers": 0, "providers": 0,
        "gles_version": None,
    }
    m = re.search(r'"package_name"\s*:\s*"([^"]+)"', text) or \
        re.search(r"package:\s*([A-Za-z0-9._]+)", text)
    if m:
        out["package"] = m.group(1)
    m = re.search(r'"min_sdk"\s*:\s*"?(\d+)', text) or \
        re.search(r"minSdkVersion[=:]\s*(\d+)", text)
    if m:
        out["min_sdk"] = int(m.group(1))
    m = re.search(r'"target_sdk"\s*:\s*"?(\d+)', text) or \
        re.search(r"targetSdkVersion[=:]\s*(\d+)", text)
    if m:
        out["target_sdk"] = int(m.group(1))
    out["permissions"] = sorted(set(re.findall(
        r"(android\.permission\.[A-Z_]+)", text)))
    out["features"] = sorted(set(re.findall(
        r"(android\.hardware\.[a-z0-9_.]+)", text)))
    out["abis"] = sorted(set(re.findall(
        r"(armeabi-v7a|arm64-v8a|x86|x86_64)", text)))
    m = re.search(r"glEsVersion[=:]\s*([\d.]+)", text)
    if m:
        try:
            out["gles_version"] = float(m.group(1))
        except ValueError:
            pass
    out["activities"] = len(re.findall(r"[Aa]ctivity\b", text)) and \
        len(re.findall(r"activity", text)) or 0
    out["services"] = len(re.findall(r"\bservice\b", text))
    out["receivers"] = len(re.findall(r"\breceiver\b", text))
    out["providers"] = len(re.findall(r"\bprovider\b", text))
    return out


def classify(findings):
    """Deterministic verdict mapping — first match wins in blocker order.
    Returns (verdict, blocker_detail).

    LAW-001a: the ABI scope check is the FIRST test law — it preempts every
    other classification whenever the evidence (real lib/ tree entries, or
    declared ABIs when the tree is absent) proves the APK has no x86/x86_64
    native ABI. LAW-001f: it needs real ABI evidence; with zero ABI evidence
    (pure-DEX) the APK is in scope and classification proceeds normally."""
    blocker = findings.get("blocker")
    if findings["parse"] == "FAILED":
        return "UNKNOWN", blocker
    # ── LAW-001 FIRST TEST LAW: ABI scope (preempts all other verdicts) ──
    abi_evidence = findings.get("lib_abis") or findings.get("abis") or []
    if abi_evidence and not (set(abi_evidence) & IN_SCOPE_NATIVE_ABIS):
        return "ABI_OUT_OF_SCOPE", (
            "LAW-001: native ABIs %s contain no host-executable ABI "
            "(x86/x86_64 only; ENV-005, no translation layer) — out of "
            "current test scope, recorded as SKIP not failure" % abi_evidence)
    if findings["install"] == "FAILED":
        # install refuses on identity/integrity — separate the honest cases
        if findings.get("install_reason") == "identity":
            return "IDENTITY_BLOCKED", blocker
        if findings.get("install_reason") == "security":
            return "SECURITY_BLOCKED", blocker
        return "INSTALL_BLOCKED", blocker
    # Environment prerequisites (proven against ENVIRONMENT_PROFILE.json).
    # NOTE: the ABI check itself moved to the LAW-001 scope rule above (it is
    # the FIRST test law and preempts everything); what remains here are the
    # SDK / hardware-feature / graphics prerequisites.
    env = findings.get("env") or {}
    sdk_int = env.get("ENV-001_api_level", {}).get("sdk_int", 34)
    if findings["min_sdk"] is not None and findings["min_sdk"] > sdk_int:
        blocker = (
            "minSdkVersion %d > host API %d (ENV-001)" %
            (findings["min_sdk"], sdk_int))
        return "ENVIRONMENT_BLOCKED", blocker
    for feat in findings["features"]:
        if any(k in feat for k in ("camera", "bluetooth", "telephony",
                                   "nfc", "usb", "fingerprint")):
            hw = env.get("ENV-008_hardware", {})
            if isinstance(hw, dict) and not hw.get(feat, False):
                blocker = (
                    "required feature %s absent from host profile "
                    "(ENV-008)" % feat)
                return "ENVIRONMENT_BLOCKED", blocker
    if findings["gles_version"] and findings["gles_version"] > SUPPORTED_GLES:
        blocker = (
            "requires OpenGL ES %s > host backend class %d (ENV-006)" %
            (findings["gles_version"], SUPPORTED_GLES))
        return "GRAPHICS_BLOCKED", blocker
    # Launch/execution outcomes
    if findings["launch"] == "BUDGET_STOPPED":
        # wall-clock soft budget reached with frames rendered — honest
        # verdict: RUNTIME_ROOT when a divergence WAS recorded (progress
        # with evidence beats a generic capture label); CAPTURE_ONLY when
        # the capture is clean but unproven.
        if findings.get("first_divergence"):
            return "RUNTIME_ROOT", blocker
        return "CAPTURE_ONLY", blocker
    if findings["launch"] == "FAILED":
        if findings.get("launch_stage") == "dex":
            return "EXECUTION_BLOCKED", blocker
        if findings.get("launch_stage") == "resource":
            return "RESOURCE_BLOCKED", blocker
        if findings.get("launch_stage") == "security":
            return "SECURITY_BLOCKED", blocker
        if findings.get("launch_stage") == "service":
            return "SERVICE_BLOCKED", blocker
        return "EXECUTION_BLOCKED", blocker
    if findings["launch"] == "OK":
        if findings.get("first_divergence"):
            # Prerequisites matched + real divergence with caller chain =
            # a genuine runtime root.
            return "RUNTIME_ROOT", blocker
        if findings.get("frames", 0) > 0 and findings.get("callbacks", 0) > 0:
            return "PREFLIGHT_PASS", blocker
        if findings.get("frames", 0) > 0:
            return "CAPTURE_ONLY", blocker
    return "UNKNOWN", blocker


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("apk")
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--max-seconds", type=int, default=120)
    args = ap.parse_args()

    apk = os.path.abspath(args.apk)
    contract = {
        "schema": "MINIANDROID_UNKNOWN_APK_PREFLIGHT/1.1",  # 1.1: +ABI_OUT_OF_SCOPE (LAW-001)
        "apk_path": apk,
        "apk_sha256_16": None,
        "verdict": None,
        "prerequisites": {},
        "environment_matches": {},
        "install": None,
        "launch": None,
        "first_divergence": None,
        "blocker": None,
        "is_environment_prerequisite": None,
        "evidence": {},
    }
    t0 = time.time()
    if not os.path.isfile(apk):
        contract["verdict"] = "UNKNOWN"
        contract["blocker"] = "file not found"
        _emit(contract, args.json)
        return 2
    contract["apk_sha256_16"] = sha256_16(apk)

    # ── 1. parse / identity (analyze) ────────────────────────────────────
    rc, out, err = run_cli(["analyze", apk])
    if rc != 0 or ('"package_name"' not in (out + err) and
                   "package:" not in (out + err)):
        contract["prerequisites"]["parse"] = "FAILED"
        contract["blocker"] = (err or out or "analyze failed")[:400]
        contract["verdict"], contract["blocker"] = classify({
            "parse": "FAILED", "install": None, "launch": None,
            "min_sdk": None, "abis": [], "features": [],
            "gles_version": None, "env": {},
        })
        _emit(contract, args.json)
        return 0
    manifest = parse_manifest(apk, out + err)
    contract["prerequisites"].update(manifest)
    contract["prerequisites"]["parse"] = "OK"

    # ZIP-level structure prerequisites (ABI trees, resources, dex)
    try:
        z = zipfile.ZipFile(apk)
        names = z.namelist()
        contract["prerequisites"]["dex_entries"] = sorted(
            n for n in names if n.endswith(".dex"))
        contract["prerequisites"]["lib_abis"] = sorted({
            n.split("/")[1] for n in names
            if n.startswith("lib/") and len(n.split("/")) > 2})
        contract["prerequisites"]["has_resources_arsc"] = \
            "resources.arsc" in names
    except zipfile.BadZipFile:
        contract["verdict"] = "UNKNOWN"
        contract["blocker"] = "bad zip"
        _emit(contract, args.json)
        return 0

    # ── LAW-001 FIRST TEST LAW: ABI scope gate (BEFORE install/launch) ───
    # The check order law: an APK with native trees and no x86/x86_64 ABI is
    # out of current scope — it never reaches install/launch, and it is
    # recorded as SKIP, never as a runtime failure.
    scope_abis = contract["prerequisites"]["lib_abis"] or manifest["abis"]
    if scope_abis and not (set(scope_abis) & IN_SCOPE_NATIVE_ABIS):
        contract["environment_matches"] = {
            "host_executable_abis": EXECUTABLE_ABIS,
            "apk_abis": scope_abis,
            "abi_scope": "OUT_OF_SCOPE (LAW-001)",
        }
        contract["verdict"] = "ABI_OUT_OF_SCOPE"
        contract["blocker"] = (
            "LAW-001 FIRST TEST LAW: native ABIs %s contain no "
            "host-executable ABI (x86/x86_64 only; ENV-005, no translation "
            "layer) — out of current test scope, SKIP not failure" % scope_abis)
        contract["is_environment_prerequisite"] = True
        contract["elapsed_s"] = round(time.time() - t0, 1)
        _emit(contract, args.json)
        return 0

    # ── 2. environment capability match (ENVIRONMENT_PROFILE.json) ──────
    try:
        with open(ENV_PROFILE) as f:
            env = json.load(f)
    except OSError:
        env = {}
    contract["environment_matches"] = {
        "host_executable_abis": EXECUTABLE_ABIS,
        "apk_abis": contract["prerequisites"]["lib_abis"] or manifest["abis"],
        "host_api": env.get("ENV-001_api_level", {}).get("sdk_int"),
        "apk_min_sdk": manifest["min_sdk"],
        "apk_target_sdk": manifest["target_sdk"],
    }
    contract["prerequisites"]["env"] = env

    # ── 3. install + launch in an isolated data root ─────────────────────
    tmp_root = args.data_root or tempfile.mkdtemp(prefix="pf_")
    os.makedirs(tmp_root, exist_ok=True)
    rc_i, out_i, err_i = run_cli(
        ["install", apk, "--data-root", tmp_root])
    contract["install"] = "OK" if rc_i == 0 else "FAILED"
    if rc_i != 0:
        blob = (err_i + out_i).lower()
        if "identity" in blob or "package name" in blob:
            contract["install_reason"] = "identity"
        elif "signature" in blob or "permission" in blob:
            contract["install_reason"] = "security"
    pkg = manifest["package"]
    if contract["install"] == "OK" and pkg:
        rc_r, out_r, err_r = run_cli(
            ["run", "--package", pkg, "--data-root", tmp_root,
             "-o", os.path.join(tmp_root, "out"),
             "--max-seconds", str(args.max_seconds)],
            timeout=args.max_seconds + 90)
        blob = out_r + err_r
        if rc_r != 0 and "MAX-SECONDS enabled" in blob:
            contract["launch"] = "BUDGET_STOPPED"
        else:
            contract["launch"] = "OK" if rc_r == 0 else "FAILED"
        contract["launch_detail"] = blob[:4000]
        # First divergence: engine markers carry method+pc evidence.
        m = re.search(
            r"\[SYNTH-EXC\][^\n]*?method=(\S+) pc=(\d+)", blob)
        if m:
            contract["first_divergence"] = {
                "kind": "uncaught_exception", "method": m.group(1),
                "pc": int(m.group(2)),
                "detail": re.search(r"\[SYNTH-EXC\][^\n]*", blob).group(0)[:300],
            }
            contract["launch_stage"] = "runtime"
        else:
            for stage, pat in [
                ("dex", r"\[ERROR\].*(dex|DEX|class)"),
                ("resource", r"(resource|arsc|axml).*(not|missing|fail)"),
                ("security", r"(permission|security).*(denied|fail)"),
                ("service", r"(service|provider).*(not found|missing)"),
            ]:
                if re.search(pat, blob, re.I):
                    contract["launch_stage"] = stage
                    contract["launch"] = "FAILED"
                    break
        m_frames = re.search(r"Frames Rendered:\s*(\d+)", blob)
        contract["frames"] = int(m_frames.group(1)) if m_frames else 0
        # App callbacks: lifecycle trace proves real app code ran.
        lt = os.path.join(tmp_root, "out", "lifecycle_trace.json")
        if os.path.isfile(lt):
            try:
                with open(lt) as f:
                    ldata = f.read()
                contract["callbacks"] = ldata.count('"method"')
            except OSError:
                contract["callbacks"] = 0
        else:
            contract["callbacks"] = 0
        contract["evidence"]["run_output"] = os.path.join(tmp_root, "out")
        if contract["first_divergence"] is None and contract["launch"] == "FAILED":
            contract["first_divergence"] = {
                "kind": "launch_failure",
                "detail": (blob[:300] if blob else "no output"),
            }
    if not args.data_root:
        shutil.rmtree(tmp_root, ignore_errors=True)

    contract["verdict"], contract["blocker"] = classify({
        "parse": "OK", "install": contract["install"],
        "install_reason": contract.get("install_reason"),
        "launch": contract["launch"], "launch_stage":
            contract.get("launch_stage"),
        "first_divergence": contract.get("first_divergence"),
        "frames": contract.get("frames", 0),
        "callbacks": contract.get("callbacks", 0),
        "min_sdk": manifest["min_sdk"], "abis": manifest["abis"],
        "lib_abis": contract["prerequisites"].get("lib_abis", []),
        "features": manifest["features"], "gles_version":
            manifest["gles_version"], "env": env,
    })
    contract["is_environment_prerequisite"] = contract["verdict"] in (
        "ENVIRONMENT_BLOCKED", "GRAPHICS_BLOCKED", "MEDIA_BLOCKED",
        "NETWORK_BLOCKED", "INPUT_BLOCKED")
    contract["elapsed_s"] = round(time.time() - t0, 1)
    _emit(contract, args.json)
    return 0


def _emit(contract, json_path):
    assert contract["verdict"] in ALL_VERDICTS, contract["verdict"]
    # LAW-001b honest-statistics fields: the SKIP bucket (ABI out of scope)
    # is separate from failures; PASS is a pass; RUNTIME_ROOT/CAPTURE_ONLY/
    # UNKNOWN are findings; every hard *_BLOCKED is a could-not-run.
    v = contract["verdict"]
    contract["verdict_class"] = VERDICT_CLASS.get(v, "BLOCKED")
    contract["in_current_test_scope"] = v != "ABI_OUT_OF_SCOPE"
    contract["counts_as_failure"] = VERDICT_CLASS.get(v, "BLOCKED") == "BLOCKED"
    print(json.dumps(contract, indent=1))
    if json_path:
        os.makedirs(os.path.dirname(os.path.abspath(json_path)),
                    exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(contract, f, indent=1)


if __name__ == "__main__":
    sys.exit(main())
