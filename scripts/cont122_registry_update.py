#!/usr/bin/env python3
"""cont122_registry_update.py — CONT-122 wave registry landing.

Probe-resolved upgrades (16-probe behavioral battery, run/c122 evidence),
honest CONFIRMED-gap classifications, and husk-row hygiene (48 untitled
"no trace"/"-" audit-generation residue rows). Both registry files
(root_registry.json main + canonical/root_cause_registry.json mirror) are
updated IN SYNC by reusing the CONT-117 by-ID sync law.
"""
import json
import copy
import sys

DATE = "2026-10-20"
BIN = "72018b033d904f16"
PROBE = "run/c122/final_probe_out.log (13 PASS / 3 honest FAIL) + prefix evidence run/c122/prefix_out.log (6 PASS / 10 FAIL pre-fix)"

MAIN = "root_registry.json"
MIRROR = "canonical/root_cause_registry.json"

# ── probe-resolved upgrades ─────────────────────────────────────────────
# (id, new_status, title_suffix/evidence note)
UPGRADES = {
    "R-NEW-010": {
        "status": "ROOT-CAUSED-FIXED",
        "note": (
            "ROOT-CAUSED-FIXED (CONT-122). LIVE probe c122: pre-fix face "
            "'U01-STORED no-exception value=7' — aput-object stored "
            "String[]<-Integer silently (no store-check); post-fix 'U01-RAISED "
            "java.lang.ArrayStoreException' + typed catch (fixture-first: probe "
            "observed the gap BEFORE the law landed). LAWS LANDED: (1) aput-object "
            "ArrayStoreException store-check (AOSP HandleAPutObject + "
            "art::ThrowArrayStoreException; conservative scope: concrete "
            "descriptors both sides, never the synthetic Larray; marker). The "
            "check EXPOSED three deeper pre-existing silent bugs, all fixed: "
            "(2) reflect Array.newInstance make_array_elem_desc double-wrapped "
            "descriptor-form elements into MALFORMED '[LLcom/...;;' arrays "
            "(tower3d live face — libGDX Array(Class)→newInstance path); "
            "(3) dalvik_class_assignable never consulted the STARTING class's "
            "own declared interfaces (anonymous AndroidApplication$1 implements "
            "LifecycleListener → false negative); (4) framework hierarchy tables "
            "lacked android.animation (ValueAnimator→Animator, telegram face) "
            "and android.text (SpannableStringBuilder→CharSequence) chains. "
            "VERIFIED: c122 U01/U02 PASS + 9/9 anchors zero drift at " + BIN
        ),
    },
    "R-NEW-169": {
        "status": "ROOT-CAUSED-FIXED",
        "note": (
            "ROOT-CAUSED-FIXED (CONT-122). LIVE probe c122: pre-fix 'U03-ALLOCATED "
            "size=2147483645' (metadata-only allocation 'succeeded'); post-fix "
            "'U03-RAISED java.lang.OutOfMemoryError msg=Failed to allocate a "
            "8589934580-byte allocation' (ART-style message). LAW: new-array "
            "byte-size (element size per descriptor [B=1 [Z/[C=2 [S/[I=4 "
            "[J/[F/[D/ref=8) > 1 GiB budget → OutOfMemoryError. Fixture note: "
            "ECJ constant-folded the first fixture's unused allocation — the "
            "fixed fixture stores to a static field to keep the allocation live. "
            "9/9 anchors zero drift at " + BIN
        ),
    },
    "R-NEW-097": {
        "status": "ROOT-CAUSED-FIXED",
        "note": (
            "ROOT-CAUSED-FIXED (CONT-122). LIVE probe c122 U09: pre-fix cats=0 "
            "(addCategory unhandled) and matchAction unusable; post-fix "
            "'matchAction true/false cats=1'. LAW: IntentFilter.addCategory/"
            "countCategories/getCategory/matchAction (AOSP IntentFilter.java — "
            "addCategory appends unconditionally, matchAction = exact contains "
            "over mActions) riding the #371 B5 intent_filters_ state, with the "
            "new intent_filter_categories_ map. 9/9 anchors zero drift at " + BIN
        ),
    },
    "R-NEW-283": {
        "status": "ROOT-CAUSED-FIXED",
        "note": (
            "ROOT-CAUSED-FIXED (CONT-122). LIVE probe c122 U10: pre-fix the "
            "component round-trip failed — getComponent answered a FRESH EMPTY "
            "ComponentName (only the class string was recorded); post-fix full "
            "identity round-trip incl. setComponent(ComponentName) field "
            "propagation. LAWS: Intent.setClassName(pkg,cls) records BOTH halves; "
            "getComponent builds the ComponentName with mPackage/mClass (F-116 "
            "convention); NEW ComponentName.getPackageName/getClassName accessors. "
            "9/9 anchors zero drift at " + BIN
        ),
    },
    "R-NEW-055": {
        "status": "VERIFIED-CORRECT",
        "note": (
            "VERIFIED-CORRECT (CONT-122). LIVE probe c122 U14: "
            "putSparseParcelableArray→getSparseParcelableArray round-trip of a "
            "SparseArray<Bundle> with inner Bundle now byte-identical (pre-fix "
            "null). LAW: Bundle object-valued arms (SparseParcelableArray/"
            "ParcelableArrayList/Bundle) identity round-trip through the "
            "bundle:<key> convention; the SparseArray half rides F-NEW-334. "
            "Honest residual: parcel-edge shapes beyond the sparse/arraylist/"
            "bundle family remain unprobed (packed primitive arrays named in "
            "the original audit stay a named residual). 9/9 anchors at " + BIN
        ),
    },
    "R-NEW-032": {
        "status": "VERIFIED-CORRECT",
        "note": (
            "VERIFIED-CORRECT (CONT-122). LIVE probe c122 U06: invalidate + "
            "postInvalidate + requestLayout exercised live on a live view tree, "
            "no exception, next frames rendered (the invalidation trace the "
            "audit demanded now exists). 9/9 anchors at " + BIN
        ),
    },
    "R-NEW-192": {
        "status": "VERIFIED-CORRECT",
        "note": (
            "VERIFIED-CORRECT (CONT-122). LIVE probe c122 U07: scrollTo(10,20) → "
            "getScrollX/Y == 10/20; scrollBy(5,-5) → 15/15 — the scroll law "
            "verified live (the scroll trace the audit demanded now exists). "
            "9/9 anchors at " + BIN
        ),
    },
    "R-NEW-193": {
        "status": "ROOT-CAUSED-FIXED",
        "note": (
            "ROOT-CAUSED-FIXED (CONT-122). LIVE probe c122 U08: pre-fix "
            "getMatrix() answered null (translation stored, matrix never built); "
            "post-fix matrix=yes. LAW: View.getMatrix() composes rotation+scale "
            "about the pivot into the Android Matrix m0..m8 convention (AOSP "
            "transformMatrix — translationX/Y deliberately NOT part of the "
            "matrix; honest note: fresh Matrix object per call, AOSP reuses "
            "mMatrix — named residual). 9/9 anchors at " + BIN
        ),
    },
    "R-NEW-282": {
        "status": "VERIFIED-CORRECT",
        "note": (
            "VERIFIED-CORRECT (CONT-122). LIVE probe c122 U04 REFUTES the "
            "recorded claim 'singletonMap/unmodifiableMap NOT implemented': "
            "Collections.singletonMap + unmodifiableMap round-trip verified "
            "live (size/get/containsKey + wrap-read). singletonList/emptyList "
            "already covered by F-039 (3ed13292). 9/9 anchors at " + BIN
        ),
    },
    "R-NEW-284": {
        "status": "VERIFIED-CORRECT",
        "note": (
            "VERIFIED-CORRECT (CONT-122). LIVE probe c122 U05: check-cast "
            "register preservation proven behaviorally — (String)null cast is "
            "legal (no NPE at the cast), the cast result received "
            "real.length()==3 (register carried the value), null-cast-then-"
            "invoke NPEs at the invoke site per AOSP. 9/9 anchors at " + BIN
        ),
    },
    "R-NEW-094": {
        "status": "VERIFIED-CORRECT",
        "note": (
            "VERIFIED-CORRECT (CONT-122, parse half). LIVE probe c122 U15: "
            "manifest exported flag parsed and surfaced via "
            "PackageManager.getActivityInfo (exported=true live). Honest note: "
            "'enforcement' is N/A in a single-app runtime by design (no "
            "cross-app IPC surface exists to enforce against); the recorded "
            "claim 'exported parsed, not enforced' resolves to parsed=proven, "
            "enforcement=not-applicable. 9/9 anchors at " + BIN
        ),
    },
    "R-NEW-132": {
        "status": "VERIFIED-CORRECT",
        "note": (
            "VERIFIED-CORRECT (CONT-122). LIVE probe c122 U16: a class living "
            "in classes2.dex (two-dex probe APK built by "
            "scripts/cont122_build_probe.sh) resolved via Class.forName AND "
            "passed an instanceof check against a classes.dex-declared "
            "interface — the dynamic multi-dex enumeration trace now exists. "
            "Sibling R-NEW-133 (in-memory DEX) stays UNPROVEN (different API, "
            "not probed). 9/9 anchors at " + BIN
        ),
    },
    # honest CONFIRMED gaps (probe-evidenced, not fixed this wave)
    "R-NEW-161": {
        "status": "CLASSIFIED",
        "note": (
            "CLASSIFIED CONFIRMED_OPEN_GAP (CONT-122). LIVE probe c122 U11: "
            "/proc/self/cmdline canRead=false — the file sandbox blocks /proc "
            "passthrough (recorded claim CONFIRMED by live evidence). Named "
            "design tension: a raw passthrough would leak HOST identity "
            "(runtime cmdline), so the honest terminal shape is a CURATED "
            "/proc/self law (app-shaped cmdline/build values) — registered as "
            "the landing lever, not silently widened. Probe face + fix lever "
            "in evidence/cont122/."
        ),
    },
    "R-NEW-083": {
        "status": "CLASSIFIED",
        "note": (
            "CLASSIFIED CONFIRMED_OPEN_GAP (CONT-122). LIVE probe c122 U12: "
            "getPackageInfo(pkg, GET_SIGNATURES) → signatures=null (len -1). "
            "AOSP contract named: PackageInfo.signatures carries the v2/v3 "
            "signing-cert chain ([Landroid/content/pm/Signature; with "
            "toCharsString hex DER); landing lever = APK v2 signing-block "
            "(id 0x7109871a) parse in apk_parser + Signature shadow. No fake "
            "signatures served. Probe face in evidence/cont122/."
        ),
    },
    "R-NEW-151": {
        "status": "CLASSIFIED",
        "note": (
            "CLASSIFIED CONFIRMED_OPEN_GAP (CONT-122). LIVE probe c122 U13: "
            "Class.forName('androidx.core.content.FileProvider') → "
            "ClassNotFoundException — androidx.core is outside the shadow set. "
            "Landing lever: FileProvider.getUriForFile law (device-rooted "
            "content:// authority mapping over the file sandbox). Probe face "
            "in evidence/cont122/."
        ),
    },
}

HUSK_NOTE = (
    "STALE_OR_SUPERSEDED (CONT-122 registry hygiene): untitled audit-generation "
    "residue — no behavioral claim (title is a bare 'no trace'/'-' marker), no "
    "evidence pointer (CONT-105 triage: BLOCKED_NEEDS_EVIDENCE 'no evidence "
    "pointer'), no referent beyond MASTER_WORKLIST's '(untitled registry entry) "
    "MC-126 documentation/registry consistency' stub, and no id-string mention "
    "in evidence/run/docs beyond index scans (CONT-119/121 full-scan law). "
    "Superseded by the titled rows that carry the actual content; nothing is "
    "merged into another root (independent-id law honored — the rows terminate "
    "as themselves, not as aliases). Probe battery note: substantive siblings "
    "(ArrayStoreException/OOM/scroll/transform/IntentFilter/Parcel/...) were "
    "NOT swept by this hygiene pass — 16 probes resolved 11 of them by live "
    "behavior."
)

def main() -> None:
    mirror = json.load(open(MIRROR))
    main_reg = json.load(open(MAIN))
    mroots = main_reg["roots"] if isinstance(main_reg, dict) else main_reg

    def apply(reg_roots):
        by_id = {}
        for r in reg_roots:
            by_id.setdefault(r["id"], r)
        changed = 0
        # upgrades
        for rid, upd in UPGRADES.items():
            r = by_id.get(rid)
            if r is None:
                print(f"MISS {rid}")
                continue
            r["status"] = upd["status"]
            old_ev = r.get("evidence") or ""
            r["evidence"] = (old_ev + "\n" if old_ev else "") + upd["note"]
            r["verified_current"] = True
            r["date"] = DATE
            changed += 1
        # husk hygiene
        for r in reg_roots:
            if r.get("status") != "UNPROVEN":
                continue
            t = r.get("title") or ""
            body = t.split(":", 1)[1].strip() if ":" in t else ""
            if body in ("no trace", "no live trace", "-"):
                r["status"] = "STALE_OR_SUPERSEDED"
                old_ev = r.get("evidence") or ""
                r["evidence"] = (old_ev + "\n" if old_ev else "") + HUSK_NOTE
                r["verified_current"] = True
                r["date"] = DATE
                changed += 1
        return changed

    croots = mirror["roots"] if isinstance(mirror, dict) and "roots" in mirror else mirror
    n_mirror = apply(croots)
    n_main = apply(mroots)
    print(f"changed mirror={n_mirror} main={n_main}")

    if isinstance(mirror, dict):
        json.dump(mirror, open(MIRROR, "w"), indent=1, ensure_ascii=False)
    else:
        json.dump(croots, open(MIRROR, "w"), indent=1, ensure_ascii=False)
    if isinstance(main_reg, dict):
        json.dump(main_reg, open(MAIN, "w"), indent=1, ensure_ascii=False)
    else:
        json.dump(mroots, open(MAIN, "w"), indent=1, ensure_ascii=False)

    # sanity: id-unique + status distribution
    import collections
    for name, roots in (("main", mroots), ("mirror", croots)):
        ids = [r["id"] for r in roots]
        dup = len(ids) - len(set(ids))
        dist = collections.Counter(r["status"] for r in roots)
        print(name, "roots", len(ids), "dup", dup, dict(dist.most_common(6)))

if __name__ == "__main__":
    main()
