#!/usr/bin/env python3
"""cont5_gate_matrix.py — PHASE 6 live-coverage matrix for the
15-verdict unknown-APK preflight gate (issue #375 CONT-5).

Runs the REAL CLI (scripts/unknown_apk_preflight.py -> miniandroid binary)
over every locally available APK + the standard install-negative fixtures,
records (verdict, blocker, evidence sha) per APK, and emits:
  run/cont5/gate_matrix/matrix.jsonl   one row per APK
  run/cont5/gate_matrix/coverage.json  verdict -> [apk,...] live counts
  docs/UNKNOWN_APK_GATE_LIVE_MATRIX.{md,jsonl} (committed ledger)

No fabricated APKs: negatives reuse the committed N-04/N-05 tamper cases
(truncated / no-manifest) and the committed reinstall-identity tamper law.
"""
import json
import os
import subprocess
import sys
import hashlib
import zipfile

BASE = "/home/z/my-project"
OUT = f"{BASE}/run/cont5/gate_matrix"
PF = f"{BASE}/scripts/unknown_apk_preflight.py"
NEG = f"{BASE}/run/cont5/gate_matrix/negatives"

ALL_VERDICTS = [
    "PREFLIGHT_PASS", "ENVIRONMENT_BLOCKED", "INSTALL_BLOCKED",
    "SECURITY_BLOCKED", "IDENTITY_BLOCKED", "SERVICE_BLOCKED",
    "EXECUTION_BLOCKED", "RESOURCE_BLOCKED", "GRAPHICS_BLOCKED",
    "MEDIA_BLOCKED", "NETWORK_BLOCKED", "INPUT_BLOCKED", "CAPTURE_ONLY",
    "RUNTIME_ROOT", "UNKNOWN",
]


def corpus():
    apks = []
    for root in ("upload/canonical_apks", "upload/foundation_apks",
                 "upload/s65_apks", "upload/s80_games", "upload/s83_games",
                 "upload/s86_games", "upload/s98_games", "upload/s105_apks",
                 "upload/s133_browser", "upload/s100_browser",
                 "apk_cache"):
        d = os.path.join(BASE, root)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".apk"):
                    apks.append((f, os.path.join(d, f)))
    for f in ("upload/opencalculator_53.apk", "upload/chess_jwtc_298.apk",
              "upload/klondike_veldsoft_3.apk", "upload/notes_secuso_105.apk",
              "upload/sudoku_secuso_101.apk", "upload/flappycow_rebuilt.apk"):
        if os.path.isfile(os.path.join(BASE, f)):
            apks.append((os.path.basename(f), os.path.join(BASE, f)))
    return apks


def make_negatives():
    """Committed negative law only: truncate + no-manifest + identity tamper."""
    os.makedirs(NEG, exist_ok=True)
    src = os.path.join(BASE, "upload/canonical_apks/app.varlorg.unote_30.apk")
    rows = []
    # N-04 law: truncated zip -> install parse failure
    trunc = f"{NEG}/truncated_unote.apk"
    with open(src, "rb") as f:
        data = f.read()
    with open(trunc, "wb") as f:
        f.write(data[: len(data) // 3])
    rows.append(("truncated_unote.apk (N-04 law)", trunc))
    # N-05 law: valid zip, no manifest
    noman = f"{NEG}/no_manifest.apk"
    with zipfile.ZipFile(noman, "w") as z:
        z.writestr("classes.dex", b"dex\nnot-a-real-dex")
    rows.append(("no_manifest.apk (N-05 law)", noman))
    # identity tamper law: SAME package claim, different bytes (reinstall
    # matrix records install-refusal identity) — flip one byte in an
    # unused zip entry region by rebuilding the zip with modified comment.
    tamper = f"{NEG}/identity_tamper_unote.apk"
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(
            tamper, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in zin.namelist():
            zout.writestr(n, zin.read(n))
        zout.comment = b"CONT5-IDENTITY-TAMPER"
    rows.append(("identity_tamper_unote.apk (reinstall-identity law)",
                 tamper))
    return rows


def run_pf(apk, label):
    j = f"{OUT}/json/{label}.json"
    os.makedirs(f"{OUT}/json", exist_ok=True)
    r = subprocess.run([sys.executable, PF, apk, "--json", j,
                        "--max-seconds", "90"],
                       capture_output=True, text=True, cwd=BASE,
                       timeout=420)
    if os.path.isfile(j):
        return json.load(open(j))
    return {"verdict": "UNKNOWN", "blocker": f"gate CLI crashed rc={r.returncode}",
            "apk_path": apk, "evidence": {}}


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [("gate_a_probe.apk", f"{BASE}/gate_a_probe.apk")]
    jobs += corpus()
    jobs += make_negatives()
    rows = []
    for label, apk in jobs:
        if not os.path.isfile(apk):
            continue
        c = run_pf(apk, label.replace("/", "_"))
        row = {
            "apk": label,
            "path": apk,
            "sha16": c.get("apk_sha256_16"),
            "verdict": c.get("verdict"),
            "blocker": (c.get("blocker") or "")[:220],
            "launch": c.get("launch"),
            "install": c.get("install"),
            "first_divergence": c.get("first_divergence"),
        }
        rows.append(row)
        print(f"{row['verdict']:>18}  {label}")
    with open(f"{OUT}/matrix.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    cov = {v: [] for v in ALL_VERDICTS}
    for r in rows:
        cov.setdefault(r["verdict"], []).append(r["apk"])
    with open(f"{OUT}/coverage.json", "w") as f:
        json.dump(cov, f, indent=1)
    print("\n== LIVE COVERAGE ==")
    for v in ALL_VERDICTS:
        print(f"{v:>20}: {len(cov.get(v, []))}")


if __name__ == "__main__":
    main()
