#!/usr/bin/env bash
# cont37_regression.sh — CONT-37 Phase-5 regression gate at the F-NEW-298
# binary. The binary CHANGED this wave (three coordinated generic laws:
# Canvas.getClipBounds (the Compose paragraph-paint gate),
# StaticLayout$Builder setText/setTextDirection prefix-conflation (the
# payload clobber), and the FRAME-HONESTY law (an in-draw halt is never
# presented — the P1-6 extension recorded PENDING in CONT-36 §6)).
# Anchor expectations: 7/8 anchors UNCHANGED (their draws never halt
# in-window; KEEP=0 — zero drift). dooz LEGITIMATELY MOVES to the honest
# keep-empty state (its boot composition takes ~15.3 s of engine time; the
# 15 s budget halts the draw mid-way; the old 250-gray anchor was the
# DISHONEST presentation of that unfinished frame — CONT-36 §6 decode).
# composeStopwatch moves to its first honest content frame (cards + text).
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont37/regression
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"

run1() { # run1 <label> <apkpath> <want-sha16|none>
  local label="$1" apk="$2" want="${3:-none}"
  local o="$OUT/$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local sha
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local verdict="DRIFT"
  [ "$sha" = "$want" ] && verdict="MATCH"
  [ "$want" = "none" ] && verdict="recorded"
  echo "REG $label rc=$rc sha=$sha want=$want $verdict"
}

DOOZ=$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
MICRO=$BASE/upload/canonical_apks/dubrowgn.microtimer_8.apk
UNOTE=$BASE/upload/canonical_apks/app.varlorg.unote_30.apk
GMDICE=$BASE/upload/canonical_apks/de.duenndns.gmdice_8.apk
OPENCALC=$BASE/upload/opencalculator_53.apk
TTT=$BASE/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk
FLAPPY=$BASE/upload/flappycow_rebuilt.apk
G2048=$BASE/upload/s80_games/build_2048/g2048_v1.0_vc1.apk
TANANA=$BASE/tmp/com.tananaev.calculator_11.apk
SIMPLECALC=$BASE/tmp/cont35_apks/simplecalc_8.apk
CSW=$BASE/tmp/cont35_apks/composeStopwatch_1009011.apk

# ---- probe battery (rebuilt fresh; run/ artifacts reset-liable) ----
bash $BASE/scripts/cont21_build_probes.sh > "$OUT/probe_build.log" 2>&1 \
  || echo "PROBE BUILD FAILED (see probe_build.log)"
bash $BASE/scripts/w4_build_probes.sh > "$OUT/w4_probe_build.log" 2>&1 \
  || echo "W4 PROBE BUILD FAILED (see w4_probe_build.log)"
bash $BASE/scripts/cont30_build_probe.sh > "$OUT/f286_probe_build.log" 2>&1 \
  || echo "F286 PROBE BUILD FAILED (see f286_probe_build.log)"

probe1() { # probe1 <label> <apk>
  local label="$1" apk="$2"
  local o="$OUT/probe_$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local pass fail
  pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
  fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
  echo "PROBE $label rc=$rc PASS=$pass FAIL=$fail"
}

# fnew298 needs the RUNNER-SIDE pixel row (the app cannot read the
# framebuffer): the final screenshot's top-left 8x8 block must be the
# frame-1 green 0xFF00FF00 (the keep-previous marker).
probe_fnew298() {
  local label="fnew298" apk="$BASE/tmp/w4_probebuild/fnew298_probe/fnew298_probe.apk"
  local o="$OUT/probe_$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local corner keep
  corner=$(python3 -c "
from PIL import Image
im = Image.open('$o/screenshot.png').convert('RGB')
ok = all(im.getpixel((x,y))==(0,255,0) for x in range(8) for y in range(8))
print('PASS' if ok else 'FAIL')
" 2>/dev/null || echo FAIL)
  keep=$(grep -c "F298-KEEP" "$o/run.log" 2>/dev/null || echo 0)
  if [ "$corner" = "PASS" ]; then
    echo "F298|KEEP-CORNER|PASS|final frame keeps the frame-1 green marker (KEEP=$keep)" >> "$o/run.log"
  else
    echo "F298|KEEP-CORNER|FAIL|final frame lost the frame-1 marker (KEEP=$keep)" >> "$o/run.log"
  fi
  local pass fail
  pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
  fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
  echo "PROBE $label rc=$rc PASS=$pass FAIL=$fail (KEEP=$keep corner=$corner)"
}

case "${1:-all}" in
anchors)
  for i in 1 2 3; do
    # CONT-40: the friend-claim audit REJECTED the "null getWindowToken
    # prevents composition creation" hypothesis (composition creation
    # happens both ways; the DEX stores the token raw with zero
    # null-gates). The AOSP-faithful getWindowToken law was PROTOTYPED and
    # PARKED: it flips dooz to a valid-but-empty scheduling path AND loses
    # composeStopwatch's visible text (5c4a0172628849ba, causality proven
    # via MINIANDROID_WTOKEN_NULL on the same binary) — shipping it would
    # regress visible content for a non-problem. Binary reverted to the
    # byte-exact CONT-39 record. Evidence: evidence/cont40/DOOZ_WTOKEN_AUDIT.md.
    run1 "dooz_r$i"       "$DOOZ"      31ddd4d5b8e6d18e
    # CONT-59 F-NEW-338 RE-PIN: the transparent-container law (a bg-less
    # container shows the theme windowBackground — the EXP-092 GREY_200
    # visibility fill painted a light slab over dark-theme windows).
    # RAW-DIFF-PROVEN per face: the ONLY changed pixels are the fill color
    # swap (micro 225→255 winbg 0xffffffff; unote 225→48 winbg default dark)
    # + AA re-blends; zero content pixels lost. New faces x3 deterministic.
    run1 "microtimer_r$i" "$MICRO"     55343bbec712618d
    run1 "unote_r$i"      "$UNOTE"     90a67cc1ddda57b7
    # CONT-59 F-NEW-337b RE-PIN: the theme-attribute ColorStateList item law
    # (?attr/… item colors resolve through the theme service — the resource-
    # table deref read the attr-DEFINITION row and painted its INT data as
    # ARGB → alpha-0). gmdice's 'Push buttons to roll!' hint line rendered
    # with the themed white for the first time. RAW-DIFF-PROVEN: the ONLY
    # changed pixels are the hint glyph bbox (62,1155)-(1020,1332); every
    # other face byte-identical. New face 3891679dff449331 x3 deterministic
    # — REAL_APP_CONTENT retained, richer render.
    run1 "gmdice_r$i"     "$GMDICE"    3891679dff449331
    # CONT-57 F-NEW-329 RE-PIN: the ConstraintLayout guideline + dimension
    # laws healed opencalc v53's display geometry (guideline1 = 0.18 x 1920
    # = 346 EXACT; inputHSV 1080x199 @y147; resultHSV 1080x153 @y346;
    # sliding_layout 1080x1421 @y499; pad buttons 270-wide 0dp+weight rows).
    # The pre-fix face a976d2f9fb675cb3 was the compressed pad (579-wide
    # sliding_layout, 52x0 display HSVs). New face 0ae271c49d2bd61c x3
    # deterministic. Every OTHER anchor byte-identical (42/42 runs).
    run1 "opencalc_r$i"   "$OPENCALC"  f25b754c4565c38b
    # CONT-60 F-NEW-342 RE-PIN (on top of the F-NEW-341 re-pin): the
    # windowBackground ?android:attr/colorBackground law — the attr ref has
    # no table row; the theme service answers it (white for OpenCalc's
    # light theme) instead of nullopt→dark-fallback. RAW-DIFF-PROVEN: the
    # ONLY changed pixels are the window-color swap (48,48,48)→(255,255,255)
    # in the pad band + row separators; icon glyphs unchanged (now crisp).
    # CONT-60 F-NEW-341 RE-PIN: the vector-tint theme-attr law (?attr/…
    # tints resolve through the theme service — the table deref answered
    # the attr-DEFINITION int and the alpha-0 SRC_IN tint erased every
    # icon). RAW-DIFF-PROVEN: 22,483 changed px, 100% inside the five
    # icon glyph boxes (menu dots, exponent caret, chevron, point,
    # backspace); display band and pad text unchanged. New face x3.
    run1 "tttdeluxe_r$i"  "$TTT"       af6094295ecb50e3
    run1 "flappycow_r$i"  "$FLAPPY"    13cf47464d9787f4
    run1 "g2048_r$i"      "$G2048"     59ca1526611c4622
    # CONT-43: the calculator fix pinned as a standing gate — the F-NEW-304
    # fragment drain + the re-landed companion class-measure law (with the
    # subtree-coherence fix) put tananaev v1.10 at rc=0 SUCCESS with the
    # real preference rows parsed/measured/attached. CONT-44: F-NEW-305's
    # ActionBarOverlayLayout inset law moved the rows BELOW the action-bar
    # band (content top = the theme's actionBarSize, 126px) — the fix face
    # re-pins here (0f649804d6e0486d = the pre-inset face; the inset leg is
    # the delta; row glyphs are F-NEW-308, a separate root).
    # CONT-58 F-NEW-336 RE-PIN: the app-package file-backed ColorStateList
    # law resolved the theme's textColorPrimary for the first time (the
    # base theme answered STRING 'res/color/abc_primary_text_material_
    # light.xml', the framework router has no abc_* row, and the raw
    # string-pool index 0x61 was cast as ARGB = alpha-0 → every glyph
    # blended away). Post-fix the rows paint real text (dark_glyph_samples
    # 0 → 4420; all five preference rows visible). New face
    # 601e0219d4cab10b x3 deterministic — REAL_APP_CONTENT retained.
    run1 "tanana_r$i"     "$TANANA"    afe0bd8dd4d09ca6
  done
  ;;
dooz180)
  # CONT-43: the dooz case-E content face as a standing gate — with a fair
  # budget the compose boot COMPLETES (~80 s / 25M insns) and the REAL app
  # scaffold renders (Material3 surface + top bar + FAB + pill button).
  # CONT-61 F-NEW-344 RE-PIN: the Layout.getDesiredWidth law — the compose
  # text intrinsic leg (AndroidTextLayoutIntrinsics Lsk0;.c ×2 measured;
  # the typed-default answered 0 → every compose StaticLayout built
  # width=0 → the paragraph clipRect w=0 → getClipBounds FALSE → the
  # compose 1.11 paint cull skipped Layout.draw → zero text pixels).
  # Post-fix: intrinsics 104px ("Dooz") / 219px ("New game") via the REAL
  # shaper; layouts build non-zero; Layout.draw dispatches; the title and
  # button label render real glyphs. RAW-DIFF: the changed pixels are the
  # text bands (title y0-120, button label band) + AA re-blends; the
  # scaffold/window pixels unchanged. New face 4f32f50fd55ccf90 x3
  # deterministic — REAL_APP_CONTENT retained, richer render.
  for i in 1 2 3; do
    o="$OUT/dooz180_r$i"; rm -rf "$o"; mkdir -p "$o"
    timeout 580 "$BIN" run "$DOOZ" --width 1080 --height 1920 \
      --frames 5 --max-seconds 180 -o "$o" > "$o/run.log" 2>&1
    rc=$?
    sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    verdict="DRIFT"
    [ "$sha" = "4f32f50fd55ccf90" ] && verdict="MATCH"
    echo "REG dooz180_r$i rc=$rc sha=$sha want=4f32f50fd55ccf90 $verdict"
  done
  ;;
target)
  # CONT-44: F-NEW-306 FIXED — the csw content-state regression is REGAINED:
  # the M3-19 active-cycle stub no longer fires on incomplete-payload keys
  # (the Lch1;.j persistent-trie builder's 3rd int — the recursion shift —
  # was exactly the dropped identity; the stub fabricated null mid-build).
  # The pinned healthy face 3442d9a9dc0fa0f9 returned byte-exact x3 with
  # zero drift everywhere. The case stays as the standing gate.
  # CONT-61 F-NEW-344 RE-PIN: the same Layout.getDesiredWidth law — csw's
  # compose (older ui, no paint cull) called it ×3 ("Compose Stopwatch"
  # →421px, "0."→39px, "00"→52px); the pre-fix width=0 layouts drew the
  # title CLIPPED OFF-SCREEN (op x≈1070 on a 1080 face). Post-fix the
  # real intrinsic widths move the title INTO VIEW (op x=607, fully
  # readable). RAW-DIFF: bbox (607,36)-(1080,1095) = the title + digits
  # bands ONLY; cards/pill/track pixels byte-identical. New face
  # d3c26b73ee21e571 x3 deterministic — REAL_APP_CONTENT retained.
  for i in 1 2 3; do
    run1 "csw_r$i" "$CSW" d3c26b73ee21e571
  done
  ;;
probes)
  probe1 fcol  "$BASE/run/w7/fcol.apk"
  probe1 f259  "$BASE/run/w7/f259.apk"
  probe1 f259g "$BASE/run/w7/f259g.apk"
  probe1 f266  "$BASE/run/w8/f266.apk"
  probe1 f268  "$BASE/run/cont18g/f268.apk"
  probe1 fnew253 "$BASE/tmp/w4_probebuild/fnew253_probe/fnew253_probe.apk"
  probe1 fnew286 "$BASE/tmp/cont30_probebuild/fnew286_probe/fnew286_probe.apk"
  probe1 fnew289 "$BASE/tmp/w4_probebuild/fnew289_probe/fnew289_probe.apk"
  probe1 ckey   "$BASE/tmp/w4_probebuild/classkey_probe/classkey_probe.apk"
  probe1 cpipe  "$BASE/tmp/w4_probebuild/colorpipe_probe/colorpipe_probe.apk"
  probe1 fnew302 "$BASE/tmp/w4_probebuild/fnew302_probe/fnew302_probe.apk"
  probe1 fnew252 "$BASE/tmp/w4_probebuild/fnew252_probe/fnew252_probe.apk"
  probe1 fnew290 "$BASE/tmp/w4_probebuild/fnew290_probe/fnew290_probe.apk"
  probe1 fnew291 "$BASE/tmp/w4_probebuild/fnew291_probe/fnew291_probe.apk"
  probe1 fnew292 "$BASE/tmp/w4_probebuild/fnew292_probe/fnew292_probe.apk"
  probe1 fnew293 "$BASE/tmp/w4_probebuild/fnew293_probe/fnew293_probe.apk"
  probe1 fnew294 "$BASE/tmp/w4_probebuild/fnew294_probe/fnew294_probe.apk"
  probe1 fnew295 "$BASE/tmp/w4_probebuild/fnew295_probe/fnew295_probe.apk"
  probe1 fnew296 "$BASE/tmp/w4_probebuild/fnew296_probe/fnew296_probe.apk"
  probe1 fnew297 "$BASE/tmp/w4_probebuild/fnew297_probe/fnew297_probe.apk"
  probe_fnew298
  ;;
control)
  # CONT-44: simplecalc re-pinned to the F-NEW-305 fix face. The app is an
  # appcompat host (ActionBarOverlayLayout) whose content previously built
  # at y=0 UNDER the action-bar band; the inset law moved it to the theme's
  # actionBarSize (126px = 48dp x 2.625) with the calculator layout intact
  # (display + pad rows all +126). The old face 7960bce447ac6d8f was the
  # pre-inset geometry; the re-pin is the fix face (same disposition as
  # the tananaev anchor).
  # CONT-58 F-NEW-336 RE-PIN: the same app-package ColorStateList law
  # resolved the app's textColorPrimary — the display's initial "0" was
  # painted alpha-0 (unresolved STRING cast) and now renders (29,29,29).
  # RAW-diff-proven: the ONLY changed pixels in the whole 1080x1920 face
  # are the "0" glyph bbox (1059-1078, 481-507); pad/geometry byte-stable.
  # New face 950b955c6999d72a x3 deterministic — REAL_APP_CONTENT retained.
  for i in 1 2 3; do
    run1 "simplecalc_r$i" "$SIMPLECALC" 341b9cec89d8f182
  done
  ;;
*)
  bash "$0" anchors
  bash "$0" target
  bash "$0" probes
  bash "$0" control
  echo "REGRESSION DONE"
  ;;
esac
