#!/usr/bin/env python3
"""cont11_loading_census.py — LOADING-SCREEN RECURRING-BLOCKER CENSUS.

Directive (2026-10-23): find problems REPEATED across several apps/games,
register them as a separate work task, and fix them so titles at least reach
the LOADING SCREEN (first real app-owned frame).

Method: install each pooled APK into a FRESH per-APK store, run a bounded
launch window (default 2-frame window + deferred-UI observability), capture
the honest verdict + first app-boundary divergence, then GROUP failures by
recurring signature.

Output: run/cont11_census/census.json + census_table.md
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
AAPT2 = f"{ROOT}/tools/aapt2/aapt2"
PKG_MAP = f"{ROOT}/run/cont11_pkg_map.txt"
OUT = f"{ROOT}/run/cont11_census"
os.makedirs(OUT, exist_ok=True)

POOLS = [
    f"{ROOT}/upload/fdroid_batch/*.apk",
    f"{ROOT}/upload/cont73_apks/*.apk",
    f"{ROOT}/upload/cont50_apks/*.apk",
    f"{ROOT}/upload/cont54_refetch/*.apk",
    f"{ROOT}/upload/cont11_apks/*.apk",
    f"{ROOT}/upload/canonical_apks/*.apk",
]

def apk_list():
    seen = set()
    out = []
    for pat in POOLS:
        for a in sorted(glob.glob(pat)):
            if a in seen:
                continue
            seen.add(a)
            out.append(a)
    return out

_MAP = None
def pkg_of(apk):
    global _MAP
    if _MAP is None:
        _MAP = {}
        try:
            for line in open(PKG_MAP):
                line = line.rstrip("\n")
                if "|" in line:
                    a, p = line.split("|", 1)
                    _MAP[os.path.basename(a)] = p
        except FileNotFoundError:
            pass
    return _MAP.get(os.path.basename(apk)) or None

def launchable_activity(apk):
    try:
        r = subprocess.run([AAPT2, "dump", "badging", apk],
                           capture_output=True, text=True, timeout=60)
        for line in r.stdout.splitlines():
            if line.startswith("launchable-activity:"):
                m = re.search(r"name='([^']+)'", line)
                if m:
                    return m.group(1)
    except Exception:
        pass
    return None

# Signature extraction: the recurring-family classifier.
def signature(logpath):
    if not os.path.exists(logpath):
        return [], None
    txt = open(logpath, errors="replace").read()
    sigs = []
    # Final uncaught exception (last SYNTH-EXC carries class + msg + site)
    excs = re.findall(r"\[SYNTH-EXC\][^\n]*", txt)
    for s in excs[-3:]:
        sigs.append(("SYNTH_EXC", s[:220]))
    # final app-boundary crash site
    props = re.findall(r"\[EXC-PROPAGATE\][^\n]*uncaught[^\n]*", txt)
    if props:
        sigs.append(("UNCAUGHT_SITE", props[-1][:220]))
    # verdict
    v = None
    for m in re.finditer(r"verdict=(\w+), first_missing_stage=(\w+)", txt):
        v = f"verdict={m.group(1)} first_missing={m.group(2)}"
    # unique REC-MISS (missing-API) signals, bounded
    rms = []
    for m in re.finditer(r"\[REC-MISS\] (\S+) caller=(\S+)", txt):
        k = f"{m.group(1)}"
        if k not in rms:
            rms.append(k)
    if rms:
        sigs.append(("REC_MISS", ",".join(rms[:8])[:220]))
    # framebuffer non-blank metric
    fbm = re.findall(r"\[EXP092-COPY\] fb has (\d+) non-white pixels", txt)
    return sigs, v

def classify(sig_text):
    """Map a raw first-divergence string to a recurring-family bucket."""
    t = (sig_text or "")
    tl = t.lower()
    # message-content keys first (more specific)
    keys = [
        ("uncaughtexceptionhandler", "THREAD-UEH-HANDLER"),
        ("fragmentmanager", "FRAGMENT-HOST"),
        ("uritostring", "URI-NULL"),
        ("uri.tostring", "URI-NULL"),
        ("sharedpreferences", "SHAREDPREFS"),
        ("glsurfaceview", "EGL-GLSURFACE"),
        ("egl", "EGL-GLSURFACE"),
        ("libgdx", "EGL-GLSURFACE"),
        ("gdxruntimeexception", "EGL-GLSURFACE"),
        ("layoutinflater", "INFLATE"),
        ("classnotfoundexception", "CLASSNOTFOUND"),
        ("nosuchmethod", "NOSUCHMETHOD"),
        ("nosuchfield", "NOSUCHFIELD"),
        ("abstractmethod", "ABSTRACT-METHOD"),
        ("nullpointerexception", "NPE-FAMILY"),
        ("illegalargumentexception", "ILLEGALARG"),
        ("illegalstateexception", "ILLEGALSTATE"),
        ("classcastexception", "CLASSCAST"),
        ("indexoutofbound", "INDEXOOB"),
        ("arrayindexoutofbound", "INDEXOOB"),
        ("negativearraysize", "NEGARRAY"),
        ("numberformat", "NUMFMT"),
        ("unsatisfiedlink", "NATIVE-LINK"),
        ("verifyerror", "VERIFY"),
        ("ioexception", "IO"),
        ("arithmetic", "ARITH"),
        ("arraystore", "ARRAYSTORE"),
        ("negativearray", "NEGARRAY"),
        ("concurrentmodification", "CONCMOD"),
    ]
    for k, fam in keys:
        if k in tl:
            return fam
    if "no_root" in tl or "window_root" in tl:
        return "NO-ROOT"
    if "app_boundary" in tl or "uncaught" in tl:
        return "UNCAUGHT-UNSPEC"
    return "OTHER"

def run_one(apk, pkg):
    tag = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(apk))[:60]
    store = f"{OUT}/store_{tag}"
    run = f"{OUT}/r_{tag}"
    for d in (store, run):
        subprocess.run(["rm", "-rf", d])
        os.makedirs(d, exist_ok=True)
    rec = {"apk": os.path.basename(apk), "path": apk, "pkg": pkg, "install": "FAIL", "run": None,
           "verdict": None, "sig": None, "family": None, "draw_ops": None}
    if not pkg:
        return rec
    r = subprocess.run([ENG, "install", apk, "--data-root", store],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        rec["sig"] = (r.stderr or r.stdout or "")[-300:]
        rec["family"] = "INSTALL"
        return rec
    rec["install"] = "OK"
    cmd = [ENG, "run", "--package", pkg, "--data-root", store,
           "--dump-view-tree", "--max-seconds", "90", "--frames", "6", "-o", run]
    with open(f"{run}/run.log", "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=subprocess.STDOUT, timeout=420)
        except subprocess.TimeoutExpired:
            rc = -99
            lf.write("\nTIMEOUT\n")
    rec["run"] = rc
    logpath = f"{run}/run.log"
    log = open(logpath, errors="replace").read() if os.path.exists(logpath) else ""
    sigs, v = signature(logpath)
    rec["verdict"] = v
    m = re.search(r"app_draw_ops[=:]?\s*(\d+)", log)
    if m:
        rec["draw_ops"] = int(m.group(1))
    fbn = re.search(r"\[EXP092-COPY\] fb has (\d+) non-white pixels", log)
    if fbn:
        rec["fb_nonwhite"] = int(fbn.group(1))
    # final uncaught exception = last SYNTH_EXC; else crash-site; else verdict
    first = None
    for kind, s in sigs:
        if kind == "SYNTH_EXC":
            first = s
    if not first:
        for kind, s in sigs:
            if kind == "UNCAUGHT_SITE":
                first = s
                break
    rec["sig"] = first or (v or "")[:180] or "no-signal"
    if first or v:
        rec["family"] = classify(rec["sig"])
        # upgrade: if final exception is NPE-family, try message keys from ANY sig
        if rec["family"] in ("NPE-FAMILY", "UNCAUGHT-UNSPEC"):
            for kind, s in sigs:
                c = classify(s)
                if c not in ("NPE-FAMILY", "UNCAUGHT-UNSPEC", "OTHER"):
                    rec["family"] = c
                    break
    else:
        rec["family"] = "NO-SIGNAL"
    # unique REC-MISS list for the record
    for kind, s in sigs:
        if kind == "REC_MISS":
            rec["rec_miss"] = s
    # loading-screen heuristic: any nonzero app draw ops => content reached
    return rec

def main():
    apks = apk_list()
    print(f"pool={len(apks)}", flush=True)
    results = []
    CJ = f"{OUT}/census.json"
    if os.path.exists(CJ):
        try:
            results = json.load(open(CJ))
        except Exception:
            results = []
    done = {r.get("path") for r in results}
    for i, apk in enumerate(apks):
        if apk in done:
            continue
        p = pkg_of(apk)
        print(f"[{i+1}/{len(apks)}] {os.path.basename(apk)} pkg={p}", flush=True)
        try:
            rec = run_one(apk, p)
        except Exception as e:
            rec = {"apk": os.path.basename(apk), "pkg": p, "install": "ERROR",
                   "run": None, "verdict": str(e)[:200], "sig": str(e)[:200],
                   "family": "HARNESS-ERROR", "draw_ops": None}
        results.append(rec)
        json.dump(results, open(f"{OUT}/census.json", "w"), indent=1)
    # summarize
    fams = {}
    for r in results:
        fams.setdefault(r["family"], []).append(r["apk"])
    with open(f"{OUT}/census_table.md", "w") as f:
        f.write("# CONT-11 loading-screen census (fresh)\n\n")
        f.write(f"pool={len(apks)}  install_ok={sum(1 for r in results if r['install']=='OK')}\n\n")
        f.write("| family | count | members |\n|---|---|---|\n")
        for fam, members in sorted(fams.items(), key=lambda kv: -len(kv[1])):
            f.write(f"| {fam} | {len(members)} | {', '.join(m.split('_')[0] for m in members[:12])}{' …' if len(members)>12 else ''} |\n")
    print(json.dumps({k: len(v) for k, v in sorted(fams.items(), key=lambda kv: -len(kv[1]))}, indent=1))

if __name__ == "__main__":
    main()
