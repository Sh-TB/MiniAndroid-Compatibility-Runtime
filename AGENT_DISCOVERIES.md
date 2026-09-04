# AGENT_DISCOVERIES — claims vs independent verification (2026-09-02)

Rule (master request §6): an agent report is DISCOVERY/LEAD, never PROOF.
This file records the reconciliation verdicts. Full index: MASTER_PROJECT_KNOWLEDGE.md.

## Legacy RESULT_ ledger (§7 of the master request)

| ID | Original claim | Verdict after independent inspection (2026-09-02) |
|----|----------------|---------------------------------------------------|
| RESULT_001 | long arithmetic / 64-bit semantics correct | **FALSE at v0.13.0 → VERIFIED+FIXED** (6fda28d). int32 union read truncated every operand >2^32 while tagging INT64. Fixture: semantic_long_cmp_conv_test.cpp. |
| RESULT_003 | clock virtualization needed for determinism | **PARTIALLY VERIFIED / ANALYSIS ONLY.** currentTimeMillis/nanoTime ARE implemented as real-clock API calls (EXP-043, ~11334-11360). Determinism is achieved by staged re-runs + hash-pinned evidence, NOT virtual time. exp018 remains experimental-only. Virtual clock = open design option, no current requirement proven. |
| RESULT_007 | opcode table audit (beyond the 4 known) | **PARTIALLY VERIFIED.** Historical off-by-1 + lit8 fixes confirmed present (ALREADY FIXED). NEW finding this pass: 12x register-nibble extraction was wrong in /2addr + CONV (K-05) — fixed; packed/sparse-switch (0x2B/0x2C) defined but NOT dispatched (K-18, open). |
| RESULT_009 | cmp-long / cmpl/cmpg semantics correct | **FALSE at v0.13.0 → VERIFIED+FIXED.** cmp-long returned 0 for all INT64 operands; no NaN ordering; FLOAT64 read via float_val; INT64-tagged double consts garbage. Fixed incl. bits_l2d. |
| RESULT_010 | conversions correct | **FALSE at v0.13.0 → VERIFIED+FIXED.** Tag-only re-tags; no sign/zero extension, no saturation, no real float↔int. Fixed (JLS 5.1.3 semantics). |
| RESULT_012 | parseInt/parseLong/parseFloat/parseDouble implemented ("NATIVE_CPP") | **FALSE as implementation.** Present only in exp018_main.cpp planning JSON. NOT in production dispatch (K-19). Roadmap item #1. |
| RESULT_013 | String substring/concat bridges | **NOT REPRODUCED as implementation.** No `method == "substring"/"concat"` dispatch exists. StringBuilder toString/length/charAt/isEmpty and String.equals ARE real (K-21). |
| RESULT_014 | Canvas matrix ops | **PARTIALLY VERIFIED.** save/restore/translate/scale/rotate/skew/concat/clipRect/saveLayer/restoreToCount are accepted by canvas_shadow.cpp (237-239). Exhaustive composition semantics unproven. |
| RESULT_016 | ARSC @string/ resolution | **VERIFIED.** Chain XML→AXML→ARSC→string→View property works; FIX-013-04 (b9d93cc) + live probe 3/3 layouts on a real APK. |

## New agent-era discoveries revalidated this pass (§8)

| Discovery | Verdict |
|---|---|
| iget-wide / iput-wide | **VERIFIED ALREADY IMPLEMENTED** (EXP-062 comments, 64-bit paths) — untouched by the fix; byte-stable app outputs confirm. |
| if-*z / if-* float semantics | if-eqz/neqz + 22t family dispatched (EXP-037 BLOCKER-018); int-based per spec; no regression found. |
| packed-switch / sparse-switch | **NOT IMPLEMENTED** (defined only) — added to NOT_DONE. |
| monitor-enter / monitor-exit | **VERIFIED** minimal dispatch (no-op lock model). |
| filled-new-array / 35c fallback | **VERIFIED ALREADY FIXED** (5/5 fixture). |
| TypedArray / obtainStyledAttributes, BitmapFactory DEX path, Resources.getColor(int), View.setBackgroundColor, renderer text_color, Canvas DEX shadow | These belong to the 013-era fix set; the byte-stable app matrix + ARSC probe confirm the paths live on. Exhaustive per-item re-audit deferred (recorded in NOT_DONE #15). |
| dump_view_tree missing visual/state fields | ANALYSIS ONLY — not re-audited this pass; kept as lead in NOT_DONE. |
| Campaign-012 "f5da664/v0.12.0" | **FALSE provenance** — hash/tag absent from local DAG, all ZIPs, and the GitHub remote (ls-remote 2026-09-02). |

## Lesson recorded

Three "already correct" semantic areas (RESULT_001/009/010 + 12x nibbles) were
still wrong at v0.13.0 because their fixes lived in a lost workspace that was
never pushed. **A fix that is not in the master repository does not exist.**
