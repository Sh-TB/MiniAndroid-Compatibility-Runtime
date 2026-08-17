# EXP-054 — Collection Runtime Status

**Date:** 2026-08-17
**Phase:** 2

## D-Suggestion #2 — [Verified]

D's suggestion that hardcoding `List.isEmpty → true` is dangerous is correct. A blanket `true` would make every List in the application appear empty, causing silent corruption (e.g., `for (Object o : list)` would iterate zero times, but `list.get(0)` would throw IndexOutOfBoundsException because the list thinks it's empty when it's not).

## Current Collection Support

**Does the runtime have:**

| Operation | Status |
|-----------|--------|
| `List.add()` | NO — no collection model |
| `List.get()` | NO |
| `List.size()` | NO |
| `List.isEmpty()` | NO — returns void (0), treated as false |
| `ArrayList.<init>()` | NO — allocated on heap but no state |
| `Iterator.hasNext()` | NO |
| `Iterator.next()` | NO |
| `Map.put()` | NO |
| `Map.get()` | NO |

## Heap Object Model

The `DalvikHeap` stores objects by `object_id` with a `class_desc` and field map. There is NO collection-specific state (no element list, no size counter, no backing array).

When `new-instance v0, Ljava/util/ArrayList;` executes, a heap object is allocated with `class_desc = "Ljava/util/ArrayList;"` and no fields. Subsequent `List.add(v0, item)` calls go through `bridge_to_api` which has no handler — the items are silently discarded.

## Implementation Plan

Instead of a global stub, implement a **CollectionShadow** that tracks real state per-collection-instance:

1. Each collection heap object gets a `CollectionState` (vector of elements + size).
2. `add(item)` → append to the vector, return true.
3. `get(index)` → return element at index (or null if out of bounds).
4. `size()` → return vector size.
5. `isEmpty()` → return `size == 0`.
6. `Iterator.hasNext()` → check if iterator position < size.
7. `Iterator.next()` → return element at position++, or null if exhausted.

This is NOT a global `return true` — it's real, state-based semantics.
