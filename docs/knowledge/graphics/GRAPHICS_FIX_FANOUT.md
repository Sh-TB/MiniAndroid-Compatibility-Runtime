# GRAPHICS FIX FANOUT (canonical) — S82-GFX-REVOLUTION

Question every fix must answer: **how many titles does this unlock?**

## F-NEW-158 fanout (fixed this wave)

- Direct fixture proof: l0_solid + l4_xmldrawables (2 fixtures, 4 drawables
  + ColorDrawable path).
- Real-corpus proof: GAME-004 re-run palette delta unique colors
  111 → 201 (evidence: run/s82gfx/fanout/GAME-004/ + FANOUT_RESULT.json;
  state fields intentionally unchanged pending full re-derivation).
- Corpus reach (static): every title whose UI builds backgrounds
  programmatically — families B/C/D/E cover 37/38/30/38 of the 41 executed
  APKs scanned (graphics_families.json). Exact per-title detector pending:
  run the dex-marker scan (s82gfx_family_scan.py) over the remaining 161
  APKs (disk-guarded lazy materialization).

## F-NEW-159 fanout (open)

Re-traced ×2 in the fanout probe (MAND-002, APP-001); shares the
F-NEW-156 blast radius (35 titles). Unlocks count = titles in the
F-NEW-156 fanout whose trace contains these two exact NPE signatures —
the fanout probe logs are the detector input.

## Fanout discipline (§18/§19 law)

1. fix lands → 2. scan corpus for the signature (static first) →
3. re-run ONLY the affected subset → 4. update every affected title issue
→ 5. record before/after palettes + SHA256s in the matrix.
