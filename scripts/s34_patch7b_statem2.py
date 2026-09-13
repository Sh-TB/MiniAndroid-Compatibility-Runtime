#!/usr/bin/env python3
"""S34 probe 7b: ComposerImpl state-machine trace WITH field values.
Reads O (inserting) and q (nodeStarted) from the LF/l receiver via
heap_.get_object_field (plain and class-qualified keys, like F-077).
Replaces the earlier S34-STATEM block. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

start_marker = """            } else if (class_name == "LF/l;" &&
                       (method_name == "j" || method_name == "F" ||
                        method_name == "C" || method_name == "b" ||
                        method_name == "g" || method_name == "r") &&
                       descriptor == "()V" || (class_name == "LF/l;" &&
                       method_name == "C" && descriptor == "()Z")) {"""
end_marker = """            } else if (class_name == "LF/l;" && method_name == "m" &&
                       descriptor == "(LL1/a;)V") {"""

i0 = src.find(start_marker)
if i0 < 0:
    if '[S34-STATEM2]' in src:
        print('already present')
        sys.exit(0)
    print('START ANCHOR NOT FOUND')
    sys.exit(1)
i1 = src.find(end_marker, i0)
assert i1 > i0, 'end anchor not found'

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
            } else if (class_name == "LF/l;" && method_name == "m" &&
                       descriptor == "(LL1/a;)V") {"""

src = src[:i0] + new_block + src[i1:]
src = src.replace('if (\'[S34-STATEM]\'', 'if (\'[S34-STATEM2]\'')
open(P, 'w').write(src)
print('state-machine probe v2 applied')
