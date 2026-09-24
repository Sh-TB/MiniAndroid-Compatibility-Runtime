#!/usr/bin/env python3
"""GRAPHICS SOURCE CONSULTATION TOOL (S94 §14 - automatic lookup).

The GRAPHICS SOURCE-FIRST LAW (CONSTITUTION V2 section 170) requires that every
graphics failure be classified and looked up BEFORE any implementation work.

Usage:
  python3 tools/source_lookup.py WRONG_COLOR
  python3 tools/source_lookup.py WRONG_CLIP --json
  python3 tools/source_lookup.py --from-failure-map docs/evidence/s93/failure_map.json
  python3 tools/source_lookup.py UNREADABLE_TEXT --laws

Exit code 0 = sources found; 2 = unknown category.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "docs/GRAPHICS_SOURCE_REGISTRY.json"
SOURCE_TO_LAW = ROOT / "run/s94/source_mining/source_to_law.json"
GAP_MAP = ROOT / "run/s94/source_mining/gap_map.json"

# failure category -> source families (mirrors source_to_law.json lookup_rule)
CATEGORY_RULES = {
    "WRONG_COLOR": ["resource-density", "image-codec", "visual-diff"],
    "WRONG_CLIP": ["geometry-clip", "drawable-ninepatch", "layout", "android-ui-reference"],
    "ANIMATION_FROZEN": ["animation", "animation-gif", "frame-loop", "surface"],
    "UNREADABLE_TEXT": ["text-shaping", "text-layout", "text-bidi", "font-raster", "text-verify"],
    "SURFACE": ["surface", "frame-loop"],
    "FRAME_SUBMISSION": ["surface", "frame-loop"],
    "WEB_NOT_PAINTED": ["web-rendering"],
    "WEBVIEW_VISUAL": ["web-rendering"],
    "SCREENSHOT_FALSE_POSITIVE": ["screenshot-testing", "visual-diff"],
    "VECTOR_WRONG": ["vector"],
    "COMPOSE_PIXELS_WRONG": ["jetpack-compose"],
    "DENSITY": ["resource-density"],
    "GIF_DISPOSAL": ["animation-gif"],
    "NINEPATCH": ["drawable-ninepatch"],
    "HITBOX": ["view-tree", "android-ui-reference"],
    "TEXT_LAYOUT": ["text-layout", "text-shaping"],
    "TOFU": ["font-raster", "text-verify"],
}


def load():
    reg = json.loads(REGISTRY.read_text())
    s2l = json.loads(SOURCE_TO_LAW.read_text())
    return reg, s2l


def sources_for_families(reg, s2l, families):
    fam_set = set(families)
    # laws whose family matches
    laws = [l for l in s2l["laws"] if l["family"] in fam_set]
    repo_ids = {l["source"]["repository"] for l in laws}
    entries = [e for e in reg["entries"]
               if (set(e["families"]) & fam_set) or e["repository"] in repo_ids]
    entries.sort(key=lambda e: (e["priority"], e["inspection_status"] != "DEEP_CLONE",
                                e["inspection_status"] != "DEEP_FETCH", e["id"]))
    return entries, laws


def lookup_category(category, want_laws=False):
    reg, s2l = load()
    fams = CATEGORY_RULES.get(category.upper())
    if not fams:
        print(f"UNKNOWN CATEGORY: {category}", file=sys.stderr)
        print("known:", ", ".join(sorted(CATEGORY_RULES)), file=sys.stderr)
        return 2
    entries, laws = sources_for_families(reg, s2l, fams)
    print(f"CATEGORY {category.upper()} -> families {fams}")
    print(f"\nSources (priority-ordered, deep-inspected first) — {len(entries)} candidates:")
    for e in entries[:14]:
        insp = f"{e['inspection_status']}({e['inspected_files']})" if e["inspected_files"] else e["inspection_status"]
        print(f"  {e['priority']}  {e['repository']:44s} {e.get('license', '?'):22s} {insp}")
    print(f"\nSemantic laws with fetched evidence — {len(laws)}:")
    for l in laws:
        print(f"  {l['law_id']:20s} {l['source']['repository']:40s} `{l['source']['path']}`")
        print(f"      {l['statement'][:150]}...")
    if want_laws:
        print(json.dumps(laws, indent=1)[:4000])
    print("\nNEXT STEPS (S94 §25 / §13):")
    print("  1. inspect the upstream file AND its tests (paths in registry + findings.jsonl)")
    print("  2. port the test before implementing (license: check reuse_class)")
    print("  3. implement the smallest semantic law; add a fixture; verify against the real APK")
    print("  4. record provenance: commit SHA + file SHA256 from this lookup")
    return 0


def from_failure_map(path):
    fm = json.loads(Path(path).read_text())
    reg, s2l = load()
    print(f"FAILURE MAP: {path}")
    for title, cats in sorted(fm.items()):
        uniq = sorted(set(cats))
        print(f"\n=== {title}: {uniq}")
        for c in uniq:
            fams = CATEGORY_RULES.get(c, [])
            if not fams:
                print(f"  {c}: NO RULE — classify manually (S94 §14)")
                continue
            entries, laws = sources_for_families(reg, s2l, fams)
            top = [e["repository"] for e in entries[:3]]
            print(f"  {c} -> families {fams}")
            print(f"     consult first: {', '.join(top)}")
            for l in laws[:2]:
                print(f"     law {l['law_id']}: {l['source']['path']}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("category", nargs="?", help="failure category e.g. WRONG_COLOR")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--laws", action="store_true", help="dump full law records")
    ap.add_argument("--from-failure-map", dest="fmap", help="classify every title in a failure map")
    a = ap.parse_args()
    if a.fmap:
        sys.exit(from_failure_map(a.fmap))
    if not a.category:
        ap.print_help()
        sys.exit(1)
    sys.exit(lookup_category(a.category, want_laws=a.laws))


if __name__ == "__main__":
    main()
