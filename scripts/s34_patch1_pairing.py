#!/usr/bin/env python3
"""S34 probe 1 (R-NEW-333): compose-view pairing trace.
Env-gated MINIANDROID_CVPARI=1, bounded. Logs, by real DEX method names:
  CV1-INIT       ComposeView.<init>            (every real-DEX construction)
  CV1-SETCONTENT ComposeView.setContent        (receiver + content lambda)
  CV1-CREATE     AbstractComposeView.c()       (=createComposition+ensure)
  CV1-CONTENT    ComposeView.a(I,LF/i;)        (=Content() override, reads q)
  CV1-ATTACH     AbstractComposeView.onAttachedToWindow
  CV1-ACV        AndroidComposeView.<init>
  CV1-E1A        e1.a(AbstractComposeView,LF/t;,LN/a;)  (composition factory)
  CV1-STATE-W    F/V0.setValue                 (state object id + value id)
The upstream law (ComposeView.android.kt 1.6.7): setContent and Content()
read/write THE SAME instance's q state. Any mismatch = the R-NEW-333 root.
Idempotent; inserts before the EXP-053 anchor like the census probe.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

if 'CV1-INIT' in src:
    print('already present')
    sys.exit(0)

anchor = """    // S33 (R-NEW-332): LayoutNode census"""
assert anchor in src

probe = """    // S34 (R-NEW-333): compose-view pairing trace — same instance law.
    {
        static thread_local const bool cvpari_on =
            std::getenv("MINIANDROID_CVPARI") != nullptr;
        if (cvpari_on) {
            static thread_local uint64_t cv1_n = 0;
            ++cv1_n;
            const char* cv1_tag = nullptr;
            if (class_name == "Landroidx/compose/ui/platform/ComposeView;" &&
                method_name == "<init>") cv1_tag = "CV1-INIT";
            else if (class_name == "Landroidx/compose/ui/platform/ComposeView;" &&
                     method_name == "setContent") cv1_tag = "CV1-SETCONTENT";
            else if (class_name == "Landroidx/compose/ui/platform/AbstractComposeView;" &&
                     method_name == "c" && descriptor == "()V") cv1_tag = "CV1-CREATE";
            else if (class_name == "Landroidx/compose/ui/platform/ComposeView;" &&
                     method_name == "a" &&
                     descriptor == "(I LF/i;)V") cv1_tag = "CV1-CONTENT";
            else if (class_name == "Landroidx/compose/ui/platform/AbstractComposeView;" &&
                     method_name == "onAttachedToWindow") cv1_tag = "CV1-ATTACH";
            else if (class_name == "Landroidx/compose/ui/platform/AndroidComposeView;" &&
                     method_name == "<init>") cv1_tag = "CV1-ACV";
            else if (class_name == "Landroidx/compose/ui/platform/e1;" &&
                     method_name == "a") cv1_tag = "CV1-E1A";
            if (cv1_tag && cv1_n <= 400) {
                std::cerr << "[" << cv1_tag << "] recv="
                          << (args.empty() ? 0 : args[0].object_id)
                          << " depth=" << recursion_depth_;
                if (args.size() > 1)
                    std::cerr << " arg1=" << args[1].object_id
                              << (args[1].is_null ? " NULL"
                                  : (args[1].type == DalvikType::OBJECT_REF
                                         ? (" " + args[1].class_desc) : ""))
                              << " line#";
                std::cerr << std::endl;
            }
        }
    }
    // S34 (R-NEW-333): content-state write identity — receiver state id +
    // written value id (bounded, env-gated). Upstream: the app lambda
    // (ComposableLambdaImpl) and the Content() read must hit ONE state.
    {
        static thread_local const bool cvw_on =
            std::getenv("MINIANDROID_CVPARI") != nullptr;
        if (cvw_on && class_name == "LF/V0;" &&
            (method_name == "setValue" || method_name == "getValue")) {
            static thread_local uint64_t cvw_n = 0;
            if (cvw_n < 90) {
                ++cvw_n;
                std::cerr << "[CV1-STATE-" << (method_name == "setValue" ? "W" : "R")
                          << "] state=" << (args.empty() ? 0 : args[0].object_id);
                if (method_name == "setValue" && args.size() > 1)
                    std::cerr << " val=" << args[1].object_id
                              << (args[1].is_null ? " NULL"
                                  : (args[1].type == DalvikType::OBJECT_REF
                                         ? (" " + args[1].class_desc) : ""));
                std::cerr << std::endl;
            }
        }
    }
    // S33 (R-NEW-332): LayoutNode census"""
src = src.replace(anchor, probe, 1)
open(P, 'w').write(src)
print('cvpari probe applied')
