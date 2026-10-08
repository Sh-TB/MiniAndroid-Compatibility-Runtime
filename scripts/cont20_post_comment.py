#!/usr/bin/env python3
"""CONT-20 — post the F-NEW-271 closure report to Issue #383."""
import subprocess, json, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 383

out = subprocess.run(["git", "config", "credential.helper"], capture_output=True, text=True).stdout
token = None
if "credential" in out or True:
    proc = subprocess.run(["git", "credential", "fill"], input="url=https://github.com\n\n",
                          capture_output=True, text=True)
    for line in proc.stdout.splitlines():
        if line.startswith("password="):
            token = line.split("=", 1)[1]

HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

BODY = r"""# CONT-20 wave report — F-NEW-271 ROOT-CAUSED + FIXED (null-element representation leak)

Workflow: reproduce the exact first divergence → heap/field representation audit → source-first semantic law (OpenJDK/ART) → genericity proof BEFORE patching → minimal generic fix → runtime proof + cross-target regression. Full record: `evidence/cont20/CONT20_F271_NULL_ELEMENT.md`. Commit `5eae8f54`, binary `b6ee41e77acb88ec`.

## A. First divergence (evidence, not inference)

- `[F271-READ]` `Lnb0;.S pc=163` reading `Lnb0;.j:Lqb0` answered **STRING_REF ""** from the **qualified heap slot `Lnb0;->j`** on recv#2838 (`declarer=Lnb0;`, `heap_cls=Lnb0;`) — the heap faithfully stored what it was given; the iget/field-key machinery (R-NEW-414 / F-NEW-251 suspects) is **exonerated**.
- `[F271-WRITE]` the alien store was caught in the act: `Lnb0;.p pc=1553 iput-object ← STRING_REF ""` into `Lnb0;.j`.
- Store source (cont3 disasm, engine-aligned): `Lnb0.p` = `i.remove(size-1)` at pc=1537 → `move-result-object v3` → `check-cast Lqb0` (engine's documented optimistic pass — no CCE; masking defect, separate scope) → `iput j`. CONT-18h's "j written only in .S" was incomplete: **.p is a third writer**.
- New channel diag `MINIANDROID_F271_COLL_TRACE` captured the fill: `Lnb0;.u pc=4` (`i.add(this.j); this.j = p1` — the enqueue-current-holder idiom) legally enqueued the real `Lqb0` holders **and six NULL_REF elements** into ArrayList o2839 (= `Lnb0.i` on composition o2838). Pre-fix `remove(0)` was served `t5/o0("")`.

**First incorrect runtime state**: CollectionShadow's null-element encoding (kind 2 + `elem_strings=""`) is **lossy** — null and genuine-`""` elements are indistinguishable in the four parallel stores, and every serve path materializes both as `STRING_REF/0`. The later exception (f141 at pc=185) was downstream damage.

## B. Semantic law

- OpenJDK `ArrayList`: *"permits all elements, including null"*; `remove(int)`/`get(int)` return **the stored element** — a null element comes back as **typed null**, never a fabricated `String`.
- ART: `move-result-object` yields a null register; the app side is null-tolerant **by design** (`Lnb0.p` pops with an explicit `if-eqz`).
- SOURCE-FIRST ≠ PORT-FIRST: no ArrayList port, no queue rewrite — one kind law on the existing four-store abstraction.

## C. Genericity — proven BEFORE the patch

New fcol rows **K19/K20** (pure `java.util.ArrayList`, zero dooz, zero Compose): **FAIL at the pre-fix binary** (`headNull=false lastNull=false poppedNull=false`; `secondNull=false`) → a generic Base defect, not a Dooz path. Any app enqueuing null into a list/deque (work queues, holder swaps, adapter recycling) hits the same primitive.

## D. Patch (minimal, generic)

`miniandroid/src/framework/android_shadows.cpp` — **NULL-ELEMENT KIND LAW** (kind 4 = null element), eleven sites: writers (`lawb_classify_arg`, add tail, add(index,e), set face, stream materialization) classify NULL_REF/zero-ref args as kind 4 (STRING args — **including `""`** — stay kind 2); readers (`lawa_remove_index`, `lawa_serve_slot`, `slot_to_arg`, iterator next, removeAll equality, `contains(null)`) serve kind 4 as typed null. Zero app/package checks. Plus the env-gated `MINIANDROID_F271_COLL_TRACE` diag and the committed K19/K20 fixture rows.

## E. Runtime proof

| Check | Pre-fix | Post-fix |
|---|---|---|
| remove serve on o2839 | `t5/o0("")` | **`t8/o0` typed null** ×2 runs |
| `Lnb0;.S pc=185` death | f141 uncaught | **GONE ×2** |
| F271-WRITE alien stores | 1 + noise | **0** |
| composition progress | dies at pc=185 | `Lnb0.S` pc=913/190 activity; deeper worker faces |
| fcol K19/K20 | FAIL/FAIL | **PASS/PASS** |
| dooz anchor | `d602648e8e401895` | unchanged (next root blocks visuals — honest) |

## F. Regression

Anchors **18/18 ×3 byte-identical** (dooz, microtimer, unote, gmdice, opencalc, chess); fcol **20/20**; f259 **7/7**; f259g **12/13** (known honest L row); f266 **6/6**; f268 **12/12**. gate-A negatives harness scores 9/19 at **both** the pre-fix and post-fix binaries with identical rows (A/B at `b4937c81aba0998c`) — pre-existing harness drift, not a regression of this wave; re-calibration queued as a work item.

## G. Decision: `IMPLEMENTED + PARTIAL`

The F-NEW-271 primitive is closed as a **generic Base/runtime root**. The dooz visual is unchanged because the chain immediately hits the **next** divergence — registered as **F-NEW-272 (CLASSIFIED, P0)**: the engine has **no Thread default UncaughtExceptionHandler law**; the app's own crash-report path (`Llo;.K pc=65` → `UncaughtExceptionHandler.uncaughtException`) runs on a **null** default handler, and the reporter NPE propagates uncaught to `MainActivity.onCreate` → APP BOUNDARY. AOSP law: the default handler is non-null (RuntimeInit LoggingHandler / KillApplicationHandler). That is the next wave's P0 target — generic Thread/runtime work, not Compose.
"""

data = json.dumps({"body": BODY}).encode()
req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
    data=data, headers=HDRS, method="POST")
with urllib.request.urlopen(req) as r:
    resp = json.load(r)
print("posted:", resp.get("html_url"))
