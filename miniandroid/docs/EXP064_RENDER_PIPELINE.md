# EXP-064 — Render Pipeline Audit (Phase 3)

Forensic audit of the EXP-063 baseline renderer (`tools/exp061_render.py`)
before any EXP-064 changes. Answers the 8 specific questions from the
EXP-064 Phase 3 spec.

## Q1: Why are class names visible in the baseline PNG?

Because `exp061_render.py` lines 254-261 explicitly draw them:

```python
# Draw class name as label
short_cls = cls.replace('Lorg/telegram/ui/', '').replace('Landroid/widget/', '')
short_cls = short_cls.replace('Landroid/view/', '').replace(';', '').replace('/', '.')
if h > 25 and '$$ExternalSynthetic' not in cls and 'access$' not in cls:
    try:
        draw.text((x + 5, y + max(0, h - 22)),
                  short_cls[:35], fill=(80, 80, 80), font=font_small)
    except:
        pass
```

The renderer intentionally draws the class name as a debug label in the
lower part of every rectangle. There is no UI_MODE / DIAGNOSTIC_MODE
distinction — every image gets both the text (if any) AND the class
label.

## Q2: Is class name intentionally used as placeholder text?

Yes, but only as a debug aid. The renderer has no notion of "the text
this View should display" beyond the `text` field on the ViewNode, and
the class name is drawn IN ADDITION to that text. Visually the class
label (drawn in light grey, in a smaller font, at the bottom of each
rectangle) competes with the actual text (drawn in dark grey, in a
larger font, at the top of each rectangle).

## Q3: Where is `node.text` stored?

In the ViewNode dump produced by the C++ runtime's `dump_view_tree()`
function. The dump writes a JSON file (`view_tree.json`) where each
node has a `text` field. For the EXP-063 baseline, 39 of 1385 nodes
have non-empty `text`.

The C++ runtime stores the text on the `ViewShadow` object (in the
heap model) whenever `TextView.setText(CharSequence)` is called by
the executing DEX bytecode. The dump then serializes that field to
JSON.

## Q4: Which renderer function produces each rectangle?

`exp061_render.py:render_to_framebuffer()` — line 245:

```python
draw.rectangle([x, y, x2, y2], fill=color, outline=(180, 180, 180))
```

where `color = class_to_color(cls)`. The color is derived from the
class name via an FNV-1a hash (lines 195-198), so different View
classes get visually distinguishable colors.

## Q5: Which renderer function draws labels?

Two functions:

1. **Text label** (lines 247-252): `draw.text((x + 10, y + 10), text[:60], fill=(30, 30, 30), font=font_medium)` — draws the first 60 characters of `node.text` at the top-left of the rectangle.
2. **Class label** (lines 254-261): `draw.text((x + 5, y + max(0, h - 22)), short_cls[:35], fill=(80, 80, 80), font=font_small)` — draws the short class name at the bottom of the rectangle.

Both labels are drawn in EVERY image. There is no UI_MODE.

## Q6: Does the renderer ever receive `node.text`?

Yes — line 247 reads `text = n.get('text', '')`. So the renderer DOES
have access to the text. The bug is that the text is drawn but
VISUALLY OBSCURED by:

1. The colored rectangle background (often dark colors that reduce contrast with the dark-grey text).
2. The class-name label drawn on the same rectangle (line 254-261).
3. The fact that only 22 of 1385 nodes are reached by the layout pass (see Q8 below) — the 39 text-bearing nodes are mostly outside the chosen root's subtree.

## Q7: Does it ever call a text-drawing primitive?

Yes — Pillow's `ImageDraw.text()` is called at lines 250 and 258. This
IS a real text rasterization call (Pillow uses freetype under the hood).
So the primitive exists; the bug is the UI_MODE / DIAGNOSTIC_MODE
conflation, not the absence of text rasterization.

## Q8: Does it load a font?

Yes — lines 213-218:

```python
font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
```

DejaVuSans TTF is loaded at three sizes. The renderer DOES use a
real font with real glyphs.

## Bonus: Why are only 22 of 1385 nodes rendered?

`exp061_render.py:layout_pass()` (lines 46-93) picks ONE root — the
ViewNode with the most descendants that matches a class-name filter
for `View / Layout / Group / Scroll / Pager / Frame / Activity`. For
Telegram's LoginActivity heap, this picks `LoginActivity$2` (id=2645,
the ViewPager container) which has many descendants but is NOT the
visible slide.

The actual visible slide — `LoginActivity$PhoneView` (id=2728) — has
`parent_id=0` (it's a top-level root in the heap, because Telegram
pre-creates slides and stores them as fields on the LoginActivity
instance, not as children of the ViewPager). So PhoneView is NOT a
descendant of LoginActivity$2, and its subtree (13 nodes including the
"Please confirm your country code and enter your phone number." text)
is never laid out or rendered.

## Trace: "Start Messaging" from ViewNode to pixel output (EXP-063 baseline)

```
ViewNode (id=2460)
  class: Lorg/telegram/ui/IntroActivity$4;
  parent_id: 2431 (IntroActivity$1)
  text: "Start Messaging"
      ↓
layout_pass() picks LoginActivity$2 as root, not IntroActivity$1.
IntroActivity$1 is NOT a descendant of LoginActivity$2.
      ↓
node 2460 is NOT in the laid_out_nodes list.
      ↓
render_to_framebuffer() loop never iterates over node 2460.
      ↓
draw.text() is never called with "Start Messaging".
      ↓
PNG pixel output: NO "Start Messaging" pixels.
```

Conclusion: the EXP-063 baseline renderer had multiple independent
defects — wrong root selection, no UI_MODE, no visibility filter,
class-name-as-label. EXP-064 fixed all of them.

## EXP-064 fixed pipeline (after rewrite)

```
ViewNode (id=2734) "Please confirm your country code and enter your phone number."
      ↓
select_visible_slide() picks LoginActivity$PhoneView (id=2728, parent_id=0)
      ↓
layout_subtree() walks PhoneView's subtree (13 nodes), assigns layout_x/y/w/h
      ↓
render_ui() iterates laid_out_nodes, finds node 2734
      ↓
is_text_view("Lorg/telegram/ui/Components/LinkSpanDrawable$LinksTextView;")
  → True (matches "LinksTextView" suffix)
      ↓
Pillow.ImageDraw.text((48, 72 + centering), "Please confirm your country code...",
                       fill=(30, 30, 30), font=DejaVuSans-Bold 26px)
      ↓
word-wrap (5 lines, each ~24px tall)
      ↓
PNG: dark-grey glyphs on white background, 1080×1920, OCR-detectable
      ↓
Tesseract: "Please confirm your country code and enter your phone number."
```
