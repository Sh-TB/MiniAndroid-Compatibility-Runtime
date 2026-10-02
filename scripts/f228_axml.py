#!/usr/bin/env python3
"""F-NEW-228 source-law mining: dump opencalc TableLayout/TableRow declared attrs."""
import logging, re, sys, zipfile

logging.disable(logging.CRITICAL)
try:
    from loguru import logger as _lu
    _lu.remove()
except Exception:
    pass
from androguard.core.axml import AXMLPrinter

APK = "/home/z/my-project/upload/opencalculator_53.apk"
CANDS = ["res/9t.xml", "res/E_.xml", "res/Ok.xml", "res/Sk.xml", "res/ra.xml", "res/v9.xml"]


def main():
    z = zipfile.ZipFile(APK)
    for name in CANDS:
        try:
            xml = AXMLPrinter(z.read(name)).get_xml().decode("utf-8", "ignore")
        except Exception as e:
            print(name, "ERR", e)
            continue
        if "TableRow" not in xml:
            continue
        rows = xml.count("<TableRow")
        print(f"== {name}: TableRow count={rows}")
        # Print every TableLayout/TableRow start tag with attrs, compressed
        for m in re.finditer(r"<(TableLayout|TableRow)\b[^>]*>", xml):
            tag = m.group(0)
            attrs = re.findall(r'android:([\w]+)="([^"]*)"', tag)
            keep = {k: v for k, v in attrs if k in (
                "layout_width", "layout_height", "layout_weight", "layout_gravity",
                "id", "stretchColumns", "shrinkColumns", "layout_marginTop", "layout_marginBottom")}
            print(" ", m.group(1), keep)
        # the parent chain of the TableLayout (first 3 lines before it)
        i = xml.find("<TableLayout")
        if i >= 0:
            pre = xml[:i].rstrip()
            print("  parent-chain tail:", pre[-300:].replace("\n", " | ")[-300:])
        break


if __name__ == "__main__":
    main()
