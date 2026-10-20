#!/usr/bin/env python3
"""cont116_find_s2_ctor_callers.py — locate methods that invoke
Lcom/google/android/gms/internal/play_billing/s2;-><init> in telegram's
classes.dex (the RawMessageInfo construction site for F-NEW-449 decode).
Reuses cont9_dexdump.Dex (fixed code_item layout + payload math)."""
import sys, zipfile
sys.path.insert(0, "scripts")
from cont9_dexdump import Dex

APK = "upload/telegram_official.apk"
TARGET = "s2;-><init>"
TARGET_CLS = "Lcom/google/android/gms/internal/play_billing/s2;"

z = zipfile.ZipFile(APK)
d = Dex(z.read("classes.dex"))

# enumerate all classes: Dex has a method map? find_class needs desc; we need
# the class list. Use the internal structures if present.
try:
    classes = d.class_list()  # hypothetical
except Exception:
    classes = None

if classes is None:
    # fallback: iterate the header's type_ids via a public-ish approach:
    # cont9's Dex stores parsed structures in attributes; introspect.
    attrs = [a for a in dir(d) if not a.startswith("__")]
    print("Dex attrs:", attrs)
    sys.exit(0)
