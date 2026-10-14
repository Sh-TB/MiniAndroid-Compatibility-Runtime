#!/usr/bin/env python3
"""cont66_evidence.py — assemble CONT-66 evidence bundle + registry entries."""
import json, os, shutil, hashlib

BASE = '/home/z/my-project'
EV = f'{BASE}/evidence/cont66'
os.makedirs(EV, exist_ok=True)

# 1) copy the wave's visual evidence
files = {
    'bmi_face_fixed.png': f'{BASE}/run/cont66/bmi_fix/screenshot.png',
    'bmi_boxes_measure.txt': None,   # written below
    'microtimer_pair.png': f'{BASE}/run/cont66/microtimer_pair.png',
    'simplecalc_pair.png': f'{BASE}/run/cont66/simplecalc_pair.png',
    'faces_strip.png': f'{BASE}/run/cont66/survey/faces_strip.png',
    'pixel_census.json': f'{BASE}/run/cont66/survey/pixel_census.json',
    'click_audit_simplecalc.jsonl': f'{BASE}/run/cont66/click_audit.jsonl',
}
for dst, src in files.items():
    if src and os.path.exists(src):
        shutil.copy(src, f'{EV}/{dst}')

with open(f'{EV}/bmi_boxes_measure.txt', 'w') as f:
    f.write("""CONT-66 W1 — BMI v402 geometry, measured (screen 1080x1920, density 2.625)

XML ground truth (aapt2 xmltree fragment_bmimain.xml):
  root RelativeLayout padding L/R = @dimen/activity_horizontal_margin = 16dp = 42px
                                  T/B = @dimen/activity_vertical_margin   = 16dp = 42px

BEFORE F-NEW-360 (face fb7c45d12014e366, binary 6aa564676ee687f9):
  RL-TRACE cached edges: EditText r1080, Button r1080, Spinner l0, TextView l0
  pixels: blue button col-run 726..1078 (flush right), spinner glyphs start x=4
  rightmost non-bg column: 1079 of 1080

AFTER F-NEW-360 (face f45d6c6603e93fc5, binary 461925acd98f6232):
  RL-TRACE cached edges: EditText l775 r1038, Button l683 r1038,
                         Spinner l42, TextView l42 (t84 -> t126 = padding_top+margin)
  pixels: blue button col-run 684..1036, spinner glyphs start x=46,
  rightmost non-bg column: 1037 of 1080  (= 1080 - 42 + 1 antialiasing)
""")

# 2) registry entries
reg_path = f'{BASE}/root_registry.json'
reg = json.load(open(reg_path))
roots = reg['roots']
existing = {r.get('id') for r in roots}

new_entries = [
 {
  "id": "F-NEW-360",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P1",
  "layer": "resources/layout-inflater (TypedValue dimension-reference law)",
  "title": "DIMENSION-REFERENCE RESOLUTION LAW (CONT-66): aapt2 compiles every dimension attribute referencing a dimen entry (padding*, layout_margin*, textSize, maxWidth/Height, elevation, ConstraintLayout guideline offsets, shape-drawable dims, layout_width/height) as a typed REFERENCE (data word = resource id; raw string empty or '@dimen/name'). parse_dim_attr had NO is_reference() branch (its sibling parse_color_attr DID) — the dimension path silently answered 0, and resolve_size_or_match fell through the empty-string sentinel to wrap_content (-2). Measured face evidence: BMI v402 root RelativeLayout padding @dimen/activity_horizontal_margin (16dp=42px) collapsed to 0 — spinner glyphs x=4 (should be 46), EditText/Button cached right=1080 flush with the screen edge (should be 1038); simplecalc v8 result TextView textSize @dimen/display_text_size (40sp) answered 0 (renderer default) and padding @dimen/activity_margin (16dp) answered 0. FIX: (a) parse_dim_attr gains the canonical TypedValue branch — is_reference() -> arsc_.resolve_value(ref_id) -> is_dimension() -> complex_to_dimension_pixel_size (the ONE GOLDEN-03 §9 conversion path); (b) textSize gate widened to is_dimension() || is_reference(); (c) resolve_size_or_match gains the same reference branch (resolved dimension = px size; resolved int passes -1/-2 through). Three real-app pixel verifications: BMI form now 42px-inset (rightmost ink 1079->1037, glyphs x=4->46); simplecalc display '0' at 40sp with 16dp padding; microtimer marginTop 2.5dp applied (keypad block 6px shift). 36/36 anchor wall re-run: 9 anchors byte-identical x3, 2 anchors changed deterministically x3 and adjudicated XML-TRUE (microtimer 55343bbec712618d->bbd350b6c14fbd52, simplecalc 341b9cec89d8f182->2ac5d8d0cbf9552a), dooz180 c94da5a928ea213b x3 MATCH.",
 },
 {
  "id": "F-NEW-361",
  "status": "ROOT-CAUSED-FIXED",
  "priority": "P1",
  "layer": "resources/layout-inflater (API-26 MarginLayoutParams axis margins)",
  "title": "AXIS-MARGIN PARSING LAW (CONT-66): layout_marginHorizontal (0x0101053b) and layout_marginVertical (0x0101053c) — the API-26 MarginLayoutParams axis forms (AOSP ViewGroup.MarginLayoutParams(c,attrs): marginHorizontal sets leftMargin=rightMargin, marginVertical sets topMargin=bottomMargin, explicit single-edge margins win over the axis forms) — were NEVER parsed; axis-margined rows laid out full-width. Measured: microtimer v8 keypad rows carry layout_marginHorizontal=@dimen/button_margin_out (2.5dp=6.56px) — old face rows spanned x=0..1079 with 360px buttons (=1080/3), XML truth is 7px side insets with 356px buttons. FIX: the two attr names added beside the margin* family (ml=mr=v / mt=mb=v, margin_set=true). Pixel-verified post-fix: keypad rows x=7..1072. Named residual (documented): AOSP resolves the axis-vs-single precedence by TYPE after reading ALL attrs, not by XML file order; the corpus has no conflicting single+axis files. Same 36/36 wall as F-NEW-360 (the two laws shipped in one binary).",
 },
 {
  "id": "F-NEW-362",
  "status": "ROOT-CAUSED-PARTIAL",
  "priority": "P1",
  "layer": "dex/view-input chain (tap -> click -> listener -> calculator core)",
  "title": "DIGIT-INPUT CHAIN DECODE (CONT-66, the 'in-app calculator typing' lane): the tap pipeline is LIVE end-to-end through 5 verified hops — --tap hit-test (DOWN target=176, the '7' Button), PerformClick queued+drained (G06-TOKEN click_dispatched=true), the butterknife debounce wrapper (enabled=1 read via SGET, ENABLE_AGAIN unlock posted from inside onClick before the handler call), listener y.a(View)->MainActivity.numpadClick(View) (click_audit dispatch_ok=true), numpadClick->getId->a(int)->sget static calculator instance->b.b(id). The chain DIES in the calculator core's first numeric recompute: b.b D (getValue) = Double.parseDouble(d.a(a())) where d.a(String)=replaceAll(\",\",\"\")+parseDouble — received \"\" and threw NumberFormatException('For input string: \"\"') at calculator/d;.a pc=8, propagated as APP BOUNDARY unwind (MainActivity.onCreate invoke_pc=30 record), NO setText followed, face byte-identical (frames f25b754c4565c38b/2ac5d8d0cbf9552a unchanged). The state field f@3245 SHOULD hold \"0\" (the V-ctor b.<init> VL calls a(\"0\") — verified live by the launch [EXP091-SETTEXT] view_id=168 text=\"0\"), so the reset-to-empty between ctor and click is the named next decode hop: b.b VI's 112-ins numpadPressed body (k() re-entry / clear-path branch) — S26-disasm tool's opcode table is off-by-one for 0x5b-0x5e family (documented; cont66_dex.py supersedes it). Adjudicated NOT-A-GAP (existing laws verified live): View setTag/getTag M3 FINDING-011 law exists and is complete (zero setTag calls in simplecalc's launch — the digit value never rode tags); butterknife debounce enabled-flag was true; XML onClick handler dispatch fine (OpenCalc path: XML_CLICK keyDigitPadMappingToDisplay DISPATCHED — the empty OpenCalc display at launch is the app's OWN state, XML text=\"\" everywhere).",
 },
]
for e in new_entries:
    if e['id'] not in existing:
        roots.append(e)
reg['total_roots'] = len(roots)
if 'count' in reg: reg['count'] = len(roots)
json.dump(reg, open(reg_path, 'w'), ensure_ascii=False, indent=1)
print('registry:', len(roots), 'roots; appended', [e['id'] for e in new_entries if e['id'] not in existing])

# 3) evidence JSON
ev = {
  "wave": "CONT-66",
  "head": "6bf640b9",
  "binary_fixed": hashlib.sha256(open(f'{BASE}/miniandroid/build/miniandroid','rb').read()).hexdigest()[:16],
  "laws": [e['id'] for e in new_entries],
  "gate": {
     "wall": {"MATCH": ["csw","dooz","flappycow","g2048","gmdice","opencalc","tanana","tttdeluxe","unote"],
              "REPIN_XML_TRUE": {"microtimer": ["55343bbec712618d","bbd350b6c14fbd52"],
                                  "simplecalc": ["341b9cec89d8f182","2ac5d8d0cbf9552a"]}},
     "dooz180": "c94da5a928ea213b x3 MATCH",
     "runs": "36 (33 wall + 3 dooz180), all deterministic"
  },
  "bmi": {"before": "fb7c45d12014e366", "after": "f45d6c6603e93fc5",
          "rightmost_ink": [1079, 1037], "glyph_x": [4, 46]},
  "input_chain": {"tap": "135,1061@3 / 149,1037@3", "click_audit": "dispatch_ok=true ins=53",
                   "throw": "NumberFormatException For input string \"\" at calculator/d;.a pc=8"}
}
json.dump(ev, open(f'{EV}/cont66_evidence.json','w'), indent=1)
print('evidence written to', EV)
