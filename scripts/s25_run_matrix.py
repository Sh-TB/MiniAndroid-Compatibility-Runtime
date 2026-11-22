#!/usr/bin/env python3
# s25_run_matrix.py — builds evidence/s25/s25_run_matrix.tsv from the final
# S25 run dirs (unique frame hashes + the per-run verdict line), mirroring
# the s24_run_matrix.tsv shape. Frame files stay local (no PNGs committed);
# the TSV carries the hashes.
import hashlib
import os
import re

BASE = "/home/z/my-project/miniandroid/evidence/s25"
OUT = os.path.join(BASE, "s25_run_matrix.tsv")


def frame_hashes(run_dir):
    d = os.path.join(BASE, run_dir, "frames")
    if not os.path.isdir(d):
        return []
    hs = set()
    for f in sorted(os.listdir(d)):
        if f.endswith(".png"):
            hs.add(
                hashlib.sha256(
                    open(os.path.join(d, f), "rb").read()).hexdigest()[:8])
    return sorted(hs)


def verdict(run_dir):
    p = os.path.join(BASE, run_dir, "stderr.log")
    if not os.path.exists(p):
        return ""
    v = ""
    for line in open(p, errors="replace"):
        m = re.search(r"verdict=([A-Z_]+)", line)
        if m:
            v = m.group(1)
    return v


def grep_count(run_dir, pat):
    p = os.path.join(BASE, run_dir, "stderr.log")
    if not os.path.exists(p):
        return 0
    return sum(1 for line in open(p, errors="replace")
               if re.search(pat, line))


rows = []
apk_runs = [
    ("org.ecos.logic.flip_a_coin_3", ["flip_r1", "flip_r2", "flip_r3"]),
    ("de.tcrass.minos_10004", ["minos_r1", "minos_r2", "minos_r3"]),
    ("com.minar.randomix_42", ["anchor_com.minar.randomix_42"]),
    ("HelloWorldToast-1.4.0-android", ["anchor_HelloWorldToast-1.4.0-android"]),
    ("dk.cocode.chess_5022", ["anchor_dk.cocode.chess_5022"]),
]
notes = {
    "flip": "S25-W1a bind-time content parent + W1b tag stamp + W1c asList "
            "dual-store + W1d AnimatorSet Builder: setPresenter RUNS, "
            "setOnClickListener registers (view 594); face blocked at the "
            "honest P1-2 VectorDrawable layer (#633/#634)",
    "minos": "S25-W2 collection copy-ctor: EventBus registration COMPLETES "
             "(METHOD_CACHE.put); EventBusException GONE; remaining deferred "
             "face = GameMetrics dims layer (recorded)",
}

for apk, runs in apk_runs:
    for r in runs:
        hs = frame_hashes(r)
        kind = "flip" if r.startswith("flip") else (
            "minos" if r.startswith("minos") else "anchor")
        extra = ""
        if kind == "flip":
            adopt = grep_count(r, r"S25-W1-BIND-ADOPT")
            pres = grep_count(r, r"setPresenter")
            listener = grep_count(r, r"EXP060-LISTENER")
            vec = grep_count(r, r"IMAGE-BLOCKED.*VectorDrawable")
            extra = (f"ADOPT={adopt} setPresenter={pres} listener={listener} "
                     f"vectorBlocked={vec}")
        elif kind == "minos":
            exc = grep_count(r, r"EventBusException")
            put = grep_count(r, r"METHOD_CACHE")
            extra = f"eventbus_exc={exc} cache_put={put}"
        rows.append(
            f"{apk}\t{r}\t{len(hs)}\t{','.join(hs) if hs else '-'}\t"
            f"{verdict(r)}\t{extra}\t{notes.get(kind, '')}")

with open(OUT, "w") as f:
    f.write("apk\trun_dir\tunique_hashes\thashes\tverdict\tfiring\tsemantic_note\n")
    for r in rows:
        f.write(r + "\n")
print(f"wrote {OUT}: {len(rows)} rows")
