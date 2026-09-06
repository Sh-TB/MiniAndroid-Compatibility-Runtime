## GOLDEN-03 — RESOURCE COMPATIBILITY INFRASTRUCTURE + RESOURCE→PIXEL: VERIFIED — commits `3c87e279` → `748c4337`

**CLAIM.** The resource subsystem is now a reusable compatibility infrastructure with a canonical, traceable, hostile-safe resolution path — and the full chain `resources.arsc → ResourceId → configuration matching → best config → ResValue → reference resolution → style/bag/attribute → AXML → View → renderer → pixel` is runtime-proven on the frozen external APK (EXT-01 HelloWorldSelfAware v1.1.0, SHA-256 `009b4671…cc41`, hash re-verified this session).

**FROZEN FIXTURE INTEGRITY.** The sandbox wipe had removed aapt2 and the fixture; both restored per documented procedures with exact SHA-256 verification before any work.

**IMPLEMENTED (all generic, zero fixture-specific code — audited).**
- §3 canonical `ResId` — the single 0xPPTTEEEE model; 6+ duplicated bit-manipulation sites folded onto it.
- §4 `resolve_full(id, deviceConfig) → ResolutionResult` — per-step selected configuration + raw/resolved value distinction (AOSP AssetManager2 law: the value comes WITH its config).
- §5 configuration engine — 48-check generic matrix (locale refinement/rejection, density closest-bucket family, orientation, sw/w dp, uiMode, screen, version tie-break + size-gate preserved).
- §6 bounded (16) + cycle-safe reference resolution with NAMED deterministic failures (`INVALID_ID`/`MISSING_ENTRY`/`MISSING_REFERENCE_TARGET`/`CYCLE`/`DEPTH_EXCEEDED`/`NOT_RESOLVABLE`).
- §7 TypedValue laws in ONE source (`res_id.{h,cpp}`): applyDimension PX/DIP/SP/PT/IN/MM, pixel-size rounding + nonzero-floor, complexToFraction, color decode; FRACTION now decoded; manifest AXML constants aligned to AOSP Res_value.
- §8 `bag_value` attribute-key style queries with `ResTable_map_entry` parent inheritance; key-aware style application (textSize 0x01010095 / textColor 0x01010098 — byte-verified from real APK bytes); generic `textAppearance` resolution.
- §9 ONE dimension conversion path everywhere; engine setTextSize unit constants corrected (PX=0, DIP=1, SP=2).
- §10 **sidecar bypass REMOVED** — `resource_values.json` can no longer override ARSC values; integers/raw/drawables seeded ARSC-first.
- §12 `resource_trace` tool; §13 resource matrix; §14 hostile hardening (entryCount OOB read fixed) + 18-check hostile suite.

**QUANTITATIVE EXTERNAL PROOF (never a single number).**
- **Chain A** theme→bag→`windowBackground`(0x01010054)→@color/colorPrimary→**5 static framebuffer regions EXACTLY rgb(0,0,0)**.
- **Chain B** `@string/hello_message` (`%1$s %2$s %3$d`)→ARSC→`getString(id, 3 args)` ARSC-first→TextView **ink 25,988 px**, bbox [216,732,865,1195].
- **Chain C** TextAppearance.Large→22sp→scaledDensity→**tallest line band EXACTLY 58px** (heights [45,45,45,58]).
- Typography vs trusted reference: **9/9 static checks** (block height Δ 0.64%, line spacing Δ 1.58%, monospace advance Δ 3.03%).

**DETERMINISM (§16).** 3 independent runs → **byte-identical** screenshot SHA-256 `142238fd92b69e11d3407526de95cad29bf46e3f4191767d09a24379fbe0bbf2` (= the frozen G48 golden). The evidence harness EXPOSED a real determinism violation — monospace font resolution was cwd-relative — fixed via exe-relative resolution (FIND-REUSE-RES-006); byte-identity verified from two different working directories.

**REGRESSION (§20).** Battery extended **23 → 27 stages, ALL PASS**: semantic 96/96 · mutf8 14/14 · resource-config **48/48** · resource core law **42/42** · resource hostile **18/18** · encoded-value 18/18 · helloworld 26/26 · tictactoe 8/8 · EXT-01 9/9 · EXT-02 12/12 · corpus 3/3. No existing regression weakened.

**FINDINGS.** `FIND-REUSE-RES-001..008` recorded (docs/research/FIND_REUSE_RES.md) with statuses per discipline — implemented/tested/runtime-proven; nothing promoted to verified from source review alone.

**EVIDENCE FILES.** docs/evidence/GOLDEN03_RESOURCE_INFRASTRUCTURE_RECORD.md (A–H) · docs/evidence/golden03/ (chain traces, chain_pixel_checks.json, chains_summary.json, screenshot) · docs/RESOURCE_MATRIX.md · scripts/golden03_evidence.sh (one-command regeneration from HEAD).

Pushed to `main` (HEAD `748c4337`, local↔remote verified in sync via API read-back).
