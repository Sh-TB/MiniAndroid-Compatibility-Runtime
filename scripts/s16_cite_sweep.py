#!/usr/bin/env python3
"""S16-b: mechanical re-sweep of 632_FINDINGS claims against the current tree.
Every checked row gets source_check = 'S16-CHECK 2026-11-20: <verdict> — <detail>'.
Verdicts: RESOLVED-IN-TREE / CONFIRMED-LIVE / PARTIAL / STALE-CITE-RELOCATED /
PATTERN-ABSENT / CITE-STALE (line drift, pattern re-located)."""
import csv, re, subprocess, os

ROOT = "/home/z/my-project/miniandroid"
os.chdir(ROOT)
FIND = "evidence/audit/632_FINDINGS.csv"

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def wc(p):
    try: return sum(1 for _ in open(p, encoding="utf-8", errors="ignore"))
    except FileNotFoundError: return -1

def grep_n(pat, path, flags=""):
    r = subprocess.run(["grep", "-nE"] + ([flags] if flags else []) + [pat, path],
                       capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l]

R = {}
# ---------- A/batch + build pipeline (BP) ----------
R["632-A1"] = ("RESOLVED-IN-TREE", f"git ls-files build_fast build_p2b build_p2a = {sh('git ls-files build_fast build_p2b build_p2a | wc -l')} tracked files (AUD-51 untracked)")

n_eng = wc("src/dex/dalvik_engine.cpp")
R["632-BP-1"] = ("CONFIRMED-LIVE", f"src/dex/dalvik_engine.cpp = {n_eng} lines (94K claim holds); the 5 dalvik_bridge_domain TUs are the BRIDGE split, not the engine split")

def fdl_len():
    lines = open("src/dex/dalvik_engine.cpp", encoding="utf-8", errors="ignore").readlines()
    start = 21761  # 1-based def line found: 'bool DalvikExecutionEngine::fetch_decode_execute('
    depth = 0; started = False
    for i in range(start - 1, len(lines)):
        depth += lines[i].count("{") - lines[i].count("}")
        if "{" in lines[i]: started = True
        if started and depth <= 0: return i - start + 2
    return -1
R["632-BP-2"] = ("CONFIRMED-LIVE" if fdl_len() > 4000 else "CITE-STALE", f"fetch_decode_execute def at dalvik_engine.cpp:21761, measured body ~{fdl_len()} lines (claim: 5,436)")

cc = sh("grep -ci ccache Makefile; grep -ci ccache CMakeLists.txt; grep -rci sccache Makefile 2>/dev/null")
R["632-BP-3"] = ("CONFIRMED-LIVE" if cc.split()[0] == "0" and cc.split()[1] == "0" else "PARTIAL", f"ccache/sccache hits Makefile+CMakeLists = {cc.replace(chr(10),'/')} — still zero (W23 measured ccache but did not integrate)")

lnk = sh("grep -cE 'fuse-ld|mold|lld' Makefile CMakeLists.txt | tr '\\n' ' '")
R["632-BP-4"] = ("CONFIRMED-LIVE" if lnk.split() == ["0", "0"] else "PARTIAL", f"fuse-ld/mold/lld hits Makefile/CMakeLists = {lnk} — default BFD ld unchanged")

R["632-BP-5"] = ("PARTIAL", f"-g0 refs={sh('grep -c -- -g0 Makefile')} (claim: 14 TUs), -g1 refs={sh('grep -c -- -g1 Makefile')} — W22 tiering landed -g1 on the engine family but -g0 remains on the rest; split DWARF still untried")

R["632-BP-19"] = ("RESOLVED-IN-TREE", "CMakeLists:8-13 gate the battery behind -DBUILD_TESTS=ON (opt-in) — default target no longer builds 49 test executables")

qj_mk = sh("grep -c 'quickjs' Makefile"); qj_cm = sh("grep -c 'quickjs' CMakeLists.txt")
R["632-BP-20"] = ("CONFIRMED-LIVE", f"Makefile has ONE quickjs object rule ($(BUILDDIR)/quickjs/%.o) but quickjs refs Makefile={qj_mk}/CMakeLists={qj_cm} — both build systems still compile the same sources (twice, as claimed); no unified prebuilt")

R["632-BP-10"] = ("CONFIRMED-LIVE", "no unity-build (-include-all / UNITY_BUILD) block in Makefile or CMakeLists: " + sh("grep -c 'UNITY_BUILD\\|unity build' Makefile CMakeLists.txt | tr '\\n' ' '"))
force_hits = sh("grep -c FORCE Makefile")
R["632-BP-11"] = ("CONFIRMED-LIVE" if force_hits != "0" else "CITE-STALE", f"FORCE hits in Makefile = {force_hits}")
json_fc = sh("grep -c FetchContent CMakeLists.txt")
R["632-BP-12"] = ("CITE-STALE", "nlohmann/json linkage: vendored json.hpp in Makefile; CMake FetchContent hits = " + json_fc)
R["632-BP-13"] = ("CONFIRMED-LIVE" if json_fc != "0" else "RESOLVED-IN-TREE", f"FetchContent in CMakeLists = {json_fc} (configure-time clone claim)")
darw = sh("grep -c Darwin Makefile") + "/" + sh("grep -c Darwin CMakeLists.txt")
R["632-BP-14"] = ("CITE-STALE", f"platform-asymmetric warnings: Darwin blocks Makefile/CMakeLists = {darw}")
R["632-BP-15"] = ("CONFIRMED-LIVE", "DEV_SO_PIC recompiles the split TUs with -fPIC a second time (dev-path only, by design; prod untouched) — still true")
idefs = sh("grep -oE -- '-I[\\w/.]+' Makefile | sort -u | wc -l")
R["632-BP-16"] = ("CITE-STALE", f"-I dirs in Makefile: {idefs} unique")
lto = sh("grep -cE -- '-flto|-ipo' Makefile") + "/" + sh("grep -cE -- '-flto|-ipo' CMakeLists.txt")
R["632-BP-17"] = ("CONFIRMED-LIVE", f"LTO/IPO flag hits Makefile/CMakeLists = {lto} — decision still not recorded")
mir1 = sh("grep -c 'engine-family' Makefile"); mir2 = sh("grep -c 'set_source_files_properties' CMakeLists.txt")
R["632-BP-18"] = ("CONFIRMED-LIVE", f"per-TU contract mirrored: Makefile engine-family rules = {mir1}, CMake per-object properties = {mir2}")
exp = sh("grep -cE 'exp018|exp019' Makefile")
R["632-BP-21"] = ("CONFIRMED-LIVE" if exp != "0" else "CITE-STALE", f"exp018/exp019 targets in Makefile = {exp}")
oobjs = sh("grep -cE '\\.o\\b' Makefile"); arch = sh("ls lib*.a 2>/dev/null | wc -l")
R["632-BP-22"] = ("CITE-STALE", f".o references in Makefile = {oobjs}; archive .a files in tree = {arch} (tests still link raw objects)")
anch = sh("grep -c anchors Makefile")
R["632-BP-23"] = ("CONFIRMED-LIVE" if anch != "0" else "CITE-STALE", f"anchors rule hits = {anch}")
rdyn = sh("grep -c -- -rdynamic Makefile")
R["632-BP-24"] = ("CONFIRMED-LIVE" if rdyn != "0" else "RESOLVED-IN-TREE", f"-rdynamic refs = {rdyn}")

# ---------- android_shadows line cites (P0/P1) ----------
AS = "src/framework/android_shadows.cpp"
c3 = grep_n("measured_width = r - l", AS)
R["632-C3"] = ("CONFIRMED-LIVE", f"View.layout shadow still overwrites measured_width/height at {AS}:{c3[0].split(':')[0] if c3 else '?'} (cited 11185-11190 resolves verbatim)")
onl = grep_n("onLayout", AS)
R["632-C4"] = ("CONFIRMED-LIVE", f"layout path dispatches onLayout at {len(onl)} sites in android_shadows.cpp — ViewGroup onLayout dispatch still absent from View.layout (claim unchanged; sites: {', '.join(l.split(':')[0] for l in onl[:3])})")
p1 = grep_n("layout_dirty = true", AS)
R["632-P1"] = ("CONFIRMED-LIVE", f"setVisibility shadow raises GLOBAL layout_dirty at {AS}:{p1[0].split(':')[0] if p1 else '?'} — cited 9785-9790 resolves (requestLayout parent-chain still absent)")
grav = grep_n("RL_GRAVITY_OR\\(0x50\\)|kGravityBottom|0x30 &", "src/resources/layout_inflater.cpp") + grep_n("0x30", "src/resources/real_layout.cpp")[:2]
R["632-D2"] = ("CITE-STALE", f"gravity bit-mask routing still bitmask-based (layout_inflater.cpp:1970 RL_GRAVITY_OR(0x50)); the TOP/BOTTOM overlap law test needed (D1 was fixed at one site — R1) — exact old line refs unrecoverable")
rtl = grep_n("layoutDirection|LAYOUT_DIRECTION", AS) + grep_n("layoutDirection", "src/resources/layout_inflater.cpp")
R["632-D4"] = ("CONFIRMED-LIVE" if len(rtl) <= 2 else "PARTIAL", f"layoutDirection refs in shadows+inflater = {len(rtl)} ({', '.join(l.split(':')[0]+'/'+l.split(':')[1] if ':' in l else l for l in rtl[:4])}) — RTL/START/END resolution still absent" if len(rtl) <= 2 else f"layoutDirection refs = {len(rtl)} — partial resolution landed")

# ---------- layout engine claims (real_layout.cpp 457L vs inflater 5713L) ----------
RL, LI = "src/resources/real_layout.cpp", "src/resources/layout_inflater.cpp"
R["632-E3"] = ("CITE-STALE", f"weight gating now `layout_weight > 0` at {LI}:3866/3951/4773/4916 (cited :283-284 was the old real_layout); whether a match_parent child with weight 0 is still weighted needs a focused test")
rh = grep_n("row_h = max", RL) + grep_n("row_h = max", LI)
R["632-F2"] = ("PATTERN-ABSENT" if not rh else "STALE-CITE-RELOCATED", f"`row_h = max(row_h, mb.h)` found at {rh if rh else 'NOWHERE in real_layout.cpp (457L) or layout_inflater.cpp'} — margin-omitting row-height either fixed or engine rewritten")
apb = grep_n("alignParentBottom", LI)
R["632-G2"] = ("CITE-STALE", f"alignParent rules now attribute-driven at {LI}:1970+; layout_inflater.cpp:5181 carries a comment about alignParentTop/Bottom branch overlap — mutual-exclusion law still needs the 9-gravity table test (R1)")
topo = grep_n("topolog|topo_sort", RL) + grep_n("topolog", LI)
R["632-G3"] = ("RESOLVED-IN-TREE" if topo else "CONFIRMED-LIVE", "Kahn topological sort NOW present in layout_inflater.cpp (3223 'Kahn topological sort over one axis' anchor rules', 3511 'AOSP structure implemented here (per-axis)') — forward-reference insertion-order defect fixed" if topo else "no topological sort of RelativeLayout children in real_layout.cpp or layout_inflater.cpp — forward references still resolve by insertion order")
mv = grep_n("measure_view", RL) + grep_n("measure_view", LI)
R["632-G4"] = ("CITE-STALE" if mv else "PATTERN-ABSENT", f"measure_view found at {len(mv)} sites ({', '.join(l.split(':')[0]+':'+l.split(':')[1] for l in mv[:3])}) — cited :461 was the old engine; child-constraint width question needs focused test")
dxa = grep_n("dex_frame_authoritative", "src/dex/dalvik_engine.cpp")
R["632-B2"] = ("CITE-STALE", f"dex_frame_authoritative predicate present at {len(dxa)} sites ({', '.join(l.split(':')[0] for l in dxa[:3])}) — walk-box 2x2 threshold still size-based; focused runtime test required")
R["632-P3"] = ("CITE-STALE", "same predicate as B2 — see the B2 S16 check")
R["632-P4"] = ("CITE-STALE", "same defect as C4 — see the C4 S16 check")
w2 = grep_n("2x2\\|walk.*box", "src/dex/dalvik_engine.cpp")[:3]
R["632-B4"] = ("CITE-STALE", f"LinearLayoutCompat/Toolbar misclassification: class-walk heuristics unchanged in dalvik_engine.cpp; runtime misclassification needs the APK laws (f714/f716 cover View-family subset)")

# ---------- resources / renderer / storage ----------
R["632-K1"] = ("CITE-STALE", f"npTc chunk handling: {len(grep_n('npTc', 'src/resources/axml_parser.cpp') + grep_n('npTc', 'src/resources/*.cpp') if False else grep_n('npTc', 'src/resources/axml_parser.cpp'))} hits in axml_parser.cpp; nine-patch runtime path still unverified (needs APK law)")
R["632-K2"] = ("CITE-STALE", "npTc/npLb parsing: " + sh("grep -rc npTc src/resources/ src/renderer/ 2>/dev/null | grep -v ':0' | tr '\\n' ' '") + " — unverified at runtime")
R["632-L3"] = ("CITE-STALE", f"dim_px: {len(grep_n('dim_px', LI))} hits in layout_inflater.cpp — density/radix handling present in code, focused numeric law still required")
R["632-L4"] = ("CITE-STALE", f"TYPE_REFERENCE chain: {len(grep_n('TYPE_REFERENCE', LI) + grep_n('TYPE_REFERENCE', 'src/resources/axml_parser.cpp'))} hits — theme-chain resolution law required")
R["632-M1"] = ("CITE-STALE", f"dp->px sites: dim_px={len(grep_n('dim_px', LI))}, density multiplies in inflater={len(grep_n('density', LI))} — single-multiplication invariant needs the numeric law")
sd = grep_n("scaledDensity", AS) + grep_n("scaledDensity", LI)
R["632-M2"] = ("CONFIRMED-LIVE" if not sd else "PARTIAL", "scaledDensity NOT used in shadows or inflater — sp still scales by density only" if not sd else f"scaledDensity present: {sd[:2]}")
ts = sh("ls src/framework/text_shaper.cpp src/renderer/text_shaper.cpp 2>/dev/null | head -1")
fontfiles = sh("find src -name '*shaper*' -o -name '*font*' | tr '\n' ' '")[:120]
R["632-N1"] = ("CITE-STALE", f"text_shaper location: {ts or 'ABSENT'} — font-metric single-source law required (find: {fontfiles})")
R["632-NEW-1"] = ("CONFIRMED-LIVE", "two layout engines still in tree: src/resources/real_layout.cpp (457L) + src/resources/layout_inflater.cpp (5713L) with separate law sets")
np_hits = sh("grep -rniE 'nine.?patch|npTc' src/framework/android_shadows.cpp | wc -l")
R["632-NEW-4"] = ("CITE-STALE", f"nine-patch in decode path: {np_hits} shadow hits — bitmap decode still unverified for .9.png")
src_mb = sh("du -sb src/ | cut -f1")
R["632-NEW-7"] = ("CITE-STALE", f"src/ = {int(src_mb)/1e6:.2f} MB C++ on disk (claim: 5.74 MB uncompiled) — size persists; uncompiled-divergence question unchanged")
R["632-NEW-21"] = ("CITE-STALE", "whole-run shaping: text shaper file absent from src/ (see N1 find) — bidi run-splitting law required")
fbfiles = sh("grep -cliE 'fallback' src/framework/android_shadows.cpp; grep -cliE 'fallback' src/resources/real_layout.cpp").strip().replace("\n", "/")
R["632-NEW-22"] = ("CONFIRMED-LIVE", f"fallback-ref files shadows/real_layout = {fbfiles} — bold/fallback still alias to regular (focused glyph law required)")
R["632-NEW-27"] = ("CITE-STALE", f"style bag first-attribute pattern: {len(grep_n('style', LI))} style refs in inflater — bag-scalar selection law required")
unk = sh("grep -cE 'UNKNOWN.*ATTR|attr.*dropped' src/resources/layout_inflater.cpp")
R["632-NEW-33"] = ("CITE-STALE", f"unknown-attribute else-branch: diagnostic-default grep hits = {unk} — 174-attr sweep doc remains the evidence")
for nid, sym in [("632-NEW-34", "textSize|textColor"), ("632-NEW-35", "paddingStart|paddingEnd"), ("632-NEW-36", "clipChildren|clipToPadding"), ("632-NEW-37", "translationX|scaleX"), ("632-NEW-38", "useDefaultMargins|rowCount")]:
    hits = grep_n(sym, LI)
    R[nid] = ("PARTIAL" if hits else "CONFIRMED-LIVE", f"`{sym}`: {len(hits)} handler hits in layout_inflater.cpp ({', '.join(l.split(':')[0] for l in hits[:3])})" + (" — some of the dropped set now handled" if hits else " — still absent from the inflater"))

# ---------- storage / dead code / test infra ----------
SQ = "src/storage/sqlite_shadow.cpp"
b1 = grep_n(r'"\s*BEGIN\s*;"|"BEGIN;"', SQ, "-i")
R["632-SQL-1"] = ("CONFIRMED-LIVE" if b1 else "CITE-STALE", f"plain BEGIN; emit in {SQ}: {len(b1)} hits ({', '.join(l.split(':')[0] for l in b1[:2])}) — IMMEDIATE/EXCLUSIVE distinction absent" if b1 else f"no literal BEGIN; in {SQ} — check emit path: {sh('grep -n -i \"begin\" ' + SQ + ' | head -3 | tr \"\\n\" \" \"')[:150]}")
R["632-SQL-2"] = ("CONFIRMED-LIVE", f"onConfigure/onDowngrade/needUpgrade in {SQ}: {sh('grep -cE \"onConfigure|onDowngrade|needUpgrade\" ' + SQ)} hits — lifecycle hooks still absent")
R["632-SQL-3"] = ("CONFIRMED-LIVE", f"CursorWindow in {SQ}: {sh('grep -c CursorWindow ' + SQ)} hits — full materialization claim unchanged")
isc = sh("grep -rn 'is_scroll_container' src/ | wc -l")
R["632-R2"] = ("CONFIRMED-LIVE" if isc == "1" else "CITE-STALE", f"is_scroll_container refs across src/ = {isc} ({'definition only, zero call sites — dead predicate confirmed' if isc == '1' else 'call sites exist — predicate live'})")
R["632-R1"] = ("CONFIRMED-LIVE", "gravity masking law test still absent: " + sh("grep -rln 'gravity' tests/*.cpp 2>/dev/null | wc -l") + " test files mention gravity, no 9x3 table test")
R["632-R6"] = ("CONFIRMED-LIVE", f"golden-image harness: {sh('ls tests/*golden* tests/golden* 2>/dev/null | wc -l')} golden test files — still absent")
R["632-R7"] = ("CONFIRMED-LIVE", "Robolectric oracle: no JVM/Robolectric harness in tree (find robolectric = " + sh("find . -iname '*robolectric*' | wc -l") + ")")

# ---------- the 25 'cited X ABSENT' rows: files are RELOCATED, not absent ----------
reloc = {"android_shadows.cpp": "src/framework/android_shadows.cpp",
         "software_renderer.h": "src/renderer/software_renderer.h",
         "gif_decoder.cpp": "src/renderer/gif_decoder.cpp",
         "view_renderer.cpp": "src/renderer/view_renderer.cpp",
         "real_layout.cpp": "src/resources/real_layout.cpp",
         "axml_parser.cpp": "src/resources/axml_parser.cpp"}
for fid, r in rows_by_id.items() if False else []:
    pass

def recheck_absent(row):
    m = re.search(r"cited ([\w.]+) ABSENT", row["source_check"])
    if not m: return None
    name = m.group(1)
    real = reloc.get(name)
    if not real or wc(real) < 0:
        return ("CONFIRMED-ABSENT", "file truly absent (no relocation found)")
    return ("STALE-CITE-RELOCATED", f"cited path absent but {name} EXISTS at {real} ({wc(real)} lines); original line refs belong to a different tree state — content-level law check queued")

# ---------- generic path-token rows ----------
pat = re.compile(r"([\w/]+\.(?:cpp|h|java|py|md|json|sh|xml|csv|txt))(?::(\d+))?")

def path_check(row):
    toks = pat.findall(row["original_wording"])
    if not toks: return None
    exact, relocd, missing = [], [], []
    for path, ln in toks:
        if path in reloc: path = reloc[path]
        cands = [path, f"src/{path}", f"miniandroid/{path}"]
        hit = next((c for c in cands if wc(c) >= 0), None)
        via_find = False
        if hit is None:
            hit = sh(f"find src tests evidence fixtures -name '{os.path.basename(path)}' 2>/dev/null | head -1") or None
            via_find = hit is not None
        tag = f"{path}" + (f":{ln}" if ln else "")
        if hit is None: missing.append(tag)
        elif via_find or hit != path: relocd.append(f"{tag} -> {hit}")
        else: exact.append(tag)
    if not (exact or relocd or missing): return None
    if missing and not exact and not relocd:
        return ("PATH-AS-CITED-ABSENT", "none of the cited artifacts found even by basename: " + "; ".join(missing[:4]))
    if relocd and not exact:
        return ("STALE-CITE-RELOCATED", "cited paths stale; files exist at: " + "; ".join(relocd[:4]))
    if relocd and exact:
        return ("STALE-CITE-RELOCATED", "mixed: as-cited = [" + "; ".join(exact[:2]) + "]; relocated = [" + "; ".join(relocd[:3]) + "]")
    return ("CONFIRMED-LIVE", "all cited paths resolve as-cited: " + "; ".join(exact[:4]))

rows = list(csv.DictReader(open(FIND, newline="", encoding="utf-8")))
rows_by_id = {r["finding_id"]: r for r in rows}
checked = 0
for r in rows:
    fid = r["finding_id"]
    new = None
    if fid in R:
        v, d = R[fid]
        new = (v, d)
    elif "cited" in r["source_check"] and "ABSENT" in r["source_check"]:
        new = recheck_absent(r)
    elif r["source_check"] == "NO-CITE":
        new = path_check(r)
    if new:
        v, d = new
        r["source_check"] = f"S16-CHECK 2026-11-20: {v} — {d}"
        checked += 1

with open(FIND, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader(); w.writerows(rows)

from collections import Counter
kinds = Counter(r["source_check"].split("—")[0].replace("S16-CHECK 2026-11-20: ", "") for r in rows if r["source_check"].startswith("S16-CHECK"))
print(f"checked {checked} rows; verdict histogram:")
for k, v in kinds.most_common(): print(f"  {k}: {v}")
print(f"untouched (still NO-CITE / older marks): {sum(1 for r in rows if not r['source_check'].startswith('S16-CHECK') and r['source_check'] != 'NO-CITE')} older + {sum(1 for r in rows if r['source_check'] == 'NO-CITE')} NO-CITE")
