#!/usr/bin/env python3
"""cont5_registry_update.py — register the F-NEW-243 org.json law +
close the F-NEW-235 residual face (Lr5;.g pc=150) with the full
classification chain. Syncs summary counts."""
import json

P = "/home/z/my-project/root_registry.json"
r = json.load(open(P))
roots = {x["id"]: x for x in r["roots"]}

f243 = {
    "id": "F-NEW-243",
    "title": "org.json real laws — JSONObject/JSONArray had NO implementation "
             "(universal stub): toString() answered null for fully "
             "serializable content; put/opt/get family absent",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "layer": "framework/org-json",
    "root_cause":
        "No org.json implementation existed in the engine — every "
        "JSONObject/JSONArray method fell to the generic stub "
        "(toString → null). AOSP org.json.JSONObject.toString() returns "
        "the serialized string for serializable content and answers null "
        "ONLY for unserializable members (JSONException caught inside). "
        "The game's settings object is fully serializable (version int, "
        "layout String, positions [[int,int,int]...], faces [int...], "
        "picks [], haptics bool, orientation String, difficulty String — "
        "[F243-DIAG] content dump) so the stub null was a pure divergence; "
        "R8's discard-result getClass null-check (Lr5;.g pc=0x96=150) "
        "fired a deferred NPE caught by the app's own save-path handler "
        "(Ly1;.a handler=0x4a). GENERIC LAW LANDED: JSONObject()/"
        "(String) parse (malformed → JSONException), put(String,X) "
        "stores-and-returns-this (null value removes; NaN/Inf → "
        "JSONException checkDouble; non-JSON objects stored → fail at "
        "serialize per JSONStringer), typed get*/opt* coercion laws "
        "(string-numbers, AOSP typeMismatch shapes), remove→previous, "
        "has, length; JSONArray()/(Collection) via the F-NEW-238 "
        "element-source cascade, put appends (null→JSON null), length, "
        "get(i) OOB → JSONException, typed getters; boxed Integer/Long/"
        "Short/Byte/Float/Double/Boolean/Character heap boxes unwrap to "
        "scalars ('value' field); ordered_json preserves AOSP "
        "LinkedHashMap insertion order. No app/package keying anywhere.",
    "evidence":
        "PHASE-1 chain: DEX disasm tmp/cont5_fairy/lr5_g.dis (pc=0x92 "
        "toString → 0x96 getClass) → runtime [SYNTH-EXC] f141-null-recv "
        "Lr5;.g pc=150 caught Ly1;.a handler=0x4a ×pre-fix → [F243-DIAG] "
        "content dump (all members serializable; boxed Integers) → "
        "post-fix run/cont5/fairy/det1-3: exit=0 Status:SUCCESS ×3 "
        "byte-identical screenshot 76e097244767d6c3 (== CONT-4 recorded "
        "sha; zero visual drift), Lr5;.g NPE rows 0/3. Stub census "
        "STUBBED 6376→6238 (138 calls → IMPLEMENTED). Regression at the "
        "same binary: f235_set_probe 15/15 ea31dc0dc539df73; anchors "
        "5/5×3 byte-identical.",
}

f235 = roots.get("F-NEW-235")
if f235:
    f235["progress_note"] = (
        f235.get("progress_note", "") +
        " CONT-5: the CONT-4 residual Lr5;.g pc=150 getClass-on-null NPE "
        "is CLASSIFIED as category D (missing generic framework contract) "
        "and CLOSED by F-NEW-243 (org.json real laws). Proof chain: the "
        "settings object's members are all JSON-serializable ([F243-DIAG] "
        "dump), so AOSP toString() cannot return null there; the stub "
        "null was a runtime divergence, not an app bug and not a "
        "legitimate app error path. Post-fix: SUCCESS x3 byte-identical "
        "(76e097244767d6c3), zero NPE rows, zero visual drift vs the "
        "recorded CONT-4 sha. F-NEW-235 is now FULLY CLOSED: every named "
        "face (F-NEW-236a-d, F-NEW-237/237b, F-NEW-238/238b, F-NEW-239, "
        "F-NEW-240, F-NEW-241, F-NEW-242, F-NEW-243) is a registered "
        "generic law with runtime evidence.")
    f235["status"] = "ROOT-CAUSED-CLOSED"

if "F-NEW-243" not in roots:
    r["roots"].append(f243)
else:
    r["roots"][r["roots"].index(roots["F-NEW-243"])] = f243

n = len(r["roots"])
r["total"] = n
r["count"] = n
r["total_roots"] = n
if "F-NEW-235" in r["summary"].get("open_frontiers", []):
    r["summary"]["open_frontiers"].remove("F-NEW-235")
r["summary"]["last_updated"] = (
    "CONT-5 (2026-10-05): F-NEW-243 org.json real laws registered "
    "(ROOT-CAUSED-FIXED); F-NEW-235 residual Lr5;.g pc=150 classified "
    "category-D runtime-root and closed via F-NEW-243 — F-NEW-235 "
    "ROOT-CAUSED-CLOSED (all faces now registered generic laws)")
json.dump(r, open(P, "w"), indent=1, ensure_ascii=False)
print("registry: %d roots; F-NEW-243 ROOT-CAUSED-FIXED; F-NEW-235 "
      "ROOT-CAUSED-CLOSED" % n)
