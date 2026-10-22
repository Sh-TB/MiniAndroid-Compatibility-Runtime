#!/usr/bin/env python3
"""W9 close-out: register F-NEW-511b/512/513 in the root registry (825→828)."""
import json

BASE = '/home/z/my-project'
with open(f'{BASE}/root_registry.json') as f:
    roots = json.load(f)

NEW = [
    {
        "id": "F-NEW-511b",
        "title": "Collections.singletonList stored the RAW CLASS_REF (object_id=0) — every heap-field ref reader requires OBJECT_REF + oid!=0, so initializer dependency lists (EmojiCompatInitializer.dependencies → singletonList(DefaultLifecycleInitializer.class)) read back empty → 'iterator exhausted (pos=0)' → StartupException. W8 decoded it; W9 LANDED it (coupled with F-NEW-512): CLASS_REF elements materialize to the stable per-descriptor heap token (F-069/F-249/511a law) before the container store. Patch lineage: evidence/cont11/w8/fnew511_patch.diff (W8) → landed W9 dalvik_engine.cpp singletonList arm.",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework/collections-container",
        "root_cause": "container element store did not materialize CLASS_REF to heap token",
        "fix": "IMPLEMENTED+TESTED (live): the Kotpref/emoji2 androidx.startup dependency chain now completes — survivalmanual R350-FORNAME KotprefInitializer → getDeclaredConstructor → Kotpref.<clinit> OK rows at binary b4c44b940ab15bbc; anchors 5/5 x3 byte-identical (chess a0319686 / opencalc 63020bc7 / microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a) — zero drift, the W8 chess-flip coupling is CLOSED by F-NEW-512's filters law.",
        "evidence": "evidence/cont11/w9/ (battery + logs); evidence/cont11/w8/fnew511_patch.diff"
    },
    {
        "id": "F-NEW-512",
        "title": "android.widget.TextView had NO getFilters/setFilters/getTransformationMethod/setTransformationMethod state laws — emoji2's EmojiProcessingFilter.g([InputFilter) executed array-length on the NULL getFilters() result → NPE → Toolbar.setSubtitle's AppCompatTextView build (l/a1 ctor → l/w → x0/g.r → x0/f.r) unwound to onCreate APP-BOUNDARY → chess Toolbar 1080x0 (b270ff04) the moment F-NEW-511b let androidx.startup reach the emoji2 initializer chain (the W8-deferred coupling).",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework/textview-state",
        "root_cause": "AOSP TextView.java: mFilters = new InputFilter[0] (getFilters NEVER null); mTransformation null-until-set. No engine law → REC-MISS null → in-APK emoji2 DEX NPE.",
        "fix": "IMPLEMENTED+TESTED (live): set/getFilters record the filter array (default fresh empty InputFilter[0], identity law); set/getTransformationMethod record (AOSP null default). A/B: chess b270ff04 → a0319686 (anchor EXACT, 0 uncaught); survivalmanual FAB chain no longer reaches the emoji filter NPE.",
        "evidence": "evidence/cont11/w9/{chess_511b_run1,chess_fixed_run1}/ + scripts/cont11_w9_chess_disasm.py (full R8 decode of the x0/f-g-w chain)"
    },
    {
        "id": "F-NEW-513",
        "title": "Resources.getValue(int, TypedValue, resolveRefs) had NO engine law — androidx ResourcesCompat.isColorInt (in-APK DEX: value.type in 0x1C..0x1F) read the zero-state TypedValue → FALSE for every color → getColorStateList took the res.getXml(id) inflate path → F-371 NotFound on a COLOR id → Resources$NotFoundException unwound MaterialResources/FAB ctor (survivalmanual 29 uncaught; alexcalc Toolbar same signature).",
        "status": "IMPLEMENTED+TESTED",
        "priority": "P1",
        "layer": "framework/resources-typedvalue",
        "root_cause": "AOSP Resources.java getValue fills the TypedValue from the ARSC (Res_value dataType IS the TypedValue.type constant space) and throws NotFound for genuinely-missing app ids. No law → zero-state tv → isColorInt false → wrong inflate path.",
        "fix": "IMPLEMENTED (law landed with a SCOPED throw): resolved ids populate type/data/assetCookie/resourceId(+string); the NotFound throw fires ONLY for genuine app-package (0x7f...) ids missing from the ARSC. W9 A/B honesty: the unscoped throw killed chess+opencalc (framework ids 0x01… + RAW-VALUE ids leaking through the theme/attr slot — chess 0xfffef7ff via l/l2.b which has NO try blocks, so device truth never reaches that call) → scoped to 0x7f with zero-state rows for upstream leaks. Remaining content blocker for the FAB/Toolbar family is UPSTREAM: the theme-attr TypedArray slot answers raw values where id-typed consumers need real ids (F-NEW-483 theme-gate family — CLASSIFIED — owns the decode; survivalmanual 0x7f0400e5 resolves INT not color-reference upstream).",
        "evidence": "evidence/cont11/w9/{survivalmanual_f513b,f513_chess_logged,final3_*}/ + [F513-GETVALUE] diagnostic rows"
    },
]

ids = {r['id'] for r in roots}
added = 0
for n in NEW:
    if n['id'] not in ids:
        roots.append(n)
        added += 1
with open(f'{BASE}/root_registry.json', 'w') as f:
    json.dump(roots, f, indent=0)
print(f'added {added} roots; total now {len(roots)}')
