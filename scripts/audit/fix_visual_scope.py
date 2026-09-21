#!/usr/bin/env python3
# S74-FINAL §13/§15/§31: scope-truthify tictactoe + connectfour visual evidence
# tictactoe: real-APK frames are uniform white -> downgrade to NOT_HUMAN_VISIBLE,
#            golden fixture X-WINS proof kept SEPARATE (§15).
# connectfour: frames are GOLDEN_FIXTURE scope -> add explicit scope marker (no conflation).
import json

P1 = "/home/z/my-project/docs/compatibility/apps/tictactoe.json"
P2 = "/home/z/my-project/docs/compatibility/apps/connectfour.json"

d = json.load(open(P1))
ve = d["visual_evidence"]
model = ve.get("model", "")
ve["status"] = "NOT_HUMAN_VISIBLE"
ve["evidence_scope"] = "REAL_APK (docs/evidence/s74_ops/tictactoe/) — frames verified S74-FINAL: uniform white 1080x1920 extrema(255,255)"
ve["note"] = ("REAL APK at HEAD: representative frames 01_launch/03_final are uniform WHITE = NO_MEANINGFUL_VISUAL_PROOF "
              "(kept as truthful blocker evidence; GL blocker F-144). Downgraded from HUMAN_VISIBLE by S74-FINAL §13/§31 "
              "independent frame verification (blank claim check). Golden-fixture X-WINS proof kept SEPARATE per §15.")
ve["frames_verified"] = {"01_launch.png": "UNIFORM white (blank)", "03_final.png": "UNIFORM white (blank)"}
ve["golden_fixture_evidence"] = {
    "status": "HUMAN_VISIBLE",
    "evidence_scope": "GOLDEN_FIXTURE (com.miniandroid.tictactoegolden, sha 9d1c2954c675813c) — NOT the real APK",
    "bundle": "docs/evidence/s74_ops/tictactoe_golden_fixture/",
    "frames": ["01_launch.png", "02_first_move.png", "03_x_wins.png"],
    "note": "X WINS board human-visible at fixture scope (extrema 33-255, nontrivial); F-144 GL limitation remains the real-APK blocker"
}
ve["model"] = model
json.dump(d, open(P1, "w"), indent=1)
print("tictactoe.json -> NOT_HUMAN_VISIBLE (real APK) + separate golden block")

d = json.load(open(P2))
ve = d["visual_evidence"]
ve["evidence_scope"] = ("GOLDEN_FIXTURE (connectfour_golden.apk built at HEAD by validate_connectfour_golden.sh) — "
                        "frames are NOT from the real APK; real-APK execution proven in S73 (issue #12, Y WINS at click 22)")
ve["note"] = ("launch 'R to move' -> midgame -> 'Y WINS' full board; validator ALL PASS at HEAD. "
              "S74-FINAL §13/§15: scope marked GOLDEN_FIXTURE to prevent real-APK conflation; frames verified nontrivial (extrema 33-255).")
json.dump(d, open(P2, "w"), indent=1)
print("connectfour.json -> HUMAN_VISIBLE scope-qualified GOLDEN_FIXTURE")
