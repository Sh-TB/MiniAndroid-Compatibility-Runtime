#!/usr/bin/env python3
"""T281-1C: exact function boundaries + namespace context for the two
bridge_to_api definitions and the domain chain. Answers: does
bridge_domain_ui_graphics really span the whole ui_graphics TU? Which
namespace encloses each bridge_to_api definition? What owns the lines
T280 called 'unreachable'?"""
import re
import sys

def analyze(path, start_line, tag):
    lines = open(path, errors="ignore").read().splitlines()
    depth = 0
    # namespace tracking: walk from file top recording namespace opens/closes
    ns_events = []  # (line, 'open'/'close', name)
    for i, line in enumerate(lines, 1):
        s = line.strip()
        m = re.match(r"namespace\s+([A-Za-z_][\w:]*)\s*\{", s)
        if m and not s.startswith("//"):
            ns_events.append((i, "open", m.group(1)))
        elif s.startswith("namespace {") or s == "namespace {" or \
                s.startswith("namespace\n{"):
            ns_events.append((i, "open", "ANON"))
        elif re.match(r"^\}\s*//\s*namespace", s):
            ns_events.append((i, "close", None))
        elif s == "}" and depth_marker_ok(i):
            pass
    # simpler: brace depth walk with namespace stack
    ns_stack = []
    in_block_comment = False
    def scan(line, lineno):
        nonlocal in_block_comment
        i = 0
        out = []
        while i < len(line):
            if in_block_comment:
                j = line.find("*/", i)
                if j < 0:
                    return out
                i = j + 2
                in_block_comment = False
                continue
            c = line[i]
            if c == '/' and i + 1 < len(line) and line[i+1] == '/':
                return out
            if c == '/' and i + 1 < len(line) and line[i+1] == '*':
                in_block_comment = True
                i += 2
                continue
            if c == '"':
                i += 1
                while i < len(line):
                    if line[i] == '\\':
                        i += 2
                        continue
                    if line[i] == '"':
                        i += 1
                        break
                    i += 1
                continue
            if c == "'":
                i += 1
                while i < len(line):
                    if line[i] == '\\':
                        i += 2
                        continue
                    if line[i] == "'":
                        i += 1
                        break
                    i += 1
                continue
            out.append((c, lineno))
            i += 1
        return out

    events = []
    for lineno, line in enumerate(lines, 1):
        events.extend(scan(line, lineno))

    depth = 0
    ns_stack = []
    func_depth = None
    func_start = None
    results = []
    pending_ns = None  # set when a namespace open was the last significant event
    line_of_char = [c for c, _ in events]
    it = iter(events)
    # Pre-index: map each brace char to its line
    idx = 0
    ev_list = list(events)
    # Walk with a namespace-open lookahead
    ns_open_lines = {}
    for lineno, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("//"):
            continue
        m = re.match(r"namespace\s+([A-Za-z_][\w]*)\s*\{?\s*$", s)
        if m:
            ns_open_lines[lineno] = m.group(1)
        elif s == "namespace {" or s.startswith("namespace {"):
            ns_open_lines[lineno] = "ANON"
        elif s.startswith("} // namespace") or s.startswith("}  // namespace"):
            ns_open_lines[lineno] = "CLOSE"

    char_no = 0
    while char_no < len(ev_list):
        c, lineno = ev_list[char_no]
        # namespace bookkeeping at line granularity
        if lineno in ns_open_lines and (char_no == 0 or ev_list[char_no-1][1] != lineno):
            v = ns_open_lines[lineno]
            if v == "CLOSE":
                if ns_stack:
                    ns_stack.pop()
            else:
                ns_stack.append(v)
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if ns_stack and depth == ns_depth_base and lineno in ns_open_lines and ns_open_lines[lineno] == "CLOSE":
                pass
        char_no += 1
    return results

def depth_marker_ok(i):
    return True

def simpler(path, start_line, name):
    """Brace-match the function starting at start_line; report its end line
    and the next function starts after it."""
    lines = open(path, errors="ignore").read().splitlines()
    depth = 0
    started = False
    end_line = None
    in_bc = False
    for i in range(start_line - 1, len(lines)):
        line = lines[i]
        j = 0
        while j < len(line):
            if in_bc:
                k = line.find("*/", j)
                if k < 0:
                    j = len(line)
                    continue
                j = k + 2
                in_bc = False
                continue
            c = line[j]
            if c == '/' and j+1 < len(line) and line[j+1] == '/':
                break
            if c == '/' and j+1 < len(line) and line[j+1] == '*':
                in_bc = True
                j += 2
                continue
            if c == '"':
                j += 1
                while j < len(line):
                    if line[j] == '\\':
                        j += 2
                        continue
                    if line[j] == '"':
                        j += 1
                        break
                    j += 1
                continue
            if c == "'":
                j += 1
                while j < len(line):
                    if line[j] == '\\':
                        j += 2
                        continue
                    if line[j] == "'":
                        j += 1
                        break
                    j += 1
                continue
            if c == '{':
                depth += 1
                started = True
            elif c == '}':
                depth -= 1
                if started and depth == 0:
                    end_line = i + 1
                    break
            j += 1
        if end_line:
            break
    print(f"[{name}] {path}:{start_line} -> function ends at line {end_line}")
    # next function starts after end
    pat = re.compile(r"^(bool|void|int|static|uint32_t|DalvikValue|std::string|float|double)\b")
    nxt = []
    for i in range(end_line, min(end_line + 400, len(lines))):
        if pat.match(lines[i]):
            nxt.append((i + 1, lines[i][:80]))
    for n in nxt[:6]:
        print(f"    next-def {n[0]}: {n[1]}")
    return end_line

e1 = simpler("miniandroid/src/dex/dalvik_bridge_domain_ui_graphics.cpp", 16, "ui_graphics::bridge_domain_ui_graphics")
e2 = simpler("miniandroid/src/dex/dalvik_bridge.cpp", 82, "dalvik_bridge::bridge_to_api")
e3 = simpler("miniandroid/src/dex/dalvik_engine.cpp", 38672, "dalvik_engine::bridge_to_api")
print("file line counts: ui_graphics",
      sum(1 for _ in open("miniandroid/src/dex/dalvik_bridge_domain_ui_graphics.cpp")),
      "bridge", sum(1 for _ in open("miniandroid/src/dex/dalvik_bridge.cpp")),
      "engine", sum(1 for _ in open("miniandroid/src/dex/dalvik_engine.cpp")))
