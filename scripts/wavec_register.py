#!/usr/bin/env python3
"""FINAL CAMPAIGN wave (phases 4 + wave-C): registry updates.
F-NEW-181 ROOT-CAUSED-FIXED (array type law) + F-NEW-190 (Build ABI /
ApplicationInfo install-time identity) + F-NEW-191 (activity attach law)
appended; worklog section recorded.
"""
import json, hashlib
from pathlib import Path

REG = Path('/home/z/my-project/canonical/root_cause_registry.json')
data = json.loads(REG.read_text())
roots = data['roots'] if isinstance(data, dict) and 'roots' in data else data
maxn = max(int(r['id'].split('-')[-1]) for r in roots
           if str(r.get('id', '')).startswith('F-NEW-'))
assert maxn == 189, f'unexpected max F-NEW-{maxn}'


def upd(rid, **kw):
    for r in roots:
        if r.get('id') == rid:
            r.update(kw)
            return True
    return False


upd('F-NEW-181',
    status='ROOT-CAUSED-FIXED',
    law='ARRAY TYPE LAW (JVMS 4.4 / AOSP Class.isAssignableFrom): an array '
        "object's runtime class IS its descriptor. NEW_ARRAY now stores the "
        'resolved element-type descriptor (filled-new-array precedent) + '
        '__element_type__ provenance; is_subclass_of classifies array types: '
        'primitive arrays final (exact-only), object arrays covariant on '
        'element type, nested arrays = Object/Cloneable/Serializable family, '
        "non-array vs array type FALSE, legacy 'Larray;' = unknown-element "
        'object array.',
    resolution='SOURCE->CODE PATH->LAW->REPRO->TRACE->FIX->3RUN complete. '
    'SOURCE: APK DEX RegularImmutableMap.create/get/createHashTable '
    '(scripts/wavec_scan.py, wavec_disasm.py): the only createHashTable call '
    'site gates the duplicate-key wrapper {partialTable, insertedCount, '
    'dupEntry} with `instance-of v2, [Ljava/lang/Object;`. CODE PATH: '
    "NEW_ARRAY stamped every array 'Larray;' -> is_subclass_of answered "
    'FALSE -> the Object[3] wrapper was stored AS the map table -> lawful '
    'get() probe looped (PC=0x6f, 50001 visits). TRACE (one instrumented '
    'run, MINIANDROID_WAVEC_TRACE permanent probe): chooseTableSize(17750) '
    '-> 32768 LAWFUL; createHashTable(alternating=47425, maxSize=17750, '
    'tableSize=32768); post-fix the wrapper is detected and unwrapped — map '
    'built with the real [S 32768 table, lawfully truncated at the dup key '
    '(size=16052, alternating copyOf 32104) per guava-33 semantics; chain '
    'advanced (0 HALT-LOOP/F084 spins, 32->8 errors). FIX: NEW_ARRAY real '
    'descriptor + is_subclass_of array closure. 3RUN: all 5 goldens '
    'byte-identical (dooz d602648e8e401895, ssw 10446aaf0cd642cc, '
    'headingcalc be1cea9cf994b26a, microtimer da73010a37dd0189, whatsapp '
    '31ddd4d5b8e6d18e) x3 + laws130 51/51. UPSTREAM: the duplicate key '
    'itself = F-NEW-173 placeholder-materialization family (open, deepest '
    'DI-lattice frontier).')

roots.append({
    'id': 'F-NEW-190',
    'status': 'ROOT-CAUSED-FIXED',
    'priority': 'P1',
    'layer': 'framework/device-identity',
    'title': 'PHASE 4 device identity: Build.SUPPORTED_ABIS absent (ISE "No '
             'supported ABIs found on this device" x3, LX/0Cz) + '
             'ApplicationInfo install-time identity absent (sourceDir null -> '
             'SoLoader LX/0Dl.A01 NPE "String.equals on null" via LX/0EU.CKw '
             'direct read; primaryCpuAbi null via reflective '
             'getDeclaredField).',
    'law': 'AOSP Build/PackageParser laws: SUPPORTED_ABIS/SUPPORTED_32/64_BIT'
           '_ABIS/CPU_ABI(_2) come from ro.product.cpu.abilist and are never '
           'empty; a normal install records sourceDir/publicSourceDir/'
           'dataDir/nativeLibraryDir/primaryCpuAbi on ApplicationInfo — '
           'never null. The runtime models an arm64 android-34 device '
           '(arm64-v8a primary, matching the SDK_INT=34 fingerprint law).',
    'resolution': 'seed_framework_device_statics: ABI list arrays (heap '
                  '[Ljava/lang/String; with element provenance); '
                  'getApplicationInfo law seeds sourceDir (real APK path)/'
                  'publicSourceDir/nativeLibraryDir/primaryCpuAbi; '
                  'Field.get instance fallback answers primaryCpuAbi/'
                  'nativeLibraryDir for the framework declarer. POST: both '
                  'SoLoader faces + the ABI ISE faces GONE (exception census '
                  '12 -> 9).',
    'evidence': 'run /tmp/wavec8-10 logs; [R337-REFLECT] '
                'getDeclaredField("primaryCpuAbi") synthetic-auto trace; '
                'LX/0EU.CKw disasm (sourceDir direct iget); gates x3 '
                'byte-identical.'})

roots.append({
    'id': 'F-NEW-191',
    'status': 'ROOT-CAUSED-FIXED',
    'priority': 'P0',
    'layer': 'framework/activity-attach',
    'title': 'PHASE 4 attach ordering: the engine never ran the app-level '
             'attachBaseContext override during activity launch (AOSP '
             'performLaunchActivity: <init> -> attach -> onCreate). WhatsApp '
             'LX/0IH override = the DI members-injector (stores lattice '
             'providers into A01/A0H/A03/A0I/A0F/A0B via LX/00C slot '
             'lookups); absent it, onCreate reads null fields -> NPE '
             "'Map.get on null' (0IH.onCreate pc=14) -> Main.onCreate "
             'catch-all rethrow BEFORE super.onCreate -> the fragment host '
             'never attaches -> the onResume/onStart ISE family '
             '("FragmentManager has not been attached to a host." / '
             '"No activity").',
    'law': 'AOSP ActivityThread.performLaunchActivity ordering law: '
           'activity.attach (drives attachBaseContext on the VIRTUAL '
           'override — closest declaration wins) precedes onCreate and the '
           'lifecycle-callback fan-outs. Chains without an override resolve '
           'to the framework boundary (F-NEW-166 ContextWrapper law serves '
           'mBase).',
    'resolution': 'run_activity_default_init now dispatches '
                  'attachBaseContext after <init> on every launch path '
                  '(direct + try_recursive_invoke_on_super bounded climb, '
                  'receiver identity preserved; F-NEW-184 base-context '
                  'convention). POST: [WAVEC-ATTACH-FIELD] A0B=obj#29343 '
                  'A03/A05 stored on obj#28223 before onCreate; the '
                  'SoLoader family advanced. HONEST RESIDUE: the attach '
                  'still dies partway at iget LX/0IE;->A00 (the component-'
                  'state holder, only writer = reflective injector A3d) — '
                  'the F-NEW-173/169 DI-lattice deep face remains the '
                  'dominant WhatsApp frontier; fragment-host ISE faces are '
                  'downstream of it.',
    'evidence': 'scripts/wavec_field_writers.py (A0B single-writer proof: '
                'LX/0IH.attachBaseContext); FIELD-TRACE A0B put/get census '
                'on obj#28223; 0IH.attachBaseContext + 0IH.onCreate '
                'disassembly; gates x3 byte-identical.'})

if isinstance(data, dict) and 'roots' in data:
    data['roots'] = roots
    json.dump(data, REG.open('w'), indent=1)
else:
    json.dump(roots, REG.open('w'), indent=1)
print('registry now', len(roots), 'roots')
