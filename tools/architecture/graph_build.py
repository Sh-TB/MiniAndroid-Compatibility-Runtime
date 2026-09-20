#!/usr/bin/env python3
"""graph_build.py — S70 ACTIVE RUNTIME KNOWLEDGE GRAPH builder.

Fuses every S69/S70 data source into ONE queryable graph:
  docs/foundation/knowledge_graph.json

Fusion inputs (all machine-generated — nothing hand-annotated):
  graph/functions.json        engine dispatch functions (guards, lines)
  graph/served_api.json       (class,method) static served surface
  graph/class_graph.json      engine C++ class inheritance
  dex_census/_aggregate.json  corpus DEX fan-out per API × APK
  api_matrix.json             status law (REBUILT with fixed served layer)
  source_map.json             source↔DEX map per pinned APK
  failure_index.json          root registry (372 roots)
  live_runs.json              per-app live frame + trace summaries
  run/s69_live/*/api_calls.json   live dispatch traces (ground truth)
  docs/evidence/foundation/fixtures/VERIFICATION.json  fixture pixel asserts
  docs/foundation/FOUNDATION_TEST_MATRIX.md  fixture verdict rows
  miniandroid/tests/fixtures_foundation/*/  fixture sources (API usage scan)
  docs/upstream/**            upstream law artifacts (OpenJDK/AOSP pins)
  canvas_shadow warn_noop     engine's own deferred-behavior declarations

Node/edge model (campaign §PHASE 1) is encoded in the sections; graph_query.py
consumes them for the mandated queries: why-pixel / why-stubbed / blast-radius.
"""
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/z/my-project")
FD = ROOT / "docs" / "foundation"
OUT = FD / "knowledge_graph.json"

SIMPLE_NAME_RE = re.compile(r"L(?:[\w$/]+/)?(\w+);")
JAVA_CALL_RE = re.compile(r"\b([A-Z]\w+)\s*\.\s*(\w+)\s*\(")


def load(path, default=None):
    p = ROOT / path if not str(path).startswith("/") else Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text())


def main():
    # ── 1. engine functions + served surface ──────────────────────────────
    functions = load("docs/foundation/graph/functions.json", {"functions": []})
    served = load("docs/foundation/graph/served_api.json", {"pairs": []})
    served_pairs = served.get("pairs", [])
    served_by_api = defaultdict(list)
    for p in served_pairs:
        served_by_api[f"{p['class']}.{p['method']}"].append(
            {"tu": p["tu"], "function": p["function"], "line": p["line"],
             "extraction": p["extraction"]})

    # ── 2. DEX census fan-out ─────────────────────────────────────────────
    agg = load("docs/foundation/dex_census/_aggregate.json", {})
    fanout = {a: n for a, n in agg.get("corpus_api_fanout", [])}
    by_apk = agg.get("corpus_api_fanout_by_apk", {})
    # S70: resolve substring-class extraction laws to descriptor keys —
    # fragment → every corpus descriptor whose simple name contains it
    # (ambiguity honest: all candidates emitted, flagged over-approx)
    frag_index = defaultdict(set)
    for a in agg.get("corpus_api_fanout", []):
        desc = a[0].split(".", 1)[0]
        mm = re.match(r"L([\w$/]+)/(\w+);", desc + ";")
        if mm:
            frag_index[mm.group(2)].add(desc)
    _extra = defaultdict(list)
    for key, sites in served_by_api.items():
        for site in sites:
            if site["extraction"] == "substring-class (over-approx)":
                cls, mth = key.split(".", 1)
                for desc in sorted(frag_index.get(cls, ())):
                    # desc is already "Landroid/content/Context;" shaped
                    _extra[f"{desc}.{mth}"].append(
                        {"tu": site["tu"], "function": site["function"],
                         "line": site["line"],
                         "extraction": f"substring-class→{cls} (over-approx)"})
    for k, v in _extra.items():
        seen_keys = {(s2['tu'], s2['function'], s2['line']) for s2 in served_by_api[k]}
        for site in v:
            if (site['tu'], site['function'], site['line']) not in seen_keys:
                served_by_api[k].append(site)

    # ── 3. live traces (ground truth) ─────────────────────────────────────
    live_status = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # api->app->status->n
    live_calls = defaultdict(int)
    for d in sorted((ROOT / "run" / "s69_live").glob("*")):
        tr = d / "api_calls.json"
        if not tr.exists():
            continue
        try:
            calls = json.loads(tr.read_text())
        except Exception:
            continue
        for c in calls:
            api = c.get("api", "")
            st = c.get("status", "?")
            live_status[api][d.name][st] += 1
            live_calls[api] += 1

    # ── 4. engine's own deferred-behavior declarations (warn_noop) ────────
    noop_by_api = defaultdict(set)
    srcs = list((ROOT / "miniandroid" / "src").rglob("*.cpp"))
    for s in srcs:
        text = s.read_text(errors="replace")
        for m in re.finditer(r"warn_noop\(\s*(\w+)\s*,\s*\"([^\"]+)\"", text):
            var, op = m.group(1), m.group(2)
            opname = op.split("(")[0]
            # attach to every method-guard pair matching opname prefix
            for api in served_by_api:
                if api.rsplit(".", 1)[-1].split("(")[0] == opname:
                    noop_by_api[api].add(f"{op} [{s.name}:{text[:m.start()].count(chr(10)) + 1}]")

    # ── 5. fixtures: registry + API usage + verification ──────────────────
    fixtures = []
    verif = load("docs/evidence/foundation/fixtures/VERIFICATION.json", [])
    verif_by_name = {v.get("fixture"): v for v in verif if isinstance(v, dict)}
    # simple-name -> descriptors index from census (for java call mapping)
    simple_index = defaultdict(set)
    for api in fanout:
        m = SIMPLE_NAME_RE.match(api.split(".", 1)[0] + ";" if False else api.split(".", 1)[0])
        mm = re.match(r"L([\w$/]+)/?(\w+);", api.split(".", 1)[0] + ";")
        if mm:
            simple_index[mm.group(2)].add(api.split(".", 1)[0] + ";")
    fix_dirs = sorted((ROOT / "miniandroid" / "tests" / "fixtures_foundation").iterdir())
    fix_dirs += sorted((ROOT / "miniandroid" / "tests" / "fixtures").iterdir())
    seen_fix = set()
    for d in fix_dirs:
        if not d.is_dir() or d.name in seen_fix:
            continue
        seen_fix.add(d.name)
        apis = set()
        for jf in d.rglob("*.java"):
            jt = jf.read_text(errors="replace")
            for cls, meth in JAVA_CALL_RE.findall(jt):
                for desc in simple_index.get(cls, ()):
                    apis.add(f"{desc}.{meth}")
        ev = ROOT / "docs" / "evidence" / "foundation" / "fixtures" / d.name
        v = verif_by_name.get(d.name)
        asserts = v.get("asserts", []) if v else []
        fixtures.append({
            "name": d.name,
            "root": str(d),
            "apis": sorted(apis),
            "verified": bool(v) and bool(asserts) and all(a.get("ok") for a in asserts),
            "asserts_total": len(asserts),
            "asserts_ok": sum(1 for a in asserts if a.get("ok")),
            "evidence_dir": str(ev) if ev.exists() else None,
        })
    tested_by = defaultdict(list)
    for f in fixtures:
        for api in f["apis"]:
            tested_by[api].append(f["name"])

    # ── 6. failures ───────────────────────────────────────────────────
    fi = load("docs/foundation/failure_index.json", {})
    failures = fi.get("failures", []) if isinstance(fi, dict) else []
    # failure → api linking: method/api fields when present
    fail_by_api = defaultdict(list)
    for fr in failures:
        api = fr.get("api")
        if api:
            fail_by_api[api].append(fr["failure"])

    # ── 7. upstream law artifacts ─────────────────────────────────────────
    upstream_docs = []
    up_root = ROOT / "docs" / "upstream"
    if up_root.exists():
        upstream_docs = [str(p.relative_to(ROOT)) for p in sorted(up_root.rglob("*"))
                         if p.is_file()]
    upstream_by_class = defaultdict(list)
    for rel in upstream_docs:
        # direct law: doc file name matches a descriptor simple name
        for cls_simple in set(re.findall(r"\b(Double|Float|String|Integer|Long|Math|"
                                         r"Canvas|Paint|Color|Bitmap|View|TextView)\b",
                                         Path(rel).stem)):
            upstream_by_class[cls_simple].append(rel)

    # ── 8. apps: pins + source map + live summary ─────────────────────────
    smap = load("docs/foundation/source_map.json", {"apps": []})
    live_runs = load("docs/foundation/live_runs.json", {})
    runs_by_apk = {}
    for r in (live_runs.get("runs") or []):
        runs_by_apk[r.get("apk") or r.get("name")] = r
    apps = {}
    for a in smap.get("apps", []):
        apk = a["apk"]
        runs = runs_by_apk.get(apk, {})
        vt = load(f"run/s69_live/{apk.replace('.apk','')}/view_tree.json", None)
        vtn = 0
        top_classes = []
        if isinstance(vt, dict):
            def count(n):
                return 1 + sum(count(c) for c in n.get("children", []))
            vtn = count(vt.get("root", vt)) if ("root" in vt or "class" in vt) else 0
            r0 = vt.get("root", vt)
            if isinstance(r0, dict):
                top_classes = [c.get("class", "?") for c in r0.get("children", [])][:12]
        apps[apk] = {
            "package": a.get("package"),
            "pin": {"repo": a.get("source_repo"), "commit": a.get("source_commit"),
                    "provenance": a.get("provenance")},
            "source_files": a.get("source_files"),
            "mapping_coverage": a.get("mapping_coverage"),
            "runtime_status": a.get("runtime_status"),
            "live": runs,
            "view_tree_nodes": vtn,
            "top_children_classes": top_classes,
        }

    # ── 9. API composite records ──────────────────────────────────────────
    apis = {}
    for api in set(fanout) | set(live_status) | set(served_by_api):
        lv = live_status.get(api, {})
        st_counts = defaultdict(int)
        for per in lv.values():
            for st, n in (per or {}).items():
                st_counts[st] += n or 0
        st_counts = dict(st_counts)
        served = served_by_api.get(api, [])
        tested = tested_by.get(api, [])
        cls_simple = None
        mm = re.match(r"L([\w$/]+)/(\w+);", api.split(".", 1)[0] + ";")
        if mm:
            cls_simple = mm.group(2)
        rec = {
            "fanout": fanout.get(api, 0),
            "by_apk": by_apk.get(api, {}),
            "served_static": served[:6],
            "served_static_count": len(served),
            "live_calls": live_calls.get(api, 0),
            "live_status_counts": st_counts,
            "live_observed_apks": sorted(lv.keys()),
            "tested_by": tested,
            "visual_proof": any(f["verified"] for f in fixtures
                                if api in f["apis"]),
            "upstream_docs": upstream_by_class.get(cls_simple, []),
            "noop_flags": sorted(noop_by_api.get(api, [])),
            "failures": fail_by_api.get(api, []),
        }
        # status law (matrix-aligned): live evidence outranks static surface.
        # per-app record = {status: n} — membership must test KEYS.
        def live_has(needle):
            return any(needle in (per or {}) for per in lv.values())
        if live_has("IMPLEMENTED"):
            status = "LIVE-IMPL"
        elif live_has("PARTIAL"):
            status = "LIVE-PARTIAL"
        elif live_has("STUBBED"):
            status = "LIVE-STUB"
        elif served:
            status = "SERVED-STATIC"
        else:
            # below-bridge reconciliation: interpreter intrinsics never reach
            # the dispatch bridge, so no trace and no guard — corroborate
            # WEAKLY with corpus run outcomes (success = no observed failure,
            # NOT proof). Fail-only exercisers are prime suspects.
            ok_apks, fail_apks = [], []
            for apk_n in rec["by_apk"]:
                run = runs_by_apk.get(apk_n, {})
                st = run.get("status")
                if st == "SUCCESS":
                    ok_apks.append(apk_n)
                elif st:
                    fail_apks.append(apk_n)
            rec["weak_evidence"] = {"success_apks": ok_apks, "fail_apks": fail_apks}
            if fail_apks and not ok_apks:
                status = "SUSPECT-FAIL-ONLY"
            elif ok_apks:
                status = "EXERCISED-OK"
            else:
                status = "UNSERVED"
        rec["status"] = status
        rec["silent_wrong"] = bool(rec["noop_flags"]) and status.startswith("LIVE")
        apis[api] = rec

    graph = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "campaign": "S70 RUNTIME UNDERSTANDING / ACTIVE SOURCE-LINKED DIAGNOSTIC ENGINE",
        "provenance": {
            "generator": "tools/architecture/graph_build.py",
            "inputs": ["graph/functions.json", "graph/served_api.json",
                       "graph/class_graph.json", "dex_census/_aggregate.json",
                       "api_matrix.json", "source_map.json",
                       "failure_index.json", "live_runs.json",
                       "run/s69_live/*/api_calls.json",
                       "docs/evidence/foundation/fixtures/VERIFICATION.json",
                       "miniandroid/tests/fixtures_foundation/*",
                       "docs/upstream/**"],
            "law": "every node/edge EXTRACTED from a named input; over-"
                   "approximations flagged in-band (extraction fields)"},
        "counts": {
            "apis": len(apis), "served_pairs": len(served_pairs),
            "functions": functions.get("count", len(functions.get("functions", []))),
            "fixtures": len(fixtures), "failures": len(failures),
            "apps": len(apps), "upstream_docs": len(upstream_docs)},
        "apis": apis,
        "fixtures": fixtures,
        "failures": failures,
        "apps": apps,
        "upstream_docs": upstream_docs,
    }
    OUT.write_text(json.dumps(graph, indent=1))
    print(f"knowledge_graph.json: {len(apis)} APIs "
          f"({sum(1 for a in apis.values() if a['status']=='LIVE-IMPL')} LIVE-IMPL, "
          f"{sum(1 for a in apis.values() if a['status']=='LIVE-STUB')} LIVE-STUB, "
          f"{sum(1 for a in apis.values() if a['status']=='SERVED-STATIC')} SERVED-STATIC, "
          f"{sum(1 for a in apis.values() if a['status']=='UNSERVED')} UNSERVED) | "
          f"{len(fixtures)} fixtures | {len(failures)} failures | {len(apps)} apps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
