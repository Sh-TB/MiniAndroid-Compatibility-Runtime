#!/usr/bin/env python3
"""S34 probe 14: destination-content invoke chain.

Chain to the game screen (evidence from static + trace):
  p.a (NavHost) → AnimatedContent content p$e.g (LL1/r) → finds entry in
  visibleEntries → l.a(entry, holder, content, ...) (LocalOwnersProvider) →
  N/a.g (Function3 composable invoke) → n1/q.g (game screen!)

Probe all five entry points, bounded 8 each. Env-gated probe build; idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

anchor = """            } else if (class_name == "Landroidx/compose/ui/node/e$a;" &&
                       method_name == "c") {"""

if '[S34-DCHAIN]' in src:
    print('already present')
    sys.exit(0)
assert anchor in src, 'anchor not found'

probe = """            } else if ((class_name == "Landroidx/navigation/compose/p$e;" &&
                        method_name == "g") ||
                       (class_name == "Landroidx/navigation/compose/l;" &&
                        method_name == "a") ||
                       (class_name == "LN/a;" && method_name == "g") ||
                       (class_name == "Ln1/q;" && method_name == "g") ||
                       (class_name == "Ln1/s;" && method_name == "g") ||
                       (class_name == "Ln1/t;" && method_name == "g")) {
                // [S34-DCHAIN] destination-content invoke chain
                static thread_local std::map<std::string, uint64_t> dch_n;
                std::string dch_key = class_name + "." + method_name;
                uint64_t n = ++dch_n[dch_key];
                if (n <= 8) {
                    std::cerr << "[S34-DCHAIN] " << dch_key << " #" << n
                              << " d=" << recursion_depth_;
                    auto frames = call_stack_.snapshot_top_first();
                    for (size_t fi = 0; fi < frames.size() && fi < 4; ++fi)
                        std::cerr << " <" << frames[fi].first << "."
                                  << frames[fi].second << ">";
                    std::cerr << std::endl;
                }
            } else if (class_name == "Landroidx/compose/ui/node/e$a;" &&
                       method_name == "c") {"""

src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('DCHAIN probes applied')
