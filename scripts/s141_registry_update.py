#!/usr/bin/env python3
"""s141_registry_update.py — S141 wave registry refresh (TRAINS 49-50).

Adds the two runtime-built titles with fresh S141 evidence:
  - com.miniandroid.snakeneon (Snake Neon): built from repo source this wave
    (zip sha16 6a8af7115b63f45b), 190-frame interactive run, 6 real taps,
    direction changes + wrap-around law proven via teal-centroid trajectory.
  - com.miniandroid.gmem (Memory Match): win REPRODUCED on the fresh binary
    (matched-green 0 -> 331,820 @f40 -> 884,388 px @f95 = all 16 matched).
Honest fields only; levels stay conservative (L2 render territory).
"""
import json

REG = 'docs/evidence/canonical/registry.json'
reg = json.load(open(REG))
ts = reg['titles']
by_pkg = {t['package']: t for t in ts}

SNAKE = {
    "apk_sha256": "",
    "artifact": "",
    "artifact_kind": "",
    "artifact_sha256": "",
    "first_divergence": "none recorded in S141 session",
    "interacted": True,
    "last_success_stage": "build + 190-frame interactive run (S141)",
    "launched": True,
    "level": 2,
    "level_name": "L2_GRAPHICALLY_INCOMPLETE",
    "notes": ("S141 TRAIN-43/45: built fresh from repo source games/snake-neon "
              "(canonical aapt2/ECJ/D8 pipeline, zip sha16 6a8af7115b63f45b; "
              "S98 APK b36885c181a323ab = prior art, method surface identical, "
              "repo HEAD authoritative). 190-frame run @110ms virtual, 6 REAL "
              "taps through the TouchDispatcher law pipeline onto the live "
              "button bounds (LEFT(154,1831) UP(411,1831) DOWN(668,1831) "
              "RIGHT(925,1831)); teal-centroid trajectory proves direction "
              "changes RIGHT->DOWN->LEFT->RIGHT->DOWN and the WRAP-AROUND law "
              "(y 1070->202 bottom->top portal) — the Neon mechanic distinct "
              "from Snake Deluxe (walls kill)"),
    "package": "com.miniandroid.snakeneon",
    "proven": "LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED",
    "remaining": "obstacle-block mechanic exercise (3rd food spawns block), "
                 "deterministic full-win plan, graphics completeness beyond L3",
    "rendered": True,
    "root_cause": "S141: static-state law + Handler postDelayed self-reposting "
                  "tick chain both live (Runnable id=34 fired every 220ms "
                  "virtual for 190 frames; diff_px=9408 per move)",
    "session": "S141",
    "source": "in-house (games/snake-neon)",
    "state_changed": True,
    "status": "candidate_INTERACTION_VERIFIED",
    "title": "Snake Neon",
    "type": "game",
    "upstream": "in-house (games/snake-neon)",
    "version": "1.0 (vc1)",
}

GMEM = {
    "apk_sha256": "",
    "artifact": "",
    "artifact_kind": "",
    "artifact_sha256": "",
    "first_divergence": "none recorded in S141 session",
    "interacted": True,
    "last_success_stage": "win reproduced on fresh binary (S141)",
    "launched": True,
    "level": 2,
    "level_name": "L2_GRAPHICALLY_INCOMPLETE",
    "notes": ("S141 TRAIN-46: deterministic win plan (scripts/s138_mem_winplan.py, "
              "44 REAL taps) re-executed on the S141 binary 0cf810383af94146 + "
              "freshly rebuilt APK (zip sha16 8c3861245fc70f74 — zip wrapper "
              "timestamp nondeterminism, engine face deterministic): "
              "matched-green px 0 @f2 -> 331,820 @f40 -> 884,388 @f95 = ALL 16 "
              "CARDS MATCHED / YOU WIN face reproduced (S138 origin 511a8e471f9c7a5f)"),
    "package": "com.miniandroid.gmem",
    "proven": "LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED",
    "remaining": "GIF artifact + graphics completeness beyond L3",
    "rendered": True,
    "root_cause": "S138 built+won; S141 re-proven zero-drift on the fresh binary",
    "session": "S138/S141",
    "source": "in-house (upload/s80_games/gmem)",
    "state_changed": True,
    "status": "candidate_INTERACTION_VERIFIED",
    "title": "Memory Match",
    "type": "game",
    "upstream": "in-house (upload/s80_games/gmem)",
    "version": "1.0 (vc1)",
}

changed = []
for entry in (SNAKE, GMEM):
    pkg = entry['package']
    if pkg in by_pkg:
        by_pkg[pkg].update(entry)
        changed.append(pkg + ' (updated)')
    else:
        ts.append(entry)
        by_pkg[pkg] = entry
        changed.append(pkg + ' (added)')

reg['count'] = len(ts)
reg['wave'] = reg.get('wave', '') + ' +S141' if isinstance(reg.get('wave'), str) else 'S141'
json.dump(reg, open(REG, 'w'), indent=1, ensure_ascii=False)
print('registry entries now:', len(ts))
for c in changed:
    print(' ', c)
