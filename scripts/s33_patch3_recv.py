#!/usr/bin/env python3
"""S33 probe 3: add receiver ids to LIFEWIN-IN entries (R-NEW-332 evidence)."""
import sys

C = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(C).read()

if 'recv=' in src.split('[LIFEWIN-IN]')[1][:300]:
    print('already patched')
    sys.exit(0)

anchor = """    if (lifewin_on && lifecycle_window_active_ && lifewin_count < 4000) {
        std::cerr << "[LIFEWIN-IN] " << class_name << "." << method_name
                  << " " << descriptor << std::endl;
        lifewin_count++;
    }"""
assert anchor in src, 'anchor not found'

new = """    if (lifewin_on && lifecycle_window_active_ && lifewin_count < 4000) {
        std::cerr << "[LIFEWIN-IN] " << class_name << "." << method_name
                  << " " << descriptor
                  << " recv=" << (args.empty() ? 0 : args[0].object_id)
                  << (args.empty() ? "" : args[0].class_desc)
                  << std::endl;
        lifewin_count++;
    }"""
src = src.replace(anchor, new, 1)
open(C, 'w').write(src)
print('recv ids added')
