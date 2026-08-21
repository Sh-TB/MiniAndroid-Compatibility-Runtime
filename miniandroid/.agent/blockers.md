# EXP-071 + EXP-072+ Blockers

Live list of blockers and TODOs. Updated during the EXP-071 reconciliation pass.

## EXP-071 status: ✅ CHECKPOINT_M = PROVEN — NO ACTIVE BLOCKERS

All blockers from the EXP-071 campaign have been resolved. The 16 generic fixes listed in `docs/EXP071_FINAL_REPORT.md` section 4 are complete and verified.

The following items were OPEN during EXP-071 but are now closed:

1. ~~`aget-boolean` does not read from heap~~ — FIXED in S1
2. ~~`instance-of` always returns false~~ — FIXED in S2
3. ~~`getContext`/`getParentActivity` return null~~ — FIXED in S2
4. ~~`String.length()`/`TextView.length()` return 0~~ — FIXED in S3
5. ~~`fill-array-data` payload offset wrong~~ — FIXED in S3
6. ~~Opcode table off-by-one for 0x24–0x2A~~ — FIXED in S4
7. ~~`FactorAnimator.animateTo` infinite loop~~ — FIXED (stubbed) in S4
8. ~~No async Runnable scheduling~~ — FIXED in S5
9. ~~`const-wide` wrong slot~~ — FIXED in S5
10. ~~No asset reading~~ — FIXED in S6
11. ~~`HashMap.get` treats key as int~~ — FIXED in S7
12. ~~Missing `toUpperCase`/`toLowerCase`/`TextUtils` stubs~~ — FIXED in S6
13. ~~Per-DEX const-string resolution uses merged table~~ — FIXED in S8 (bundled into S10)
14. ~~`unzip` asset path missing `assets/` prefix~~ — FIXED in S9 (bundled into S10)
15. ~~`try_shadow_dispatch` treats args[0] as receiver for static calls~~ — FIXED in S10
16. ~~`isSimAvailable` returns true causing SIM loop~~ — FIXED in S4

## Pre-existing non-blockers (still open, do NOT prevent CHECKPOINT_M)

These were open before EXP-071, remain open, and do not block any EXP-071 criterion:

### Loops caught by detector (50K-iteration limit)

- `LocaleController.getLocaleFileStrings (PC=0x38)` — infinite loop because locale strings file is not in APK. Caught by detector. Does not prevent runtime completion (exit 0) or screenshot generation.
- `FragmentFloatingButton.onFactorChanged (PC=0x3e)` — infinite loop because factor animation never completes. Caught by detector. Does not prevent runtime completion.

### Layout / rendering limitations (carried over from EXP-061)

- Layout is approximate (simple vertical stack, not real Android measure/layout). Affects screenshot fidelity but not the semantic proof.
- No real drawable decoding (ImageView placeholders are gray rectangles).
- `Resources.getColor` returns default black.

### Code hygiene (non-fatal warnings)

- `apk_path_` redeclaration warning in `dalvik_engine.h:1650` — merge artifact, can be cleaned up.
- `ready` variable shadowing in `HandlerShadow::drain_ready` (android_shadows.cpp:475) — non-fatal.
- `run.log` is non-deterministic across runs (timestamps). Expected; not a defect.

## Blockers for the NEXT experiment (EXP-072+)

The next experiment should target a GENERIC compatibility feature. Ranked candidates with their blockers:

### Candidate 1: Real drawable decoding (RECOMMENDED)

**Blockers:**
- Need to integrate libpng/libjpeg/libwebp into the build (or use existing Android libbitmap equivalents).
- Need to wire `BitmapFactory.decodeResource(int)` to the ARSC parser from EXP-063.
- VectorDrawable (XML) requires path parsing.

**Estimated effort:** Medium. Existing tools: `tools/exp067_axml_parser.py` (XML), `tools/exp063_arsc_parser.py` (resources).

### Candidate 2: Real color resolution

**Blockers:**
- `Resources.getColor(int)` needs to resolve from `<color>` entries in the ARSC table.
- 165 color resources already catalogued in `resource_values.json`.

**Estimated effort:** Low. Mostly a wiring task.

### Candidate 3: Generic LayoutInflater (setContentView(R.layout.foo))

**Blockers:**
- AXML parser exists (`tools/exp067_axml_parser.py`) but is Python-only; needs C++ port.
- Need to handle `merge`/`include`/`ViewStub` tags.
- Need to wire `setContentView(int)` to inflate the layout.

**Estimated effort:** High. Several days.

### Candidate 4: Real measure/layout engine

**Blockers:**
- No `View.measure(int, int)` / `View.layout(int, int, int, int)` execution.
- Need MATCH_PARENT/WRAP_CONTENT/weight/margin semantics.
- Need to integrate with the existing `dump_view_tree` JSON output.

**Estimated effort:** High. Several days.

### Candidate 5: JNI / loadLibrary

**Blockers:**
- All native methods currently stubbed.
- Need to implement `dlopen`/`dlsym` for `.so` files inside the APK.
- Need to handle JNI signatures and call into native code (or emulate via interpretation).

**Estimated effort:** Very high. Week+.

## Credential / infrastructure status

- ✅ Git push to `origin/main` works (token in remote URL).
- ✅ GitHub API works via curl (token authentication).
- ❌ `gh` CLI is NOT installed in this environment. All GitHub operations go through the REST API.
- ✅ All EXP-071 commits and the merge commit are pushed to `origin/main`.
- ✅ All 12 session comments are posted on issue #7.

---
