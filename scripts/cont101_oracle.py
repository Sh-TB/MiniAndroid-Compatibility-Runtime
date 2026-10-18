#!/usr/bin/env python3
"""cont101_oracle.py — deterministic raster oracles for the CONT-101 batch.

Usage: cont101_oracle.py <tag>   (tag = pre|post; reads run/cont101/<tag>/)

zo (z-order, screen coords == view coords, window fills 1080x1920):
  PHASE1 raster (zo1): (100,100)RED (200,200)GREEN (300,300)BLUE
                       (950,150)YELLOW (1000,1000)WHITE
  PHASE2 raster (zo2): (200,200)RED (300,300)RED (400,400)BLUE
                       (950,150)YELLOW (1000,1000)WHITE
cv (canvas, custom view at y=20..320, sibling 320..420):
  (75,150)RED (225,150)GREEN (50,50)YELLOW (225,50)GREEN (150,350)BLUE
tx (text ink-band scans on fixed-height boxes):
  bands: tv1 y=20..120 (300 wide), tv3 y=140..220 (320 wide, ellipsize:
  inkRight<=318), tv4 y=240..340 (300, wrapped), tv5 y=360..460 (300),
  tv6 y=480..560 (300, RTL ink exists); gap bands y=120..140, 220..240,
  340..360, 460..480 must be pure bg; L5: tv5 inkTop < tv1 inkTop.
"""
import sys

def load_ppm(path):
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:2] == b'P6', 'not P6: ' + path
    i, fields = 2, []
    while len(fields) < 3:
        while i < len(data) and data[i:i+1].isspace(): i += 1
        if data[i:i+1] == b'#':
            while data[i:i+1] not in (b'\n', b''): i += 1
            continue
        j = i
        while j < len(data) and not data[j:j+1].isspace(): j = j + 1
        fields.append(int(data[i:j])); i = j
    i += 1
    w, h = fields[0], fields[1]
    return w, h, data[i:i + w*h*3]

def px(buf, w, x, y):
    o = (y * w + x) * 3
    return buf[o], buf[o+1], buf[o+2]

def near(c, ref, tol=40):
    return all(abs(a-b) <= tol for a, b in zip(c, ref))

RED, GREEN, BLUE, YELLOW = (0xCC,0x22,0x22), (0x22,0xCC,0x22), (0x22,0x22,0xCC), (0xCC,0xCC,0x22)
WHITE, BG = (0xFF,0xFF,0xFF), (0xEE,0xEE,0xEE)

def ink_bbox(buf, w, x0, x1, y0, y1, bgcolor):
    """bbox of pixels differing from bg by >60 in any channel"""
    t = b = l = r = None
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = px(buf, w, x, y)
            if any(abs(a-bq) > 60 for a, bq in zip(c, bgcolor)):
                if t is None: t = y
                b = y
                if l is None or x < l: l = x
                if r is None or x > r: r = x
    return t, b, l, r

def main(tag):
    base = f'run/cont101/{tag}'
    fails = []
    def check(name, cond, detail=""):
        print(f"  [{'OK' if cond else 'DIVERGE'}] {name} {detail}")
        if not cond: fails.append(name)

    # ---- zo ----
    try:
        w,h,b1 = load_ppm(f'{base}/zo1/screenshot.ppm')
        print(f"zo1 raster {w}x{h}:")
        check("P1 (100,100)RED",  near(px(b1,w,100,100),  RED),  str(px(b1,w,100,100)))
        check("P2 (200,200)GREEN",near(px(b1,w,200,200),  GREEN),str(px(b1,w,200,200)))
        check("P3 (300,300)BLUE", near(px(b1,w,300,300),  BLUE), str(px(b1,w,300,300)))
        check("P4 (950,150)YELLOW",near(px(b1,w,950,150),YELLOW),str(px(b1,w,950,150)))
        check("P5 (1000,1000)WHITE",near(px(b1,w,1000,1000),WHITE),str(px(b1,w,1000,1000)))
    except Exception as e:
        print("zo1 raster UNAVAILABLE:", e); fails.append('zo1-raster')
    try:
        w,h,b2 = load_ppm(f'{base}/zo2/screenshot.ppm')
        print(f"zo2 raster {w}x{h}:")
        check("Q1 (200,200)RED",  near(px(b2,w,200,200),  RED),  str(px(b2,w,200,200)))
        check("Q2 (300,300)RED",  near(px(b2,w,300,300),  RED),  str(px(b2,w,300,300)))
        check("Q3 (400,400)BLUE", near(px(b2,w,400,400),  BLUE), str(px(b2,w,400,400)))
        check("Q4 (950,150)YELLOW",near(px(b2,w,950,150),YELLOW),str(px(b2,w,950,150)))
    except Exception as e:
        print("zo2 raster UNAVAILABLE:", e); fails.append('zo2-raster')

    # ---- cv ----
    try:
        w,h,bc = load_ppm(f'{base}/cv/screenshot.ppm')
        print(f"cv raster {w}x{h}:")
        check("R1 (75,150)RED",   near(px(bc,w,75,150),  RED),   str(px(bc,w,75,150)))
        check("R2 (225,150)GREEN",near(px(bc,w,225,150), GREEN), str(px(bc,w,225,150)))
        check("R3 (50,50)YELLOW", near(px(bc,w,50,50),   YELLOW),str(px(bc,w,50,50)))
        check("R4 (225,50)GREEN", near(px(bc,w,225,50),  GREEN), str(px(bc,w,225,50)))
        check("R5 (150,350)BLUE", near(px(bc,w,150,350), BLUE),  str(px(bc,w,150,350)))
    except Exception as e:
        print("cv raster UNAVAILABLE:", e); fails.append('cv-raster')

    # ---- tx ----
    try:
        w,h,bt = load_ppm(f'{base}/tx/screenshot.ppm')
        print(f"tx raster {w}x{h}:")
        boxes = [('tv1', 300, 20, 120), ('tv3', 320, 140, 220),
                 ('tv4', 300, 240, 340), ('tv5', 300, 360, 460),
                 ('tv6', 300, 480, 560)]
        inks = {}
        for name, bw, y0, y1 in boxes:
            t,b,l,r = ink_bbox(bt, w, 0, bw, y0, y1, BG)
            inks[name] = (t,b,l,r)
            inside = (t is not None and t >= y0 and b < y1 and r < bw)
            check(f"TX-L1 {name} ink-inside-box", inside,
                  f"ink=(top{t},bot{b},left{l},right{r}) box=y{y0}..{y1} w{bw}")
        for gy0, gy1 in [(120,140),(220,240),(340,360),(460,480)]:
            t,b,l,r = ink_bbox(bt, w, 0, 340, gy0, gy1, BG)
            check(f"TX-L2 gap y{gy0}..{gy1} pure-bg", t is None,
                  f"ink=(top{t},bot{b},left{l},right{r})")
        # L3: tv3 ellipsize — ink right edge strictly inside 320
        t,b,l,r = inks['tv3']
        check("TX-L3 tv3 ellipsize capped", t is not None and r <= 318, f"inkRight={r}")
        # L4: tv4 wraps inside box (ink exists, bottom < 340)
        t,b,l,r = inks['tv4']
        check("TX-L4 tv4 wrapped-inside", t is not None and b < 340, f"inkBot={b}")
        # L5: includeFontPadding law — with the primary face fm.top ==
        # fm.ascent (-45), AOSP predicts NO ink-top delta between tv1
        # (ifp=true) and tv5 (ifp=false): the BOX-RELATIVE ink tops must
        # be EQUAL (the metrics rows carry the law proof; a font with
        # top<ascent would produce a delta — the G47 branch is live).
        t1 = inks['tv1'][0]; t5 = inks['tv5'][0]
        rel1 = t1 - 20 if t1 is not None else None      # tv1 box y=20
        rel5 = t5 - 360 if t5 is not None else None     # tv5 box y=360
        check("TX-L5 tv5 box-relative inkTop == tv1 (top==ascent font law)",
              rel1 is not None and rel5 is not None and rel5 == rel1,
              f"rel1={rel1} rel5={rel5}")
        # L6: RTL ink exists
        t,b,l,r = inks['tv6']
        check("TX-L6 tv6 RTL ink-exists", t is not None, f"ink=(top{t},bot{b})")
    except Exception as e:
        print("tx raster UNAVAILABLE:", e); fails.append('tx-raster')

    print("ORACLE FAILS:", len(fails), fails if fails else "(none)")
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'pre'))
