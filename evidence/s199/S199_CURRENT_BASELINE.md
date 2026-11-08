# S199 CURRENT BASELINE

Recorded: 2026-11-08 20:03 UTC

## Environment
- Runtime repo: `/home/z/my-project/miniandroid` (branch `main`)
- HEAD at wave start: `74d7693a` (S195 integration line, binary 31be843614e67bab)
- HEAD at S199 close: `89682811`
- Working tree at close: DIRTY: M evidence/s188_w18/floor_rerun/FLOOR_RERUN.json
 M evidence/s188_w18/floor_rerun/floor_rerun.partial.json
 M evidence/s

## Canonical integrated binary
- Path: `miniandroid/build/miniandroid`
- SHA-256: `414332acd3603dacc2bd0c66251975998ee77384089384c7f47b8b3b339d335b`
- sha16 (evidence records): `414332acd3603dac`
- Built from HEAD with `make -j$(nproc)` (reproducible-build law: rebuild
  from the same tree reproduces the same sha16 — re-verified this wave)

## What changed this wave (S199 P0 chain)
Laws ported / implemented on top of the S195 line (all committed):
| Law | Source | Content |
|---|---|---|
| F-NEW-580 | C3 S196 | S100 String-family receiver identity-form normalization (heap-String OBJECT_REF read via `__string_value__`/`value`) |
| F-NEW-580b | C3 S196 | bridge_to_api boundary String receiver normalization (the ONE chokepoint; alias keeps zero cost for non-heap receivers) |
| F-NEW-582 | C3 S196 | engine allocateDirect + newDisposableByteBuffer mint REAL calloc'd backing, register through the f590 hook (ONE registry — no second registry per mission §4 C6) |
| F-NEW-582 put/get mirror | C3 S196 | ByteBuffer bulk put([B)/put(ByteBuffer)/get([B) + put_wide/get_wide real-memory mirror |
| F-NEW-582b | C3 S196 | BufferUtils.copyJni 5-arg byte form (engine-side REAL law, structural arg resolution) |
| F-NEW-588 | C3 S196 | heap-String replace family: replaceAll/replaceFirst/replace(CharSequence)/replace(CC)/matches/contains with real regex semantics (regex_error falls through honestly) |
| F-NEW-589 | C3 S196 | java.util.Stack REAL LIFO (push/pop/peek/size/empty; AssetManager taskQueue) |
| F-NEW-587 | C3 S196 | GLES20.glGetString GL_EXTENSIONS law (GLTexture.<clinit> supportsExtension) |
| F-NEW-610 | C3 S198c | typed-view position(int)/limit(int) setters (reconstructed from the truncated part-2/2 tail, defect #557 6725597246) |
| F-NEW-615 | S199 W19a | zero-capacity direct-buffer validity (AOSP: 0-cap direct ByteBuffer is well-formed; NewDirectByteBuffer(pixels,0) must answer a box) |
| F-NEW-616 | S199 W19a | GL marshal TYPED-VIEW PARENT-FIRST resolution (the view's own f590 lookup took the zeroed __bb_b{i}__ snapshot leg) |
| F-NEW-616b | S199 W19a | typed-view put/get PARENT MIRROR (one identity, engine writer surface) |
| F-NEW-616c | S199 W19a | GL out-param write-back mirrors into parent memory (glGetShaderiv/glGetIntegerv/gen*) |
| F-NEW-616d | S199 W19a | one identity, TWO mint forms: `__bb_addr__` (native-mint) resolved everywhere alongside `__bb_direct__` (engine-mint) |
| F-NEW-617 | S199 W19a | copyJni 4-arg ELEMENT copier ([F Buffer I I — Mesh.setVertices rides it; real native disasm 0x67f0: memcpy(GetDirectBufferAddress(dst), src+off*esz, num*esz)) |
| F-NEW-618 | S199 W19a | [F raw-bits element law in the GLES marshal (F-028 dual convention: INT32-stored float element = raw bits; get_object_array_float_element) |

## Gates at close
- Goldens 3/3 HOLD (bouncy 8a6c24ac, unote 3b8dcb0a, dooz 31ddd4d5) — evidence/s199/../s188_w18 chain, rerun on 414332acd3603dac
- Floor 11/11 CLEAN — scripts/s188_w18_floor_rerun.py output
- gmdice 5-tap interactive regression PRESERVED (5 taps → 5 distinct result states, rerun identical)
