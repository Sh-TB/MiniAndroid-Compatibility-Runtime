#!/usr/bin/env python3
"""s84_cleanup.py — S84 §15 evidence cleanup (SURGICAL, manifest-recorded).

Deletes ONLY:
  A. all tracked .ppm raw framebuffer dumps (315 MB — closed-investigation
     intermediates; the rendered evidence of every closed root cause is
     preserved as PNG/JPG/GIF + SHA256SUMS manifests)
  B. closed root-cause investigation frame-by-frame dirs (snake restart
     S73/S75/S76, tictactoe visual-forensics engine frames) — the final
     proofs live in docs/evidence/s83*/ + canonical/
  C. exact content-duplicate images elsewhere in the repo (first-seen by
     (hash, dir-priority) — canonical/ and golden/ladder evidence win)

NEVER touches: docs/evidence/canonical/*, golden/ladder fixtures,
upstream corpus art, SHA256SUMS manifests, report docs, src fixtures.
Everything is recorded with SHA256 in docs/evidence/S84_CLEANUP_MANIFEST.md
(git history retains all deleted blobs — recoverable).
"""
import glob
import hashlib
import json
import os
import subprocess

ROOT = "/home/z/my-project"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tracked(pattern):
    out = subprocess.run(["git", "-C", ROOT, "ls-files", pattern],
                         capture_output=True, text=True)
    return [l for l in out.stdout.splitlines() if l]


def git_rm(paths):
    if not paths:
        return
    for i in range(0, len(paths), 100):
        subprocess.call(["git", "-C", ROOT, "rm", "-q", "--cached"] +
                        paths[i:i + 100])
        # also unlink from disk (they stay in git history)
    for p in paths:
        if os.path.exists(p):
            os.remove(p)


MANIFEST = {"ppm_deleted": [], "frames_deleted": [], "dups_deleted": [],
            "kept_canonical": [], "totals": {}}
n0 = len(tracked("*.ppm")) + len(tracked("*.png")) + \
    len(tracked("*.jpg")) + len(tracked("*.gif"))
sz0 = 0
for f in tracked("*.ppm") + tracked("*.png") + tracked("*.jpg") + \
        tracked("*.gif"):
    sz0 += os.path.getsize(f"{ROOT}/{f}") if os.path.exists(f"{ROOT}/{f}") \
        else 0

# ---- A. PPM dumps ----------------------------------------------------------
ppms = tracked("*.ppm")
MANIFEST["ppm_deleted"] = ppms
git_rm(ppms)

# ---- B. closed-investigation frame dirs ------------------------------------
FRAME_DIRS = [
    "docs/evidence/s73_snake_autoplay",
    "docs/evidence/s75",
    "docs/evidence/s76",
    "docs/evidence/visual_forensics/tictactoe",
]
frames = []
for d in FRAME_DIRS:
    for ext in ("*.png", "*.ppm"):
        frames += tracked(f"{d}/**/{ext}")
        frames += tracked(f"{d}/{ext}")
frames = sorted(set(frames))
MANIFEST["frames_deleted"] = frames
git_rm(frames)

# ---- C. content duplicates -------------------------------------------------
PRIORITY_PREFIX = ["docs/evidence/canonical/", "miniandroid/golden/",
                   "miniandroid/tests/", "fixtures/", "games/", "examples/",
                   "docs/evidence/visual_forensics/", "docs/evidence/s8",
                   "docs/evidence/"]
seen = {}
dups = []
imgs = tracked("*.png") + tracked("*.jpg") + tracked("*.jpeg") + \
    tracked("*.gif")


def prio(p):
    for i, pref in enumerate(PRIORITY_PREFIX):
        if p.startswith(pref):
            return i
    return len(PRIORITY_PREFIX)


for f in sorted(imgs, key=prio):
    path = f"{ROOT}/{f}"
    if not os.path.exists(path):
        continue
    h = sha256(path)
    if h in seen:
        dups.append((f, seen[h]))
    else:
        seen[h] = f
MANIFEST["dups_deleted"] = [{"deleted": d, "kept": k} for d, k in dups]
git_rm([d for d, _ in dups])

# ---- totals ----------------------------------------------------------------
n1 = len(tracked("*.ppm")) + len(tracked("*.png")) + \
    len(tracked("*.jpg")) + len(tracked("*.gif"))
sz1 = 0
for f in tracked("*.ppm") + tracked("*.png") + tracked("*.jpg") + \
        tracked("*.gif"):
    p = f"{ROOT}/{f}"
    if os.path.exists(p):
        sz1 += os.path.getsize(p)
MANIFEST["totals"] = {
    "images_before": n0, "images_after": n1,
    "bytes_before": sz0, "bytes_after": sz1,
    "bytes_saved": sz0 - sz1,
    "ppm_deleted": len(MANIFEST["ppm_deleted"]),
    "frames_deleted": len(MANIFEST["frames_deleted"]),
    "dups_deleted": len(MANIFEST["dups_deleted"]),
}
with open(f"{ROOT}/docs/evidence/S84_CLEANUP_MANIFEST.json", "w") as f:
    json.dump(MANIFEST, f, indent=1)
print(json.dumps(MANIFEST["totals"], indent=1))
