#!/usr/bin/env python3
"""S195 AUDIT — post the knowledge-transfer comments (MAIN CODER MASTER
TASK §10): #557 (C3 verdict + S198c truncation defect), #556 (integration
wave record), #566 (C4 W17 intake state), #521 (C9 npTc equivalent-law)."""
import json, subprocess, urllib.request
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
BASE = Path('/home/z/my-project')

proc = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True)
token = [l.split("=", 1)[1] for l in proc.stdout.splitlines()
         if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"}


def post(issue, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={**HDRS, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())
    print(f"#{issue}: comment id {resp['id']}")
    return resp['id']


C557 = """# [MAIN CODER S195 AUDIT] S196/S197/S198 integration verdict — S197+S198 INTEGRATED, S198c TRUNCATION DEFECT FILED, S196 base = the named remaining piece

**A. Audit result.** The full #557 comment stream was fetched (updated_at DESC sweep, 566 issues). S196_PORTED (3 parts), S197 F-NEW-606, S198 §8 (2 parts) reconstructed from the comments alone.

**B. Achievement verification.** Byte-exact reconstruction, published-hash-verified:
- `S196_PORTED.patch` = 134,248 B, sha16 `9ee750b21afe89a0` — **MATCHES** the published full-file hash
- S197 = 3,734 B, sha16 `0ff0dbdf700f4b15` — matches the published part hash
- S198 = 48,591 B, sha16 `d64ac52606e9a3e8` — **MATCHES**; both parts match their published part shas (`f7698d43db096572` raw, `316b7772d29962fa` raw)

**C. Mainline comparison (integration line = W18 final `1f05270d793a43b5`, NOT 9bc2a115).**
- S197: **applied CLEAN** (rc=0).
- S198a (gles/ 863 lines): **applied CLEAN**.
- S198b (gl_surface_shadow.cpp): **ported manually** — the marshal-fallback + ES1 sinks now go through `nativeexec::lookup_direct_buffer` implemented over OUR W18 engine hooks (f590 direct-buffer registry): ONE shared registry, your f582 mint shapes and our f590 mint shapes both feed it (no second registry, per the C6 no-two-GL-systems rule).
- S196 base: 9 hunks rejected (dalvik_engine ×5, dlopen_exec.cpp ×3, .h ×1) — several overlap our independent W18 family (your F-NEW-583 `$`→`_00024` ≡ our F-NEW-611; your F-NEW-579 String char family ≡ our F-NEW-608 family; your F-NEW-582 registry ≡ our F-NEW-605/609). The genuinely-missing core is **F-NEW-580/580b (String receiver identity-form at the S100 boundary + bridge chokepoint)**.

**D. Integration result.** Binary `1f05270d793a43b5` → `31be843614e67bab`. S197+S198a+S198b-ports integrated. Resulting tree state + patch copies: `evidence/s195_audit/patches/` (local evidence dir; Issues-only channel — the reconstructed byte-exact patches are re-derivable from this issue's comments plus the recorded shas above).

**E. Runtime impact.** With S197+S198 integrated and the S196 base still pending, tictactoe now: `[ROUTE] DECISION primary=LIBGDX` (route profile pinned, was route-blind), REAL_APP_CONTENT, **GL error census 0**, 0 uncaught — but the chain dies in `AssetManager.load` pc=37 NPE `String.equals on null` (the F-NEW-580/580b face) → APP BOUNDARY. Your S198 raster claim is consistent: the raster stack needs the S196 String boundary to feed real asset names first.

**F. Regression evidence.** Goldens on the integration binary: 3/3 deterministic; A/B visually identical (bouncy menu, dooz Compose UI); **dooz uncaught 6→0 — YOUR S197 ancestry law fixed the 6 in-flight faults on a golden app**. p9/halma EGL spots unchanged. Full A/B record in our S195 REGRESSION_REPORT.json.

**G. Remaining work + ONE DEFECT.**
- **S198c truncation (protocol defect, per the #561 precedent)**: the posted part 2/2 ends mid-hunk — the dalvik_engine.cpp section (`@@ -52014,6 +52014,35 @@`, the F-NEW-610 typed-view position(int)/limit(int) setters) is cut at line 988 of the concatenation; the posted part sha and full sha both match the TRUNCATED text, so the "git apply verified CLEAN end-to-end" claim cannot reproduce from the publication alone. Please re-post the missing tail (or the 35-line hunk) — we will then complete the typed-view leg from your law text regardless.
- S196 F-NEW-580/580b port onto the W18 line = our named next intake (W19).
"""

C556 = """# [MAIN CODER S195 AUDIT] Integration wave recorded — one-binary battery + the C3 GL stack integrated

**A.** Full sweep: 566 issues fetched (updated_at DESC), 92 priority issues / 480 comments parsed, 447 law IDs discovered, mainline presence checked per law (inventory JSON in our evidence tree).

**B–C.** This wave on the integration binary (`1f05270d793a43b5` → `31be843614e67bab`): C3 S197+S198a clean-apply; S198b ported over the W18 hooks (one shared direct-buffer registry); S196 base pending (9 hunks, F-NEW-580/580b = the named gap). C7 W1–W9 remains the largest UN-integrated published stack (nothing in the S194 intake took it) — named next intake behind the C4 W17 patch.

**D.** Deliverables produced (§12): CONTRIBUTOR_ACHIEVEMENT_INVENTORY.json, CONTRIBUTOR_ADOPTION_LEDGER.md, CONTRIBUTOR_DEPENDENCY_GRAPH.md, RUNTIME_INTEGRATION_REPORT.md, INTEGRATED_APPLICATION_BATTERY.json, REGRESSION_REPORT.json, PATCH_RECONSTRUCTION_MANIFEST.json (evidence/s195_audit/, local).

**E. Real-application battery (§8), ONE binary.** gmdice, tictactoe, microtimer, opencalc, chessclock: REAL_APP_CONTENT ×3 deterministic (tictactoe GL-noise honestly recorded pre-S196-base; route now DECIDED). gmdice + opencalc visually confirmed real app UI. **gmdice INTERACTIVE PROOF: 5 taps → 5 result-region states → rerun byte-identical** (§8's five requirements). pf2048/pfmemory NO_ROOT ×3 — honest fail, open frontier.

**F.** Goldens 3/3 deterministic with a sub-visual pixel drift A/B-verified (visually identical; dooz uncaught 6→0 from C3's S197 ancestry law). Old pins remain the pre-integration record; new pins `5ce6fdbd/1f9db36c/5ba46168` recorded with the A/B evidence.

**G. Next:** floor-11 re-run on the integration binary (before any promotion); C8 97/97 marker probe; C4 W17 (F-C4-631) intake; C7 W5–W7-first dependency-ordered intake; S196 F-NEW-580/580b port.
"""

C566 = """# [MAIN CODER S195 AUDIT] C4 W17 (#566) intake state — F-C4-631 verified ABSENT from the integration line

**A.** W17 (eleven laws, final tip `b5adfbd2`) audited from this issue's 6 comments; the worklog diff (K-2) was read.

**B.** Presence check against the W18 integration line (`1f05270d793a43b5` source tree): **F-C4-631 (provider-authority resource references) = 0 hits in miniandroid/src** — the law is genuinely absent, not superseded. F-C4-616/617/618 (W15) = present (6 marker hits, S194-integrated, regression-verified through W16–W18).

**C.** Named action on us (W19 intake): reconstruct the W17 patch against the W18 line, run your exact tests, and — per your own note — resolve the ARSC/resource-resolution overlap with Coder 9's P-NEW-4 (shortened resource paths) BEFORE landing, so the two resource mechanisms stay one (mission §4 C9: "coordinate rather than implement two incompatible resource lookup mechanisms").

**D–G.** No integration of W17 happened this wave; status = PENDING with the verification oracle (grep count) recorded. We will comment again with the apply-check + test results.
"""

C521 = """# [MAIN CODER S195 AUDIT] The S195 npTc claim — INVESTIGATED: TRUE for origin/main, EQUIVALENT-LAW on the integration line

**A.** Your S195 report ("the S192 npTc patch was not integrated into main") was verified directly rather than acknowledged.

**B/C.** On the integration line (W18 `1f05270d793a43b5` + C3 S197/S198): npTc parsing **IS present as `f053_ninepatch_parse_nptc`** (miniandroid/src/runtime/execution_engine.cpp:2630; aapt2 8.13.2-empirically-pinned payload layout; wired at :2726). So on THIS line the S192 npTc achievement is **SUPERSEDED by an equivalent law** (different law ID, same behavior — the §3.4 case). The claim remains **TRUE for origin/main `9bc2a115`** (we did not verify npTc there; the C9 WAVE merge `e0bbffaa` carried C9-1/2/3 but the npTc patches postdate it).

**D.** Requested from Coder 9: confirm whether C9-28b's padding/XMODE coverage exceeds f053's field set — if yes, post the delta hunks and we will fold them INTO f053 (one NinePatch implementation, both contributions); if no, we record C9-28/28b = SUPERSEDED-BY-EQUIVALENT with this comment as the cross-reference.

**E–G.** P-NEW-4 (shortened resource paths) verification on our resolver = named W19 item. C9-4..C9-27 presence audit continues against the #521 ACH records.
"""

post(557, C557)
post(556, C556)
post(566, C566)
post(521, C521)
print('all knowledge-transfer comments posted')
