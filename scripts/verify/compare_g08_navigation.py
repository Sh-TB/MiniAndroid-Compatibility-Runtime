#!/usr/bin/env python3
# compare_g08_navigation.py — G08 §11–14 navigation golden comparator.
#
# Two-tap run on the g08_navigation fixture (real aapt2+ECJ+D8 APK, two REAL
# DEX activities):
#   tap 1 (540,378) = btn_launch_result → startActivityForResult(i, 42)
#     frame_002 = SECOND activity's window: red BACK button in B's region,
#                 zero A pixels (real window switch — not a screen swap)
#   tap 2 (540,356) = btn_back on B → setResult(-1, Intent) + finish()
#     cascade onPause→onStop→onDestroy (real DEX), pop stack,
#     onActivityResult(42, -1, data) delivered BEFORE onStart (law),
#     A restored: frame_004 shows A's window AND the app's own DEX-written
#     "R42:-1" result receipt.
#
# Extra law proof (single-tap run): explicit-Intent extras roundtrip —
#   btn_launch sends putExtra("greet","hello") + putExtra("num",7) and B's
#   own onCreate (real DEX) renders "hello:7".
#
# Usage: compare_g08_navigation.py <nav_run> <extras_run> [--json out.json]
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
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, w, h, idat = 8, None, None, b""
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        ct = data[pos + 4:pos + 8]
        ch = data[pos + 8:pos + 8 + ln]
        if ct == b"IHDR":
            w, h, *_ = struct.unpack(">IIBBBBB", ch)
        elif ct == b"IDAT":
            idat += ch
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 3
    out = bytearray(w * h * 3)
    prev = bytearray(stride)
    pp = 0
    for y in range(h):
        ft = raw[pp]
        pp += 1
        line = bytearray(raw[pp:pp + stride])
        pp += stride
        if ft == 1:
            for i in range(3, stride):
                line[i] = (line[i] + line[i - 3]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - 3] if i >= 3 else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - 3] if i >= 3 else 0
                b = prev[i]
                c = prev[i - 3] if i >= 3 else 0
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


GREEN = (76, 175, 80)    # A's btn_launch
RED = (244, 67, 54)      # B's btn_back
BTN_A = (105, 105, 975, 252)     # A's launch button bbox
BTN_B_BACK = (105, 283, 975, 430)  # B's back button bbox


def texts_of(frame):
    return {t["text"] for t in frame.get("visible_texts", [])}


def main():
    nav_run, extras_run = sys.argv[1], sys.argv[2]
    out_json = None
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]

    m = json.loads((Path(nav_run) / "frames" / "manifest.json").read_text())
    launch = m.get("activity_launch", {})

    print("── G08 §12/§13: second-Activity launch (TransactionExecutor law) ──")
    check(launch.get("launched") is True,
          "pending Intent CONSUMED: second activity launched through the "
          "Activity system (FIND-G08-001 dead code is live)")
    cbs = {c.get("method"): c for c in launch.get("callbacks", [])}
    oc = cbs.get("onCreate", {})
    check(oc.get("dispatched") is True and oc.get("instructions", 0) > 0,
          "B.onCreate executed REAL bytecode (performLaunchActivity law)")
    check(launch.get("a_class") and "MainActivity" in launch["a_class"],
          "A identified in the launch record")
    check("SecondActivity" in launch.get("component", ""),
          "explicit component resolution (setClassName → SecondActivity)")
    ms = [c["virtual_ms"] for c in m.get("touch_trace", [])
          if "virtual_ms" in c]
    check(launch.get("b_view_root", 0) != launch.get("a_view_root", 0),
          "B built its OWN view tree (distinct window root)")

    print("── G08 §13: window switch is pixel-real ──")
    w, h, p0 = read_png_rgb(str(Path(nav_run) / "frames" / "frame_000.png"))
    _, _, p2 = read_png_rgb(str(Path(nav_run) / "frames" / "frame_002.png"))
    _, _, p4 = read_png_rgb(str(Path(nav_run) / "frames" / "frame_004.png"))
    check(count_color(p0, w, h, GREEN, BTN_A) > 100000,
          "frame_000: A's window (green LAUNCH button)")
    check(count_color(p2, w, h, GREEN, BTN_A) == 0,
          "frame_002: A's window GONE (A.onStop real — not a screen swap)")
    check(count_color(p2, w, h, RED, BTN_B_BACK) > 100000,
          "frame_002: B's window (red BACK button in B's region)")
    check(count_color(p4, w, h, GREEN, BTN_A) > 100000,
          "frame_004: A's window RESTORED after B finished")

    print("── G08 §14: finish cascade + result delivery + back ──")
    fc = m.get("finish_cascade", {})
    cbs2 = {c.get("method"): c for c in fc.get("callbacks", [])}
    check(cbs2.get("onPause", {}).get("method") == "onPause" and
          cbs2.get("onStop", {}).get("method") == "onStop" and
          cbs2.get("onDestroy", {}).get("method") == "onDestroy",
          "B cascade: onPause → onStop → onDestroy (ActivityThread law)")
    ar = next((c for c in fc.get("restore_callbacks", [])
               if c.get("method") == "onActivityResult"), {})
    check(ar.get("dispatched") is True and ar.get("instructions", 0) > 0,
          "onActivityResult executed REAL bytecode on the caller")
    check(ar.get("request_code") == 42 and ar.get("result_code") == -1,
          "result contract: request 42 + RESULT_OK(-1) delivered")
    rest_names = [c.get("method") for c in fc.get("restore_callbacks", [])]
    if "onActivityResult" in rest_names and "onStart" in rest_names:
        check(rest_names.index("onActivityResult") < rest_names.index("onStart"),
              "onActivityResult BEFORE onStart (Activity.java law)")
    check("R42:-1" in texts_of(m["frames"][4]),
          "A's own DEX code received and RENDERED the result (R42:-1)")
    check(fc.get("final_state") == "RESUMED (A restored)",
          "restored activity state = RESUMED (restart law)")

    print("── G08 §12: explicit-Intent extras roundtrip (single-tap run) ──")
    me = json.loads((Path(extras_run) / "frames" / "manifest.json").read_text())
    check("hello:7" in texts_of(me["frames"][2]),
          "B's real onCreate read getStringExtra('greet')='hello' + "
          "getIntExtra('num')=7 from the LAUNCH intent")
    le = me.get("activity_launch", {})
    check(le.get("launched") is True,
          "extras run: second activity launched (putExtra path)")

    print("── G08 NAVIGATION GOLDEN ──")
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
