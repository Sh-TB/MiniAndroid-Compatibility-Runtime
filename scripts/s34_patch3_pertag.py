#!/usr/bin/env python3
"""S34 probe 3: per-tag bounded counters in the CV1 probe (the shared cv1_n
counter suppressed late events after 400 method entries). Each tag gets its
own bound of 80. Also fixes the CV1-CONTENT tag to log its arg registers
later via the DEPTHBAND interplay. Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

old = """    {
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
    }"""

new = """    {
        static thread_local const bool cvpari_on =
            std::getenv("MINIANDROID_CVPARI") != nullptr;
        if (cvpari_on) {
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
            // [S34-PERTAG] per-tag bounded counters (shared counter was
            // suppressing late events — Content() runs AFTER startup churn).
            if (cv1_tag) {
                static thread_local uint64_t cv1_init_n = 0, cv1_setc_n = 0,
                    cv1_create_n = 0, cv1_content_n = 0, cv1_attach_n = 0,
                    cv1_acv_n = 0, cv1_e1a_n = 0;
                uint64_t* cnt = nullptr;
                if (cv1_tag[4] == 'I') cnt = &cv1_init_n;
                else if (cv1_tag[4] == 'S') cnt = &cv1_setc_n;
                else if (cv1_tag[4] == 'C' && cv1_tag[5] == 'R') cnt = &cv1_create_n;
                else if (cv1_tag[4] == 'C') cnt = &cv1_content_n;
                else if (cv1_tag[4] == 'A' && cv1_tag[5] == 'T') cnt = &cv1_attach_n;
                else if (cv1_tag[4] == 'A') cnt = &cv1_acv_n;
                else cnt = &cv1_e1a_n;
                if (*cnt < 80) {
                    ++*cnt;
                    std::cerr << "[" << cv1_tag << "] recv="
                              << (args.empty() ? 0 : args[0].object_id)
                              << " depth=" << recursion_depth_;
                    if (args.size() > 1)
                        std::cerr << " arg1=" << args[1].object_id
                                  << (args[1].is_null ? " NULL"
                                      : (args[1].type == DalvikType::OBJECT_REF
                                             ? (" " + args[1].class_desc) : ""));
                    if (!call_stack_.empty()) {
                        const StackFrame& cfr = call_stack_.top();
                        std::cerr << " caller=" << cfr.class_name << "."
                                  << cfr.method_name;
                    }
                    std::cerr << std::endl;
                }
            }
        }
    }"""

if old not in src:
    if '[S34-PERTAG]' in src:
        print('already present')
        sys.exit(0)
    print('ANCHOR NOT FOUND')
    sys.exit(1)

src = src.replace(old, new, 1)
open(P, 'w').write(src)
print('per-tag probe applied')
