#!/usr/bin/env python3
# S56 registry update 2: R-NEW-368 verdict — premise refuted by a
# coordinate-correct tap; uNote main-menu input chain proven at L6.
import json

REG = 'root_registry.json'
reg = json.load(open(REG))

for r in reg['roots']:
    if r.get('id') == 'R-NEW-368':
        r['status'] = 'VERIFIED-FIXED'
        r['fixed'] = 'S56 (premise refuted — no engine defect)'
        r['title'] = (
            "uNote main-menu buttons unreachable for input — REFUTED at S56: "
            "the 16-probe grid (y 300..1780) never covered the bottom 44px "
            "button band (y=1876..1920); a tap at the real coordinates hits, "
            "consumes, and launches NoteEdition"
        )
        r['summary'] = (
            "S56 re-probe: EXP092-RENDER places Add note/Search/Quit at "
            "y=1876..1920 (nodes 13/14/15, 360x44 each). Canonical tap "
            "pipeline at (270,1898): G06-TAP DOWN target=13 consumed=1, UP "
            "click_posted=1 -> app's own addNote ran -> startActivity -> "
            "NoteEdition.onCreate dispatched (its PreferenceManager/"
            "getApplicationContext calls logged). Paint rect == touch rect; "
            "the old no-engine-fix-needed verdict stands: no geometry law "
            "was broken, the probe grid predates the current layout."
        )
        r['evidence'] = {
            'doc': 'docs/evidence/s56_unote/RNEW368_EVIDENCE.md',
            'tap': 'G06-TAP DOWN (270,1898) target=13 consumed=1; UP click_posted=1',
            'navigation': 'startActivity -> Lapp/varlorg/unote/NoteEdition;',
            'head': 'S56 working tree (F-084 + F-085), battery ALL PASS 96/96',
        }
        r['next'] = (
            "uNote ladder continues at NoteEdition: PreferenceManager."
            "getDefaultSharedPreferences + Activity.getApplicationContext "
            "REC-MISS surface (new, minor); notes.db persistence ladder "
            "unchanged as the L10 target."
        )
        break
else:
    raise SystemExit('R-NEW-368 not found')

json.dump(reg, open(REG, 'w'), indent=1, ensure_ascii=False)
print('R-NEW-368 -> VERIFIED-FIXED')
