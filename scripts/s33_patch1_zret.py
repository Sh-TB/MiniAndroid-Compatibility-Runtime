#!/usr/bin/env python3
"""S33 probe 1: draw-window ()Z return-value probe (R-NEW-332 evidence).
Inserts after `return_val = last_invoke_return_;` in try_recursive_invoke.
Idempotent: skips if [DRAWWIN-ZRET] already present.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

if '[DRAWWIN-ZRET]' in src:
    print('probe already present, skip')
    sys.exit(0)

anchor = """        return_val = last_invoke_return_;

        // S21 trie forensics"""
assert anchor in src, 'anchor not found'

probe = """        return_val = last_invoke_return_;

        // S33 (R-NEW-332 evidence): inside the custom-view draw window, print
        // the RETURN VALUE of every ()Z method (isPlaced-style predicates)
        // with the DECLARING class + receiver id, so the draw walk's gating
        // predicates are directly readable. Also reveals which declaring
        // class actually serves a receiver-class entry (R8 letter mapping).
        if (draw_window_active_) {
            static thread_local uint64_t dwz_count = 0;
            if (dwz_count < 300 && method.descriptor == "()Z") {
                ++dwz_count;
                std::cerr << "[DRAWWIN-ZRET] decl=" << cls_ref.name << "."
                          << method.name
                          << " recv=" << (args.empty() ? 0 : args[0].object_id)
                          << "(" << (args.empty() ? std::string("null")
                                                  : args[0].class_desc) << ")"
                          << " ret=" << (return_val.int_val ? "TRUE" : "FALSE")
                          << std::endl;
            }
        }

        // S21 trie forensics"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('probe inserted OK')
