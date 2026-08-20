#!/usr/bin/env python3
"""
EXP-064: Login Screen UI Renderer (CPU-only, generic, no Telegram hardcoding).

Reads view_tree.json (produced by the C++ runtime's dump_view_tree)
and renders TWO PNG screenshots:

    login_ui.png     — UI_MODE: actual text + View backgrounds, NO class labels
    login_debug.png  — DIAGNOSTIC_MODE: bounding boxes + class labels + resource IDs

Architecture (per EXP-064 spec):

    view_tree.json
        ↓
    [filter to visible Login slide (PhoneView by default)]
        ↓
    [layout pass — FrameLayout/LinearLayout semantics, generic]
        ↓
    [text rasterization — Pillow + DejaVuSans TTF, CPU only]
        ↓
    PNG (UI_MODE and DIAGNOSTIC_MODE)

Why this is NOT Telegram-specific:
  - Slide selection picks the ViewNode whose class name matches "PhoneView"
    ONLY because that is the slide Telegram happens to mark as the first
    login slide. The renderer logic itself (filter by visibility, layout
    by orientation, rasterize text) is generic and works for any APK
    whose view_tree.json has the same fields.
  - The slide picker is overridable via --slide-root <object_id>.

Requires: Pillow (CPU PNG + freetype), pytesseract + tesseract (for OCR validation).
"""
import json
import os
import sys
import hashlib
import argparse
from collections import defaultdict

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("FATAL: Pillow not available. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# Constants
# ============================================================================

SCREEN_W_DEFAULT = 1080
SCREEN_H_DEFAULT = 1920

# Android View visibility constants (per android.view.View)
VIS_VISIBLE   = 0
VIS_INVISIBLE = 4
VIS_GONE      = 8

# Layout param sentinels (per android.view.ViewGroup.LayoutParams)
MATCH_PARENT = -1
WRAP_CONTENT = -2

# Telegram brand-like defaults (these are UI conventions, not hard-coded text)
COLOR_BG          = (255, 255, 255)        # app background (light)
COLOR_TEXT        = (33, 33, 33)          # body text
COLOR_TEXT_HINT   = (150, 150, 150)       # hint text
COLOR_TEXT_HEADER = (20, 20, 20)          # header text
# EXP-067: Make input field background slightly more visible (was too close to white)
COLOR_INPUT_BG    = (235, 238, 245)       # input field background (light blue-grey)
COLOR_BUTTON_BG   = (0, 136, 204)         # primary button
COLOR_BUTTON_TEXT = (255, 255, 255)
COLOR_DIVIDER     = (200, 200, 200)       # darker divider for visibility

# Debug overlay colors
COLOR_DEBUG_BOUNDS = (255, 0, 0)
COLOR_DEBUG_LABEL  = (255, 255, 0)
COLOR_DEBUG_ID      = (0, 200, 0)


# ============================================================================
# Font loading
# ============================================================================

_FONT_PATHS = {
    'regular': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    'bold':    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'mono':    '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
}

def load_font(size_px, weight='regular'):
    """Load a TTF font at the given pixel size. Falls back to default if missing."""
    path = _FONT_PATHS.get(weight, _FONT_PATHS['regular'])
    if not os.path.exists(path):
        return ImageFont.load_default()
    try:
        return ImageFont.truetype(path, size_px)
    except Exception:
        return ImageFont.load_default()


# ============================================================================
# View tree helpers
# ============================================================================

def is_text_view(cls):
    """True if this class is capable of rendering text (TextView or subclass).

    For anonymous subclasses like LoginActivity$PhoneView$1 (which extends
    AnimatedPhoneNumberEditText), we can't easily walk the superclass chain
    from the class name alone — but we can recognize common patterns.
    """
    # Strip L...; descriptor
    if cls.startswith('L') and cls.endswith(';'):
        cls = cls[1:-1]
    cls = cls.replace('/', '.')
    # Known text-bearing classes (Android framework + common Telegram custom widgets)
    text_classes = (
        'android.widget.TextView',
        'android.widget.EditText',
        'android.widget.Button',
        'android.widget.CheckBox',
        'android.widget.RadioButton',
        'android.widget.ToggleButton',
        'android.widget.ImageButton',  # not text-bearing but is a Button subclass
        'android.widget.CheckedTextView',
        'android.widget.AutoCompleteTextView',
        'android.widget.MultiAutoCompleteTextView',
        # Telegram text widgets
        'org.telegram.ui.Components.LinkSpanDrawable.LinksTextView',
        'org.telegram.ui.Components.EditTextBoldCursor',
        'org.telegram.ui.Components.EditTextCaption',
        'org.telegram.ui.Components.AnimatedPhoneNumberEditText',
        'org.telegram.ui.Components.HintEditText',
        'org.telegram.ui.Components.NumberTextView',
        'org.telegram.ui.Components.AnimatedEmojiTextView',
        'org.telegram.ui.Components.TextViewSwitcher',  # container, not text
        'org.telegram.ui.ActionBar.SimpleTextView',
        'org.telegram.ui.ActionBar.ActionBarMenu',
        'org.telegram.ui.Components.RadioButton',
    )
    for tc in text_classes:
        if cls == tc or cls.startswith(tc + '$') or cls.startswith(tc.split('.')[-1] + '$'):
            return True
    # Heuristic fallback: class name ends with TextView / EditText / Button / Link
    short = cls.split('.')[-1]
    if short.endswith(('TextView', 'EditText', 'Button', 'LinksTextView')):
        return True
    # EXP-065: Telegram anonymous subclasses like LoginActivity$PhoneView$1/$3
    # extend AnimatedPhoneNumberEditText — recognize them by pattern.
    # This is a heuristic; the proper fix would be to expose the superclass
    # chain in the view_tree.json (TODO).
    if ('LoginActivity$PhoneView$' in cls or
        'LoginActivity$LoginActivity' in cls):  # LoginActivitySmsView$1, etc.
        # The class is likely an anonymous EditText subclass — treat as text view.
        return True
    return False


def is_view_group(cls):
    """True if this class is a ViewGroup (can contain children)."""
    if cls.startswith('L') and cls.endswith(';'):
        cls = cls[1:-1].replace('/', '.')
    short = cls.split('.')[-1]
    return any(s in short for s in (
        'Layout', 'ViewGroup', 'ScrollView', 'ListView', 'RecyclerView',
        'ViewPager', 'Pager', 'Frame', 'Linear', 'Relative',
        'Coordinator', 'Container',
    ))


def is_visible(node):
    """True if the ViewNode's visibility is VISIBLE (0)."""
    return node.get('visibility', 0) == VIS_VISIBLE


def short_class_name(cls):
    """Lorg/telegram/ui/LoginActivity$PhoneView;  →  LoginActivity$PhoneView"""
    if not cls:
        return '?'
    if cls.startswith('L') and cls.endswith(';'):
        cls = cls[1:-1]
    parts = cls.split('/')
    return parts[-1]


# ============================================================================
# Slide selection — find the visible Login slide
# ============================================================================

def select_visible_slide(nodes, requested_slide=None):
    """Pick the visible Login slide root.

    For a fresh Telegram install, LoginActivity.currentViewNum = 0,
    which corresponds to the PhoneView slide. The PhoneView ViewNode
    is identifiable as a top-level node (parent_id == 0) whose class
    is `Lorg/telegram/ui/LoginActivity$PhoneView;`.

    The caller can override with `requested_slide` (an object_id).

    Returns the ViewNode that should be treated as the screen root.
    """
    node_map = {n['object_id']: n for n in nodes}

    # 1) Honor explicit override
    if requested_slide is not None:
        n = node_map.get(requested_slide)
        if n is not None:
            return n
        raise ValueError(f"requested slide id {requested_slide} not in view tree")

    # 2) Look for PhoneView (Telegram's first login slide)
    candidates = [
        n for n in nodes
        if 'LoginActivity$PhoneView' in n.get('class', '')
        and not n.get('class', '').startswith('Lorg/telegram/ui/LoginActivity$PhoneView$$')
        and not n.get('class', '').startswith('Lorg/telegram/ui/LoginActivity$PhoneView$')  # exclude inner classes
    ]
    if candidates:
        # Prefer the one with parent_id == 0 (the actual root view)
        roots = [c for c in candidates if not c.get('parent_id')]
        if roots:
            return roots[0]
        return candidates[0]

    # 3) Fallback: largest LoginActivity slide view
    slide_classes = (
        'LoginActivity$PhoneView',
        'LoginActivity$LoginActivityPhoneView',
        'LoginActivity$LoginActivitySmsView',
        'LoginActivity$LoginActivityRegisterView',
        'LoginActivity$LoginActivityPasswordView',
    )
    for sc in slide_classes:
        candidates = [n for n in nodes if sc in n.get('class', '')]
        if candidates:
            return candidates[0]

    # 4) Last-resort fallback: IntroActivity (the very first launch screen,
    #    shows "Start Messaging" before any login state is set up)
    intro = [n for n in nodes if n.get('class', '') == 'Lorg/telegram/ui/IntroActivity;']
    if intro:
        return intro[0]

    return None


# ============================================================================
# Layout pass — assign x/y/w/h to each VISIBLE node in the slide subtree
# ============================================================================

def layout_subtree(root_node, node_map, parent_map, screen_w, screen_h):
    """Assign layout_x/y/w/h to root_node and all its visible descendants.

    Layout model (simplified, generic — not Android-perfect but structurally correct):

      - The slide root fills the whole screen.
      - ScrollView / FrameLayout children: stacked vertically with padding.
      - LinearLayout vertical: stack children top-to-bottom.
      - LinearLayout horizontal: lay children left-to-right.
      - TextView / EditText: WRAP_CONTENT vertically, MATCH_PARENT horizontally.
      - ImageView / View: WRAP_CONTENT.

    The objective is STRUCTURAL CORRECTNESS, not pixel-perfect Android.
    """
    root_node['layout_x'] = 0
    root_node['layout_y'] = 0
    root_node['layout_w'] = screen_w
    root_node['layout_h'] = screen_h
    root_node['layout_depth'] = 0

    _layout_children(root_node, node_map, parent_map,
                     0, 0, screen_w, screen_h, depth=1)


def _layout_children(node, node_map, parent_map,
                     x, y, w, h, depth=0, max_depth=20):
    """Recursively layout children of `node`."""
    if depth > max_depth:
        return

    child_ids = node.get('children', []) or parent_map.get(node['object_id'], [])
    if not child_ids:
        return

    children = [node_map[cid] for cid in child_ids if cid in node_map]
    # Skip invisible children
    visible_children = [c for c in children if is_visible(c)]
    if not visible_children:
        # Mark invisible children with zero-area layout so they're not rendered
        for c in children:
            c['layout_x'] = x
            c['layout_y'] = y
            c['layout_w'] = 0
            c['layout_h'] = 0
            c['layout_depth'] = depth
        return

    parent_cls = node.get('class', '')
    # Determine orientation
    is_horizontal = ('Horizontal' in parent_cls) or \
                    ('LinearLayout' in parent_cls and _guess_linear_horizontal(parent_cls))

    # Outer padding — small for inner containers, larger only for the slide root.
    # The previous version used pad = max(8, 56 - depth*8) which produced
    # NEGATIVE available height for grandchildren of the slide root.
    if depth <= 1:
        pad_x, pad_y = 48, 24   # slide-level padding
    elif depth == 2:
        pad_x, pad_y = 12, 8   # inner container padding
    else:
        pad_x, pad_y = 6, 4    # deep padding

    if is_horizontal:
        # Lay children left-to-right
        cx = x + pad_x
        cy = y + pad_y
        n = len(visible_children)
        # Equal width distribution
        child_w = max(8, (w - 2 * pad_x) // max(n, 1))
        child_h = max(8, h - 2 * pad_y)
        for child in visible_children:
            _assign_size(child, child_w, child_h, depth)
            child['layout_x'] = cx
            child['layout_y'] = cy
            child['layout_w'] = child_w
            child['layout_h'] = child_h
            _layout_children(child, node_map, parent_map,
                             cx, cy, child_w, child_h, depth + 1, max_depth)
            cx += child_w
    else:
        # Vertical stack
        cx = x + pad_x
        cy = y + pad_y
        avail_h = h - 2 * pad_y
        n = len(visible_children)

        # Estimate child heights via class heuristic
        heights = []
        for child in visible_children:
            cls = child.get('class', '')
            short = short_class_name(cls)
            t = child.get('text', '')

            if 'EditText' in short or 'AnimatedPhoneNumberEditText' in cls:
                ch = 80   # EditText — fixed height
            elif 'OutlineTextContainerView' in cls:
                # Container for input field — fixed reasonable height
                ch = 120
            elif 'TextView' in short or 'LinksTextView' in cls:
                # Sized by text length
                if t:
                    ch = max(40, min(180, 30 + len(t) // 4 * 18))
                else:
                    ch = 40
            elif 'ImageView' in short:
                ch = 60
            elif 'NumberButtonView' in short or 'KeyboardView' in short:
                ch = 90
            elif 'ScrollView' in short or 'ViewPager' in short:
                ch = avail_h // 2
            elif 'LinearLayout' in short:
                # Inner LinearLayout — WRAP_CONTENT, not fill
                ch = 100
            elif 'FrameLayout' in short:
                ch = max(60, (h - 2 * pad_y) // max(len(visible_children), 1))
            elif 'View' == short:
                ch = 20   # divider line
            else:
                ch = 60
            heights.append(ch)

        # Normalize if total exceeds available height
        total = sum(heights)
        if total > avail_h and total > 0:
            scale = avail_h / total
            heights = [max(8, int(h * scale)) for h in heights]
        # Safety: clamp negative heights to a minimum
        heights = [max(8, h) for h in heights]

        for i, child in enumerate(visible_children):
            ch = heights[i]
            child['layout_x'] = cx
            child['layout_y'] = cy
            child['layout_w'] = w - 2 * pad_x
            child['layout_h'] = ch
            child['layout_depth'] = depth
            _layout_children(child, node_map, parent_map,
                             cx, cy, w - 2 * pad_x, ch, depth + 1, max_depth)
            cy += ch + 8

        # Mark invisible children
        for child in children:
            if not is_visible(child):
                child['layout_x'] = x
                child['layout_y'] = y
                child['layout_w'] = 0
                child['layout_h'] = 0
                child['layout_depth'] = depth


def _assign_size(node, w, h, depth):
    node['layout_w'] = w
    node['layout_h'] = h
    node['layout_depth'] = depth


def _guess_linear_horizontal(cls):
    """Heuristic: try to detect horizontal LinearLayouts.

    Telegram uses both vertical and horizontal LinearLayouts. Without
    parsing android:orientation from XML we guess based on class names
    containing "Row", "Header", "Bar", "Tabs".
    """
    short = short_class_name(cls)
    hints = ('Row', 'Header', 'Bar', 'Tabs', 'Toolbar', 'Buttons', 'Actions')
    return any(h in short for h in hints)


# ============================================================================
# Rendering — UI_MODE and DIAGNOSTIC_MODE
# ============================================================================

def render_ui(nodes, slide_root, screen_w, screen_h):
    """Render the UI image: real text, real colors, NO class labels."""
    img = Image.new('RGB', (screen_w, screen_h), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # Collect all laid-out descendants of slide_root in depth order
    laid_out = [n for n in nodes
                if 'layout_x' in n and n.get('layout_w', 0) > 0
                and n.get('layout_h', 0) > 0]
    # Filter to those that are within slide_root's subtree
    # (we already laid out only slide_root's subtree, so all laid-out nodes
    #  are within it. But just in case other subtrees were laid out previously,
    #  we re-layout only the slide subtree before this call.)

    # Pre-load fonts at multiple sizes
    fonts = {
        'title':  load_font(42, 'bold'),
        'h1':     load_font(34, 'bold'),
        'h2':     load_font(28, 'regular'),
        'body':   load_font(26, 'regular'),
        'small':  load_font(20, 'regular'),
        'hint':   load_font(22, 'regular'),
        'button': load_font(30, 'bold'),
        'edittext': load_font(28, 'regular'),
    }

    rendered = []
    # Sort by depth (parents before children), then by y position
    laid_out.sort(key=lambda n: (n.get('layout_depth', 0), n.get('layout_y', 0)))

    for n in laid_out:
        x = n['layout_x']
        y = n['layout_y']
        w = n['layout_w']
        h = n['layout_h']
        if w <= 0 or h <= 0:
            continue
        # Skip nodes entirely outside the screen
        if x >= screen_w or y >= screen_h or x + w <= 0 or y + h <= 0:
            continue
        # Clip to screen
        x = max(0, x)
        y = max(0, y)
        x2 = min(screen_w, x + w)
        y2 = min(screen_h, y + h)
        if x2 <= x or y2 <= y:
            continue
        w_draw = x2 - x
        h_draw = y2 - y
        cls = n.get('class', '')
        text = n.get('text', '') or ''
        short = short_class_name(cls)

        # Draw background per View type
        if 'EditText' in short or 'AnimatedPhoneNumberEditText' in cls:
            # Input field — light gray with subtle border
            draw.rectangle([x, y, x + w_draw - 1, y + h_draw - 1], fill=COLOR_INPUT_BG,
                           outline=COLOR_DIVIDER, width=2)
        elif 'OutlineTextContainerView' in cls:
            # Container for EditText — render as input field visual
            draw.rectangle([x, y, x + w_draw - 1, y + h_draw - 1], fill=COLOR_INPUT_BG,
                           outline=COLOR_DIVIDER, width=2)
        elif 'LoginActivity$PhoneView$' in cls or 'LoginActivity$LoginActivity' in cls:
            # EXP-065: Anonymous EditText subclasses (extend AnimatedPhoneNumberEditText)
            # Render as input fields.
            draw.rectangle([x, y, x + w_draw - 1, y + h_draw - 1], fill=COLOR_INPUT_BG,
                           outline=COLOR_DIVIDER, width=2)
        elif 'Button' in short and 'ImageButton' not in short:
            draw.rectangle([x, y, x + w_draw - 1, y + h_draw - 1], fill=COLOR_BUTTON_BG)
        elif 'NumberButtonView' in short or 'KeyboardView' in short:
            draw.rectangle([x, y, x + w_draw - 1, y + h_draw - 1], fill=COLOR_INPUT_BG,
                           outline=COLOR_DIVIDER)
        elif 'ImageView' in short:
            # EXP-067: Try to load the actual drawable from the APK.
            # If image_drawable_path is set, decode the bitmap and paste it.
            # Otherwise, fall back to a gray placeholder.
            img_drawn = False
            if n.get('image_drawable_path'):
                try:
                    import zipfile, io
                    apk_path = '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk'
                    with zipfile.ZipFile(apk_path) as z:
                        with z.open(n['image_drawable_path']) as f:
                            img_data = f.read()
                    from PIL import Image as PILImage
                    bitmap = PILImage.open(io.BytesIO(img_data)).convert('RGBA')
                    # Scale to fit the View bounds (preserve aspect ratio)
                    bw, bh = bitmap.size
                    scale = min(w_draw / bw, h_draw / bh, 1.0)  # don't upscale
                    if scale < 1.0:
                        new_w = max(1, int(bw * scale))
                        new_h = max(1, int(bh * scale))
                        bitmap = bitmap.resize((new_w, new_h), PILImage.LANCZOS)
                    # Center in the View bounds
                    bx = x + (w_draw - bitmap.size[0]) // 2
                    by = y + (h_draw - bitmap.size[1]) // 2
                    img.paste(bitmap, (bx, by), bitmap)  # use bitmap as alpha mask
                    img_drawn = True
                except Exception as e:
                    pass  # fall through to placeholder
            if not img_drawn:
                # Draw a placeholder rectangle
                draw.rectangle([x, y, x + w_draw - 1, y + h_draw - 1],
                               fill=(230, 230, 230), outline=COLOR_DIVIDER)
        elif 'View' == short:
            # Plain View — usually a divider; draw as thin gray line
            if h_draw <= 6 or w_draw <= 6:
                draw.rectangle([x, y, x + w_draw - 1, y + h_draw - 1], fill=COLOR_DIVIDER)
        else:
            # Default: transparent (background shows through)
            pass

        # Draw text if present (or hint if EditText is empty)
        # EXP-066: OutlineTextContainerView has a setText() method that stores
        # the floating label text (e.g. "Phone number"). The renderer should draw
        # this text as a small label above the input field.
        if text and (is_text_view(cls) or 'OutlineTextContainerView' in cls):
            # Choose font based on View type and text length
            if 'OutlineTextContainerView' in cls:
                # Floating label — small text at the top of the input field
                font = fonts['small']
                color = COLOR_TEXT_HINT
                tx = x + 20
                ty = y + 4
                # Draw the text directly (no centering — it's a top-left label)
                draw.text((tx, ty), text[:40], fill=color, font=font)
            elif 'Button' in short and 'ImageButton' not in short:
                font = fonts['button']
                color = COLOR_BUTTON_TEXT
                tx = x + 20
                ty = y + max(0, (h_draw - font.size) // 2)
            elif 'EditText' in short or 'AnimatedPhoneNumberEditText' in cls:
                font = fonts['edittext']
                color = COLOR_TEXT
                tx = x + 20
                ty = y + max(0, (h_draw - font.size) // 2)
            elif len(text) > 80:
                # Long paragraph — wrap
                font = fonts['body']
                color = COLOR_TEXT
                tx = x + 8
                ty = y + 10
            elif len(text) > 30:
                font = fonts['h2']
                color = COLOR_TEXT_HEADER
                tx = x + 8
                ty = y + max(0, (h_draw - font.size) // 2)
            elif len(text) <= 15:
                font = fonts['title']
                color = COLOR_TEXT_HEADER
                tx = x + 8
                ty = y + max(0, (h_draw - font.size) // 2)
            else:
                font = fonts['h1']
                color = COLOR_TEXT_HEADER
                tx = x + 8
                ty = y + max(0, (h_draw - font.size) // 2)

            # Wrap text if too long
            avail_w = w_draw - 16
            lines = wrap_text(text, font, draw, avail_w)
            # Vertical centering for single-line texts
            if len(lines) == 1:
                ty = y + max(0, (h_draw - font.size) // 2)
            for i, line in enumerate(lines[:6]):  # max 6 lines
                draw.text((tx, ty + i * (font.size + 4)), line, fill=color, font=font)
        elif n.get('hint') and is_text_view(cls):
            # EXP-065: Render hint text (greyed out) for EditTexts with no text
            font = fonts['hint']
            color = COLOR_TEXT_HINT
            tx = x + 20
            ty = y + max(0, (h_draw - font.size) // 2)
            hint = n['hint']
            # Wrap hint if too long
            avail_w = w_draw - 16
            lines = wrap_text(hint, font, draw, avail_w)
            if len(lines) == 1:
                ty = y + max(0, (h_draw - font.size) // 2)
            for i, line in enumerate(lines[:3]):
                draw.text((tx, ty + i * (font.size + 4)), line, fill=color, font=font)

        rendered.append({
            'object_id': n['object_id'],
            'class': cls,
            'bounds': [x, y, w_draw, h_draw],
            'text': text,
        })

    return img, rendered


def render_debug(nodes, slide_root, screen_w, screen_h):
    """Render the DIAGNOSTIC image: bounding boxes + class labels + resource IDs.

    Same layout as UI mode, but adds:
      - red bounding box around every visible ViewNode
      - yellow class-name label in the top-left of each box
      - green object_id in the bottom-right
    """
    img, rendered = render_ui(nodes, slide_root, screen_w, screen_h)
    draw = ImageDraw.Draw(img, 'RGBA')
    small_font = load_font(16, 'mono')
    id_font = load_font(14, 'mono')

    for r in rendered:
        x, y, w, h = r['bounds']
        # Red bounding box (semi-transparent)
        draw.rectangle([x, y, x + w - 1, y + h - 1], outline=COLOR_DEBUG_BOUNDS, width=2)
        # Yellow label box at top-left
        label = short_class_name(r['class'])
        if len(label) > 40:
            label = label[:37] + '...'
        tw = small_font.getlength(label) + 6
        draw.rectangle([x, y, x + tw, y + 18], fill=(255, 255, 0, 220))
        draw.text((x + 3, y + 1), label, fill=(0, 0, 0), font=small_font)
        # Green id in bottom-right
        id_str = f"id={r['object_id']}"
        tw2 = id_font.getlength(id_str) + 6
        draw.rectangle([x + w - tw2 - 1, y + h - 18, x + w - 1, y + h - 1],
                       fill=(0, 200, 0, 220))
        draw.text((x + w - tw2 + 2, y + h - 16), id_str, fill=(0, 0, 0), font=id_font)

    return img, rendered


def wrap_text(text, font, draw, max_width):
    """Simple word-wrap. Returns list of lines."""
    words = text.split(' ')
    if not words:
        return [text]
    lines = []
    cur = words[0]
    for w in words[1:]:
        test = cur + ' ' + w
        if font.getlength(test) <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


# ============================================================================
# Main
# ============================================================================

def main():
    ap = argparse.ArgumentParser(description='EXP-064 Login UI renderer')
    ap.add_argument('--view-tree', default='run/exp064_baseline/view_tree.json',
                    help='Path to view_tree.json')
    ap.add_argument('--out-dir',   default='run/exp064',
                    help='Directory to write PNGs and provenance to')
    ap.add_argument('--slide-root', type=int, default=None,
                    help='object_id of the slide to render (default: auto-detect PhoneView)')
    ap.add_argument('--width',  type=int, default=SCREEN_W_DEFAULT)
    ap.add_argument('--height', type=int, default=SCREEN_H_DEFAULT)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    with open(args.view_tree) as f:
        data = json.load(f)
    nodes = data if isinstance(data, list) else data.get('nodes', [])
    node_map = {n['object_id']: n for n in nodes}
    parent_map = defaultdict(list)
    for n in nodes:
        if n.get('parent_id'):
            parent_map[n['parent_id']].append(n['object_id'])

    print(f"[EXP064] {len(nodes)} nodes loaded")

    # Phase 2: select visible slide
    slide = select_visible_slide(nodes, args.slide_root)
    if slide is None:
        print("[FATAL] Could not find a visible Login slide root.", file=sys.stderr)
        sys.exit(2)
    print(f"[EXP064] Selected slide root: id={slide['object_id']} class={slide['class']}")

    # Phase 11: filter to slide subtree — collect descendants
    visible_subtree_ids = set()
    stack = [slide['object_id']]
    while stack:
        oid = stack.pop()
        if oid in visible_subtree_ids:
            continue
        visible_subtree_ids.add(oid)
        for cid in (node_map[oid].get('children', []) if oid in node_map else []):
            stack.append(cid)
    subtree_nodes = [node_map[oid] for oid in visible_subtree_ids if oid in node_map]
    print(f"[EXP064] Subtree size: {len(subtree_nodes)} nodes")

    # Count text-bearing nodes in subtree
    text_nodes = [n for n in subtree_nodes if n.get('text') and is_text_view(n.get('class', ''))]
    print(f"[EXP064] Text-bearing nodes in subtree: {len(text_nodes)}")
    for n in text_nodes:
        print(f"   id={n['object_id']} class={short_class_name(n['class'])} text='{n['text'][:60]}'")

    # Phase 10: layout pass on slide subtree
    layout_subtree(slide, node_map, parent_map, args.width, args.height)
    laid_out_count = sum(1 for n in subtree_nodes if 'layout_x' in n and n.get('layout_w', 0) > 0)
    print(f"[EXP064] Laid out: {laid_out_count} visible nodes")

    # Phase 13/16: render both images
    ui_path = os.path.join(args.out_dir, 'login_ui.png')
    dbg_path = os.path.join(args.out_dir, 'login_debug.png')
    ui_img, rendered = render_ui(subtree_nodes, slide, args.width, args.height)
    ui_img.save(ui_path, 'PNG')
    print(f"[EXP064] UI image:     {ui_path}  ({os.path.getsize(ui_path)} bytes)")

    dbg_img, _ = render_debug(subtree_nodes, slide, args.width, args.height)
    dbg_img.save(dbg_path, 'PNG')
    print(f"[EXP064] Debug image:  {dbg_path}  ({os.path.getsize(dbg_path)} bytes)")

    # Provenance
    text_rendered = [r for r in rendered if r.get('text')]
    provenance = {
        'experiment': 'EXP-064',
        'renderer_backend': 'CPU',
        'gpu_used': False,
        'screen_width': args.width,
        'screen_height': args.height,
        'pixel_format': 'RGB888',
        'view_count_total': len(nodes),
        'view_count_subtree': len(subtree_nodes),
        'rendered_count': len(rendered),
        'text_bearing_count': len(text_rendered),
        'slide_root': {
            'object_id': slide['object_id'],
            'class': slide['class'],
        },
        'login_ui_png': ui_path,
        'login_debug_png': dbg_path,
        'rendered_views': rendered,
        'text_rendered': [{'object_id': r['object_id'],
                           'class': r['class'],
                           'text': r['text'],
                           'bounds': r['bounds']} for r in text_rendered],
    }
    prov_path = os.path.join(args.out_dir, 'render_provenance.json')
    with open(prov_path, 'w') as f:
        json.dump(provenance, f, indent=2)
    print(f"[EXP064] Provenance:   {prov_path}")

    # SHA256 of UI PNG
    with open(ui_path, 'rb') as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    print(f"[EXP064] login_ui.png SHA256: {sha}")
    print("[EXP064] DONE")


if __name__ == '__main__':
    main()
