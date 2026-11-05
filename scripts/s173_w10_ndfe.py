#!/usr/bin/env python3
"""s173_w10_ndfe.py — S173: the TB residual Koin NDFE family (S172 PINNED
NEXT #1) — probe-first decode + formal verification battery.

FINDING (pre-registered in the probe evidence): the single residual
NoDefinitionFoundException is FAITHFUL-BY-DESIGN app behavior:
  - TB's MultiFeatureFlagProvider definition factory (R8-merged lambda,
    decoded CoreCommonModuleKt$$ExternalSyntheticLambda1.invoke branch
    0x010a-0x01a0) builds its provider list as
      getOrNull<BaseCatalogFeatureFlagProvider>(InjectQualifier.InMemory)
        ?.let(::add)                       <- optional variant probe
      + resolve<BaseCatalogFeatureFlagProvider>(InjectQualifier.Local)
      + resolve<BundledCatalogFeatureFlagProvider>(null)
  - the APK registers ONLY the ':local:' variant (dex-wide scan: ZERO
    ':inmemory:' registration sites for BaseCatalogFeatureFlagProvider);
  - the Koin index is a DESUGARED j$/util/concurrent/ConcurrentHashMap
    (resolveDefinition$koin_core, R8-merged into EventRecodingLogger);
    the [S173-CHM-*] interpreter probe proves the load-time put of
    "…BaseCatalogFeatureFlagProvider:local:_root_" and the byte-exact
    resolution-time lookup keys — ':inmemory:' misses BY DESIGN,
    ':local:' hits (exactly one NDFE, caught at Scope.getOrNull).

NO code law required; this script runs the no-behavior-change battery:
  tb_pre   — REF  = fea1759d58653d41 (S172 NCGroups standing binary)
  tb_post  — NEW  = current build (probe code env-gated, run WITHOUT env)
  gates    — microtimer/g2048/opencalc anchors + dooz + TG pairs
  verdict  — S173_W10_NDFE_VERDICT.json
"""
import json
import re
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s167_w6_gates as g
import s165_trains as t
import s166_trains as s166
import s172_w10 as s172

g.REF = BASE / ("upload/_ma_local_backup/"
                "miniandroid_s172_ncgroups_fea1759d58653d41.bin")
g.NEW = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s173_w10"
g.OUT.mkdir(parents=True, exist_ok=True)
g.EVID = BASE / "evidence/s173_w10"
g.EVID.mkdir(parents=True, exist_ok=True)


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
        row = s172.tb_run("tb_pre", g.REF, probe_env=False)
        show("tb_pre", row)
        save("S173_W10_NDFE_TB_PRE.json", row)
    elif phase == "tb_post":
        row = s172.tb_run("tb_post", g.NEW, probe_env=False)
        show("tb_post", row)
        save("S173_W10_NDFE_TB_POST.json", row)
    elif phase.startswith("gates"):
        out = g.EVID / "S173_W10_NDFE_GATES.json"
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
            ctl = s166.dooz_run("w10ndfe_dz_ctl", g.REF, store_root=g.OUT)
            fix = s166.dooz_run("w10ndfe_dz_fix", g.NEW, store_root=g.OUT)
            cur["w10ndfe_dz_ctl"] = ctl
            cur["w10ndfe_dz_fix"] = fix
            cur["w10ndfe_dz_summary"] = s166.pair_summary(ctl, fix)
            print("dooz:", json.dumps(s166.pair_summary(ctl, fix))[:300])
        if phase in ("gates", "gates_tg"):
            tctl = s166.tg_run("w10ndfe_tg_ctl", g.REF,
                               store_name="s173_tg")
            cur["w10ndfe_tg_ctl"] = tctl
            save("S173_W10_NDFE_GATES.json", cur)
            tfix = s166.tg_run("w10ndfe_tg_fix", g.NEW,
                               store_name="s173_tg")
            cur["w10ndfe_tg_fix"] = tfix
            cur["w10ndfe_tg_summary"] = s166.pair_summary(tctl, tfix)
            print("tg:", json.dumps(s166.pair_summary(tctl, tfix))[:300])
        save("S173_W10_NDFE_GATES.json", cur)
    elif phase == "verdict":
        pre = json.load(open(g.EVID / "S173_W10_NDFE_TB_PRE.json"))
        post = json.load(open(g.EVID / "S173_W10_NDFE_TB_POST.json"))
        gates = json.load(open(g.EVID / "S173_W10_NDFE_GATES.json"))
        anchors = gates.get("anchors", {})
        pin = anchors.get("microtimer", {})
        verdict = {
            "wave": "S173 W10-NDFE",
            "ref_bin": "fea1759d58653d41",
            "new_bin": t.sha16(g.NEW),
            "finding": (
                "FAITHFUL-BY-DESIGN: the TB residual Koin NDFE is the app's "
                "own optional-variant probe — MultiFeatureFlagProvider's "
                "factory does getOrNull<BaseCatalogFeatureFlagProvider>("
                "InjectQualifier.InMemory); the APK registers ONLY the "
                "':local:' variant (dex-wide scan: zero ':inmemory:' "
                "registration sites), so exactly ONE NoDefinitionFoundException "
                "is thrown at Scope.resolveFromContext pc=734 and caught by "
                "Scope.getOrNull. The Koin index is a desugared "
                "j$/util/concurrent/ConcurrentHashMap; the S173 interpreter "
                "probe proves the load-time put AND the resolution-time "
                "lookup keys are byte-exact ('…BaseCatalog…:local:_root_' "
                "put == get; ':inmemory:' has no entry). NO runtime gap; "
                "NO code law; census row reclassified."),
            "law": ("S173 NDFE-PROBE law: NoDefinitionFoundException from "
                    "the ':inmemory:' BaseCatalogFeatureFlagProvider lookup "
                    "is faithful app behavior (caught at getOrNull, provider "
                    "list continues with the ':local:' + BundledCatalog "
                    "variants); never suppress, never fake the definition."),
            "pre": {"bin": pre["bin"], "face": pre["screenshot_face"],
                    "uncaught": pre["uncaught"], "ndfe": pre["ndfe"],
                    "api": pre.get("api_calls")},
            "post": {"bin": post["bin"], "face": post["screenshot_face"],
                     "uncaught": post["uncaught"], "ndfe": post["ndfe"],
                     "api": post.get("api_calls")},
            "face_equal": pre["screenshot_face"] == post["screenshot_face"],
            "uncaught_equal": pre["uncaught"] == post["uncaught"],
            "gates": gates,
            "microtimer_pin": pin.get("screenshot_face"),
        }
        save("S173_W10_NDFE_VERDICT.json", verdict)
        print(json.dumps({k: v for k, v in verdict.items()
                          if k not in ("gates",)}, indent=1)[:1200])
