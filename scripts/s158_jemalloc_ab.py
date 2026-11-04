#!/usr/bin/env python3
"""s158_jemalloc_ab.py — S158: READY-MADE allocator swap vs the dooz spin.

User law: don't reinvent the wheel — use what exists. glibc ENV KNOBS were
REJECTED in S157 (same face, wall -0.6%); that tests glibc's tuning, NOT a
different allocator. jemalloc 5.3.0 is ALREADY INSTALLED on this VM
(/usr/lib/x86_64-linux-gnu/libjemalloc.so.2) and is a proven drop-in for the
exact observed pathology: massive small-object churn (unordered_map nodes,
CowStr, std::string) where glibc keeps growing RSS (+2MB/s, minor faults
470-800/s during the spin) instead of reusing freed bins. Zero engine code
changes — LD_PRELOAD only, byte-inert by construction (same contents, same
values; faces must not depend on heap addresses).

Arms (dooz E5 no-tap, fresh store each, binary 908d5ba6 insurance copy):
  C  control, no preload         -> expect standing spin face 11a38a5a
  J1 LD_PRELOAD jemalloc, defaults (reuse-friendly tcache bins)
  J2 LD_PRELOAD jemalloc + MALLOC_CONF=background_thread:true (async purge,
     decay defaults kept so dirty pages stay reusable)

Success criteria:
  face == 851cc1761a1dfcdf (board renders)   -> dooz MOVED: run tap probe next
  face == 11a38a5aeeff45a6, wall moved >=20% -> throughput lever confirmed
  face == 11a38a5aeeff45a6, wall flat, fault curve collapsed -> churn link
     partially broken (allocator reuses) but live-set growth is the residual
  any other face                             -> instability, investigate

Per-arm /proc monitor: RSS + minflt/majflt sampled 2s -> the S156 fault-churn
correlate, measured inside the SAME run (not inferred).

Usage: python3 scripts/s158_jemalloc_ab.py C|J1|J2|collect
"""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s155_dooz_placement as s155

OUT = BASE / "run_s158_jemalloc"   # run/ is root-owned (infra artifact)
EVID = BASE / "evidence/s156_record_loop"
OUT.mkdir(parents=True, exist_ok=True)
EVID.mkdir(parents=True, exist_ok=True)

# S157-B verified artifact (insurance copy), NOT the in-progress rebuild
BIN = BASE / "upload/_ma_local_backup/miniandroid_s157b_gated_908d5ba61aa62485.bin"
JEM = "/usr/lib/x86_64-linux-gnu/libjemalloc.so.2"

ARMS = {
    "C_rebuild": {},
    "J1_je_default": {"LD_PRELOAD": JEM},
    "J2_je_bgthread": {"LD_PRELOAD": JEM,
                       "MALLOC_CONF": "background_thread:true"},
}


def monitor(pid, stop, samples):
    """sample /proc RSS + faults every 2s until stop"""
    while not stop.is_set():
        try:
            stat = Path(f"/proc/{pid}/stat").read_text()
            fields = stat.rsplit(")", 1)[1].split()
            minflt = int(fields[7])       # field 10 overall (1-indexed)
            majflt = int(fields[9])       # field 12 overall
            status = Path(f"/proc/{pid}/status").read_text()
            rss = 0
            for ln in status.splitlines():
                if ln.startswith("VmRSS:"):
                    rss = int(ln.split()[1])  # kB
                    break
            samples.append({"t": round(time.time(), 1), "rss_kb": rss,
                            "minflt": minflt, "majflt": majflt})
        except (FileNotFoundError, ProcessLookupError, IndexError):
            break
        stop.wait(2.0)


def run_arm(tag, extra_env, max_seconds=110, frames=30, taps=None):
    store = OUT / f"store_{tag}/data"
    rundir = OUT / tag
    console = OUT / f"{tag}_console.log"
    env = dict(os.environ)
    env.pop("MINIANDROID_S155_APPLY", None)
    env.update(extra_env)
    # fresh store per arm (allocator behavior depends on heap history)
    subprocess.run(["rm", "-rf", str(store), str(rundir)], check=False)
    inst = subprocess.run(
        [str(BIN), "install", str(s155.DOOZ_APK), "--data-root", str(store)],
        capture_output=True, timeout=300)
    if inst.returncode != 0:
        print("INSTALL FAIL", inst.stderr[-300:])
        return None
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(max_seconds), "--frames", str(frames),
           "--trace", "--package", "io.github.yamin8000.dooz"]
    for t in (taps or []):
        cmd += ["--tap", t]
    samples = []
    stop = threading.Event()
    t0 = time.time()
    killed = False
    with open(console, "w") as cf:
        proc = subprocess.Popen(cmd, stdout=cf, stderr=subprocess.STDOUT,
                                env=env)
        mon = threading.Thread(target=monitor, args=(proc.pid, stop, samples))
        mon.start()
        try:
            proc.wait(timeout=max_seconds + 90)
        except subprocess.TimeoutExpired:
            killed = True
            proc.kill()
            proc.wait()
        stop.set()
        mon.join()
    wall = round(time.time() - t0, 1)
    text = console.read_text(errors="replace")
    row = s155.analyze(tag, taps, wall, killed, text, rundir)
    # fault-churn correlate from the SAME run
    if len(samples) >= 3:
        dt = samples[-1]["t"] - samples[0]["t"]
        dmin = samples[-1]["minflt"] - samples[0]["minflt"]
        row["rss_start_kb"] = samples[0]["rss_kb"]
        row["rss_end_kb"] = samples[-1]["rss_kb"]
        row["rss_grow_mb_s"] = round(
            (samples[-1]["rss_kb"] - samples[0]["rss_kb"]) / 1024.0 / dt, 3)
        row["minflt_per_s"] = round(dmin / dt, 1)
        row["majflt"] = samples[-1]["majflt"]
    row["arm_env"] = extra_env
    row["binary"] = "908d5ba61aa62485 (insurance)"
    print(f"[{tag}] verdict={row['verdict']} face={row['screenshot_face']} "
          f"wall={wall}s rss_grow={row.get('rss_grow_mb_s')}MB/s "
          f"minflt/s={row.get('minflt_per_s')}")
    return row


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "C"
    # reuse s155's analyze; make its OUT match ours for artifact paths
    s155.OUT = OUT
    rows_path = EVID / "S158_JEMALLOC_AB.json"
    rows = json.loads(rows_path.read_text()) if rows_path.exists() else {}
    wanted = list(ARMS) if mode == "all" else (
        ["C_rebuild"] if mode == "C" else
        [k for k in ARMS if k.startswith(mode)])
    for tag in wanted:
        rows[tag] = run_arm(tag, ARMS[tag])
        json.dump(rows, open(rows_path, "w"), indent=1, default=str)
        print(f"-> {rows_path}")
    # classification
    for tag, row in rows.items():
        face = (row or {}).get("screenshot_face")
        cls = ("BOARD_RENDERED (dooz MOVED)" if face == s155.PIN_DOOZ else
               "SPIN_PERSISTS" if face == "11a38a5aeeff45a6" else
               "UNEXPECTED_FACE")
        print(f"{tag}: {cls}")
    if mode == "all":
        print("DONE")


if __name__ == "__main__":
    main()
