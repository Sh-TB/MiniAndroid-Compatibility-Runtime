#!/usr/bin/env python3
"""W6 Phase 1: per-TU compile memory profile (measured, not estimated).
Compiles each TU with its EXACT make flags to a scratch object, records
wall/CPU/peak-RSS via RUSAGE_CHILDREN in a fresh interpreter per TU,
then nm/size function stats and .d header-dep counts.
Resumable: checkpoint per TU into evidence/wave6/w6_memory_profile.json.
Usage: w6_tu_profile.py dalvik | rest | fanout | report
"""
import json, os, re, subprocess, sys, glob

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave6"
PROF = "/tmp/w6prof"
os.makedirs(EV, exist_ok=True); os.makedirs(PROF, exist_ok=True)
RESF = f"{EV}/w6_memory_profile.json"
RES = json.load(open(RESF)) if os.path.exists(RESF) else {}

MEASURE = '''
import subprocess, resource, sys, time
t0 = time.monotonic()
r = subprocess.run(sys.argv[1:], capture_output=True, timeout=540)
dt = time.monotonic() - t0
ru = resource.getrusage(resource.RUSAGE_CHILDREN)
cpu = ru.ru_utime + ru.ru_stime
print(f"RESULT {r.returncode} {dt:.2f} {ru.ru_maxrss // 1024} {cpu:.2f}")
'''

def measure(cmd):
    r = subprocess.run([sys.executable, "-I", "-c", MEASURE] + cmd,
                       capture_output=True, text=True, timeout=600)
    lines = [l for l in r.stdout.splitlines() if l.startswith("RESULT")]
    if not lines:
        return None, 0.0, 0, 0.0
    _, rc, dt, peak, cpu = lines[-1].split()
    return int(rc), float(dt), int(peak), float(cpu)

def all_compile_commands():
    mk = subprocess.run(["make", "--no-print-directory", "-n", "-B", "all"],
                        capture_output=True, text=True, timeout=300).stdout
    cmds = {}
    for l in mk.splitlines():
        l = l.strip()
        if " -c -o build/" in l and l.startswith("g++"):
            m = re.search(r"-o (\S+) (\S+)$", l)
            if m:
                cmds[m.group(2)] = l  # source -> full command
    return cmds

def profile_tu(src, cmd):
    name = os.path.basename(src)[:-4]
    if name in RES.get("tus", {}):
        print(f"  {name}: done, skip"); return
    out = f"{PROF}/{name}.o"
    pcmd = re.sub(r"-o \S+ ", f"-o {out} ", cmd) + f" 2>{PROF}/{name}.err"
    rc, dt, peak, cpu = measure(["bash", "-c", pcmd])
    rec = {"source": src, "rc": rc, "wall_s": dt, "peak_mb": peak, "cpu_s": cpu,
           "flags": re.sub(r"-I\S+", "-I<inc>", cmd.split("-c")[0]).strip()}
    try:
        rec["obj_bytes"] = os.path.getsize(out)
        sz = subprocess.run(["size", out], capture_output=True, text=True).stdout
        m = re.search(r"TEXT\s+(\d+)", sz)
        rec["text_bytes"] = int(m.group(1)) if m else None
        nm = subprocess.run(["nm", "--print-size", "--size-sort", "-C", out],
                            capture_output=True, text=True).stdout
        syms = [l for l in nm.splitlines() if l.strip()]
        rec["sym_count"] = len(syms)
        top = []
        for l in syms[-6:]:
            p = l.split()
            if len(p) >= 4:
                top.append({"bytes": int(p[0], 16), "name": p[3][:70]})
        rec["top_functions"] = top[::-1]
    except Exception as e:
        rec["analysis_error"] = str(e)[:80]
    lines = 0
    try:
        lines = sum(1 for _ in open(src, errors="replace"))
    except Exception:
        pass
    rec["source_lines"] = lines
    dd = f"build/{name}.d"
    alt = glob.glob(f"build/**/{name}.d", recursive=True)
    if os.path.exists(dd):
        deps = open(dd).read().split()
        rec["header_dep_count"] = len(set(d for d in deps[1:] if d.endswith((".h", ".hpp"))))
    elif alt:
        deps = open(alt[0]).read().split()
        rec["header_dep_count"] = len(set(d for d in deps[1:] if d.endswith((".h", ".hpp"))))
    RES.setdefault("tus", {})[name] = rec
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"  {name}: rc={rc} wall={dt:.1f}s cpu={cpu:.1f}s peak={peak}MB "
          f"lines={lines} obj={rec.get('obj_bytes', '?')}")

which = sys.argv[1] if len(sys.argv) > 1 else "dalvik"
cmds = all_compile_commands()
print(f"{len(cmds)} compile commands discovered")

DALVIK_PARTS = ["dalvik_engine_core", "dalvik_engine_invoke", "dalvik_interpreter",
                "dalvik_opcodes", "dalvik_opcodes_invoke", "dalvik_bridge",
                "dalvik_engine_tail"]
if which == "dalvik":
    for n in DALVIK_PARTS:
        src = next((s for s in cmds if s.endswith(f"/{n}.cpp")), None)
        if src:
            profile_tu(src, cmds[src])
        else:
            print(f"  {n}: NOT FOUND in compile commands")
    # interpreter flag experiments (OBSERVED, temp objects only)
    base = next(c for s, c in cmds.items() if "dalvik_interpreter" in s)
    res = RES.setdefault("experiments", {})
    for tag, extra in [("interp_fno_ipa_cp", "-fno-ipa-cp"),
                       ("interp_fno_ipa_sra", "-fno-ipa-sra"),
                       ("interp_Og", "-Og")]:
        if tag in res: continue
        out = f"{PROF}/{tag}.o"
        pcmd = re.sub(r"-o \S+ ", f"-o {out} ", base) + " " + extra
        rc, dt, peak, cpu = measure(["bash", "-c", pcmd])
        res[tag] = {"rc": rc, "wall_s": dt, "peak_mb": peak, "cpu_s": cpu}
        json.dump(RES, open(RESF, "w"), indent=1)
        print(f"  experiment {tag}: rc={rc} wall={dt:.1f}s peak={peak}MB")
elif which == "monolith":
    base = next(c for s, c in cmds.items() if "dalvik_opcodes.cpp" in s)
    pcmd = re.sub(r"-o \S+ ", f"-o {PROF}/dalvik_engine_monolith.o ",
                  base).replace("src/dex/dalvik_opcodes.cpp", "src/dex/dalvik_engine.cpp")
    if "dalvik_engine_monolith" not in RES.get("experiments", {}):
        rc, dt, peak, cpu = measure(["bash", "-c", pcmd])
        RES["experiments"]["dalvik_engine_monolith"] = {
            "rc": rc, "wall_s": dt, "peak_mb": peak, "cpu_s": cpu,
            "note": "monolithic dalvik_engine.cpp at part flags (-O2 -g0)"}
        json.dump(RES, open(RESF, "w"), indent=1)
        print(f"  monolith: rc={rc} wall={dt:.1f}s peak={peak}MB")
elif which == "rest":
    skip = set(DALVIK_PARTS)
    for s, c in sorted(cmds.items()):
        if os.path.basename(s)[:-4] in skip:
            continue
        profile_tu(s, c)
elif which == "fanout":
    fan = {}
    for df in glob.glob("build/**/*.d", recursive=True):
        obj = os.path.basename(df)[:-2]
        deps = set(d for d in open(df).read().split() if d.endswith((".h", ".hpp")))
        fan[obj] = sorted(deps)
    RES["dep_graph"] = fan
    header_fanout = {}
    for obj, deps in fan.items():
        for h in deps:
            header_fanout.setdefault(h, []).append(obj)
    RES["header_fanout"] = {h: {"objects": len(v), "list": v}
                            for h, v in sorted(header_fanout.items(),
                                               key=lambda kv: -len(kv[1]))}
    json.dump(RES, open(RESF, "w"), indent=1)
    top = list(RES["header_fanout"].items())[:10]
    for h, v in top:
        print(f"  {h}: {v['objects']} objects")
print("PROFILE STEP DONE:", which)
