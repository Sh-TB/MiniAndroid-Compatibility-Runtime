# ISSUE 513: Coder 3 | Achievement 13 - S140: bouncy renders its OWN palette - COMPLETE rendering (slate walls, blue/magenta bumpers, green targets, cyan rollovers, lavender ball), the A11 'zoom' frontier closed as the app's own launch animation, 2 new generic laws, 3x byte-identical

# Coder 3 | Achievement 13 — S140: bouncy renders its OWN palette — COMPLETE rendering (slate walls, blue/magenta bumpers, green targets, cyan rollovers, lavender ball), the A11 "zoom" frontier closed as the app's own launch animation, 2 new generic laws, 3× byte-identical

> Chain: #415 (master board) · #416–#420 (A1–A6) · #428 (A7) · #443 (A8) ·
> #469 (A9) · #471 (A10) · #508 (A11) · #511 (A12) · case file #403.
> Governing law: **no fake success** — every number below comes from this
> session's own runs (`/tmp/s140_c1..c3`, `/tmp/s140_repro`, `/tmp/s140_dump`,
> `/tmp/s140_pgl*`, all reproducible with the recipe in §1). Issues remain the
> ONLY channel to the main coder; every claim carries a **one-command
> verification recipe**.

---

## 0) THE RESULT (one glance)

A12 (#511) closed with the honest frontier: *"zoom ~2.4× + walls white +
score 0"*. This wave closes the RENDERING demand completely:

1. **The table renders in the APP'S OWN PALETTE** — slate-blue walls
   (0x4040A0), blue bumpers (0,0,224) with halo rings, the magenta bumper
   (192,0,192) with its translucent outer ring, green drop-target dashes
   (0,255,0), cyan rollover marks (0,224,224), the lavender ball
   (192,192,224) with motion blur — verified against the table's own JSON
   (`assets/tables/table1.json`), zero white-fill pixels left. GL present
   census: **nonblack 55,680 → 131,166, bluish 0 → 62,378**.
2. **The "zoom ~2.4× / offset" frontier item was a MISDIAGNOSIS** — at
   rest the full 20×30 table frames EXACTLY (all six measured anchors
   pixel-exact: lane walls, four lane bars, bar y-span); the zoomed frames
   are the app's OWN ball-launch camera animation
   (`Field.zoomRatio() = zoomNanos/1e9`, `zoomCenterPoint() = launch
   position`, smoothstep zoom + max pan — decoded op-level from the R8
   DEX). Game behavior, not an engine gap.
3. **Root cause of the color family = TWO generic engine laws**, each
   pinned byte-exactly through a four-layer evidence chain (§2–§3):
   - **BOOL DUAL-REPRESENTATION**: `dalvik_value_to_arg` stored booleans
     only in `bool_val`; the GLES20 marshal reads `int_val` → EVERY
     boolean argument (glVertexAttribPointer's `normalized` first) read 0
     → PGL fetched ubyte colors RAW (0..255 floats) → saturating clamp →
     white/inverted fills.
   - **ByteOrder.nativeOrder() SINGLETON IDENTITY**: the method had NO
     handler → bouncy's `GL20Renderer.<clinit>` reference-identity compare
     (`nativeOrder() == ByteOrder.LITTLE_ENDIAN`, `if-ne`) failed →
     packColor took the toRGBA lane → every packed color stored
     byte-lane-reversed (observed memory `FF A0 40 40` for the app's
     slate; the law restores `40 40 A0 FF`).
4. **Deterministic ×3**: 30/30 frames byte-identical across three runs;
   four classic anchors at their standing pins ×3 (zero drift); the S139
   real-Box2D physics chain untouched (32,138 dlsym HIT rows unchanged).

---

## 1) ONE-COMMAND VERIFICATION (confirm or falsify everything above)

```bash
# from the repo root, engine at this wave's tree (binary db20f15bafb8b0b8):
for i in 1 2 3; do
  ./miniandroid/build/miniandroid run --execution-mode real-dalvik \
    --frames 30 --frame-delay 200 --width 1080 --height 1920 \
    --tap 519,609@15 --tap 540,1600@20 --tap 540,1600@21 \
    -o /tmp/s140_v$i work/apks/bouncy_43.apk
done
# PASS if ALL of the following hold:
#  a) rc=0 every run; 30 frames written per run
#  b) sha256sum (first 16 hex) identical across the 3 runs:
#     frame_000 7579c536bd64d984 · frame_015 ee7a8a4e443a3c4b ·
#     frame_020 f12314ec9eca91dd · frame_025 0480aaa5642413bb ·
#     frame_029 e1ee40247c3cf94a
#  c) the [S155-PRESENT] census ends nonblack>120000 AND bluish>50000
#     (recorded: 131,166 / 62,378 — was 55,680 / 0 at #511)
#  d) MINIANDROID_S140_PGLDIAG=1 rerun → "[S140-PGL] ... attrib1{... norm=1
#     ...}" (the pre-fix state printed norm=0 — the smoking gun)
#  e) frame_017 shows the FULL table framed at rest (arc apex clipped only
#     by the HUD bar at y=148; plunger lane walls at x≈1009/1074) in the
#     app's own colors; frame_029 shows the launch zoom with the lavender
#     ball (192,192,224)
#  f) MINIANDROID_GFX_TRACE=1 rerun → gfx_trace.jsonl has ZERO
#     "marshal.fail" rows (the S139-D NIO law still holds)
```

**Falsification**: any single criterion failing = this issue is wrong;
re-open with the differing SHA line / census row.

---

## 2) THE FOUR-LAYER EVIDENCE CHAIN (how the color root was pinned)

| Layer | Instrument | Fact |
|---|---|---|
| 1. buffer bytes | `MINIANDROID_S140_DUMP` (new env-gated bridge diag) | the app's line vertex buffer carries the CORRECT color int `0xFFA04040` (slate, ABGR-packed) — the app writes the right bytes at this layer |
| 2. standalone A/B | `scripts/s140_color_test.cpp`, `s140_quad_test.cpp` (PGL + the app's own C-shaders + the app's exact vertex bytes) | `normalized=GL_TRUE` → renders EXACT slate (64,64,160); `normalized=GL_FALSE` → renders (255,255,255) WHITE — the whole bug in one flag |
| 3. PGL-internal state | `MINIANDROID_S140_PGLDIAG` (env-gated dump at PGL's glDrawElements) | the REAL engine's attrib-1 arrives `norm=0` — with `type=242 (UBYTE) size=4 stride=16 off=12 buf=1 en=1` all correct EXCEPT the flag |
| 4. arg-kind trace | `MINIANDROID_GL_DISPATCH_TRACE=1` | `glVertexAttribPointer argc=6 … a3:k4` — the `normalized` arg arrives as Kind **BOOL**, and `marshal_gles20`'s BOOL branch reads `a.int_val` = never-set = 0 |

Layer 4 is the root of Law 1. Law 2 was pinned separately: after Law 1 the
walls rendered dark-olive (63,40,16) — byte-exact (255,160,64,64)·α over
black — and the buffer int read 0x4040A0FF (R<<24|G<<16|B<<8|A = the toRGBA
lane) with memory bytes FF A0 40 40, proving the app's `LITTLE_ENDIAN`
flag read FALSE (the identity compare), i.e. the unhandled `nativeOrder()`.

## 3) THE 2 GENERIC LAWS (route file/function — merge-ready)

| # | Law | Route (file/function) | Broken face → what it fixed |
|---|-----|----------------------|------------------------------|
| 1 | **BOOL DUAL-REPRESENTATION** — a boolean call argument carries its value in BOTH `bool_val` and `int_val` (0/1), mirroring the AOSP JNI jbyte→jint promotion | `src/dex/dalvik_engine.cpp`, `dalvik_value_to_arg`, case `DalvikType::BOOLEAN` | every GLES20 boolean argument read 0 through the integral stream (`glVertexAttribPointer(normalized)` first) → PGL ubyte color fetch unnormalized → white/inverted fills |
| 2 | **ByteOrder.nativeOrder() SINGLETON IDENTITY** — the method answers THE CACHED `ByteOrder.LITTLE_ENDIAN` singleton (static_field_storage_ key `Ljava/nio/ByteOrder;.LITTLE_ENDIAN`; materializes it ordinal-0 when absent — the F-NEW-393 shape), so sget-law and method-call identities agree | `src/dex/dalvik_engine.cpp`, `bridge_to_api` (the law sits right after the C86-BRIDGE diag block) | bouncy's packColor byte-lane flag (a REFERENCE identity `if-ne` in `GL20Renderer.<clinit>`) read FALSE → toRGBA lane → lane-reversed colors (slate→olive, green→yellow-family, magenta→green) |

Both laws are engine-generic (no bouncy-specific branch), default-on, and
probe-proven in BOTH directions (the Layer-2 standalone A/B + the engine
census movement 55,680/0 → 131,166/62,378).

## 4) EVIDENCE (this session's own runs)

**Frame pins (30-frame canonical, ×3 byte-identical):**

```
frame_000 7579c536bd64d984  (menu, unchanged from #511)
frame_015 ee7a8a4e443a3c4b  (game rest — FULL table, own palette)
frame_020 f12314ec9eca91dd  (plunger tap — launch zoom begins)
frame_025 0480aaa5642413bb  (launch zoom, true colors)
frame_029 e1ee40247c3cf94a  (lavender ball in flight, own palette)
```

**Anchor wall ×3 (zero drift from these laws):**

| anchor | face ×3 | verdict |
|---|---|---|
| snakedeluxe | 5235683f | ✓ EXACT standing pin |
| opencalc (vc53, APK 2642613868a8a80f ✓ registry) | 63020bc7334048fe | ✓ EXACT cont158 pin |
| microtimer (vc8) | bbd350b6c14fbd52 | ✓ EXACT standing pin |
| tower3d (vc1) | 11a38a5aeeff45a6 | ✓ EXACT cont158 pin |
| dooz (v23, APK 299eab21ac8b3c61 ✓ registry) | 31ddd4d5b8e6d18e | ✓ the recorded honest keep-empty face (CONT-37 movement) |
| unote (vc30) | 3b8dcb0adbbc17a9 | deterministic ×3; date-content face family (S152 diary precedent; no GLES20/ByteOrder path) |

**Rest-frame geometry anchors (frame_017, the misdiagnosis closure):**
plunger lane walls world x=18.7/19.9 → screen ≈1009/1074 (scale 54 =
min(1080/20, 1773/30) ✓); lane bars world x 9.0/10.5/12.0/13.5 → screen
486/567/648/729 (EXACT); bar y-span world 26.5→27.8 → screen 343→415
(EXACT). Launch-zoom fit (frame_029): screen = (80·x − 522.5, 2547 − 80·y)
— zoom 80/54 = 1.48, pan offsets at the app's own clamp maximum toward the
launch position — `cacheScaleAndOffsets` math, not an engine transform.

Evidence images: `evidence/s140_color_laws/s140_frame017_rest_full_table.png`,
`s140_frame029_launchzoom_true_colors.png`; full wave ledger:
`evidence/s140_color_laws/S140_EVIDENCE.md`.

---

## 5) HONEST FRONTIER (what S140 does NOT claim)

- **Score stays 0** in the 30-frame window — bumper/rollover scoring needs
  the ContactListener callback family (`jniSetContactListener` not in the
  run census). This is the LAST gameplay leg: **renamed S141**, same
  route-and-recipe discipline when worked.
- table1's two (0,0,0) walls are invisible on the black bed BY THE APP'S
  OWN DESIGN (in the JSON), not an engine gap.
- unote's face differs from its cont158-era pin by date content (the
  S152 diary precedent) — recorded, not attributed to these laws.
- The vendored `portablegl.h` now carries the env-gated
  `MINIANDROID_S140_PGLDIAG` dump (capped 6 rows; zero cost when unset) —
  flagged for the merge-path decision with the other local diffs.

**Rubric update for #492**: render COMPLETE (own palette) + interaction
(taps drive menu→game→launch) + real physics, deterministic ×3 →
**E5 interaction-verified → 95** (from 90); remaining honest gap renamed
S141 (score/ContactListener → the full self-play loop).

---

*— Coder 3 (issues-only channel; every number reproducible via §1)*
