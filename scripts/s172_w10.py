#!/usr/bin/env python3
"""s172_w10.py — S172 W10 wave: the TB uncaught NPE frontier
(Fragment$$ExternalSyntheticLambda0.run invoke_pc=0xf5 →
NotificationChannelManager.$r8$lambda → List.iterator on the NULL
NotificationManager.getNotificationChannelGroups() result).

Phases (mirror s170_w9_gates.py):
  tb_pre   — probe build (env MINIANDROID_W10_PROBE=1) TB run, PRE record
  tb_post  — law build TB run, POST record (fresh stores both)
  gates    — microtimer/g2048/opencalc anchors + dooz + TG pairs
  verdict  — assemble S172_W10_VERDICT.json
"""
import json
import os
import re
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s167_w6_gates as g
import s165_trains as t
import s166_trains as s166

g.REF = BASE / ("upload/_ma_local_backup/"
                "miniandroid_s170_w9_4bb7c4d424923b87.bin")
g.NEW = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s172_w10"
g.OUT.mkdir(parents=True, exist_ok=True)
g.EVID = BASE / "evidence/s172_w10"
g.EVID.mkdir(parents=True, exist_ok=True)

TB_APK = BASE / "upload/net.thunderbird.android_33.apk"
TB_PKG = "net.thunderbird.android"
SEED_SKIP = {"MINIANDROID_APP_DATA_SEED": "1",
             "MINIANDROID_PROVIDER_SKIP":
                 "FirebaseInitProvider,MlKitInitProvider"}


def sha16(p):
    return t.sha16(p)


def census(tag):
    con = g.OUT / f"{tag}.err"
    if not con.exists():
        return {}
    txt = con.read_text(errors="replace")
    return {
        "uncaught_rows": len(re.findall(r"UNCAUGHT", txt)),
        "ndfe": len(re.findall(r"NoDefinitionFoundException", txt)),
        "npe_unwind": len(re.findall(
            r"NullPointerException; unwound "
            r"Landroidx/fragment/app/Fragment\$\$ExternalSyntheticLambda0;", txt)),
        "npe_ncm_lambda": len(re.findall(
            r"NotificationChannelManager;\.\$r8\$lambda"
            r"\$m3LNel5iYKrrYmwu_gXHemecIYY pc=", txt)),
        "w10_probe_rows": len(re.findall(r"\[W10-PROBE\]", txt)),
        "w10_law_rows": len(re.findall(r"\[W10-NCGroups\]", txt)),
        "f578": len(re.findall(r"F-C4-578", txt)),
        "f574": len(re.findall(r"F-C4-574", txt)),
        "f581": len(re.findall(r"F-C4-581", txt)),
        "f582": len(re.findall(r"F-C4-582", txt)),
        "vme": len(re.findall(r"VirtualMachineError", txt)),
        "upgrade_failed": len(re.findall(r"Storage database upgrade failed", txt)),
        "probe_unhandled_groups": len(re.findall(
            r"\[W10-PROBE\] NotificationManager\.getNotificationChannelGroups",
            txt)),
        "probe_unhandled_channels": len(re.findall(
            r"\[W10-PROBE\] NotificationManager\.getNotificationChannels",
            txt)),
        "probe_lines": re.findall(r"\[W10-PROBE\][^\n]{0,160}", txt)[:24],
        "law_lines": re.findall(r"\[W10-NCGroups\][^\n]{0,160}", txt)[:12],
    }


def tb_run(tag, bin_path, probe_env=False):
    for k in g.CLEAN_ENVS:
        os.environ.pop(k, None)
    os.environ.update(SEED_SKIP)
    if probe_env:
        os.environ["MINIANDROID_W10_PROBE"] = "1"
    store = g.OUT / f"store_{tag}"   # fresh store per arm (S156/S169 law)
    assert t.ensure_store(TB_APK, store, bin_path, TB_PKG), f"install fail {tag}"
    rundir = g.OUT / tag
    console = g.OUT / f"{tag}.err"
    cmd = [str(bin_path), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", "100", "--frames", "8",
           "--trace", "--package", TB_PKG]
    t0 = __import__("time").time()
    with open(console, "w") as cf:
        import subprocess
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       timeout=190)
    wall = round(__import__("time").time() - t0, 1)
    shot = rundir / "screenshot.png"
    text = console.read_text(errors="replace")
    row = {
        "tag": tag, "bin": sha16(bin_path), "wall_s": wall,
        "stderr_sha16": sha16(console) if console.exists() else None,
        "screenshot_face": sha16(shot) if shot.exists() else None,
        "uncaught": len(re.findall(r"UNCAUGHT", text)),
        "ndfe": len(re.findall(r"NoDefinitionFoundException", text)),
        "frames": re.findall(r"Frames Rendered: (\d+)", text)[-1:],
        "census": census(tag),
    }
    ts = rundir / "trace_summary.json"
    if ts.exists():
        try:
            s = json.load(open(ts))
            fa = s.get("frame_analysis") or {}
            row["app_owned_pixels"] = fa.get("app_owned_pixels")
            row["final_state"] = (s.get("lifecycle") or {}).get("final_state")
        except Exception:
            pass
    at = rundir / "api_trace.json"
    if at.exists():
        try:
            row["api_calls"] = json.load(open(at)).get("total_calls")
        except Exception:
            pass
    for k in list(SEED_SKIP) + (["MINIANDROID_W10_PROBE"] if probe_env else []):
        os.environ.pop(k, None)
    return row


def save(name, payload):
    out = g.EVID / name
    json.dump(payload, open(out, "w"), indent=1, default=str)
    print("evidence ->", out)


def show(tag, row):
    print(f"[{tag}] bin={row['bin']} face={row['screenshot_face']} "
          f"wall={row['wall_s']}s uncaught={row['uncaught']} "
          f"ndfe={row['ndfe']} api={row.get('api_calls')} "
          f"pixels={row.get('app_owned_pixels')} "
          f"state={row.get('final_state')}", flush=True)
    c = {k: v for k, v in row["census"].items()
         if not k.endswith("_lines")}
    print("   census:", json.dumps(c), flush=True)


if __name__ == "__main__":
    phase = sys.argv[1]
    if phase == "tb_pre":
        row = tb_run("tb_pre", g.NEW, probe_env=True)
        show("tb_pre", row)
        save("S172_W10_TB_PRE.json", row)
    elif phase == "tb_post":
        row = tb_run("tb_post", g.NEW, probe_env=True)
        show("tb_post", row)
        save("S172_W10_TB_POST.json", row)
    elif phase.startswith("gates"):
        out = g.EVID / "S172_W10_GATES.json"
        cur = {}
        if out.exists():
            cur = json.load(open(out))
        if phase in ("gates", "gates_anchors"):
            rows = {"microtimer": g.anchor_pair("microtimer"),
                    "g2048": g.anchor_pair("g2048"),
                    "opencalc": g.anchor_pair("opencalc")}
            cur.setdefault("anchors", {}).update(rows)
            for k, v in rows.items():
                print(k, json.dumps(v)[:220])
        if phase in ("gates", "gates_dooz"):
            ctl = s166.dooz_run("w10_dz_ctl", g.REF, store_root=g.OUT)
            fix = s166.dooz_run("w10_dz_fix", g.NEW, store_root=g.OUT)
            cur["w10_dz_ctl"] = ctl
            cur["w10_dz_fix"] = fix
            cur["w10_dz_summary"] = s166.pair_summary(ctl, fix)
            print("dooz:", json.dumps(s166.pair_summary(ctl, fix))[:300])
        if phase in ("gates", "gates_tg"):
            tctl = s166.tg_run("w10_tg_ctl", g.REF, store_name="s172_tg")
            tfix = s166.tg_run("w10_tg_fix", g.NEW, store_name="s172_tg")
            cur["w10_tg_ctl"] = tctl
            cur["w10_tg_fix"] = tfix
            cur["w10_tg_summary"] = s166.pair_summary(tctl, tfix)
            print("tg:", json.dumps(s166.pair_summary(tctl, tfix))[:300])
        json.dump(cur, open(out, "w"), indent=1, default=str)
    elif phase == "verdict":
        pre = json.load(open(g.EVID / "S172_W10_TB_PRE.json"))
        post = json.load(open(g.EVID / "S172_W10_TB_POST.json"))
        gt = json.load(open(g.EVID / "S172_W10_GATES.json"))
        verdict = {
            "ref_bin": sha16(g.REF), "law_bin": sha16(g.NEW),
            "pre": {k: pre[k] for k in
                    ("bin", "screenshot_face", "wall_s", "uncaught", "ndfe",
                     "api_calls") if k in pre},
            "post": {k: post[k] for k in
                     ("bin", "screenshot_face", "wall_s", "uncaught", "ndfe",
                      "api_calls") if k in post},
            "gates": gt.get("anchors", {}),
            "dooz": gt.get("w10_dz_summary"),
            "tg": gt.get("w10_tg_summary"),
        }
        save("S172_W10_VERDICT.json", verdict)
        print(json.dumps(verdict, indent=1, default=str)[:2000])
