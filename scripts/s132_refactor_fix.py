#!/usr/bin/env python3
"""s132_refactor_fix.py — fixups for the R-NEW-440 refactor pass 1:
1) replace remaining bare measure( calls inside the extracted law body
   (the \\b-after-']' regex boundary never matched before ',');
2) remove the stray lambda terminator ('    };') left by the body cut.
Idempotent.
"""
import sys

P = "/home/z/my-project/miniandroid/src/resources/layout_inflater.cpp"
src = open(P).read()

start = src.index("LayoutInflater::measure_node_raw")
end = src.index("void LayoutInflater::measure_layout")
region = src[start:end]

# 1) bare recursive measure( calls → measure_node(views, …)
n_calls = region.count("measure(")
region = region.replace("measure(", "measure_node(views, ")
# undo any accidental double-prefix
region = region.replace("measure_node(views, measure_node(views, ",
                        "measure_node(views, ")
# the raw fn must not have rewritten its own recursion marker comments
region = region.replace("measure_node(views, …", "measure(…")

src = src[:start] + region + src[end:]

# 2) stray lambda terminator: the body still ends with
#      return {n->measured_width, n->measured_height};
#    };
#    (blank)
#    return {n->measured_width, n->measured_height};
#    }
#    Remove the '};' + blank line between the two returns.
dup = ("        return {n->measured_width, n->measured_height};\n"
       "    };\n"
       "\n"
       "    return {n->measured_width, n->measured_height};\n"
       "}\n")
if dup in src:
    src = src.replace(
        dup,
        "        return {n->measured_width, n->measured_height};\n}\n", 1)
    print("stray lambda terminator removed")
else:
    print("no stray terminator found (already clean)")

open(P, "w").write(src)
print(f"rewrote {n_calls} bare measure( call sites in the law body")
