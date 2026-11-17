#!/usr/bin/env python3
"""W4 Phase 3 v2: split dalvik_engine.cpp into 5 semantic TUs.
- Lines 187-589 (F-107a trivial tables/structs/inline helpers) move verbatim
  into dex/dalvik_engine_internal.h — EXCEPT stateful non-inline functions
  (function-local statics), which stay as single definitions in the core TU
  (de-static'd) with declarations in the header.
- Lines 21553-21586 (IEEE bit/conv law helpers, anon-ns) also move to the
  header (wrapper dropped).
- Lines 590+ split into core/invoke/opcodes/bridge/tail TUs at verified
  brace-depth-2 cuts. All moves verbatim except de-static + header decls.
Execution order matters: header -> parts -> manifest -> de-static pass."""
import json, re

SRC = "src/dex/dalvik_engine.cpp"
lines = open(SRC).read().split("\n")

HEAD_END = 186
UT_END = 589
HEADER_RANGES = [(187, 589), (21553, 21586), (8858, 8877), (38357, 38417)]
# extra verbatim header blocks: (start, end, inline_add_signature_prefix)
EXTRA_HEADER_BLOCKS = [
    (8858, 8877, "std::string fnew304_resolve_pref_text("),   # F-NEW-304 helper
    (21553, 21586, None),                                     # IEEE bit/conv
    (38357, 38417, None),                                     # BridgeCensus family
    (38470, 38549, "C9"),                                     # C9 png/display-metrics
]
BODY_RANGES = {
    "dalvik_engine_core":   (590, 9816),
    "dalvik_engine_invoke": (9817, 21753),
    "dalvik_opcodes":       (21754, 38593),
    "dalvik_bridge":        (38594, 93789),
    "dalvik_engine_tail":   (93790, 94201),
}
NS_CLOSE = "\n} // namespace dalvik\n} // namespace miniandroid\n"
# ns-scope variable definitions trapped in the 4430-4434 anon block: moved to
# the core part at real namespace scope (external linkage, header externs).
ANON_VAR_LINES = [4431, 4432]
CORE_APPEND = []      # de-static'd stateful definitions kept in the core TU
HDR_DECLS = []        # prototypes for the moved-to-core definitions

mapj = json.load(open("evidence/issue612_audit/wave4_family_map.json"))
# NOTE: the map's build_invoke_args span (518-547) is bogus — lines 518-531
# are DECLARATIONS (defns live in the opcodes range); lines 532-589 are the
# inline dalvik_*_value helpers. The whole 518-589 sub-block is header content.
ut_defns = sorted([(s, e, n) for s, e, n, ns, sz in mapj["defns"]
                   if 187 <= s <= UT_END and n != "build_invoke_args"])
GAP_DESTATICS = [
    ("static std::vector<DalvikValue> build_invoke_args(",
     "std::vector<DalvikValue> build_invoke_args("),
    ("static int framework_enum_ordinal(",
     "int framework_enum_ordinal("),
    ("static int framework_static_int(",
     "int framework_static_int("),
    ("static framework::CallContext::Arg dalvik_value_to_arg",
     "framework::CallContext::Arg dalvik_value_to_arg"),
    ("static DalvikValue call_result_to_dalvik",
     "DalvikValue call_result_to_dalvik"),
    ("static std::vector<std::string> parse_proto_param_types(",
     "std::vector<std::string> parse_proto_param_types("),
]

def strip_static(t):
    return t.replace("static ", "", 1) if t.lstrip().startswith("static ") else t

def proto(s, e, name):
    chunk = []
    for i in range(s, e + 1):
        t = lines[i - 1]
        c = t.find("{")
        if c >= 0:
            chunk.append(t[:c]); break
        chunk.append(t)
    sig = " ".join(" ".join(chunk).split())
    return strip_static(sig) + ";"

hdr_parts = []
i = 187
for s, e, n in ut_defns + [(UT_END + 1, UT_END + 1, "_END")]:
    if i < s:
        gap = "\n".join(lines[i - 1:s - 1])
        for old, new in GAP_DESTATICS:
            gap = gap.replace(old, new)
        hdr_parts.append(gap)
        i = s
    if n == "_END":
        break
    first = lines[s - 1]
    if "inline" in first.split("{")[0] or "template" in first:
        hdr_parts.append(strip_static("\n".join(lines[s - 1:e])))
    else:
        span = "\n".join(lines[s - 1:e])
        # default args live on the header declaration only (C++ single-site rule)
        span = span.replace("const char* class_desc = nullptr)",
                            "const char* class_desc)")
        CORE_APPEND.append(strip_static(span))
        HDR_DECLS.append(proto(s, e, n))
    i = e + 1
header_gap_text = "\n".join(hdr_parts)

header = "// dalvik_engine_internal.h — ISSUE-612 WAVE-4 split support.\n"
header += "// Verbatim relocation of the F-107a trivially-destructible utility block\n"
header += "// (dalvik_engine.cpp lines 187-589: structs, static const tables, inline\n"
header += "// helpers) and the IEEE bit/conv law helpers (21553-21586), shared by the\n"
header += "// five split engine TUs. Stateful non-inline helpers remain single\n"
header += "// definitions in dalvik_engine_core.cpp, declared here (de-static'd).\n"
header += "// Inline functions with function-local statics keep single-instance\n"
header += "// semantics per the C++ inline rule.\n"
header += "#pragma once\n#ifndef MINIANDROID_DALVIK_ENGINE_INTERNAL_H\n"
header += "#define MINIANDROID_DALVIK_ENGINE_INTERNAL_H\n\n"
header += "#include \"dex/dalvik_engine.h\"\n\n"
header += "namespace miniandroid {\nnamespace dalvik {\n\n"
header += header_gap_text
for hs, he, inline_sig in EXTRA_HEADER_BLOCKS:
    header += (f"\n\n// ── verbatim helper block {hs}-{he} (anon wrapper dropped) ──\n")
    blk = lines[hs:he - 1]  # content between the two wrapper lines
    blk_text = "\n".join(blk)
    if inline_sig == "C9":
        blk_text = blk_text.replace("\nstatic bool c9_png_encode_rgba(",
                                    "\ninline bool c9_png_encode_rgba(")
        blk_text = blk_text.replace("\nstatic void c9_fill_display_metrics(",
                                    "\ninline void c9_fill_display_metrics(")
    elif inline_sig:
        blk_text = blk_text.replace(inline_sig, "inline " + inline_sig, 1)
    header += blk_text
header += "\n// ── cross-TU stateful helper declarations ──\n"
header += "\n".join(HDR_DECLS)
header += ("\n// ── cross-TU helper declarations (linker-driven additions) ──\n"
           "uint32_t csl_wrap_single(DalvikHeap& heap, uint32_t pc, int32_t argb,\n"
           "                         uint32_t frame_id = 0);\n"
           "std::string s130_norm_cls(std::string cls);\n"
           "std::string s134_dex_field_key(const std::string& cls,\n"
           "                               const std::string& name,\n"
           "                               bool dex_defined);\n"
           "std::vector<std::pair<int, std::string>> framework_enum_constants(\n"
           "    const std::string& class_desc);\n"
           "bool c9_png_encode_rgba(int w, int h,\n"
           "                        const std::vector<uint8_t>& rgba,\n"
           "                        std::vector<uint8_t>* out);\n"
           "void c9_fill_display_metrics(DalvikHeap& heap, uint32_t dm_id);\n"
           "const char* framework_string_id_text(uint32_t resid);\n"
           "\n// ── cross-TU variables (defined in core, used in invoke) ──\n"
           "extern std::map<std::string, uint64_t> g_d7_read_census;\n"
           "extern uint64_t g_d7_draws;\n")
header += "\n} // namespace dalvik\n} // namespace miniandroid\n\n#endif\n"
open("src/dex/dalvik_engine_internal.h", "w").write(header)
print(f"internal header written: {len(HDR_DECLS)} stateful decls, "
      f"{len(CORE_APPEND)} definitions moved to core")

pre_ns = "\n".join(lines[:183])
ns_opens = "\n".join(lines[183:HEAD_END])

def body_text(s, e):
    """Emit lines s..e (1-based inclusive), skipping HEADER_RANGES spans and
    the extracted anon-var definition lines."""
    out = []
    for ln in range(s, e + 1):
        if any(hs <= ln <= he for hs, he in HEADER_RANGES):
            continue
        if ln in ANON_VAR_LINES:
            continue
        out.append(lines[ln - 1])
    return "\n".join(out)

for name, (s, e) in BODY_RANGES.items():
    body = body_text(s, e)
    if name == "dalvik_engine_core":
        var_defs = "\n".join(lines[l - 1] for l in ANON_VAR_LINES)
        body = var_defs + "\n\n" + body
        if CORE_APPEND:
            body = "\n".join(CORE_APPEND) + "\n\n" + body
    text = (pre_ns + '\n#include "dex/dalvik_engine_internal.h"\n'
            + ns_opens + body + NS_CLOSE)
    open(f"src/dex/{name}.cpp", "w").write(text)
    print(f"{name}.cpp: {text.count(chr(10))} lines")

man = open("core_sources.manifest").read()
parts_lines = "\n".join(f"src/dex/{n}.cpp" for n in BODY_RANGES)
if "src/dex/dalvik_engine.cpp\n" in man:
    man = man.replace("src/dex/dalvik_engine.cpp\n", parts_lines + "\n")
    open("core_sources.manifest", "w").write(man)
    print("manifest updated")
else:
    print("manifest already updated")

# De-static the cross-TU DEFINITIONS living in the opcodes/other parts —
# MUST run after the part files are written (anchored at column 0 so
# comments never match).
CROSS_TU_DEFS = [
    "\nstatic std::vector<DalvikValue> build_invoke_args(",
    "\nstatic int framework_static_int(",
    "\nstatic int framework_enum_ordinal(",
    "\nstatic framework::CallContext::Arg dalvik_value_to_arg(",
    "\nstatic miniandroid::framework::CallContext::Arg dalvik_value_to_arg(",
    "\nstatic DalvikValue call_result_to_dalvik(",
    "\nstatic uint32_t csl_wrap_single(",
    "\nstatic std::string s130_norm_cls(",
    "\nstatic std::string s134_dex_field_key(",
    "\nstatic bool c9_png_encode_rgba(",
    "\nstatic void c9_fill_display_metrics(",
    "\nstatic const char* framework_string_id_text(",
    "\nstatic std::vector<std::pair<int, std::string>>\nframework_enum_constants(",
    "\nstatic std::vector<std::string> parse_proto_param_types(",
]
for name in BODY_RANGES:
    p = f"src/dex/{name}.cpp"
    t = open(p).read()
    orig = t
    for old in CROSS_TU_DEFS:
        t = t.replace(old, "\n" + old[8:])
    t = t.replace("uint32_t frame_id = 0)", "uint32_t frame_id)")
    if t != orig:
        open(p, "w").write(t)
        print(f"de-static pass: {name}.cpp")
print("done")
