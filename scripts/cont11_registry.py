#!/usr/bin/env python3
"""cont11_registry.py — register F-NEW-509 (CONT-11 W7) in root_registry.json
with the batch-20 evidence chain. No inflation: one root, one entry."""
import json

RR = "/home/z/my-project/root_registry.json"
r = json.load(open(RR))
# registry shape may be dict-with-roots or bare list (post-rebase remote form)
roots = r["roots"] if isinstance(r, dict) and "roots" in r else r
entry = None
if isinstance(r, dict) and "roots" in r:
    hit = [x for x in roots if x.get("id") == "F-NEW-509"]
    if hit:
        print("F-NEW-509 already present — refreshing fields only")
        entry = hit[0]
    else:
        entry = {"id": "F-NEW-509"}
        roots.append(entry)
else:
    hit = [x for x in roots if isinstance(x, dict) and x.get("id") == "F-NEW-509"]
    entry = hit[0] if hit else {"id": "F-NEW-509"}
    if not hit:
        roots.append(entry)

entry.update({
    "id": "F-NEW-509",
    "status": "ROOT-CAUSED-FIXED",
    "title": (
        "bridge_to_api Context-family guards (P0.12 getSharedPreferences / "
        "getPreferences) matched the receiver by RUNTIME-CLASS NAME SUBSTRING "
        "(\"Context\"/\"Activity\" in the descriptor) — real APK hierarchies "
        "(R8-renamed support-v7/v4 activity chains like GameSelector, and "
        "plain app subclasses with neither substring) missed the guard, the "
        "call answered NULL, and the app's own bundled PreferenceManager / "
        "direct prefs reads then NPE'd on the null receiver. Fix: ancestry "
        "fallback — same bounded 16-hop DEX-chain walk as the F-NEW-259 slot "
        "resolution — accepting any receiver whose runtime chain reaches a "
        "Context-family shadow root (Activity/Application/Service/"
        "ContextWrapper/Context). Generic: no app-specific code, no R8-"
        "specific interception."
    ),
    "priority": "P0",
    "layer": "framework/context",
    "evidence": "evidence/cont11/batch20_ledger.json",
    "probe": "fixtures/fnew261_probe 5/5 PASS (F261-A..E: direct baseline / "
             "fix-face PrefsHost receiver / 2-hop Deep ancestry / cross-"
             "receiver per-name identity S99 / cross-file negative)",
    "verified_current": (
        "batch-20 A/B at binary 8f45e4eca7d142fa (fix) vs aed46450c103f2ea "
        "(pre-fix): uncaught exceptions 35->0 (solitaire_tb), 27->0 "
        "(andstatus2048), 23->0 (deskclock), 3->0 (bmi), 37->0 (etar), 5->0 "
        "(textpad), 4->0 (alexcalc), 5->0 (fossify_math), 9->0 (tictactoe_em), "
        "6->0 (stacktower), 12->0 (bouncy) — all ten crash-family APKs now "
        "run clean; secuso_memory flipped DEFAULT_BACKGROUND_ONLY -> "
        "REAL_APP_CONTENT (4e6e59ecfb910187). Regression at the fixed "
        "binary: anchors 5/5 x3 byte-identical (opencalc a976d2f9 / chess "
        "b5a7a35d / dooz d602648e / microtimer da73010a / unote 4f1a9e4e), "
        "F259 probe A..G all PASS, negatives 19/19, skill 13/13, gate A "
        "98/0/1."
    ),
})

if isinstance(r, dict):
    r["total_roots"] = len(roots)
    r["total"] = len(roots)
    import collections
    r["status_counts"] = dict(collections.Counter(x.get("status", "?") for x in roots))
json.dump(r, open(RR, "w"), indent=1)
print("registry roots:", len(roots), "| F-NEW-509 registered ROOT-CAUSED-FIXED")
