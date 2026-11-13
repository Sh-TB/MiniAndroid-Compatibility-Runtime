# S213-C — cont69_mosaic measured audit (PNG vs JPG)

Measured 2026-11-13 at working tree of the S229 wave (#587 S213-C). Tools:
`tools/evidence_image_optimizer.py` (Pillow 11.3.0). Claim re-measured, not repeated.

## 1. Exact measurements

| file | bytes | dimensions | class | verdict | sha256 (first 16) |
|---|---:|---|---|---|---|
| `evidence/cont69/cont69_mosaic.png` | 896,399 | 2160x5000 | PHOTO_NOISY | REJECT_PROMOTION (legacy baseline) | `3ef9443010366c76` |
| `evidence/cont69/cont69_mosaic.jpg` | 50,423 | 553x1280 | PHOTO_NOISY | OK | `48d128bec724ccb0` |

Both RGB, no alpha, no animation.

## 2. Derivation proof (is the JPG derived from the PNG?)

Yes. Downscaling the PNG to the JPG's dimensions and comparing: RMS-DELTA
(gray 256x256 downsample) = **0.814**, max channel delta = 9/255 — the tracked JPG
is a faithful derivative of the PNG (same content, resampled). Re-encoding the
downscaled PNG at q85 yields 65,922 B vs the tracked 50,423 B, so the tracked JPG
was produced at a slightly lower quality (or marginally different resampling).

## 3. The size ratio — claimed 12x, measured

- **Total path ratio (PNG / tracked JPG) = 17.78x** — NOT 12x.
- Decomposition: the dimension reduction (2160x5000 -> 553x1280 = 15.3x area) does
  most of the work; **the JPEG format effect alone, at identical native 2160x5000
  resolution and q85, is 512,223 B = only 1.75x**.
- Any future claim should quote both numbers, never a single blended ratio.

## 4. Legibility / visual comparison

At the JPG's native presentation size the two are visually equivalent
(RMS-Δ 0.814). The JPG drops to 3.9x linear resolution, so fine print inside
16x zoomed mosaic tiles is sharper in the PNG. For the mosaic's evidence purpose
(showing the refreshed CONT-69 face grid at a glance) the JPG is fully legible.

## 5. References (which file is referenced where)

| consumer | references |
|---|---|
| `canonical/root_cause_registry.json` (2 hits) | `cont69_mosaic.png` |
| `docs/POLICY_ALLOWLIST.json` | both (1 each) |
| `evidence/evidence_size_inventory.tsv` | both (1 each) |
| `scripts/cont69_mosaic.py` (generator) | outputs `cont69_mosaic.jpg` |

## 6. Disposition (S213-C decision)

- **JPG = canonical presentation asset** (materially smaller, legible, generator output).
- **PNG retained with a narrow per-file exception** recorded in
  `docs/IMAGE_EXCEPTIONS.json`: full-resolution provenance source for the CONT-69
  mosaic claim (2160x5000, measured JPEG alternative 512,223 B @ q85 native) —
  a provenance role, not a presentation role. Review trigger: migration wave in #386.
- Reference audit result: the PNG is referenced only as a *provenance* record
  (`canonical/root_cause_registry.json` evidence field + ledgers); no
  presentation-facing document embeds either file, so no consumer rewrite is
  required — the roles are fixed by this audit + the exception record, and any
  future presenter must link the JPG.
- Result: no two visually-equivalent presentation copies circulate; each remaining
  path has one documented role.
