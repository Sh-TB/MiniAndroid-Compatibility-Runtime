#!/usr/bin/env python3
"""S53 image hygiene executor.

Classes:
  KEEP-FIXTURE  golden/fixture/asset images (battery oracles, mascots, demos)
  KEEP          meaningful unique images
  DELETE-BLANK  blank-class (renderer artifact / white-black frames)
  DELETE-DUP    byte-identical duplicate (keep best-path canonical)
  DELETE-GEN    generated run outputs under miniandroid/run/** (not referenced)
Removal list + SHA256 -> docs/evidence/S53_REMOVED_IMAGES_SHA256SUMS.txt
"""
import hashlib
import os
import subprocess
from PIL import Image

KEEP_PREFIXES = (
    "docs/evidence/helloworld_golden/",
    "docs/evidence/hello_color_golden/",
    "docs/evidence/external_hello_golden/",
    "docs/evidence/golden03/",
    "docs/assets/",
    "docs/evidence/s53_frames/",
    "miniandroid/tests/",
)


def git_ls():
    out = subprocess.check_output(["git", "ls-files"], text=True)
    return [l for l in out.splitlines() if l.lower().endswith((".png", ".jpg", ".jpeg"))]


def digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def blankness(path):
    try:
        im = Image.open(path)
    except Exception:
        return (0.0, 0.0, -1, "ERR")
    g = im.convert("L")
    h = g.histogram()
    total = im.size[0] * im.size[1] or 1
    nw = sum(h[245:]) / total * 100
    nb = sum(h[:12]) / total * 100
    c = im.convert("RGB").getcolors(maxcolors=1 << 24)
    ncol = len(c) if c else -1
    return (nw, nb, ncol, "OK")


def is_blank(nw, nb, ncol):
    return (nw >= 99.5 or nb >= 99.5) or (0 <= ncol <= 8)


def path_score(p):
    """lower = better canonical candidate"""
    s = 0
    if p.startswith("docs/evidence/s51_audit/"):
        s += 5
    elif p.startswith("docs/evidence/"):
        s += 10
    elif p.startswith("docs/"):
        s += 30
    else:
        s += 60          # miniandroid/run/** etc
    if "/click/" in p or "/frames/" in p:
        s += 5
    return s + len(p) / 1000.0


def main():
    imgs = git_ls()
    info = {}
    for f in imgs:
        dg = digest(f)
        nw, nb, ncol, st = blankness(f)
        info[f] = dict(sha=dg, nw=nw, nb=nb, ncol=ncol, size=os.path.getsize(f), st=st)

    groups = {}
    for f, d in info.items():
        groups.setdefault(d["sha"], []).append(f)

    removed, kept = [], []
    for f in sorted(imgs):
        d = info[f]
        keep = False
        if f.startswith(KEEP_PREFIXES):
            keep = True                      # fixtures/assets/canonical gallery
        elif d["size"] == 0:
            keep = False                     # zero-byte always out
        else:
            g = groups[d["sha"]]
            best = min(g, key=path_score)
            if f != best:
                pass                         # duplicate -> delete
            elif d["st"] == "OK" and not is_blank(d["nw"], d["nb"], d["ncol"]):
                keep = True                  # meaningful unique
            elif f.startswith("miniandroid/run/"):
                keep = False                 # generated run output, blank or not
            elif is_blank(d["nw"], d["nb"], d["ncol"]):
                keep = False                 # blank evidence
            else:
                keep = True                  # unique non-blank, non-run
        if keep:
            kept.append(f)
        else:
            why = ("zero-byte" if d["size"] == 0 else
                   f"dup-of:{best}" if f != groups[d["sha"]][0] and f != min(groups[d["sha"]], key=path_score) else
                   "blank-class" if d["st"] == "OK" and is_blank(d["nw"], d["nb"], d["ncol"]) else
                   "generated-run-output")
            removed.append((f, d["sha"][:16], d["size"], why))

    # report
    print(f"total={len(imgs)} keep={len(kept)} remove={len(removed)}")
    from collections import Counter
    print("reasons:", Counter(w for _, _, _, w in removed))
    os.makedirs("docs/evidence", exist_ok=True)
    with open("docs/evidence/S53_REMOVED_IMAGES_SHA256SUMS.txt", "w") as fh:
        fh.write("# S53 removed tracked images — SHA256(provenance; blobs remain in git history)\n")
        for f, sha, size, why in sorted(removed):
            fh.write(f"{sha}  {size:>9}B  {why:<46} {f}\n")
    for f, _, _, why in removed:
        if os.path.exists(f):
            os.remove(f)
    print("removal executed; SHA list -> docs/evidence/S53_REMOVED_IMAGES_SHA256SUMS.txt")


if __name__ == "__main__":
    main()
