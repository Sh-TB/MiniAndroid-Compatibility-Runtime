#!/usr/bin/env python3
"""cont81_corpus_runner.py — CONT-78-addendum-compliant corpus runner (v2).

Closes the seven source-audit gaps of cont76_semantic_probe.py (issue #364
comment 6237592508) while preserving that script untouched for history:

 1. Versioned verdict vocabulary V2 (12 buckets) + raw legacy verdict kept
    per row; historical evidence is never silently rewritten.
 2. Pixel richness alone can NEVER yield REAL_APP_CONTENT — correlated
    runtime provenance (engine frame_analysis.verdict from
    trace_summary.json) is mandatory; pixels-without-provenance is
    PARTIAL_MARGINAL with an explicit note.
 3. Install/run failures separated: INSTALL_FAILURE, RUNTIME_CRASH,
    BUDGET_TIMEOUT, HARNESS_ENVIRONMENT_FAILURE — never collapsed into
    NO_SCREEN.
 4. Rich evidence columns: versionName/versionCode, ABI/native-lib
    inventory, exact install/run commands + rc, full screenshot SHA-256,
    engine verdict + first_missing_stage, trace_summary first_divergence,
    uncaught-exception count (F-016), termination reason, per-app logs.
 5. Interaction manifest: real dispatched --tap input, before/after
    screenshot + pixel-delta proof, --repeat N 3-run repeatability.
 6. ROOT resolved from script location (env MINIANDROID_ROOT override),
    fail-fast HARNESS_ENVIRONMENT_FAILURE if binary/toolchain absent.
 7. Honest denominator: distinct APK SHA vs distinct package counts, raw
    totals AND executable-denominator percentages, exclusions listed.

Verdict vocabulary V2 (row["verdict_v2"]):
  Harness/install bucket (excluded from app-success numerator):
    HARNESS_ENVIRONMENT_FAILURE, INSTALL_FAILURE, PREREQUISITE_MISMATCH
  Run-outcome bucket:
    BUDGET_TIMEOUT, RUNTIME_CRASH, NO_SCREEN
  App-outcome bucket (evidence-backed faces):
    REAL_APP_CONTENT, INTERACTIVE_CONTENT_VERIFIED, SPLASH_ONLY,
    WHITE_BLANK, DARK_SURFACE_NO_OPS, DEFAULT_BACKGROUND_ONLY,
    PARTIAL_MARGINAL

Usage:
  cont81_corpus_runner.py <apk...> [--out DIR] [--frames N] [--budget S]
      [--repeat N] [--manifest FILE] [--roots FILE] [--label L]
      [--selftest]

--selftest runs the 10 acceptance-gate classifier cases (no runtime).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("MINIANDROID_ROOT",
                      os.path.dirname(SCRIPT_ROOT))
BIN = os.path.join(ROOT, "miniandroid", "build", "miniandroid")
AAPT2 = os.path.join(ROOT, "tools", "toolchain", "aapt2")
SPLASH_SHA16 = "31ddd4d5b8e6d18e"
LEGACY_SPLASH_FAMILY = {"31ddd4d5b8e6d18e"}

V2_HARNESS = {"HARNESS_ENVIRONMENT_FAILURE", "INSTALL_FAILURE",
              "PREREQUISITE_MISMATCH"}
V2_RUN = {"BUDGET_TIMEOUT", "RUNTIME_CRASH", "NO_SCREEN"}
V2_APP = {"REAL_APP_CONTENT", "INTERACTIVE_CONTENT_VERIFIED", "SPLASH_ONLY",
          "WHITE_BLANK", "DARK_SURFACE_NO_OPS", "DEFAULT_BACKGROUND_ONLY",
          "PARTIAL_MARGINAL"}
V2_ALL = V2_HARNESS | V2_RUN | V2_APP


def sha256_full(p):
    h = hashlib_sha256(p)
    return h


def hashlib_sha256(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha16(s):
    return s[:16]


def fail_fast():
    """Addendum gap 6: resolve ROOT from script location, fail early."""
    problems = []
    if not os.path.isfile(BIN):
        problems.append(f"runtime binary missing: {BIN}")
    if not os.path.isfile(AAPT2):
        problems.append(f"aapt2 missing: {AAPT2}")
    return problems


def probe_apk(apk):
    """Addendum gap 4: package, version, ABI/native inventory."""
    info = {"apk_path": apk}
    info["apk_sha256"] = hashlib_sha256(apk)
    info["apk_sha16"] = sha16(info["apk_sha256"])
    info["apk_size_bytes"] = os.path.getsize(apk)
    try:
        r = subprocess.run([AAPT2, "dump", "badging", apk],
                           capture_output=True, text=True, timeout=90)
        out = r.stdout
        m = re.search(r"package: name='([^']+)'", out)
        info["package"] = m.group(1) if m else os.path.basename(apk)
        m = re.search(r"versionCode='([^']*)'", out)
        info["version_code"] = m.group(1) if m else ""
        m = re.search(r"versionName='([^']*)'", out)
        info["version_name"] = m.group(1) if m else ""
        m = re.search(r"sdkVersion:'([^']*)'", out)
        info["min_sdk"] = m.group(1) if m else ""
        m = re.search(r"targetSdkVersion:'([^']*)'", out)
        info["target_sdk"] = m.group(1) if m else ""
    except Exception as e:
        info["package"] = os.path.basename(apk)
        info["badging_error"] = str(e)
    # ABI inventory from the zip central directory
    abis = {}
    try:
        with zipfile.ZipFile(apk) as z:
            for n in z.namelist():
                if n.startswith("lib/"):
                    parts = n.split("/")
                    if len(parts) >= 3 and parts[2].endswith(".so"):
                        abis.setdefault(parts[1], 0)
                        abis[parts[1]] += 1
    except Exception as e:
        info["zip_error"] = str(e)
    info["abi_inventory"] = abis
    # The runtime host is x86_64: arm-only APKs are honest prerequisites.
    runnable = [a for a in abis if a in ("x86", "x86_64")]
    arm_only = bool(abis) and not runnable
    info["arm_only"] = arm_only
    info["has_native"] = bool(abis)
    return info


def parse_run_evidence(outdir, combined):
    """Correlated runtime provenance: trace_summary.json + stderr rows."""
    ev = {}
    ts_path = os.path.join(outdir, "trace_summary.json")
    if os.path.isfile(ts_path):
        try:
            ts = json.load(open(ts_path))
            fa = ts.get("frame_analysis") or {}
            ev["engine_verdict"] = fa.get("verdict", "")
            ev["first_missing_stage"] = fa.get("first_missing_stage", "")
            ev["engine_unique_colors"] = fa.get("unique_colors")
            ev["first_divergence"] = ts.get("first_divergence")
            ev["last_exception"] = ts.get("last_exception")
        except Exception as e:
            ev["trace_summary_error"] = str(e)
    # stderr fallback + honesty rows (F-016 uncaught, F-NEW-233 frame truth)
    m = re.search(r"\[F-016 exception-honesty: (\d+) uncaught", combined)
    if m:
        ev["uncaught_n"] = int(m.group(1))
    m = re.search(r"\[F-NEW-233 frame truth: verdict=([^,\]]+)"
                  r"(?:, first_missing_stage=([^\]]+))?", combined)
    if m:
        ev.setdefault("engine_verdict", m.group(1).strip())
        if m.group(2):
            ev.setdefault("first_missing_stage", m.group(2).strip())
    if "PATH-LAW" in combined:
        ev["path_law_rows"] = combined.count("PATH-LAW")
    return ev


def pixel_metrics(png):
    from PIL import Image
    import math
    im = Image.open(png).convert("RGB")
    w, h = im.size
    px = list(im.resize((min(w, 270), min(h, 480))).getdata())
    total = len(px)
    colors = {}
    for p in px:
        colors[p] = colors.get(p, 0) + 1
    bg = max(colors.values())
    nonbg = total - bg
    ent = (-sum((c / total) * math.log2(c / total) for c in colors.values())
           if total else 0.0)
    return {"unique_colors": len(colors),
            "nonbg_ratio": round(nonbg / total, 4),
            "entropy": round(ent, 3)}


def dominant_pixel(png):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    return im.getpixel((5, 5))


def classify_v2(row):
    """Pure verdict function — self-testable (addendum acceptance gate).

    Input row keys consumed: install_rc, arm_only, has_native,
    run_termination ("completed"|"timeout"|"error"|"not-run"), run_rc,
    screenshot_path-present (screenshot_sha256 nonempty), pixel census,
    engine_verdict, harness_ok, interactive block.
    """
    verdict = None
    notes = []
    # 1. Harness bucket — always wins
    if not row.get("harness_ok", True):
        verdict = "HARNESS_ENVIRONMENT_FAILURE"
    # 2. Install honesty: a failed install is NEVER a runtime face
    elif row.get("install_rc", 0) != 0:
        verdict = "INSTALL_FAILURE"
    # 3. ABI prerequisite gate — pre-run refusal, not a renderer failure
    elif row.get("arm_only"):
        verdict = "PREREQUISITE_MISMATCH"
    # 4. Run-outcome bucket
    elif row.get("run_termination") == "timeout":
        verdict = "BUDGET_TIMEOUT"
    elif (row.get("run_termination") == "error"
          and not row.get("screenshot_sha256")):
        verdict = "RUNTIME_CRASH"
    elif not row.get("screenshot_sha256"):
        verdict = "NO_SCREEN"
    else:
        # 5. App-outcome bucket — correlated proof REQUIRED for real
        eng = row.get("engine_verdict", "")
        rich = (row.get("nonbg_ratio", 0) >= 0.02
                and row.get("unique_colors", 0) >= 64)
        if row.get("interactive_delta") and eng == "REAL_APP_CONTENT":
            verdict = "INTERACTIVE_CONTENT_VERIFIED"
        elif eng == "REAL_APP_CONTENT":
            # The engine frame census is the authoritative correlated
            # provenance (app-owned pixels INSIDE the live window, counted
            # at runtime). Sparse-content apps (sparse board on dark bg,
            # black-on-white calculator) are legitimately thin in the
            # downscaled PIL re-census — the runtime census wins; both
            # measurements stay in the row for review.
            verdict = "REAL_APP_CONTENT"
            if not rich:
                notes.append("sparse-content: engine-owned-pixel census "
                             "authoritative; PIL re-census thin")
        elif rich and not eng:
            verdict = "PARTIAL_MARGINAL"
            notes.append("pixels-without-provenance: engine verdict absent")
        elif rich and eng and eng != "REAL_APP_CONTENT":
            verdict = "PARTIAL_MARGINAL"
            notes.append(f"rich pixels but engine says {eng}")
        else:
            shot16 = sha16(row.get("screenshot_sha256", ""))
            if shot16 in LEGACY_SPLASH_FAMILY:
                verdict = "SPLASH_ONLY"
            else:
                dom = row.get("dominant_rgb", [0, 0, 0])
                uniform = row.get("unique_colors", 99) <= 2
                if uniform and dom[0] > 240 and dom[1] > 240 \
                        and dom[2] > 240:
                    verdict = "WHITE_BLANK"
                elif eng == "DEFAULT_BACKGROUND_ONLY":
                    verdict = "DEFAULT_BACKGROUND_ONLY"
                elif uniform:
                    verdict = "DARK_SURFACE_NO_OPS"
                elif row.get("nonbg_ratio", 0) >= 0.002 \
                        or row.get("unique_colors", 0) >= 24:
                    verdict = "PARTIAL_MARGINAL"
                else:
                    verdict = "WHITE_BLANK"
    row["verdict_v2"] = verdict
    row["notes"] = (row.get("notes", "") + " | ".join(notes)).strip(" |")
    # legacy vocabulary preserved (cont76 shared vocabulary mapping)
    lv = {"REAL_APP_CONTENT": "REAL_APP_UI",
          "INTERACTIVE_CONTENT_VERIFIED": "REAL_APP_UI",
          "SPLASH_ONLY": "SPLASH_ONLY",
          "WHITE_BLANK": "WHITE_BLANK",
          "DARK_SURFACE_NO_OPS": "DARK_SURFACE_NO_OPS",
          "DEFAULT_BACKGROUND_ONLY": "DARK_SURFACE_NO_OPS",
          "PARTIAL_MARGINAL": "PARTIAL_MARGINAL",
          "PREREQUISITE_MISMATCH": "PREREQUISITE_MISMATCH"}.get(verdict)
    row["legacy_verdict"] = lv
    return row


def run_one(apk, out_base, frames, budget, store, taps=None, run_tag="r1",
            click_test=False):
    """Install + one bounded run. Returns the raw row (pre-classification)."""
    info = probe_apk(apk)
    pkg = info["package"]
    outdir = os.path.join(out_base, pkg, run_tag)
    shutil.rmtree(outdir, ignore_errors=True)
    os.makedirs(outdir, exist_ok=True)
    row = dict(info)
    row["binary_sha16"] = sha16(hashlib_sha256(BIN)) \
        if os.path.isfile(BIN) else "MISSING"
    row["harness_ok"] = os.path.isfile(BIN) and os.path.isfile(AAPT2)

    # --- install (addendum gap 3: separated + preserved) ---
    inst_cmd = [BIN, "install", apk, "--data-root", store]
    row["install_cmd"] = " ".join(inst_cmd)
    try:
        inst = subprocess.run(inst_cmd, capture_output=True, text=True,
                              timeout=180)
        row["install_rc"] = inst.returncode
        row["install_stderr_tail"] = (inst.stderr or "")[-800:]
    except subprocess.TimeoutExpired:
        row["install_rc"] = 124
        row["install_stderr_tail"] = "install timeout 180s"
    if row["install_rc"] != 0:
        row["run_termination"] = "not-run"
        return row

    # --- run (canonical harness command) ---
    cmd = [BIN, "run", "--package", pkg, "--data-root", store,
           "--width", "1080", "--height", "1920",
           "--frames", str(frames), "--max-seconds", str(budget),
           "-o", outdir]
    if taps:
        for t in taps:
            cmd += ["--tap", t]
    if click_test:
        cmd += ["--click-test"]
    row["run_cmd"] = " ".join(cmd)
    row["run_termination"] = "completed"
    t0 = time.time()
    # MINIANDROID_BOOT_TRACE=1 → trace_summary.json (correlated runtime
    # provenance: engine frame verdict + first_missing_stage + divergence).
    # Zero-drift law verified on the canonical wall rows this wave.
    env = dict(os.environ)
    env.setdefault("MINIANDROID_BOOT_TRACE", "1")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=budget + 90, env=env)
        combined = (r.stdout or "") + "\n" + (r.stderr or "")
        row["run_rc"] = r.returncode
        if r.returncode not in (0,):
            row["run_termination"] = "error"
    except subprocess.TimeoutExpired as e:
        combined = ""
        if e.stdout:
            combined += e.stdout.decode(errors="replace") \
                if isinstance(e.stdout, bytes) else e.stdout
        if e.stderr:
            combined += e.stderr.decode(errors="replace") \
                if isinstance(e.stderr, bytes) else e.stderr
        row["run_rc"] = None
        row["run_termination"] = "timeout"
    row["wall_seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(out_base, pkg, f"stdout_{run_tag}.txt"),
              "w") as f:
        f.write(combined)
    row["run_combined_chars"] = len(combined)

    # --- evidence capture ---
    shot = os.path.join(outdir, "screenshot.png")
    if os.path.isfile(shot):
        s256 = hashlib_sha256(shot)
        row["screenshot_sha256"] = s256
        row["screenshot_sha16"] = sha16(s256)
        shutil.copy(shot, os.path.join(out_base, pkg,
                                       f"screenshot_{run_tag}.png"))
        row.update(pixel_metrics(shot))
        row["dominant_rgb"] = list(dominant_pixel(shot))
    else:
        row["screenshot_sha256"] = ""
    row.update(parse_run_evidence(outdir, combined))
    ts_path = os.path.join(outdir, "trace_summary.json")
    if os.path.isfile(ts_path):
        shutil.copy(ts_path, os.path.join(out_base, pkg,
                                          f"trace_summary_{run_tag}.json"))
    return row


def run_repeat(apk, out_base, frames, budget, store, repeat, taps=None,
               click_test=False):
    """--repeat N: 3-run repeatability for claimed successes."""
    rows = [run_one(apk, out_base, frames, budget, store, taps,
                    run_tag=f"r{i+1}", click_test=click_test)
            for i in range(repeat)]
    classify_v2(rows[0])
    faces = {r.get("screenshot_sha256", "") for r in rows}
    verdicts = set()
    for r in rows[1:]:
        classify_v2(r)
        verdicts.add(r["verdict_v2"])
    row = rows[0]
    row["repeat_runs"] = repeat
    row["repeat_face_stable"] = len(faces) == 1
    row["repeat_verdicts"] = sorted(verdicts | {row["verdict_v2"]})
    row["repeat_all_same_verdict"] = len(verdicts | {row["verdict_v2"]}) <= 1
    return row


def run_interactive(apk, out_base, frames, budget, store, taps, repeat,
                    click_test=False, i_frames=None):
    """Addendum gap 5: real dispatched input + before/after delta proof."""
    before = run_one(apk, out_base, frames, budget, store, taps=None,
                     run_tag="before", click_test=False)
    classify_v2(before)
    after = run_repeat(apk, out_base, i_frames or frames, budget, store,
                       repeat, taps=taps, click_test=click_test)
    row = dict(after)
    row["interactive_taps"] = taps
    row["before_screenshot_sha256"] = before.get("screenshot_sha256", "")
    row["before_verdict_v2"] = before.get("verdict_v2", "")
    delta = (before.get("screenshot_sha256", "") != ""
             and before.get("screenshot_sha256")
             != after.get("screenshot_sha256", ""))
    row["interactive_delta"] = bool(delta)
    if delta:
        row["notes"] = (row.get("notes", "")
                        + " before!=after face under dispatched taps").strip()
    # classify again now that interactive_delta is known
    classify_v2(row)
    return row


def scoreboard(rows, label=""):
    """Addendum gap 7: honest denominator, distinct counts, exclusions."""
    n = len(rows)
    distinct_apk = len({r.get("apk_sha256") for r in rows})
    distinct_pkg = len({r.get("package") for r in rows})
    excluded = [r for r in rows if r.get("verdict_v2") in V2_HARNESS]
    executable = [r for r in rows if r.get("verdict_v2") not in V2_HARNESS]
    tally = {}
    for r in rows:
        tally[r.get("verdict_v2")] = tally.get(r.get("verdict_v2"), 0) + 1
    tally_exec = {}
    for r in executable:
        tally_exec[r.get("verdict_v2")] = \
            tally_exec.get(r.get("verdict_v2"), 0) + 1
    ne = len(executable)
    real = sum(1 for r in executable
               if r.get("verdict_v2") in ("REAL_APP_CONTENT",
                                          "INTERACTIVE_CONTENT_VERIFIED"))
    inter = sum(1 for r in executable
                if r.get("verdict_v2") == "INTERACTIVE_CONTENT_VERIFIED")
    sb = {
        "label": label,
        "raw_rows": n,
        "distinct_apk_shas": distinct_apk,
        "distinct_packages": distinct_pkg,
        "exclusions": {v: tally.get(v, 0) for v in sorted(V2_HARNESS)},
        "executable_denominator": ne,
        "tally_all_rows": tally,
        "tally_executable": tally_exec,
        "pct_of_executable": {k: round(100.0 * v / ne, 1)
                              for k, v in tally_exec.items()} if ne else {},
        "real_app_content_pct_of_executable":
            round(100.0 * real / ne, 1) if ne else 0.0,
        "interactive_verified_count": inter,
    }
    return sb


def selftest():
    """Addendum acceptance gate: 10 classifier cases, no runtime needed."""
    ok = [0, 0]

    def check(name, got, want):
        good = got == want
        ok[0] += good
        ok[1] += 1
        print(f"  [{'PASS' if good else 'FAIL'}] {name}: {got}"
              + ("" if good else f"  (want {want})"))

    base = {"harness_ok": True, "install_rc": 0, "arm_only": False,
            "run_termination": "completed", "run_rc": 0,
            "screenshot_sha256": "0" * 64, "nonbg_ratio": 0.0,
            "unique_colors": 1, "dominant_rgb": [255, 255, 255],
            "engine_verdict": ""}
    # 1. install failure
    r = dict(base); r["install_rc"] = 1; r["screenshot_sha256"] = ""
    check("install-failure", classify_v2(r)["verdict_v2"], "INSTALL_FAILURE")
    # 2. no screenshot
    r = dict(base); r["screenshot_sha256"] = ""
    check("no-screenshot", classify_v2(r)["verdict_v2"], "NO_SCREEN")
    # 3. splash
    r = dict(base)
    r["screenshot_sha256"] = "31ddd4d5b8e6d18e" + "0" * 48
    check("splash", classify_v2(r)["verdict_v2"], "SPLASH_ONLY")
    # 4. white blank
    r = dict(base); r["unique_colors"] = 2
    check("white-blank", classify_v2(r)["verdict_v2"], "WHITE_BLANK")
    # 5. app-owned dark background, no draw ops (engine verdict present)
    r = dict(base); r["unique_colors"] = 2
    r["dominant_rgb"] = [8, 36, 26]
    r["engine_verdict"] = "DEFAULT_BACKGROUND_ONLY"
    check("dark-default-bg", classify_v2(r)["verdict_v2"],
          "DEFAULT_BACKGROUND_ONLY")
    # 6. rich pixels WITHOUT provenance
    r = dict(base); r["nonbg_ratio"] = 0.3; r["unique_colors"] = 200
    out = classify_v2(r)
    check("rich-no-provenance", out["verdict_v2"], "PARTIAL_MARGINAL")
    check("rich-no-provenance-note",
          "pixels-without-provenance" in out["notes"], True)
    # 7. genuine content WITH provenance
    r = dict(base); r["nonbg_ratio"] = 0.3; r["unique_colors"] = 200
    r["engine_verdict"] = "REAL_APP_CONTENT"
    check("genuine-content", classify_v2(r)["verdict_v2"],
          "REAL_APP_CONTENT")
    # 8. ABI refusal
    r = dict(base); r["arm_only"] = True
    check("abi-refusal", classify_v2(r)["verdict_v2"],
          "PREREQUISITE_MISMATCH")
    # 9. budget timeout
    r = dict(base); r["run_termination"] = "timeout"
    check("budget-timeout", classify_v2(r)["verdict_v2"], "BUDGET_TIMEOUT")
    # 10. interactive before/after
    r = dict(base); r["nonbg_ratio"] = 0.3; r["unique_colors"] = 200
    r["engine_verdict"] = "REAL_APP_CONTENT"
    r["interactive_delta"] = True
    check("interactive", classify_v2(r)["verdict_v2"],
          "INTERACTIVE_CONTENT_VERIFIED")
    # 11. sparse-content: engine REAL, thin PIL re-census → still REAL
    r = dict(base); r["nonbg_ratio"] = 0.0136; r["unique_colors"] = 209
    r["engine_verdict"] = "REAL_APP_CONTENT"
    out = classify_v2(r)
    check("sparse-content", out["verdict_v2"], "REAL_APP_CONTENT")
    check("sparse-content-note",
          "sparse-content" in out["notes"], True)
    # harness failure case (bonus)
    r = dict(base); r["harness_ok"] = False
    check("harness-failure", classify_v2(r)["verdict_v2"],
          "HARNESS_ENVIRONMENT_FAILURE")
    print(f"SELFTEST: {ok[0]}/{ok[1]} PASS")
    return 0 if ok[0] == ok[1] else 1


def collect(out, label):
    """Recompute the scoreboard from every <out>/<pkg>/row.json —
    resume-friendly master collect (container resets kill batches)."""
    rows = []
    if os.path.isdir(out):
        for pkg in sorted(os.listdir(out)):
            p = os.path.join(out, pkg, "row.json")
            if os.path.isfile(p):
                try:
                    rows.append(json.load(open(p)))
                except Exception:
                    pass
    if not rows:
        print(f"COLLECT: no rows under {out}")
        return 2
    sb = scoreboard(rows, label)
    result = {"scoreboard": sb, "rows": rows}
    json.dump(result, open(os.path.join(out, "result.json"), "w"),
              indent=1, default=str)
    print(f"COLLECT [{label}]: {sb['raw_rows']} rows "
          f"({sb['distinct_apk_shas']} distinct APK SHA / "
          f"{sb['distinct_packages']} packages), "
          f"executable={sb['executable_denominator']}")
    print(f"TALLY: {sb['tally_all_rows']}")
    print(f"PCT(executable): {sb['pct_of_executable']}")
    print(f"REAL_APP_CONTENT(+INTERACTIVE)="
          f"{sb['real_app_content_pct_of_executable']}% "
          f"of executable, interactive={sb['interactive_verified_count']}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("apks", nargs="*")
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--store", default=None)
    ap.add_argument("--frames", type=int, default=5)
    ap.add_argument("--budget", type=int, default=90)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--manifest", default=None,
                    help="interaction manifest JSON: "
                         "{package: {taps: [\"x,y@frame\", ...]}}")
    ap.add_argument("--roots", default=None,
                    help="optional JSON {package|apk_sha16: root_id}")
    ap.add_argument("--label", default="cont81")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.collect:
        out = args.out or os.path.join(ROOT, "run", "cont81",
                                       f"corpus_{args.label}")
        return collect(out, args.label)

    if args.selftest:
        return selftest()

    problems = fail_fast()
    out = args.out or os.path.join(ROOT, "run", "cont81",
                                   f"corpus_{args.label}")
    store = args.store or os.path.join(out, "store")
    os.makedirs(store, exist_ok=True)
    if problems:
        # fail-fast with explicit harness error for EVERY requested apk
        rows = [{"package": os.path.basename(a), "apk_path": a,
                 "harness_ok": False, "install_rc": 0,
                 "run_termination": "not-run",
                 "harness_problems": problems} for a in args.apks]
        for r in rows:
            classify_v2(r)
        sb = scoreboard(rows, args.label)
        result = {"scoreboard": sb, "rows": rows,
                  "harness_problems": problems}
        os.makedirs(out, exist_ok=True)
        json.dump(result, open(os.path.join(out, "result.json"), "w"),
                  indent=1, default=str)
        print(f"HARNESS_ENVIRONMENT_FAILURE: {'; '.join(problems)}")
        return 2

    manifest = {}
    if args.manifest:
        manifest = json.load(open(args.manifest))
    roots_map = {}
    if args.roots:
        roots_map = json.load(open(args.roots))

    rows = []
    for apk in args.apks:
        info = probe_apk(apk)
        pkg = info["package"]
        m = manifest.get(pkg) or manifest.get(info["apk_sha16"]) or {}
        taps = m.get("taps")
        if taps or m.get("click_test"):
            row = run_interactive(apk, out, args.frames, args.budget,
                                  store, taps, args.repeat,
                                  click_test=bool(m.get("click_test")),
                                  i_frames=m.get("frames"))
        else:
            row = run_repeat(apk, out, args.frames, args.budget, store,
                             args.repeat)
        row["root_id"] = (m.get("root_id")
                          or roots_map.get(pkg)
                          or roots_map.get(info["apk_sha16"], ""))
        row["next_action"] = m.get("next_action", "")
        print(f"  {pkg}: {row['verdict_v2']} "
              f"(shot {row.get('screenshot_sha16', '-')})"
              + (f" repeat_stable={row['repeat_face_stable']}"
                 if row.get("repeat_runs", 1) > 1 else ""))
        json.dump(row, open(os.path.join(out, pkg, "row.json"), "w"),
                  indent=1, default=str)
        rows.append(row)

    sb = scoreboard(rows, args.label)
    result = {"scoreboard": sb, "rows": rows}
    os.makedirs(out, exist_ok=True)
    json.dump(result, open(os.path.join(out, "result.json"), "w"),
              indent=1, default=str)
    print(f"SCOREBOARD [{args.label}]: {sb['raw_rows']} rows "
          f"({sb['distinct_apk_shas']} distinct APK SHA / "
          f"{sb['distinct_packages']} packages), "
          f"executable={sb['executable_denominator']}, "
          f"REAL_APP_CONTENT(+INTERACTIVE)="
          f"{sb['real_app_content_pct_of_executable']}% "
          f"of executable, interactive={sb['interactive_verified_count']}")
    print(f"TALLY: {sb['tally_all_rows']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
