#!/usr/bin/env python3
"""w23_split_engine_header.py — W23-03 phase 1: verbatim header split.

Splits the 4744-line src/dex/dalvik_engine.h at the DalvikExecutionEngine
class boundary into:

  dalvik_engine_types.h  — everything BEFORE the class: the stable public
                           value/opcode/trace/result surface (verbatim).
  dalvik_engine_impl.h   — the DalvikExecutionEngine class definition and
                           everything after it (verbatim), including the
                           types header.
  dalvik_engine.h        — becomes the public contract shell: includes the
                           types header and forward-declares the class.
                           Existing semantic content for class consumers now
                           lives in dalvik_engine_impl.h; consumers are
                           repointed in w23_repoint_includes.sh.

Verbatim guarantee: byte-for-byte relocation of every declaration — no
semantic change; the include set is adjusted in a follow-up shrink pass.

Run from anywhere; paths are repo-absolute via MINIANDROID_REPO.
"""
import os
import re
import sys

REPO = os.environ.get("MINIANDROID_REPO", "/home/z/my-project/miniandroid")
SRC = os.path.join(REPO, "src/dex/dalvik_engine.h")

lines = open(SRC, encoding="utf-8").read().split("\n")

# locate the class declaration line
class_idx = None
for i, ln in enumerate(lines):
    if re.match(r"^class DalvikExecutionEngine \{", ln):
        class_idx = i
        break
if class_idx is None:
    sys.exit("FATAL: class boundary not found")
print("class DalvikExecutionEngine at line %d (1-based)" % (class_idx + 1))

# locate the closing namespace lines at the tail
tail_ns = None
for i in range(len(lines) - 1, 0, -1):
    if re.match(r"^\} // namespace miniandroid", lines[i]):
        tail_ns = i
        break
if tail_ns is None:
    sys.exit("FATAL: closing namespace not found")
print("closing namespaces at lines %d-%d (1-based)" % (tail_ns + 1, tail_ns + 2))
# class body = class_idx .. tail_ns+2 exclusive of the two namespace closers
# the class's own `};` is the line before `} // namespace dalvik`
cls_end = tail_ns - 1  # line index of `} // namespace dalvik`
assert lines[cls_end].rstrip().endswith("} // namespace dalvik"), lines[cls_end]

types_body = lines[:class_idx]          # 1..1758 (0-based 0..class_idx-1)
impl_body = lines[class_idx:cls_end]    # class .. its closing `};`
head_guard_old = "MINIANDROID_REAL_DALVIK_ENGINE_H"

# ---- dalvik_engine_types.h ----
types_out = []
for ln in types_body:
    types_out.append(ln)
# replace the old include guard with the new one (first #ifndef/#define pair)
types_out[0] = types_out[0].replace(head_guard_old, "MINIANDROID_DALVIK_ENGINE_TYPES_H")
for i, ln in enumerate(types_out):
    if ln.startswith("#ifndef MINIANDROID_REAL_DALVIK_ENGINE_H"):
        types_out[i] = "#ifndef MINIANDROID_DALVIK_ENGINE_TYPES_H"
    elif ln.startswith("#define MINIANDROID_REAL_DALVIK_ENGINE_H"):
        types_out[i] = "#define MINIANDROID_DALVIK_ENGINE_TYPES_H"
        break
types_out += [
    "",
    "} // namespace dalvik",
    "} // namespace miniandroid",
    "",
    "#endif  // MINIANDROID_DALVIK_ENGINE_TYPES_H",
    "",
]

# ---- dalvik_engine_impl.h ----
impl_out = [
    "// dalvik_engine_impl.h — W23-03: private implementation header.",
    "// VERBATIM relocation of the DalvikExecutionEngine class definition and",
    "// the post-class content of dalvik_engine.h (W23 header-cascade redesign:",
    "// implementation details move out of the widely-included public header;",
    "// see evidence/w23/W23_DEPENDENCY_ANALYSIS.md). Attribution and all",
    "// law comments are carried unchanged with the relocated code.",
    "#ifndef MINIANDROID_DALVIK_ENGINE_IMPL_H",
    "#define MINIANDROID_DALVIK_ENGINE_IMPL_H",
    "",
    '#include "dalvik_engine_types.h"',
    "",
    "namespace miniandroid {",
    "namespace dalvik {",
    "",
]
impl_out += impl_body
impl_out += [
    "",
    "} // namespace dalvik",
    "} // namespace miniandroid",
    "",
    "#endif  // MINIANDROID_DALVIK_ENGINE_IMPL_H",
    "",
]

# ---- new dalvik_engine.h (public contract shell) ----
pub_out = [
    "/*",
    " * MiniAndroid Runtime - Real Dalvik Execution Engine (public contract)",
    " *",
    " * W23-03 header-cascade redesign: the public header now carries ONLY the",
    " * stable shared surface — opcode constants, value/register/frame/heap/",
    " * call-stack types, execution traces and DalvikExecutionResult — verbatim",
    " * relocated from the former monolithic header (see",
    " * dalvik_engine_types.h). The DalvikExecutionEngine class definition is",
    " * implementation detail and lives in dalvik_engine_impl.h, included only",
    " * by the engine-family translation units and their tests. A change to",
    " * engine internals therefore no longer recompiles unrelated consumers",
    " * (evidence/w23/W23_DEPENDENCY_ANALYSIS.md).",
    " */",
    "",
    "#ifndef MINIANDROID_REAL_DALVIK_ENGINE_H",
    "#define MINIANDROID_REAL_DALVIK_ENGINE_H",
    "",
    '#include "dalvik_engine_types.h"',
    "",
    "namespace miniandroid {",
    "namespace dalvik {",
    "",
    "class DalvikExecutionEngine;  // definition: dalvik_engine_impl.h",
    "",
    "} // namespace dalvik",
    "} // namespace miniandroid",
    "",
    "#endif  // MINIANDROID_REAL_DALVIK_ENGINE_H",
    "",
]

open(os.path.join(REPO, "src/dex/dalvik_engine_types.h"), "w", encoding="utf-8").write(
    "\n".join(types_out))
open(os.path.join(REPO, "src/dex/dalvik_engine_impl.h"), "w", encoding="utf-8").write(
    "\n".join(impl_out))
open(SRC, "w", encoding="utf-8").write("\n".join(pub_out))

print("wrote dalvik_engine_types.h (%d lines)" % len(types_out))
print("wrote dalvik_engine_impl.h (%d lines)" % len(impl_out))
print("rewrote dalvik_engine.h (%d lines)" % len(pub_out))
