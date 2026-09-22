#!/usr/bin/env python3
"""s82_issue_body.py — S82 §9: build the Compatibility Report body for one
title from its registry record. This is the permanent per-title dossier format.
"""
import json

REG = "/home/z/my-project/docs/corpus/s82/title_registry.json"


def fmt_status(t):
    return (f"- State: `{t.get('STATE','STATE-NOT-LOADED')}`\n"
            f"- Execution: `{t.get('EXECUTION','NOT_TESTED')}`\n"
            f"- Interaction: `{t.get('INTERACTION','NONE')}`\n"
            f"- State change: `{t.get('STATE_CHANGE','NONE')}`\n"
            f"- Rendering: `{t.get('RENDERING','NONE')}`\n"
            f"- Graphics: `{t.get('GRAPHICS','NONE')}`\n"
            f"- Visual correlation: `{t.get('VISUAL_CORRELATION','NONE')}`\n"
            f"- Human verification: `{t.get('HUMAN_VERIFICATION','NOT_REVIEWED')}` "
            "(L5 = human review only, never self-granted §31)")


def body_for(t):
    pkg = t["PACKAGE"]
    mand_ref = ""
    if t["TYPE"] == "mandatory" and t.get("REFERENCE_SCREENSHOT_URL"):
        mand_ref = t["REFERENCE_SCREENSHOT_URL"]
    ref = t.get("REFERENCE") or {}
    vis = t.get("VISUAL") or {}
    runs = t.get("RUNS", 0)
    repro = ""
    if runs:
        repro = "\n".join(
            f"{i+1}. RUN-{i+1}: `miniandroid run --execution-mode real-dalvik "
            f"--frames 8 --frame-delay 300 <{pkg}_{t.get('VERSION_CODE','vc')}.apk>`"
            for i in range(runs))
        if t.get("TAPS_USED"):
            repro += ("\n- Interaction RUN: taps (540,960)@3 → "
                      "(540,1700)@5 → (300,1700)@6 (game) / (540,960)@3 → "
                      "(540,400)@5 (app) via canonical TouchDispatcher")
    else:
        repro = ("1. NOT TESTED THIS WAVE (§26 honest status — record exists, "
                 "execution queued for S83 batches)")

    evidence = []
    if t.get("SCREENSHOT"):
        evidence.append(f"- screenshot: `{t['SCREENSHOT']}` sha256:`{(t.get('SCREENSHOT_SHA256') or '')[:16]}…`")
    if t.get("APK_SHA256"):
        evidence.append(f"- APK sha256: `{t['APK_SHA256']}` (version {t.get('VERSION','?')} vc {t.get('VERSION_CODE','?')})")
    if t.get("BEFORE_FRAME_SHA256"):
        evidence.append(f"- before/after frames sha256: `{t['BEFORE_FRAME_SHA256'][:16]}…` → `{t['AFTER_FRAME_SHA256'][:16]}…` (pixel diff {t.get('PIXEL_DIFF_PX')} px)")
    if t.get("LOG_EXCERPT"):
        evidence.append("- trace excerpt (stderr tail):\n\n```text\n" + t["LOG_EXCERPT"][:900] + "\n```")
    if ref.get("STATUS") == "OK":
        evidence.append(f"- reference: {ref['URL']} sha256:`{(ref.get('SHA256') or '')[:16]}…`")
    else:
        evidence.append(f"- reference: `{ref.get('STATUS','PENDING')}` (no fabricated reference — §10)")
    if not evidence:
        evidence.append("- none yet (not executed)")

    cmp_ = t.get("COMPARISON") or {}
    cmp_lines = []
    if cmp_:
        cmp_lines.append(f"- verdict: `{cmp_.get('STATUS')}` level {cmp_.get('LEVEL')}")
        rp = cmp_.get("REFERENCE_PALETTE") or {}
        mp = cmp_.get("MINIANDROID_PALETTE") or {}
        if rp:
            cmp_lines.append(f"- REFERENCE_PALETTE: uniq {rp.get('UNIQUE_COLORS')}, dominant {rp.get('DOMINANT', [])[:2]}, lum {rp.get('LUMINANCE_RANGE')}")
        if mp:
            cmp_lines.append(f"- MINIANDROID_PALETTE: uniq {mp.get('UNIQUE_COLORS')}, dominant {mp.get('DOMINANT', [])[:2]}, lum {mp.get('LUMINANCE_RANGE')}")
        if cmp_.get("STATUS") == "VISUAL_FAIL":
            cmp_lines.append("- §19 law: palette mismatch with correct text is still a VISUAL_FAIL")

    fid_lines = []
    for f in t.get("F_IDS", []):
        fid_lines.append(f"- `{f}` — common runtime (root-cause issue: see §17/§18 fanout graph in `docs/corpus/s82/root_cause_graph.md`)")
    for f in t.get("VF_IDS", []):
        fid_lines.append(f"- `{f}` — visual failure chain")
    for f in t.get("FAILURE_LABELS", []):
        fid_lines.append(f"- `{f}`")
    if not fid_lines:
        fid_lines.append("- none recorded")

    name = t.get("NAME") or pkg
    return f"""# {name}

## Identity

- Title ID: **{t['TITLE_ID']}** (stable identity — independent of issue number)
- Type: {t['TYPE']}
- Package: `{pkg}`
- Version: {t.get('VERSION') or 'unresolved'} (vc {t.get('VERSION_CODE') or '?'})
- APK SHA256: `{t.get('APK_SHA256') or 'NOT_SOURCED_YET'}`
- F-Droid: {t.get('F_DROID_URL') or '(inventory title — no F-Droid page)'}
- Source: {t.get('SOURCE_URL') or 'NOT_RECOVERED (never guessed — §6)'}
- Source revision: {t.get('SOURCE_REVISION') or 'NOT_PINNED'}

## MiniAndroid

- Commit: `{(t.get('LAST_TESTED_COMMIT') or 'NOT_TESTED')[:12]}`
- Runtime build: miniandroid (real-dalvik execution mode)
- Session: `{t.get('SESSION_ID') or 'NONE'}`
- Test date: {t.get('TESTED_AT') or 'not tested'}
- Environment: container Linux x86_64, 8 frames × 300 ms standard protocol

## Current compatibility status

{fmt_status(t)}

## Expected behavior

{(mand_ref and f"Official F-Droid reference screenshot: {mand_ref}") or "Reference behavior per the real app on a real Android device / official F-Droid screenshot (see Reference evidence)."}

## Observed behavior

{t.get('OBSERVED') or ('Executed this wave — see status + evidence below.' if runs else 'Not executed yet. This record exists so future work has a permanent home (§5/§26).')}

## Reproduction

{repro}

## Input performed

{('Canonical taps dispatched: ' + str(t.get('TAPS_USED'))) if runs else 'none'}

## State transition

{(f"pixel diff before→after: {t.get('PIXEL_DIFF_PX')} px" + (f" — proven" if (t.get('PIXEL_DIFF_PX') or 0) > 250 else " — below threshold / none")) if t.get('PIXEL_DIFF_PX') is not None else ('not attempted' if not runs else 'no state change proven')}

## Reference evidence

- reference screenshot: {ref.get('URL') or (mand_ref or 'REFERENCE_NOT_AVAILABLE')}
- reference source: {ref.get('SOURCE', 'F-Droid official package page')}
- reference version: {t.get('VERSION') or 'latest'}
- reference SHA: `{ref.get('SHA256') or 'NONE'}`

## MiniAndroid evidence

- screenshot: {t.get('SCREENSHOT') or 'NONE'}
- screenshot SHA: `{t.get('SCREENSHOT_SHA256') or 'NONE'}`
- trace: {'logged in session dir `run/s82/' + t['TITLE_ID'] + '/`'} 
- ViewTree: available via engine `-o` artifacts when rendered
- render trace: stderr tail in Evidence section

## Visual comparison

{('Three-level (§30): structural / visual / semantic.\n' + chr(10).join(cmp_lines)) if cmp_lines else 'PENDING — requires reference + MiniAndroid screenshots side by side (performed for mandatory + representative titles this wave).'}

- layout: {cmp_.get('LAYOUT', 'PENDING')}
- colors: {(str(cmp_.get('LEVEL')) + '/3 palette overlap') if cmp_ else 'PENDING'}
- text: {('present' if (vis.get('TEXT_PIXELS') or 0) > 0 else 'none observed') if vis else 'PENDING'}
- icons: {('present' if (vis.get('ICON_PIXELS') or 0) > 0 else 'none observed') if vis else 'PENDING'}
- images: {('present' if (vis.get('IMAGE_PIXELS') or 0) > 0 else 'none observed') if vis else 'PENDING'}
- drawables: {'PENDING'}
- canvas: {'PENDING'}
- state: {t.get('STATE_CHANGE', 'NONE')}

## Failure / Root cause

{chr(10).join(fid_lines)}

- first failing method: {t.get('FIRST_FAILING_METHOD') or 'NOT_TRACED'}
- producer: {t.get('PRODUCER') or 'PENDING'}
- consumer: {t.get('CONSUMER') or 'PENDING'}

## Regression

- previous status: {t.get('PREV_STATUS') or 'NONE (first S82 record)'}
- current status: `{t.get('STATE','STATE-NOT-LOADED')}`

## Resolution

{t.get('RESOLUTION', 'OPEN')}
"""


if __name__ == "__main__":
    reg = json.load(open(REG))
    for t in reg["TITLES"][:1] + reg["TITLES"][200:201]:
        print(body_for(t)[:3000])
        print("=" * 60)
