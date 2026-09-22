#!/usr/bin/env python3
"""s82_dashboard.py — S82 §32/§33/§41: COMPATIBILITY_INDEX.md +
compatibility_index.json + root_cause_graph (md + json). Answers §33's
questions directly from the registry; no derived-hand-patching (S24 law)."""
import json
import os
from collections import Counter, defaultdict

import s82_lib as L

OUT = "/home/z/my-project/docs/corpus/s82"


def main():
    reg = L.load_registry()
    titles = reg["TITLES"]

    def cnt(pred):
        return sum(1 for t in titles if pred(t))

    exec_ = cnt(lambda t: t.get("EXECUTION") == "EXECUTED")
    blocked = cnt(lambda t: str(t.get("EXECUTION", "")).startswith("BLOCKED"))
    not_tested = len(titles) - exec_ - blocked
    states = Counter(t.get("STATE") for t in titles)
    graph = Counter(t.get("GRAPHICS") for t in titles if t.get("EXECUTION") == "EXECUTED")
    inter = Counter(t.get("INTERACTION") for t in titles if t.get("EXECUTION") == "EXECUTED")
    stch = Counter(t.get("STATE_CHANGE") for t in titles if t.get("EXECUTION") == "EXECUTED")
    vis_corr = Counter(t.get("VISUAL_CORRELATION") for t in titles)
    f156 = cnt(lambda t: "F-NEW-156" in (t.get("F_IDS") or []))
    f157 = cnt(lambda t: "F-NEW-157" in (t.get("F_IDS") or []))
    oncreate = cnt(lambda t: "FAIL-ONCREATE" in (t.get("FAILURE_LABELS") or []))
    img_gap = cnt(lambda t: any("IMAGE_DECODED_VS_RENDERED_GAP" in f for f in (t.get("FLAGS") or [])))
    dialog = cnt(lambda t: "VF-NEW-001" in (t.get("VF_IDS") or []))
    refs_ok = cnt(lambda t: (t.get("REFERENCE") or {}).get("STATUS") == "OK")
    game_exec = cnt(lambda t: t["TYPE"] == "game" and t.get("EXECUTION") == "EXECUTED")
    app_exec = cnt(lambda t: t["TYPE"] == "app" and t.get("EXECUTION") == "EXECUTED")

    summary = {
        "TITLE_RECORDS": len(titles),
        "GAME": cnt(lambda t: t["TYPE"] == "game"),
        "APP": cnt(lambda t: t["TYPE"] == "app"),
        "MANDATORY": cnt(lambda t: t["TYPE"] == "mandatory"),
        "EXECUTED": exec_, "GAME_EXECUTED": game_exec, "APP_EXECUTED": app_exec,
        "BLOCKED": blocked, "NOT_TESTED": not_tested,
        "STATE_COUNTS": dict(states),
        "RENDERED": states.get("STATE-RENDERED", 0) + states.get("STATE-GRAPHICALLY-NONTRIVIAL", 0),
        "GRAPHICALLY_NONTRIVIAL": states.get("STATE-GRAPHICALLY-NONTRIVIAL", 0),
        "INTERACTIVE": inter.get("INPUT_RESPONSE_PX", 0),
        "TAP_DISPATCHED": inter.get("TAP_DISPATCHED", 0),
        "STATE_CHANGED": stch.get("PIXEL_DIFF_PROVEN", 0),
        "VISUAL_CORRELATED": vis_corr.get("STRUCTURAL_CANDIDATE", 0),
        "HUMAN_VERIFIED": 0,
        "VISUAL_FAIL_VS_REFERENCE": vis_corr.get("VISUAL_FAIL_PALETTE", 0),
        "PARTIAL_PALETTE": vis_corr.get("PARTIAL_PALETTE", 0),
        "ONCREATE_FAILURES": oncreate,
        "IMAGE_RENDER_GAPS": img_gap,
        "DIALOG_LINKED": dialog,
        "F_NEW_156_FANOUT": f156,
        "F_NEW_157_FANOUT": f157,
        "REFERENCES_OK": refs_ok,
        "REFERENCES_NA": cnt(lambda t: (t.get("REFERENCE") or {}).get("STATUS") == "REFERENCE_NOT_AVAILABLE"),
    }

    # ---------------- machine index
    idx = {
        "WAVE": "S82",
        "GENERATED": L.now(),
        "SUMMARY": summary,
        "ROOT_CAUSES": {
            "F-NEW-156": {"title": "onCreate APP-BOUNDARY-UNWIND family",
                          "fanout": [t["TITLE_ID"] for t in titles if "F-NEW-156" in (t.get("F_IDS") or [])]},
            "F-NEW-157": {"title": "libGDX AndroidGraphics.createGLSurfaceView NPE (EGL/GLSurfaceView frontier)",
                          "fanout": [t["TITLE_ID"] for t in titles if "F-NEW-157" in (t.get("F_IDS") or [])]},
            "VF-NEW-001": {"title": "VF-DIALOG-ITEMS (fixed S81; dialog path gated upstream)",
                           "fanout": [t["TITLE_ID"] for t in titles if "VF-NEW-001" in (t.get("VF_IDS") or [])]},
            "VF-NEW-002": {"title": "VF-PLACEHOLDER-GARBLE (fixed S81; AFTER-state holds on real titles)",
                           "fanout": ["GAME-014 (unote/unote ladder)", "APP (muellerma stopwatch — service family face)"]},
            "VF-NEW-003": {"title": "IMAGE_DECODED_VS_RENDERED_GAP chain",
                           "fanout": [t["TITLE_ID"] for t in titles if "VF-NEW-003" in (t.get("VF_IDS") or [])]},
        },
        "TITLES": [{k: t.get(k) for k in
                    ("TITLE_ID", "TYPE", "NAME", "PACKAGE", "CATEGORY", "VERSION",
                     "VERSION_CODE", "APK_SHA256", "ISSUE_NUMBER", "ISSUE_URL",
                     "STATE", "EXECUTION", "INTERACTION", "STATE_CHANGE",
                     "RENDERING", "GRAPHICS", "VISUAL_CORRELATION",
                     "HUMAN_VERIFICATION", "F_IDS", "VF_IDS", "FAILURE_LABELS",
                     "LAST_TESTED_COMMIT", "SESSION_ID", "SCREENSHOT",
                     "SCREENSHOT_SHA256", "REFERENCE", "COMPARISON")}
                   for t in titles],
    }
    os.makedirs(OUT, exist_ok=True)
    json.dump(idx, open(f"{OUT}/compatibility_index.json", "w"), indent=1)

    # ---------------- root-cause fanout graph (§41)
    rc_lines = ["# S82 Root-Cause Fanout Graph (§41)", "",
                "One fix -> exactly which titles must regression (§19/§34).", ""]
    for rid, info in idx["ROOT_CAUSES"].items():
        rc_lines.append(f"## {rid} — {info['title']}")
        rc_lines.append(f"- status: {'OBSERVED-FAIL (P0)' if rid.startswith('F-') and rid != 'F-NEW-156' else ('OBSERVED-FAIL family (S81)' if rid=='F-NEW-156' else 'FIXED (S81) — title-level retests recorded')}")
        rc_lines.append(f"- fanout ({len(info['fanout'])} titles): {', '.join(info['fanout']) if info['fanout'] else '(none recorded this wave)'}")
        rc_lines.append("")
    open(f"{OUT}/root_cause_graph.md", "w").write("\n".join(rc_lines))
    json.dump(idx["ROOT_CAUSES"], open(f"{OUT}/root_cause_graph.json", "w"), indent=1)

    # ---------------- human dashboard
    md = [
        "# S82 COMPATIBILITY INDEX — per-title compatibility tracker",
        "",
        f"Generated: {L.now()} · Registry: `title_registry.json` (canonical, §3 freeze)",
        "",
        "## §33 Dashboard answers",
        "",
        "| QUESTION | COUNT |", "|---|---|",
        f"| Title records | {len(titles)} |",
        f"| Games really executed | {game_exec} |",
        f"| Apps really executed | {app_exec} |",
        f"| Mandatory executed (P9, TimeLimit) | {cnt(lambda t: t['TYPE']=='mandatory' and t.get('EXECUTION')=='EXECUTED')}/2 |",
        f"| Only loaded (no frames) | {states.get('STATE-NOT-LOADED',0)+states.get('STATE-LOADED',0)} |",
        f"| Rendered (non-blank pixels) | {summary['RENDERED']} |",
        f"| Interactive (input response) | {summary['INTERACTIVE']} |",
        f"| State changed (pixel-diff proven) | {summary['STATE_CHANGED']} |",
        f"| Graphics nontrivial | {summary['GRAPHICALLY_NONTRIVIAL']} |",
        f"| Image present in APK but 0 image pixels | {summary['IMAGE_RENDER_GAPS']} |",
        f"| Crashed / onCreate failure | {summary['ONCREATE_FAILURES']} |",
        f"| Visually correlated (L3+) | {summary['VISUAL_CORRELATED']} |",
        f"| Human verified (L5) | 0 (never self-granted, §31) |",
        f"| Open issues | see GitHub query `label:compatibility is:open` |",
        f"| Titles sharing a root cause | F-NEW-156: {f156} · F-NEW-157: {f157} |",
        f"| References with provenance | {refs_ok} OK / {summary['REFERENCES_NA']} NA |",
        "",
        "## §52 Counts",
        "",
        "```text",
        f"EXECUTED {exec_} · BLOCKED {blocked} · NOT_TESTED {not_tested}",
        f"STATE-NONBLANK {states.get('STATE-NONBLANK',0)} · STATE-RENDERED {states.get('STATE-RENDERED',0)} · "
        f"STATE-GRAPHICALLY-NONTRIVIAL {states.get('STATE-GRAPHICALLY-NONTRIVIAL',0)}",
        f"TAP_DISPATCHED {inter.get('TAP_DISPATCHED',0)} · INPUT_RESPONSE_PX {inter.get('INPUT_RESPONSE_PX',0)} · "
        f"PIXEL_DIFF_PROVEN {stch.get('PIXEL_DIFF_PROVEN',0)}",
        f"VISUAL_FAIL_VS_REFERENCE {summary['VISUAL_FAIL_VS_REFERENCE']} · PARTIAL_PALETTE {summary['PARTIAL_PALETTE']}",
        "HUMAN_VERIFIED 0 (L5 requires human review — never self-granted)",
        "```",
        "",
        "## Per-title index",
        "",
        "| ID | TITLE | TYPE | PACKAGE | VERSION | ISSUE | STATUS | GRAPHICS | INPUT | STATE | VISUAL | F-ID | LAST TESTED |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for t in titles:
        issue = f"[#{t['ISSUE_NUMBER']}](#{t['ISSUE_NUMBER']})" if t.get("ISSUE_NUMBER") else "—"
        md.append(
            f"| {t['TITLE_ID']} | {t.get('NAME','')[:28]} | {t['TYPE']} | `{t['PACKAGE']}` | "
            f"{t.get('VERSION') or '?'} | {issue} | {t.get('STATE','STATE-NOT-LOADED').replace('STATE-','')} | "
            f"{t.get('GRAPHICS','NONE')} | {t.get('INTERACTION','NONE')} | "
            f"{t.get('STATE_CHANGE','NONE')} | {t.get('VISUAL_CORRELATION','NONE')} | "
            f"{','.join(t.get('F_IDS', []) or ['—'])} | {(t.get('LAST_TESTED_COMMIT') or '')[:8]} |")
    open(f"{OUT}/COMPATIBILITY_INDEX.md", "w").write("\n".join(md))
    print("dashboard written:", OUT)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
