#!/usr/bin/env python3
"""U008: Generate resource_values.json for an APK using the androguard ARSC
parser (ADOPTED OPEN-SOURCE ORACLE — androguard 4.1.4, Apache-2.0).

This closes the UNIFIED_007 PARTIAL: 'Telegram string values show resource
names'. The engine resolves LocaleController.getString(resid) via
field_name_by_resid_ → resource_string_values_[name]; the VALUES now come
from the real resources.arsc instead of a hand-built file.

Usage: u008_gen_resource_values.py <apk> <out.json>
"""
import json
import sys
import zipfile

from androguard.core.axml import ARSCParser


def main():
    apk_path = sys.argv[1]
    out_path = sys.argv[2]

    with zipfile.ZipFile(apk_path) as z:
        names = z.namelist()
        arsc_name = "resources.arsc"
        if arsc_name not in names:
            print(json.dumps({"error": "no resources.arsc"}))
            return 1
        arsc_bytes = z.read(arsc_name)

    arsc = ARSCParser(arsc_bytes)
    packages = arsc.get_packages_names()
    result = {"string": {}, "color": {}, "dimen": {}, "integer": {},
              "bool": {}, "array": {}, "drawable": {}}
    counts = {"resolved_strings": 0, "resolved_colors": 0}

    for pkg in packages:
        # androguard's get_*_resources(pkg) return an XML <resources> blob.
        # Parse name→value pairs out of it (values may contain CDATA and
        # entity escapes — unescape via a tiny loop, no XML dep needed).
        import re
        import html

        def harvest(blob, key, store):
            text = blob.decode("utf-8", "replace") if isinstance(blob, bytes) else blob
            # <string name="X">value</string> / <color name="X">#fff</color>
            for m in re.finditer(
                    r'<%s\s+name="([^"]+)"\s*>(.*?)</%s\s*>' % (key, key),
                    text, re.S):
                name, value = m.group(1), m.group(2)
                # strip CDATA wrapper
                cdata = re.match(r"<!\[CDATA\[(.*)\]\]>\s*$", value, re.S)
                if cdata:
                    value = cdata.group(1)
                value = html.unescape(value)
                store[name] = value

        harvesters = [
            ("string", "string", "resolved_strings"),
            ("color", "color", "resolved_colors"),
            ("dimen", "dimen", "resolved_dimens"),
            ("integer", "integer", "resolved_integers"),
            ("bool", "bool", "resolved_bools"),
            ("drawable", "drawable", "resolved_drawables"),
        ]
        for api_name, xml_key, count_key in harvesters:
            try:
                blob = getattr(arsc, "get_%s_resources" % api_name)(pkg)
                if blob:
                    harvest(blob, xml_key, result[xml_key])
                    counts[count_key] = len(result[xml_key])
            except Exception as e:  # noqa: BLE001
                counts[api_name + "_error"] = str(e)

    counts["packages"] = packages
    result["__meta__"] = {
        "generator": "u008_gen_resource_values.py (androguard ARSCParser)",
        "apk": apk_path,
        "counts": counts,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(json.dumps(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
