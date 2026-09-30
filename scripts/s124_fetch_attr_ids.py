#!/usr/bin/env python3
"""S124: fetch AOSP public.xml + attrs.xml — exact framework attr-id ground
truth for the View-ctor defStyleAttr law (widget -> default-style attr)."""
import base64, re, urllib.request

BASE = "https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/res/res/values/"

def fetch(name):
    raw = urllib.request.urlopen(BASE + name + "?format=TEXT", timeout=60).read()
    return base64.b64decode(raw).decode("utf-8", "replace")

pub = fetch("public.xml")
open("/tmp/s124_aosp/public.xml", "w").write(pub)
print(f"public.xml: {len(pub)} bytes")

# The View-ctor defStyleAttr set (frameworks/base View ctor law):
WANTED = ["buttonStyle", "textViewStyle", "editTextStyle", "imageViewStyle",
          "imageButtonStyle", "checkboxStyle", "radioButtonStyle",
          "progressBarStyle", "seekBarStyle", "spinnerStyle",
          "switchStyle", "scrollViewStyle", "toolbarStyle", "listViewStyle",
          "gridViewStyle", "recyclerViewStyle" , "textAppearanceSmall",
          "textAppearanceMedium", "textAppearanceLarge", "windowBackground",
          "windowNoTitle", "windowActionBar", "colorPrimary", "colorAccent",
          "colorPrimaryDark", "colorSecondary", "colorOnPrimary",
          "colorOnSecondary", "colorSurface", "colorOnSurface",
          "colorError", "android_windowLightStatusBar"]

ids = {}
for m in re.finditer(r'<public type="attr" name="([\w]+)" id="(0x[0-9a-f]+)"', pub):
    n, i = m.group(1), m.group(2)
    if n in WANTED:
        ids.setdefault(n, i)
for n in WANTED:
    print(f"{n} = {ids.get(n, 'NOT-FOUND')}")

# framework public STYLE ids (default widget styles referenced by themes)
styles_wanted = ["Widget_Material_Button", "Widget_Material_Light_Button",
                 "Theme_Material", "Theme_Material_Light"]
for m in re.finditer(r'<public type="style" name="([\w]+)" id="(0x[0-9a-f]+)"', pub):
    n, i = m.group(1), m.group(2)
    if n in styles_wanted:
        print(f"style {n} = {i}")
