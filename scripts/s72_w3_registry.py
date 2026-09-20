#!/usr/bin/env python3
"""S72-W3 registry update: F-141 ROOT-CAUSED-FIXED (6 sub-law fixes, real-app
proof); register F-146/F-147 (new first divergences surfaced by the law)."""
import json

REG = "/home/z/my-project/root_registry.json"
r = json.load(open(REG))
items = r if isinstance(r, list) else r.get("roots", r.get("failures", []))

def find(fid):
    for f in items:
        if f.get("id") == fid:
            return f
    return None

f141 = find("F-141")
f141["status"] = "ROOT-CAUSED-FIXED"
f141["priority"] = "P0"
f141["upstream_law"] = ("AOSP ART interpreter DoInvoke: instance invoke with "
                        "null receiver throws NullPointerException at the "
                        "call site BEFORE any callee body executes; OpenJDK "
                        "Runtime/Long/Integer/Boolean + AOSP "
                        "Activity/FragmentManager/View/Theme laws for the "
                        "null producers surfaced by the law")
f141["fix"] = [
    "F-141a: ART null-receiver NPE law — throw_deferred NPE at the invoke "
    "site in ALL five instance-invoke paths (35c virtual/super/direct/"
    "interface + 3rc range), replacing the log-only silent dispatch "
    "(dalvik_engine.cpp; f141_is_null_receiver helper, dalvik_engine.h)",
    "F-141b: Runtime.getRuntime()/availableProcessors() — OpenJDK Runtime.java "
    "singleton law (RuntimeShadow, framework/android_shadows.cpp); dooz "
    "xr1.<clinit> Dispatchers.Default init",
    "F-141c: Long.getLong/Integer.getInteger/Boolean.getBoolean boxed-reader "
    "family over the F-080 platform property table (never null with primitive "
    "default; decode law) — dooz xu.<clinit> DefaultExecutor.keepAlive",
    "F-141d: Activity.getFragmentManager() non-null + FragmentManager/"
    "FragmentTransaction minimal subset (FragmentManagerShadow) — androidx "
    "LifecycleDispatcher report-fragment install path (im.onCreate→mc1.b)",
    "F-141e: View.getResources() → Resources singleton (P0.2 View receivers) "
    "— Compose init lambda we.run class-identity idiom",
    "F-141f: Context.getTheme() non-null + Theme.resolveAttribute law "
    "(theme chain authority = F-093 ResourceRuntime; TypedValue type/data/"
    "resourceId/string fill) — unote NoteMain.onCreate pc=43",
    "F-088 ext: Object.getClass on STRING_REF receivers answers String.class "
    "(never null) — dooz g8.a DataStore path",
]
f141["evidence"] = (
    "dooz: W2 silent dispatch produced this=NULL trie corruption "
    "(PersistentHashMapBuilder.putAll entry #49); with the law: 5 successive "
    "first-divergence sites each root-caused and law-fixed; dooz frame_008 "
    "nonwhite 197→23472 (splash surface now real content), determinism x3 "
    "BYTE-IDENTICAL (sha eb16ab5c68fa...); unote regression caused by the law "
    "(resolveAttribute null-theme) FIXED by F-141f: 23472→231120 px "
    "recovered; corpus regression: 4 SAME / 5 UP / 0 unexpected DOWN; "
    "fixtures 25/25 pixel-SAME, zero f141 breaks; gmdice x3 BYTE-IDENTICAL")
f141["fanout"] = ("Law-level: every instance-invoke in every APK now carries "
                  "ART NPE semantics; 6 null-producer APIs/classes closed "
                  "(Runtime, boxed-readers, FragmentManager family, "
                  "View.getResources, getTheme/resolveAttribute, string "
                  "getClass); affected real apps this wave: dooz, unote, "
                  "gmdice, microtimer, fishrings, tripeaks")

for new in [
    {
        "id": "F-146",
        "title": "dooz: ur.e(J) invoked on null receiver at g8.a pc=569 "
                 "(coroutine state machine; null producer upstream of the "
                 "call)",
        "status": "OPEN",
        "priority": "P1",
        "evidence": "S72-W3: f141 law surfaced the site (recv_type=8 NULL_REF, "
                    "F141-DIAG v4:t8/o0); escapes MainActivity.onCreate at "
                    "0xc1; next: trace the producer of the null ur receiver "
                    "in the compose/coroutine path",
        "next_action": "trace v4's def chain in g8.a (engine-pc domain), "
                       "identify the null producer API, law-fix per upstream",
        "session": "S72",
    },
    {
        "id": "F-147",
        "title": "dooz: ViewGroup.getChildAt(I) on null receiver at "
                 "MainActivity.onCreate pc=228 (v10 null — likely a "
                 "findViewById/content-view resolution gap)",
        "status": "OPEN",
        "priority": "P1",
        "evidence": "S72-W3: f141 law surfaced the site (recv NULL_REF; "
                    "method_idx 1592 = android.view.ViewGroup.getChildAt); "
                    "second boundary escape at 0xb4",
        "next_action": "trace v10's producer (findViewById/content lookup) "
                       "in onCreate's pc domain; classify findViewById "
                       "resolution law",
        "session": "S72",
    },
]:
    if not find(new["id"]):
        items.append(new)

json.dump(r, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry updated: F-141 ROOT-CAUSED-FIXED; F-146/F-147 registered")
print("total entries:", len(items))
