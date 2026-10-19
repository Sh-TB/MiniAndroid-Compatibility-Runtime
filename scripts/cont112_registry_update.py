#!/usr/bin/env python3
"""CONT-112: update root_registry.json + canonical mirror with wave results.

Wave: the F-NEW-448 layer-2 chain (chess Toolbar 1080x0) resolved through
FIVE new roots:
- F-NEW-454  framework-package style-bag routing (apply_style table law)
- F-NEW-454b folded into 454: theme style-reference raw law (a style entry
  is a BAG, not a value — Theme resolve_attribute deref guard)
- F-NEW-455  TypedArray dimension reader pointer-deref law (REFERENCE/
  ATTRIBUTE slots deref to the terminal dimension before conversion)
- F-NEW-456  virtual dispatch starts at the receiver's RUNTIME class
  (heap object class, not the static reference type)
- F-NEW-457  obtainStyledAttributes producer recs-scan ordering (the scan
  must precede the xml-style extraction; stage-2 never fired before)
- F-NEW-458  android:minWidth/minHeight TRUE ids 0x0101013F/0x01010140
  (CONT-111's 0x01010150/51 matched no real bag key) + android:style
  rec-id law 0x01010000 (ns-less style attr dropped from the store)
- F-NEW-448  layer-2 CLOSED: chess Toolbar 1080x168 with the version text;
  app A/B bracket b270ff04 (1080x0) -> a0319686 (1080x168).

Registry: 768 -> 773 (id-unique both ways).
"""
import json, sys

DATE = '2026-10-20'

main_path = 'root_registry.json'
mirror_path = 'canonical/root_cause_registry.json'
main_reg = json.load(open(main_path))
mirror = json.load(open(mirror_path))

def find(reg, rid):
    for i, r in enumerate(reg):
        if r['id'] == rid:
            return i
    return -1

t454 = ("F-NEW-454 (CONT-112) ROOT-CAUSED-FIXED — two stacked laws. (a) "
        "FRAMEWORK-PACKAGE STYLE ROUTING: AOSP AssetManager2 routes a style "
        "reference to the package its id names (app 0x7f -> APK table, "
        "android 0x01 -> framework-res); LayoutInflater::apply_style "
        "resolved ONLY the app table, so framework-package style ids "
        "silently dropped their bags. Now table-parametric (walk_style_table "
        "over arsc_router().fw, parent chain included, env-gated "
        "MINIANDROID_FW_STYLE_DIAG). (b) THEME STYLE-REFERENCE RAW LAW: "
        "Theme::resolve_attribute dereferenced ANY reference — a "
        "toolbarStyle->@style/Widget.Material3.Toolbar answer deref'd to the "
        "style entry's single-value compat slot (complex_items[0]) — live "
        "chess 298: toolbarStyle=?attr resolved to @android:color "
        "0x106000d, the style= walk silently missed. The AOSP law (the "
        "resolve_attr_raw contract in-tree): a style entry is a BAG, not a "
        "value — deref VALUE references only; complex (bag) targets stay "
        "raw so the style= walk loads the real bag.")
e454 = ("run/c112/chess_diag.log + run/c112/chess_res_dump.txt + "
        "run/c112/chess_fw.log + run/c112/chess_fix6.log + "
        "run/c112/c449.log + evidence/cont112/evidence.json")

t455 = ("F-NEW-455 (CONT-112) ROOT-CAUSED-FIXED — TypedArray dimension "
        "reader pointer-deref law. AOSP TypedArray.getDimensionPixelSize/"
        "getLayoutDimension accept a TypedValue that may be a POINTER "
        "(TYPE_REFERENCE / TYPE_ATTRIBUTE) to the terminal dimension. The "
        "F-NEW-450 producer stores the RAW typed word; a slot resolved "
        "through the theme/style stages can carry a REFERENCE or ATTRIBUTE "
        "word the reader passed through UNRESOLVED. Live evidence (jwtc "
        "chess 298): ActionBarOverlayLayout$LayoutParams.<init> read "
        "android:layout_height = ?attr/actionBarSize stored as the raw "
        "ATTRIBUTE word 0x7f040006 -> setLayoutParams height=2130968582 -> "
        "EXACTLY(0x3f040006) child spec -> Toolbar overflow "
        "([F-NEW-327-READ] getLayoutDimension idx=13 present=1 "
        "val=2130968582 caller=Ll/e3;.<init>). Fix: the reader derefs the "
        "pointer chain (ATTRIBUTE hops through the theme, REFERENCE hops "
        "through the package-routed ARSC, <=8 hops) THEN converts "
        "DIMENSION-typed terminals.")
e455 = ("run/c112/chess_fix4.log + run/c112/chess_fix5.log + "
        "run/c112/chess_fix6.log + run/c112/c449.log")

t456 = ("F-NEW-456 (CONT-112) ROOT-CAUSED-FIXED — ART virtual dispatch "
        "resolves on the receiver's RUNTIME class, not the static type of "
        "the reference. The C013-HIER shadow walk started at args[0]."
        "class_desc (the STATIC type): a Context-typed variable holding the "
        "Activity (every (Context, AttributeSet) view ctor passes the "
        "activity as Context) died at Landroid/content/Context; (no DEX "
        "super entry) and the ActivityShadow producer never ran. Fix: the "
        "walk starts from the heap object's runtime class (get_object_class) "
        "when resolvable. Probe-visible only after this: DerefView's "
        "obtainStyledAttributes reached [EXP088-B-DISPATCH] + the "
        "[F-NEW-175] producer ([TAG-ENTRY] bridge_to_api trace).")
e456 = ("run/c112/c449_t3.log + run/c112/c449_t4.log + run/c112/c449.log")

t457 = ("F-NEW-457 (CONT-112) ROOT-CAUSED-FIXED — obtainStyledAttributes "
        "producer recs-scan ORDERING. The ContextShadow producer scanned the "
        "ctx args for the AttributeSet marker AFTER f327_xml_style was "
        "computed, so xml_recs was still nullptr at the extraction point and "
        "the F-NEW-327 stage-2 (tag XML style=) walk NEVER fired from the "
        "shadow producer for ANY APK. Live evidence (c449 probe): the marker "
        "arrived with 4 recs ([F457-INSTALL] view=19 recs_in=4 recs_store=4) "
        "while xmlstyle stayed 0x0 and both styleable slots resolved "
        "present=0; the engine-side S101 producer (dalvik_engine.cpp) already "
        "had the correct order. Fix: the recs scan moved above the xml-style "
        "extraction in the shadow producer.")
e457 = ("run/c112/c449_t9.log + run/c112/c449_t10.log + run/c112/c449.log")

t458 = ("F-NEW-458 (CONT-112) ROOT-CAUSED-FIXED — two framework attr-id "
        "laws verified against the aapt2/linker authority. (a) android:"
        "minWidth = 0x0101013F and android:minHeight = 0x01010140 (compiled "
        "<item name=\"android:minHeight\"> with aapt2 -I android-34.jar "
        "twice: the ground truth). The CONT-111 bag-tier ids "
        "(0x01010150/51) matched NO real bag key — every style/theme-bag "
        "android:min* item was silently unconsumed (the chess Toolbar's "
        "Base.Widget.AppCompat.Toolbar ancestor bag carries "
        "android:minHeight=?attr/actionBarSize and the walk never seeded "
        "it). (b) the ns-less android:style attribute carries NO "
        "resource-map id (aapt2 xmltree: 'A: style=@0x...' with no id in "
        "parens) — the rec build's attr_resid==0 gate dropped it from every "
        "AttributeSetStore record set; assigned the AOSP public-final id "
        "0x01010000 in the AXML parser.")
e458 = ("run/c112/idprobe + run/c112/chess_res_dump.txt + "
        "fixtures/cont112_lawderef/res/values/styles.xml + run/c112/c449.log")

t448 = ("F-NEW-448 (CONT-112) ROOT-CAUSED-FIXED — layer-2 CLOSED. The chess "
        "Toolbar chain resolved through five stacked roots (454/455/456/457/"
        "458, this registry). The theme's toolbarStyle now reaches the M3 "
        "Toolbar style bag RAW (454b), its parent chain's "
        "android:minHeight=?attr/actionBarSize item seeds "
        "node.min_height=168 (458 + the CONT-111 family), the lp ctor's "
        "layout_height pointer derefs to 168 (455), and Toolbar.onMeasure's "
        "getSuggestedMinimumHeight() (DEX decode @1126-1134, "
        "cont112_toolbar_disasm.py) floors the chain: Toolbar 1080x168 with "
        "the version text rendered. APP A/B BRACKET: pre-fix binary "
        "(fresh worktree at origin/main 96bcb963, 62df609a) Toolbar 1080x0 "
        "face b270ff040b3601dc -> post-fix (623827ee+) Toolbar 1080x168 "
        "face a0319686d56ff5c0. PROBE c449 (fixtures/cont112_lawderef, "
        "real aapt2/ECJ/D8, sha16 90420f5a2d87ba20): 4/4 post-fix vs 0/4 "
        "pre-fix (FLOOR-MIN 168, FLOOR-MEASURE 168, DEREF-REF 168, "
        "DEREF-ATTR 168). Full battery green: wall 12/12 byte-identical, "
        "c448 7/7, c74esc 7/7, goldens/negatives/reinstall/MG-310/MG-150/"
        "selftests rc=0.")
e448 = ("run/c112/battery.log + run/c112/chess_pre.log + "
        "run/c112/chess_final.log + run/c112/c449_pre.log + "
        "run/c112/c449.log + scripts/cont112_toolbar_disasm.py + "
        "evidence/cont112/evidence.json")

new_roots = [
    {"id": "F-NEW-454", "title": "Framework-package style routing missing in apply_style + theme style-reference deref'd like a value",
     "status": "ROOT-CAUSED-FIXED", "priority": "P0-CRITICAL", "layer": "RESOURCES",
     "date": DATE, "root_cause": t454, "evidence": e454},
    {"id": "F-NEW-455", "title": "TypedArray dimension readers pass REFERENCE/ATTRIBUTE slots through unresolved",
     "status": "ROOT-CAUSED-FIXED", "priority": "P0-CRITICAL", "layer": "RESOURCES",
     "date": DATE, "root_cause": t455, "evidence": e455},
    {"id": "F-NEW-456", "title": "Shadow hierarchy dispatch starts at the static reference type instead of the receiver runtime class",
     "status": "ROOT-CAUSED-FIXED", "priority": "P1-HIGH", "layer": "RUNTIME",
     "date": DATE, "root_cause": t456, "evidence": e456},
    {"id": "F-NEW-457", "title": "obtainStyledAttributes producer recs-scan runs after the xml-style extraction (stage-2 dead)",
     "status": "ROOT-CAUSED-FIXED", "priority": "P0-CRITICAL", "layer": "RESOURCES",
     "date": DATE, "root_cause": t457, "evidence": e457},
    {"id": "F-NEW-458", "title": "android:minWidth/minHeight/style framework attr ids wrong or missing (0x0101013F/0x01010140/0x01010000)",
     "status": "ROOT-CAUSED-FIXED", "priority": "P0-CRITICAL", "layer": "RESOURCES",
     "date": DATE, "root_cause": t458, "evidence": e458},
]

for reg, path in ((main_reg, main_path), (mirror, mirror_path)):
    for nr in new_roots:
        if find(reg, nr["id"]) == -1:
            reg.append(dict(nr))
    # F-NEW-448 refresh
    i = find(reg, "F-NEW-448")
    if i >= 0:
        reg[i]["status"] = "ROOT-CAUSED-FIXED"
        reg[i]["priority"] = "P0-CRITICAL"
        reg[i]["date"] = DATE
        reg[i]["root_cause"] = t448
        reg[i]["evidence"] = e448

ids_m = [r["id"] for r in main_reg]
ids_f = [r["id"] for r in mirror]
assert len(ids_m) == len(set(ids_m)), "main not id-unique"
assert len(ids_f) == len(set(ids_f)), "mirror not id-unique"
json.dump(main_reg, open(main_path, "w"), indent=1, ensure_ascii=False)
json.dump(mirror, open(mirror_path, "w"), indent=1, ensure_ascii=False)
print("main:", len(main_reg), "mirror:", len(mirror))
for rid in ("F-NEW-454", "F-NEW-455", "F-NEW-456", "F-NEW-457",
            "F-NEW-458", "F-NEW-448"):
    print(rid, "->", find(main_reg, rid))
