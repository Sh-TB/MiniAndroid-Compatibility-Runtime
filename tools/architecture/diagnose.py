#!/usr/bin/env python3
"""diagnose.py — S70 FAILURE AUTO-TRACE / automatic drill-down (§PHASE 2+17).

Usage:
  diagnose <failure-id>            registry-driven diagnostic bundle
  diagnose --live <app> [frame]    live-run anomaly chain (per-frame evidence)

Every section prints REAL data from the fused knowledge graph / registry /
census / source map / live artifacts. When a link has no evidence it prints
`GAP:` + what is needed — a missing link is reported, never invented (§25).

FIRST DIVERGENCE law: the chain walks UPSTREAM (pixel → render → view/layout →
resource → API → implementation → source), reporting the FIRST level whose
expected semantics diverge from observed — not the final wrong pixel.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/z/my-project")
GRAPH = ROOT / "docs" / "foundation" / "knowledge_graph.json"


def load(p, d=None):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else d


def freshest_live_base():
    """S71 fix: prefer the NEWEST live-run generation (s71_live > s69_live).
    Previously s69_live was hardcoded → the RENDER/API sections could cite
    stale pre-fix artifacts (S71 W7: stale-data false-lead found in the
    F-136 bundle, which showed the S69 golden sha while the current binary
    deterministically produces the R-NEW-389 sha)."""
    for gen in ("s71_live", "s69_live"):
        base = ROOT / "run" / gen
        if base.exists() and any(base.iterdir()):
            return base
    return ROOT / "run" / "s69_live"


def resolve_app_dir(appkey):
    """fuzzy: 'tripeaks' → run/<newest-live>/tripeaks_v1.2.1_vc4/"""
    base = freshest_live_base()
    if not appkey:
        return None
    d = base / appkey
    if d.exists():
        return d
    for c in sorted(base.glob("*")):
        if appkey in c.name:
            return c
    return None


def census_for(apk):
    for c in (ROOT / "docs/foundation/dex_census").glob("*.json"):
        if c.name.startswith("_"):
            continue
        if apk.replace(".apk", "") in c.name or c.name == apk:
            return load(c, {})
    return {}


def section(title):
    print(f"\n=== {title} ===")


def diagnose_failure(g, fid):
    frs = [f for f in g["failures"] if f.get("failure") == fid]
    if not frs:
        print(f"unknown failure {fid}")
        return 1
    fr = frs[0]
    apk = fr.get("apk")
    api = fr.get("api")

    section("FAILURE")
    for k in ("failure", "status", "priority", "apk", "source_commit",
              "runtime_commit"):
        if fr.get(k):
            print(f"  {k}: {fr[k]}")

    section("FIRST DIVERGENCE")
    exp, obs = fr.get("expected"), fr.get("observed")
    if exp or obs:
        print(f"  expected: {exp}")
        print(f"  observed: {obs}")
        print("  (registry-recorded divergence; walk upstream below to the "
              "contract that defines 'expected')")
    else:
        print("  GAP: registry records no explicit expected/observed pair — "
              "first_divergence requires a micro fixture reproducing this "
              "failure with asserted semantics")

    section("DEX")
    if apk:
        dc = census_for(apk)
        if dc:
            print(f"  apk={apk} classes={dc.get('app_classes')} "
                  f"methods={dc.get('app_methods')} "
                  f"api_call_sites={dc.get('api_call_sites')}")
            target = fr.get("method")
            if target:
                sites = [s for s in dc.get("api_sites", [])
                         if s.get("method") == target]
                for s in sites[:5]:
                    print(f"  call site: {s['target_class']}->"
                          f"{s['method']}{s.get('descriptor','')} "
                          f"×{s['call_sites']}")
            ma = dc.get("method_apis", {})
            hits = [m for m, apis in ma.items() if api and any(api.split(".", 1)[0] in a2 for a2 in apis)]
            for h in hits[:5]:
                print(f"  caller method: {h} → {ma[h][:3]}")
        else:
            print(f"  GAP: no census for {apk}")
    else:
        print("  GAP: failure not pinned to an APK")

    section("CLASS / METHOD")
    if fr.get("method"):
        print(f"  method: {fr['method']}")
    smap = load(ROOT / "docs/foundation/source_map.json", {"apps": []})
    sapp = None
    for a in smap.get("apps", []):
        if apk and (apk in a["apk"] or a["apk"] in str(apk)):
            sapp = a
            break
    if sapp:
        print(f"  source pin: {sapp.get('source_repo')} @ {sapp.get('source_commit')}")
        print(f"  mapping coverage: {sapp.get('mapping_coverage')}")
        # source file for the failing class if recorded in the method string
        m = fr.get("method") or ""
        for sf in (sapp.get("source_to_dex") or {}):
            if m and m.split(".")[0] in sf:
                print(f"  candidate source file: {sf}")

    section("API")
    rec = g["apis"].get(api) if api else None
    if rec:
        print(f"  {api}: {rec['status']} "
              f"sites={rec['fanout']} apks={len(rec['by_apk'])} "
              f"live_calls={rec['live_calls']}")
        if rec["noop_flags"]:
            print(f"  deferred-ops: {rec['noop_flags']}")
    else:
        print(f"  GAP: failure carries no machine-resolvable API "
              f"({'no api field' if not api else api + ' not in graph'})")

    section("IMPLEMENTATION")
    if rec and rec["served_static"]:
        for s in rec["served_static"][:4]:
            print(f"  {s['tu']}:{s['line']} in {s['function']}() "
                  f"[{s['extraction']}]")
    elif rec:
        print("  GAP: no served surface — API not implemented at the bridge "
              "layer (or handled below-bridge intrinsically)")
    else:
        print("  GAP: no API link")

    section("CALLERS")
    if rec and rec["by_apk"]:
        for a, n in sorted(rec["by_apk"].items(), key=lambda kv: -kv[1])[:6]:
            print(f"  {a}: {n} static call sites")
    else:
        print("  GAP: no census callers")

    section("CONSUMERS")
    if rec and rec["tested_by"]:
        print(f"  fixtures: {', '.join(rec['tested_by'][:8])}")
    else:
        print("  GAP: no fixture exercises this API")
    if sapp:
        print(f"  real APK consumer: {sapp['apk']} (pin {sapp.get('source_commit')})")

    section("STATE CHANGE")
    if obs and any(w in str(obs).lower() for w in
                   ("state", "text", "count", "flag", "value")):
        print(f"  registry-observed: {obs}")
    else:
        print("  GAP: no state mutation evidence recorded (needs a state-"
              "asserting fixture: input → listener → mutation → invalidate)")

    section("VIEW / LAYOUT")
    appdir = resolve_app_dir(apk or "")
    vt = load(appdir / "view_tree.json") if appdir else None
    if vt and isinstance(vt, dict) and vt.get("nodes"):
        nodes = vt["nodes"]
        print(f"  live ViewTree nodes: {vt.get('view_count', len(nodes))}")
        tops = [n.get("class", "?") for n in nodes if not n.get("parent_id")]
        print(f"  top classes: {tops[:8]}")
        for n in nodes[:4]:
            print(f"    {n.get('class','?')} @({n.get('x')},{n.get('y')}) "
                  f"{n.get('width')}x{n.get('height')} vis={n.get('visibility')}")
    else:
        print("  GAP: no live view_tree.json for this app")

    section("RENDER")
    lr = load(ROOT / "docs/foundation/live_runs.json", {"runs": []})
    appkey = (apk or "").replace(".apk", "")
    run = next((r for r in lr.get("runs", []) if appkey and appkey in r.get("apk", "")),
               None) if appkey else None
    if run:
        shot = run.get("screenshot") or {}
        frames = run.get("frames") or []
        uniq = {f["sha256"] for f in frames}
        print(f"  live: status={run.get('status')} nonwhite={shot.get('nonwhite')} "
              f"frames={len(frames)} distinct_shas={len(uniq)}")
        for f in frames[:3]:
            print(f"    {f['frame']}: nonwhite={f['nonwhite']} sha={f['sha256'][:16]}")
    else:
        print("  GAP: no live run summary")

    section("UPSTREAM LAW")
    up = (fr.get("root_cause") or "") + " " + (fr.get("evidence") or "")
    i = up.find("UPSTREAM:")
    if i >= 0:
        seg = up[i + len("UPSTREAM:"):]
        for stop in ("LAW:", "PLAN:", "EVIDENCE:"):
            j = seg.find(stop)
            if j >= 0:
                seg = seg[:j]
        print(f"  {seg.strip()[:300]}")
    if rec and rec["upstream_docs"]:
        print(f"  docs: {', '.join(rec['upstream_docs'][:4])}")
    if i < 0 and not (rec and rec["upstream_docs"]):
        print("  GAP: upstream law not pinned for this failure's API")

    section("EXISTING TESTS")
    if rec and rec["tested_by"]:
        print(f"  {rec['tested_by']}")
    else:
        print("  none")

    section("MISSING TEST")
    if rec and not rec["tested_by"] and api:
        print(f"  → fixture needed: {api.split('.', 1)[0].split('/')[-1]}"
              f"_{api.rsplit('.', 1)[-1].split('(')[0]} (micro: construct → "
              f"call → assert state + pixel + ViewTree; determinism ×3)")
    elif rec and rec["tested_by"]:
        print("  covered (see EXISTING TESTS); extend only if semantics "
              "outgrow the current asserts")
    else:
        print("  GAP: cannot map failure to a single API — fixture design "
              "needs the reproduction chain first")

    section("FANOUT")
    if rec:
        print(f"  static sites: {rec['fanout']} across {len(rec['by_apk'])} APKs; "
              f"layer: {api.split(';')[0] + ';' if api else '?'}")
        print(f"  fix blast radius: {'CORPUS-WIDE' if rec['fanout'] > 100 else 'LOCAL'}")

    section("LIKELY ROOT CAUSE")
    rc = fr.get("root_cause")
    if rc:
        print(f"  (registry, evidence-backed): {rc[:400]}")
    else:
        print("  GAP: no root cause recorded — this failure needs "
              "investigation; do NOT guess (§0)")

    section("EVIDENCE")
    for path in [
        "docs/foundation/FOUNDATION_GAP_MATRIX.md",
        "docs/foundation/FOUNDATION_RENDER_MATRIX.md",
        "docs/foundation/FOUNDATION_LAYOUT_MATRIX.md",
        "docs/evidence/foundation/fixtures/",
        str(appdir or "") + "/" if appdir else "run/s69_live/ (no dir resolved)",
    ]:
        p = ROOT / path
        if p.exists():
            print(f"  {path}")
    print()
    return 0


def diagnose_live(g, app, frame=None):
    section("LIVE ANOMALY — " + app)
    a = g["apps"].get(app)
    if not a:
        cand = [k for k in g["apps"] if app in k]
        if len(cand) == 1:
            app, a = cand[0], g["apps"][cand[0]]
        else:
            print(f"unknown app {app}")
            return 1
    print(f"  pin: {a['pin'].get('repo')} @ {a['pin'].get('commit')}")
    appdir = resolve_app_dir(app)  # S71: freshest live generation
    live = a.get("live") or {}
    shot = live.get("screenshot") or {}
    frames = live.get("frames") or []
    shas = {f["sha256"] for f in frames}
    print(f"  run status: {live.get('status')}  rc_zero={live.get('rc_zero')}")
    print(f"  frames: {len(frames)} ({len(shas)} distinct) "
          f"nonwhite(s)={sorted({f['nonwhite'] for f in frames})}")

    # FIRST DIVERGENCE classification (S66 forensics law)
    tr = load(appdir / "api_calls.json", []) if appdir else []
    stubs = [e for e in tr if e.get("status") == "STUBBED"]
    impl_fail = [e for e in tr if e.get("status") not in ("STUBBED", "IMPLEMENTED")]
    section("FIRST DIVERGENCE (live classification)")
    if frames and all(f["nonwhite"] == 0 for f in frames):
        if shas and len(shas) == 1:
            print("  ALL FRAMES IDENTICAL + BLANK → composition produced no "
                  "pixels: suspect chain = resource/inflate → view creation "
                  "→ measure/layout → render entry (check ViewTree below)")
        else:
            print("  ALL FRAMES BLANK but CHANGING → traversal runs, nothing "
                  "draws: suspect = visibility/alpha/color resolution")
    elif frames and len(shas) > 1:
        print("  FRAMES CHANGING WITH INK → render loop alive; divergence "
              "suspects: per-frame API stubs + input/state effects")
    print(f"  live STUBBED dispatches: {len(stubs)} "
          f"(top: {_top_api(stubs)})")
    if impl_fail:
        print(f"  live other-status dispatches: {len(impl_fail)}")

    vt = load(appdir / "view_tree.json") if appdir else {}
    section("VIEW / LAYOUT")
    if vt:
        def count(n):
            if not isinstance(n, dict):
                return 0
            return 1 + sum(count(c) for c in n.get("children", []) or [])
        r = vt.get("root", vt)
        n = count(r)
        print(f"  ViewTree nodes: {n}")
        if n == 0:
            print("  GAP: EMPTY VIEW TREE → divergence at inflate/compose, "
                  "NOT at renderer")
        else:
            print("  ViewTree exists → if pixels wrong, divergence is at "
                  "geometry/render, NOT inflation (renderer-first debugging "
                  "is FORBIDDEN by this verdict)")

    section("API")
    apis = {}
    for e in tr:
        apis.setdefault(e["api"], [0, set()])
        apis[e["api"]][0] += 1
        apis[e["api"]][1].add(e.get("status"))
    worst = sorted(((k, v) for k, v in apis.items() if "STUBBED" in v[1]),
                   key=lambda kv: -kv[1][0])[:8]
    for k, (c, sts) in worst:
        rec = g["apis"].get(k, {})
        print(f"  {k}: {c} live calls {sts} "
              f"(static sites: {rec.get('fanout', '?')})")

    section("LIKELY ROOT CAUSE")
    print("  evidence-ranked candidates from THIS run:")
    if stubs:
        top = _top_api(stubs)
        print(f"    A: stubbed dispatch family '{top}' pollutes downstream "
              f"state ({len(stubs)} calls) — pin upstream law, implement "
              f"generically, fixture first")
    if vt and count(vt.get('root', vt)) > 0 and frames and all(f['nonwhite'] == 0 for f in frames):
        print("    B: non-empty ViewTree + zero ink → renderer/geometry gap "
              "(visibility, bounds, alpha)")
    if frames and len(shas) == 1 and frames and frames[0]["nonwhite"] == 0:
        print("    C: composition never produced content — lifecycle/loop "
              "not reaching first draw")
    print("  (candidates are hypotheses with evidence, NOT verdicts — §0)")

    section("EVIDENCE")
    print(f"  {(appdir or '(no live dir resolved)')}/ (api_calls.json, "
          f"view_tree.json, frames)")
    print(f"  docs/foundation/live_runs.json")
    return 0


def _top_api(stubs):
    import collections
    c = collections.Counter(e["api"] for e in stubs)
    return ", ".join(f"{k}×{n}" for k, n in c.most_common(3))


def main():
    g = load(GRAPH)
    if not g:
        print("run graph_build.py first")
        return 2
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    if args[0] == "--live":
        return diagnose_live(g, args[1], args[2] if len(args) > 2 else None)
    return diagnose_failure(g, args[0])


if __name__ == "__main__":
    raise SystemExit(main())
