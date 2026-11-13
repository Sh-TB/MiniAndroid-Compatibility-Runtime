#!/usr/bin/env python3
"""S232: post the P0-closeout receipt on #582 (the GP audit tracker)."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

BODY = """# S232 receipt (operator, main line) — the two P0 rows dispositioned against current main; GP-DEX-012 residual CLOSED with a two-directional ASan discriminator

**Reviewed HEAD:** `0f78b77a` (S232 P0 wave, pushed). Binary under test `006d05fc28f8c090` (post-P0-fix, clean build). Re-verification followed the master-directive §6 law: every finding re-checked against CURRENT source before any patch.

## CLOSED — [GP-DEX-012] (the residual, fixed + discriminated)

- **Re-verification:** 7 of the 8 listed checks already carried the uint64 cast from the earlier wave (`interfaces_off`/`annotations_off`/`class_ann_off`/`item_off` ×2/`annotations_off + 16`/`ann_set_size` range). The **one residual**: the method-annotation walk's `set_off` guard (`dex_parser.cpp:816`) and its follow-up range check (823) still evaluated `set_off + 4` in 32-bit — `set_off` is `uint32_t`; `0xFFFFFFFC + 4` wraps to 0, passes the guard, and `data + set_off` memcpy reads ~4 GiB past the buffer. Same wrap family, same ASan SEGV shape as the original reproducer.
- **Fix:** both checks now cast `set_off` to 64-bit BEFORE the addition (the exact law the fixed siblings already obey).
- **Discriminating regression, proven BOTH directions under ASan:** the crafted DEX (0x70 header + one class_def + annotations_directory_item fields_size=0 methods=1 + method_annotation with `set_off=0xFFFFFFFC`) **SEGVs the pre-fix parser at `dex_parser.cpp:820` in `parse_class_defs` (exit=1, exact ASan reproducer)** and **passes the post-fix parser clean** (no ASan report). Pinned in `gp_dex003_fuzz_law_test.cpp` (negative wrapped-set_off row + positive valid-annotation control): 13/13 rows, ASan build 13/13.

## VERIFIED-ALREADY-FIXED — [GP-RES-001] (no code change needed; regression rows PINNED)

- **Re-verification:** `string_pool.cpp` on current main carries the full 64-bit law the finding demanded 1:1 (in-source GP-RES-001 comment block): validation precedes the `resize` (face 1), offset-table arithmetic in uint64 (face 2), `strings_start64 + off >= chunk_size` guard with the Arsc empty-entry face (face 3), `remain` underflow unreachable given the 64-bit guard.
- **What was missing:** the finding's regression rows. Now pinned in `resource_core_law_test.cpp` §10 — the exact GP reproducer (64-byte chunk, `strings_start=0xFFFFFFF0`, entry `0x20`) must answer the empty-entry/named-error face and never dereference; count `2^30` offset-table wrap rejected pre-allocation; `chunk_size > avail` rejected; valid 2-string pool positive control. **46/46 rows pass.**

## TESTED (regression discipline)

- `make test-all` **29/29**; **six-pin gate ALL HOLD byte-exact** on the post-P0 binary: bouncy `98abca38` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 identical / microtimer `b39665f6` 0-uncaught / ttt `7354c1b2` ×3 deterministic → the dex-parser hardening is **pin-neutral**.

## REMAINING (the ledger's other rows, unchanged by this wave)

- `GP-INT-012…015`, `GP-NET-001`, `GP-JNI-001/002` and the GLES/LAYOUT/TEST rows keep their ledger statuses — next per the §6 seven-step loop, each re-verified against current source first.
"""

cred = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
token = [l.split("=", 1)[1] for l in cred.splitlines() if l.startswith("password=")][0]
req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/582/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {token}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "s232-receipt"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    out = json.loads(r.read().decode())
    print(f"posted #582 comment id={out['id']}")
