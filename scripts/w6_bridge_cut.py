#!/usr/bin/env python3
"""W6 Phase 3: bridge_to_api arm extraction (verbatim whole-arm moves into
private member helpers; dispatch order and conditions preserved exactly).
Idempotent: always regenerates dalvik_bridge.cpp from git HEAD + state.
State (extra helper params discovered by compiler) persists in a JSON file.
Usage: w6_bridge_cut.py <topN|all> [--dry]
"""
import json, os, re, subprocess, sys

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave6"
BR = "src/dex/dalvik_bridge.cpp"
HDR = "src/dex/dalvik_engine.h"
STATEF = f"{EV}/w6_bridge_cut_state.json"
STATE = json.load(open(STATEF)) if os.path.exists(STATEF) else \
    {"extra_params": [["const std::vector<DalvikValue>&", "args"]], "extracted": []}

BASE_PARAMS = [("const std::string&", "class_name"),
               ("const std::string&", "method"),
               ("const std::vector<DalvikValue>&", "args_raw"),
               ("DalvikValue&", "result"),
               ("ApiCallTrace::Status&", "status"),
               ("uint32_t", "method_idx_hint")]
PARAMS = BASE_PARAMS + [tuple(p) for p in STATE["extra_params"]]

def sig_text():
    return ", ".join(f"{t} {n}" for t, n in PARAMS)

def call_text():
    return ", ".join(n for _, n in PARAMS)

def strip_line(l):
    s = l.split("//")[0].rstrip()
    return s

def strip_code_all(text):
    # comment/string-aware brace view (raw strings not expected in this file)
    out = []; i = 0; n = len(text); state = "code"
    while i < n:
        c = text[i]; nxt = text[i+1] if i + 1 < n else ""
        if state == "code":
            if c == "/" and nxt == "/": state = "lc"; out.append("  "); i += 2; continue
            if c == "/" and nxt == "*": state = "bc"; out.append("  "); i += 2; continue
            if c == '"': state = "str"; out.append(" "); i += 1; continue
            if c == "'": state = "chr"; out.append(" "); i += 1; continue
            out.append(c); i += 1; continue
        if state == "lc":
            out.append("\n" if c == "\n" else " ")
            if c == "\n": state = "code"
            i += 1; continue
        if state == "bc":
            if c == "*" and nxt == "/": state = "code"; out.append("  "); i += 2; continue
            out.append("\n" if c == "\n" else " "); i += 1; continue
        if state == "str":
            if c == "\\": out.append("  "); i += 2; continue
            if c == '"': state = "code"; out.append(" "); i += 1; continue
            out.append("\n" if c == "\n" else " "); i += 1; continue
        if state == "chr":
            if c == "\\": out.append("  "); i += 2; continue
            if c == "'": state = "code"; out.append(" "); i += 1; continue
            out.append(" "); i += 1; continue
    return "".join(out)

def select_arms(topn):
    am = json.load(open(f"{EV}/w6_arm_map.json"))
    an = am["arm_analysis"]
    sel = []
    for x in an:
        # coarse pre-filter only; the GCC -Wreturn-type probe below decides
        safe = not x["has_goto"] and not x["has_fallthrough_attr"]
        if x["lines"] >= 100 and safe:
            sel.append(x)
    sel.sort(key=lambda x: -x["lines"])
    if topn != "all":
        sel = sel[:int(topn)]
    sel.sort(key=lambda x: -x["start"])   # bottom-up processing
    return sel

def select_arms_filtered(topn, exclude_starts):
    return [a for a in select_arms(topn) if a["start"] not in exclude_starts]

def raw_span(lines, start, end):
    """Return (cond_text, body_lines). 'start' (1-based) is the line holding
    the arm's opening '{' (per the arm map); the condition may span several
    lines ABOVE it. Body = lines strictly between the braces (verbatim)."""
    i = start - 1                      # 0-based brace line
    assert "{" in lines[i], f"no brace at {start}"
    k = i
    while k > 0:
        prev = strip_line(lines[k - 1])
        if not prev or prev.startswith("#") or prev.lstrip().startswith("//") \
                or prev.endswith((";", "}", "{", ":")):
            break
        k -= 1
    cond = " ".join(strip_line(lines[t]) for t in range(k, i + 1)).strip()
    assert cond.endswith("{"), f"cond parse fail at {start}: ...{cond[-60:]}"
    cond = cond[:-1].strip()
    assert cond.startswith(("if", "else")), f"cond prefix fail: {cond[:40]}"
    body = lines[i + 1:end - 1]
    return cond, body

def main():
    argv = sys.argv[1:]
    args = [a for a in argv if not a.startswith("--")]
    topn = args[0] if args else "10"
    exclude = set()
    for a in argv:
        if a.startswith("--exclude="):
            exclude = set(int(x) for x in a.split("=", 1)[1].split(",") if x)
    arms = select_arms_filtered(topn, exclude) if exclude else select_arms(topn)
    dry = "--dry" in argv
    subprocess.run(["git", "checkout", "--", BR, HDR], check=True)
    lines = open(BR, errors="replace").read().split("\n")
    print(f"extracting {len(arms)} arms, "
          f"{sum(a['lines'] for a in arms)} lines; params: {call_text()}")
    helpers = []
    for a in arms:  # descending start => safe in-place edits
        cond, body = raw_span(lines, a["start"], a["end"])
        name = f"bridge_arm_{a['start']}"
        indent = "    "
        repl = [f"{indent}{cond} return {name}({call_text()});"]
        lines[a["start"] - 1:a["end"]] = repl
        helpers.append((name, body))
    STATE["extracted"] = [{"start": a["start"], "lines": a["lines"],
                           "helper": n} for (n, _), a in zip(helpers, arms)]
    # append helper definitions at END OF FILE with re-opened namespaces
    block = ["", "namespace miniandroid { namespace dalvik {"]
    for name, body in helpers:
        block.append(f"bool DalvikExecutionEngine::{name}({sig_text()}) {{")
        block.extend(body)
        block.append("}")
        block.append("")
    block.append("}  // namespace dalvik")
    block.append("}  // namespace miniandroid")
    text = "\n".join(lines).rstrip("\n") + "\n" + "\n".join(block) + "\n"
    # hoist empty-capture fn-scope static lambdas that extracted arms use
    # (stateless -> file-scope static is exactly equivalent)
    hoisted = []
    import subprocess as sp
    prefix = sp.run(["git", "rev-parse", "--show-prefix"], capture_output=True,
                    text=True, check=True).stdout.strip()
    blob = sp.run(["git", "show", f"HEAD:{prefix}{BR}"], capture_output=True,
                  text=True, check=True).stdout.split("\n")
    text2 = text
    for ident in STATE.get("hoist_ids", []):
        m = re.search(rf"^    static auto {ident} = \[\]\(",
                      "\n".join(blob), re.M)
        if not m:
            print(f"  hoist: {ident} not found as empty-capture static lambda"
                  f" -> ABORT"); raise SystemExit(2)
        start = ("\n".join(blob)[:m.start()]).count("\n")
        stripped = strip_code_all("\n".join(blob)).split("\n")
        depth = 0; end = None
        for i in range(start, len(blob)):
            depth += stripped[i].count("{") - stripped[i].count("}")
            if depth == 0 and i > start and blob[i].rstrip().endswith("};"):
                end = i
                break
        if end is None:
            print(f"  hoist: {ident} block end not found"); raise SystemExit(2)
        body_txt = "\n".join(blob[start:end + 1])
        if body_txt + "\n" not in text2:
            print(f"  hoist: {ident} block not verbatim in transformed file");
            raise SystemExit(2)
        text2 = text2.replace(body_txt + "\n", "")
        hoisted.append(body_txt[4:] if body_txt.startswith("    ") else body_txt)
    if hoisted:
        anchor = text2.find("namespace dalvik {")
        if anchor < 0:
            print("ns-dalvik anchor not found"); raise SystemExit(2)
        text2 = text2[:anchor] + "namespace {\n" + \
            "\n".join(hoisted) + "\n}  // namespace\n" + text2[anchor:]
        print(f"hoisted {len(hoisted)} stateless lambdas to file scope: "
              f"{[h.split()[2] for h in hoisted]}")
    open(BR, "w").write(text2)
    # header declarations: anchor inside class DalvikExecutionEngine via
    # brace matching on comment/string-stripped text
    hdr = open(HDR, errors="replace").read()
    hlines = hdr.split("\n")
    cls_start = next(i for i, l in enumerate(hlines)
                     if "class DalvikExecutionEngine" in l and "{" not in l) \
        if not any("class DalvikExecutionEngine" in l and "{" in l
                   for l in hlines) else \
        next(i for i, l in enumerate(hlines)
             if "class DalvikExecutionEngine" in l)
    depth = 0; cls_end = None
    for i in range(cls_start, len(hlines)):
        depth += hlines[i].count("{") - hlines[i].count("}")
        if depth == 0 and i > cls_start:
            cls_end = i
            break
    decls = ["  // WAVE-6 (ISSUE-612): bridge_to_api arm extraction — verbatim bodies"]
    for name, _ in helpers:
        decls.append(f"  bool {name}({sig_text()});")
    hlines[cls_end:cls_end] = decls + ["};-KEEP-ANCHOR-"]
    # place decls before the class's closing '};' line: cls_end points at the
    # line containing the closing brace; insert BEFORE it
    hlines = [l for l in hlines if l != "};-KEEP-ANCHOR-"]
    hdr = "\n".join(hlines)
    open(HDR, "w").write(hdr)
    json.dump(STATE, open(STATEF, "w"), indent=1)
    moved = sum(len(b) for _, b in helpers)
    print(f"wrote {len(helpers)} helpers, {moved} body lines moved; "
          f"decls inserted into {HDR}")
    if dry or os.environ.get("W6_SKIP_PROBE"):
        if not dry:
            print("W6_SKIP_PROBE=1 - probe skipped")
        print("DRY MODE - no build")
        return
    # GCC -Wreturn-type probe: find arms whose body can fall off the end
    # (the SIGILL root cause) and re-extract without them, automatically.
    mk = subprocess.run(["make", "--no-print-directory", "-n", "-B", "all"],
                        capture_output=True, text=True, timeout=300).stdout
    base = next(l.strip() for l in mk.splitlines()
                if " -c -o build/" in l and l.strip().endswith(BR))
    probe = base.replace("-o build/dex/dalvik_bridge.o",
                         "-o /tmp/w6prof/probe_bridge.o").strip() \
        + " -Werror=return-type"
    for it in range(5):
        r = subprocess.run(["bash", "-c", probe], capture_output=True,
                           text=True, timeout=400)
        bad_lines = [int(m.group(1)) for m in re.finditer(
            r"src/dex/dalvik_bridge\.cpp:(\d+):\d+: (?:warning|error): control "
            r"reaches end of non-void function", r.stderr)]
        other = [l for l in r.stderr.splitlines()
                 if (": error:" in l or ": fatal error:" in l)
                 and "control reaches end" not in l]
        if other:
            print("probe HARD ERRORS (undeclared hoist candidates?):")
            for l in other[:6]:
                print("  ", l.strip()[:130])
            subprocess.run(["git", "checkout", "--", BR, HDR], check=True)
            print("PROBE-FAIL - tree restored to pristine")
            sys.exit(2)
        if not bad_lines:
            print(f"probe pass iteration {it}: all {len(helpers)} helpers "
                  f"return on every path")
            return
        blines = sorted(bad_lines)
        # map warning line -> enclosing helper definition
        cur = None
        bad_helpers = set()
        for i, l in enumerate(open(BR, errors="replace").read().split("\n"), 1):
            m = re.match(r"bool DalvikExecutionEngine::(bridge_arm_\d+)\(", l)
            if m:
                cur = m.group(1)
            if i in blines and cur:
                bad_helpers.add(cur)
        if not bad_helpers:
            bad_helpers = {f"line{b}" for b in blines}
        excl = set()
        for e in STATE["extracted"]:
            if e["helper"] in bad_helpers:
                excl.add(e["start"])
        print(f"probe iteration {it}: fall-off-end helpers {sorted(bad_helpers)}"
              f" -> excluding arm starts {sorted(excl)}")
        exclude |= excl
        arms = select_arms_filtered(topn, exclude)
        return re_main(topn, exclude, dry=False)
    print("probe iterations exhausted")

def re_main(topn, exclude, dry):
    argv = [str(topn), "--exclude=" + ",".join(map(str, exclude))]
    globals()["_ARGV_OVERRIDE"] = argv
    sys.argv = [sys.argv[0]] + argv
    main()

if __name__ == "__main__":
    main()
