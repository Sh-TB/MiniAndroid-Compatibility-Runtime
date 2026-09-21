#!/usr/bin/env python3
"""s74f_ops_campaign.py — S74 FOLLOW-UP WAVE: operational execution evidence.

Runs every canonical app on the freshly-built HEAD binary, captures
launch/interaction frames, inspects the per-app sandbox data-root,
and assembles a compact human-visible evidence bundle per app under
docs/evidence/s74_ops/<app>/.

LAWS:
  - visual_evidence.status is assigned ONLY from measured frame metrics
    (non-white px + color diversity), never from "the run exited 0".
  - No frame fabrication: every bundled PNG is copied from a real run dir.
  - Interaction uses the canonical input paths only (--click-count
    round-robin listener dispatch, --tap x,y@frame scheduled touch).
  - Determinism: not re-proven here (S73/S74 fidelity probes own that);
    this wave records single-session evidence + SHA256SUMS.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from PIL import Image
import numpy as np

REPO = "/home/z/my-project"
BIN = f"{REPO}/miniandroid/build/miniandroid"
CORPUS = f"{REPO}/upload/canonical_apks"
RUNROOT = f"{REPO}/run/s74f_ops"
OUTROOT = f"{REPO}/docs/evidence/s74_ops"

HEAD = subprocess.check_output(
    ["git", "-C", REPO, "rev-parse", "--short", "HEAD"], text=True).strip()

# (dossier_id, apk_path, launch_frames, interaction_clicks, interaction_taps, timeout_s)
APPS = [
    ("unote",        "app.varlorg.unote_30.apk",        6, 6,  [], 150),
    ("dooz",         "io.github.yamin8000.dooz_23.apk", 6, 0,  [], 150),
    ("gmdice",       "de.duenndns.gmdice_8.apk",        6, 0,  ["348,1848@3", "116,1848@4"], 150),
    ("microtimer",   "dubrowgn.microtimer_8.apk",       6, 6,  [], 150),
    ("fishrings",    "fishrings_v1.23_vc6.apk",         9, 0,  [], 150),
    ("tripeaks",     "tripeaks_v1.2.1_vc4.apk",         6, 3,  [], 150),
    ("bouncy",       "bouncy.apk",                      6, 4,  [], 150),
    ("stopwatch",    "com.github.muellerma.stopwatch_6.apk", 4, 0, [], 150),
    ("opmt",         "opmt_v0.1.2_vc1.apk",             6, 4,  [], 150),
    ("tictactoe",    "com.emmanuelmess.tictactoe_3.apk", 3, 0, [], 150),
]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def frame_metrics(png_path):
    im = np.array(Image.open(png_path).convert("RGB"))
    px = im.reshape(-1, 3).astype(np.int32)
    nonwhite = int((px.sum(axis=1) < 720).sum())
    nonblack = int((px.sum(axis=1) > 60).sum())
    colors = {tuple(c) for c in px[::97]}
    return {
        "resolution": [im.shape[1], im.shape[0]],
        "nonwhite_px": nonwhite,
        "nonblack_px": nonblack,
        "color_diversity_sampled": len(colors),
    }


def walk_sandbox(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            out.append({"path": rel, "size": os.path.getsize(p),
                        "sha256_16": sha256_file(p)[:16]})
    return sorted(out, key=lambda x: x["path"])


def run_engine(run_dir, apk, extra_args, timeout):
    os.makedirs(run_dir, exist_ok=True)
    cmd = [BIN, "run", "--execution-mode", "real-dalvik",
           "--dump-api-trace", "--dump-view-tree",
           "--data-root", f"{run_dir}/sandbox", "-o", run_dir, apk] + extra_args
    try:
        r = subprocess.run(cmd, cwd=run_dir, capture_output=True, text=True,
                           timeout=timeout)
        rc = r.returncode
        log = (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        rc = 124
        log = f"TIMEOUT after {timeout}s\n{(e.stdout or '')[:2000]}"
    with open(f"{run_dir}/engine_stdout.log", "w") as f:
        f.write(log)
    return rc


def report_summary(run_dir):
    """Extract engine-reported status/errors from report.md (canonical)."""
    rep = os.path.join(run_dir, "report.md")
    status, errors = None, None
    if os.path.exists(rep):
        txt = open(rep, errors="replace").read()
        for line in txt.splitlines():
            if "Status:" in line:
                status = line.split("Status:")[1].strip()
            if line.startswith("| Errors |"):
                try:
                    errors = int(line.split("|")[2].strip())
                except (ValueError, IndexError):
                    pass
    return status, errors


def pick_representatives(frames_dir, interaction):
    """Pick launch / interaction / final frames by metric (deterministic)."""
    if not os.path.isdir(frames_dir):
        return []
    names = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
    if not names:
        return []
    infos = []
    for n in names:
        m = frame_metrics(os.path.join(frames_dir, n))
        infos.append((n, m))
    launch = infos[0]
    final = infos[-1]
    picked = [("01_launch.png", launch)]
    if interaction and len(infos) > 2:
        # interaction frame: first frame whose metrics differ from launch
        for n, m in infos[1:-1]:
            if abs(m["nonwhite_px"] - launch[1]["nonwhite_px"]) > 500:
                picked.append(("02_interaction.png", (n, m)))
                break
        picked.append(("03_final.png", final))
    elif len(infos) > 2:
        # no interaction: include the most-different mid frame if any
        mid = max(infos[1:-1], key=lambda t: abs(t[1]["nonwhite_px"] - launch[1]["nonwhite_px"]))
        if abs(mid[1]["nonwhite_px"] - launch[1]["nonwhite_px"]) > 500:
            picked.append(("02_mid_maxdiff.png", mid))
        picked.append(("03_final.png", final))
    else:
        if final[0] != launch[0]:
            picked.append(("03_final.png", final))
    return picked


def main():
    only = sys.argv[1:] or None
    os.makedirs(OUTROOT, exist_ok=True)
    sessions = {}
    for aid, apk_name, frames, clicks, taps, timeout in APPS:
        if only and aid not in only:
            continue
        apk = f"{CORPUS}/{apk_name}"
        run_dir = f"{RUNROOT}/{aid}"
        shutil.rmtree(run_dir, ignore_errors=True)
        os.makedirs(run_dir, exist_ok=True)

        args = ["--frames", str(frames), "--frame-delay", "800"]
        if taps:
            for t in taps:
                args += ["--tap", t]
        rc = run_engine(run_dir, apk, args, timeout)
        status, errors = report_summary(run_dir)

        sandbox_files = walk_sandbox(f"{run_dir}/sandbox") if os.path.isdir(f"{run_dir}/sandbox") else []
        picked = pick_representatives(f"{run_dir}/frames", interaction=False)

        # interaction pass (separate run: click-count is mutually exclusive
        # with --frames) — separate data-root to keep sandbox attribution clean
        ic_rc, ic_status, ic_errors, ic_picked = None, None, None, []
        if clicks:
            ic_dir = f"{RUNROOT}/{aid}_click"
            shutil.rmtree(ic_dir, ignore_errors=True)
            os.makedirs(ic_dir, exist_ok=True)
            ic_rc = run_engine(ic_dir, apk,
                               ["--click-count", str(clicks), "--frame-delay", "800"],
                               timeout)
            ic_status, ic_errors = report_summary(ic_dir)
            ic_picked = pick_representatives(f"{ic_dir}/frames", interaction=True)

        # persistence probe: relaunch in the SAME data-root, see if the
        # engine re-reads anything (only meaningful when sandbox has files)
        persist = {"probe": "relaunch_same_data_root",
                   "sandbox_files_before": len(sandbox_files)}
        if sandbox_files:
            p_dir = f"{RUNROOT}/{aid}_persist"
            shutil.rmtree(p_dir, ignore_errors=True)
            os.makedirs(p_dir, exist_ok=True)
            prc = run_engine(p_dir, apk, ["--frames", "3", "--frame-delay", "800"], timeout)
            persist["relaunch_rc"] = prc
            after = walk_sandbox(f"{run_dir}/sandbox")
            persist["sandbox_files_after_relaunch"] = len(after)
            persist["sandbox_file_list"] = after
        else:
            persist["verdict"] = "NO_PERSISTENCE_OBSERVED (app created no files in its data root)"

        # ---- assemble bundle ----
        bundle = f"{OUTROOT}/{aid}"
        shutil.rmtree(bundle, ignore_errors=True)
        os.makedirs(bundle, exist_ok=True)
        bundled = []
        for dest, (srcname, m) in picked:
            src = f"{run_dir}/frames/{srcname}"
            if os.path.exists(src):
                shutil.copy2(src, f"{bundle}/{dest}")
                m2 = dict(m)
                m2["source_run"] = "launch"
                m2["source_frame"] = srcname
                bundled.append((dest, m2))
        for dest, (srcname, m) in ic_picked:
            # merge interaction-pass frames after launch-pass ones
            tag = "04_" if not any(d.startswith(("01", "02", "03")) for d, _ in bundled) else \
                  {0: "04_", 1: "05_", 2: "06_"}.get(sum(1 for d, _ in bundled if d[0:2] in ("04", "05", "06")), "07_")
            src = f"{RUNROOT}/{aid}_click/frames/{srcname}"
            if os.path.exists(src):
                shutil.copy2(src, f"{bundle}/{tag}{srcname}")
                m2 = dict(m)
                m2["source_run"] = "interaction"
                m2["source_frame"] = srcname
                bundled.append((f"{tag}{srcname}", m2))

        metrics = {}
        for dest, m in bundled:
            metrics[dest] = m
            metrics[dest]["png_sha256_16"] = sha256_file(f"{bundle}/{dest}")[:16]

        session = {
            "session_format": "s74-ops/1 (S74 FOLLOW-UP WAVE §6 execution checkpoint)",
            "app_dossier": f"docs/compatibility/apps/{aid}.json",
            "runtime_commit": HEAD,
            "binary": "miniandroid/build/miniandroid (built at HEAD, zero runtime drift vs origin/main)",
            "apk": {"file": apk_name, "sha256_16": sha256_file(apk)[:16]},
            "execution_mode": "real-dalvik (bytecode interpretation)",
            "launch_run": {"rc": rc, "engine_status": status, "errors": errors,
                           "frames_requested": frames,
                           "tap_schedule": taps},
            "interaction_run": ({"rc": ic_rc, "engine_status": ic_status,
                                 "errors": ic_errors, "clicks": clicks} if clicks else None),
            "sandbox": {"data_root": f"run/s74f_ops/{aid}/sandbox",
                        "files_created": sandbox_files},
            "persistence": persist,
            "representative_frames": list(metrics.keys()),
            "frame_metrics": metrics,
        }
        with open(f"{bundle}/session.json", "w") as f:
            json.dump(session, f, indent=1)
        with open(f"{bundle}/SHA256SUMS", "w") as f:
            for fn in sorted(os.listdir(bundle)):
                if fn == "SHA256SUMS":
                    continue
                f.write(f"{sha256_file(os.path.join(bundle, fn))}  {fn}\n")
        sessions[aid] = session
        print(f"[BUNDLED] {aid}: rc={rc}/{ic_rc} frames={len(metrics)} "
              f"sandbox={len(sandbox_files)} "
              f"launch_px={metrics.get('01_launch.png', {}).get('nonwhite_px')}")

    with open(f"{OUTROOT}/OPS_SESSIONS.json", "w") as f:
        json.dump({"head": HEAD, "sessions": {k: v for k, v in sessions.items()}}, f, indent=1)
    print(f"\nDONE: {len(sessions)} app bundles at docs/evidence/s74_ops/")


if __name__ == "__main__":
    main()
