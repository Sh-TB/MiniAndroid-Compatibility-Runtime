#!/usr/bin/env python3
"""S34 probe 7c: ComposerImpl state-machine trace WITH field values (fresh
insertion before the e$a.c block). Reads O (inserting) / q (nodeStarted) /
x from the LF/l receiver. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if (class_name == "Landroidx/compose/ui/node/e$a;" &&
                       method_name == "c") {"""

if '[S34-STATEM2]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

new_block = """            } else if (class_name == "LF/l;" &&
                       ((method_name == "j" || method_name == "F" ||
                         method_name == "b" || method_name == "g" ||
                         method_name == "r" || method_name == "i") &&
                        descriptor == "()V")) {
                // [S34-STATEM2] ComposerImpl state machine with field values:
                // j=startNode, F=useNode, r/b/g/i=group end/skip variants.
                static thread_local uint64_t statem_count = 0;
                ++statem_count;
                if (statem_count <= 150) {
                    std::cerr << "[S34-STATEM] LF/l." << method_name
                              << " depth=" << recursion_depth_;
                    uint32_t recv = args.empty() ? 0 : args[0].object_id;
                    for (const char* fname : {"O", "q", "x"}) {
                        auto v = heap_.get_object_field(recv, fname);
                        if (!v)
                            v = heap_.get_object_field(
                                recv, std::string("LF/l;.") + fname);
                        if (v)
                            std::cerr << " " << fname << "=" << v->int_val;
                    }
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " caller=" << frames[0].first << "."
                                  << frames[0].second;
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/node/e$a;" &&
                       method_name == "c") {"""

src = src.replace(anchor, new_block, 1)
open(P, 'w').write(src)
print('state-machine probe v2 applied (fresh)')
