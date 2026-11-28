# DUPLICATE_WORK.md — overlapping/duplicate implementations

## Confirmed duplicates / redundancies

1. **Dual bridge_to_api implementations (RESOLVED by T281)**: T280 treated them as an ODR contest; truth = exactly one compiled definition (dalvik_bridge.o) in the default build. The monolith copy is a fallback mirror — edits there are invisible to production. GUARD: T281 banner at dalvik_engine.cpp:1-19 + recommended build-gate assert.
2. **RectF width/height + isEmpty law duplicated in monolith + ui_graphics (T280 mirrored both)**: the monolith mirror copy is inert in the default build. Kept for fallback correctness; risk = drift. Track under the monolith-fate decision.
3. **Wave9 lineage duplicated via parallel routes**: wave9/dev-so-integration (3 commits) vs main's direct W21-W23 — integration branch SUPERSEDED. wave10 (PR #626) holds the only NEW content (W20 fixes) — cherry-pick, do not merge the lineage.
4. **#597 W27 text laws vs later TextView work**: Coder-4 continued filing wave reports on #597 after main moved to W28+; verify each wave against main before implementing (waves may already be integrated under different commit messages).

## Same-root-cause groups (consolidation targets)

- **Provider stack**: KA-KYK-031 (ArrayAdapter) + audit/s236 provider laws + #618/#619/#623 app campaigns — one provider-law wave.
- **Compose interaction**: T280 CIP-1 (pfdicer/itsfrz) + #712 R-NEW-344 census + T279-C2 classifications — one compose-host materialization design.
- **Layout geometry**: #713 TableLayout + #714 MeasureSpec + LAYOUT-PIPE-001 (#606, closed 17 comments) — one geometry-law battery.
