#!/usr/bin/env python3
# cont39_registry.py — CONT-39 registry update: F-NEW-301 (the TextView
# color-state law — getCurrentTextColor answers the stored state exactly
# as the renderer paints it). Dedup-checked append, standing conventions.
import json, collections

P = '/home/z/my-project/root_registry.json'
d = json.load(open(P))
ids = {r.get('id') for r in d['roots']}
assert 'F-NEW-301' not in ids, 'F-NEW-301 already present — dedup check'

entry = {
  "id": "F-NEW-301",
  "title": "TextView color-state law: getCurrentTextColor() had NO shadow handler — the typed-default stub answered 0, so TextView.setTextColor(int) → getCurrentTextColor() never round-tripped (explicit colors, alpha, and recolor-between-draws all read back as 0)",
  "status": "ROOT_CAUSED_FIXED",
  "priority": "P1",
  "layer": "framework/view-text-color-state",
  "root_cause": "PROVEN BY THE STANDING colorpipe PROBE (fixtures/colorpipe_probe rows PC-01..04, the recorded CONT-38 checkpoint) + the [M3-SETTEXTCOLOR] trace: the setter side was ALREADY faithful — TextView.setTextColor(int) reaches the ViewShadow law (android_shadows.cpp, M3 FIX-M3-005b, ADDITIONAL-AUDIT P1-10 provenance) and stores the value on the ViewNode (text_color + text_color_provenance=EXPLICIT_RUNTIME; the trace shows all 7 probe calls stored the EXACT argb incl. the red→green change). The GETTER side had no law anywhere in the engine: rg 'getCurrentTextColor' src/ = zero matches pre-fix — every call fell through all shadows to the typed-default int stub and answered 0. PRE ×3 on the CONT-38 binary 80d9ea341f1b6ccc: PC-01 FAIL (getCurrentTextColor=0), PC-02 FAIL, PC-03 FAIL (alpha=0), PC-04 FAIL. AOSP law: TextView.getCurrentTextColor() returns mCurTextColor — the color the view's text actually paints with; setTextColor(int) sets it to EXACTLY the argument (ColorStateList.valueOf → updateTextColors → getColorForState default state), preserving alpha.",
  "fix": "ONE generic point in the ViewShadow (android_shadows.cpp, immediately after the setTextColor law, same state store): getCurrentTextColor() answers find_node(receiver).text_color when set (covers BOTH EXPLICIT_RUNTIME and STYLE_RESOLVED provenance), else mirrors the RENDERER's default law EXACTLY as view_renderer draw_text_into applies it — text_color==0 → opaque black 0xFF000000, Button-label (non-ImageButton) → white 0xFFFFFFFF — so a getter reader observes the same color the rasterizer paints (getter state and rendered pixels cannot diverge). A getter never creates render nodes (find_node only, no side effect). The ColorStateList variant's default-color resolution stays the recorded draw-time gap (text_color_state_object has no failing consumer; NOT value-guessed in the getter). Env-gated MINIANDROID_TEXT_COLOR_TRACE diag [F-301-GETTEXTCOLOR]. No name matching, no app branches. Build config: android_shadows.cpp hit the cc1plus -g OOM peak (dmesg, ~936 MB RSS) — the CONT-37 per-file -g0 Makefile precedent extended to this TU (same -O2, debug sections dropped).",
  "synthetic_probe": "fixtures/colorpipe_probe (com.probe.cpipe, real toolchain, 17 rows — ALREADY the standing battery): PC-01 explicit non-black round-trip, PC-02 explicit black is a valid requested color (the removed M3-007b heuristic would have broken it), PC-03 alpha preserved (no truncation to opaque), PC-04 color CHANGE between two draws on the SAME widget. PRE ×3 on 80d9ea341f1b6ccc: 13/4 (PC-01..04 FAIL with getCurrentTextColor=0) → POST ×3 on 111340a583d48d92: 17/0 (ff3366cc / ff000000 / 80ff8800 / ff0000→ff00ff00 all read back exactly). TR-01..08 + SC-01..05 unchanged PASS both binaries.",
  "evidence": "evidence/cont39/TEXT_COLOR_STATE.md; runs run/cont39/pre/{r1..3} (PRE) + run/cont39/post/{r1..3} (POST); scripts/cont39_pre.sh + cont39_post.sh",
  "not_claimed": "TextView.getTextColors() (the ColorStateList object getter) and the CSL default-color draw-time resolution remain honest untested scope (no failing consumer; the captured text_color_state_object is untouched). The law covers the View/ViewShadow path — the Compose path's color resolution is F-NEW-300's package-routed law (unaffected; composeStopwatch frame byte-stable through this wave).",
  "regression": "binary 111340a583d48d92: anchors 8/8 ×3 BYTE-IDENTICAL (dooz 31ddd4d5b8e6d18e, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622); composeStopwatch 3442d9a9dc0fa0f9 ×3 (F-NEW-300 state retained, zero drift); battery == CONT-28..38 records EXACTLY (fcol 140/0, f259 49/0, f259g 84/7-known, f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, ckey 15/0, fnew252 56/0, fnew290 56/0, fnew291 56/0, fnew292 70/0, fnew293 56/0, fnew294 77/0, fnew295 49/0, fnew296 42/0, fnew297 42/0, fnew298 19/0 KEEP=5 corner=PASS) + cpipe 17/0 (was 13/4); simplecalc ×3 rc=0 7960bce447ac6d8f. ZERO DRIFT."
}

d['roots'].append(entry)
d['total'] = len(d['roots'])
sc = collections.Counter(r.get('status') for r in d['roots'])
d['status_counts'] = dict(sorted(sc.items()))
d['meta']['last_update'] = ("CONT-39 session 2026-10-10: F-NEW-301 (the TextView color-state law — getCurrentTextColor "
                            "answers the stored state; cpipe PC-01..04 flip 13/4→17/0 ×3 both directions; zero drift).")
d['generated'] = 'CONT-39 session'
json.dump(d, open(P, 'w'), indent=1, ensure_ascii=False)
print('roots now:', len(d['roots']), '| total field:', d['total'])
print('F-NEW-301 appended; status_counts:', sc.get('ROOT_CAUSED_FIXED'), 'ROOT_CAUSED_FIXED')
