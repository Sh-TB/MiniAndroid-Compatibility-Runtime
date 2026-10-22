#!/usr/bin/env python3
"""cont155_train4_registry.py — TRAIN 3+4: WINDOW_ROOT cohort census (17 apps,
4 sub-types) + F-NEW-482 ROOT-CAUSED-FIXED (inherited-onCreate dispatch).
Syncs both registry files, verifies id-unique + main==mirror."""
import json, sys

NEW_ROOT = {
    "id": "F-NEW-482",
    "title": "F-NEW-482 — launcher-activity INHERITED onCreate silently skipped by the DEX-0 entry-point path: the same-class all_methods() scan found no onCreate/main and fell through without any super-chain resolution (AOSP ActivityThread.performLaunchActivity always calls activity.onCreate regardless of declaring class) — ROOT-CAUSED-FIXED in dalvik_engine.cpp",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": "activity-lifecycle",
    "evidence": (
        "CONT-155 TRAIN 3 (binary f6b272ea, 17-app WINDOW_ROOT cohort census"
        " scripts/cont155_train3_windowroot.sh -> run/c155/t3/): cohort = 4"
        " sub-types — A:7 onCreate-never-ran (flashlight, app.subster, voyager,"
        " how2vote, ricochlime, fdroid-privileged, fossify-contacts), B:2"
        " app-DI/Koin NoDefinitionFound at onCreate (goodtime Lcc4;.e 'No"
        " definition found for type' via wb2.z lazy getValue; readrops), C:3"
        " AppCompat theme-gate false-negative (todolist/leradar/exodusprivacy:"
        " AppCompatDelegateImpl.createSubDecor throws 'You need to use a"
        " Theme.AppCompat theme' although the app declares Theme.AppCompat —"
        " engine theme-attr resolution gap), D:4 named exceptions (ghostsq"
        " ArrayStoreException, aat/shizuwall/librecontactsbackup NPE)."
        " Sub-type A decoded (flashlight verbose run t3f4): launcher path"
        " prints F-NEW-169 attachBaseContext -> U0113-ACTIVITY -> C94"
        " LAUNCH-STORE -> 'main_method is EMPTY, trying fallback' — the DEX-0"
        " path's 'Find onCreate' loop scans ONLY cls.all_methods() of the"
        " launcher class itself (SplashActivity declares only <init>; the"
        " real onCreate is Ll7/h; 219 insns) -> loop finds nothing ->"
        " entry_point_search_done with main_method EMPTY -> legacy fallback"
        " heuristic runs some other class. The manifest multi-DEX path and"
        " G07 onStart/onResume already resolve via try_recursive_invoke"
        " super-chain; the DEX-0 path did not. FIX (dalvik_engine.cpp, after"
        " the same-class method loop, before goto entry_point_search_done):"
        " when main_method is still empty, dispatch INHERITED onCreate via"
        " try_recursive_invoke(cls, 'onCreate', {this, null})"
        " (Landroid/os/Bundle;)V with the full AOSP wrap — CONT-68 theme bind"
        " -> F-058 onActivityPreCreated -> onCreate -> F-NEW-304"
        " fragments-to-created -> onActivityCreated -> F-NEW-366 finish gate"
        " -> A93 onPostCreate -> onActivityPostCreated. VERIFY (binary after"
        " rebuild, wall 9/9 anchors byte-identical incl. dooz d602648e +"
        " telegram 20ac8cbbbb; negatives 19/19 after probe-store prep was"
        " re-created post container-reset — the 9/19 intermediate was the"
        " missing probe_store artifact, not a fix regression; skill selftest"
        " 13/13): flashlight SplashActivity.onStart 27->1190 insns,"
        " setContentView NOW fires (F023-PARENTLINK view=1102, R349-ORDER"
        " attach+measure, R005-DECOR view=2668 under decor=1101), face"
        " default-bg -> 100% non-white splash; cohort re-run (run/c155/t4_*):"
        " 6/17 WINDOW_ROOT apps now render real content (flashlight, subster,"
        " voyager, how2vote, fossify-contacts, fossify-filemanager);"
        " honest residuals named: aat (still no onCreate evidence — next"
        " case), C-type theme gate (3 apps reach setContentView then die),"
        " Koin pair, NPE trio."
    ),
}

for path in ('canonical/root_cause_registry.json', 'root_registry.json'):
    reg = json.load(open(path))
    roots = reg['roots'] if isinstance(reg, dict) and 'roots' in reg else reg
    if any(isinstance(r, dict) and r.get('id') == 'F-NEW-482' for r in roots):
        print(f'{path}: F-NEW-482 already present')
    else:
        roots.append(NEW_ROOT)
        print(f'{path}: F-NEW-482 appended ({len(roots)} roots)')
    ids = [r['id'] for r in roots if isinstance(r, dict) and 'id' in r]
    assert len(ids) == len(set(ids)), f'{path}: id not unique'
    json.dump(reg, open(path, 'w'), ensure_ascii=False, indent=1)

a = json.dumps(json.load(open('canonical/root_cause_registry.json')), sort_keys=True, ensure_ascii=False)
b = json.dumps(json.load(open('root_registry.json')), sort_keys=True, ensure_ascii=False)
assert a == b, 'main != mirror'
print('main==mirror OK, id-unique OK')
