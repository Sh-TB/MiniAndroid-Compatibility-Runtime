#!/usr/bin/env python3
"""s76_registry_update.py — S76 WAVE registry + doc updates.

Evidence-locked updates (append-only evidence, no invented semantics):
1. F-146: OPEN -> ROOT-CAUSED-FIXED (R-NEW-390 getAbsoluteFile + R-NEW-391
   getCanonicalFile/Path; chain moved to Llt0;.w pc=808 = new F-152).
2. F-147: append S76 note (F-146 fix landed; F-147 boundary unchanged).
3. NEW R-NEW-390..394 + F-152 + F-153 registrations with file:line law
   citations and per-app runtime proof.
4. summary.last_updated -> S76.
Statuses use the registry's own vocabulary; evidence appended, never
rewritten.
"""
import json
from datetime import datetime, timezone

ROOT = "/home/z/my-project"
P = f"{ROOT}/root_registry.json"

d = json.load(open(P))

F146_EVIDENCE = (
    " | S76 UPSTREAM PRODUCER TRACE + FIX: traced the pc=569 receiver v4 "
    "def-chain in Lg8;.a (DataStore file-name lambda; scripts/"
    "s76_g8_disasm.py full disasm): pc=565 File.getAbsoluteFile -> "
    "pc=568 move-result-object v4 -> pc=569 Object.getClass on v4. ROOT: "
    "java.io.File.getAbsoluteFile() had NO implementation (R-NEW-347 "
    "covered only the String variant getAbsolutePath) -> null receiver. "
    "FIX R-NEW-390 (File-returning sibling, OpenJDK File.java "
    "'new File(fs.resolve(f.getPath()))' never-null law) + R-NEW-391 "
    "(getCanonicalFile/getCanonicalPath for the DataStore singleton guard "
    "at Lot;.a pc=37, canonical==absolute in the sandbox). PROOF: "
    "[R347-FILE] getAbsoluteFile path=\"...settings.preferences_pb\" -> "
    "File o894; the g8.a pc=569 escape is GONE; the dooz chain moved "
    "DEEPER: DataStore multi-instance guard passes, protobuf schema init "
    "runs, new first divergence Llt0;.w pc=808 (registered F-152). "
    "Evidence: docs/evidence/s76/dooz_f146_upstream/.")
F147_EVIDENCE = (
    " | S76: F-146 fix landed (see F-146 entry); the onCreate pc=228 "
    "boundary escape (p0 NULL, secondary to the F-146 coroutine unwind) "
    "re-observed after the fix — the composition no longer dies at g8.a "
    "pc=569 but the boundary escape persists downstream of F-152.")

R390 = {
    "id": "R-NEW-390",
    "status": "ROOT-CAUSED-FIXED",
    "evidence": (
        "java.io.File.getAbsoluteFile() law (S76). Oracle: OpenJDK "
        "java/io/File.java getAbsoluteFile() = new File(fs.resolve("
        "getPath())) — NEVER null; the File-returning sibling of "
        "getAbsolutePath (R-NEW-347, S42). Implementation: dalvik_engine.cpp "
        "R-NEW-347 block extended (getAbsoluteFile branch: fresh File heap "
        "object, 'path' field = absolute path, same app-data-root "
        "resolution). Real demand: dooz_23 F-146 — the DataStore file-name "
        "lambda Lg8;.a calls getAbsoluteFile then getClass on the result "
        "(pc=565/568/569); unimplemented -> null -> the F-146 NPE escape "
        "that killed the composition. Proof: [R347-FILE] getAbsoluteFile "
        "-> File o894 in docs/evidence/s76/dooz_f146_upstream/; battery "
        "26/26 rc=0; verifier 24/24; Level C fidelity byte-identical 90/90.")
}
R391 = {
    "id": "R-NEW-391",
    "status": "ROOT-CAUSED-FIXED",
    "evidence": (
        "java.io.File.getCanonicalFile()/getCanonicalPath() law (S76). "
        "Oracle: OpenJDK File.java — canonical = absolute + symlink/'.'/'..'"
        " resolution, never null; in the runtime's app-data sandbox "
        "(no symlinks, path::lexically-normal) canonical == absolute "
        "(documented equivalence, not a filesystem walk). Implementation: "
        "dalvik_engine.cpp R-NEW-347 block (File-returning + String "
        "branches). Real demand: dooz_23 DataStore multi-instance guard "
        "Liu;->e Le40; calls g8.a (file lambda) then getCanonicalFile "
        "(Lot;.a pc=30) then getAbsolutePath (pc=37) — unimplemented "
        "canonical File -> null -> guard NPE -> catch-all retry -> "
        "F084-bounded Lsr.run spin. Proof: [R347-FILE] getCanonicalFile -> "
        "File o895/o897; guard passes; protobuf schema init runs; "
        "dooz/evidence/s76/dooz_f146_upstream/.")
}
R392 = {
    "id": "R-NEW-392",
    "status": "ROOT-CAUSED-FIXED",
    "evidence": (
        "TextView SUBSUMPTION law (S76). Oracle: AOSP Button extends "
        "TextView; getText()/length() are inherited, not overridden — any "
        "TextView-subclass receiver must dispatch to the TextView law. "
        "Implementation: dalvik_engine.cpp getText/length intercepts "
        "(try_recursive_invoke + bridge_to_api) now walk the DEX "
        "superclass chain via is_subclass_of(class, Landroid/widget/"
        "TextView;) (EXP-068 map) instead of substring-matching class "
        "names. Real demand: gmdice_8 GameMasterDice.onClick calls "
        "Button.getText() ('3D20') then CharSequence.toString — "
        "REC-MISS null -> toString NPE -> event loop died on the FIRST "
        "click (the S75 'listener fires but roll never draws' lead). "
        "Proof: docs/evidence/s76/gmdice_roll_visible/ — clicks dispatch, "
        "DSADiceSet.roll runs (Random.nextInt x3 + StringBuilder), frames "
        "CHANGE (diff_px 1,511,441 first click; roll results '6' then "
        "'5' visible).")
}
R393 = {
    "id": "R-NEW-393",
    "status": "ROOT-CAUSED-FIXED",
    "evidence": (
        "View.getBackground() themed-widget non-null law + "
        "Drawable.setColorFilter(int, PorterDuff$Mode) (S76). Oracle: "
        "AOSP View.java — framework widgets (Button/TextView/EditText/"
        "ImageView family) always resolve a background from the theme "
        "(Widget.* styles); getBackground() on that family NEVER returns "
        "null; Drawable.setColorFilter mutates the drawable paint, never "
        "throws on a tracked drawable. Implementation: android_shadows.cpp "
        "ViewShadow dispatch (getBackground -> fresh Drawable heap object; "
        "bare Views stay null unless bg_color/state-list registered; "
        "setTransformationMethod acknowledged void) + dalvik_engine.cpp "
        "bridge_to_api setColorFilter (tint_color recorded on the drawable "
        "object; framebuffer tint application NOT claimed — honest scope). "
        "Real demand: gmdice onCreate loop buttons[i].getBackground()."
        "setColorFilter(color, MULTIPLY) — getBackground REC-MISS null -> "
        "setColorFilter NPE killed onCreate at the FIRST iteration -> "
        "button_more/resultview never assigned -> roll result TextView "
        "null (roll() pc=13 setText NPE). Proof: [R393-BG] getBackground "
        "-> Drawable o46/o49/o50/o51 + [R393-TINT]; onCreate completes "
        "(5/5 buttons clickable vs 1/5 before); gmdice roll renders.")
}
R394 = {
    "id": "R-NEW-394",
    "status": "ROOT-CAUSED-FIXED",
    "evidence": (
        "Dialog decor LAYOUT + topmost-window TOUCH law (S76). Oracle: "
        "AOSP — a dialog's decor is measured/laid out in its OWN window; "
        "WindowManager routes touches to the TOPMOST window whose frame "
        "contains the point (dialogs sit above the activity window). "
        "Implementation: dialog_shadow.cpp/h — DialogWindow records decor "
        "node ids (title/message/items/row/buttons) at build time; "
        "layout_decor_nodes() assigns REAL bounds mirroring the painter "
        "geometry (pad=24, button row at b-112, thirds split over "
        "non-empty labels in neutral/negative/positive order) at show() "
        "and each paint; decor_root_at(x,y) returns the topmost showing "
        "dialog root covering the point; execution_engine.cpp F117 tap "
        "site routes the dispatch root to the dialog decor when covered "
        "([R394-TAP]). Real demand: snake game-over restart is "
        "Dialog-based (showMessageDialog -> AlertDialog 'Game Over!' -> "
        "positive button '重新开始' -> SnakePanelView$1$1.onClick -> "
        "reStartGame, static DEX proof) — S73/S75 START@99 tapped the "
        "WRONG window (dialog WAS rendered but tap-dead: target=0). "
        "Proof: docs/evidence/s76/snake_dialog_restart/ — tap (758,1022)"
        "@99 after game-over at frame 94 -> RESTART OBSERVED at frame 99 "
        "(snake back at the initial row, fresh game runs to frame 115+, "
        "wall wrap + 2 captures).")
}
F150 = {
    "id": "F-152",
    "status": "OPEN",
    "evidence": (
        "dooz NEW first divergence after R-NEW-390/391 (S76). Site: "
        "Llt0;.w pc=808 — null receiver (recv t8/o0) — the compose/protobuf "
        "chain now reaches Llt0;.w (the S43-wave disasm subject, 1009 "
        "units). Previously masked BY F-146: the coroutine unwind killed "
        "the composition before this code ever ran. Evidence: docs/"
        "evidence/s76/dooz_f146_upstream/ engine log (F141-DIAG Llt0;.w "
        "pc=808); visual state unchanged (nonwhite 23,472 — engine-default "
        "face). Honest frontier: producer trace of the Llt0;.w receiver is "
        "the NEXT dooz lead.")
}
F151 = {
    "id": "F-153",
    "status": "OPEN",
    "evidence": (
        "Dialog button CJK label paint gap (S76, residual of R-NEW-394). "
        "The DialogShadow painter constructs a bare BitmapFont (ASCII "
        "glyph set); the snake game-over dialog labels 重新开始/退出 paint 0 "
        "pixels (blue 0x0062CC label color absent from the dialog frame — "
        "pixel-scanned), while the ASCII message 'Game Over!' paints "
        "(grey 33,33,33 measured). The dialog buttons are clickable and "
        "the restart works (input path proven); only the label GLYPHS are "
        "invisible. Fix belongs to the font/CJK family (route the painter "
        "through the project CJK-capable shaper/font, cf. f05_persian). "
        "Evidence: docs/evidence/s76/snake_dialog_restart/ report.json "
        "'positive_label_paint'.")
}

updates = {"F-146": F146_EVIDENCE, "F-147": F147_EVIDENCE}
statuses = {"F-146": "ROOT-CAUSED-FIXED"}
new_roots = [R390, R391, R392, R393, R394, F150, F151]

found = set()
for r in d.get("roots", []):
    rid = str(r.get("id"))
    if rid in updates:
        if rid in statuses:
            r["status"] = statuses[rid]
        r["evidence"] = r.get("evidence", "") + updates[rid]
        found.add(rid)

missing = (set(updates) - found)
assert not missing, f"missing roots: {missing}"

existing_ids = {str(r.get("id")) for r in d["roots"]}
for nr in new_roots:
    assert nr["id"] not in existing_ids, f"id collision: {nr['id']}"
    d["roots"].append(nr)

d.setdefault("summary", {})["last_updated"] = \
    f"S76 {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
d["summary"]["total_roots"] = len(d["roots"])

with open(P, "w") as f:
    json.dump(d, f, indent=1, ensure_ascii=False)
print(f"registry updated: F-146 -> ROOT-CAUSED-FIXED; +{len(new_roots)} "
      f"new roots (R-NEW-390..394, F-152, F-153); total={len(d['roots'])}")
