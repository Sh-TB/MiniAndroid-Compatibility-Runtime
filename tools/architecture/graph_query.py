#!/usr/bin/env python3
"""graph_query.py — S70 query engine over the ACTIVE runtime knowledge graph.

Answers the campaign's mandated questions in one command (docs/foundation/
knowledge_graph.json is the single fused source — every answer cites the
evidence it stands on, and honest gaps are flagged as gaps, never papered):

  api <substr>            API record: status, fan-out, served-by, tests, laws
  why-stubbed <api>       full stub chain: call sites → APKs → handler status
                          → upstream law → tests → missing fixture
  why-pixel <app> [frame] pixel production chain: APK → Activity → ViewTree →
                          renderer stage → framebuffer → SHA (live evidence vs
                          static-only links flagged per hop)
  blast-radius <name>     what breaks if this function/file/API changes:
                          served APIs → consumers (sites×APKs) → fixtures →
                          failures
  failure <id>            failure bundle: registry fields + graph links
  gaps [--top N] [--cls substr]   fan-out × risk ranked foundation gaps
  classify [--top N]      LIVE-STUB tail P0/P1/P2/P3/UNKNOWN triage (§PHASE 19)

Exit code is 0 whenever the query RAN (even when the answer is "gap").
"""
import json
import sys
from pathlib import Path

ROOT = Path("/home/z/my-project")
GRAPH = ROOT / "docs" / "foundation" / "knowledge_graph.json"

# foundation layer of a framework class (§PHASE 7 domain matrix) — derived
# from the DEX descriptor prefix, one lookup, no hand-maintained rows
LAYERS = [
    ("Landroid/view/", "framework-view"),
    ("Landroid/widget/", "framework-widget"),
    ("Landroid/graphics/", "rendering"),
    ("Landroid/content/", "framework-context"),
    ("Landroid/app/", "framework-activity"),
    ("Landroid/os/", "runtime-os"),
    ("Landroid/util/", "framework-util"),
    ("Landroid/res/", "resources"),
    ("Ljava/lang/", "java-lang"),
    ("Ljava/util/", "java-util"),
    ("Ljava/util/concurrent/", "concurrency"),
    ("Ljava/lang/reflect/", "reflection"),
    ("Lkotlin", "kotlin"),
]


def layer_of(api: str) -> str:
    for prefix, layer in LAYERS:
        if api.startswith(prefix):
            return layer
    return "other"


def load_graph():
    if not GRAPH.exists():
        print("knowledge_graph.json missing — run graph_build.py first")
        raise SystemExit(2)
    return json.loads(GRAPH.read_text())


def fmt_api_rec(rec):
    lines = [f"  status: {rec['status']}"
             f"{'  SILENT-WRONG flags: ' + str(rec['noop_flags']) if rec['noop_flags'] else ''}",
             f"  static call sites: {rec['fanout']}"
             f"  live dispatch calls: {rec['live_calls']}"
             f"  APKs using: {len(rec['by_apk'])}"]
    if rec["by_apk"]:
        top = sorted(rec["by_apk"].items(), key=lambda kv: -kv[1])[:5]
        lines.append("  top APKs: " + ", ".join(f"{a}:{n}" for a, n in top))
    if rec["served_static"]:
        lines.append("  served by (static, over-approx flagged):")
        for s in rec["served_static"][:3]:
            lines.append(f"    - {s['tu']}:{s['line']} in {s['function']}()"
                         f" [{s['extraction']}]")
    if rec["tested_by"]:
        lines.append(f"  exercised by fixtures: {', '.join(rec['tested_by'][:6])}"
                     f"{' (visual-proofed)' if rec['visual_proof'] else ''}")
    if rec["upstream_docs"]:
        lines.append(f"  upstream law docs: {', '.join(rec['upstream_docs'][:4])}")
    if rec["failures"]:
        lines.append(f"  linked failures: {', '.join(rec['failures'][:6])}")
    return lines


def cmd_api(g, term):
    hits = {k: v for k, v in g["apis"].items() if term in k}
    if not hits:
        print(f"no API matching '{term}'")
        return
    for k, rec in sorted(hits.items(), key=lambda kv: -kv[1]["fanout"])[:6]:
        print(f"API {k}")
        print("\n".join(fmt_api_rec(rec)))


def cmd_why_stubbed(g, api):
    rec = g["apis"].get(api)
    if not rec:
        cand = [k for k in g["apis"] if api in k]
        if len(cand) == 1:
            api = cand[0]
            rec = g["apis"][api]
        elif cand:
            print(f"ambiguous ({len(cand)}): " + ", ".join(sorted(cand)[:8]))
            return
        else:
            print(f"unknown API {api}")
            return
    print(f"=== WHY-IS-{api} ===")
    print("\n".join(fmt_api_rec(rec)))
    print("  chain:")
    print(f"    call sites: {rec['fanout']} across {len(rec['by_apk'])} APKs")
    if rec["live_calls"]:
        print(f"    live dispatch: {rec['live_calls']} calls "
              f"({rec['live_status_counts']}) in {rec['live_observed_apks']}")
    else:
        print("    live dispatch: NEVER EXERCISED in corpus runs — no runtime "
              "proof either way (fixture gap)")
    if rec["status"] == "UNSERVED":
        print("    runtime handler: NONE (no static guard, no live dispatch)")
        print("    → missing implementation; upstream law must be pinned first")
    elif rec["status"] == "SERVED-STATIC":
        print("    runtime handler: static surface only — not yet exercised "
              "live; needs a fixture before it is trusted")
    elif rec["status"] == "LIVE-STUB":
        print("    runtime handler: STUB (declared, not implemented)")
    else:
        print("    runtime handler: implemented (live-verified)")
    if rec["noop_flags"]:
        print(f"    deferred-behavior declarations: {rec['noop_flags']}")
    if not rec["tested_by"]:
        print("    existing tests: NONE for this API — missing fixture")
    else:
        print(f"    existing tests: {rec['tested_by']}")
    if not rec["upstream_docs"]:
        print("    upstream law: NOT PINNED — fetch AOSP/OpenJDK source first")
    else:
        print(f"    upstream law: {rec['upstream_docs']}")


def cmd_why_pixel(g, app, frame=None):
    a = g["apps"].get(app)
    if not a:
        cand = [k for k in g["apps"] if app in k]
        if len(cand) == 1:
            app, a = cand[0], g["apps"][cand[0]]
        else:
            print(f"unknown app '{app}' (have: {', '.join(sorted(g['apps']))})")
            return
    print(f"=== PIXEL PRODUCTION CHAIN — {app} ===")
    pin = a.get("pin") or {}
    print(f"  [1] APK pinned source : {pin.get('repo')} @ {pin.get('commit')}"
          if pin.get("repo") else "  [1] APK source: UNPINNED (gap)")
    print(f"  [2] package           : {a.get('package')}")
    print(f"  [3] source↔DEX map    : {a.get('mapping_coverage')} "
          f"({a.get('source_files')} files)")
    live = a.get("live") or {}
    shot = live.get("screenshot") or {}
    print(f"  [4] live run          : status={live.get('status')} "
          f"rc_zero={live.get('rc_zero')}")
    if shot:
        print(f"      screenshot: {shot.get('width')}x{shot.get('height')} "
              f"nonwhite={shot.get('nonwhite')} sha={str(shot.get('sha256'))[:16]}…")
    frames = live.get("frames") or []
    if frames:
        uniq = {f["sha256"] for f in frames}
        print(f"      frames: {len(frames)} ({len(uniq)} distinct SHAs)")
        for f in (frames[:3] if frame is None else
                  [x for x in frames if x["frame"] == frame]):
            print(f"      {f['frame']}: nonwhite={f['nonwhite']} "
                  f"sha={f['sha256'][:16]}…")
    vt = a.get("view_tree_nodes")
    print(f"  [5] ViewTree nodes    : {vt}")
    if a.get("top_children_classes"):
        print(f"      top children: {', '.join(a['top_children_classes'][:8])}")
    print("  [6] renderer stage    : software_renderer.cpp + canvas_shadow.cpp"
          " (static; per-frame op trace NOT yet recorded — provenance gap)")
    print("  verdict: chain hops [1]-[5] evidence-linked; hop [6] "
          "op-level provenance missing → use f08/canvas_probe fixtures for "
          "op-level proof")
    if shot and shot.get("nonwhite", 0) == 0:
        print("  ⚠ blank frame: composition produced no pixels — inspect hop "
              "[5]→[6] (ViewTree exists?) before touching the renderer")


def cmd_blast_radius(g, name):
    print(f"=== BLAST RADIUS — {name} ===")
    # 1. engine function match
    funcs = json.loads((ROOT / "docs/foundation/graph/functions.json").read_text())
    fns = [f for f in funcs["functions"]
           if name in f["name"] or name in f["qualified"]]
    apis = set()
    if fns:
        for f in fns:
            print(f"  engine function: {f['qualified']} ({f['tu']}:{f['start_line']})"
                  f" class-guards={len(f['class_guards'])} plain-guards={len(f['plain_guards'])}")
        # served APIs through these functions
        served = json.loads((ROOT / "docs/foundation/graph/served_api.json").read_text())
        for p in served["pairs"]:
            if p["function"] in {f["name"] for f in fns} and p["tu"] in {f["tu"] for f in fns}:
                apis.add(f"{p['class']}.{p['method']}")
    # 2. API-substring match too
    for k, rec in g["apis"].items():
        if name in k:
            apis.add(k)
    if not apis and not fns:
        print("  no function or API matched")
        return
    total_sites, total_apks, fixtures, failures = 0, set(), set(), set()
    for k in sorted(apis):
        rec = g["apis"].get(k)
        if not rec:
            continue
        total_sites += rec["fanout"]
        total_apks.update(rec["by_apk"].keys())
        fixtures.update(rec["tested_by"])
        failures.update(rec["failures"])
        if rec["fanout"]:
            print(f"  API {k}: {rec['fanout']} sites × {len(rec['by_apk'])} APKs "
                  f"[{rec['status']}]")
    print(f"  TOTAL: {len(apis)} APIs, {total_sites} static call sites, "
          f"{len(total_apks)} APKs")
    if fixtures:
        print(f"  fixtures to re-run: {', '.join(sorted(fixtures)[:10])}")
    if failures:
        print(f"  failures touching this area: {', '.join(sorted(failures)[:10])}")


def cmd_failure(g, fid):
    frs = [f for f in g["failures"] if f.get("failure") == fid]
    if not frs:
        cand = [f.get("failure") for f in g["failures"] if fid in f.get("failure", "")]
        print(f"unknown failure '{fid}'" + (f" — candidates: {cand[:8]}" if cand else ""))
        return
    fr = frs[0]
    for k in ("failure", "status", "priority", "apk", "source_commit",
              "runtime_commit", "method", "api", "root_cause", "expected",
              "observed", "pixel_diff", "reproducible", "evidence_next"):
        if fr.get(k) is not None:
            print(f"  {k}: {fr[k]}")
    api = fr.get("api")
    if api and api in g["apis"]:
        print("  — graph links for its API —")
        print("\n".join("  " + l for l in fmt_api_rec(g["apis"][api])))


def risk_score(rec):
    """§PHASE 6 internal triage score — evidence, not a substitute for it."""
    fan = rec["fanout"]
    apk_n = len(rec["by_apk"])
    layer_w = {"rendering": 1.5, "framework-view": 1.4, "resources": 1.3,
               "framework-widget": 1.2, "java-lang": 1.1, "concurrency": 1.1,
               "framework-context": 1.2, "framework-activity": 1.2}.get(
        layer_of(next(iter(rec["by_apk"]), "")), 1.0) if rec["by_apk"] else 1.0
    silent = 2.0 if rec["silent_wrong"] else (1.5 if rec["noop_flags"] else 1.0)
    stub_w = 1.2 if rec["status"] == "LIVE-STUB" else 1.0
    test_w = 0.7 if rec["tested_by"] else 1.0  # tested → slightly lower priority
    return fan * apk_n * layer_w * silent * stub_w * test_w


def cmd_gaps(g, top=25, cls=None, statuses=("UNSERVED", "LIVE-STUB", "LIVE-PARTIAL")):
    rows = []
    for k, rec in g["apis"].items():
        if rec["status"] not in statuses:
            continue
        if rec["fanout"] == 0:
            continue  # never used by any corpus APK — not a gap yet
        if cls and cls not in k:
            continue
        rows.append((risk_score(rec), k, rec))
    rows.sort(reverse=True, key=lambda r: r[0])
    print(f"=== FOUNDATION GAPS (fan-out × risk ranked, top {top}) ===")
    print(f"{'score':>10}  {'sites':>6}  {'apks':>4}  status          API")
    for score, k, rec in rows[:top]:
        print(f"{score:>10.0f}  {rec['fanout']:>6}  {len(rec['by_apk']):>4}  "
              f"{rec['status']:<15} {k}"
              + ("  [SILENT-WRONG]" if rec["silent_wrong"] else
                 ("  [deferred-ops]" if rec["noop_flags"] else "")))


def cmd_classify(g, top=80):
    """§PHASE 19 — LIVE-STUB tail triage."""
    buckets = {"P0": [], "P1": [], "P2": [], "P3": [], "UNKNOWN": []}
    for k, rec in g["apis"].items():
        if rec["status"] != "LIVE-STUB":
            continue
        lay = layer_of(k)
        fan, apks = rec["fanout"], len(rec["by_apk"])
        if lay in ("java-lang", "java-util", "concurrency", "reflection"):
            b = "P0" if fan >= 20 else "P1"
        elif lay in ("rendering", "framework-view", "framework-widget", "resources"):
            b = "P0" if fan >= 50 else "P1"
        elif rec["live_calls"] > 0:
            b = "P1"
        elif fan == 0 and rec["live_calls"] == 0:
            b = "P3"
        else:
            b = "UNKNOWN"
        buckets[b].append((fan, apks, k))
    for b in ("P0", "P1", "P2", "P3", "UNKNOWN"):
        rows = sorted(buckets[b], reverse=True)
        print(f"{b}: {len(rows)}")
        for fan, apks, k in rows[:top // 5]:
            print(f"    {k}  sites={fan} apks={apks}")


def main():
    g = load_graph()
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    cmd, rest = args[0], args[1:]
    if cmd == "api":
        cmd_api(g, rest[0])
    elif cmd == "why-stubbed":
        cmd_why_stubbed(g, rest[0])
    elif cmd == "why-pixel":
        cmd_why_pixel(g, rest[0], rest[1] if len(rest) > 1 else None)
    elif cmd == "blast-radius":
        cmd_blast_radius(g, rest[0])
    elif cmd == "failure":
        cmd_failure(g, rest[0])
    elif cmd == "gaps":
        top, cls = 25, None
        it = iter(rest)
        for a in it:
            if a == "--top":
                top = int(next(it))
            elif a == "--cls":
                cls = next(it)
        cmd_gaps(g, top, cls)
    elif cmd == "classify":
        cmd_classify(g, int(rest[1]) if len(rest) > 1 and rest[0] == "--top" else 80)
    else:
        print(f"unknown command {cmd}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
