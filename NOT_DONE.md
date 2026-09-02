# NOT_DONE — what remains broken, missing, or unproven (updated 2026-09-03)

Ordered by leverage. Companion: MASTER_PROJECT_KNOWLEDGE.md (K-numbers), TOP_BLOCKERS_013.md.

## RESOLVED 2026-09-03 (master reconciliation PHASE 4 — commit 9d095f9)

The four runtime gaps below were implemented, fixture-proven (0/25 → 25/25),
and regression-gated (goldens byte-identical; see VERIFIED_TESTS.md):
1. ~~String/parse bridge (K-19, K-20)~~ → FIXED (parseInt/parseLong/parseFloat/
   parseDouble/substring/concat now dispatch; strict Java semantics).
2. ~~packed-switch / sparse-switch (K-18)~~ → FIXED (both payload shapes).
3. ~~div/rem-long by zero (K-29)~~ → FIXED (all integer forms throw
   ArithmeticException; the int/2addr form was also unguarded C++ UB).
4. ~~neg-long / not-long audit~~ → audit found WORSE: the whole 0x7B..0x80
   family was never implemented (K-32) AND the lit8 opcode table was shifted
   against AOSP (K-31, real add-int/lit8 dispatched as AND). Both fixed.

## Architecture boundaries (unmoved this campaign)

5. **Compose** (K-24): Dooz renders a deterministic blank frame; the composition
   hook (setContent → Compose runtime → LayoutNode tree) is not crossed.
6. **GLES** (K-25): PortableGL glue exists (golden cube renders standalone) but the
   GLSurfaceView/EGL dispatch hook is not wired into the engine's render loop.
7. **Layout geometry**: weight distribution wrong (simplestopwatch buttons full-height).
8. **Fonts**: long-string overlap (SFS-010); RTL pipeline is POC, not wired into TextView.
9. **Audio**: engine recovered but not in the default build.

## Data / provenance debts

10. **Telegram golden APK** (K-26): SHA f5e11927… lost from the external cache;
    telegram.org now serves newer bytes. Re-acquire the exact build to re-assert
    the 088ea640 baseline; until then the Telegram row is NOT REPRODUCED (not a
    code regression — simplestopwatch carries the pixel-exact regression proof).
11. **Campaign 014 code** (K-28): the lost session's runtime changes exist only as
    triage artifacts (docs/campaign014_evidence/). Re-running Campaign 014 from
    v0.13.0 (or this branch) is required for a true v0.14.0.
12. **Shallow-history boundary** (K-30 note): commits below a9434de in the ORIGINAL
    local clone were recovered from the GitHub master; any work done in lost local
    workspaces below that boundary that was never pushed is gone (only tags/
    artifacts survived).

## Process debts

13. WhatsApp/Signal probes are single-run evidence; no pinned goldens yet.
14. `run/` evidence directories are curated manually; an automated evidence
    manifest (hash + size budget) would prevent bloat.
15. RESULT_014 Canvas matrix: dispatch presence verified; exhaustive matrix
    composition tests (rotate+scale+clip interplay) still missing.
