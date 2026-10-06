#!/usr/bin/env python3
"""CONT-10 W6 — invalidation-chain analysis of dooz method trace.
Chain (upstream Compose 1.11.4 GapComposer law):
  state write -> CompositionImpl.recordModificationsOf (Lwo;.c)
             -> CompositionImpl.invalidate (Lwo;.s/.t)
             -> RecomposeScopeImpl.invalidateForResult (Lza1;.b)
  recompose  -> CompositionImpl.? (Lwo;.w) -> GapComposer.doCompose (Lnb0;.n)
             -> GapComposer.updateComposerInvalidations (Lnb0;.c0)
             -> recomposeToGroupEnd -> scope.compose -> block.invoke  [Lom;/Lj90; family]
Counts + line-split pass#1 (initial) vs pass#2 (frame-driven recompose)."""
import re, sys
from collections import Counter

ENTRY = re.compile(r"^\[METHOD-IN\] (L[^;. ]*;)\.([^ ]+)")

WATCH = ['Lwo;.c','Lwo;.s','Lwo;.t','Lza1;.b','Lza1;.a','Lza1;.c','Lza1;.d',
         'Lnb0;.n','Lnb0;.c0','Lnb0;.a0','Lnb0;.D','Lnb0;.U','Lnb0;.p','Lnb0;.h0',
         'Laj0;.<init>','Lbj0;.<clinit>','Lwo;.w','Lwo;.j','Lwo;.k','Lom;.h','Lj90;']

events=[]  # (lineno, cls, meth)
for i,line in enumerate(open(sys.argv[1],errors='replace')):
    m=ENTRY.match(line)
    if m: events.append((i+1,m.group(1),m.group(2)))

counts=Counter()
for _,c,m in events:
    counts[f'{c}.{m}']+=1

print('== whole-run counts (watched) ==')
for k in WATCH:
    if counts.get(k): print(f'  {k:18s} {counts[k]}')
# composable-lambda-ish invokes: Lom;.h and any Lj90; implementor h
hinv=[(n,c,m) for n,c,m in events if f'{c}.{m}'=='Lom;.h']
if hinv:
    print('== Lom;.h (ComposableLambda.invoke) entries ==')
    print('  lines:', [n for n,_,_ in hinv])
# find doCompose (Lnb0;.n) entry lines -> pass boundaries
nlines=[n for n,c,m in events if f'{c}.{m}'=='Lnb0;.n']
print('== Lnb0;.n (doCompose) entries at lines:', nlines)
if len(nlines)>=2:
    p1s,p2s=nlines[0],nlines[1]
    for tag,lo,hi in [('pass#1',0,p2s),('pass#2',p2s,10**9)]:
        cc=Counter()
        for n,c,m in events:
            if lo<=n<hi: cc[f'{c}.{m}']+=1
        print(f'== {tag} (lines {lo}..{hi}) watched ==')
        for k in WATCH:
            if cc.get(k): print(f'  {k:18s} {cc[k]}')
        print(f'  total entries {sum(cc.values())}')
