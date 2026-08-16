#!/usr/bin/env python3
"""EXP-042: Memory profiling harness.

Runs the MiniAndroid binary against the Telegram APK, samples RSS every 5 seconds,
and prints a final report. Used to identify which phase consumes memory.
"""
import subprocess
import time
import sys
import os

APK = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk"
BIN = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/build_exp042/miniandroid_exp042"
OUT = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp042_memprobe"

os.makedirs(OUT, exist_ok=True)
# Clean stale logs
for f in os.listdir(OUT):
    try: os.remove(os.path.join(OUT, f))
    except: pass

log_path = os.path.join(OUT, "run.log")
log = open(log_path, "wb")

print(f"[probe] launching {BIN}")
print(f"[probe] log: {log_path}")

proc = subprocess.Popen(
    [BIN, APK, OUT],
    stdout=log, stderr=subprocess.STDOUT, bufsize=0
)

rss_samples = []
start = time.time()
try:
    while True:
        if proc.poll() is not None:
            break
        try:
            with open(f"/proc/{proc.pid}/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        rss_kb = int(line.split()[1])
                        rss_samples.append((time.time() - start, rss_kb))
                        break
        except (FileNotFoundError, ProcessLookupError):
            break
        time.sleep(5)
        elapsed = time.time() - start
        if elapsed > 120:
            print(f"[probe] 120s elapsed, killing")
            proc.kill()
            break
finally:
    log.close()

print(f"\n[probe] exit_code={proc.returncode}")
print(f"[probe] RSS samples ({len(rss_samples)}):")
print(f"  t(s)   RSS(MB)")
for t, kb in rss_samples:
    print(f"  {t:5.1f}   {kb/1024:7.1f}")

# Inspect log for last meaningful line
print(f"\n[probe] last 25 log lines:")
with open(log_path) as f:
    lines = f.readlines()
    for ln in lines[-25:]:
        print(f"  {ln.rstrip()}")
