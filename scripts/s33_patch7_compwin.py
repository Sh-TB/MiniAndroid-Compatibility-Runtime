#!/usr/bin/env python3
"""S33 probe 7: composition-window trace (R-NEW-332 tree-shape evidence).
From the AbstractComposeView.ensureCompositionCreated entry, log the next
N method entries (env-gated MINIANDROID_COMPWIN_TRACE=1, bounded 800) so the
content-lambda invocation (or its absence) is directly visible.
"""
import sys

C = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(C).read()

if '[COMPWIN' in src:
    print('already present')
    sys.exit(0)

anchor = """    // S33 (R-NEW-332): LayoutNode census"""
assert anchor in src

probe = """    // S33 (R-NEW-332): composition-window trace — from the
    // AbstractComposeView.ensureCompositionCreated entry, log the next 800
    // method entries (env-gated, bounded) so the app content-lambda invoke
    // is directly visible in the composition pass.
    {
        static thread_local const bool compwin_on =
            std::getenv("MINIANDROID_COMPWIN_TRACE") != nullptr;
        if (compwin_on) {
            static thread_local bool compwin_active = false;
            static thread_local uint64_t compwin_logged = 0;
            if (!compwin_active &&
                class_name == "Landroidx/compose/ui/platform/AbstractComposeView;" &&
                method_name == "ensureCompositionCreated") {
                compwin_active = true;
                std::cerr << "[COMPWIN-OPEN] " << class_name << "."
                          << method_name << " depth=" << recursion_depth_
                          << std::endl;
            }
            if (compwin_active && compwin_logged < 800) {
                ++compwin_logged;
                std::cerr << "[COMPWIN] " << class_name << "." << method_name
                          << " " << descriptor << " d=" << recursion_depth_
                          << std::endl;
                if (compwin_logged == 800)
                    std::cerr << "[COMPWIN-CLOSE] cap reached" << std::endl;
            }
        }
    }
    // S33 (R-NEW-332): LayoutNode census"""
src = src.replace(anchor, probe, 1)
open(C, 'w').write(src)
print('compwin probe applied')
