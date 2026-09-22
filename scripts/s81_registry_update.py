#!/usr/bin/env python3
"""s81_registry_update.py — S81 §42: extend the runtime failure registry with
the Visual Failure family (VF-*) + S81 findings. Appends entries; never
rewrites history (§24: script-driven, deterministic)."""
import json

REG = "/home/z/my-project/root_registry.json"
d = json.load(open(REG))
roots = d["roots"]
have = {r["id"] for r in roots}

NEW = [
 {
  "id": "VF-NEW-001",
  "title": "VF-DIALOG-ITEMS: AlertDialog$Builder.setItems(CharSequence[],listener) drops the item array — dialog paints title/message with items=0",
  "status": "ROOT_CAUSED-FIXED",
  "priority": "P0",
  "evidence": "UPSTREAM: AOSP AlertDialog.Builder.setItems law (frameworks/base/core/java/android/app/AlertDialog.java) — the CharSequence[] elements BECOME the dialog's item list. REPRODUCE: S81 probe fixture fixtures/s81_visual_probe (4 phases) — phase-1 dialog rendered title+message only, [DIALOG-LAYOUT] items=0, zero item rows painted. ROOT CAUSE: DialogShadow::dispatch_builder recorded only item_listener; the array arg was never materialized. FIX: dual-view law (same shape as R-NEW-339) in DalvikExecutionEngine::try_shadow_dispatch AND bridge_to_api — heap array elements (\"array[i]\" fields, length \"__array_length__\"/\"__new_array_length__\") materialized into DialogWindow::items before shadow dispatch; listener recording unchanged. OBSERVED: [S81-DIALOG-ITEMS] materialized 3/3; [DIALOG-LAYOUT] frame grew 920x144→920x408 items=3; ITEM-A/ITEM-B/ITEM-C rows painted with dividers (frame_007). REGRESSION: battery 26/26 rc=0, fidelity BYTE-IDENTICAL 90/90, f152 6/6, f153 3/3, spot pixel-golden verifier 4/4. EVIDENCE: /tmp/s81_probe_run2 (pre) vs /tmp/s81_probe_run3 (post) frames; fixtures/s81_visual_probe.",
  "wave": "S81",
 },
 {
  "id": "VF-NEW-002",
  "title": "VF-PLACEHOLDER-GARBLE: C013-CUSTOMVIEW placeholder painted the raw class descriptor (e.g. Lorg.billthefarmer.markdown.MarkdownView) over full-screen regions — user-visible garbled text",
  "status": "ROOT_CAUSED-FIXED",
  "priority": "P0",
  "evidence": "REPRODUCE: S81 visual audit of org.billthefarmer.notes_139 + omegacentauri.simplestopwatch_26 — overlapping unreadable strings at top-left of both screenshots. ROOT CAUSE: execution_engine.cpp C013-CUSTOMVIEW placeholder path drew the internal class descriptor as visible screen text at (left+12, top+12) of a 1080x1920 region. FIX (both placeholder sites): neutral small marker \"custom view (not rendered)\" at region bottom-left in light grey; class name kept in stderr trace only (honesty preserved, garble removed). OBSERVED: Notes frame_007 clean after fix (garble gone, marker bottom-left). REGRESSION: battery 26/26, fidelity BYTE-IDENTICAL 90/90 (replays contain no placeholders), f152 6/6, f153 3/3, pixel-golden spot 4/4.",
  "wave": "S81",
 },
 {
  "id": "F-NEW-156",
  "title": "Fresh-corpus onCreate APP BOUNDARY unwind family: first-run NPE inside app onCreate (before/at setContentView) unwinds process → blank two-color screen. Faces: de.tobiasbielefeld.solitaire GameSelector.onCreate invoke#3, org.debian.eugen.headingcalculator MainActivity.onCreate invoke#6 (MainActivity$1.<init>), com.chessclock ChessClock.onCreate invoke#2, omegacentauri.simplestopwatch StopWatch.onCreate invoke#18 (findViewById null → downstream NPE)",
  "status": "OBSERVED-FAIL",
  "priority": "P0",
  "evidence": "BATCH-01 (25 fresh F-Droid APKs, run/s81_batch01/batch01_report.json): 19/25 rendered uniq=2 (blank) with the onCreate-unwind signature in logs. This is the dominant visual-compatibility frontier: apps die inside onCreate on unbridged surface calls before any inflation. NEXT: per-app first-NPE disasm (scripts/s81_disasm_probe.py) → root-cause chain per §43.",
  "wave": "S81",
 },
 {
  "id": "R-NEW-402",
  "title": "S81 visual audit instrument: status ladder EXECUTED ≠ VISUALLY COMPATIBLE (L0 LOADED_ONLY … L5 VISUALLY_VERIFIED) + metric suite (UNIQUE_COLORS/COLOR_ENTROPY/DOMINANT ratios/region classes) + APK-raster-vs-screen image-presence gap detector",
  "status": "IMPLEMENTED",
  "priority": "P1",
  "evidence": "scripts/s81_visual_audit.py + scripts/s81_run_and_audit.py (methodology constants in-file, §36 no single fake score). Applied to the 18-APK curated ladder (run/s81_audit/s81_visual_report.json) and BATCH-01 (run/s81_batch01/batch01_report.json). Findings: zero curated third-party apps reach L3; only S80's own games do; 7 apps flagged IMAGE_DECODED_VS_RENDERED_GAP (A7b decode proven, ImageView path proven, but XML-src capture never fires for programmatic/complex resource chains).",
  "wave": "S81",
 },
]
added = 0
for e in NEW:
    if e["id"] not in have:
        roots.append(e)
        added += 1
json.dump(d, open(REG, "w"), indent=1)
print(f"registry: {len(roots)-added} -> {len(roots)} (+{added})")
