#!/usr/bin/env python3
"""ISSUE-612 WAVE-2 receipt comment."""
import json, subprocess, re

cfg = subprocess.run(["git", "config", "--list"], capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
tok = re.search(r"github_pat_[A-Za-z0-9_]*", cfg).group(0)

body = """## WAVE 2 RECEIPT — audit + fast-feedback infrastructure landed (measured)

**Runtime:** additive Makefile layer + `dev.py` + first L0 component test; production profile byte-untouched; all experiment edits reverted (0 dirty). Full report: `evidence/issue612_audit/REPORT.md`.

### Phase 1 — the "4-minute change" root cause, measured

| Cost component | Measured |
|---|---:|
| `dex/dalvik_engine.cpp` @ `-O2` (production) | **216.24 s**, peak ≈ 2.9 GB |
| same TU @ `-O0 -g0` | **35.8–38.5 s** |
| PCH probe (json.hpp + engine header prebuilt) | 36.4 s → **NO benefit, rejected** |
| Full-binary link, warm cache | **1.27 s** (cold first link ≈ 56 s, disk-bound) |

The frontend (parse/sema of 94,194 lines) dominates — not codegen, not headers, not the linker. Header fan-out: `android_shadows.h` → **18 TUs** (the wide header); `dalvik_engine.h` → only 4 ✓. Largest functions: `CollectionShadow::dispatch` **4,449 lines**, `stage_execute_application_real_dalvik` **2,056**, `ActivityShadow::dispatch` 1,360. Inside `dalvik_engine.cpp`: only **20,954 of 94,194 lines** are `DalvikExecutionEngine::` methods — **~73 K lines are free-function law families in anonymous namespaces** (lines 64/932/4421/7181…), which defines the real Wave-3 split surface.

### Delivered (Phases 3/4/6/7)

1. **`make DEV=1`** — `-O0 -g0` for every TU, into a **separate `build_dev/` tree** (make tracks timestamps, not flags: a dev build can no longer ship `-O0` objects into the production binary).
2. **`make module MODULE=<m>`** — manifest-filtered per-module object builds (dormant/broken sources excluded exactly like the main build).
3. **First L0 component test**: `make DEV=1 mutf8_component` — links ONLY production `dex/mutf8.o`; **24 checks PASS in 0.4 s** (ULEB128/SLEB128/MUTF-8 laws incl. encoded-NUL, CESU-8 surrogate combine, declared/decoded cross-check).
4. **`dev.py`**: `build module` · `test component` · `test module` · `test affected` · `run-apk` · `test regression` · `timings`.

### Phase 9 experiments (real edits, reverted; DEV=1) vs Phase 8 targets

| Exp | Change | Measured | Target | |
|---|---|---:|---|---|
| F | no-change rebuild ×3 | **0.02 s** | <1 s | ✅ |
| L0 | component change → test loop | **0.41 s** | <5 s | ✅ |
| D | framework component + link | **8.1 s** | <15 s | ✅ |
| A | dalvik arithmetic-law touch | **38.5 s** + link | <30 s | ❌ split-dependent |
| B/C | register / reflection laws | same TU as A | <30 s | ❌ split-dependent |
| E | shared header (18-TU fan-out) | **98.4 s** | — | ⚠️ measured |

Production-profile reference for A: **216 s + link** — the dev loop is already ~6× faster; the split takes the law-change loop to ≈ 11 s (24 K-line TU ≈ 10 s + 1.3 s link).

### Findings

1. **`resources/real_layout.cpp` is a broken dormant TU** (`AxmlNode`/`ResolvedValue`/`parse()` drifted from current headers) — not in the manifest, not linked; module targets now skip it; proposed for `DORMANT_SOURCES` or repair.
2. **The `-O2 -g` OOM family extends beyond CONT-37/39** (real_layout died during an experiment pass) — the `-g0` precedent needs a per-TU audit.
3. **ccache**: not installable on this host (apt blocked) — rejected this wave; `build_dev/` + module targets cover the need.
4. **`-j2` unsafe while the dalvik TU compiles** (2.9 GB @ -O2 on a 4 GB host).

### Wave-3 split plan (Phase 2 — incremental, one boundary per session)

`dex/dalvik_detail.h` internal interface → migrate anonymous-namespace law helpers → extract, in order: JSON/diagnostic glue (~1 K lines, lowest coupling) → resource/asset law family → exception-handling family → opcode dispatch (the 4.4 K-line core, last, behind a stable dispatch-table interface). Each boundary lands with: both TUs compile + link + one real-APK re-run comparison. Acceptance after the split: one small dalvik change → ~10 s compile + 1.3 s link + PASS/FAIL, no full-runtime involvement.

Phase 10 guardrails: additive-only, production profile untouched, no test removed, manifest remains the single source of truth."""

url = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/612/comments"
out = subprocess.run(
    ["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {tok}",
     "-H", "Content-Type: application/json",
     "-d", json.dumps({"body": body}), url],
    capture_output=True, text=True).stdout
d = json.loads(out)
print(d.get("html_url", d.get("message", "ERR")))
