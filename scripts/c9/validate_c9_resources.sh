#!/usr/bin/env bash
# scripts/c9/validate_c9_resources.sh — CODER 9 synthetic resources harness.
#
# One-command reproduction of Issue #521 §5/§6:
#   1. (re)generate deterministic fixture assets
#   2. build the fixture APK with the REAL toolchain (aapt2+ECJ+D8)
#   3. post-process: pin assets/c9_stored.bin STORED + c9_compressed.txt
#      DEFLATE, 1980 epoch, print the independent APPNOTE §4.3.7 data offsets
#   4. run the engine under 4 device configs (420/en, 160/en, 240/en, 420/fa)
#   5. assert 41 laws: identity, selected config, raw entry bytes, SHA-256,
#      decoder, dims/mime, error behavior + §6 framebuffer pixel law
#
# Usage: bash scripts/c9/validate_c9_resources.sh [evidence_dir]
# Expects: build/miniandroid already built (make -j all inside miniandroid/).
set -uo pipefail

EVID="${1:-/tmp/c9_evidence}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIX="$ROOT/miniandroid/tests/fixtures/c9_resources"
ENG="$ROOT/miniandroid/build/miniandroid"
APK="$EVID/c9_resources.apk"
mkdir -p "$EVID"

g_pass=0; g_fail=0
law() {  # law <number> <description> <condition-exit-code>
    if [ "$3" -eq 0 ]; then g_pass=$((g_pass+1));
    else g_fail=$((g_fail+1)); echo "  LAW $1 FAIL: $2"; fi
}

echo "== [1/5] fixture assets (deterministic) =="
python3 "$ROOT/scripts/c9/gen_c9_fixture_assets.py" > "$EVID/gen.log" 2>&1
law 1 "fixture assets generated" $?

echo "== [2/5] fixture APK build (aapt2+ECJ+D8 real toolchain) =="
bash "$ROOT/scripts/build/build_fixture_apk.sh" "$FIX" "$APK" > "$EVID/build.log" 2>&1
law 2 "fixture APK built" $?

echo "== [3/5] post-process (pin STORED/DEFLATE + determinism) =="
python3 "$ROOT/scripts/c9/postprocess_c9_fixture.py" "$APK" | tee "$EVID/postprocess.log"
law 3 "stored asset pinned STORED" $(grep -qc "PINNED assets/c9_stored.bin: method=0" "$EVID/postprocess.log"; echo $?)
law 4 "compressed asset pinned DEFLATE" $(grep -qc "PINNED assets/c9_compressed.txt: method=8" "$EVID/postprocess.log"; echo $?)

STORED_DATA_OFFSET=$(grep -oP "PINNED assets/c9_stored\.bin:.*data_offset=\K[0-9]+" "$EVID/postprocess.log")
STORED_SHA=$(grep -oP "PINNED assets/c9_stored\.bin:.*sha256=\K[0-9a-f]{64}" "$EVID/postprocess.log")

echo "== [4/5] engine runs under 4 device configs =="
run_cfg() {  # run_cfg <density> <locale> <tag>
    MINIANDROID_DENSITY="$1" MINIANDROID_LOCALE="$2" timeout 180 \
        "$ENG" run -o "$EVID/$3" "$APK" > "$EVID/$3.log" 2>&1
}
run_cfg 420 en-US run_420en; law 5 "run 420/en completes" $?
run_cfg 160 en-US run_160en; law 6 "run 160/en completes" $?
run_cfg 240 en-US run_240en; law 7 "run 240/en completes" $?
run_cfg 420 fa-IR run_420fa; law 8 "run 420/fa completes" $?

case_grep() {  # case_grep <tag> <pattern-with-anchor> -> 0 if it matches
    grep -q "$2" "$EVID/$1.log"
}

echo "== [5/5] 33 law assertions =="
# CASE01 — decodeResource density law per selected bucket (C9-1)
law 9  "CASE01 @420 natural=105x53 (hdpi x1.75)" $(case_grep run_420en '^CASE01 natural=105x53'; echo $?)
law 10 "CASE01 @160 natural=40x20 (mdpi x1.0)"   $(case_grep run_160en '^CASE01 natural=40x20'; echo $?)
law 11 "CASE01 @240 natural=60x30 (hdpi x1.0)"   $(case_grep run_240en '^CASE01 natural=60x30'; echo $?)
# CASE02 — WebP bounds contract + full decode
ok=0
for t in run_420en run_160en run_240en run_420fa; do
    case_grep $t '^CASE02 bounds=24x12 mime=image/webp natural=' || ok=1
done
law 12 "CASE02 bounds=24x12 mime=image/webp (all runs)" $ok
law 13 "CASE02 @420 natural=63x32" $(case_grep run_420en '^CASE02 bounds=24x12 mime=image/webp natural=63x32'; echo $?)
# CASE03 — nested asset identity (list + bytes + head)
ok=0
for t in run_420en run_160en run_240en run_420fa; do
    case_grep $t '^CASE03 list=\[deep\]; 29 bytes; head=43392d4e45535445' || ok=1
done
law 14 "CASE03 nested asset: list=[deep]; 29B; head=43392d4e45535445 (all runs)" $ok
# CASE04 — compressed asset laws
ok=0
for t in run_420en run_160en run_240en run_420fa; do
    case_grep $t '^CASE04 open=2000 bytes; openFd=FileNotFoundException' || ok=1
done
law 15 "CASE04 open=2000B served; openFd refuses (all runs)" $ok
# CASE05 — AFD data-offset law vs independent python arithmetic (C9-2)
ok=0
for t in run_420en run_160en run_240en run_420fa; do
    case_grep $t "^CASE05 afd startOffset=$STORED_DATA_OFFSET length=115 declared=115 openBytes=115 stream==open=true" || ok=1
done
law 16 "CASE05 startOffset==data_offset($STORED_DATA_OFFSET) len=115 stream==open (all runs)" $ok
# fd-window provenance: bytes at [startOffset,+115) re-read independently
ok=0
python3 - "$APK" "$STORED_DATA_OFFSET" "$STORED_SHA" <<'PY' || ok=1
import sys, zipfile, hashlib, struct
apk, off, sha = sys.argv[1], int(sys.argv[2]), sys.argv[3]
data = open(apk, 'rb').read()
window = data[off:off+115]
assert hashlib.sha256(window).hexdigest() == sha, "fd window sha mismatch"
# cross-check: zipfile extraction of the same entry must equal the window
with zipfile.ZipFile(apk) as z:
    assert z.read('assets/c9_stored.bin') == window, "extraction != fd window"
print("fd-window provenance OK (two read paths agree)")
PY
law 17 "fd window SHA-256 == payload sha; extraction path == fd path" $ok
# CASE06 — VectorDrawable intrinsic law (C9-3)
law 18 "CASE06 @420 intrinsic=126x126" $(case_grep run_420en '^CASE06 intrinsic=126x126'; echo $?)
law 19 "CASE06 @240 intrinsic=72x72"   $(case_grep run_240en '^CASE06 intrinsic=72x72'; echo $?)
law 20 "CASE06 @160 intrinsic=48x48"   $(case_grep run_160en '^CASE06 intrinsic=48x48'; echo $?)
# CASE07 — density-qualified bucket selection (dims echo)
law 21 "CASE07 @420 photo=105x53" $(case_grep run_420en '^CASE07 photo=105x53'; echo $?)
law 22 "CASE07 @240 photo=60x30"  $(case_grep run_240en '^CASE07 photo=60x30'; echo $?)
law 23 "CASE07 @160 photo=40x20"  $(case_grep run_160en '^CASE07 photo=40x20'; echo $?)
# CASE08 — locale-qualified strings
law 24 "CASE08 en 'Hello C9' (both en runs)" $([ $(grep -lc '^CASE08 string=Hello C9' "$EVID/run_420en.log" "$EVID/run_160en.log" 2>/dev/null | wc -l) -eq 2 ]; echo $?)
law 25 "CASE08 fa 'سلام کد۹'" $(case_grep run_420fa '^CASE08 string=سلام کد۹'; echo $?)
# CASE09/10/11/12 — typeface + missing-resource/asset + invalid image laws
ok=0
for t in run_420en run_160en run_240en run_420fa; do
    case_grep $t '^CASE09 typeface=loaded' || ok=1
    case_grep $t '^CASE10 decode_null=true; string_error=NotFoundException' || ok=1
    case_grep $t '^CASE11 asset_error=FileNotFoundException' || ok=1
    case_grep $t '^CASE12 invalid_null=true' || ok=1
done
law 26 "CASE09 typeface loaded (all runs)" $ok
ok=0
for t in run_420en run_160en run_240en run_420fa; do
    case_grep $t '^CASE10 decode_null=true; string_error=NotFoundException' || ok=1
done
law 27 "CASE10 missing string → NotFoundException (all runs)" $ok
ok=0
for t in run_420en run_160en run_240en run_420fa; do
    case_grep $t '^CASE11 asset_error=FileNotFoundException' || ok=1
done
law 28 "CASE11 missing asset → FileNotFoundException (all runs)" $ok
ok=0
for t in run_420en run_160en run_240en run_420fa; do
    case_grep $t '^CASE12 invalid_null=true' || ok=1
done
law 29 "CASE12 invalid image → null, no fake pixels (all runs)" $ok
# CASE13 — nodpi never scales
ok=0
for t in run_420en run_160en run_240en; do
    case_grep $t '^CASE13 nodpi=40x20' || ok=1
done
law 30 "CASE13 nodpi=40x20 unscaled at 420/160/240" $ok
# CASE14 — §6 view chain
ok=0
for t in run_420en run_160en run_240en; do
    case_grep $t '^CASE14 children=3 texts=Hello C9' || ok=1
done
law 31 "CASE14 children=3 texts=Hello C9 (en runs)" $ok
law 32 "CASE14 fa texts=سلام کد۹" $(case_grep run_420fa '^CASE14 children=3 texts=سلام کد۹'; echo $?)
# §6 pixel law — bucket selection proven at the framebuffer level
PIX=$(python3 - "$EVID" <<'PY'
import sys
from PIL import Image
evid = sys.argv[1]
out = {}
for tag in ('run_160en', 'run_240en', 'run_420en', 'run_420fa'):
    img = Image.open(f'{evid}/{tag}/screenshot.png').convert('RGB')
    px = img.load(); w, h = img.size
    red = green = blue = amber = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if r > 150 and g < 110 and b < 110: red += 1
            elif g > 130 and r < 110 and b < 130: green += 1
            elif b > 130 and r < 110 and g < 110: blue += 1
            elif r > 220 and g > 150 and b < 80: amber += 1
    out[tag] = (red, green, blue, amber)
print(out['run_160en'][0], out['run_160en'][1],
      out['run_240en'][1], out['run_240en'][0],
      out['run_420en'][1], out['run_420en'][0],
      out['run_420fa'][1], out['run_420fa'][0],
      min(out[t][2] for t in out), min(out[t][3] for t in out))
PY
)
read R160 G160 G240 R240 G420 R420 GFA RFA BLUEMIN AMBERMIN <<< "$PIX"
law 33 "pixel @160: RED family painted ($R160 px), ZERO green" $([ "$R160" -gt 500 ] && [ "$G160" -eq 0 ]; echo $?)
law 34 "pixel @240: GREEN family painted ($G240 px), ZERO red" $([ "$G240" -gt 500 ] && [ "$R240" -eq 0 ]; echo $?)
law 35 "pixel @420en: GREEN family painted ($G420 px), ZERO red" $([ "$G420" -gt 500 ] && [ "$R420" -eq 0 ]; echo $?)
law 36 "pixel @420fa: GREEN family painted ($GFA px), ZERO red" $([ "$GFA" -gt 500 ] && [ "$RFA" -eq 0 ]; echo $?)
law 37 "pixel: blue vector paints in ALL runs (min $BLUEMIN px)" $([ "$BLUEMIN" -gt 500 ]; echo $?)
law 38 "pixel: amber triangle paints in ALL runs (min $AMBERMIN px)" $([ "$AMBERMIN" -gt 100 ]; echo $?)
law 39 "pixel: bucket change MOVES the framebuffer (160 red vs 240/420 green)" $([ "$R160" -gt 0 ] && [ "$G240" -gt 0 ] && [ "$G420" -gt 0 ]; echo $?)

# Evidence integrity — 4 distinct screenshot SHAs
SHA_OUT=$(python3 - "$EVID" <<'PY'
import sys, hashlib
evid = sys.argv[1]
shas = []
for tag in ('run_420en', 'run_160en', 'run_240en', 'run_420fa'):
    d = open(f'{evid}/{tag}/screenshot.png', 'rb').read()
    shas.append(hashlib.sha256(d).hexdigest())
    print(f"{tag} screenshot sha256={shas[-1]}")
print("distinct:", len(set(shas)))
PY
)
echo "$SHA_OUT" | tee "$EVID/screenshot_shas.txt"
law 40 "4 screenshots exist" $([ $(grep -c "sha256=" "$EVID/screenshot_shas.txt") -eq 4 ]; echo $?)
law 41 "4 DISTINCT screenshot SHAs (config changes the framebuffer)" $([ "$(grep -oP 'distinct: \K[0-9]+' "$EVID/screenshot_shas.txt")" -eq 4 ]; echo $?)

echo "$STORED_SHA" > "$EVID/stored_payload_sha.txt"
echo "APK $(sha256sum "$APK")" > "$EVID/apk_sha.txt"

echo
echo "== CODER 9 harness result: $g_pass/$((g_pass+g_fail)) PASS =="
[ "$g_fail" -eq 0 ] || exit 1
