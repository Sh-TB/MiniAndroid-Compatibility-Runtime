#!/usr/bin/env python3
"""S34 probe 10: pin the divergence callers.
- LD/b.f (the lambda trampoline after the Layout emit) — did it run? caller?
- LB0/b.c (rememberNavController) — caller chain (who invoked it?)
- Lh1/e.<init> (NavController ctor) — caller chain
Env-gated MINIANDROID_NODE_CENSUS. Bounded 12 each. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if (class_name == "LF/l;" && method_name == "k" &&
                       descriptor == "()Z") {"""

if '[S34-DIVERGE]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if (class_name == "LD/b;" && method_name == "f") {
                // [S34-DIVERGE] LD/b.f trampoline — ran? from where?
                static thread_local uint64_t dbf_n = 0;
                ++dbf_n;
                if (dbf_n <= 12) {
                    std::cerr << "[S34-DIVERGE] LD/b.f #" << dbf_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 4; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LB0/b;" && method_name == "c") {
                // [S34-DIVERGE] rememberNavController — caller chain
                static thread_local uint64_t b0c_n = 0;
                ++b0c_n;
                if (b0c_n <= 8) {
                    std::cerr << "[S34-DIVERGE] LB0/b.c #" << b0c_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 5; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "Lh1/e;" && method_name == "<init>") {
                // [S34-DIVERGE] NavController ctor — caller chain
                static thread_local uint64_t nve_n = 0;
                ++nve_n;
                if (nve_n <= 8) {
                    std::cerr << "[S34-DIVERGE] NavController.<init> #" << nve_n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 5; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "LF/l;" && method_name == "k" &&
                       descriptor == "()Z") {"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('diverge probe applied')
