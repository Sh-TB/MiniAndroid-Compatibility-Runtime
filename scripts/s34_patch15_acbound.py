#!/usr/bin/env python3
"""S34 probe 15: AnimatedContent boundary + p inner lambdas.

p.a:0fc8 calls j/b.b(k/V Transition, ..., LL1/r content=N/a(p$e), ...) =
Transition.AnimatedContent. The content (p$e.g) NEVER composes. Probe:
  - j/b.b entries (the AnimatedContent composable)
  - k/K method entries (the transition SegmentState — currentState/target)
  - p$f.g / p$c.o / p$p.o / p$q.o (the remaining NavHost lambdas)
  - F/M.c entries (the updateValue helper at 1002)
Bounded 8 per key; idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if ((class_name == "Landroidx/navigation/compose/p$e;" &&
                        method_name == "g") ||"""

if '[S34-ACBOUND]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if ((class_name == "Lj/b;" && method_name == "b") ||
                       (class_name == "Lk/K;") ||
                       (class_name == "Landroidx/navigation/compose/p$f;" &&
                        method_name == "g") ||
                       (class_name == "Landroidx/navigation/compose/p$c;" &&
                        method_name == "o") ||
                       (class_name == "Landroidx/navigation/compose/p$p;" &&
                        method_name == "o") ||
                       (class_name == "Landroidx/navigation/compose/p$q;" &&
                        method_name == "o") ||
                       (class_name == "LF/M;" && method_name == "c")) {
                // [S34-ACBOUND] AnimatedContent boundary + p lambdas
                static thread_local std::map<std::string, uint64_t> acb_n;
                std::string acb_key = class_name + "." + method_name;
                uint64_t n = ++acb_n[acb_key];
                if (n <= 8) {
                    std::cerr << "[S34-ACBOUND] " << acb_key << " #" << n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if ((class_name == "Landroidx/navigation/compose/p$e;" &&
                        method_name == "g") ||"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('ACBOUND probes applied')
