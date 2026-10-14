#!/usr/bin/env python3
"""cont12_registry.py — CONT-12: append F-NEW-266 + F-NEW-266a to the
root registry and update count/summary fields honestly."""
import json

p = "/home/z/my-project/root_registry.json"
r = json.load(open(p))
roots = r["roots"]

have = {x.get("id") for x in roots}
assert "F-NEW-266" not in have and "F-NEW-266a" not in have

roots.append({
    "id": "F-NEW-266",
    "status": "ROOT-CAUSED-FIXED",
    "title": "INVOKE-VIRTUAL TRANSITIVE INTERFACE-DEFAULT DISPATCH LAW "
             "(ART/JVMS 5.4.5 virtual resolution): when the receiver's class "
             "chain declares no implementation, virtual resolution must "
             "continue into the receiver's TRANSITIVELY IMPLEMENTED "
             "INTERFACES and execute the first code-bearing (default) method "
             "with the exact descriptor. The invoke-interface path already "
             "implemented this (F-023); invoke-virtual (35c AND 3rc) fell to "
             "the API bridge whose stub silently returned null, and the null "
             "fed the next instruction. ORACLE FACE (external un-renamed "
             "Compose 1.11.4, no R8, exact Maven artifacts): "
             "AndroidComposeView$root$1$1.then(other) -> interface "
             "Modifier.then default body -> null receiver -> chained "
             "invoke-interface NPE x172 -> AbstractComposeView.setContent "
             "dead -> composition never created. dooz never hits it because "
             "R8 inline/bridges the default bodies away — found only through "
             "the un-renamed oracle; fan-out = every non-R8-shrunk APK "
             "(debug builds, D8-only builds, CI harnesses).",
    "priority": "P0",
    "layer": "dex/invocation",
    "evidence": "evidence/cont12/CONT12_EXTERNAL_COMPOSE_ORACLE.md",
    "probe": "fixtures/f266_probe (real aapt2/ECJ/D8, apk bd79275a2e18c289): "
             "A direct-default PASS 42; B most-derived-override PASS 51; "
             "C transitive-2-hop PASS 42; D null-receiver NPE FAIL (new "
             "finding F-NEW-266a); E receiver-identity PASS 101; F value "
             "fidelity PASS 21 -> 5/6 PASS + 1 honest FAIL registered",
    "verified_current": "anchors 5/5 x3 byte-identical at binary "
                        "0ee46f5a719d2a8c (dooz d602648e8e401895 unchanged; "
                        "opencalc a976d2f9 / chess b5a7a35d / microtimer "
                        "da73010a / unote 4f1a9e4e all unchanged); "
                        "negatives 19/19; skill 13/13; f259 7/7; f259g "
                        "11/13 (2 registered honest FAILs unchanged); "
                        "gate A 3/3 available families PASS (2 corpus APKs "
                        "absent since container reset, recorded)",
    "fanout": "every invoke-virtual/range that legally resolves to a "
              "superinterface default method — the Modifier.then family "
              "(millions of sites in any Compose app), coroutine "
              "AbstractCoroutine family, Kotlin Function defaults; zero "
              "native-drift on the recorded anchor set",
    "date": "2026-10-07",
})

roots.append({
    "id": "F-NEW-266a",
    "status": "CLASSIFIED",
    "title": "NULL-RECEIVER LAW GAP on invoke-interface default-method fast "
             "path: a typed-null receiver invoke-interface of a DEX default "
             "method DISPATCHED the default body instead of throwing "
             "NullPointerException at the call site (ART law: NPE before any "
             "callee body runs). Probe face: fixtures/f266_probe row D — "
             "OtherDefI typed-null other() returned a stub value with no "
             "exception (r4=0). NEXT ARM: apply the F-141 null-receiver gate "
             "to the interface-default dispatch path inside "
             "try_recursive_invoke (the 35c invoke-interface generic path "
             "already gates BEFORE dispatch; the default-method route "
             "bypassed it).",
    "priority": "P1",
    "layer": "dex/exceptions+invocation",
    "evidence": "evidence/cont12/CONT12_EXTERNAL_COMPOSE_ORACLE.md",
    "probe": "fixtures/f266_probe row D (honest FAIL, registered, not "
             "patched this wave)",
    "verified_current": "no regression: all anchors byte-identical at "
                        "0ee46f5a719d2a8c",
    "fanout": "any interface-typed call on a null receiver where the target "
              "is a DEX-defined default method",
    "date": "2026-10-07",
})

r["total"] = len(roots)
r["count"] = len(roots)
json.dump(r, open(p, "w"), indent=1, ensure_ascii=False)
print("registry:", len(roots), "roots; added F-NEW-266, F-NEW-266a")
