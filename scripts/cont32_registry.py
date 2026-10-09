#!/usr/bin/env python3
# cont32_registry.py — add F-NEW-290 to root_registry.json (598 -> 599),
# dedup-checked, status_counts reconciled.
import json

REG = "/home/z/my-project/root_registry.json"
with open(REG) as f:
    r = json.load(f)

ids = [x.get("id") for x in r["roots"]]
assert "F-NEW-290" not in ids, "F-NEW-290 already present — dedup check failed"
assert ids[-1] == "F-NEW-289", f"unexpected tail: {ids[-1]}"

entry = {
    "id": "F-NEW-290",
    "status": "ROOT_CAUSED_FIXED",
    "title": "DIALOG OBJECT LAW: Dialog.getWindow()/getContext() answered NULL for any Dialog receiver "
             "whose runtime class is a renamed subclass (DialogShadow::handles_class gates on the platform "
             "class names; the virtual dispatch reaches the bridge with the runtime class; the S71 ancestry "
             "walk then re-dispatches Dialog->Context and the stub default answers null) \u2014 androidx "
             "DialogWrapper's ctor `val window = window ?: error(\"Dialog has no window\")` then killed the "
             "whole dialog path (composeStopwatch ground truth: ISE 'Dialog has no window' x31/run at "
             "Lea;.r pc=2 depth=53).",
    "priority": "P1",
    "layer": "dalvik-engine/dialog-window",
    "root_cause": "FIRST DIVERGENCE PROVEN AT RUNTIME (2026-10-09, run/cont32: composeStopwatch v1.9.1 "
                  "vc1009011 sha256 dbf937ebbe7c0b3d on binary 9bdd61328d0f01d9 after F-NEW-289): "
                  "androidx.compose.ui.window DialogWrapper (Lis; extends Lpj; extends android.app.Dialog) "
                  "ctor pc=13 invoke-virtual Dialog.getWindow() \u2014 runtime class Lis; \u2014 "
                  "DialogShadow never asked (handles_class: 'AlertDialog$Builder'/AlertDialog;/Dialog;"
                  "platform names only) \u2192 bridge fallthrough \u2192 S71-ANCESTRY re-dispatch Lis; as "
                  "Landroid/content/Context; (kPlatformSuper maps Dialog->Context) \u2192 no guard answers "
                  "getWindow \u2192 STUBBED null \u2192 Lis; pc=113-115 const-string 'Dialog has no window' "
                  "+ invoke-static Lea;.r (kotlin error()) \u2192 ISE x31/run, caught by Lx30;.n catch-alls, "
                  "propagated; frame DEFAULT_BACKGROUND_ONLY 5c4a0172628849ba. AOSP android.app.Dialog "
                  "ctor: mWindow = new PhoneWindow(context) and mContext are bound BEFORE any subclass ctor "
                  "body runs \u2014 getWindow()/getContext() NEVER answer null afterwards, for ANY Dialog "
                  "receiver, renamed or not (same receiver-identity principle as S134-F134A). Ground truth "
                  "via androguard disasm of classes.dex (Lis;/Lpj;/Lea;). The Window object must also carry "
                  "its own WindowManager.LayoutParams (AOSP PhoneWindow.mWindowAttributes: getAttributes() "
                  "never null \u2014 Lis; pc 21-25 iputs LayoutParams.type through it, a null answer is an "
                  "instant NPE) and requestFeature() answers true while no content is installed.",
    "fix": "F-NEW-290 DIALOG OBJECT LAW (generic, receiver-identity keyed, no name-based dispatch): "
           "(1) bridge law (dalvik_engine.cpp after the S134-F134A Activity getWindow arm): getWindow/"
           "getContext on a receiver whose class chain reaches android.app.Dialog (is_subclass_of walk) "
           "is dispatched to the DialogShadow under the PLATFORM class name 'Landroid/app/Dialog;' \u2014 "
           "the nearest guard-visible ancestor that owns the method; (2) DialogShadow::dispatch_dialog "
           "gains getWindow (mints ONE 'Landroid/view/Window;' heap object per DialogWindow, stable for "
           "the dialog lifetime \u2014 one PhoneWindow per Dialog) and getContext (answers the ctor-bound "
           "mContext recorded at <init> arg 0); (3) companion Window attribute law (bridge, after P1.2 "
           "setFlags): Window.getAttributes answers a per-RECEIVER cached "
           "'Landroid/view/WindowManager$LayoutParams;' (window_layout_params_ map \u2014 every Window "
           "carries its OWN LayoutParams), setAttributes/setBackgroundDrawableResource/setGravity/addFlags "
           "absorb void, requestFeature answers true. No package checks, no app logic, no exception "
           "suppression, no forced rendering.",
    "evidence": "evidence/cont32/DIALOG_WINDOW_FRONTIER.md; probe fixtures/fnew290_probe (real "
                "aapt2/ECJ/D8, w4 script): Dialog-subclass ctor consuming getWindow immediately (the "
                "androidx DialogWrapper shape; probe class named to AVOID the 'Activity' substring \u2014 "
                "the first draft's MainActivity$WrapperDialog name collided with the S134 find(\"Activity\") "
                "arm and masked the null, caught and fixed before any engine build): PRE-fix DLG-WINDOW|FAIL "
                "(getWindow null \u2014 divergence isolated); POST-fix x3 SUMMARY|PASS|7 pass 0 fail "
                "(getWindow non-null, getAttributes non-null, setAttributes absorbed, requestFeature true, "
                "getContext non-null, bg/gravity/flags absorbed, getWindow identity stable). composeStopwatch "
                "post-fix x3 (binary c280b243f880e7e6): 'Dialog has no window' ISE 31->0 per run "
                "(deterministic), DialogWrapper ctor chain completes (setTitle/setCanceledOnTouchOutside/"
                "getAttributes served), frame UNCHANGED 5c4a0172628849ba \u2014 divergence honestly MOVED "
                "onward (Lh4; still ops=0; deferred faces unchanged: R350-FORNAME, S102-CLASSLOADER "
                "AndroidCompositionLocals_androidKt CNFE = FAITHFUL behavior \u2014 the class genuinely is "
                "NOT in the R8-minified APK (0 Landroidx/compose/ui/platform/* classes; the name exists only "
                "as a loadClass constant and the app's own catch handles it), DataStore ENOENT with a "
                "mangled path worth a future look, STR-BRIDGE SIOOBE at Lwv;.p pc=26); regression at "
                "c280b243f880e7e6: 24/24 anchors x3 BYTE-IDENTICAL (dooz/microtimer/unote/gmdice/opencalc/"
                "tttdeluxe/flappycow/g2048), battery fcol 140/0 f259 49/0 f259g 84/7-known f266 42/0 f268 "
                "96/0 fnew253 147/0 fnew286 10/0 fnew289 28/0 fnew252 56/0 == CONT-28..31 records EXACTLY, "
                "fnew290 56/0; simplecalc x3 7960bce447ac6d8f rc=0 FULL SUCCESS retained.",
    "registered": "2026-10-09 CONT-32"
}

r["roots"].append(entry)
r["total_roots"] = 599
r["generated"] = "CONT-32 (2026-10-09)"
sc = r.get("status_counts", {})
sc["ROOT-CAUSED-FIXED"] = sc.get("ROOT-CAUSED-FIXED", 0) + 1
r["status_counts"] = sc

with open(REG, "w") as f:
    json.dump(r, f, indent=1, ensure_ascii=False)
print("registry: 598 -> 599 (F-NEW-290 ROOT_CAUSED_FIXED), dedup OK")
