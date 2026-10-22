#!/usr/bin/env python3
"""CONT-11: Per-title problem sweep — every game/app in the frozen corpus,
its execution state, its registered problems, and cross-reference with root registry."""
import json, collections

BASE = '/home/z/my-project'
with open(f'{BASE}/docs/corpus/s82/title_registry.json') as f:
    reg = json.load(f)
titles = reg['TITLES']

# per-type + per-state counts
by_state = collections.Counter((t.get('STATE'), t.get('EXECUTION')) for t in titles)
print("== (STATE, EXECUTION) counts ==")
for k, v in by_state.most_common(20):
    print(f"  {k}: {v}")

# RENDERING / INTERACTION labels
by_render = collections.Counter(str(t.get('RENDERING')) for t in titles)
print("\n== RENDERING labels ==")
for k, v in by_render.most_common(15):
    print(f"  {k}: {v}")

# Titles with issue numbers
with_issue = [t for t in titles if t.get('ISSUE_NUMBER')]
print(f"\n== Titles with GitHub issue: {len(with_issue)} ==")

# Game vs app
games = [t for t in titles if t.get('TYPE') == 'game']
apps = [t for t in titles if t.get('TYPE') == 'app']
print(f"games: {len(games)}, apps: {len(apps)}, other: {len(titles)-len(games)-len(apps)}")

# Which titles are EXECUTED with evidence vs NOT_TESTED
exec_states = collections.Counter(t.get('EXECUTION') for t in titles)
print("\n== EXECUTION ==")
for k, v in exec_states.most_common():
    print(f"  {k}: {v}")

# Show a sample of executed games with their state
print("\n== EXECUTED GAMES (state, rendering, interaction) ==")
for t in games:
    if t.get('EXECUTION') == 'EXECUTED':
        print(f"  {t['TITLE_ID']} {t['PACKAGE']:40s} {str(t.get('STATE')):20s} {str(t.get('RENDERING')):28s} {str(t.get('INTERACTION'))[:40]}")

print("\n== EXECUTED APPS ==")
for t in apps:
    if t.get('EXECUTION') == 'EXECUTED':
        print(f"  {t['TITLE_ID']} {t['PACKAGE']:40s} {str(t.get('STATE')):20s} {str(t.get('RENDERING')):28s} {str(t.get('INTERACTION'))[:40]}")
