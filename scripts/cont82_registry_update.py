#!/usr/bin/env python3
"""cont82_registry_update.py — CONT-82 wave registry updates.

1. F-NEW-383 (NEW, ROOT-CAUSED-FIXED P1): the ColorStateList resource law
   family — TypedArray.getColorStateList / Resources.getColorStateList /
   ColorStateList.valueOf/getDefaultColor/getColorForState had NO law, so
   the androidx Material drawable chain (Lq/a.<init> → TypedArray.
   getColorStateList → Lq/b.<init> → getDefaultColor) received null and
   NPE'd (jwtc chess f141 family). ALSO: the obtainStyledAttributes
   producer gate extended to Context-family receivers (ContextThemeWrapper
   / Context / ContextWrapper — the androidx themed-obtain idiom
   `new ContextThemeWrapper(ctx, resid).obtainStyledAttributes(attrs)`
   answered null → TypedArray.getInt NPE at f2/p.a pc=22). Honest
   first-run catch recorded: the raw-word fallback initially wrapped an
   attr id (0x10104e2) as an ARGB color — gated to null with a bounded row.
2. F-NEW-384 (NEW, LAW-LANDED — PARTIAL, residual named): the root
   window-insets dispatch — ViewRootImpl.performTraversals dispatches the
   host window's root WindowInsets BEFORE measure; the engine never
   dispatched any insets pass, so androidx fields caching platform insets
   (ActionBarOverlayLayout.mLastInsets / the fragment dispatch wrappers'
   own caches) stayed null and WindowInsetsCompat.toWindowInsetsCompat(null)
   NPE'd at the first getClass (Ln0/k1.c pc=2, chess ×7-8; the same family
   AndStatus2048's Lt60;.getValue candidate belongs to). Landed: one
   materialized root WindowInsets dispatched per window root at the frame
   boundary BEFORE measure (the AOSP performTraversals order), through the
   app's REAL dispatchApplyWindowInsets/onApplyWindowInsets chain with the
   AOSP down-tree child walk (first consuming override wins; root
   authority = ActivityShadow content_view_id — the skeleton-tree and
   last-root mispicks were caught and fixed during the wave). Honest
   residual: chess's face stays byte-identical (b270ff040b3601dc, zero
   drift) — the measure-path cached-inset wrappers still read fields
   populated from PRE-dispatch passes; the second-generation null source
   is named (k1.b() platform-insets field chain + the d1.l(IIII) builder
   family), NOT closed.
3. F-NEW-385 (NEW, ROOT-CAUSED-FIXED P1): the array component-typing law
   family, caught by the CONT-82 Arrays.toString overload-matrix fixture
   (fixtures/cont82_arrays_fixture, com.probe.a2t, apk run/cont82/
   cont82_arrays_probe.apk): (a) new-array ZERO-INIT — fresh arrays left
   slots absent so unstored indices rendered null ([Z {true} →
   "[true, null]"; AOSP answers "[true, false]"); (b) aput component
   typing — the APUT opcode VARIANT is the component type (aput-boolean/
   char/byte/short stored raw INT32/NULL); (c) fill-array-data component
   typing for the width-2 branch ([C stored INT32 → "[120, 121]"), and
   filled-new-array component typing ([Z/[C/[B/[S register values typed
   per the array descriptor). Post-fix: the 8-row matrix is 8/8 PASS
   (INTS/BOOLS/CHARS/EMPTY/OBJS/NULL/NULLOBJ/LONGS) — closes the CONT-80
   Track-4 acceptance gate that had been BLOCKED_NEEDS_EVIDENCE.
4. CONT-81 DexSQL directive executed (the only fully-unexecuted #364
   instruction): controlled install (v0.1.0 linux-amd64, sha256 recorded,
   no upstream checksum file exists in the release — recorded honestly;
   license read: closed-source binary, use permitted), 12-query cookbook
   (scripts/cont82_dexsql_cookbook.py; categories 1+12 honestly
   UNSUPPORTED — DEX-only schema, baseline aapt2 covers them), paired A/B
   on the genuinely-open families (Q1 veldsoft deferred-launch, Q2 chess
   NPE). Decision: LIMITED ADOPT — caller-chain/decode queries answered in
   ~0.02-0.04s vs ~5-7 min hand-toolchain loops (measured), byte-precise
   descriptors, but manifest/resources (cat 1/12) remain aapt2 territory.
5. Corpus reclassification (3 rows, deferred-drain law): fishrings,
   tripeaks, klondike flipped DEFAULT_BACKGROUND_ONLY → REAL_APP_CONTENT
   at --frames 24 (virtual clock 7200ms > the 5000ms splash Timer; the
   CONT-81 5-frame budget was 1500ms < 5000ms — the harness budget was the
   divergence, the engine F-115 Timer law was CORRECT). Faces byte-stable
   ×3 runs each (a341e3ad9092f640 / e2a290ab98762eea / a77038da303ed1b4);
   real launches proven (startActivity → GameActivity/LobbyActivity/
   MenuActivity + real onCreate/setContentView + 105K/560K/502K
   non-dominant app pixels).
"""
import json

ROOT = "/home/z/my-project"
P1 = f"{ROOT}/root_registry.json"
P2 = f"{ROOT}/canonical/root_cause_registry.json"


def main():
    r = json.load(open(P1))
    roots = r["roots"] if isinstance(r, dict) and "roots" in r else r
    ids = [x.get("id") for x in roots]
    assert len(ids) == len(set(ids)), "duplicate root ids"
    by_id = {x["id"]: x for x in roots if "id" in x}

    new_roots = [
        {
            "id": "F-NEW-383",
            "status": "ROOT-CAUSED-FIXED",
            "priority": "P1",
            "title": "ColorStateList resource law family + Context-family "
                     "obtainStyledAttributes producer gate",
            "layer": "resources/framework",
            "root_cause":
                "TypedArray.getColorStateList / Resources.getColorStateList / "
                "ColorStateList.valueOf/getDefaultColor/getColorForState had "
                "no law; the androidx Material drawable chain "
                "(Lq/a.<init> → TypedArray.getColorStateList → Lq/b.<init> → "
                "getDefaultColor) received null and NPE'd (jwtc chess f141 "
                "family, APP_DRAW_OPS white). The Context-family "
                "obtainStyledAttributes receivers (ContextThemeWrapper from "
                "the androidx themed-obtain idiom, decoded live via DexSQL "
                "from Lf2/p;->a(Context,I,I,Lf2/a;)Lf2/o;) reached NO "
                "producer (the F-093/F-NEW-175 producer only dispatched for "
                "Activity-typed receivers) → TypedArray.getInt on null.",
            "evidence":
                "run/cont82/chess_post*/stderr.log ([F383-CSL] rows: "
                "valueOf color=0xffffffff; the honest attr-id gate catch "
                "0x10104e2 → null); DexSQL decode of Lf2/p.a (the exact "
                "bytecode: new ContextThemeWrapper → getTheme → "
                "obtainStyledAttributes([I) → getInt pc=22); "
                "evidence/cont82/dexsql_cookbook_chess/",
            "fix_surface":
                "dalvik_engine.cpp: csl_wrap_single helper + the ColorStateList "
                "class law + Resources.getColorStateList + "
                "TypedArray.getColorStateList (absent-slot → null AOSP law, "
                "attr-id gate) + the S101 producer gate extended to "
                "ContextThemeWrapper/Context/ContextWrapper receivers",
            "honest_note":
                "The full state-spec ColorStateList (state-dependent colors) "
                "is the named deeper frontier — the landed law is the single "
                "default-state spec (AOSP valueOf law), never an invented "
                "state color. The Ln0/k1.c getClass NPE family in chess is "
                "the F-NEW-384 domain, not this law.",
        },
        {
            "id": "F-NEW-384",
            "status": "LAW-LANDED-PARTIAL",
            "priority": "P1",
            "title": "Root window-insets dispatch (performTraversals insets "
                     "pass) — landed; measure-path residual named",
            "layer": "viewroot/lifecycle",
            "root_cause":
                "The engine never dispatched ANY window-insets pass; androidx "
                "fields caching platform insets (ActionBarOverlayLayout."
                "mLastInsets / mBaseInnerInsets and the fragment dispatch "
                "wrappers' own caches) stayed null and "
                "WindowInsetsCompat.toWindowInsetsCompat(null) NPE'd at the "
                "first getClass (Ln0/k1.c pc=2, chess ×7-8 uncaught → "
                "start.onCreate unwind → APP_DRAW_OPS white face).",
            "evidence":
                "run/cont82/chess_post8/9 stderr: [F384-ROOTINSETS] "
                "root=o421 (ActionBarOverlayLayout) dispatched=true (the "
                "skeleton-tree o232 and last-root o631 mispicks were caught "
                "and fixed during the wave); chess face byte-identical "
                "b270ff040b3601dc pre/post (zero drift)",
            "fix_surface":
                "dalvik_engine.cpp: dispatch_root_window_insets() consumed at "
                "the frame boundary BEFORE measure (AOSP performTraversals "
                "order); empty-insets law (no simulated system bars); "
                "down-tree child walk with the public dispatchApplyWindow-"
                "Insets entry first (the wrappers cache the platform insets "
                "in their own fields — bypassing them left second-generation "
                "nulls)",
            "honest_note":
                "PARTIAL: the dispatch is real and AOSP-ordered, but chess's "
                "k1.c NPE family persists via the measure-path cached-inset "
                "wrappers reading fields populated from PRE-dispatch passes "
                "(k1.b() platform-insets chain + the d1.l(IIII) builder "
                "family) — the second-generation null source is NAMED, not "
                "closed. AndStatus2048's Lt60;.getValue candidate belongs to "
                "this family; the CONT-76 decode stands.",
        },
        {
            "id": "F-NEW-385",
            "status": "ROOT-CAUSED-FIXED",
            "priority": "P1",
            "title": "Array component-typing law family (new-array zero-init "
                     "+ aput/fill/filled-new-array typing)",
            "layer": "interpreter/arrays",
            "root_cause":
                "(a) new-array left slots ABSENT (no zero-init) → unstored "
                "indices read null; (b) aput-boolean/char/byte/short stored "
                "the raw register (INT32 or the zeroed-register NULL) losing "
                "the component kind; (c) fill-array-data width-2 stored "
                "make_int for [C/[S; (d) filled-new-array stored untyped "
                "register values for [Z/[C/[B/[S. Every typed reader "
                "(Arrays.toString per-type rendering, aget-boolean identity) "
                "answered the wrong face. Caught by the CONT-82 fixture.",
            "evidence":
                "fixtures/cont82_arrays_fixture (com.probe.a2t) + "
                "scripts/cont82_build_arrays_probe.sh (real aapt2/ECJ/D8, "
                "apk run/cont82/cont82_arrays_probe.apk): pre-fix "
                "[1, null] / [120, 121], post-fix 8/8 PASS "
                "([1, 2, 3] / [true, false] / [x, y] / [] / [a, null] / "
                "null / null / [7]) — run/cont82/a2t4.out",
            "fix_surface":
                "dalvik_engine.cpp: NEW_ARRAY zero-init loop (component "
                "defaults, bounded 4096), ARRAY_PUT_CASE aput variant "
                "typing, FILL_ARRAY_DATA width-2 [C/[S typing, "
                "filled-new-array [Z/[C/[B/[S typing",
            "honest_note":
                "Closes the CONT-80 Track-4 acceptance gate (Arrays.toString "
                "overload matrix) that was BLOCKED_NEEDS_EVIDENCE — the "
                "matrix fixture now exists and locks the CONT-366 law at "
                "HEAD. Full regression battery green at binary 9a3d89f7995a5505.",
        },
    ]
    for nr in new_roots:
        if nr["id"] in by_id:
            by_id[nr["id"]].update(nr)
        else:
            roots.append(nr)
    if isinstance(r, dict) and "roots" in r:
        r["roots"] = roots
    json.dump(r, open(P1, "w"), indent=1, ensure_ascii=False)
    json.dump(r, open(P2, "w"), indent=1, ensure_ascii=False)
    ids2 = [x.get("id") for x in roots]
    assert len(ids2) == len(set(ids2)), "dup after update"
    print("registry updated:", len(roots), "roots (689 ->", str(len(roots)) + ")")


if __name__ == "__main__":
    main()
