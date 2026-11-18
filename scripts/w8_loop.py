#!/usr/bin/env python3
"""W8 money benchmarks on the dev .so path + runtime proof.
1. relink tests/main with correct $ORIGIN rpath
2. battery run (LD_LIBRARY_PATH belt+suspenders)
3. interpreter edit-loop x3 (PIC compile -> .so relink -> battery run)
4. opcode edit-loop x2
5. 3 APKs on miniandroid_dev (original APKs; hash proof)"""
import subprocess, re, os, time, hashlib

os.chdir("/home/z/my-project/miniandroid")
BD = "build_dev_so"

def sh(cmd, timeout=600, env=None):
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env)
    return time.monotonic() - t0, r.returncode, (r.stdout + r.stderr)

def timed(label, cmd, env=None):
    w, rc, out = sh(cmd, env=env)
    print(f"{label}: rc={rc} {w:.2f}s")
    if rc != 0: print("  FAIL tail:", out[-500:].replace("\n", "\n  "))
    return w, rc, out

mk = subprocess.run("make --no-print-directory -pn 2>/dev/null", shell=True,
                    capture_output=True, text=True).stdout
def mvar(n):
    m = re.search(rf"^{n} = (.*)$", mk, re.M); return m.group(1).strip() if m else ""
CXXFLAGS, INCLUDES, LIBS, FONTS = mvar("CXXFLAGS"), mvar("INCLUDES"), mvar("LIBS"), mvar("FONTS_LIBS")
RL = subprocess.run("find third_party -name 'librlottie.a' | head -1", shell=True,
                    capture_output=True, text=True).stdout.strip()
FONTS = re.sub(r"\$\(RLOTTIE_DIR\)\S*", RL, FONTS) if RL else FONTS
JSONI = "-Ithird_party/nlohmann_json/include"
manifest = [l.strip() for l in open("core_sources.manifest") if l.strip() and not l.startswith("#")]
allobjs = [f"build/{l[4:-4]}.o" for l in manifest if os.path.exists(f"build/{l[4:-4]}.o")]
PARTS = ["dex/dalvik_engine_core", "dex/dalvik_engine_invoke", "dex/dalvik_interpreter",
         "dex/dalvik_opcodes", "dex/dalvik_opcodes_invoke", "dex/dalvik_bridge",
         "dex/dalvik_engine_tail"]
robs = [o for o in allobjs if o not in {f"build/{p}.o" for p in PARTS}]
STATIC = " ".join(robs) + " build/quickjs/*.o build/jni/native_thunk.o"

# 1. proper rpath relinks
TESTS = ["simple_test", "s130_laws_test", "gp582_engine_probe_test"]
tw = 0
for t in TESTS:
    w, rc, _ = timed(f"relink {t} ($ORIGIN)",
        f"g++ {CXXFLAGS} {INCLUDES} {JSONI} -o {BD}/tests/{t} tests/{t}.cpp {STATIC} "
        f"-L{BD} -lminiandroid_dalvik -Wl,-rpath,'\$ORIGIN/..' {LIBS} {FONTS}")
    tw += w
_, _, mainline = sh("make --no-print-directory -n -B build/miniandroid 2>/dev/null | grep ' -o build/miniandroid' | head -1")
noncore = [o for o in re.findall(r"build/\S+\.o", mainline)
           if o not in set(allobjs) | {"build/quickjs/quickjs.o", "build/jni/native_thunk.o"}]
timed("relink miniandroid_dev ($ORIGIN)",
    f"g++ {CXXFLAGS} {INCLUDES} {JSONI} -o {BD}/miniandroid_dev {' '.join(noncore)} {STATIC} "
    f"-L{BD} -lminiandroid_dalvik -Wl,-rpath,'\$ORIGIN' {LIBS} {FONTS}")

ENV = dict(os.environ, LD_LIBRARY_PATH=BD)
# 2. battery
w_bat, rc_bat, out_bat = timed("battery (so path, 3 tests)",
    f"{BD}/tests/simple_test && {BD}/tests/s130_laws_test && {BD}/tests/gp582_engine_probe_test", env=ENV)
print(f"battery PASS={out_bat.count('[PASS]') if '[PASS]' in out_bat else 'no-marker'} rc={rc_bat}")

# 3/4. edit loops
def edit_loop(tu, reps):
    src = f"src/{tu}.cpp"; obj = f"{BD}/objects/{os.path.basename(tu)}.o"
    extra = "--param inline-unit-growth=15 --param large-function-growth=120" if "interpreter" in tu else ""
    opt = "-Og" if "bridge" in tu else "-O2"
    res = []
    for i in range(reps):
        subprocess.run(["touch", src])
        w1, rc1, _ = timed(f"  {tu} PIC compile r{i+1}",
            f"g++ {CXXFLAGS.replace('-O2', opt)} -g0 -fPIC {extra} {INCLUDES} {JSONI} -c -o {obj} {src}")
        w2, rc2, _ = timed(f"  .so relink r{i+1}",
            f"g++ -shared -o {BD}/libminiandroid_dalvik.so {BD}/objects/*.o "
            f"-Wl,-soname,libminiandroid_dalvik.so -Wl,-rpath,'\$ORIGIN' {LIBS}")
        w3, rc3, out3 = timed(f"  battery r{i+1}",
            f"{BD}/tests/simple_test >/dev/null && {BD}/tests/s130_laws_test >/dev/null && {BD}/tests/gp582_engine_probe_test >/dev/null", env=ENV)
        tot = w1 + w2 + w3
        res.append((round(tot, 2), round(w1, 2), round(w2, 2), round(w3, 2)))
        print(f"  => {tu} loop r{i+1}: END-TO-END {tot:.2f}s (compile {w1:.1f} + so {w2:.2f} + tests {w3:.2f}) rc={rc1==0 and rc3==0}")
        if not (rc1 == 0 and rc2 == 0 and rc3 == 0): break
    return res
interp = edit_loop("dex/dalvik_interpreter", 3)
opcode = edit_loop("dex/dalvik_opcodes", 2)

# 5. runtime proof: original APKs on miniandroid_dev
CANON = {"ru.zxalexis.ugaday_15": "87fe26766fc48d06c59d4c15",
         "tech.gaskell.diceroller_1_debug": "46b07062ba6fe36ca8a6e42d",
         "com.itsfrz.tictactoe_5": "d55056a8928a26ffeb15f66d"}
par = {}
for a, canon in CANON.items():
    out = f"/tmp/w8_{a}"
    w, rc, _ = timed(f"APK {a}",
        f"{BD}/miniandroid_dev run --max-seconds 60 --frames 3 -o {out} "
        f"/home/z/my-project/upload/handoff_apks/{a}.apk > /tmp/w8_{a}.log 2>&1", env=ENV)
    h = ""
    if os.path.exists(f"{out}/screenshot.png"):
        h = hashlib.sha256(open(f"{out}/screenshot.png", "rb").read()).hexdigest()[:24]
    par[a] = {"rc": rc, "sha256_24": h, "canon": canon, "match": h.startswith(canon[:16])}
    print(f"  {a}: rc={rc} sha={h[:16]} match={par[a]['match']}")
print("LOOP_RESULTS:", {"interpreter": interp, "opcode": opcode})
print("PARITY:", par)
import json
json.dump({"interpreter_loop_s": interp, "opcode_loop_s": opcode, "parity": par,
           "battery_rc": rc_bat, "test_links_s": round(tw, 2)},
          open("/tmp/w8_results.json", "w"), indent=1)
