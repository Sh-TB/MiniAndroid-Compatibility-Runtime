#!/usr/bin/env python3
"""W8 shared-library dev architecture (isolated build_dev_so/, production untouched).
Volatile dalvik set (7 TUs) recompiled -fPIC -> libminiandroid_dalvik.so;
stable runtime + quickjs + thunk stay STATIC in test exes and miniandroid_dev.
Engine edits then relink only the small .so — test exes never relink.
Also runs Experiment A: --strip-debug static test relink for comparison.
Rollback: rm -rf build_dev_so/"""
import subprocess, re, os, time, resource, sys

os.chdir("/home/z/my-project/miniandroid")
BD = "build_dev_so"
os.makedirs(f"{BD}/tests", exist_ok=True); os.makedirs(f"{BD}/objects", exist_ok=True)

def sh(cmd, timeout=900):
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return time.monotonic() - t0, r.returncode, (r.stdout + r.stderr)

def timed(label, cmd):
    w, rc, out = sh(cmd)
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
    print(f"{label}: rc={rc} {w:.2f}s (children_peak_rss<={rss:.0f}MB)")
    if rc != 0: print("  FAIL tail:", out[-600:].replace("\n", "\n  "))
    return w, rc, out

mk = sh("make --no-print-directory -pn 2>/dev/null")[2]
def mvar(name):
    m = re.search(rf"^{name} = (.*)$", mk, re.M)
    return m.group(1).strip() if m else ""
CXXFLAGS = mvar("CXXFLAGS"); INCLUDES = mvar("INCLUDES")
JSONI = "-Ithird_party/nlohmann_json/include"
LIBS = mvar("LIBS"); FONTS = mvar("FONTS_LIBS")
RL = subprocess.run("find third_party -name 'librlottie.a' | head -1", shell=True,
                    capture_output=True, text=True).stdout.strip()
FONTS = FONTS.replace("$(RLOTTIE_DIR)/build/src/librlottie.a", RL).replace(RLOTTIE_RAW, RL) if False else FONTS
FONTS = re.sub(r"\$\(RLOTTIE_DIR\)\S*", RL, FONTS)
print(f"rlottie: {RL} | FONTS={FONTS}")

manifest = [l.strip() for l in open("core_sources.manifest") if l.strip() and not l.startswith("#")]
allobjs = [f"build/{l[4:-4]}.o" for l in manifest if os.path.exists(f"build/{l[4:-4]}.o")]
PARTS = ["dex/dalvik_engine_core", "dex/dalvik_engine_invoke", "dex/dalvik_interpreter",
         "dex/dalvik_opcodes", "dex/dalvik_opcodes_invoke", "dex/dalvik_bridge",
         "dex/dalvik_engine_tail"]
SRC = {p: f"src/{p}.cpp" for p in PARTS}
dobjs = [f"build/{p}.o" for p in PARTS]
robs = [o for o in allobjs if o not in set(dobjs)]
qobjs = subprocess.run("ls build/quickjs/*.o", shell=True, capture_output=True,
                       text=True).stdout.split()
thunk = "build/jni/native_thunk.o"
print(f"objects: dalvik={len(dobjs)} rest={len(robs)} quickjs={len(qobjs)} thunk={os.path.exists(thunk)}")

# ---- 1. one-time: PIC recompile of the 7 volatile TUs (same flags + -fPIC;
#         interpreter keeps its inline-budget params, bridge keeps -Og) ----
pic = []
for p in PARTS:
    out = f"{BD}/objects/{os.path.basename(p)}.o"
    if os.path.exists(out):
        pic.append(out); continue
    extra = "--param inline-unit-growth=15 --param large-function-growth=120" if p.endswith("interpreter") else ""
    opt = "-Og" if p.endswith("bridge") else "-O2"
    w, rc, _ = timed(f"PIC compile {p}",
        f"g++ {CXXFLAGS.replace('-O2', opt)} -g0 -fPIC {extra} {INCLUDES} {JSONI} "
        f"-c -o {out} {SRC[p]}")
    if rc == 0: pic.append(out)
    else: sys.exit("PIC compile failed — rollback: rm -rf build_dev_so")

# ---- 2. libminiandroid_dalvik.so ----
w_so, rc_so, _ = timed("link libminiandroid_dalvik.so",
    f"g++ -shared -o {BD}/libminiandroid_dalvik.so {' '.join(pic)} "
    f"-Wl,-soname,libminiandroid_dalvik.so -Wl,-rpath,$ORIGIN {LIBS}")

# ---- 3. test exes: static stable runtime + dynamic dalvik ----
STATIC = " ".join(robs + qobjs + [thunk])
TESTS = ["simple_test", "s130_laws_test", "gp582_engine_probe_test"]
tw = 0
for t in TESTS:
    w, rc, _ = timed(f"link test {t} (static+so)",
        f"g++ {CXXFLAGS} {INCLUDES} {JSONI} -o {BD}/tests/{t} tests/{t}.cpp {STATIC} "
        f"-L{BD} -lminiandroid_dalvik -Wl,-rpath,'\$$ORIGIN/..' {LIBS} {FONTS}")
    tw += w

# ---- Experiment A: --strip-debug on the CURRENT full-static link (gp582) ----
_, _, nline = sh("make --no-print-directory -n -B build/tests/gp582_engine_probe_test 2>/dev/null | grep ' -o build/tests/gp582' | head -1")
A_w, A_rc, _ = timed("ExpA: gp582 static link --strip-debug",
    nline.strip().replace("-o build/tests/gp582_engine_probe_test",
                          f"-o {BD}/gp582_stripped -Wl,--strip-debug"))
B_w, B_rc, _ = timed("ExpA-ctrl: gp582 static link full debug",
    nline.strip().replace("-o build/tests/gp582_engine_probe_test", f"-o {BD}/gp582_full"))

# ---- 4. miniandroid_dev main binary ----
_, _, mainline = sh("make --no-print-directory -n -B build/miniandroid 2>/dev/null | grep ' -o build/miniandroid' | head -1")
objs_in_ml = re.findall(r"build/\S+\.o", mainline)
core_set = set(allobjs) | set(qobjs) | {thunk}
noncore = [o for o in objs_in_ml if o not in core_set]
print(f"main link: {len(objs_in_ml)} objects, non-core kept {len(noncore)}: {noncore[:4]}")
w3, rc3, _ = timed("link miniandroid_dev",
    f"g++ {CXXFLAGS} {INCLUDES} {JSONI} -o {BD}/miniandroid_dev {' '.join(noncore)} {STATIC} "
    f"-L{BD} -lminiandroid_dalvik -Wl,-rpath,$ORIGIN {LIBS} {FONTS}")

# ---- 5. battery on the dev .so path ----
w4, rc4, out4 = timed("battery (dev .so path)",
    f"{BD}/tests/simple_test && {BD}/tests/s130_laws_test && {BD}/tests/gp582_engine_probe_test")
print(f"battery PASS lines: {out4.count('PASS')}")
sizes = sh(f"du -sh {BD} && ls -la {BD}/*.so {BD}/tests/* {BD}/miniandroid_dev {BD}/gp582_stripped {BD}/gp582_full 2>/dev/null")[2]
print(sizes)
print("SUMMARY:", {"pic_compile_s": None, "dalvik_so_s": round(w_so, 2),
      "test_links_s": round(tw, 2), "expA_strip_s": round(A_w, 2), "expA_full_s": round(B_w, 2),
      "main_dev_s": round(w3, 2), "battery_s": round(w4, 2), "battery_rc": rc4})
