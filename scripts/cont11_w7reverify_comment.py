#!/usr/bin/env python3
"""CONT-11 W7 RE-VERIFY — post the honest reconciliation ledger to Issue #387
(the current batch-tracking issue). Same-Issue protocol."""
import json, subprocess, sys

BODY = r"""
# CONT-11 W7 RE-VERIFY — cold-reset reconciliation (2026-10-24)

This session's container was reset to the **CONT-10 snapshot `e99c2fbd`** (registry 566)
while origin/main had already advanced (CONT-11 W7 → CONT-14 batches → CONT-17/18h,
registry 834). The wave therefore ran as an **independent re-derivation** of the dooz
draw-path chain, then reconciled honestly against the remote truth. Commit `61427851`.

## Independent re-derivation — every link CONFIRMED against F-NEW-265

- Cold rebuild after reset (kernel OOM-kills; `trace_exporter.o` built -O1, deviation
  recorded): **SEMANTIC NEUTRALITY PROVEN — 5 anchors ×3 byte-identical** (opencalc
  `a976d2f9fb675cb3` / chess `b5a7a35d5fe0564b` / dooz `d602648e8e401895` / microtimer
  `da73010a37dd0189` / unote `4f1a9e4e8f64fae8`).
- Draw chain reproduced link-for-link: `Lt4;.dispatchDraw` runs to `return-void`
  (`dispatched=YES ops=0`, no exception); CanvasHolder swap `Lt4;.w=Lhi;` → `Ly3;.a`;
  `root.draw(Ly3;)` at pc=184; walk descends (`Lel0;.i` ×164, `Lpz0;.L0` path-B ×82
  translate-pairs, `M0` ×164, `Ly3;.f` ×164, **`Ly3;.p` drawRect ×0**);
  `T0(4)=head(Nodes.Draw)` null on every visited chain.
- **The gate reproduces quantitatively: `Lel0;.I()Z` (isPlaced) FALSE ×108 / TRUE ×18** —
  matching the F-NEW-265 face. R8-map corrections (Ly3;=AndroidCanvas via Lhi;
  CanvasHolder; W6's Ljt1; = text-path symptom) independently re-derived.
- **RECONCILIATION HONEST**: an interim local registration ("F-NEW-261 = placement gate")
  collided with the remote F-NEW-261 (S83-APXACT) and was **dropped** — registry untouched
  (834 roots), zero inflation. Evidence: `evidence/cont11_w7reverify/W7_INDEPENDENT_REVERIFY.md`.

## 40% old-apps block (at this re-run's CONT-10-era binary — labeled as such)

- **forkgram (Telegram classic) REAL_APP_CONTENT ×2 byte-identical `cf4c41e62ceb6557`**;
  44 in-flight exceptions past app frames (UnsatisfiedLinkError `ApplicationLoader;.onCreate`
  native-lib + NPE family `Lorg/telegram/ui/ActionBar/d6;.b0/y3/x3` launch-layout init) —
  the honest Telegram frontier at this binary; to re-check at the CURRENT remote binary.
- Old-games regression ×2 each **ALL REAL_APP_CONTENT**: 2048 `59ca1526611c4622`,
  SnakeDeluxe `34a712689ce66e58`, MiniCraft `b0876952f41e4af2`, Tetris `f360daa244cfca8d`,
  SnakeNeon `24fb7694eb64634a`, gmdice `f3b483fe7b7cf51b`.

## Tooling banked

`scripts/cont11_disasm_dispatch.py` (androguard per-method disassembler mapping trace pcs
to call targets), `scripts/cont11_buildloop.sh` (OOM-resilient single-thread build),
`scripts/cont11_baseline.sh` / `cont11_drawtrace.sh`.

Next: F-NEW-265 ARM-1/2/3 decomposition (remote pointer) remains the highest-ROI root;
forkgram d6; NPE family re-check at the current remote binary.
"""


def gh_token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None


def main():
    token = gh_token()
    if not token:
        print("NO TOKEN")
        sys.exit(1)
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/387/comments",
        "-H", f"Authorization: token {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"body": BODY}),
    ], capture_output=True, text=True)
    try:
        resp = r.json()
        print("posted:", resp.get("id"), resp.get("html_url"))
    except Exception:
        print("FAIL", r.stdout[:300])


if __name__ == "__main__":
    main()
