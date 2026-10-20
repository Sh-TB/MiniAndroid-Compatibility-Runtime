#!/usr/bin/env python3
"""cont123_registry_update.py — CONT-123 decode-wave registry landing."""
import json

DATE = "2026-10-20"
BIN = "04a89c528ba7cc59"

UPDATES = {
    "F-NEW-192": {
        "status": "ROOT-CAUSED-PARTIAL",
        "note": (
            "CONT-123: the elevation Z-STATE family landed + live-probed — "
            "setTranslationZ/getTranslationZ/getZ/setZ (AOSP View.java law: "
            "Z = elevation + translationZ; setZ keeps elevation and adjusts "
            "translationZ) on the ViewShadow node state. LIVE probe c123 "
            "(fixtures/cont123_zstate, binary " + BIN + "): 4/4 PASS — "
            "setElevation(4)→getZ=4; +translationZ(3)→getZ=7; setZ(10)→tZ=6 "
            "el=4; getElevation round-trip. Status REGISTERED → "
            "ROOT-CAUSED-PARTIAL: the draw-walk half (RenderNode sibling "
            "Z-ordering + outline shadow rasterization) stays the named "
            "residual — the axis-aligned walk keeps declaration order; the "
            "21-P0-6 draw-order law itself was re-verified CONT-97 (12/12 "
            "anchors)."
        ),
    },
    "F-NEW-384": {
        "status": "VERIFIED-FIXED",
        "note": (
            "CONT-123 re-verification at HEAD (binary " + BIN + ", live run "
            "run/c123/chess_probe.log): the NAMED measure-path residual (k1.c "
            "NPE via cached-inset wrappers) shows ZERO occurrences; the inset "
            "chains are all served live — [ROOT-059] WindowInsets$Builder."
            "build ×2, [C013-HIER] setOnApplyWindowInsetsListener + "
            "getRootWindowInsets + computeSystemWindowInsets dispatched via "
            "the ActionBarOverlayLayout superclass chain, [F384-ROOTINSETS] "
            "dispatch live; chess anchor a0319686d56ff5c0 byte-identical. The "
            "second-generation null source the row named is closed by the "
            "post-CONT-82 window-insets law family (ROOT-059 builder + C013 "
            "hier-dispatch). Honest note: the k1/d1 wrapper decode (CONT-76 "
            "candidate family) is recorded in the chain evidence, not deleted."
        ),
    },
    "F-NEW-267": {
        "status": "ROOT-CAUSED-PARTIAL",
        "note": (
            "CONT-123 scripted-tap refresh at HEAD (binary " + BIN + ", live "
            "run run/c123/dooz_tap.log, --tap 820,1837): face d602648e8e401895 "
            "byte-identical to the anchor (tap consumed without visual change "
            "at frame 1); [F117-TAP] DOWN target=0 at frame 1 — the "
            "compose-internal hit-test frontier is UNCHANGED (the empty hit "
            "list inside AndroidComposeView.dispatchTouchEvent; diag line "
            "[UC009-ATTACH-DIAG] ComposeView NOT in class index is the "
            "recorded decode pointer). Row stays ROOT-CAUSED-PARTIAL; the "
            "synthetic-Compose-tree probe spec (this row's probe field) "
            "remains the landing lever."
        ),
    },
}

def main():
    for path in ("canonical/root_cause_registry.json", "root_registry.json"):
        reg = json.load(open(path))
        roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg
        by_id = {r["id"]: r for r in roots}
        for rid, upd in UPDATES.items():
            r = by_id.get(rid)
            if r is None:
                print("MISS", rid, path)
                continue
            r["status"] = upd["status"]
            old = r.get("evidence") or ""
            if isinstance(old, dict):
                old = json.dumps(old, ensure_ascii=False)
            elif isinstance(old, list):
                old = " ".join(str(x) for x in old)
            r["evidence"] = (old + "\n" if old else "") + upd["note"]
            r["verified_current"] = True
            r["date"] = DATE
        if isinstance(reg, dict):
            json.dump(reg, open(path, "w"), indent=1, ensure_ascii=False)
        else:
            json.dump(roots, open(path, "w"), indent=1, ensure_ascii=False)
        print(path, "updated", len(UPDATES))
    # sanity
    a = json.load(open("canonical/root_cause_registry.json"))
    b = json.load(open("root_registry.json"))
    ra = a["roots"] if isinstance(a, dict) and "roots" in a else a
    rb = b["roots"] if isinstance(b, dict) and "roots" in b else b
    ka = {r["id"]: (r["status"], r.get("date")) for r in ra}
    kb = {r["id"]: (r["status"], r.get("date")) for r in rb}
    print("row-equal:", ka == kb, "| roots:", len(ka), len(kb))

if __name__ == "__main__":
    main()
