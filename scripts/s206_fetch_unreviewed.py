#!/usr/bin/env python3
"""S206 — fetch the 5 UNREVIEWED coder deliveries (full bodies) to disk."""
import json, subprocess
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s206')
OUT.mkdir(parents=True, exist_ok=True)

IDS = {
    "c3_s205_ledger_final": 6743675895,
    "c3_s205_ledger_opened": 6742700958,
    "c3_l06_winjudge_intel": 6743539452,
    "c9_s198_part1_rebased": 6743028191,
    "c9_s198_patch_p1": 6743028885,
    "c9_s198_patch_p2": 6743029544,
    "c9_s198_patch_p3": 6743030431,
    "c9_s198_patch_p4": 6743031214,
    "c9_s198_part2_receipts": 6743315564,
    "c7_master_ledger_42": 6742742510,
    "c7_t2122_index": 6742579888,
    "c8_w15_ledger": 6727645869,
    "c8_w15_diff_p1": 6727646579,
    "c8_w15_diff_p2": 6727647291,
    "c8_w15_diff_p3": 6727648006,
}

def tok():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    return [l.split("=", 1)[1] for l in out.splitlines() if l.startswith("password=")][0]

T = tok()
summary = []
for name, cid in IDS.items():
    r = subprocess.run(["curl", "-s", "-m", "60", "-H", f"Authorization: token {T}",
                        f"https://api.github.com/repos/{REPO}/issues/comments/{cid}"],
                       capture_output=True, text=True)
    c = json.loads(r.stdout)
    body = c.get("body", "")
    (OUT / f"{name}.md").write_text(body)
    summary.append({"name": name, "id": cid, "len": len(body),
                    "created": c.get("created_at")})
    print(f"{name}: id={cid} len={len(body)}")
(OUT / "fetch_summary.json").write_text(json.dumps(summary, indent=1))
