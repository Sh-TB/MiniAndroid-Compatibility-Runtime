#!/usr/bin/env python3
"""CONT-121 registry update — by-ID discipline (CONT-111/117 precedent):
update root_registry.json (main) AND canonical/root_cause_registry.json
(authoritative mirror) row-equal. No id inflation beyond the two new rows."""
import json, sys

NEW_ROWS = [
    {
        "id": "F-NEW-467",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "dex/concurrency (desugared-lib method-scoped bypass discipline)",
        "title": "BOUNCY Set.add-ON-NULL (f141-null-recv x9): the EXP-088+ Phase 5 CHM bridge bypass was CLASS-SCOPED — it force-bridged EVERY Lj$/util/concurrent/ConcurrentHashMap; method to protect the two decoded hang methods (.e/.f = computeIfAbsent/compute). The bridge has no newKeySet handler, so ConcurrentHashMap.newKeySet() (real dex bytecode at BouncyActivity.<init> 0x00fa: new KeySetView(new CHM(), TRUE)) answered <unset> — FIELD-TRACE pinned iput requestedThumbnails value=<unset> at obj#21 — and requestThumbnail pc=6 died 'Set.add on null' x9 per getView. Fix (F-NEW-215 precedent: a bypass owns exactly the methods whose bytecode hangs): both swallow lists now METHOD-SCOPED to the compute family (.e/.f R8-renamed + computeIfAbsent/compute/computeIfPresent/merge real names); every other CHM method executes its real dex bytecode. Verified: FIELD-TRACE value=obj#96 (real KeySetView), f141 count 9->0.",
        "evidence": ["run/c121/bouncy.log (f141 x9)", "run/c121/bouncy_ft.log (FIELD-TRACE <unset>)",
                     "run/c121/bouncy2.log (value=obj#96, f141 0)", "scripts/cont121_bouncy_decode.py",
                     "scripts/cont121_s2_builder.py"],
    },
    {
        "id": "F-NEW-468",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "dex/concurrency (Unsafe array-element atomic law)",
        "title": "DesugarVarHandle$0.m CAS-RETRY SPIN (F084 halt, bouncy, after F-NEW-467 lifted newKeySet): KeySetView.add -> CHM.putVal -> casTabAt(table, i) -> Unsafe.compareAndSwapObject(tab, ABASE+i*ASHIFT, ...) — the engine answers arrayBaseOffset=0/arrayIndexScale=1 so the dex-computed offset IS the element index, but field_name_for337 only resolves OBJECT-field offsets -> F-NEW-217 UNSAFE-CAS-UNRESOLVED (obj=277 offset=1) -> CAS false forever while getObject kept returning the expected value -> infinite retry, F084 interpreter halt (honest, not a hang). Fix (F-NEW-468 law): resolve_unsafe_name_for337 — when the target object is an array box (has __array_length__), the offset addresses the ELEMENT 'array[i]' (offset bounds-checked); the object-field offset registry (F-NEW-160) is only consulted for non-array targets (a blind registry hit on a colliding offset would cross-link two objects' storage). Landed across getObject/getObjectVolatile/getOrderedObject, putObject family, compareAndSwapObject/Int/Long. Verified: bouncy rc 1->0 FULL SUCCESS (first clean corpus run of bouncy), F084 0, F-NEW-217 0, face stable 8a6c24ac.",
        "evidence": ["run/c121/bouncy2.log (F084 halts, F-NEW-217 x16)", "run/c121/bouncy3.log (rc=0 clean)",
                     "scripts/cont121_c3_analysis.py"],
    },
]

for path in ["root_registry.json", "canonical/root_cause_registry.json"]:
    reg = json.load(open(path))
    roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg
    ids = {r.get("id") for r in roots}
    # 1. F-NEW-449 upgrade
    for r in roots:
        if r.get("id") == "F-NEW-449":
            r["status"] = "ROOT-CAUSED-FIXED"
            r["title"] = (
                r.get("title", "")
                + " || CONT-121 ENDGAME ROOT: the two-count-sources divergence was String.length() answering the UTF-8 BYTE count while n2.r walks String.charAt/length() under the JVM UTF-16 CODE-UNIT law — the p3 info string is 40 UTF-16 units but 64 UTF-8 bytes (12 Myanmar-block chars = 3 bytes each, 1 unit), so the walk loop i<length() ran 24 phantom iterations, decoded garbage field descriptors, over-consumed the Object[11] entries array (built by p3.d case-4: 11 x aput-object zzd..zzn) and died at entries[11] (S36-AOOB len=11 idx=11). Fix (JVM unit law, str_utf16_unit_count/str_char_at_unit): String.length() answers the UTF-16 unit count and String.charAt(idx) addresses units (supplementary code point = two unit slots, high+low surrogate) at BOTH dispatch sites (C97 bridge-intrinsic entry + F-090e deep site). Verified: n2.r walk resolves ALL 11 p3 fields in p3.d's exact aput order (zze,zzd,zzg,zzh,zzi,zzf,zzj,zzk,zzl,zzm,zzn), S36-AOOB eliminated, telegram screenshot face 20ac8cbbbb byte-identical to the recorded anchor."
            )
            ev = r.get("evidence")
            if not isinstance(ev, list):
                ev = [ev] if ev else []
            r["evidence"] = list(set(ev + [
                "run/c121/telegram.log (11/11 field walk, no AOOB)",
                "run/c121/dis_p3_d.txt (Object[11] builder)",
                "run/c121/dis_n2;_r.txt (MessageSchema walk, pc=692)",
                "scripts/cont121_info_string.py (40 units vs 64 bytes)"]))
    # 2. new rows
    for row in NEW_ROWS:
        if row["id"] not in ids:
            roots.append(row)
            ids.add(row["id"])
    json.dump(reg, open(path, "w"), indent=1, ensure_ascii=False)
    print(f"{path}: {len(roots)} roots")

# integrity check
m = json.load(open("root_registry.json"))
c = json.load(open("canonical/root_cause_registry.json"))
mroots = m["roots"] if isinstance(m, dict) and "roots" in m else m
croots = c["roots"] if isinstance(c, dict) and "roots" in c else c
mids = [r["id"] for r in mroots]
cids = [r["id"] for r in croots]
print("id-unique:", len(mids) == len(set(mids)), "main==mirror ids:", set(mids) == set(cids),
      "counts:", len(mids), len(cids))
mm = {r["id"]: r.get("status") for r in mroots}
cc = {r["id"]: r.get("status") for r in croots}
print("status row-equal:", mm == cc)
