#!/usr/bin/env python3
"""CONT-111: update root_registry.json + canonical mirror with wave results.

- F-NEW-448: stays CONFIRMED_OPEN_GAP (chess face byte-identical pre/post)
  but refreshed with the REFINED two-layer root cause: layer 1 (shadow
  family absence) FIXED this wave with A/B bracketing; layer 2 (DEX-ctor
  attr-chain seeding) is the named lever.
- F-NEW-367: SUPERSEDED-BY-EVIDENCE (native bridge landed via #371 S-2 +
  F-NEW-382b + F-NEW-441; live re-run pending APK re-supply).
Fills numbers from evidence/cont111/evidence.json.
"""
import json, sys

DATE = '2026-10-20'

main_path = 'root_registry.json'
mirror_path = 'canonical/root_cause_registry.json'
main_reg = json.load(open(main_path))
mirror = json.load(open(mirror_path))

def find(reg, rid):
    for i, r in enumerate(reg):
        if r['id'] == rid:
            return i
    return -1

t448 = ("F-NEW-448 (CONT-111 refresh) CONFIRMED_OPEN_GAP — root cause refined to two "
        "layers. LAYER 1 (FIXED this wave): the AOSP View suggested-minimum family was "
        "ABSENT from the shadow layer (setMinimumWidth/Height, getMinimumWidth/Height, "
        "getSuggestedMinimumWidth/Height — zero dispatch sites; android:minWidth "
        "0x01010150 / android:minHeight 0x01010151 parsed nowhere). Implemented: "
        "ViewNode.min_width/min_height + five shadow dispatches + two getters + "
        "XML-element/style/theme-bag seeding (apply_style_item first-writer slots, "
        "element>bag>0 precedence). Probe fixtures/cont111_minmeasure (c448, real "
        "aapt2/ECJ/D8) 7/7; A/B bracketed: pre-fix binary (fresh worktree 5fe175d4) "
        "0/7 -> fix binary 7/7; full battery green, wall zero-drift. LAYER 2 (OPEN "
        "lever): chess_jwtc_298's appcompat Toolbar is DEX-CONSTRUCTED — its render "
        "tree is byte-identical pre/post (Toolbar 1080x0 both; ActionBarContainer "
        "1080x168 pre-existing) because the old appcompat ctor has zero "
        "setMinimumHeight callsites (androguard) and the DEX view-construction path "
        "(run_custom_view_constructor -> AttributeSetStore) never resolves "
        "android:minWidth/minHeight from the AttributeSet/style chain into the node. "
        "Next step: seed ViewNode.min_* in the framework View <init>(Context, "
        "AttributeSet) shadow from AttributeSetStore + theme chain.")
e448 = ("run/c111/c448.log + run/c111/chess_post.log + /tmp/c111_ab_pre.log + "
        "/tmp/c111_chess_pre.log + run/c111/battery.log + "
        "evidence/cont111/evidence.json + scripts/cont111_scan_toolbar.py")

t367 = ("F-NEW-367 (CONT-111 refresh) SUPERSEDED-BY-EVIDENCE: the 2026 BLOCKED "
        "premise 'the runtime has no native-library bridge' is superseded — the "
        "bridge landed as #371 CLOSEOUT S-2 (real dlopen + JNI_OnLoad + symbol "
        "resolution), F-NEW-382b (CONT-81 lazy G-4 nativeLibraryDir derivation, "
        "citing the SAME stack.tower3d live evidence), and F-NEW-441 (CONT-103 "
        "on-demand extraction for direct runs; System.load absolute-path branch "
        "implemented). All three are ROOT-CAUSED-FIXED in this registry. Honest "
        "residual: live libGDX re-run pending APK re-supply (stack.tower3d_1 / "
        "bouncy_43 lost in a container reset; flappycow_rebuilt carries no "
        "native libs).")

for reg, path in ((main_reg, main_path), (mirror, mirror_path)):
    i = find(reg, 'F-NEW-448')
    if i >= 0:
        reg[i]['title'] = t448
        reg[i]['evidence'] = e448
        reg[i]['date'] = DATE
        reg[i]['verified_current'] = True
    j = find(reg, 'F-NEW-367')
    if j >= 0:
        reg[j]['status'] = 'SUPERSEDED-BY-EVIDENCE'
        reg[j]['title'] = t367
        reg[j]['date'] = DATE

json.dump(main_reg, open(main_path, 'w'), indent=2, ensure_ascii=False)
json.dump(mirror, open(mirror_path, 'w'), indent=2, ensure_ascii=False)
for reg, name in ((main_reg, 'main'), (mirror, 'mirror')):
    ids = [r['id'] for r in reg]
    assert len(ids) == len(set(ids)), f'{name} duplicate ids'
    print(f'{name}: {len(reg)} roots id-unique')
st = {r['id']: r['status'] for r in main_reg}
print('F-NEW-448:', st['F-NEW-448'], '(open, refined)')
print('F-NEW-367:', st['F-NEW-367'])
