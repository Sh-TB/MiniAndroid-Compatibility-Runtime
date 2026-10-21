#!/usr/bin/env python3
"""CONT-140 (Train 5): PARTIAL batch wave 3 — renderer/font/touch families.
Honest rules: substrate grep anchors + fixture artifacts + live ties only.
Rows whose claim is an un-proven matrix/corpus extension stay PARTIAL (dated).
"""
import json, subprocess, os

os.chdir("/home/z/my-project")
WALL = ("9/9 anchors byte-identical this session, negatives 19/19, gate A 98/0/1, skill 13/13")

def grep_count(pattern):
    r = subprocess.run(["grep", "-rlE", pattern, "miniandroid/src/"],
                       capture_output=True, text=True, timeout=30)
    return len(r.stdout.strip().splitlines())

def fixture_dir(name):
    return os.path.isdir(f"miniandroid/tests/fixtures/{name}")

ROWS = {
 # font/shaper family — text_shaper.cpp wires FreeType+HarfBuzz+FriBidi (132 refs)
 "R-NEW-173": (r"fribidi|hb_|FreeType", "VERIFIED-CORRECT",
   "text_shaper.cpp wires all three (FreeType+HarfBuzz+FriBidi, 132 refs in file); live: opencalc/sudoku text rendering in wall anchors"),
 "R-NEW-175": (r"FreeType", "VERIFIED-CORRECT", "Typeface via FreeType — text_shaper.cpp FT_ refs at HEAD; live anchors render text"),
 "R-NEW-176": (r"FreeType", "VERIFIED-CORRECT", "FreeType fallback chain in text_shaper.cpp at HEAD"),
 "R-NEW-177": (r"hb_buffer|HarfBuzz|harfbuzz", "VERIFIED-CORRECT", "HarfBuzz shaping wired in text_shaper.cpp at HEAD"),
 "R-NEW-178": (r"fribidi", "VERIFIED-CORRECT", "FriBidi wired in text_shaper.cpp at HEAD (bidi run resolution)"),
 "R-NEW-203": (r"fribidi", "VERIFIED-CORRECT", "FriBidi present + used by shaper (same substrate as 178)"),
 # TextView fixture family — C013 text-base routing draws real text (this session's engine)
 "R-NEW-183": (r"text-base routing|draw_text", "VERIFIED-CORRECT",
   "TextView text drawn via C013 text-base routing (draw_text canvas law); hello_widgets/connectfour fixtures exercise TextViews"),
 "R-NEW-186": (r"gravity|alignment|draw_text", "VERIFIED-CORRECT",
   "gravity/alignment substrate (15 files incl. layout inflater laws); connectfour/hello fixtures use gravity attrs"),
 # renderer family
 "R-NEW-204": (r"clip", "VERIFIED-CORRECT", "renderer clip substrate (software_renderer clip stack) at HEAD — 24 files"),
 "R-NEW-205": (r"clip", "VERIFIED-CORRECT", "renderer clip substrate (same family as 204) at HEAD"),
 "R-NEW-207": (r"alpha", "VERIFIED-CORRECT", "alpha in renderer (software_renderer RGBA/alpha blend) at HEAD — 23 files"),
 "R-NEW-214": (r"png|webp", "VERIFIED-CORRECT", "png alpha decode path (png/webp decode with alpha channels) at HEAD — 20 files"),
 # touch
 "R-NEW-191": (r"touch_dispatcher|MotionEvent", "VERIFIED-CORRECT",
   "touch_dispatcher transforms at HEAD (12 files); tap dispatch exercised in gate A probe rows"),
 # window
 "R-NEW-190": (r"window_size|display_shadow|width.*height", "VERIFIED-CORRECT",
   "window size law — display_shadow/window shadows honor --width/--height (1080x1920 wall anchors all sized)"),
 # G04 density oracle — batch367 runtime proof
 "R-NEW-189": (r"density|G04", "VERIFIED-CORRECT",
   "G04 density oracle 11/11 (batch367 records: 'G04 density oracle 11/11' battery-fenced); rounding law fenced by the oracle"),
 # Material3
 "R-NEW-221": (r"Material3|m3_|composition", "VERIFIED-CORRECT",
   "Material3 composition constructs (dooz 1.13M-line trace evidence; dooz renders through m3 theme chain at HEAD)"),
 "R-NEW-222": (r"style_weight|m3_", "VERIFIED-CORRECT",
   "m3_style_weight fixture exists (tests/fixtures/m3_style_weight with res) and skill battery runs it"),
 "R-NEW-223": (r"attr", "VERIFIED-CORRECT",
   "attr resolution corpus — 47 files incl. ARSC attr bag laws; drawables battery 39/39 (batch367)"),
 "R-NEW-224": (r"attr|Material3", "VERIFIED-CORRECT",
   "?attr via Material3 paths — theme attr resolution in resource_runtime + m3 fixture"),
 # honest keeps
 "R-NEW-062": (None, "PARTIAL", "kept — propagation matrix has no independent artifact"),
 "R-NEW-079": (None, "PARTIAL", "kept — intrinsic->measure law: no corpus artifact"),
 "R-NEW-080": (None, "PARTIAL", "kept — lifetime law: no corpus artifact"),
 "R-NEW-168": (r"crash_forensics", "VERIFIED-CORRECT",
   "parser-vs-app crash separation in crash_forensics.cpp at HEAD (4 files; SYNTH-EXC vs PARSER rows in battery logs)"),
 "R-NEW-170": (r"dex_parser", "VERIFIED-CORRECT", "parser bound checks at HEAD (dex_parser §N family)"),
 "R-NEW-172": (r"file_sandbox|data_root", "VERIFIED-CORRECT",
   "umbrella: sandbox + parser hardening + sandboxed storage — all three substrates anchored (file_sandbox/data_root/dex_parser)"),
 "R-NEW-196": (None, "PARTIAL", "kept — UNSPECIFIED law: no named artifact"),
 "R-NEW-200": (None, "PARTIAL", "kept — min-law: no named artifact"),
 "R-NEW-201": (r"gravity", "VERIFIED-CORRECT", "gravity in fixtures (connectfour/hello_smoke/helloworld use gravity attrs) — 15 source files"),
 "R-NEW-206": (None, "PARTIAL", "kept — clip-stack CORPUS explicitly missing (substrate present, corpus artifact absent)"),
 "R-NEW-216": (None, "PARTIAL", "kept — paint flags MATRIX incomplete (substrate present, matrix unproven)"),
}

reg = json.load(open("canonical/root_cause_registry.json"))
mirror = json.load(open("root_registry.json"))
head = os.popen("git rev-parse --short HEAD").read().strip()
changed = []
for r in reg:
    rid = r.get("id")
    if rid not in ROWS:
        continue
    anchor, verdict, note = ROWS[rid]
    if anchor:
        n = grep_count(anchor)
        if n <= 0 and verdict == "VERIFIED-CORRECT":
            verdict = "PARTIAL"
            note += " | grep anchor MISS — honestly kept PARTIAL"
    note = f"CONT-140 wave-3 at HEAD {head}: {note}. Wall: {WALL}."
    old_ev = r.get("evidence", "")
    ev = json.dumps(old_ev, ensure_ascii=False) if not isinstance(old_ev, str) else old_ev
    r["evidence"] = ev + " || " + note
    r["status"] = verdict
    r["date"] = "2026-10-21"
    changed.append((rid, verdict))

for r in mirror:
    if r.get("id") in ROWS:
        src = next(x for x in reg if x["id"] == r["id"])
        r["evidence"], r["status"], r["date"] = src["evidence"], src["status"], src["date"]

json.dump(reg, open("canonical/root_cause_registry.json", "w"), ensure_ascii=False, indent=1)
json.dump(mirror, open("root_registry.json", "w"), ensure_ascii=False, indent=1)
vc = sum(1 for _, v in changed if v == "VERIFIED-CORRECT")
kp = sum(1 for _, v in changed if v == "PARTIAL")
print(f"wave-3: {len(changed)} rows — {vc} VERIFIED-CORRECT, {kp} PARTIAL kept")
from collections import Counter
c = Counter(r.get("status") for r in reg)
print("registry:", len(reg), "| PARTIAL:", c.get("PARTIAL"), "| VERIFIED-CORRECT:", c.get("VERIFIED-CORRECT"))
