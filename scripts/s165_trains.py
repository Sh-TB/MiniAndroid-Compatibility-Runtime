#!/usr/bin/env python3
"""s165_trains.py — S165: the 10-train campaign (5 dooz + 5 Telegram).

User directive: bring 5 dooz trains and 5 Telegram trains to destination,
10 verified achievements, apps must LOAD FASTER and run LIGHTER.

Trains T1-T3 (Telegram baseline / provider platform-skip / app-data seed)
and D1-D2 (dooz face-inert baseline / composite color census) are already
recorded in evidence/s164_trains/*.json — formalized into the S165 ledger
by t4_formalize() (no re-run; reuse law).

This script's phases (argv[1]):
  d3_probe    D3 — dooz 60s on the standing seedskip bin with HALT_HISTO:
              which frames present vs keep-prev, what the Lt4 frames do,
              where the dark cover wins. Decides the composite surgery.
  t5_ab       T5 — Telegram speed/weight A/B: S163-main-bin (no env) x2 vs
              S164-seedskip-bin (seed+skip) x2, RSS monitor thread, wall,
              frames, api calls, app pixels -> the faster/lighter numbers.
  t4_formalize T4 — extract boot-depth evidence from the existing
              run_s164_gates/tg_deep + tg_train rows into the S165 ledger.
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s154_awaitup_gate as g

EVID = BASE / "evidence/s165_trains"
EVID.mkdir(parents=True, exist_ok=True)
OUT = BASE / "run_s165_trains"
OUT.mkdir(parents=True, exist_ok=True)

BIN_MAIN = BASE / "upload/_ma_local_backup/miniandroid_main_w5merged_edfb7760_512517269d9634a1.bin"
BIN_SEED = BASE / "upload/_ma_local_backup/miniandroid_s164_trains_seedskip_1cb76138897a22d2.bin"

TG_APK = BASE / "upload/telegram_official.apk"
TG_PKG = "org.telegram.messenger.web"
TG_STORE = BASE / "run_s163_telegram/store_telegram/data"

DOOZ_APK = BASE / "upload/canonical_apks/dooz_23_toplevel.apk"
DOOZ_PKG = "io.github.yamin8000.dooz"
DOOZ_STORE = BASE / "run_s163_dooz/store_dooz/data"


def sha16(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def ensure_store(apk, store, bin_path, pkg):
    """Fresh install when the sandbox recycle wiped the run store.
    The S160 lesson: --data-root must be the full store dir; the engine
    appends /data itself."""
    marker = store / "data" / "app" / pkg / "base.apk"
    if marker.exists():
        return True
    store.mkdir(parents=True, exist_ok=True)
    print(f"[install] {pkg} -> {store} (bin {sha16(bin_path)})")
    r = subprocess.run([str(bin_path), "install", str(apk), "--data-root",
                        str(store)], capture_output=True, timeout=600)
    ok = marker.exists()
    print(f"[install] {'OK' if ok else 'FAIL'} "
          f"{(r.stderr or b'')[-200:].decode(errors='replace')}")
    return ok


def save(name, row):
    out = EVID / name
    rows = {}
    if out.exists():
        try:
            rows = json.load(open(out))
        except Exception:
            rows = {}
    rows.update(row)
    json.dump(rows, open(out, "w"), indent=1, default=str)
    print("evidence ->", out)


# ── RSS monitor (s158 pattern; skips teardown rss==0 samples) ───────────
class RSSMonitor:
    def __init__(self, pid, interval=0.25):
        self.pid = pid
        self.interval = interval
        self.peak = 0
        self.last = 0
        self.samples = []
        self._stop = threading.Event()

    def _loop(self):
        while not self._stop.is_set():
            try:
                with open(f"/proc/{self.pid}/status") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            kb = int(line.split()[1])
                            if kb > 0:  # teardown samples are 0 — skip
                                mb = kb / 1024.0
                                self.last = mb
                                self.peak = max(self.peak, mb)
                                self.samples.append((time.time(), mb))
            except (FileNotFoundError, ProcessLookupError):
                break
            except Exception:
                break
            self._stop.wait(self.interval)

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self._stop.set()
        time.sleep(0.1)


# ── D3 probe: dooz 60s, which frame presents and why ────────────────────
def d3_probe(seconds=60):
    clean = {k: os.environ.pop(k, None) for k in
             ("MINIANDROID_APP_DATA_SEED", "MINIANDROID_PROVIDER_SKIP",
              "MINIANDROID_SETCOLOR_TRACE", "MINIANDROID_S109_BITMAP")}
    os.environ["MINIANDROID_HALT_HISTO"] = "1"
    g.BIN = BIN_SEED
    g.OUT = OUT
    assert ensure_store(DOOZ_APK, OUT / "store_dooz", BIN_SEED, DOOZ_PKG), \
        "dooz install failed"
    DOOZ_STORE = OUT / "store_dooz"
    rundir = OUT / "dooz_d3probe"
    console = OUT / "dooz_d3probe_console.log"
    cmd = [str(BIN_SEED), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(DOOZ_STORE), "-o", str(rundir),
           "--max-seconds", str(seconds), "--frames", "12",
           "--trace", "--package", DOOZ_PKG]
    print(f"== D3 probe dooz {seconds}s HALT_HISTO (bin {sha16(BIN_SEED)}) ==")
    t0 = time.time()
    with open(console, "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       timeout=seconds + 120, env=dict(os.environ))
    wall = round(time.time() - t0, 1)
    text = console.read_text(errors="replace")
    row = {
        "bin": sha16(BIN_SEED), "wall_s": wall,
        "settle": wall < seconds - 5,
        "face": sha16(rundir / "screenshot.png")
        if (rundir / "screenshot.png").exists() else None,
        "f298_keep_rows": len(re.findall(r"\[F298-KEEP\]", text)),
        "f351_erase_rows": len(re.findall(r"F351.*CLEAR|CLEAR.*erase", text)),
        "c013_replayed": re.findall(
            r"\[C013-CUSTOMVIEW\] onDraw replayed (\d+) ops for (\S+);", text),
        "c013_unrendered": len(re.findall(
            r"\[C013-CUSTOMVIEW\] unrendered custom view", text)),
        "exp092_last3": re.findall(r"\[EXP092-COPY\] fb has \d+ non-white",
                                   text)[-3:],
        "halt_loop_rows": re.findall(r"HALT: Infinite loop[^\n]{0,90}", text)[:5],
        "halt_loop_count": len(re.findall(r"HALT: Infinite loop", text)),
        "wall_halt_rows": len(re.findall(r"HALT: Wall-clock", text)),
        "histo_frames": re.findall(r"\[HALT-HISTO\] frame=(\S+) pc=(\S+)",
                                   text)[:8],
        "verdict_timeline": re.findall(r"FRAME_ANALYSIS state=(\S+)", text),
        "frames_rendered": re.findall(r"Frames Rendered: (\d+)", text),
        "winbg": re.findall(r"\[EXT01-WINBG\][^\n]{0,90}", text)[-2:],
        "awt_present_rows": len(re.findall(r"frame presented|PRESENT", text)),
    }
    save("S165_D3_PROBE.json", row)
    print(json.dumps({k: row[k] for k in
                      ("wall_s", "settle", "face", "f298_keep_rows",
                       "halt_loop_count", "c013_replayed",
                       "verdict_timeline", "frames_rendered")}, indent=1))
    for k, v in clean.items():
        if v is not None:
            os.environ[k] = v
    os.environ.pop("MINIANDROID_HALT_HISTO", None)
    return row


# ── T5: Telegram speed/weight A/B ────────────────────────────────────────
def tg_run(tag, bin_path, envs, max_seconds=90):
    store = OUT / ("store_tg_base" if "base" in tag else "store_tg_fix")
    assert ensure_store(TG_APK, store, bin_path, TG_PKG), \
        f"telegram install failed for {tag}"
    rundir = OUT / tag
    console = OUT / f"{tag}_console.log"
    env = dict(os.environ)
    for k in ("MINIANDROID_APP_DATA_SEED", "MINIANDROID_PROVIDER_SKIP"):
        env.pop(k, None)
    env.update(envs)
    cmd = [str(bin_path), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(max_seconds), "--frames", "8",
           "--trace", "--package", TG_PKG]
    proc = subprocess.Popen(cmd, stdout=open(console, "w"),
                            stderr=subprocess.STDOUT, env=env)
    mon = RSSMonitor(proc.pid)
    mon.start()
    t0 = time.time()
    proc.wait(timeout=max_seconds + 120)
    wall = round(time.time() - t0, 1)
    mon.stop()
    text = console.read_text(errors="replace")
    row = {
        "tag": tag, "bin": sha16(bin_path), "env": envs, "wall_s": wall,
        "rss_peak_mb": round(mon.peak, 1),
        "rss_final_mb": round(mon.last, 1),
        "uncaught": len(re.findall(r"UNCAUGHT", text)),
        "verdict": re.findall(r"FRAME_ANALYSIS state=(\S+)", text)[-1:]
        or None,
        "frames_rendered": re.findall(r"Frames Rendered: (\d+)", text),
    }
    ts = rundir / "trace_summary.json"
    if ts.exists():
        try:
            s = json.load(open(ts))
            fa = s.get("frame_analysis") or {}
            row["app_draw_ops"] = fa.get("app_draw_ops")
            row["app_owned_pixels"] = fa.get("app_owned_pixels")
            row["final_state"] = (s.get("lifecycle") or {}).get("final_state")
        except Exception:
            pass
    at = rundir / "api_trace.json"
    if at.exists():
        try:
            row["api_calls"] = json.load(open(at)).get("total_calls")
        except Exception:
            pass
    return row


def t5_ab():
    print("== T5 Telegram speed/weight A/B (2x baseline vs 2x fixed) ==")
    rows = []
    for tag, b, e in (
        ("t5_base_1", BIN_MAIN, {}),
        ("t5_base_2", BIN_MAIN, {}),
        ("t5_fix_1", BIN_SEED,
         {"MINIANDROID_APP_DATA_SEED": "1",
          "MINIANDROID_PROVIDER_SKIP":
              "FirebaseInitProvider,MlKitInitProvider"}),
        ("t5_fix_2", BIN_SEED,
         {"MINIANDROID_APP_DATA_SEED": "1",
          "MINIANDROID_PROVIDER_SKIP":
              "FirebaseInitProvider,MlKitInitProvider"}),
    ):
        r = tg_run(tag, b, e)
        rows.append(r)
        print(json.dumps(r))
        save("S165_T5_SPEEDWEIGHT.json", {tag: r})
    summary = {
        "runs": rows,
        "baseline_median_wall": sorted(r["wall_s"] for r in rows
                                       if r["tag"].startswith("t5_base"))[1],
        "fixed_median_wall": sorted(r["wall_s"] for r in rows
                                    if r["tag"].startswith("t5_fix"))[1],
        "baseline_uncaught_total": sum(r["uncaught"] for r in rows
                                       if r["tag"].startswith("t5_base")),
        "fixed_uncaught_total": sum(r["uncaught"] for r in rows
                                    if r["tag"].startswith("t5_fix")),
        "baseline_rss_peak_median": sorted(r["rss_peak_mb"] for r in rows
                                           if r["tag"].startswith("t5_base"))[1],
        "fixed_rss_peak_median": sorted(r["rss_peak_mb"] for r in rows
                                        if r["tag"].startswith("t5_fix"))[1],
    }
    save("S165_T5_SPEEDWEIGHT.json", {"summary": summary})
    print(json.dumps(summary, indent=1))
    return summary


# ── T4: formalize boot depth from existing S164 runs ────────────────────
def t4_formalize():
    s164 = json.load(open(BASE / "evidence/s164_trains/S164_GATES.json"))
    base = json.load(open(
        BASE / "evidence/s164_trains/S164_TG_BASELINE.json"))
    deep = json.load(open(
        BASE / "run_s164_gates/tg_deep/trace_summary.json"))
    lc = json.load(open(
        BASE / "run_s164_gates/tg_deep/lifecycle_trace.json"))
    if not isinstance(lc, dict):
        lc = {}
    fa = deep.get("frame_analysis") or {}
    row = {
        "method": "extraction from committed S164 runs (reuse law; no re-run)",
        "baseline_train": {
            "tag": "tg_baseline_90s (bin 512517269d9634a1, no env)",
            "verdict": base.get("verdict"), "wall_s": base.get("wall_s"),
            "uncaught": base.get("uncaught"),
            "uncaught_l9j": base.get("uncaught_l9j"),
            "frames": base.get("frames_rendered"),
        },
        "t2_t3_train": {
            "tag": "tg_train_90s (bin 1cb76138897a22d2, seed+skip)",
            "verdict": s164["tg_train"].get("verdict"),
            "wall_s": s164["tg_train"].get("wall_s"),
            "uncaught": s164["tg_train"].get("uncaught"),
            "uncaught_l9j": s164["tg_train"].get("uncaught_l9j"),
            "uncaught_tl_autodl": s164["tg_train"].get("uncaught_tl_autodl"),
            "skip_providers": [
                r.split("PLATFORM-SKIP ")[1].split(" ")[0]
                for r in s164["tg_train"].get("skip_rows", [])],
        },
        "t4_boot_depth": {
            "tag": "tg_deep (150s, 24 frames, seed+skip)",
            "final_state": lc.get("final_state"),
            "transitions": [
                f"{t['from']}->{t['to']} ({t['reason'][:60]})"
                for t in lc.get("transitions", [])],
            "frames_captured": deep.get("events_total") and
            len(deep.get("last_events") or []),
            "app_draw_ops": fa.get("app_draw_ops"),
            "app_owned_pixels": fa.get("app_owned_pixels"),
            "content_bounds": fa.get("content_bounds"),
            "last_exception": deep.get("last_exception"),
            "severity_census": deep.get("severity_census"),
        },
    }
    save("S165_T4_BOOTDEPTH.json", row)
    print(json.dumps(row, indent=1)[:1800])
    return row


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"
    if phase in ("all", "d3_probe"):
        d3_probe()
    if phase in ("all", "t5_ab"):
        t5_ab()
    if phase in ("all", "t4_formalize"):
        t4_formalize()
