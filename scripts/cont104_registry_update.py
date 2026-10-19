#!/usr/bin/env python3
"""cont104_registry_update.py — append CONT-104 roots (F-NEW-442..442e) to the
root registry and mirror to canonical/, enforcing id uniqueness."""
import json
import sys

ROOTS = [
    {
        "id": "F-NEW-442",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "View.getRootWindowInsets() answered null on ATTACHED views — androidx ViewCompat.getRootWindowInsets consumers died in the R8-inlined requireNonNull of WindowInsetsCompat.toWindowInsetsCompat (issue #364 CONT-104 chess batch).",
        "layer": "framework (android_shadows ViewShadow getRootWindowInsets law)",
        "root_cause": "AOSP View.java: an ATTACHED view (mAttachInfo != null) answers NON-NULL root insets from its ViewRootImpl; the engine had no law at all, the API bridge fell through to a silent stub null, and androidx (chess_jwtc_298: RecyclerView.onAttachedToWindow -> ViewCompat.getRootWindowInsets -> Ln0/k1;.c) hit the R8-inlined Objects.requireNonNull (getClass()) -> NPE x8 -> start.onCreate APP-BOUNDARY unwind -> white frame.",
        "fix": "ViewShadow dispatch law: attached node -> allocate a REAL Landroid/view/WindowInsets; object marked __root_insets__=1 (the SAME model F-NEW-384 frame-boundary dispatch materializes — one model, two delivery laws: pull at attach-time consumers, push at frame boundary); unattached -> lawful null (AOSP no-AttachInfo face). Probes: fixtures/cont104_insets_probe rows PREATTACH null=true / ATTACHED nonnull=true / CLS identity.",
        "evidence": "run/cont104/chess_pre (PRE NPE x8), run/cont104/p104i_pre|post (probe 4/4), chess_post5 f141=0",
    },
    {
        "id": "F-NEW-442b",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "View.computeSystemWindowInsets(WindowInsets, Rect) answered null — androidx Api23Impl.computeSystemWindowInsets (Ln0/f0;.b) fed the null straight into WindowInsetsCompat.toWindowInsetsCompat (issue #364 CONT-104 chess batch).",
        "layer": "framework (android_shadows ViewShadow computeSystemWindowInsets law)",
        "root_cause": "AOSP View.computeSystemWindowInsets NEVER returns null for a non-null insets input (attached path returns the consumed variant after ViewRootImpl dispatch; no-AttachInfo fast path = outLocalInsets.setEmpty() + the SAME insets). The engine bridge was a silent stub returning null; chess androidx ActionBarOverlayLayout.onApplyWindowInsets -> f0.b (k1.b() platform non-null -> view.computeSystemWindowInsets -> k1.c(result, view) with R8-inlined requireNonNull) -> NPE (the SECOND k1.c null source).",
        "fix": "ViewShadow law: out rect setEmpty() + return the INPUT insets object (the runtime's F-NEW-384 zero-inset window satisfies consumed-of-zero == input, matching BOTH AOSP paths' observable behavior). Probe row C104-CSWI same=true emptyLocal=true.",
        "evidence": "run/cont104/chess_ct CL-TRACE d=3, p104i_pre2 same=false emptyLocal=false -> post same=true emptyLocal=true",
    },
    {
        "id": "F-NEW-442c",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P2",
        "title": "Rect.isEmpty() had NO implementation — silent stub false for every consumer of computeSystemWindowInsets' out rect (issue #364 CONT-104 chess batch).",
        "layer": "framework (dalvik_engine Rect/RectF isEmpty law)",
        "root_cause": "AOSP Rect.java: public final boolean isEmpty() { return left >= right && top >= bottom; } — the engine implemented width/height (field-reading) but not isEmpty; every isEmpty answered a silent false (the honesty red line's silent-default class), corrupting insets emptiness checks in androidx insets math.",
        "fix": "Read the SAME plain int fields the Rect ctor bridge stores (left/top/right/bottom) and answer the AOSP conjunction law for Rect and RectF. Probe row C104-CSWI emptyLocal=true after the fix.",
        "evidence": "p104i_post2 emptyLocal=false (stub) -> p104i_post3 emptyLocal=true",
    },
    {
        "id": "F-NEW-442d",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "WindowInsets.inset(IIII) answered null — the R8-MOVED androidx delegate (androidx/lifecycle/c0;.j = pure insets.inset(l,t,r,b) delegation) fed the null into k1.c -> the THIRD requireNonNull NPE source (issue #364 CONT-104 chess batch).",
        "layer": "framework (dalvik_engine WindowInsets.inset law)",
        "root_cause": "AOSP WindowInsets.inset(IIII) returns a NEW clamped WindowInsets and NEVER null. The engine bridge had no law; the silent stub null propagated through chess androidx g1.l (WindowInsetsCompat impl replace-insets path) -> k1.c(result, view) -> R8-inlined requireNonNull -> NPE x8.",
        "fix": "Allocate a NEW real Landroid/view/WindowInsets; carrying the receiver's __root_insets__ marker and recording the applied deltas (__inset_l__/t/r/b) — the runtime's zero-inset window model keeps the numeric getters at their lawful 0 while the object identity law (non-null, fresh object) is exact.",
        "evidence": "run/cont104/chess_ct2 CL-TRACE d=3 (g1.l), tg-independent chess_post4 f141 count 8->7",
    },
    {
        "id": "F-NEW-442e",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "View.dispatchApplyWindowInsets(WindowInsets) answered null — androidx d0.a (R8-renamed dispatch wrapper) fed the null into k1.c -> the FOURTH requireNonNull NPE source (issue #364 CONT-104 chess batch).",
        "layer": "framework (android_shadows ViewShadow dispatchApplyWindowInsets law)",
        "root_cause": "AOSP View.dispatchApplyWindowInsets: the registered OnApplyWindowInsetsListener if present, else onApplyWindowInsets(insets); the platform DEFAULT answers the insets object — NEVER null for a non-null input. The engine's F-NEW-384 walk already dispatches into DEX-level overrides BEFORE this bridge, so the bridge face is the no-listener/no-override pass-through; the silent stub null instead reached chess ActionBarOverlayLayout.onMeasure -> k1.c(stripped, content) -> NPE.",
        "fix": "ViewShadow pass-through law: return the input insets object (null only for a null input). Chess f141 count after 442/442b/442c/442d/442e: 8 -> 0.",
        "evidence": "run/cont104/chess_ct3 CL-TRACE d=2 (onMeasure), chess_post5 f141=0",
    },
]


def main():
    paths = ["canonical/root_cause_registry.json", "root_cause_registry.json"]
    for p in paths:
        try:
            with open(p) as f:
                data = json.load(f)
        except FileNotFoundError:
            if p == paths[0]:
                raise
            continue
        roots = data if isinstance(data, list) else data["roots"]
        ids = {r.get("id") for r in roots}
        added = 0
        for r in ROOTS:
            if r["id"] not in ids:
                roots.append(r)
                added += 1
        with open(p, "w") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print(f"{p}: +{added} -> {len(roots)} roots")


if __name__ == "__main__":
    main()
