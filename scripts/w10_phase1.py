#!/usr/bin/env python3
"""W10 Phase 1: compiler-time attribution for the two expensive Dalvik TUs.
Separates preprocessing / parsing / optimization+codegen / assembly via
-fsyntax-only, -E, -ftime-report x5, /usr/bin/time RSS x2, nm per-function sizes."""
import subprocess, re, json, os, time

os.chdir("/home/z/my-project/miniandroid")
os.makedirs("evidence/wave10", exist_ok=True)

def run(cmd, timeout=900):
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return time.monotonic() - t0, r.returncode, r.stdout, r.stderr

R = {"gcc": subprocess.run(["gcc", "--version"], capture_output=True, text=True).stdout.split("\n")[0],
     "gxx": subprocess.run(["g++", "--version"], capture_output=True, text=True).stdout.split("\n")[0]}

TUS = {"interpreter": "build_dev_so/objects/dalvik_interpreter.o",
       "bridge": "build_dev_so/objects/dalvik_bridge.o"}

for name, obj in TUS.items():
    out = subprocess.run(f"make --no-print-directory -n -B {obj}", shell=True,
                         capture_output=True, text=True).stdout
    lines = [l.strip() for l in out.split("\n") if " -c -o " in l]
    line = lines[0]
    E = {"cmd": line}
    # 5x full compile with -ftime-report
    reports = []
    for i in range(5):
        cmd = line.replace(f" -c -o {obj} ", f" -c -o /tmp/w10_{name}_fr{i}.o -ftime-report ")
        w, rc, so, se = run(cmd)
        blob = so + se
        phases = [l.rstrip() for l in blob.split("\n") if re.search(r":\s+\d+\.\d+\s+\(\s*\d+%\)", l)]
        tot = [l.rstrip() for l in blob.split("\n") if "TOTAL" in l]
        reports.append({"wall_s": round(w, 2), "rc": rc, "phases": phases, "total_line": tot})
    E["ftime_report_x5"] = reports
    # parse-only x2 (-fsyntax-only)
    syn = []
    for i in range(2):
        cmd = line.replace(f" -c -o {obj} ", " -fsyntax-only ").replace(" -MMD -MP", "")
        w, rc, so, se = run(cmd)
        syn.append({"wall_s": round(w, 2), "rc": rc})
    E["fsyntax_only_x2"] = syn
    # preprocessing: time + volume
    cmd = line.replace(f" -c -o {obj} ", " -E ") + " > /tmp/w10_%s_pre.i 2>/dev/null" % name
    w, rc, so, se = run(cmd)
    try:
        n = sum(1 for _ in open("/tmp/w10_%s_pre.i" % name, errors="replace"))
        b = os.path.getsize("/tmp/w10_%s_pre.i" % name)
    except OSError:
        n = b = None
    E["preprocess"] = {"wall_s": round(w, 2), "rc": rc, "lines": n, "bytes": b}
    # memory x2
    mems = []
    for i in range(2):
        cmd = "/usr/bin/time -v " + line.replace(f" -c -o {obj} ", f" -c -o /tmp/w10_{name}_m{i}.o ")
        w, rc, so, se = run(cmd)
        m = re.search(r"Maximum resident set size \(kbytes\): (\d+)", so + se)
        mems.append({"wall_s": round(w, 2), "rss_mb": int(m.group(1)) // 1024 if m else None})
    E["full_compile_mem_x2"] = mems
    # per-function sizes from existing object
    nm = subprocess.run(f"nm --print-size --size-sort -C {obj} 2>/dev/null | tail -6",
                        shell=True, capture_output=True, text=True).stdout
    E["largest_functions_nm"] = nm.strip().split("\n")
    R[name] = E
    print(f"{name}: full {[r['wall_s'] for r in reports]} syntax {[s['wall_s'] for s in syn]} "
          f"preproc {E['preprocess']} mem {mems}", flush=True)

json.dump(R, open("evidence/wave10/w10_attribution_raw.json", "w"), indent=1)
print("PHASE1 done")
