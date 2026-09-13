#!/usr/bin/env python3
"""S33 probe 2: F-096 lifecycle-window instrumentation (R-NEW-332 evidence).
Adds a lifecycle_window_active_ flag + method-entry/ZRET/exception probes so
the real-DEX onMeasure/onLayout dispatch (F-096) can be traced exactly like
the draw window. Idempotent.
"""
import sys

H = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.h'
C = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'

h = open(H).read()
if 'lifecycle_window_active_' in h:
    print('header probe present, skip')
else:
    anchor = "    bool draw_window_active_ = false;"
    assert anchor in h
    h = h.replace(anchor, anchor + """

    // S33 diagnostic (env-gated, read-only): TRUE while the F-096 real-DEX
    // onMeasure/onLayout lifecycle dispatch window is open. Method-entry
    // and ()Z-return probes attribute entries to the measure/layout phase —
    // evidence for the R-NEW-332 placement gate (isPlaced at draw time).
    bool lifecycle_window_active_ = false;""", 1)
    open(H, 'w').write(h)
    print('header patched')

c = open(C).read()
changed = 0

# 1) method-entry probe next to the DRAWWIN-IN probe
if '[LIFEWIN-IN]' not in c:
    anchor = """    if (drawwin_on && draw_window_active_ && drawwin_count < 3000) {
        std::cerr << "[DRAWWIN-IN] " << class_name << "." << method_name
                  << " " << descriptor << std::endl;
        drawwin_count++;
    }"""
    assert anchor in c, 'drawwin anchor not found'
    c = c.replace(anchor, anchor + """
    // S33 (R-NEW-332): method entries inside the F-096 lifecycle dispatch
    // window (real-DEX onMeasure/onLayout) — shows the measure/layout
    // traversal the placement pass actually executes.
    static thread_local const bool lifewin_on =
        std::getenv("MINIANDROID_LIFEWIN_TRACE") != nullptr;
    static thread_local uint64_t lifewin_count = 0;
    if (lifewin_on && lifecycle_window_active_ && lifewin_count < 4000) {
        std::cerr << "[LIFEWIN-IN] " << class_name << "." << method_name
                  << " " << descriptor << std::endl;
        lifewin_count++;
    }""", 1)
    changed += 1

# 2) ()Z return probe inside lifecycle window (ZRET generalization)
if '[LIFEWIN-ZRET]' not in c:
    anchor = """        if (draw_window_active_) {
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
        }"""
    assert anchor in c, 'zret anchor not found'
    c = c.replace(anchor, anchor + """
        if (lifecycle_window_active_) {
            static thread_local uint64_t lwz_count = 0;
            if (lwz_count < 300 && method.descriptor == "()Z") {
                ++lwz_count;
                std::cerr << "[LIFEWIN-ZRET] decl=" << cls_ref.name << "."
                          << method.name
                          << " recv=" << (args.empty() ? 0 : args[0].object_id)
                          << "(" << (args.empty() ? std::string("null")
                                                  : args[0].class_desc) << ")"
                          << " ret=" << (return_val.int_val ? "TRUE" : "FALSE")
                          << std::endl;
            }
        }""", 1)
    changed += 1

# 3) open/close the window in dispatch_view_lifecycle_once
if '[LIFEWIN-OPEN]' not in c:
    anchor = """    bool dispatched_any = false;
    // 1) onMeasure(II)V — EXACTLY specs from the resolved rect."""
    assert anchor in c, 'lifecycle open anchor not found'
    c = c.replace(anchor, """    bool dispatched_any = false;
    // S33 (R-NEW-332): open the lifecycle evidence window for the two real-DEX
    // dispatches below (onMeasure + onLayout).
    lifecycle_window_active_ = true;
    std::cerr << "[LIFEWIN-OPEN] " << cls << " view=" << view_object_id << std::endl;
    // 1) onMeasure(II)V — EXACTLY specs from the resolved rect.""", 1)
    changed += 1

if '[LIFEWIN-CLOSE]' not in c:
    anchor = """        if (ok) dispatched_any = true;
    }
    // Bounded evidence trace."""
    assert anchor in c, 'lifecycle close anchor not found'
    c = c.replace(anchor, """        if (ok) dispatched_any = true;
    }
    // S33: close the lifecycle evidence window.
    std::cerr << "[LIFEWIN-CLOSE] " << cls << " view=" << view_object_id
              << " dispatched=" << (dispatched_any ? "YES" : "NO") << std::endl;
    lifecycle_window_active_ = false;
    // Bounded evidence trace.""", 1)
    changed += 1

# 4) exception visibility inside the window (bounded): pending_exception_ set
#    at method entry is cleared — catch swallow points via the EXC propagate
#    marker instead; nothing to patch here.

open(C, 'w').write(c)
print(f'cpp patched ({changed} edits)')
