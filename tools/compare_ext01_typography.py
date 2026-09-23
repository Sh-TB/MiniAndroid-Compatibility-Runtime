#!/usr/bin/env python3
"""
compare_ext01_typography.py — GOLDEN-01 typography golden (G48, Rule 10).

Compares the trusted reference screenshot (upstream author's real phone,
600x1067) against the MiniAndroid screenshot (1080x1920) with PER-LINE,
PER-QUANTITY measurements — never a single whole-image similarity number.

DYNAMIC vs STATIC (DYNAMIC CONTENT RULE):
  The rendered strings contain device-specific values (ANDROID_ID, Android
  version, API level). Text CONTENT is therefore never compared. The STATIC
  quantities below are compared: background, ink presence, line structure,
  centering, block size, line spacing, monospace advance, band heights.
  (The dynamic values happen to be the same character LENGTH on both sides
  — 20-char hex id, 1-2 digit numbers — so per-line widths stay comparable;
  this is recorded, not assumed: MiniAndroid prints its own values.)

Usage:
  compare_ext01_typography.py <ref.png> <mini.png> [--json out.json]
Exit 0 iff every STATIC check passes.
"""
import json
import statistics
import sys

from typography_measure import analyze


def rel(x, base):
    return x / base


def main():
    ref = analyze(sys.argv[1], "reference_phone", sysbar_frac=0.07)
    mini = analyze(sys.argv[2], "miniandroid")
    checks = []
    rows = []

    def check(name, passed, detail):
        checks.append((name, bool(passed), detail))
        rows.append(f"{'PASS' if passed else 'FAIL'}  {name}: {detail}")

    # ---- static quantities ----
    check("background identical (black)",
          ref["bg"] == mini["bg"] == 0,
          f"ref bg={ref['bg']} mini bg={mini['bg']}")
    check("ink present",
          ref["ink_total"] > 1000 and mini["ink_total"] > 1000,
          f"ref ink={ref['ink_total']} mini ink={mini['ink_total']} "
          f"(grayscale, ink = |px-bg| > 60)")
    check("4-line band structure",
          len(ref["lines"]) == 4 and len(mini["lines"]) == 4,
          f"ref bands={len(ref['lines'])} mini bands={len(mini['lines'])}")

    rcx, mcx = ref["cx"], mini["cx"]
    check("horizontal centering within 3%",
          abs(rcx - 0.5) < 0.03 and abs(mcx - 0.5) < 0.03,
          f"ref cx={rcx:.4f} mini cx={mcx:.4f}")
    rcy, mcy = ref["cy"], mini["cy"]
    check("vertical centering within 6%",
          abs(rcy - 0.5) < 0.06 and abs(mcy - 0.5) < 0.06,
          f"ref cy={rcy:.4f} mini cy={mcy:.4f}")

    # text block relative width (screen-width fraction)
    rw, mw = ref["rel_block_width"], mini["rel_block_width"]
    check("text block width ratio within 10%",
          abs(mw - rw) / rw < 0.10,
          f"ref={rw:.4f} mini={mw:.4f} rel.diff={abs(mw-rw)/rw*100:.2f}%")

    # text block relative height
    rh, mh = ref["rel_block_height"], mini["rel_block_height"]
    check("text block height ratio within 10%",
          abs(mh - rh) / rh < 0.10,
          f"ref={rh:.4f} mini={mh:.4f} rel.diff={abs(mh-rh)/rh*100:.2f}%")

    # line spacing: median baseline-to-baseline / image height
    # (baseline = band bottom for descender-free lines 1-3; line 4 bottom
    # includes the 'p' descender — use bottom_to_bottom[0] and [1] plus
    # top_to_top as the spacing set)
    ref_sp = statistics.median(ref["bottom_to_bottom"][:2] + ref["top_to_top"][1:])
    mini_sp = statistics.median(mini["bottom_to_bottom"][:2] + mini["top_to_top"][1:])
    ref_sp_rel = ref_sp / ref["h"]
    mini_sp_rel = mini_sp / mini["h"]
    check("line spacing ratio within 10%",
          abs(mini_sp_rel - ref_sp_rel) / ref_sp_rel < 0.10,
          f"ref median spacing={ref_sp:.1f}px ({ref_sp_rel:.5f} of height) "
          f"mini={mini_sp:.1f}px ({mini_sp_rel:.5f}) "
          f"rel.diff={abs(mini_sp_rel-ref_sp_rel)/ref_sp_rel*100:.2f}%")

    # monospace advance: line 2 = "i'm <20-char id>" (dynamic VALUE, same
    # char count) — ink width / 20 chars as the advance proxy
    ref_adv = ref["lines"][1]["rel_width"] / 20.0
    mini_adv = mini["lines"][1]["rel_width"] / 20.0
    check("monospace advance ratio within 10%",
          abs(mini_adv - ref_adv) / ref_adv < 0.10,
          f"ref advance={ref_adv:.5f} of width/char "
          f"mini={mini_adv:.5f} rel.diff={abs(mini_adv-ref_adv)/ref_adv*100:.2f}%")

    # per-line ink geometry table (Rule 10 reporting)
    print("== per-line ink geometry ==")
    print(f"{'line':>4} {'ref y0-y1':>12} {'ref h':>6} {'ref w':>6} "
          f"{'mini y0-y1':>12} {'mini h':>6} {'mini w':>6}")
    for i in range(4):
        r = ref["lines"][i]
        m = mini["lines"][i]
        print(f"{i:>4} {f'{r[chr(121)+chr(48)]}-{r[chr(121)+chr(49)]}':>12} "
              f"{r['height']:>6} {r['width']:>6} "
              f"{f'{m[chr(121)+chr(48)]}-{m[chr(121)+chr(49)]}':>12} "
              f"{m['height']:>6} {m['width']:>6}")
    print()

    for r in rows:
        print(r)
    ok = all(p for _, p, _ in checks)
    print()
    print("GOLDEN-01 TYPOGRAPHY GOLDEN:", "PASS" if ok else "FAIL",
          f"({sum(1 for _, p, _ in checks if p)}/{len(checks)} static checks)")
    if "--json" in sys.argv:
        outp = sys.argv[sys.argv.index("--json") + 1]
        with open(outp, "w") as f:
            json.dump({"reference": ref, "miniandroid": mini,
                       "checks": [{"name": n, "pass": p, "detail": d}
                                  for n, p, d in checks],
                       "verdict": "PASS" if ok else "FAIL"}, f, indent=1)
        print("wrote", outp, file=sys.stderr)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
