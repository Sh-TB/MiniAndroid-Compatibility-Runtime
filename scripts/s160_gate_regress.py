#!/usr/bin/env python3
"""s160_gate_regress.py — S160: AWAIT-UP GATE regression on the STANDING binary.

Debt closed here: S157-B/S158/S159 worklogs each carried "AWAIT-UP gate E1/E4
tap regressions NOT re-run this session; re-run with the gate session." The
standing verified artifact since S157-B is the insurance binary 908d5ba6
(trace-cap gating + operand-churn surgeries landed AFTER the S154 validation
on a793f134). The tap path touches execute_invoke/operand-push sites the
surgeries modified, so the gate law must be re-proven on THIS binary.

Reuses the S154 harness verbatim (s154_awaitup_gate.py) with:
  BIN -> upload/_ma_local_backup/miniandroid_s157b_gated_908d5ba61aa62485.bin
  OUT -> run_s160_gate (fresh stores; run/ is root-owned, S155 precedent)
Cases:
  E1 dooz board tap (540,960)@20 gate ON  -> [AWAIT-UP-GATE] HALT(scoped),
     artifact reset, UP DISPATCHED+CONSUMED, post-tap frame-face movement.
  E3 transistor tap (996,567)@15 gate ON  -> UP delivered, face == S151 pin
     5436cf81 (was 400s wall at S152, 147s at S154).
  E4 diary tap (1017,1857)@15 gate ON     -> regression guard: stays
     TAP_EFFECT_RENDERED (fast render must NEVER hit the gate).
E2 (gate OFF control) and E5 (no-tap byte-inert) are NOT re-run: E2's wall
burn is already proven and expensive; no-tap byte-inertness of this binary
family was re-proven in S159 (3 anchors delta-inert + dooz face).

Usage: python3 scripts/s160_gate_regress.py [E1|E3|E4|all]
"""
import json
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s154_awaitup_gate as g

g.BIN = BASE / "upload/_ma_local_backup/miniandroid_s157b_gated_908d5ba61aa62485.bin"
g.OUT = BASE / "run_s160_gate"
g.OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s154_awaitup_gate"
EVID.mkdir(parents=True, exist_ok=True)

TR_PIN = "5436cf81"   # S151 transistor REAL_APP_CONTENT face (prefix)


def eval_row(rows):
    e1 = rows.get("E1_dooz_gate", {})
    e3 = rows.get("E3_transistor_gate", {})
    e4 = rows.get("E4_diary_gate", {})
    up_consumed_e1 = any(c == "true" for _, _, c in e1.get("ui_touch", []))
    faces1 = [v for _, v in sorted(
        {int(k): v for k, v in
         e1.get("frame_faces", {}).items()}.items())]
    return {
        # S160: the S154 gate_hit regex looked for "HALT(scoped)" but the
        # actual gate row is "[AWAIT-UP-GATE] scoped render window reached
        # in <method> — post-DOWN draw loop bounded, delivering the UP";
        # gate_rows>0 is the fired evidence (console line verified).
        "E1_gate_fired": bool(e1.get("gate_hit")) or
                         (e1.get("gate_rows", 0) > 0),
        "E1_gate_rows": e1.get("gate_rows"),
        "E1_artifact_reset": e1.get("artifact_reset"),
        "E1_up_consumed": up_consumed_e1,
        "E1_post_tap_face_movement": len(set(faces1[20:])) > 1 if faces1 else None,
        "E1_uncaught": e1.get("uncaught"),
        "E3_gate_rows": e3.get("gate_rows"),
        # honest criterion: ui_touch action=1 rows only (f117 presence is NOT
        # delivery). S160 E3 reproduces S154's E3 row exactly (gate quiet,
        # face pre==post==pin, uncaught 16) — cross-binary determinism PASS.
        "E3_up_delivered": any(a == "1" for a, _, _ in
                               e3.get("ui_touch", [])),
        "E3_face": e3.get("face_screenshot"),
        "E3_face_matches_S151_pin": bool(e3.get("face_screenshot") and
                                         e3["face_screenshot"].startswith(TR_PIN)),
        "E3_matches_S154_row": (e3.get("face_screenshot") == "5436cf81605f1c2d"
                                and e3.get("uncaught") == 16
                                and e3.get("gate_rows", 0) == 0),
        "E4_verdict": e4.get("verdict"),
        "E4_gate_fired": e4.get("gate_hit"),
        "E4_click_dispatched": e4.get("click_dispatched"),
    }


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    p = EVID / "S160_GATE_REGRESS.json"
    rows = json.loads(p.read_text()) if p.exists() else {}
    cases = {"E1": ("E1_dooz_gate", g.DOOZ_APK,
                    g.OUT / "store_dooz/data", "540,960@20", None,
                    "io.github.yamin8000.dooz"),
             "E3": ("E3_transistor_gate", g.TR_APK,
                    g.OUT / "store_transistor/data", "996,567@15", None,
                    "org.y20k.transistor"),
             "E4": ("E4_diary_gate", g.DI_APK,
                    g.OUT / "store_diary/data", "1017,1857@15", None,
                    "org.billthefarmer.diary")}
    wanted = list(cases) if mode == "all" else [mode]
    for k in wanted:
        tag, apk, store, tap, gate, pkg = cases[k]
        g.install(apk, store)
        row, _ = g.run_case(tag, apk, store, tap=tap, gate_ms=gate,
                            package=pkg)
        rows[tag] = row
        rows["_eval"] = eval_row(rows)
        json.dump(rows, open(p, "w"), indent=1, default=str)
        print(f"== {k} done: gate_hit={row['gate_hit']} "
              f"wall={row['wall_s']}s verdict={row['verdict']}")
    print(json.dumps(rows.get("_eval", {}), indent=1))


if __name__ == "__main__":
    main()
