# R-NEW-374 — String.valueOf(char) descriptor-driven overload law

**Status: VERIFIED-FIXED** · Discovered: S51 finalization (2026-09-16) · Priority P1

## Problem
Crossword fixture letter cells rendered decimal ASCII codes ("66", "77")
instead of characters ("B", "M") after `String.valueOf(TARGET[r][c])` where
`TARGET` is a `char[][]`.

## Observed signature
`frame9 visible_texts: view 49 = '66' (expected 'B'), view 58 = '77' (expected 'M')`

## Root cause
Two laws interact:
1. `aget-char` yields an INT register — REAL Dalvik law (K-41 normalization,
   engine-correct).
2. The `String.valueOf` bridge selected the overload by inspecting the
   runtime `DalvikValue` tag (INT32 → decimal path). DEX registers are
   untyped 32-bit slots; only the call site's **declared proto**
   `(C)Ljava/lang/String;` identifies the char overload.

## Upstream law
OpenJDK `String.valueOf(char)` renders the code point; ART resolves
overloads statically from the method_id's proto, never from runtime tags.

## Fix
`bridge_to_api` valueOf handler resolves
`resolve_method_proto_for_dex(method_idx_hint, current_dex_index_)`; when the
first parameter is `C`, the int is rendered as a UTF-8 code point regardless
of the INT tag. `valueOf(I)` path unchanged (decimal).

## Test
- crossword_golden validator: final grid letters exactly `A,A,B,E,M,O,P,P,R`
  + `SOLVED!` — ALL PASS (8 checks).
- Full battery after fix: **98/98 ALL PASS ×3 runs** (94 prior stages + 4 new
  game gates). Zero regressions.

## Runtime impact
Every char-array-driven UI (crosswords, word grids, minesweeper digits from
char lookup tables) renders correctly. Discovered BY the new game fixtures —
the fixtures doubled as a runtime probe.
