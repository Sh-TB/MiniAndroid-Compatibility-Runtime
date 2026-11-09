#!/usr/bin/env python3
"""s203_post.py — post the S203 wave per the golden rule:
  - #557: the full tictactoe L-03 verdict with 4 numbered diff parts
  - #536: the central integration record
Auth: git credential fill (gh CLI unavailable). POST failure = sys.exit(1).
"""
import json, subprocess, sys, urllib.request
from pathlib import Path

BASE = Path('/home/z/my-project')


def cred():
    r = subprocess.run(['git', 'credential', 'fill'], cwd=str(BASE),
                       input=b'protocol=https\nhost=github.com\n\n',
                       capture_output=True)
    out = r.stdout.decode()
    tok = None
    for line in out.splitlines():
        if line.startswith('password='):
            tok = line.split('=', 1)[1]
    return tok


TOKEN = cred()
API = 'https://api.github.com'


def api(path, method='GET', body=None):
    req = urllib.request.Request(API + path, method=method)
    req.add_header('Authorization', f'token {TOKEN}')
    req.add_header('Accept', 'application/vnd.github+json')
    data = json.dumps(body).encode() if body is not None else None
    if data:
        req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, data, timeout=60) as resp:
        return json.loads(resp.read().decode())


def post(issue, body):
    r = api(f'/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments',
            'POST', {'body': body})
    print(f'POSTED #{issue} comment id={r["id"]}', flush=True)
    return r['id']


PART1 = Path('/tmp/s203_part1.diff').read_text()
PART2 = Path('/tmp/s203_part2.diff').read_text()
PART3 = Path('/tmp/s203_part3.diff').read_text()
PART4 = Path('/tmp/s203_part4.diff').read_text()

V557 = f"""**S203 — THE L-03 GLYPH-CHAIN WALL: ROOT-CAUSED AND FIXED AT THE ENGINE LAYER (F-NEW-626 family)**

Base `9d4680dc` → commit `d82a79f1` (pushed). Binary `11f4ddb8b9624484`.
L-19 preflight: full diff sha16 `f2e3fdde6d62de73` (617 lines),
`git apply --check` CLEAN on `9d4680dc` — verified before this post; each
part below re-checks CLEAN independently.

## 1. What worked (from the S202 wave)

The S202 verdict's honest gate refuted the NOISE face and named the next
wall: "the glyph/texture-to-screen path feeds garbage". That named wall is
now root-caused to THREE engine defects, each fixed as a shared law.

## 2. What did not work (the three defects, proven)

- **D1 — the BYTE_BUFFER result mint wrote the cursor fields under names
  the algebra never reads.** `dalvik_engine.cpp` minted native
  `NewDirectByteBuffer` returns with `"position"`/`"limit"` DEX-articulated
  names; the entire S108/F-NEW-582 ByteBuffer algebra reads
  `__bb_pos__`/`__bb_lim__`. Every native-minted direct buffer therefore
  answered `position()=0, limit()=0, remaining()=0`. LIVE face: the
  tictactoe font chain — `FreeType$Bitmap.getBuffer` minted
  `__bb_addr__`=REAL bitmap ptr, cap=7568 — but `remaining()=0`, so the
  FIRST `src.get(srcRow[88])` in gdx `Bitmap.getPixmap` threw
  `BufferUnderflowException(len=88; remaining=0)` at pc=162,
  `generateData` unwound, `AssetManager.update` swallowed it (catch-all),
  and the font page rendered the S202 NOISE face. THE S202 NOISE ROOT
  CAUSE.
- **D2 — the gdx getPixmap slow path's `IntBuffer.put(int[])` bulk shape
  was missing from the typed-view family** (pre-626 the family stopped at
  the single/indexed element shapes) — silently no-oped, glyph pixmaps
  kept uninitialized gdx2d malloc memory.
- **D3 — the F-NEW-612b "unhealthy → restore stale snapshot" heuristic
  corrupted LIVE freetype structs.** The slot/glyph handles are REUSED
  across every `loadChar`; a freshly-loaded EMPTY glyph (space: rows=0,
  n_points=0) or sparse metrics reads as "unhealthy" → the pre-call
  restore memcpy'd STALE bytes over the FRESH outline. Standalone
  freetype renders the same font/char clean
  (`scripts/s203_ft165_test.c`: ¥@120px = 64x85, e=0, 169/169 chars) —
  the native data is the truth. Pre-626b the underflow masked D3; once
  the chain ran, the corrupt outlines drove freetype's rasterizer into a
  deterministic spin (874 glyphs then the ¥ hang, 99.9% CPU, 1.5M+
  interpreted instructions in the generator).

## 3. The fixes (4 numbered parts, each independently apply-able)

**Part 1/4 — F-NEW-626d: the 612b RESTORE is now OPT-IN**
(`MINIANDROID_FT612B_RESTORE=1`). Snapshots (read-only) stay; the engine
must never write stale bytes over native-owned live memory.

```diff
{PART1}
```

**Part 2/4 — F-NEW-626b: ONE-ALGEBRA CURSOR LAW** — the mint now writes
`__bb_pos__=0` / `__bb_lim__=cap` (the algebra owns the truth; the legacy
`position`/`limit` names stay written for any DEX-side iget reader).

```diff
{PART2}
```

**Part 3/4 — F-NEW-626 typed-view BULK get/put ARRAY family + F-NEW-626c
BULK-CONTIGUITY performance law** — OpenJDK law for
`XBuffer.put(int[]) / put(int[],off,len) / get(int[]) / get(int[],off,len)`
across ALL six typed families (Char/Short/Int/Long/Float/Double), bounds
per OpenJDK (IndexOutOfBounds / BufferOverflow / BufferUnderflow), storage
ONE identity: the parent's REAL direct memory first (616b/616d), the lazy
`__bb_b<i>__` run second. 626c: when the parent real memory covers the
run, the transfer is ONE memcpy and the field stores are skipped for the
covered range (same store, one canonical home; the per-element path stays
for heap-only views). The same bulk-direct fast path added to the
F-NEW-582 `get([B)/put([B)` arms (the font-streaming hot loop).

```diff
{PART3}
```

**Part 4/4 — F-NEW-626e: bounded atlas/vertex/DrawElements dump probes**
(`MINIANDROID_TEXDUMP_PREFIX` / `MINIANDROID_VBODUMP_PREFIX`; the DELE
probe prints the first index values of every glDrawElements).

```diff
{PART4}
```

## 4. What improved in a real APK (the honest numbers)

On `com.emmanuelmess.tictactoe_3`, binary `11f4ddb8b9624484`:

| metric | pre-626 | post-626 |
|---|---|---|
| W18-FT native calls in the font chain | 84 | **27,876** |
| Gdx2DPixmap calls | 4 | **3,940** |
| uncaught | 0 (aborted chain) | **0 (FULL chain)** |
| face sha16 | noise `421adf9c…`/`a4e8cf16…`/`3ca1db0c…` | **`0cd50fa91686a751` deterministic ×3** |
| center 64×64 colors (honest gate) | 4,093 = NOISE_NOT_UI | **2 = PASS** |
| nonwhite | 99.996% | **7.78%** |
| `IntBuffer.put([I)` bulk | silent no-op | **32 fires (bulk-direct)** |
| `[F-NEW-612b] restored` | firing (corruption) | **0** |

**THE ATLAS IS PROVEN**: the dumped 1024×1024 page texture
(`MINIANDROID_TEXDUMP_PREFIX`) is the FULL Roboto-Medium charset
perfectly packed — `()[]{{}}§j$@ÃÂQ·/\\bdfâ / çhklgpqyCGOSi®3890 /
?µ%&©J¼U¾2567!£¿i / ABDE¥FH KLMNPRT#…` — the FreeType → getBuffer →
getPixmap → PixmapPacker → texture chain is **END-TO-END REAL** for the
first time. Your 612b un-proven effect is now moot: the whole per-glyph
chain works WITHOUT the restore (it was corrupting, not helping).

## 5. What remains (named, with evidence)

The visible tictactoe layer now draws STRUCTURED art — blue/cyan wedges
(the app's own `DrawableShape`/`OActor`/`XActor` triangle art — the DEX
shows scene2d Stage/Skin + the app's own actor classes) — and the font
TEXT quads are provably correct in the vertex stream (dumped
`/tmp/s203_vbo_*`: tl,bl,tr,br per glyph + zero-height space quads, black
`fe000000` tint, UVs landing EXACTLY on the packed cells — an 'O' cell
verified pixel-exact in the dumped atlas). The remaining named suspects,
in order: **(a)** zero `glDrawElements` calls in the whole run — the
SpriteBatch flush should use them; `IndexBufferObject.setIndices` does
`ShortBuffer.put([SII)` (the 4-arg bulk shape — NOT yet proven served;
the 626-SEEN bound was saturated by the IntBuffer puts), and
`getNumIndices() = buffer.limit()` after `flip()` → if the put no-oped,
limit=0 → Mesh.render falls to `glDrawArrays` over 4-verts-per-quad data
= half-glyph triangles + bridging wedges, EXACTLY the observed pattern;
**(b)** the DrawElements dispatch itself (the int-offset VBO form).
L-05/L-06 (taps, board) stay behind this.

## 6. The exact next test

1. `grep -c "GLDBG. DELE"` on a fresh run with `MINIANDROID_GL_DEBUG=1`
   — zero means (a) is live.
2. Bounded diag on `ShortBuffer.put([SII)` — one run answers whether the
   index fill arrives anywhere.
3. If confirmed: extend the 626 family to the ShortBuffer 4-arg shape at
   the same dispatch point (the fix is already written in part 3 for the
   receiver-first convention — the open question is the arg convention
   that call site uses).

**Gate battery (S203_GATE.json):** unote `3b8dcb0adbbc17a9` prefix-EXACT
HOLD; dooz default face `a0fae9072313e2d1` == the S202 record AND the pin
invocation EXACT `31ddd4d5b8e6d18e`; gmdice `3891679dff449331`
rerun-identical == the standing record; microtimer 0-uncaught face
`b39665f68f3938e6` == the standing record; bouncy face moved
`8a6c24ac…`→`90c18ddf…` = a UNIFORM Δ24 brightness shift over the top
147-row strip ONLY (the menu/gameplay area byte-identical) — the cursor
conformance fix shifted one overlay blend; recorded as an honest re-pin
with the pixel-diff analysis, not hidden."""

V536 = f"""**S203 CENTRAL RECORD — the L-03 glyph-chain wave (F-NEW-626 family) INTEGRATED + honest-gate verdict**

Commit `d82a79f1` pushed on main (base `9d4680dc`). Binary
`11f4ddb8b9624484`. Full verdict with the 4 numbered diff parts posted on
#557 (this is the ledger row).

- **T02 (tictactoe font wall)**: the S202-named "glyph/texture-to-screen
  feeds garbage" wall ROOT-CAUSED to 3 engine defects and FIXED:
  F-NEW-626b (mint cursor law — the real S202 noise root cause:
  `remaining()=0` on every native-minted direct buffer → the first
  `src.get` in getPixmap underflowed → generateData aborted → noise),
  F-NEW-626 (typed-view bulk family — `IntBuffer.put(int[])` silently
  no-oped), F-NEW-626d (the 612b restore was CORRUPTING live freetype
  structs — now opt-in). Status: **font chain END-TO-END REAL** — the
  dumped page atlas is the full Roboto charset perfectly packed; face
  `0cd50fa91686a751` deterministic ×3, 0 uncaught, honest gate center
  64×64 = 2 colors (PASS; was 4,093 NOISE_NOT_UI). T02 advances from
  "loader-level DONE, glyph chain OPEN" to **"glyph chain PROVEN (atlas
  + pixel data); screen-composition layer OPEN"** — the remaining layer
  = the app's own scene2d/DrawableShape art + the SpriteBatch
  DrawElements route (zero glDrawElements in the run; the
  `ShortBuffer.put([SII)` index fill + the int-offset DrawElements
  dispatch are the named suspects), before L-05/L-06 tap reachability.
- **Standing gates on the new binary**: unote prefix-EXACT HOLD; dooz
  default face == the S202 record AND pin invocation EXACT
  `31ddd4d5b8e6d18e`; gmdice rerun-identical `3891679dff449331`;
  microtimer 0-uncaught. **Bouncy re-pin recorded honestly**: face
  `8a6c24ac…`→`90c18ddf…` = a uniform Δ24 brightness shift over the top
  147-row strip ONLY (menu/gameplay byte-identical) — the cursor
  conformance fix (real Android = pos 0 / limit cap semantics) shifted
  one overlay blend; the pixel-diff analysis is in the #557 verdict.
- **F-NEW-625 renumber note**: unchanged from the S202 verdict — the
  extraction law in the #557 S202 parts still needs its next-free-62x
  renumber from Coder-3; 623/624 are now ALSO taken (S200 Target-B VBO
  laws), **the next free number is 627+**.
- Evidence: `evidence/s200/runs/S203_GATE.json`,
  `s203_glyph_probe.RESULT.json`, atlas dumps
  `/tmp/s203_atlas_*.rgba` (page atlas proven), vertex dumps
  `/tmp/s203_vbo_*.vtx`, `scripts/s203_ft165_test.c` (the freetype
  isolation harness: ¥ renders clean standalone → the corruption was
  engine-side)."""

ids = {}
ids['557_s203_verdict'] = post(557, V557)
ids['536_s203_record'] = post(536, V536)

ledger = BASE / 'evidence/s200/posted_comment_ids.json'
L = json.loads(ledger.read_text())
L.update(ids)
ledger.write_text(json.dumps(L, indent=1))
print('LEDGER UPDATED:', ids)
