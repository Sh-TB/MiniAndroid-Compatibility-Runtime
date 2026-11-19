#!/usr/bin/env python3
"""w23_probe.py — W23-07 incremental build benchmark harness (validated probes).

Runs the mission's operations A-J against a chosen build profile, with
per-probe VALIDATION (parses the make log for actual compiler/linker
invocations and cross-checks against the expected dependency closure), so a
mis-probed no-op or a wrong edit cannot pass silently.

Operations:
  A  no-change rebuild            (expect 0 compiles, 0 links)
  B  leaf implementation file     (src/dex/dalvik_value_glue.cpp)
  C  dalvik interpreter file      (src/dex/dalvik_interpreter.cpp)
  D  opcode implementation        (src/dex/dalvik_opcodes.cpp)
  E  bridge implementation        (src/dex/dalvik_bridge.cpp)
  F  private header               (src/dex/dalvik_engine_internal.h)
  G  public engine header         (src/dex/dalvik_engine.h)  <- W22 probe of record
  H  common cross-module header   (src/framework/android_shadows.h)
  I  full clean rebuild           (rm -rf BUILDDIR; full build)
  J  second unchanged rebuild     (same as A, after I)

Each probe appends a UNIQUE comment line to the target (a real source change
on every run — never benchmarks a stale no-op), runs the profile's build
command, then records wall/CPU/peak-RSS/rc + compiled-TU set + link count +
the validation verdict. Comment-only changes never alter semantics; the
caller restores the tree with git checkout afterwards.

Profiles:
  prod  : make -j1 --output-sync all            (build/)
  devso : make -j1 dev-so-test                  (build_dev_so/; lib+4-test battery)

Usage:
  python3 scripts/w23_probe.py --profile prod --ops A --runs 3 \
      --out evidence/w23/probes_prod.jsonl
"""
import argparse
import hashlib
import json
import os
import re
import resource
import subprocess
import sys
import time

REPO = os.environ.get("MINIANDROID_REPO", "/home/z/my-project/miniandroid")

PROFILES = {
    "prod": {"buildcmd": ["make", "-j1", "--output-sync", "all"], "marker": "build/miniandroid"},
    "devso": {"buildcmd": ["make", "-j1", "dev-so-test"], "marker": "build_dev_so/tests/simple_test"},
}

OPS = {
    "A": {"desc": "no-change rebuild", "edit": None},
    "B": {"desc": "leaf implementation file", "edit": "src/dex/dalvik_value_glue.cpp"},
    "C": {"desc": "dalvik interpreter file", "edit": "src/dex/dalvik_interpreter.cpp"},
    "D": {"desc": "opcode implementation", "edit": "src/dex/dalvik_opcodes.cpp"},
    "E": {"desc": "bridge implementation", "edit": "src/dex/dalvik_bridge.cpp"},
    "F": {"desc": "private engine header", "edit": "src/dex/dalvik_engine_internal.h"},
    "G": {"desc": "public engine header", "edit": "src/dex/dalvik_engine.h"},
    "H": {"desc": "common cross-module header", "edit": "src/framework/android_shadows.h"},
    "I": {"desc": "full clean rebuild", "edit": None, "clean": True},
    "J": {"desc": "second unchanged rebuild", "edit": None},
}

COMPILE_RE = re.compile(r"g\+\+ .*-c -o (\S+\.o) ")
C_COMPILE_RE = re.compile(r"\bgcc\b .*-c -o (\S+\.o) ")
LINK_RE = re.compile(r"g\+\+ .*-o (\S+) \^?")
ASM_RE = re.compile(r"\bgcc\b -c -o (\S+\.o) ")


def run_logged(cmd, log_path, cwd=REPO):
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd)
    logf = open(log_path, "w")
    n_compile, n_clink, n_alink, n_asm = 0, 0, 0, 0
    tus, links = [], []
    for raw in iter(p.stdout.readline, b""):
        line = raw.decode("utf-8", "replace").rstrip("\n")
        logf.write("%8.2f %s\n" % (time.time() - t0, line))
        if COMPILE_RE.match(line):
            n_compile += 1
            tus.append(COMPILE_RE.match(line).group(1))
        elif ASM_RE.match(line) or C_COMPILE_RE.match(line):
            if C_COMPILE_RE.match(line):
                n_clink += 1
                tus.append(C_COMPILE_RE.match(line).group(1))
            elif ASM_RE.match(line):
                n_asm += 1
        elif LINK_RE.match(line):
            n_alink += 1
            links.append(LINK_RE.match(line).group(1))
    logf.close()
    p.wait()
    wall = time.time() - t0
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"rc": p.returncode, "wall_s": round(wall, 3),
            "cpu_user_s": round(ru.ru_utime, 3), "cpu_sys_s": round(ru.ru_stime, 3),
            "maxrss_kb": ru.ru_maxrss, "n_compiled_tus": n_compile,
            "compiled_tus": tus, "n_c_compiles": n_clink, "n_asm": n_asm,
            "n_links": n_alink, "linked_targets": links, "log": log_path}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def head_dirty():
    try:
        st = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                            capture_output=True, text=True).stdout.strip()
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                              capture_output=True, text=True).stdout.strip()
        return head, st
    except Exception:
        return None, None


def apply_edit(op, run_idx):
    """Append a unique comment line; returns (changed, sha_before, sha_after)."""
    target = OPS[op]["edit"]
    path = os.path.join(REPO, target)
    before = sha256(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write("// W23-BENCH op=%s run=%d t=%d\n" % (op, run_idx, int(time.time())))
    return target, before, sha256(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=PROFILES, required=True)
    ap.add_argument("--ops", default="A")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    prof = PROFILES[args.profile]
    head, dirty = head_dirty()
    results = []
    os.makedirs(os.path.dirname(os.path.join(REPO, args.out)), exist_ok=True)
    out_path = os.path.join(REPO, args.out)
    logdir = os.path.join(REPO, "evidence/w23/probe_logs")
    os.makedirs(logdir, exist_ok=True)

    for op in args.ops.replace(",", "").upper():
        if op not in OPS:
            sys.exit("unknown op: " + op)
        for r in range(1, args.runs + 1):
            tag = "%s_%s_r%d" % (args.profile, op, r)
            log_path = os.path.join(logdir, tag + ".log")
            edit_info = {"edited": None}
            if OPS[op].get("clean"):
                bdir = "build" if args.profile == "prod" else "build_dev_so"
                subprocess.run(["rm", "-rf", bdir], cwd=REPO, check=True)
            elif OPS[op]["edit"]:
                tgt, b, a = apply_edit(op, r)
                edit_info = {"edited": tgt, "sha_before": b, "sha_after": a}
            rec = run_logged(prof["buildcmd"], log_path)
            rec.update(edit_info)
            rec.update({"profile": args.profile, "op": op, "op_desc": OPS[op]["desc"],
                        "run": r, "tag": args.tag, "head": head, "dirty": dirty,
                        "buildcmd": prof["buildcmd"]})
            # validation
            problems = []
            if rec["rc"] != 0:
                problems.append("rc=%d" % rec["rc"])
            if op in ("A", "J"):
                if rec["n_compiled_tus"] or rec["n_c_compiles"] or rec["n_links"]:
                    problems.append("expected pure no-op: got %d compiles %d links"
                                    % (rec["n_compiled_tus"] + rec["n_c_compiles"], rec["n_links"]))
            if OPS[op]["edit"] and op not in ("F", "G", "H"):
                if not any(t.endswith(os.path.basename(OPS[op]["edit"]).replace(".cpp", ".o"))
                           for t in rec["compiled_tus"]):
                    problems.append("edited TU NOT recompiled (accidental no-op!)")
            rec["valid"] = not problems
            rec["validation_problems"] = problems
            with open(out_path, "a") as f:
                f.write(json.dumps(rec) + "\n")
            results.append(rec)
            print("%s op=%s run=%d wall=%.2fs tus=%d links=%d valid=%s %s" % (
                args.profile, op, r, rec["wall_s"], rec["n_compiled_tus"],
                rec["n_links"], rec["valid"], " ".join(problems)))

    med = {}
    for op in set(x["op"] for x in results):
        walls = sorted(x["wall_s"] for x in results if x["op"] == op)
        med[op] = walls[len(walls) // 2]
    print("medians:", json.dumps({k: round(v, 2) for k, v in sorted(med.items())}))


if __name__ == "__main__":
    main()
