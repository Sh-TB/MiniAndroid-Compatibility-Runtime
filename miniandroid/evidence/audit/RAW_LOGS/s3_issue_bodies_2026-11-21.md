# S3 — issue bodies fetched 2026-11-21 (authenticated API)

## #635 — MASTER CROSS-CODER ACHIEVEMENT AUDIT — item-by-item verification ledger (50 claims: 30 confirmed, 4 rejected-measured, 5 partial, 4 blocked, 3 pending) [open]

labels: []

# MASTER CROSS-CODER ACHIEVEMENT AUDIT — complete item-by-item verification

Source mission: the pasted MASTER TASK (1040 lines, §0-§12). Execution date: **2026-11-20**. Auditor: independent (repo owner account), working from HEAD `d8b8fbb9` before audit edits, audit commit `9b953ce1`.

**Method (per mission §0):** every mandatory section read line by line; every claim tested where the environment allowed; no coder status accepted as proof; one disposition per claim; unavailable verification marked BLOCKED with the exact missing dependency — never turned into a PASS.

**Baseline manifest:** repo `Sh-TB/MiniAndroid-Compatibility-Runtime`, branch `main`, HEAD `d8b8fbb9`, tree clean at start. Toolchain g++ 14.2.0 + GNU Make; **cmake ABSENT** (CMake graph measurements BLOCKED, not skipped). Host 2 vCPU / 4 GB, hypervisor steal measured 24-25 % of every build window today. Tracker: 300 issues+PRs fetched via API — every mission-referenced issue exists (#586-#634, incl. #625/#626 as PRs). No destructive cleanup performed.

---

## §1 — Mission checklist (registered in full, nothing omitted)

### A. Issue #632 registry (194 items, 11 comments)
- [x] Fetched full body + all 11 comments via API (43 KB body + 132 KB comments)
- [x] Section structure mapped (§A hygiene → §R testing/CI)
- [x] Architectural corrections rechecked: layout path = `layout_inflater.cpp` ✔ (file + gravity handling verified); FriBidi/HarfBuzz/FreeType text pipeline ✔ (text_shaper.h + FONTS_LIBS); GridLayout absent ✔ CONFIRMED-live; nine-patch npTc absent ✔ CONFIRMED-live; ScrollView wiring PARTIAL (aged claim — wiring now exists, offset laws open); 174-attribute claim → item-level PENDING
- [x] B1/B2: CMake battery loop without EXCLUDE_FROM_ALL ✔ CONFIRMED (CMakeLists:493); QuickJS compiled twice (two OBJECT libs :298+:459) ✔ CONFIRMED-source (Make compiles once ✔); `all: $(EXECUTABLE) anchors` ✔; TEST_CORE/HOSTILE/LAW counts ✔; NEW-9 guard at :433 ✔ CONFIRMED (retraction justified); 52-links+OOM BLOCKED (no cmake; OOM NOT observed on Make path — peak RSS 1221 MB / 4 GB across ~40 full builds)
- [x] B1 historical figures (94k lines = 94,305 ✔ CONFIRMED; 5,436-line function → SUPERSEDED by W4 split default; PCH 36.4 s ✔ preserved rejection ×3; inline-params placebo ✔ preserved BUG-5)
- [x] B3 ccache ✔ CONFIRMED (cold 553.42 s / 0 hits; warm 20.94 s / 88-88; warm rebuild 25.40 s — committed logs)
- [x] B4 mold/lld ✘ REJECTED (link 1.5 s of 350 s)
- [x] B5 -gsplit-dwarf ✘ REJECTED-MEASURED TODAY (+4 % slower on heaviest TU, ABBA probe)
- [x] B6 ggc-min tuning ✘ REJECTED-MEASURED TODAY (3× slower — GC thrash)
- [x] B7 -fno-var-tracking-assignments ✘ REJECTED-MEASURED TODAY (no win; GCC14 fixed VTA; -g1 already covers)
- [x] B8 .DELETE_ON_ERROR ✔ CONFIRMED-missing → **FIXED: added to Makefile this audit**, behavior demo on failed target + full link rc0
- [x] B9 job pools ✔ CONFIRMED non-issue at -j2 (zero OOM in ~40 full builds)

### B. RC-12 ScaleType pixel-exact verification
- [x] Verifier + probe searched: `verifier/scaletype_oracle.py` ABSENT, `apps/probe_scaletype` ABSENT, commits `46ca6258/73dcadb6/1439627a/d77edba6` ABSENT (git cat-file ×4) → **BLOCKED / NOT-INTEGRATED** — the 0/579,784-pixel + 8/8-mutation results are NOT reproducible in mainline and are not counted as runtime capabilities
- [ ] Negative-mutation re-run → BLOCKED on obtaining the 4 commits

### C. #633 vector PathData / #634 animated drawable
- [x] MG-011 fix `out->ok = err.empty() && !paths.empty();` searched in src/ → **ABSENT → CONFIRMED-NOT-INTEGRATED** (top recovery candidate)
- [x] MG-010 clip-path: handling exists in vector_inflater.cpp + s132_svg_reader.cpp → PARTIALLY CONFIRMED (completeness tests open)
- [ ] #634 full source audit → PENDING (tracker state fetched: open, 5 comments)

### D. #630/#631 layout test apps
- [x] `apps/` directory EMPTY in mainline → **CONFIRMED-NOT-INTEGRATED** (diagnostic/local-only work); canonical tracking recommendation + links preserved in ledger

### 

---

## #633 — [MG-009] vector pathData parse failure — aapt2 string references unreachable through VectorRefResolver [open]

labels: []

## MG-009 — `vector pathData parse failure` on real aapt2 APKs

**Status: root-caused and fixed locally; commit blocked from pushing (see Limitations).**
**Domain:** `resource/asset` · **Upstream law:** AOSP `android.util.PathParser` + aapt2 resource table inlining.

### Symptom

Real, unmodified vector drawables from F-Droid apps failed to decode with:

```
DECODE_FAIL res/cc.xml: vector pathData parse failure
```

Three assets in one app (`org.secuso.privacyfriendlymemory_100.apk`) were affected: `res/cc.xml`, `res/tk.xml`, `res/wu.xml`. The decoder reported a *named* error rather than silently drawing nothing, which is correct per project law — but the path was perfectly valid.

### Reproduction

```
python3 -c "import zipfile; open('/tmp/cc.xml','wb').write(zipfile.ZipFile('/workspace/apk_cache/org.secuso.privacyfriendlymemory_100.apk').read('res/cc.xml'))"
./vec2png /tmp/cc.xml        # -> DECODE_FAIL vector pathData parse failure
```

Dumping the AXML element tree shows the `<path>` element's `pathData` attribute is **`TYPE_REFERENCE` (0x01)**, not `TYPE_STRING`:

```
START nm=19 (path) acnt=6
   attr ns=18 nm=0  raw=20          type=0x03 data=20          # name -> "eye_mask"
   attr ns=18 nm=6  raw=4294967295  type=0x01 data=2131689558  # pathData -> 0x7f0f0056
   attr ns=18 nm=5  raw=4294967295  type=0x01 data=17170443    # fillColor -> 0x0106000B
```

### Root cause

aapt2 hoists a large attribute value into `resources.arsc` and leaves only a reference in the compiled XML. The string pool for `cc.xml` contains no path data at all — the payload genuinely lives elsewhere:

```
0x7f0f0056 -> type=3 str='M12,4.5C7,4.5 2.73,7.61 1,12c1.73,4.39 6,7.5 11,7.5s9.27,-3.11 11,-7.5c-1.73,-4.'
0x7f0f0058 -> type=3 str='M2,4.27 L2,4.27 L4.54,1.73 L4.54,1.73 L4.54,1 L23,1 L23,23 L1,23 L1,4.27 Z'
0x7f0f0059 -> type=3 str='M3.27,4.27 L19.74,20.74'
```

The `VectorRefResolver` seam — the callback the decoder uses to reach app resources — carried only `is_color`/`argb` and `bytes`/`path`/`density`. **There was no way to return a string.** So the decoder read an empty attribute and correctly reported a parse failure. The bug is architectural: the resolver contract could not express the answer even though the ARSC had it.

### Fix

1. `VectorImageRef` gains `is_string` + `str_value` (`src/renderer/software_renderer.h`).
2. `ExecutionEngine::image_ref_resolver()` answers `TYPE_STRING` rows from the ARSC (`src/runtime/execution_engine.cpp`).
3. The decoder, on an empty `pathData` that is a reference, asks the resolver for the payload before declaring failure (`src/renderer/vector_decode.cpp`).

A missing resolver still produces the same named error — no silent blank drawable.

### Measured impact

Corpus of 4 real APKs in `/workspace/apk_cache`, density 160, counting only documents whose parsed root element is literally `<vector>`:

| | vectors decoded | failures |
|---|---|---|
| before | 41 / 44 | 3 |
| after | **44 / 44** | **0** |

Zero regressions: every vector that decoded before still decodes.

```
org.secuso.privacyfriendlymemory_100.apk   before 33/36   after 36/36
dubrowgn.microtimer_9.apk                  before  8/8    after  8/8
de.duenndns.gmdice_11.apk                  no vectors
omegacentauri.mobi.simplestopwatch_31.apk  no vectors
```

### Tests

`s257_vector_stroke_law_test` extended to 13 assertions. The three new ones:

```
PASS  R0_unresolved_ref_is_named_error — error='vector pathData parse failure'
PASS  R1_string_ref_resolves_and_renders — ok=1 calls=1 ink=3600
PASS  R2_ref_matches_inline_path — inline_ink=3600 ref_ink=3600
```

`R2` is the important one: the resolver path produces **byte-identical** raster output to the same path supplied inline. That proves the change is a pure substitution and does not fork the rendering code path.

Also added `tests/axml_gen.h` support for `TYPE_REFERENCE` attributes so law tests can emit genuine reference-carrying AXML.

Regressions: `s256` 14/14, `s243` 113/113, `s98` 21/21, `s

---

## #634 — [MG-012] animated-vector decodes to nothing; drawable references never resolve to a document [open]

labels: []

## MG-012 — `<animated-vector>` decoded to nothing, and no drawable reference could ever resolve

**Status: root-caused and fixed locally; commit blocked from pushing (see Limitations).**
**Domain:** `resource/asset` · **Upstream law:** `AnimatedVectorDrawable.getConstantState()`, `VectorDrawable.draw()`.

Two defects. The second is a shared-layer bug far wider than animated vectors.

### Symptom 1 — AVDs rejected outright

```
$ vecstat org.secuso.privacyfriendlymemory_100.apk
FAIL res/Ks.xml  vector: root element <animated-vector> unsupported
FAIL res/Q1.xml  ...
FAIL res/gZ.xml  ...
FAIL res/gl.xml  ...
FAIL res/jt.xml  ...
FAIL res/rE.xml  ...
VECTORS total=42 ok=36 fail=6
```

6 of the 42 vectors in this real APK are animated. Every one produced no image at all.

### Symptom 2 — no drawable reference could resolve (shared bug)

Adding the AVD path was not enough. The next failure was:

```
animated-vector: drawable 0x7f08005c did not resolve to a document
```

Investigating the reference showed why:

```
0x7f08005c: BRANCH=string str='res/Cb.xml'  <-- drawable file never extracted
0x7f080000: BRANCH=string str='res/cc.xml'  <-- drawable file never extracted
```

`ExecutionEngine::image_ref_resolver()` claimed **every** `TYPE_STRING` row as a pathData payload:

```cpp
if (val && val->is_string() && !val->string_value.empty()) {
    out->is_string = true; out->str_value = val->string_value; return true;
}
```

aapt2 also stores **drawable** references this way, with the payload being a zip entry path. That branch returned before `select_file()` ever ran, so `ref.bytes` stayed empty. This is why `<animated-vector android:drawable>` could never resolve — and it left `<adaptive-icon>` layer references exposed to exactly the same failure, since `decode_adaptive_icon()` consumes `ref.bytes`.

### Root cause

1. `decode_vector_drawable()` only accepted `root.name == "vector"`; `animated-vector` fell through to the generic unsupported-root error.
2. The resolver used the **type** of a table row to decide what it meant, but aapt2 uses `TYPE_STRING` for two different things: inline pathData payloads *and* file references.

### Fix

**AVD still frame.** AOSP `AnimatedVectorDrawable.getConstantState()` builds its `VectorDrawable` from `android:drawable`, and `VectorDrawable.draw()` paints whatever the *current* property values are. So the honest still frame is the referenced VD rendered with its **own declared attributes** — not a frame synthesised from an animator's `start` values, which is the tempting wrong answer (it would also be wrong for any animation mid-flight).

Root-level `<target>`/`<objectAnimator>` carry no paint and are consumed rather than walked. Depth-guarded against cycles.

**Resolver.** A string row whose payload is a `res/*.xml` entry is a *file*, so it now takes the file branch and extracts the bytes:

```cpp
const bool looks_like_entry =
    sv.rfind("res/", 0) == 0 &&
    (sv.size() > 4 && sv.compare(sv.size() - 4, 4, ".xml") == 0);
```

This is a shared fix at the resolver layer, not an AVD-specific hack: it repairs drawable reference resolution for every consumer.

### Measured impact on the real corpus

| | vectors decoded | failures |
|---|---|---|
| before | 36 / 42 | 6 |
| after | **42 / 42** | **0** |

All six previously-failing AVDs now render real, recognisable media-control icons:

| asset | size | ink px | PNG sha256 |
|---|---|---|---|
| `Ks.xml` | 32×32 | 188 | `1b489043d338df86ae404618bd7575495845a4fe32575ab5fc92d7f8a152eddc` |
| `Q1.xml` | 32×32 | 330 | `5353de54fc44861cd32527d7355cc1cd77cce4001aa68946846a45d3b25f75c4` |
| `gZ.xml` | 32×32 | 124 | `203e49cc69bc7feb4d3bf721a42d18a43fcf5273c696edcc3cea0b86978e2214` |
| `gl.xml` | 32×32 | 266 | `b0eddc8fe930e1eaf31f9836df0831f8084072422882fb27db9f36c9e16793bc` |
| `jt.xml` | 32×32 | 360 | `e976891e725c9862c4cb0f101732d0a21f9eb74c8481bdd0c2b002335cbd04b2` |
| `rE.xml` | 32×32 | 283 | `2113c37ca68cd59e696f9facea8e9417403024210f576abec5f69202847659ce`

---

