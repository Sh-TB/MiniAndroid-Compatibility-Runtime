#!/usr/bin/env python3
"""FINAL CAMPAIGN PHASE 11 — dalvik_engine/shadow call-contract audit.
Classifies every shadow-dispatch method answer in android_shadows.cpp:
  CONTRACT-OK  — void AOSP method (lawfully void) or state captured
                 engine-side (post-dispatch hook) before the void answer
  STATE-LAW    — returns a value carrying state (getters)
  SILENT-VOID  — a mutator-shaped method (set*/add*/remove*/clear*/put* /
                 register*/start*/stop*) answered void with NO capture —
                 each is a candidate silent-state-drop (the P1-2 pattern)
Also census the dalvik_engine post-dispatch hooks that capture state so
SILENT-VOID hits can be cross-checked against an engine hook.
"""
import re
from pathlib import Path

SRC = Path('/home/z/my-project/miniandroid/src/framework/android_shadows.cpp')
ENGINE = Path('/home/z/my-project/miniandroid/src/dex/dalvik_engine.cpp')
txt = SRC.read_text(errors='ignore')
etx = ENGINE.read_text(errors='ignore')

# every `if (m == "...")` / `method == "..."` guard preceding handled_void
void_sites = []
for mm in re.finditer(r'if \(m(?:ethod)? == "([A-Za-z0-9_$<>]+)"\)', txt):
    tail = txt[mm.end():mm.end() + 400]
    if 'handled_void' in tail:
        void_sites.append((mm.group(1), mm.start()))

mutator = re.compile(
    r'^(set|add|remove|clear|put|register|unregister|start|stop|post|'
    r'send|attach|detach|show|hide|enable|disable|assign|record)[A-Za-z0-9_]*$')

# engine hooks that already capture the same call (post-dispatch hooks)
engine_hooks = set(re.findall(r'method == "([A-Za-z0-9_$<>]+)"', etx))

state_capture_hint = re.compile(
    r'(set_object_field|set_bg_|->set_|_shadow_->|heap_\.|field_trace|'
    r'ViewNode|node->|\bn->|\bn2->|pending_|listener|store|capture)', re.I)

silent, lawful_void, verified = [], [], []
for name, pos in void_sites:
    # find the enclosing block text (up to 800 chars before the guard)
    ctx = txt[max(0, pos - 800):pos + 400]
    if not mutator.match(name):
        lawful_void.append(name)
        continue
    if name in engine_hooks:
        verified.append(name)
        continue
    if state_capture_hint.search(ctx):
        verified.append(name)
    else:
        silent.append(name)

print(f'void-answer sites: {len(void_sites)}')
print(f'  lawful-void (non-mutator): {len(lawful_void)}')
print(f'  state-capture verified:    {len(verified)}')
print(f'  SILENT-VOID mutators:      {len(silent)}')
for s in sorted(set(silent)):
    print('    -', s)
