#!/usr/bin/env python3
"""s203_recon.py — offline reference render from the S203 dumps.

Takes the dumped interleaved SpriteBatch vertex run (vtx) and the dumped
atlas (rgba) and rasterizes the quads with PIL, applying the SpriteBatch
projection (u_projTrans m00=1/1080, m31=-1, m32=-1 — y-down screen space)
and per-quad UV sampling. Output: reference frame + per-quad atlas cell
strip, to compare against the real screenshot.
"""
import struct, sys
from PIL import Image

V = sys.argv[1] if len(sys.argv) > 1 else '/tmp/s203_vbo_0_count30.vtx'
A = sys.argv[2] if len(sys.argv) > 2 else '/tmp/s203_atlas_0_1024x1024.rgba'
OUT = sys.argv[3] if len(sys.argv) > 3 else '/tmp/s203_recon.png'

atlas = Image.frombytes('RGBA', (1024, 1024),
                        open(A, 'rb').read())
data = open(V, 'rb').read()
n = len(data) // 20
verts = [struct.unpack_from('<5f', data, i * 20) for i in range(n)]
# gdx quad = 6 verts (0,1,2, 2,3,0) — DrawArrays count is multiple of 6
# for pure quads; here count=30 = 5 quads IF drawn as tri-pairs, but gdx
# uses indices — DrawArrays with count=30 means the mesh already holds
# EXPANDED triangles? No — SpriteBatch draws with glDrawElements on the
# index buffer... this dump came from glDrawArrays count=30: treat as
# 30 consecutive verts = 10 triangles; pair them per triangle.
print('verts:', n)

W, H = 540, 480
ref = Image.new('RGB', (W, H), (255, 255, 255))
px = ref.load()

def sample(u, v):
    ax, ay = int(u * 1024) % 1024, int(v * 1024) % 1024
    r, g, b, a = atlas.getpixel((ax, ay))
    # SpriteBatch shader: gl_FragColor = v_color * tex; color black a=254
    # → final = tex.rgb * 0 (black) + ... actually color*texture:
    # black text: rgb=0, alpha = tex.a * color.a
    return (0, 0, 0, int(a * (254 / 255.0)))

# project: u_projTrans maps x*0.00277778 - 1, y*0.00277778*(-1)? The mat4
# printed: m00=0.00277778 m30=-1 m31=-1 m32=-1 m33=1 → clip = (x*s -1,
# -y*s*? ...). Simpler: gdx y-up world → screen y-down flip. We just
# normalize: screen_x = x, screen_y = 1920 - y (flip), scale 0.5.
def scr(x, y):
    return int(x * 0.5), int((1920.0 - y) * 0.5)

for t in range(0, n - 2, 3):
    p0, p1, p2 = verts[t], verts[t + 1], verts[t + 2]
    s0, s1, s2 = scr(p0[0], p0[1]), scr(p1[0], p1[1]), scr(p2[0], p2[1])
    uv0, uv1, uv2 = (p0[3], p0[4]), (p1[3], p1[4]), (p2[3], p2[4])
    minx = max(0, min(s0[0], s1[0], s2[0]))
    maxx = min(W - 1, max(s0[0], s1[0], s2[0]))
    miny = max(0, min(s0[1], s1[1], s2[1]))
    maxy = min(H - 1, max(s0[1], s1[1], s2[1]))
    d = ((s1[0] - s0[0]) * (s2[1] - s0[1]) -
         (s2[0] - s0[0]) * (s1[1] - s0[1]))
    if abs(d) < 1e-9:
        continue
    for yy in range(miny, maxy + 1):
        for xx in range(minx, maxx + 1):
            w0 = ((s1[0] - s0[0]) * (yy - s0[1]) -
                  (xx - s0[0]) * (s1[1] - s0[1]))
            w1 = ((xx - s0[0]) * (s2[1] - s0[1]) -
                  (s2[0] - s0[0]) * (yy - s0[1]))
            w2 = d - w0 - w1
            if w0 < 0 or w1 < 0 or w2 < 0:
                continue
            lu = (uv0[0] * w0 + uv1[0] * w1 + uv2[0] * w2) / d
            lv = (uv0[1] * w0 + uv1[1] * w1 + uv2[1] * w2) / d
            r, g, b, a = sample(lu, lv)
            if a > 60:
                px[xx, yy] = (int(0), int(g * 0), int(b * 0))
ref.save(OUT)
print('saved', OUT)

# atlas cell strip: per quad, crop the uv rect
strip = Image.new('RGB', (1024, 200), (255, 255, 255))
sx = 0
for q in range(0, n - 3, 6):
    u1, v1 = verts[q][3], verts[q][4]
    u2, v2 = verts[q + 3][3], verts[q + 3][4]
    x1, y1, x2, y2 = (int(u1 * 1024), int(v1 * 1024),
                      int(u2 * 1024), int(v2 * 1024))
    if x2 - x1 <= 0 or y2 - y1 <= 0:
        continue
    c = atlas.crop((x1, y1, x2, y2)).convert('RGB')
    if sx + (x2 - x1) < 1024:
        strip.paste(c, (sx, 4))
        sx += x2 - x1 + 2
strip.save(OUT.replace('.png', '_cells.png'))
print('saved cells strip')
