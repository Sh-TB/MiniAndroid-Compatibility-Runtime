#!/usr/bin/env python3
"""T281-1E: route instrumentation + KA-KYK-035 discriminating experiment.

1. Move the T280 RectF width/height + isEmpty block from the TOP of
   bridge_domain_ui_graphics back to its ORIGINAL slot (immediately before
   the F-NEW-442d comment) — tests whether the alleged early-exit
   (KA-KYK-035) exists at all, or whether T280's probe history was
   contaminated by stale builds.
2. Add env-gated, bounded route probes:
   - dalvik_bridge.cpp:82 entry        -> [T281-ROUTE] chain-entry
   - each of the 5 domain entries      -> [T281-ROUTE] domain=<name>
   - the ui_graphics RectF/isEmpty arm -> [T281-ROUTE] rectf-law
   All gated on MINIANDROID_T281_ROUTE, first-N bounded, stderr only.
"""
import re

UI = "miniandroid/src/dex/dalvik_bridge_domain_ui_graphics.cpp"
BR = "miniandroid/src/dex/dalvik_bridge.cpp"
DOM = {
    "jdk": "miniandroid/src/dex/dalvik_bridge_domain_jdk.cpp",
    "android_core": "miniandroid/src/dex/dalvik_bridge_domain_android_core.cpp",
    "ui_graphics": UI,
    "app_runtime": "miniandroid/src/dex/dalvik_bridge_domain_app_runtime.cpp",
    "io_lang": "miniandroid/src/dex/dalvik_bridge_domain_io_lang.cpp",
}

# ---------- 1. move the RectF block back to its original slot ----------
src = open(UI).read()
start_marker = "    if ((method == \"width\" || method == \"height\") &&"
end_marker = "    // F-NEW-442d (CONT-104) \u2014 AOSP WindowInsets.inset(IIII) law"
i = src.find(start_marker)
assert i > 0, "width block not found at top"
j = src.find(end_marker, i)
assert j > i, "442d marker not found"
block = src[i:j]
src = src[:i] + src[j:]  # remove from top
# original slot: immediately before the 442d comment (which is now the only one left)
k = src.find(end_marker)
assert k > 0
# route probe inside the block, right after the block header line
probe = """        if (diag_env("MINIANDROID_T281_ROUTE")) {
            static thread_local uint64_t t281r = 0;
            if (t281r++ < 24)
                std::cerr << "[T281-ROUTE] rectf-law " << class_name << "."
                          << method << std::endl;
        }
"""
anchor = "        if (recv != 0) {"
m = block.find(anchor)
assert m > 0
block2 = block[:m + len(anchor)] + "\n" + probe + block[m + len(anchor):]
# block2 now contains the probe; splice the block back before 442d
src = src[:k] + block2 + src[k:]
open(UI, "w").write(src)
print("ui_graphics: block moved back to original slot + rectf-law probe added")

# ---------- 2. chain-entry probe in dalvik_bridge.cpp ----------
br = open(BR).read()
anchor2 = "    BridgeCensusGuard c97_census_guard;\n    if (bridge_census().on) c97_census_guard.begin(class_name, method);"
assert anchor2 in br, "bridge.cpp anchor missing"
probe2 = """    if (diag_env("MINIANDROID_T281_ROUTE")) {
        static thread_local uint64_t t281c = 0;
        if (t281c++ < 40)
            std::cerr << "[T281-ROUTE] chain-entry " << class_name << "."
                      << method << std::endl;
    }
"""
br = br.replace(anchor2, probe2 + anchor2, 1)
open(BR, "w").write(br)
print("dalvik_bridge.cpp: chain-entry probe added")

# ---------- 3. domain-entry probes ----------
for name, path in DOM.items():
    s = open(path).read()
    if name == "ui_graphics":
        # function starts at line 16; anchor on the locals block tail
        anchor3 = "    uint32_t method_idx_hint = fr.method_idx_hint;\n"
        assert anchor3 in s, f"{name} anchor missing"
    else:
        # find the domain function's locals tail (same shape in all domain files)
        anchor3 = "    uint32_t method_idx_hint = fr.method_idx_hint;\n"
        assert anchor3 in s, f"{name} anchor missing"
    probe3 = (f"""    if (diag_env("MINIANDROID_T281_ROUTE")) {{
        static thread_local uint64_t t281d_{name} = 0;
        if (t281d_{name}++ < 12)
            std::cerr << "[T281-ROUTE] domain={name} " << class_name
                      << "." << method << std::endl;
    }}
""")
    s = s.replace(anchor3, anchor3 + probe3, 1)
    open(path, "w").write(s)
    print(f"{name}: domain probe added")
print("ALL INSTRUMENTATION DONE")
