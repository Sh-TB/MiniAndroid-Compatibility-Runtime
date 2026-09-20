#!/usr/bin/env python3
"""dex_census.py — §13 API COVERAGE MATRIX data source.

For every canonical corpus APK, walk the DEX with androguard and record:
  * every class/method DEFINED by the app
  * every invoke-* call SITE: target class, method, descriptor
  * aggregate fan-out: how many call sites consume each android.*/java.* API
    across the whole corpus (FAN-OUT FIRST — §14)

Output:
  docs/foundation/dex_census/<package>.json   per-APK census
  docs/foundation/dex_census/_aggregate.json  corpus-wide API fan-out
"""
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import logging
logging.getLogger().setLevel(logging.ERROR)
# androguard is chatty through loguru/std logging — silence both channels
for noisy in ("androguard", "loguru"):
    logging.getLogger(noisy).setLevel(logging.CRITICAL)

ROOT = Path("/home/z/my-project")
CORPUS = ROOT / "upload" / "canonical_apks"
OUT = ROOT / "docs" / "foundation" / "dex_census"

INVoke_OPS = {"invoke-virtual", "invoke-super", "invoke-direct",
              "invoke-static", "invoke-interface"}
# method ref inside invoke operand: Lcls;->name(desc) — desc has no spaces
INVOKE_REF_RE = re.compile(r"(L[^;\s]+;)->([^\s(]+)(\([^)]*\))")


def census(apk_path: Path) -> dict:
    from androguard.misc import AnalyzeAPK
    a, d_list, dx = AnalyzeAPK(str(apk_path))
    pkg = a.get_package()

    app_classes = set()
    for d in d_list:
        for c in d.get_classes():
            name = c.get_name()
            # descriptors: Lapp/varlorg/unote/NoteMain;
            cn = name[1:-1].replace("/", ".")
            if cn.startswith(pkg) or (cn and not cn.startswith(
                    ("android.", "androidx.", "java.", "javax.", "kotlin",
                     "kotlinx.", "com.google.", "org.apache.", "dalvik.",
                     "com.android.", "io.reactivex", "org.intellij",
                     "org.jetbrains", "bsh.", "the.bytecode.club",
                     "android.support", "org.slf4j", "org.json",
                     "org.xmlpull", "org.w3c", "org.xml"))):
                app_classes.add(name)

    # method-level API edges (for source_map) + API call-site fan-out
    method_apis = {}          # "Lcls;->meth(desc)" -> [api strings]
    api_sites = Counter()     # (target_class, method, desc) -> call sites
    api_per_class = Counter() # target_class -> call sites

    for m in dx.get_methods():
        try:
            if m.is_external():
                continue
            enc = m.get_method()
            cls = enc.get_class_name()
            if cls not in app_classes:
                continue
            key = f"{cls}-> {enc.get_name()}{enc.get_descriptor()}"
            edges = []
            for ins in (enc.get_instructions() or []):
                op = ins.get_name()
                if op not in INVoke_OPS:
                    continue
                try:
                    operand = ins.get_output()
                except Exception:
                    continue
                # output shape varies ("v0, Lcom/x;->foo(...)V" etc.) — extract
                # the method reference directly instead of positional splits
                mref = INVOKE_REF_RE.search(operand)
                if not mref:
                    continue
                tcls, tmethod, tdesc = mref.group(1), mref.group(2), mref.group(3)
                api = f"{tcls};.{tmethod}"
                edges.append(api)
                api_sites[(tcls, tmethod, tdesc)] += 1
                api_per_class[tcls] += 1
            if edges:
                method_apis[f"{cls}->{enc.get_name()}{enc.get_descriptor()}"] = edges
        except Exception:
            continue

    # counts of defined classes/methods
    n_methods = 0
    for d in d_list:
        for c in d.get_classes():
            if c.get_name() in app_classes:
                n_methods += len(c.get_methods())

    return {
        "apk": apk_path.name,
        "package": pkg,
        "versionCode": a.get_androidversion_code(),
        "app_classes": len(app_classes),
        "app_methods": n_methods,
        "api_call_sites": sum(api_sites.values()),
        "distinct_apis": len(api_sites),
        "top_target_classes": api_per_class.most_common(25),
        "api_sites": [{"target_class": t, "method": m, "descriptor": d,
                       "call_sites": n} for (t, m, d), n in
                      sorted(api_sites.items(), key=lambda kv: -kv[1])],
        "method_apis": method_apis,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    aggregate = Counter()
    agg_by_apk = defaultdict(dict)
    rows = []
    for apk in sorted(CORPUS.glob("*.apk")):
        t0 = time.time()
        try:
            c = census(apk)
        except Exception as e:
            print(f"[FAIL] {apk.name}: {e}", file=sys.stderr)
            continue
        slug = apk.stem.replace("/", "_")
        (OUT / f"{slug}.json").write_text(json.dumps(c, indent=1))
        # aggregate fan-out over android/java/kotlin framework targets
        for s in c["api_sites"]:
            tc = s["target_class"]
            if tc.startswith(("Landroid/", "Ljava/", "Ljavax/", "Lkotlin/",
                              "Lkotlinx/", "Lorg/json", "Lorg/xml")):
                key = f"{tc}.{s['method']}"
                aggregate[key] += s["call_sites"]
                agg_by_apk[key][apk.name] = s["call_sites"]
        rows.append({"apk": apk.name, "package": c["package"],
                     "app_classes": c["app_classes"],
                     "app_methods": c["app_methods"],
                     "api_call_sites": c["api_call_sites"],
                     "distinct_apis": c["distinct_apis"]})
        print(f"[{apk.name}] classes={c['app_classes']} methods={c['app_methods']} "
              f"sites={c['api_call_sites']} apis={c['distinct_apis']} "
              f"({time.time()-t0:.0f}s)")

    (OUT / "_aggregate.json").write_text(json.dumps({
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "per_apk": rows,
        "corpus_api_fanout": aggregate.most_common(),
        "corpus_api_fanout_by_apk": {k: v for k, v in agg_by_apk.items()},
    }, indent=1))
    print(f"\naggregate: {len(aggregate)} distinct framework APIs consumed corpus-wide")


if __name__ == "__main__":
    main()
