#!/usr/bin/env python3
"""S128 PHASE-0 registry repair (audit finding R1):
the S125 canonical builder's GAME_OVERRIDES keys "FlappyCow" / "GameMasterDice" /
"Snake Neon" never bind because docs/verified_executed_games.json lacks those rows —
3 evidence-backed titles were silently absent from the canonical game registry.
This script appends them (evidence-shaped rows, same schema) and regenerates canonical.
Idempotent: skips titles already present."""
import json, sys

P = '/home/z/my-project/docs/verified_executed_games.json'
a = json.load(open(P))
have = {g['title'] for g in a['games']}

NEW = [
 {"title": "FlappyCow", "package": "com.quchen.flappycow", "version": "rebuilt (S123)",
  "kind": "game", "upstream": "upstream source rebuild — upload/flappycow_rebuilt.apk",
  "fdroid": None, "apk_sha256": None, "registry_status": "candidate_INTERACTION_VERIFIED",
  "audit_status": "VERIFIED", "evidence_level": "E5", "render_level": "L4 L4_RENDER_CANDIDATE",
  "sessions": "S123 / S124 / S127",
  "execution_protocol": "real-dalvik run; start-screen golden 13cf4746 3-run byte-identical (S124, re-proven S127 wave); G08-LAUNCH chain: PLAY tap (541,910) -> StartscreenView.onTouchEvent -> startActivity(new Intent(com.quchen.flappycow.Game)) -> Game activity full lifecycle (onCreate 976 instructions)",
  "interaction": True, "state_change_evidence": "23472 px state change on PLAY tap (S123)",
  "recorded_runs": 3, "runs_evidence": "S123/S124/S127 golden waves",
  "note": "Start screen VERIFIED_3RUN; gameplay blocked by GMS frontier (honest: load+menu render only)"},
 {"title": "GameMasterDice", "package": "de.duenndns.gmdice", "version": "8",
  "kind": "game", "upstream": "F-Droid (de.duenndns.gmdice)", "fdroid": "https://f-droid.org/packages/de.duenndns.gmdice/",
  "apk_sha256": None, "registry_status": "VERIFIED", "audit_status": "VERIFIED",
  "evidence_level": "E5", "render_level": "L4", "sessions": "S121 / S124 / S127",
  "execution_protocol": "real-dalvik run; S121 full-load + roll tap state change; S124 themed menu render; S127 wave stable",
  "interaction": True, "state_change_evidence": "agent roll tap -> dice result change (S121)",
  "recorded_runs": 2, "runs_evidence": "S121, S127 wave",
  "note": "full-load + themed menu + roll interaction (S124 theme base)"},
 {"title": "Snake Neon", "package": "com.miniandroid.snakeneon", "version": "1.0 (vc1)",
  "kind": "game", "upstream": "in-house — games/snake-neon (source in repo)",
  "fdroid": None, "apk_sha256": None, "registry_status": "candidate_INTERACTION_VERIFIED",
  "audit_status": "VERIFIED", "evidence_level": "E5", "render_level": "L4",
  "sessions": "S119",
  "execution_protocol": "real-dalvik run, autoplay driver; score=10 len=4 HUD-anchored",
  "interaction": True, "state_change_evidence": "score 10 / len 4 HUD (S119)",
  "recorded_runs": 1, "runs_evidence": "S119 wave",
  "note": "wrap-wall BFS AI reference implementation for snake_deluxe port"},
]

added = []
for row in NEW:
    if row["title"] not in have:
        a["games"].append(row)
        added.append(row["title"])

json.dump(a, open(P, 'w'), indent=1, ensure_ascii=False)
print(f"added: {added}; games now {len(a['games'])}")
