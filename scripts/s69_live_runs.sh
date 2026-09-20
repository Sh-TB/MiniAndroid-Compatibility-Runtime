#!/usr/bin/env bash
# s69_live_runs.sh — live dispatch-surface capture for every pinned corpus APK.
# run/ is gitignored (raw evidence law §5); the compact summary is written to
# docs/foundation/live_runs.json by the python step below.
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
CORPUS=$ROOT/upload/canonical_apks
OUT=$ROOT/run/s69_live
mkdir -p "$OUT"

APKS=(
  app.varlorg.unote_30.apk
  bouncy.apk
  com.emmanuelmess.tictactoe_3.apk
  com.github.muellerma.stopwatch_6.apk
  de.duenndns.gmdice_8.apk
  dooz_23_toplevel.apk
  dubrowgn.microtimer_8.apk
  fishrings_v1.23_vc6.apk
  opmt_v0.1.2_vc1.apk
  tripeaks_v1.2.1_vc4.apk
)

for apk in "${APKS[@]}"; do
  name="${apk%.apk}"
  d="$OUT/$name"
  rm -rf "$d"; mkdir -p "$d"
  # canonical corpus recipe (S65/S66 session ledger): real-dalvik + 9-frame
  # pump with 1500ms virtual frame delay (splash Timer navigation lands)
  (cd "$d" && timeout 150 "$ENG" run --execution-mode real-dalvik \
     --frames 9 --frame-delay 1500 \
     --dump-api-trace --dump-view-tree \
     -o . "$CORPUS/$apk" > engine.log 2>&1)
  echo "$name rc=$?"
done

python3 - <<'PYEOF'
import hashlib, json, os, re
from pathlib import Path
OUT = Path("/home/z/my-project/run/s69_live")
DOC = Path("/home/z/my-project/docs/foundation")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def png_nonwhite(p):
    from PIL import Image
    im = Image.open(p).convert("RGB")
    px = im.getdata()
    return sum(1 for t in px if t != (255, 255, 255)), im.size

runs = []
for d in sorted(OUT.iterdir()):
    if not d.is_dir():
        continue
    log = (d / "engine.log")
    log_text = log.read_text(errors="replace") if log.exists() else ""
    rec = {"apk": d.name + ".apk", "dir": str(d)}
    # rc: parse the runner's status line
    m = re.search(r"Status: (SUCCESS|PARTIAL SUCCESS|FAILURE|CRASH)", log_text)
    rec["status"] = m.group(1) if m else "UNKNOWN"
    rec["rc_zero"] = "Status: SUCCESS" in log_text
    shot = d / "screenshot.png"
    if shot.exists():
        try:
            nw, size = png_nonwhite(shot)
            rec["screenshot"] = {"sha256": sha(shot), "nonwhite": nw,
                                 "width": size[0], "height": size[1]}
        except Exception as e:
            rec["screenshot"] = {"error": str(e)}
    # per-frame evidence (canonical corpus law: frame_004+ carries the real
    # board; the final screenshot.png can be white after splash finish)
    fdir = d / "frames"
    if fdir.exists():
        frames = sorted(fdir.glob("frame_*.png"))
        fstats = []
        for f in frames:
            try:
                nw, size = png_nonwhite(f)
                fstats.append({"frame": f.name, "nonwhite": nw,
                               "sha256": sha(f)})
            except Exception:
                pass
        rec["frames"] = fstats
        rec["max_frame_nonwhite"] = max((f["nonwhite"] for f in fstats), default=0)
    vt = d / "view_tree.json"
    if vt.exists():
        try:
            tree = json.loads(vt.read_text())
            nodes = tree if isinstance(tree, list) else tree.get("nodes", [])
            rec["view_tree_nodes"] = len(nodes)
            rec["view_tree_sha256"] = sha(vt)
        except Exception as e:
            rec["view_tree_nodes"] = None
    ap = d / "api_calls.json"
    if ap.exists():
        try:
            calls = json.loads(ap.read_text())
            from collections import Counter
            st = Counter(c.get("status") for c in calls)
            rec["api_calls"] = {"total": len(calls),
                                "by_status": dict(st),
                                "sha256": sha(ap)}
        except Exception:
            pass
    # REC-MISS census from stderr log (failure auto-trace §4)
    misses = [l for l in log_text.splitlines() if l.startswith("[REC-MISS]")]
    rec["rec_miss_lines"] = len(misses)
    rec["rec_miss_top"] = Counter(
        l.replace("[REC-MISS] ", "").split(" caller=")[0]
        for l in misses).most_common(15)
    unsup = [l for l in log_text.splitlines() if "UNSUPPORTED" in l]
    rec["unsupported_lines"] = len(unsup)
    rec["unsupported_top"] = Counter(unsup).most_common(6)
    runs.append(rec)

(DOC / "live_runs.json").write_text(json.dumps(
    {"generated": "S69", "runs": runs}, indent=1))
for r in runs:
    print(r["apk"], r["status"], "api:", r.get("api_calls", {}).get("total", 0),
          "miss:", r["rec_miss_lines"], "unsp:", r["unsupported_lines"],
          "shot:", r.get("screenshot", {}).get("nonwhite", "NONE"))
PYEOF
