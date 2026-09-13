#!/usr/bin/env python3
"""S34 probe 2 (R-NEW-333): caller context on content-state ops.
Extends the CV1-STATE-R/W lines with the direct caller frame (call_stack_.top()
is the CALLER at method-entry probe time — the callee frame is pushed later).
Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

probe_anchor = """                if (method_name == "setValue" && args.size() > 1)
                    std::cerr << " val=" << args[1].object_id
                              << (args[1].is_null ? " NULL"
                                  : (args[1].type == DalvikType::OBJECT_REF
                                         ? (" " + args[1].class_desc) : ""));
                std::cerr << std::endl;"""

if '[S34-CALLER]' in src:
    print('already present')
    sys.exit(0)
assert probe_anchor in src, 'anchor not found'

replacement = """                if (method_name == "setValue" && args.size() > 1)
                    std::cerr << " val=" << args[1].object_id
                              << (args[1].is_null ? " NULL"
                                  : (args[1].type == DalvikType::OBJECT_REF
                                         ? (" " + args[1].class_desc) : ""));
                // [S34-CALLER] direct caller frame (callee frame not yet pushed)
                if (!call_stack_.empty()) {
                    const StackFrame& cfr = call_stack_.top();
                    std::cerr << " caller=" << cfr.class_name << "."
                              << cfr.method_name;
                }
                std::cerr << std::endl;"""

src = src.replace(probe_anchor, replacement, 1)
open(P, 'w').write(src)
print('caller probe applied')
