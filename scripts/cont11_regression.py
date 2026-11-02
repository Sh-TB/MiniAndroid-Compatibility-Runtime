#!/usr/bin/env python3
"""cont11_regression.py — CONT-11 wave: full old-program regression battery.

Groups (run one per invocation, resumable):
  anchors_a  opencalc/chess/dooz      x3 runs each
  anchors_b  microtimer/unote         x3 runs each
  games_a    2048/mini-tetris/minicraft x3
  games_b    snake-deluxe/snake-neon/tictactoe-deluxe x3
  satellites tower3d/freebloks/bouncy x1 each (fresh store)
  telegram   forkgram + official x1 each, sqlite scan
  new        new-program batch (see NEW_BATCH)

Writes evidence/cont11/CONT11_REGRESSION.json incrementally (merge-safe).
"""
import hashlib, json, os, re, shutil, subprocess, sys, time

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"
RUN = f"{BASE}/run/cont11"
EV = f"{BASE}/evidence/cont11"
OUT_JSON = f"{EV}/CONT11_REGRESSION.json"
os.makedirs(EV, exist_ok=True)

RECORDED_ANCHORS = {
    # app -> expected screenshot sha16 (W5/W6 recorded; opencalc changed at W6)
    "opencalc": "a976d2f9", "chess": "b5a7a35d", "dooz": "d602648e",
    "microtimer": "da73010a", "unote": "4f1a9e4e",
}
RECORDED_GAMES = {
    "2048": "7ad9a8bdefba539b", "mini-tetris": "26ccfce917c0e24c",
    "minicraft": "ce27f331770f6979", "snake-deluxe": "34a712689ce66e58",
    "snake-neon": "477bb95e1e6398ce", "tictactoe-deluxe": "0a1cd01bb490fdc5",
}
APKS = {
    "opencalc": (f"{BASE}/upload/opencalculator_53.apk", "com.darkempire78.opencalculator"),
    "chess":    (f"{BASE}/upload/chess_jwtc_298.apk", "jwtc.android.chess"),
    "dooz":     (f"{BASE}/upload/canonical_apks/io.github.yamin8000.dooz_23.apk", "io.github.yamin8000.dooz"),
    "microtimer": (f"{BASE}/upload/canonical_apks/dubrowgn.microtimer_8.apk", "dubrowgn.microtimer"),
    "unote":    (f"{BASE}/upload/canonical_apks/app.varlorg.unote_30.apk", "app.varlorg.unote"),
    "2048":     (f"{BASE}/upload/s80_games/build_2048/g2048_v1.0_vc1.apk", "com.miniandroid.g2048"),
    "mini-tetris": (f"{BASE}/upload/s80_games/build_tetris/tetris_v1.0_vc1.apk", "com.miniandroid.tetris"),
    "minicraft": (f"{BASE}/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk", "com.miniandroid.minicraft"),
    "snake-deluxe": (f"{BASE}/upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk", "com.miniandroid.snakedeluxe"),
    "snake-neon": (f"{BASE}/upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk", "com.miniandroid.snakeneon"),
    "tictactoe-deluxe": (f"{BASE}/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk", "com.miniandroid.tictactoedeluxe"),
    "tower3d":  (f"{BASE}/upload/canonical_apks/stack.tower3d_1.apk", None),
    "freebloks": (f"{BASE}/upload/canonical_apks/de.saschahlusiak.freebloks_184.apk", None),
    "bouncy":   (f"{BASE}/upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk", None),
    "forkgram": (f"{BASE}/upload/forkgram_709208.apk", None),
    "telegram": (f"{BASE}/upload/telegram_official.apk", None),
}
# new-program batch: fdroid_batch APKs, decided at call time via NEW_BATCH env or default list
NEW_BATCH = os.environ.get("NEW_BATCH", "").split(":") if os.environ.get("NEW_BATCH") else []

def sha16(p):
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    except Exception:
        return None

def load_state():
    if os.path.exists(OUT_JSON):
        return json.load(open(OUT_JSON))
    return {"binary_sha16": sha16(BIN), "runs": {}}

def save_state(st):
    st["binary_sha16"] = sha16(BIN)
    tmp = OUT_JSON + ".tmp"
    json.dump(st, open(tmp, "w"), indent=1)
    os.replace(tmp, OUT_JSON)

def pkg_of(apk):
    r = subprocess.run([BIN, "install", apk, "--data-root", "/tmp/pkgprobe"],
                       capture_output=True, text=True, timeout=120)
    m = re.search(r'"package":\s*"([\w.]+)"', r.stdout + r.stderr)
    shutil.rmtree("/tmp/pkgprobe", ignore_errors=True)
    return m.group(1) if m else None

def one_run(name, pkg, apk, run_dir, store, max_seconds, extra=None):
    os.makedirs(run_dir, exist_ok=True)
    cmd = [BIN, "run", "--package", pkg, "--data-root", f"{store}/data",
           "--execution-mode", "real-dalvik", "--trace",
           "--max-seconds", str(max_seconds), "-o", run_dir]
    if extra: cmd += extra
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, timeout=max_seconds + 120)
    dt = time.time() - t0
    log = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
    shot = f"{run_dir}/screenshot.png"
    row = {"seconds": round(dt, 1), "screenshot_sha16": sha16(shot)}
    m = re.search(r"verdict=([A-Z_]+), first_missing_stage=([A-Z_]+)", log)
    row["verdict"] = m.group(1) if m else None
    row["first_missing_stage"] = m.group(2) if m else None
    if row["verdict"] is None:
        m2 = re.search(r"verdict=([A-Z_]+)", log)
        row["verdict"] = m2.group(1) if m2 else None
    ts = f"{run_dir}/trace_summary.json"
    if row["verdict"] is None and os.path.exists(ts):
        try:
            fa = json.load(open(ts)).get("frame_analysis") or {}
            row["verdict"] = fa.get("verdict"); row["app_owned_pixels"] = fa.get("app_owned_pixels")
        except Exception: pass
    m = re.search(r"([0-9]+) uncaught in-flight exception", log)
    row["uncaught_exceptions"] = int(m.group(1)) if m else 0
    row["log_lines"] = len(log.splitlines())
    row["sqlite_mentions"] = len(re.findall(r"(?i)sqlite", log))
    row["sqlite_exception_lines"] = [
        l.strip()[:160] for l in log.splitlines() if "SQLiteException" in l or "android.database.sqlite" in l][:8]
    open(f"{run_dir}/console.log", "w").write(log)
    return row

def run_group(titles, n_runs, max_seconds, extra=None):
    st = load_state()
    for name in titles:
        apk, pkg = APKS[name]
        if pkg is None: pkg = pkg_of(apk)
        key = f"{name}"
        st["runs"].setdefault(key, {"apk": apk, "apk_sha256": hashlib.sha256(open(apk,'rb').read()).hexdigest(),
                                    "package": pkg, "runs": {}})
        store = f"{RUN}/store_{name}"
        if not os.path.isdir(f"{store}/data"):
            shutil.rmtree(store, ignore_errors=True); os.makedirs(store)
            subprocess.run([BIN, "install", apk, "--data-root", f"{store}/data"],
                           capture_output=True, text=True, timeout=300)
        for i in range(1, n_runs + 1):
            rkey = f"run{i}"
            if rkey in st["runs"][key]["runs"]:  # resumable
                continue
            rdir = f"{RUN}/{name}_run{i}"
            if os.path.exists(f"{rdir}/screenshot.png") and not os.path.exists(f"{rdir}/console.log"):
                # hashed earlier but console lost -> re-run cheaply only if needed
                row = {"screenshot_sha16": sha16(f"{rdir}/screenshot.png")}
            elif os.path.exists(f"{rdir}/console.log"):
                row = {"screenshot_sha16": sha16(f"{rdir}/screenshot.png"),
                       "verdict": (re.search(r"verdict=([A-Z_]+)", open(f'{rdir}/console.log').read()) or [None,None])[1],
                       "sqlite_exception_lines": [l.strip()[:160] for l in open(f'{rdir}/console.log') if "SQLiteException" in l][:8]}
            else:
                shutil.rmtree(rdir, ignore_errors=True)
                row = one_run(name, pkg, apk, rdir, store, max_seconds, extra)
            st["runs"][key]["runs"][rkey] = row
            save_state(st)
            print(f"{name} {rkey}: {row.get('screenshot_sha16')} verdict={row.get('verdict')} "
                  f"({row.get('seconds','?')}s)", flush=True)
    save_state(st)

def summarize(st):
    out = {"anchors": {}, "games": {}, "satellites": {}, "telegram": {}, "new": {}}
    for name, rec in st["runs"].items():
        shas = [r.get("screenshot_sha16") for r in rec["runs"].values()]
        verd = [r.get("verdict") for r in rec["runs"].values()]
        row = {"sha_x3": shas, "verdicts": verd, "package": rec.get("package")}
        if name in RECORDED_ANCHORS:
            row["recorded"] = RECORDED_ANCHORS[name]
            row["matches_recorded"] = all(s and (s == RECORDED_ANCHORS[name] or s.startswith(RECORDED_ANCHORS[name])) for s in shas)
            out["anchors"][name] = row
        elif name in RECORDED_GAMES:
            row["recorded"] = RECORDED_GAMES[name]
            row["matches_recorded"] = all(s and (s == RECORDED_GAMES[name] or s.startswith(RECORDED_GAMES[name])) for s in shas)
            out["games"][name] = row
        elif name in ("tower3d", "freebloks", "bouncy"):
            out["satellites"][name] = row
        elif name in ("forkgram", "telegram"):
            sql = [r.get("sqlite_exception_lines") for r in rec["runs"].values()]
            row["sqlite_exception_lines"] = sql
            row["sqlite_mentions"] = [r.get("sqlite_mentions") for r in rec["runs"].values()]
            out["telegram"][name] = row
        else:
            out["new"][name] = row
    return out

if __name__ == "__main__":
    group = sys.argv[1] if len(sys.argv) > 1 else "anchors_a"
    GROUPS = {
        "anchors_a": (["opencalc", "chess", "dooz"], 3, 90, None),
        "anchors_b": (["microtimer", "unote"], 3, 90, None),
        "games_a": (["2048", "mini-tetris", "minicraft"], 3, 110, ["--dump-view-tree"]),
        "games_b": (["snake-deluxe", "snake-neon", "tictactoe-deluxe"], 3, 110, ["--dump-view-tree"]),
        "satellites": (["tower3d", "freebloks", "bouncy"], 1, 110, ["--dump-view-tree"]),
        "telegram": (["forkgram", "telegram"], 1, 110, None),
    }
    if group in GROUPS:
        titles, n, ms, extra = GROUPS[group]
        run_group(titles, n, ms, extra)
        st = load_state()
        print(json.dumps(summarize(st).get(
            "anchors" if group.startswith("anchors") else
            "games" if group.startswith("games") else
            "telegram" if group == "telegram" else "satellites", {}), indent=1)[:2000])
    elif group == "summarize":
        st = load_state()
        print(json.dumps(summarize(st), indent=1))
    else:
        print("unknown group", group); sys.exit(2)
