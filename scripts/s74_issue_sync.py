#!/usr/bin/env python3
"""s74_issue_sync.py — S74 Issue<->Profile synchronization (taskbook §62):
post ONE dated evidence-checkpoint comment per canonical [EXEC] issue (#10-#23)
linking its committed compatibility dossier. No duplicate issues created; no
bodies rewritten; English-only public content (taskbook §51). Token comes from
the GH_TOKEN environment variable ONLY (never written to disk)."""
import json, os, sys, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
HEAD = os.popen("git -C /home/z/my-project rev-parse --short HEAD").read().strip()

APPS = [
    (10, "helloworld", "DONE — completed state documented and preserved (golden control target)"),
    (11, "tictactoe", "DONE — completed state documented and preserved (9-click chain, win x3, deterministic frames)"),
    (12, "connectfour", "DONE — completed state documented and preserved with the corrected result (22/24 meaningful transitions, Y win at click 22)"),
    (13, "androidgamesnake", "OBSERVED — S73 autonomous gameplay preserved: 88 moves / 22 turns / 1 food capture / 3-run byte-identical; restart-after-game-over honestly open"),
    (14, "dooz", "BLOCKED — F-146 / F-147 root blockers, F-145 visual frontier; the 23,472-px false visual claim is preserved as SUPERSEDED record CLAIM-DOOZ-23472-VISUAL"),
    (15, "unote", "PARTIAL — themed UI 231,120 px proven; input/state legs unprobed at current HEAD"),
    (16, "telegram", "PARTIAL — historical checkpoint-M evidence preserved; init budget blocker; not re-run at current HEAD"),
    (17, "gmdice", "PARTIAL — render + S63 L7 historical; ladder open at current HEAD"),
    (18, "microtimer", "PARTIAL — render + historical L7 keypad-to-display; ladder open"),
    (19, "fishrings", "PARTIAL — board render + historical S10 interactions; game-logic depth unexercised at HEAD"),
    (20, "tripeaks", "BLOCKED (visual) — R-NEW-388 app-specific OBJECT-IDENTITY; generic RL anchor laws stay proven"),
    (21, "bouncy", "PARTIAL — S62 L6 two-state clicks preserved; L7 physics-loop proof open"),
    (22, "stopwatch", "BLOCKED by design — service-only manifest (F-143 family); engine behavior correct"),
    (23, "opmt", "PARTIAL — S6 chain preserved; app-own IOOBE (OBJECT-IDENTITY) stops progression"),
]

BODY = ("**S74 dossier sync (architecture wave; runtime untouched)**\n\n"
        "Canonical compatibility dossier committed at `docs/compatibility/apps/{aid}.json` "
        "(schema v1: identity / completion criteria C1-C14 / current blocker / next executable "
        "task / linked semantic laws, capabilities, evidence).\n\n"
        "Status snapshot at {head}: {status}.\n\n"
        "This issue remains the living execution record; the dossier is its structured mirror. "
        "Graph integrity gate: `tools/validate_compatibility_graph.py` PASS at S74 HEAD "
        "(references, statuses, provenance, evidence paths, registry, index). "
        "Vendor-neutral execution workflow: `skills/android-execution/SKILL.md`.")


def post(issue, body):
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("FAIL: GH_TOKEN env var not set (refusing to proceed without credentials)")
    url = f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"
    data = json.dumps({"body": body}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "miniandroid-s74-sync",
    })
    with urllib.request.urlopen(req) as r:
        out = json.load(r)
    return out.get("html_url", "?")


def main():
    only = [int(x) for x in sys.argv[1:]] or None
    for issue, aid, status in APPS:
        if only and issue not in only:
            continue
        body = BODY.format(aid=aid, head=HEAD, status=status)
        url = post(issue, body)
        print(f"#{issue} <- {aid}.json  {url}")


if __name__ == "__main__":
    main()
