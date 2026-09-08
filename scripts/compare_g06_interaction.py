#!/usr/bin/env python3
# compare_g06_interaction.py — G06 §6 interaction golden comparator.
#
# Validates the g06_interaction fixture runs against law-derived
# expectations (AOSP View.onTouchEvent + StateListDrawable + disabled law):
#
#   RUN A (--tap 540,178 on btn_tap, enabled, state-list background):
#     frame_000  launch: btn_tap bbox = #2196F3 blue, counter "Taps: 0"
#     frame_001  mid-press: btn_tap bbox = #FF5252 RED (pressed visible)
#     post-drain frames (M3 FINDING-010 tick frames — the frame stream now
#                also captures mutations DURING the queue drain):
#       the drain may emit intermediate frames (e.g. PerformClick applied
#       while still pressed, then UnsetPressedState restoring blue).
#       LAW (index-robust): SOME frame after the press shows the button
#       restored to #2196F3, and the FINAL frame must show it restored —
#       press is transient (64ms law); the counter must read "Taps: 1" in
#       the final state (real DEX onClick mutated the app state).
#     manifest   DOWN consumed + setPressed(true); UP click_posted;
#                PerformClick dispatched (real DEX); UnsetPressedState at +64
#   RUN B (--tap 540,430 on btn_disabled):
#     all frames byte-identical (disabled law: consumes, never responds)
#   DETERMINISM: RUN A executed 3× — frame SHAs byte-identical (checked by
#     the battery script over the 3 output dirs).
#
# Usage: compare_g06_interaction.py <run_a_dir> <run_b_dir> [--json out.json]
# Exit 0 = ALL PASS; 1 = failures present.
import json
import struct
import sys
import zlib
from pathlib import Path

CHECKS = {"total": 0, "pass": 0, "fail": 0}
FAILURES = []


def check(ok, what):
    CHECKS["total"] += 1
    if ok:
        CHECKS["pass"] += 1
        print(f"  PASS: {what}")
    else:
        CHECKS["fail"] += 1
        FAILURES.append(what)
        print(f"  FAIL: {what}")


def read_png_rgb(path):
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path}: not a PNG"
    pos, w, h, idat, color = 8, None, None, b"", None
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        ct = data[pos + 4:pos + 8]
        ch = data[pos + 8:pos + 8 + ln]
        if ct == b"IHDR":
            w, h, bitd, color = struct.unpack(">IIBB", ch[:10])
        elif ct == b"IDAT":
            idat += ch
        pos += 12 + ln
    raw = zlib.decompress(idat)
    assert color == 2, f"{path}: expected RGB PNG, got color={color}"
    bpp, stride = 3, w * 3
    out = bytearray(w * h * bpp)
    prev = bytearray(stride)
    pp = 0
    for y in range(h):
        ft = raw[pp]
        pp += 1
        line = bytearray(raw[pp:pp + stride])
        pp += stride
        if ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, bytes(out)


def count_color(px, w, h, color, bbox):
    n = 0
    for y in range(bbox[1], bbox[3]):
        for x in range(bbox[0], bbox[2]):
            i = (y * w + x) * 3
            if (px[i], px[i + 1], px[i + 2]) == color:
                n += 1
    return n


# Fixture layout law (420dpi device, density 2.625):
#   margins 40dp = 105px; buttons 56dp = 147px; counter 40dp = 105px
BTN_TAP = (105, 105, 975, 252)       # x0,y0,x1,y1 (exclusive)
BTN_DISABLED = (105, 357, 975, 504)
BLUE = (33, 150, 243)                # #2196F3 default selector item
RED = (255, 82, 82)                  # #FF5252 state_pressed item
GREY = (158, 158, 158)               # #9E9E9E disabled background
BTN_AREA = 870 * 147


def frame_pixels(run_dir, name):
    return read_png_rgb(str(Path(run_dir) / "frames" / name))


def main():
    run_a, run_b = sys.argv[1], sys.argv[2]
    out_json = None
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]

    print("── RUN A: tap on btn_tap (enabled, state-list bg) ──")
    m = json.loads((Path(run_a) / "frames" / "manifest.json").read_text())
    check(m.get("gesture") == "TAP", "gesture = TAP (canonical pipeline)")
    check(m.get("changed_pixels_vs_launch", 0) > 0,
          "tap changed pixels (state mutation → render)")

    w, h, p0 = frame_pixels(run_a, "frame_000.png")
    _, _, p1 = frame_pixels(run_a, "frame_001.png")

    blue0 = count_color(p0, w, h, BLUE, BTN_TAP)
    red1 = count_color(p1, w, h, RED, BTN_TAP)
    red0 = count_color(p0, w, h, RED, BTN_TAP)
    check(blue0 > BTN_AREA * 0.9 and red0 == 0,
          "frame_000: btn_tap is selector default #2196F3 (unpressed)")
    check(red1 > BTN_AREA * 0.9,
          "frame_001: pressed state VISIBLE — #FF5252 fills the button "
          "(StateListDrawable re-pick law)")

    # M3 FINDING-010: the drain emits mutation-keyed tick frames between the
    # press and the post-gesture frame. The 64ms UnsetPressedState law is
    # stream-level: the restored #2196F3 state must APPEAR after the press
    # and PERSIST to the final frame (press is transient).
    frame_names = [f["file"] for f in m["frames"]]
    restored_at = None
    blue_final = 0
    for idx, fname in enumerate(frame_names):
        _, _, pf = frame_pixels(run_a, fname)
        bf = count_color(pf, w, h, BLUE, BTN_TAP)
        rf = count_color(pf, w, h, RED, BTN_TAP)
        if idx >= 2 and restored_at is None and bf > BTN_AREA * 0.9 and rf == 0:
            restored_at = idx
        blue_final = bf if idx == len(frame_names) - 1 else blue_final
    check(restored_at is not None,
          "a post-press frame restores #2196F3 (UnsetPressedState 64ms law; "
          f"first restored frame index={restored_at})")
    check(blue_final > BTN_AREA * 0.9,
          "final frame: btn_tap still #2196F3 (pressed state transient — "
          "no sticky press law)")

    evs = {e["action"]: e for e in m["events"]}
    down, up = evs.get("ACTION_DOWN", {}), evs.get("ACTION_UP", {})
    check(down.get("consumed") is True and down.get("disabled_law") is None,
          "DOWN consumed by enabled target (no disabled law)")
    check("setPressed(true)" in down.get("state_changes", []),
          "DOWN set the pressed state (View.java L17119-17125 law)")
    check(up.get("click_posted") is True,
          "UP posted PerformClick on the main queue (post-law)")
    cbs = [t for t in m.get("touch_trace", []) if "callback" in t]
    names = [c["callback"] for c in cbs]
    check("PerformClick" in names and "UnsetPressedState" in names,
          "queue drained PerformClick AND UnsetPressedState (one-queue law)")
    pc = next((c for c in cbs if c["callback"] == "PerformClick"), {})
    check(pc.get("click_dispatched") is True,
          "PerformClick dispatched the real DEX onClick")
    us = next((c for c in cbs if c["callback"] == "UnsetPressedState"), {})
    check("setPressed(false)" in us.get("state_changes", []),
          "UnsetPressedState cleared pressed (PRESSED_STATE_DURATION law)")
    check(us.get("virtual_ms", 0) - up.get("virtual_ms", 0) >= 64,
          "UnsetPressedState fired no earlier than +64ms after UP "
          "(PRESSED_STATE_DURATION post law; drain granularity may exceed)")
    check(down.get("virtual_ms", 0) < up.get("virtual_ms", 0) <=
          down.get("virtual_ms", 0) + 50,
          "tap window: UP within +50ms virtual (< TAP_TIMEOUT-scale tap)")

    texts0 = {t["text"] for t in m["frames"][0].get("visible_texts", [])}
    final_texts = {t["text"]
                   for t in m["frames"][-1].get("visible_texts", [])}
    check("Taps: 0" in texts0, "launch state: counter at 0")
    check("Taps: 1" in final_texts,
          "final state: counter incremented by the app's own DEX "
          "onClick (state mutation)")

    print("── RUN B: tap on btn_disabled (disabled law) ──")
    mb = json.loads((Path(run_b) / "frames" / "manifest.json").read_text())
    frame_names_b = [f["file"] for f in mb["frames"]]
    evs_b = {e["action"]: e for e in mb["events"]}
    db, ub = evs_b.get("ACTION_DOWN", {}), evs_b.get("ACTION_UP", {})
    check(db.get("consumed") is True and db.get("disabled_law") is True,
          "disabled view CONSUMED the DOWN (View.java L17049-17057 law)")
    check(ub.get("consumed") is True and ub.get("disabled_law") is True,
          "disabled view CONSUMED the UP without responding")
    check("setPressed(true)" not in db.get("state_changes", []),
          "no pressed state on disabled view")
    check(mb.get("changed_pixels_vs_launch") == 0,
          "ZERO pixels changed: disabled tap is visually inert")

    _, _, b0 = frame_pixels(run_b, "frame_000.png")
    _, _, blast = frame_pixels(run_b, frame_names_b[-1])
    identical = True
    for fname in frame_names_b[1:]:
        _, _, bf = frame_pixels(run_b, fname)
        if bf != b0:
            identical = False
    check(identical and b0 == blast,
          "all disabled-run frames byte-identical (no response law)")
    g1 = count_color(blast, w, h, GREY, BTN_DISABLED)
    check(g1 > (BTN_DISABLED[2] - BTN_DISABLED[0]) *
          (BTN_DISABLED[3] - BTN_DISABLED[1]) * 0.9,
          "disabled button still draws its static #9E9E9E background "
          "(visual sanity)")

    print("── G06 INTERACTION GOLDEN ──")
    verdict = "PASS" if CHECKS["fail"] == 0 else "FAIL"
    print(f"{verdict} ({CHECKS['pass']}/{CHECKS['total']} checks)")
    if out_json:
        Path(out_json).write_text(json.dumps({
            "verdict": f"{verdict} ({CHECKS['pass']}/{CHECKS['total']} checks)",
            "checks": CHECKS, "failures": FAILURES,
        }, indent=2))
    return 0 if CHECKS["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
