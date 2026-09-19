# S67 · MY OWN FAN-OUT-FIRST CENSUS (ordered by "smallest primitive × most consumers")

Snowball law: a wrong base primitive does not stay local — every later line of DEX,
every View, every resource compiled on top of it inherits the error. This list is
ordered by `consumers × depth`, not by how loud the symptom is. Every entry carries
evidence from this session's source census (file:line in the respective matrix).

## TIER A — silent-wrongness primitives (produce plausible-but-wrong pixels/state)

| # | Primitive | Evidence | Fan-out | Class |
|---|---|---|---|---|
| A1 | `?attr/x` in layouts silently mis-queried as resource id (no theme-attr branch at inflate) | layout_inflater.cpp:787-1185 (no branch); theme path only via obtainStyledAttributes android_shadows.cpp:2113-2150 | every Material/AppCompat app; OPMT family | RESOURCE |
| A2 | `Resources.getDimensionPixelSize` seeded with UNCONVERTED mantissa (raw dp as px) | execution_engine.cpp:571-578, dalvik_engine.cpp:23895-23917 | every app reading dimens | RESOURCE |
| A3 | Non-PNG-magic drawable (WebP/JPEG) → silent blank, no decode attempt, no placeholder | execution_engine.cpp:2322-2373 | every image-heavy app | IMAGE |
| A4 | INVISIBLE(4) views are DRAWN (only GONE prunes) | layout_inflater.cpp:2360, execution_engine.cpp:2619 | visibility-dependent UIs | RENDER |
| A5 | Canvas `Paint.setARGB` unhandled → color stays 0xFF000000 | canvas_shadow.cpp:462 | custom-view drawing | RENDER |
| A6 | Canvas non-ASCII text renders as SPACE glyph silently (8x16 ASCII font, signed char) | software_renderer.cpp:99-104,195 | any custom view drawing text | TEXT |
| A7 | Manifest label REFERENCE → literal "@0x…"; icon not parsed at all | manifest_reader.cpp:661-663, 598 | every APK's identity | RESOURCE |
| A8 | `Resources.getDimensionPixelSize` default fallback 24px | dalvik_engine.cpp:23895-23917 | silent wrong geometry | RESOURCE |
| A9 | Canvas.getWidth/getHeight hardcoded 1080x1920 regardless of actual canvas | canvas_shadow.cpp:1018-1019 | coordinate math in custom views | RENDER |
| A10 | `Theme.getColor` stub 0xFF000000; `Theme.resolveAttribute` absent; `Resources.getSystem` absent | dalvik_engine.cpp:29365-29376 | themed apps | RESOURCE |

## TIER B — missing foundation (consumers fail loudly or degrade)

| # | Primitive | Evidence | Fan-out |
|---|---|---|---|
| B1 | No canvas transform matrix: scale/rotate/skew/concat NO-OP (translation only) | canvas_shadow.cpp:1010-1017 | games, card flips, custom drawing |
| B2 | clipRect accepted, never enforced; no clip stack exists | canvas_shadow.cpp:1010-1017; grep zero clip in src/renderer | clipping everywhere |
| B3 | `Canvas.drawBitmap` NO-OP on DEX path; BitmapFactory.* absent | canvas_shadow.cpp:1010-1017; grep zero BitmapFactory | every image-drawing app |
| B4 | saveLayer/restoreToCount NO-OP; save/restore carry only translation | canvas_shadow.cpp:981-992, 1010-1017 | alpha compositing patterns |
| B5 | View.setX/setTranslationX/setY/AbsoluteLayout x-y absent; programmatic LayoutParams x,y dropped | dalvik_engine.cpp:20288-20301 | animation, drag UIs |
| B6 | ScrollView scrolling absent (no scrollY anywhere) | grep zero | any scrolling app |
| B7 | drawRoundRect radius ignored; drawCircle stroke = filled disc r+w | canvas_shadow.cpp:214-228, 229-250 | UI polish wrongness |
| B8 | Paint.setTextSize recorded-never-read on Canvas path | canvas_shadow.cpp:451-454 | custom text views |
| B9 | No italic face/synthesis; Paint.setTypeface no-op on Canvas path | text_shaper.cpp:73-78; canvas_shadow.cpp:455 | styled text |
| B10 | No per-codepoint fallback faces beyond FreeSerif/emoji (CJK depends on system TTF) | text_shaper.h:251-260 | non-Latin apps |
| B11 | View-level `android:theme` not applied at inflate | layout_inflater.cpp (no branch) | themed sub-trees |
| B12 | `@android:` framework resources unresolvable (no framework ARSC) | layout_inflater.cpp:416-422 | many published apps |

## TIER C — model/lifecycle correctness (bugs appear only in specific idioms)

| # | Primitive | Evidence |
|---|---|---|
| C1 | Programmatic RelativeLayout children: rl_edges_valid=false → fixed-point fallback | layout_inflater.cpp:2680-2762 |
| C2 | Render-without-measure path on RL trees → legacy fallback has NO RL branch → pile at (0,0) | execution_engine.cpp:2628-2830 (R-NEW-388 residual) |
| C3 | LL horizontal cross-axis TOP(0x30) falls into center branch | layout_inflater.cpp:2496-2502 |
| C4 | `gravity` one attr → two fields (container+text conflated) | layout_inflater.cpp:1089 |
| C5 | setText/setVisibility/setTextColor never raise layout_dirty (masked by full re-measure per frame on resource path; programmatic trees can go stale) | android_shadows.cpp:3127-3178, 2825-2829 |
| C6 | invalidate() no-op; no dirty-region model (whole-tree re-render each frame) | android_shadows.cpp:3300-3306 |
| C7 | RenderNode node alpha/translation/scale/rotation accepted-but-ignored | canvas_shadow.cpp:407-413 |
| C8 | FrameBuffer blend forces result alpha=255; PNG encode drops alpha (RGB) — alpha semantics untestable end-to-end | software_renderer.h:88-101, :823-852 |
| C9 | ViewTree evidence export lacks alpha/padding/measured fields | dalvik_engine.cpp:9082-9137 |
| C10 | getIdentifier dual path: real id resolution vs legacy stub | dalvik_engine.cpp:18636 vs 23873 |
| C11 | fraction TypedValue dead code (complex_to_fraction zero consumers) | res_id.cpp:61-70 |
| C12 | fontScale fixed 1.0 (sp == dp always) | layout_inflater.h:39 |

## TIER D — hygiene / evidence integrity

| # | Item | Evidence |
|---|---|---|
| D1 | view_renderer.cpp dead AND does not compile vs current ViewNode | census g++ -fsyntax-only |
| D2 | real_layout.cpp + resource_parser.cpp legacy orphan (self-include only) | real_layout.h:113-116 |
| D3 | api_dispatcher.cpp = EXP-036 stub, in build, grep trap (613 lines, no live role) | census |
| D4 | CMake/Makefile drift: exp088_a4 CMake target links pre-libpng lib set | CMakeLists.txt:98-100 vs Makefile:32 |
| D5 | scripts/build_exp124.sh references moved text_shaper path | stale |
| D6 | screenshot PNG alpha dropped (RGB encode) — capture proven faithful only for opaque frames | S66 |
| D7 | ViewTree JSON vs renderer dual field names (x/y vs measured_left/top) — same write site today, fragile model | layout_inflater.cpp:2353-2358 |
