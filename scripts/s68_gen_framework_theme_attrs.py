#!/usr/bin/env python3
"""s68_gen_framework_theme_attrs.py — generate the framework theme-attr
defaults table from AOSP law files (oreo-release).

LAW (AOSP frameworks/base core/res):
  * ?android:attr/name (TypedValue TYPE_ATTRIBUTE, 0x01xxxxxx) resolves
    through the app theme; a theme that lacks the attr falls back to the
    framework theme value. Flavor: Theme.Material (dark) vs
    Theme.Material.Light (light) — the framework's own *.Light convention.
  * State-list text colors (res/color/text_color_*.xml) resolve their
    enabled-state item: colorForeground × contentAlpha (per flavor).
Output: miniandroid/src/resources/framework_theme_attrs.h
        docs/upstream/aosp/FRAMEWORK_ATTR_PROVENANCE.md
"""
import re, hashlib, os

A = "/home/z/my-project/docs/upstream/aosp"
OUT = "/home/z/my-project/miniandroid/src/resources/framework_theme_attrs.h"

def sha(p):
    return hashlib.sha256(open(os.path.join(A, p), 'rb').read()).hexdigest()

ids = {}
for m in re.finditer(r'<public type="attr" name="([\w]+)" id="(0x[0-9a-f]+)"', open(f"{A}/public.xml").read()):
    ids[m.group(1)] = int(m.group(2), 16)

# colors + float dimens (all live in colors*.xml as <color> or <item type=dimen>)
colors, dimens = {}, {}
for f in ["colors.xml", "colors_material.xml", "colors_holo.xml", "colors_legacy.xml", "colors_device_defaults.xml"]:
    p = os.path.join(A, f)
    if not os.path.exists(p): continue
    txt = open(p).read()
    for m in re.finditer(r'<color name="([\w]+)">([^<]+)</color>', txt):
        colors[m.group(1)] = m.group(2).strip()
    for m in re.finditer(r'<item name="([\w]+)" format="float" type="dimen">([^<]+)</item>', txt):
        dimens[m.group(1)] = m.group(2).strip()

# res/color state lists: enabled-state color = the LAST item without a state.
state_lists = {}
import os as _os
cdir = os.path.join(A, "res_color")
if _os.path.isdir(cdir):
    for fn in sorted(_os.listdir(cdir)):
        if not fn.endswith(".xml"): continue
        txt = open(os.path.join(cdir, fn)).read()
        nostate = re.findall(r'<item (?!android:state)[^>]*android:color="([^"]+)"', txt)
        if nostate:
            state_lists[fn[:-4]] = nostate[-1]

bools = {}
bp = os.path.join(A, "bools.xml")
if os.path.exists(bp):
    for m in re.finditer(r'<bool name="([\w]+)">([\w]+)</bool>', open(bp).read()):
        bools[m.group(1)] = m.group(2)

def parse_themes():
    txt = open(f"{A}/themes_material.xml").read()
    styles = {}
    for m in re.finditer(r'<style name="([\w.]+)"(?:\s+parent="([^"]+)")?>(.*?)</style>', txt, re.S):
        name, parent, body = m.group(1), m.group(2) or "", m.group(3)
        items = {}
        for it in re.finditer(r'<item name="([\w.]+)">([^<]+)</item>', body):
            items[it.group(1)] = it.group(2).strip()
        styles[name] = (parent, items)
    def flat(name, seen=None):
        seen = seen or set()
        if name in seen or name not in styles: return {}
        seen.add(name)
        parent, items = styles[name]
        # parent may be "@android:style/Theme.Holo"
        p = parent.split("/")[-1] if "/" in parent else parent
        out = flat(p, seen) if p else {}
        out.update(items)
        return out
    return {n: flat(n) for n in styles}

themes = parse_themes()

def to_argb(s):
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 6: h = "ff" + h
        if len(h) == 8: return int(h, 16)
    return None

def scale_alpha(argb, alpha):
    a = int(round(((argb >> 24) & 0xFF) * alpha))
    return ((a & 0xFF) << 24) | (argb & 0xFFFFFF)

def resolve(v, depth=0):
    """Multi-hop resolver: @color/x (multi-hop), #hex, bool, @dimen float."""
    if depth > 8 or v is None: return None
    v = v.strip()
    if v.startswith("#"): return to_argb(v)
    for pre in ("@color/", "@android:color/"):
        if v.startswith(pre):
            bare = v[len(pre):]
            if bare in state_lists:   # res/color state list → enabled item
                return resolve(state_lists[bare], depth + 1)
            return resolve(colors.get(bare), depth + 1)
    if v.startswith("@dimen/"):
        try: return float(dimens.get(v[len("@dimen/"):], "nan"))
        except ValueError: return None
    if v in ("true", "false"): return 1 if v == "true" else 0
    try: return int(v)
    except ValueError: return None

ATTRS = [
    "colorPrimary", "colorPrimaryDark", "colorAccent",
    "textColorPrimary", "textColorSecondary", "textColorTertiary",
    "textColorPrimaryInverse", "textColorSecondaryInverse",
    "textColorTertiaryInverse", "textColorHintInverse", "textColorHint",
    "colorForeground", "colorForegroundInverse", "colorBackground",
    "backgroundTint", "windowBackground", "windowActionBar", "windowNoTitle",
    "windowFullscreen", "navigationBarColor", "statusBarColor",
    "colorControlNormal", "colorControlActivated", "colorControlHighlight",
    "colorButtonNormal", "colorSwitchThumbNormal", "disabledAlpha",
]

DARK, LIGHT = "Theme.Material", "Theme.Material.Light"

def attr_value(theme, name):
    """Resolve one attr for one theme flavor; state lists hand-expanded."""
    v = themes.get(theme, {}).get(name)
    if v is None: return None
    if name == "textColorPrimary" or name == "textColorSecondary":
        # res/color/text_color_{primary,secondary}.xml enabled item:
        # color = ?attr/colorForeground, alpha = primary/secondaryContentAlpha.
        fg = resolve(themes[theme].get("colorForeground"))
        alpha = resolve(themes[theme].get("primaryContentAlpha" if name == "textColorPrimary" else "secondaryContentAlpha"))
        if fg is None or alpha is None or not isinstance(alpha, float): return None
        return scale_alpha(fg, alpha)
    if name == "textColorTertiary":
        # Theme.Material: @color/secondary_text_material_{dark,light}
        v2 = themes[theme].get(name)
        return resolve(v2)
    if name == "textColorHint":
        # oreo Theme: @color/hint_foreground_material_* (state list)
        return resolve(v)
    if v.startswith("?attr/") or v.startswith("?android:attr/"):
        inner = v.split("attr/")[-1]
        return attr_value(theme, inner)   # theme-internal reference chain
    return resolve(v)

rows, deferred = [], []
for name in ATTRS:
    aid = ids.get(name)
    if aid is None:
        deferred.append((name, "no public id")); continue
    d = attr_value(DARK, name)
    l = attr_value(LIGHT, name)
    if d is None or l is None:
        deferred.append((name, f"dark={themes.get(DARK,{}).get(name)!r}→{d} light={themes.get(LIGHT,{}).get(name)!r}→{l}"))
        continue
    # float = AOSP fraction (TypedValue FRACTION_UNIT law: data = v * (1<<15))
    def enc(x):
        return int(round(x * (1 << 15))) if isinstance(x, float) else x
    rows.append((name, aid, enc(d), enc(l)))

with open(OUT, "w") as f:
    f.write("""// framework_theme_attrs.h — S68 W2 (A1/A10): FRAMEWORK theme-attr defaults.
//
// LAW (AOSP frameworks/base core/res): ?android:attr/name (TypedValue
// TYPE_ATTRIBUTE, id 0x01xxxxxx) resolves through the app theme; when the
// theme chain lacks the attr, the value is the framework theme default.
// Flavor (dark=Theme.Material vs light=Theme.Material.Light) follows the
// framework's own *.Light naming convention on the resolved theme parent
// chain — generic framework contract, never app-specific.
// State-list text colors are hand-expanded to their enabled-state item
// (colorForeground × contentAlpha) per res/color/*.xml law.
//
// GENERATED by scripts/s68_gen_framework_theme_attrs.py from AOSP
// oreo-release law files (regenerate, never hand-edit):
""")
    for p in ["public.xml", "themes_material.xml", "colors_material.xml", "colors.xml", "colors_holo.xml", "colors_legacy.xml"]:
        f.write(f"//   {p}  sha256={sha(p)[:32]}\n")
    f.write("""
#pragma once
#include <cstdint>
#include <cstddef>

namespace miniandroid { namespace resources {

struct FrameworkThemeAttr { const char* name; uint32_t id; uint32_t dark; uint32_t light; };

// dark  = Theme.Material       value (AOSP law)
// light = Theme.Material.Light value (AOSP law)
inline const FrameworkThemeAttr FRAMEWORK_THEME_ATTRS[] = {
""")
    for name, aid, d, l in rows:
        f.write(f'    {{"{name}", 0x{aid:08x}u, 0x{d:08x}u, 0x{l:08x}u}},\n')
    f.write("""};
inline const size_t FRAMEWORK_THEME_ATTR_COUNT = sizeof(FRAMEWORK_THEME_ATTRS) / sizeof(FRAMEWORK_THEME_ATTRS[0]);

} } // namespace miniandroid::resources
""")

with open(f"{A}/FRAMEWORK_ATTR_PROVENANCE.md", "w") as f:
    f.write("# Framework theme-attr defaults — provenance (S68 W2)\n\n")
    f.write("Source: aosp-mirror/platform_frameworks_base @ oreo-release\n\n")
    for p in ["public.xml", "themes_material.xml", "colors_material.xml", "colors.xml", "colors_holo.xml", "colors_legacy.xml"]:
        pth = os.path.join(A, p)
        if os.path.exists(pth):
            f.write(f"- `{p}` sha256=`{sha(p)}`\n")
    f.write(f"\n## Resolved ({len(rows)} attrs)\n\n| attr | id | Theme.Material | Theme.Material.Light |\n|---|---|---|---|\n")
    for name, aid, d, l in rows:
        f.write(f"| {name} | 0x{aid:08x} | 0x{d:08x} | 0x{l:08x} |\n")
    f.write(f"\n## Deferred ({len(deferred)})\n\n| attr | reason |\n|---|---|\n")
    for name, why in deferred:
        f.write(f"| {name} | {why} |\n")
print(f"resolved {len(rows)} attrs, deferred {len(deferred)}; wrote {OUT}")
for name, aid, d, l in rows:
    print(f"  {name} 0x{aid:08x} dark=0x{d:08x} light=0x{l:08x}")
for name, why in deferred:
    print(f"  DEFER {name}: {why[:90]}")
