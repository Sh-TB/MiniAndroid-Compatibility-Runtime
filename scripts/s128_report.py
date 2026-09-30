#!/usr/bin/env python3
"""S128: post the MASTER WORKLIST report (campaign report format A-U) to the evidence issue."""
import json, os, urllib.request

TOK = open('/tmp/.gh_token').read().strip()
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'

BODY = """**S128 — CANONICAL MASTER WORKLIST: CREATED, GENERATED, VISIBLE** (campaign phase 0 complete)

The master worklist now exists as a first-class generated control document — no more "421 roots" abstractions:

- **[docs/MASTER_WORKLIST.md](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/docs/MASTER_WORKLIST.md)** (8,723 lines, generated — do not hand-edit)
- **[canonical/master_worklist.json](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/canonical/master_worklist.json)** — machine twin; every item carries ALL 27 campaign fields
- Commit `df18cc30`

## What it contains
1. **§1 Status counts** (computed, never invented) — table below.
2. **§2 Visual roadmap** — DONE/IN-PROGRESS/PENDING/BLOCKED/SUPERSEDED tree + the 19-node base pipeline `APK→DEX→Runtime→Application→Activity→Theme→Resources→ViewTree→Layout→Text→Images→Drawable→Canvas→Surface→Framebuffer→Screenshot→Input→StateChange→Redraw` with per-node open roots, pending caps, representative APKs, next blocker.
3. **§3 APK coverage matrix** — 27 validation targets × 15 columns (LOAD/DEX/APP/ACTIVITY/THEME/RESOURCE/VIEWTREE/TEXT/IMAGE/DRAW/FRAMEBUFFER/SCREENSHOT/INPUT/STATE/REDRAW), computed from L0–L7 checkpoints + honest frontier overrides (Telegram VIEWTREE=FAIL grey NOT-A-RENDER; WhatsApp ACTIVITY/VIEWTREE=FAIL b/w NOT-A-RENDER; FlappyCow gameplay blocked note; WebView/HTML5 Breakout row; 65-title OBSERVED corpus aggregate row).
4. **§4 Root-cause clustering** — 16 clusters (resource decode law / compose first-frame / touch dispatch / MessageQueue / concurrency / theme residue / drawables / text stack / Telegram / WhatsApp / service-window-GL / DEX robustness / VIDEO / GAME / native on-demand / security radar).
5. **§5 Dependency graph + critical path** (computed edges from registry dependencies).
6. **§6 P0–P4 priority queues** (recomputed on every regeneration).
7. **§7 Categories MC-001…MC-129** — every one of the 127 mandated categories + 2 discovered (security/sandbox boundary, IPC/Binder/Parcel), each with AOSP/upstream reference + mature implementation per the TOOL-FIRST law.
8. **§8 Full 27-field records for all 260 open items. §9 Closed ledger (220). §10 Campaign watchlist. §11 Audit trail.**

## Status counts (480 deduplicated items)
| STATUS | COUNT |
|---|---|
| VERIFIED_3RUN | 3 |
| VERIFIED | 148 |
| TESTED | 13 |
| IMPLEMENTED | 7 |
| OBSERVED | 6 |
| PARTIAL | 105 |
| PENDING | 145 |
| BLOCKED | 3 |
| SUPERSEDED | 49 |
| IN_PROGRESS | 1 |
| **TOTAL** | **480** |

Sources reconciled & deduplicated: root_registry.json (421 roots) + capability_registry (197 caps; 37 PENDING) + app_registry (15) + game_registry (**91 after repair**) + campaign mandates (22 M-items) + worklogs S120–S127 + 100 open issues + keyword sweep (TODO/FIXME/STUB/PLACEHOLDER/HARDCODED).

## Registry repair found by the audit (R1)
`FlappyCow` / `GameMasterDice` / `Snake Neon` were **missing** from the audit source — the S125 overrides for them were silently dead (never bound, invisible in the canonical registry). Fixed idempotently (`scripts/s128_registry_repair.py`); canonical regenerated: **91 games**, overrides bind → GAME-024 FlappyCow (start-screen golden 13cf4746 ×3, gameplay blocked by GMS frontier), GAME-025 gmdice, GAME-026 snake-neon. Game IDs for observed titles shifted +3 (generation-order ids).

## P0 queue (20 open items — architectural/high fan-out)
| ID | TITLE | NEXT |
|---|---|---|
| M-01 | INPUT layer: touch dispatch + gestures + focus + scrolling | CAP-INPUT-102 TouchTarget law first |
| M-03 | GAME layer: lockCanvas loop + game loops + timestep | CAP-GAME-177 lockCanvas loop |
| M-06 | Compose render cluster (dooz v23 blank first frame) | R-NEW-294 MonotonicFrameClock fold |
| M-07 | Telegram frontier: SvgHelper SVG + gms Api nulls | SVG engine TOOL-FIRST decision |
| M-08 | WhatsApp frontier: AppContext.set + INVOKE_RETURN null | generic Context static law |
| M-02 | VIDEO layer (MediaCodec/Extractor/decode/Surface) | FFmpeg candidate + license record |
| M-12 | Corpus failure clustering (65 OBSERVED games) | cluster waves after INPUT/GAME base |
| M-16 | WebView/HTML5 engine TOOL-FIRST decision | decision record (no browser rewrite) |
| M-17 | Golden ladder G0–G11 codified runner | scripts/s128_ladder.sh |
| R-NEW-001/061/242/246/256/259/260/279/285, F-NEW-156/157 | (registry P0s — full records in worklist §8) | per-item |

## Campaign report (A–U)
- **A. MASTER WORKLIST CREATED/UPDATED**: YES — generated, canonical, visible (links above); wired into README CONTROL SYSTEM + ROADMAP §3.
- **B. TOTAL ITEMS**: 480.
- **C. VERIFIED**: 148 (+3 VERIFIED_3RUN, incl. R-NEW-423 S127).
- **D. TESTED**: 13.
- **E. IMPLEMENTED**: 7 (source-proof ceiling; never upgraded without runtime evidence).
- **F. OBSERVED**: 6.
- **G. PARTIAL**: 105.
- **H. PENDING**: 145.
- **I. BLOCKED**: 3 (Telegram, WhatsApp, FlappyCow gameplay — GMS/boundary).
- **J. SUPERSEDED**: 49 (NOT-APPLICABLE substrate + evidence-superseded).
- **K. P0 ROOTS**: 20 open.
- **L. P1 ROOTS**: 68 open.
- **M. P2 ROOTS**: 64 open (P3 105, P4 3).
- **N. CURRENT CRITICAL PATH**: R-NEW-294 (MonotonicFrameClock fold) → R-NEW-295 (composition render) → R-NEW-246/279/285 → R-NEW-256 → R-NEW-242 → dooz v23 unblock → compose corpus. Parallel: M-01 INPUT TouchTarget → interactive corpus; M-03 GAME lockCanvas → SurfaceView corpus; M-02/M-16 TOOL-FIRST decisions → VIDEO/WEB layers.
- **O. ROOTS CLOSED THIS CYCLE**: 0 runtime roots (phase-0 cycle); R-NEW-423 ROOT-CAUSED-CLOSED/VERIFIED_3RUN state recorded (S127).
- **P. CAPABILITIES COMPLETED**: 0 this cycle; all 37 PENDING capabilities are now explicit worklist items with TOOL-FIRST reuse paths.
- **Q. APKs IMPROVED**: 3 registry rows made visible (FlappyCow, gmdice, snake-neon).
- **R. APKs STILL BLOCKED**: Telegram (grey = NOT A RENDER), WhatsApp (b/w = NOT A RENDER), dooz v23 (blank first frame), FlappyCow gameplay (GMS).
- **S. REGRESSIONS**: 0 — worklist generation is runtime-side-effect-free; registry game-ids renumbered (generation-order), goldens untouched (calc a169346e ×3, flappy menu 13cf4746 ×3 remain the standing gates).
- **T. NEW ROOTS**: 0 runtime roots; audit finding R1 (dead overrides) filed as M-22 and closed this cycle.
- **U. NEXT AUTOMATIC ROOT**: **M-01 — INPUT layer, first law CAP-INPUT-102 TouchTarget** (AOSP ViewGroup.dispatchTouchEvent TouchTarget chain), then onInterceptTouchEvent / VelocityTracker / EdgeEffect; fan-out plan: reproducer + 2 unrelated APKs + 2 unrelated games + battery gate + golden ladder + 3-run when visual.

---
*Standing note: MiniAndroid renders frames into a real framebuffer and verifies them by pixel metrics + SHA; honest labels are enforced everywhere — Telegram's grey frame and WhatsApp's black/white frame remain load frontiers and are called NOT-A-RENDER in every generated panel; no "100% rendered" claims exist or are allowed; evidence images are published as small English-only JPGs (no gameplay GIFs per directive).*
"""

req = urllib.request.Request(
    f'https://api.github.com/repos/{REPO}/issues/354/comments',
    data=json.dumps({'body': BODY}).encode(),
    headers={'Authorization': f'Bearer {TOK}', 'Accept': 'application/vnd.github+json'})
r = urllib.request.urlopen(req)
print('posted:', json.load(r)['html_url'])
