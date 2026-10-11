#!/usr/bin/env python3
"""CONT-11: append F-NEW-260/261/262 to root_registry.json (no duplication;
566 -> 569 roots). Read-modify-write with full re-dump."""
import json

REG = '/home/z/my-project/root_registry.json'

NEW = [
    {
        "id": "F-NEW-260",
        "status": "ROOT-CAUSED-FIXED",
        "title": ("Class.getModifiers() for MEMBER (nested) classes returned the "
                  "class_def access_flags, which never carry ACC_STATIC in DEX "
                  "(the static bit lives in the SYSTEM visibility "
                  "Ldalvik/annotation/InnerClass; annotation). The support-v4 "
                  "BackStackRecord.doAddOp chain getClass->getModifiers->"
                  "isAnonymousClass->Modifier.isPublic->isMemberClass->isStatic "
                  "then mis-threw ISE \"Fragment <cls> must be a public static "
                  "class\" for legitimately static inner fragments and killed "
                  "BMI (com.zola.bmi) at BMIMain.onCreate (first-ever run). Fix "
                  "(generic, OpenJDK law: nested classes report the "
                  "InnerClasses-attribute flags): dex_parser captures the "
                  "InnerClass accessFlags into ClassInfo.inner_class_flags "
                  "(reflection visibility unchanged — F-087 Class.getAnnotation "
                  "still cannot see SYSTEM annotations); the "
                  "Class.getModifiers law prefers inner_class_flags when "
                  "present. A/B: BMI uncaught 2->0 (ISE + the follow-on "
                  "commit-on-null NPE both gone)."),
        "priority": "P0",
        "layer": "dex/reflection",
        "evidence": "evidence/cont11/cont11_ledger.json",
        "probe": ("scripts/cont11_innerclass_check.py (BMI "
                  "BMIMain$PlaceholderFragment: class_def flags 0x1 vs InnerClass "
                  "accessFlags 9 = PUBLIC|STATIC — ground truth); live A/B "
                  "bmi_postfix1 (uncaught 0)"),
        "verified_current": True,
        "discovered": "CONT-11",
    },
    {
        "id": "F-NEW-261",
        "status": "IMPLEMENTED+TESTED",
        "title": ("S83-APXACT activity-bypass scope law refined: the bypass "
                  "answered FragmentActivity/AppCompatActivity.onCreate void "
                  "even when the class ships a REAL DEX body, so the support "
                  "fragment host never attached (mHost null) and every app-"
                  "level transaction threw ISE \"Activity has been destroyed\" "
                  "(BMI). Fix: fall through to real DEX execution for the "
                  "legacy Landroid/support/ family (v4+v7 — ONE machine: the "
                  "v7 onCreate drives the v4 attachHost) when the class has a "
                  "DEX body. Scope measured BY A/B at the same binary: support "
                  "family real execution SURVIVES (BMI uncaught 2->0, "
                  "attachHost->attachController->enqueueAction all land, real "
                  "HostCallbacks/FragmentHostCallback ctors execute); the "
                  "androidx family stays on the S83 bypass because androidx "
                  "fall-through re-killed notes_secuso (NPE at "
                  "FragmentActivity.onCreate pc=0xc — mFragmentLifecycleRegistry "
                  "null = the F-NEW-262 initializer root) while the bypass keeps "
                  "it byte-identical to the recorded eb5ebd559cad1028 anchor. "
                  "Zero drift: dooz d602648e8e401895 / opencalc a976d2f9 / "
                  "microtimer da73010a / chess b5a7a35d / unote 4f1a9e4e / "
                  "notes eb5ebd559cad1028 all match recorded values (x3 core "
                  "trio)."),
        "priority": "P0",
        "layer": "framework/activity",
        "evidence": "evidence/cont11/cont11_ledger.json",
        "probe": ("A/B matrix baseline-binary (git checkout e99c2fbd sources, "
                  "byte-identical rebuild aed46450c103f2ea) vs fixed binary "
                  "0bb9798addccc548: solitaire 6588621c/28-uncaught IDENTICAL "
                  "both arms (predates this session), BMI 2->0, notes/dooz "
                  "zero drift"),
        "verified_current": True,
        "discovered": "CONT-11",
    },
    {
        "id": "F-NEW-262",
        "status": "CLASSIFIED",
        "title": ("Framework/API-bridge RETURN VALUE lost across specific "
                  "shadow->DEX dispatch shapes — three independent "
                  "manifestations at the same root family, all runtime-proven "
                  "this wave: (1) BMI FragmentHostCallback.<init> stores "
                  "value=<unset> into its final mHandler field (FIELD-TRACE "
                  "put-obj value=<unset>), so mHost.getHandler() answers null "
                  "and the commit runnable is posted on a NULL receiver "
                  "(ROOT-059 null-recv law silently no-ops) — the transaction "
                  "never executes (execPendingActions/moveToState/"
                  "performCreateView all 0); (2) solitaire (de.tobiasbielefeld."
                  "solitaire): bridge getCallback ANSWERS act=21 (S134-GCB row) "
                  "yet v7 WindowCallbackWrapper i.<init> receives NULL and "
                  "throws IAE \"Window callback may not be null\" (28 uncaught "
                  "at session start AND at the fixed binary — predates "
                  "CONT-11); (3) notes_secuso androidx fall-through: "
                  "mFragmentLifecycleRegistry null at "
                  "FragmentActivity.onCreate pc=0xc (final-field initializer "
                  "chain mFragments = FragmentController.createController(new "
                  "HostCallbacks()) loses its value). Fix surface: the "
                  "bridge_to_api result -> last_invoke_return_ -> "
                  "move-result-object path under invoke shapes that cross "
                  "shadow dispatch inside constructors. Blocks: BMI fragment "
                  "inflation (views=1 shell), AlexCalc androidx attach (\""
                  "Fragment null has not been attached yet\"), solitaire v7 "
                  "delegate chain, androidx family DEX-body execution."),
        "priority": "P0",
        "layer": "dex/bridge-return",
        "evidence": "evidence/cont11/cont11_ledger.json",
        "probe": "PENDING (next wave: FIELD-TRACE + METHOD-TRACE pc walk of the three chains)",
        "verified_current": True,
        "discovered": "CONT-11",
    },
]

with open(REG) as f:
    d = json.load(f)
ids = {r['id'] for r in d['roots']}
added = 0
for n in NEW:
    if n['id'] not in ids:
        d['roots'].append(n)
        added += 1
d['count'] = len(d['roots'])
d['total_roots'] = len(d['roots'])
d['status_counts'] = {}
for r in d['roots']:
    d['status_counts'][r['status']] = d['status_counts'].get(r['status'], 0) + 1
d['generated'] = "CONT-11 WAVE 7 (2026-10-11): F-NEW-260/261 landed A/B-proven; F-NEW-262 CLASSIFIED with three manifestations"
with open(REG, 'w') as f:
    json.dump(d, f, indent=1, ensure_ascii=False)
print(f"added {added}; roots now {d['count']}")
