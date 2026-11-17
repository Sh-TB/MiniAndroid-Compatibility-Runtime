#!/usr/bin/env python3
"""W6 Phase 2: rigorous arm-terminal analysis for bridge_to_api (extraction
feasibility evidence) + interpreter dispatch-structure probe.
Checks per arm: last meaningful statement is an unconditional return;
no goto/[[fallthrough]] at arm level; lambdas present; static decls.
Output: appended into evidence/wave6/w6_arm_map.json as "arm_analysis".
"""
import json, os, re

strip_comment_re = re.compile(r"//.*$")

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave6"
am = json.load(open(f"{EV}/w6_arm_map.json"))
raw = open("src/dex/dalvik_bridge.cpp", errors="replace").read().split("\n")

analysis = []
for a in am["bridge_to_api"]["arms"]:
    body = raw[a["start"] - 1:a["end"]]
    last = None
    for l in reversed(body[:-1]):
        s = l.strip()
        if s and not s.startswith("//") and s != "}":
            last = s
            break
    joined = "\n".join(body)
    core = strip_comment_re.sub("", last or "")
    analysis.append({
        "start": a["start"], "end": a["end"], "lines": a["lines"],
        "last_stmt": (last or "")[:60],
        "ends_unconditional_return": bool(core.startswith("return ")
                                          and core.endswith(";")),
        "has_goto": bool(re.search(r"\bgoto\b", joined)),
        "has_fallthrough_attr": "[[fallthrough]]" in joined,
        "has_lambda": bool(re.search(r"\[&?\]?[(&]", joined)),
        "has_static_local": bool(re.search(r"^\s*static\s+", joined, re.M)),
        "cond_raw": a["cond"][:100],
    })
ends = sum(1 for x in analysis if x["ends_unconditional_return"])
gotos = sum(1 for x in analysis if x["has_goto"])
ft = sum(1 for x in analysis if x["has_fallthrough_attr"])
print(f"arms={len(analysis)} ends_with_unconditional_return={ends} "
      f"goto_arms={gotos} fallthrough_arms={ft}")
big = [x for x in analysis if x["lines"] >= 100]
print(f"arms>=100 lines: {len(big)} covering {sum(x['lines'] for x in big)} lines")
bad = [x for x in big if not x["ends_unconditional_return"] or x["has_goto"]
       or x["has_fallthrough_attr"]]
print(f"big arms violating extraction safety: {len(bad)}")
for x in bad[:6]:
    print("  VIOLATION:", x["start"], repr(x["last_top_stmt"][:50]))

# interpreter dispatch structure
iraw = open("src/dex/dalvik_interpreter.cpp", errors="replace").read().split("\n")
dispatch_styles = {
    "if_op_const": sum(1 for l in iraw if re.search(r'if\s*\(\s*op\s*==\s*OP_', l)),
    "if_op_hex": sum(1 for l in iraw if re.search(r'if\s*\(\s*op\s*==\s*0x', l)),
    "if_op_named_macro": sum(1 for l in iraw if re.search(r'case\s+OP_', l)),
    "execute_calls": sum(1 for l in iraw if re.search(r'\bexecute_\w+\(', l)),
    "continue_stmts": sum(1 for l in iraw if re.match(r'\s*continue;', l)),
    "goto_stmts": sum(1 for l in iraw if re.search(r'\bgoto\s+\w+;', l)),
}
span_body = "\n".join(iraw[183:5619])
interp = {
    "dispatch_styles": dispatch_styles,
    "loop_carried_state_refs": {k: len(re.findall(k, span_body)) for k in
                                [r"\bpc_\s*=", r"\bcontinue\b", r"\bhalted_\b",
                                 r"\bthrow\b", r"\bfind_catch_handler\b"]},
}
am["arm_analysis"] = analysis
am["fetch_decode_execute"]["structure"] = interp
json.dump(am, open(f"{EV}/w6_arm_map.json", "w"), indent=1)
print("interpreter structure:", json.dumps(interp["dispatch_styles"]))
print("loop-state refs:", interp["loop_carried_state_refs"])
