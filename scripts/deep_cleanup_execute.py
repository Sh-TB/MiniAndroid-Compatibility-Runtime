#!/usr/bin/env python3
"""DEEP-CLEANUP execution set + SHA ledger (S-SLIM methodology: record all
SHAs first, then untrack). Zero-risk class ONLY:
  E1. upstream/s43/ui_android_src/ — 379 files byte-identical to the
      canonical ui_android/ twin (measured), original ui-android-1.11.4-
      sources.jar tracked beside them (regenerable by unzip), and the
      S-SLIM duplicate ledger's own verdict is 'losers keep ui_android
      canonical, ui_android_src keep-local'. The bulk untrack pass missed
      this tree; completing it executes documented policy.
  E2. 5 of 6 NOISE-face screenshots (user-directed): ~1M-unique-color
      random-pixel failed renders (uninitialized framebuffer class); zero
      app information beyond the face hash; the run reports + traces stay
      tracked; the user-named exhibit (tictactoe_s195fix_r1) is RETAINED
      as the family representative.
Everything else = LEDGER-ONLY (owner decisions). Read-only elsewhere.
"""
import hashlib, os, subprocess

ROOT = "/home/z/my-project"
OUT = os.path.join(ROOT, "evidence/audit/deep_cleanup")
os.makedirs(OUT, exist_ok=True)
os.chdir(ROOT)

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

rows = []

# E1 ledger: the ui_android_src twin
e1 = subprocess.run(["git", "ls-files", "upstream/s43/ui_android_src"],
                    capture_output=True, text=True).stdout.splitlines()
for p in sorted(e1):
    rows.append(("E1_untrack_s43_twin", p, sha(p), os.path.getsize(p)))

# E2 ledger: the 6 noise faces (the user-named exhibit RETAINED)
noise = [
    "evidence/s195_audit/cohort/runs/tictactoe_s195fix_r1/screenshot.png",
    "evidence/s195_audit/gates/runs/spot_halma/screenshot.png",
    "evidence/s200/runs/s202_625_forced/screenshot.png",
    "evidence/s207/runs/s207_ttt0/screenshot.png",
    "evidence/s188_w13/runs/app.halma/screenshot.png",
    "evidence/s188_w18/runs/halma_w18_r1/screenshot.png",
]
KEEP = 0  # index of the retained exhibit (the user-named file)
for i, p in enumerate(sorted(noise)):
    act = "E2_KEEP_EXHIBIT" if i == KEEP else "E2_delete_noise_face"
    rows.append((act, p, sha(p), os.path.getsize(p)))

with open(os.path.join(OUT, "SHA256SUMS.txt"), "w") as f:
    f.write("# DEEP-CLEANUP executed-set SHA ledger (record-then-untrack law)\n")
    for act, p, h, s in rows:
        f.write(f"{h}  {s:>9}  {act}  {p}\n")

# execute
for i, p in enumerate(sorted(noise)):
    if i != KEEP and os.path.isfile(p):
        subprocess.run(["git", "rm", "-q", "--cached", p], check=True)
        os.remove(p) if os.path.exists(p) else None
        if os.path.exists(p):
            subprocess.run(["git", "rm", "-q", "-f", p], check=True)
for p in sorted(e1):
    subprocess.run(["git", "rm", "-q", "--cached", p], check=True)
    fp = os.path.join(ROOT, p)
    if os.path.exists(fp):
        os.remove(fp)
print(f"ledger rows: {len(rows)} (E1={len(e1)}, E2 removed=5 kept=1)")
print("staged:", subprocess.run(["git", "status", "--porcelain"],
                                 capture_output=True, text=True).stdout.count("D"))
