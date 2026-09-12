# HANDOFF_013 — Campaign 013 handoff

## Baseline (verified, not assumed)

```text
branch:        campaign-013 (created from main @ ea81e00)
baseline tag:  v0.13.0-baseline = ea81e00 = v0.11.3-unified-011-3
verified via:  handoff ZIP MiniAndroid_v0.11.3-unified-011-3_GIT_HANDOFF.zip
               SHA256 45bae5948c0fe403a9d09bfd30ece63ccc70fbb755726b6b41fbb837ddfa9e6d
               (byte-identical to VERSION_HANDOFF_MANIFEST_v0.11.3.md)
```

**Baseline discrepancy record (§1):** the campaign directive names
`v0.12.0 @ f5da664` as the baseline. That commit/tag/artifact does NOT exist
in this environment (no repository, no ZIP, no upload contains it; the
tag/commit space here is the verified v0.11.3 lineage). Campaign-012's
described results (bouncy menu, chessclock recursion, Shorty, CAS semantics)
have NO artifacts here and were treated as UNVERIFIED hypotheses throughout.
All BEFORE/AFTER measurements in this campaign are against the verified
v0.11.3 baseline. If the f5da664 artifact surfaces, the campaign-013 branch
rebases/merges cleanly (linear fixes on top of ea81e00).

## Final state

```text
final commit:  a6958b4 (hygiene redaction) — tag v0.13.0
fix commits:   a5f7995 FIX-013-01 (dialogs)
               cb621fc FIX-013-02/03 (hierarchy dispatch + inflation policy)
               b9d93cc FIX-013-04 (ARSC value paths; tag v0.11.4-fix-01)
               cd0463f FIX-013-05 (onDraw execution)
tags:          v0.13.0-baseline, v0.11.4-fix-01, v0.13.0 (final)
working tree:  clean at handoff
```

## Build & test commands

```bash
# build (rlottie static lib required at $RLOTTIE_DIR/build/src/librlottie.a)
cd miniandroid && make -j2          # binary: build/miniandroid

# semantic fixtures (mandatory gate)
g++ -std=c++17 -Isrc -Ithird_party/nlohmann_json/include \
    -o /tmp/f1 tests/unified0113_typed_catch_test.cpp $(find build -name '*.o' ! -name main.o) <libs>
/tmp/f1    # expect: 8 passed, 0 failed
# (same for unified0112_filled_new_array_test → 5/5)

# corpus triage (BEFORE/AFTER matrix generator)
python3 scripts/triage_013.py --stage after      # uses build/miniandroid
MINIANDROID_BINARY=... python3 scripts/triage_013.py --stage baseline

# goldens
./build/miniandroid run $CACHE/exp038_telegram/Telegram.apk -o /tmp/tg -v
#   screenshot.png SHA256 must equal 088ea640587ec0d28fc7cd16b0097f2529ff7da2d594c3c2663c67531d770f6a
./build/miniandroid run $CACHE/corpus/simplestopwatch.apk -o /tmp/ssw
#   screenshot.png SHA256 must equal 2a12587a0acf196cb9a52a521d6a7bc7d72e2d21dfa71eba41a694dbaa3d8c1b
```

## APK corpus + SHA256 (external cache only — zero APKs in the repo/ZIP)

Registry: `tests/corpus/apks.json` (canonical) + campaign-013 additions:

```text
gmdice                 1621eda11b5dbc0c… (registry-verified)
telegram_v12           f5e1192725772960… (registry-verified, re-downloaded byte-identical)
simplestopwatch/microtimer/unote/bgclock/chessclock/headingcalculator/
stopwatchmuellerma/simplekeyboard/openlauncher/tictactoeemmanuelmess/
notesbillthefarmer/dooz  registry-verified via download_test_apks.py
bouncy                 ffda0d9cb0b1b2aa58be9559dda891c4fa24391bc481d297a8e3d96c31f62721 (NEW, F-Droid 43)
droidify               08d5a826be0cc5b699139b80bd5b610a9b3663a69987bc082ac0d9825afc72f6 (NEW, F-Droid 760)
tinymusicplayer        d7bcb24d101b04beb3394b69… (REPLACED: v1 artifact was lost/truncated; v4 SHA-locked)
openlauncher           b3320463a7a1ed46… (drift vs registry documented: F-Droid re-upload; both sources agree)
```

## Verified results (headline)

- REAL_UI 3→5, REAL_INTERACTION 1→4, ACTIVITY_FAILED 10→6, BOOT_FAILED 1→0
  (same 17-APK corpus, same classifier; see REAL_APP_MATRIX_013.md).
- Six apps moved up: gmdice→REAL_INTERACTION (dialog chain),
  unote→REAL_INTERACTION, bouncy→REAL_INTERACTION (libGDX canvas),
  headingcalculator/chessclock/notesbillthefarmer→REAL_UI.
- Telegram golden + SimpleStopwatch golden + semantic fixtures 8/8+5/5: green
  after EVERY fix (regression-gated campaign).
- 4 high-leverage shared root-cause fixes landed (§23 target ≥4 met:
  dialogs, hierarchy dispatch, inflation+placeholder policy, ARSC value
  paths) + onDraw execution (5th).

## Known failures / remaining blockers

See TOP_BLOCKERS_013.md (OB-1..OB-7): Compose composition boundary, appcompat
activity chains, GLES GL-backend stages, multi-dex method index completeness,
microtimer app-side validation exception, WebView UIs, canvas state ops.

## Exact next campaign (recommended)

1. **AppCompat/fragment entry chain (OB-2)** — unlocks stopwatchmuellerma,
   openlauncher, simplekeyboard, and UNBLOCKS droidify up to setContent
   (feeds OB-1). Highest APK-count leverage.
2. **Compose composition hook (OB-1)** with dooz as reproducer; re-run
   droidify after OB-2.
3. **GLES Stage 1** (record/replay software GLES per GLES_REPORT_013 §14
   recommendation) with tictactoe as target; bouncy canvas path as the
   architectural template.
4. **Multi-dex method-index completeness (OB-4)** — small fix, unlocks
   CanvasFieldView (bouncy full game field).
5. Continue §7 dialog validation on unote/headingcalculator menus.

## Handoff artifact

- `MiniAndroid_v0.13.0_GIT_HANDOFF.zip` — the AUTHORITATIVE SHA256 lives in
  `MINIANDROID_HANDOFF_ZIP_SHA256_013.txt` next to the ZIP (the doc cannot
  embed its own container's hash; final packaged value at time of writing:
  0fb86ec45500bb54d4255205c13107d31382afcd55215e85d853b622dbd330eb,
  7,904,441 bytes).
- Contains: tracked tree @ v0.13.0 + shallow clone `repo/` (depth 120 =
  complete UNIFIED_011..013 lineage, branch campaign-013).
- **Shallow-boundary accuracy note:** the 011.3 handoff shipped a shallow
  .git while its manifest claimed "complete .git (75+3 commits)" — this
  campaign unshallowed from origin (350 commits, fsck clean) and packages an
  HONEST shallow clone with the boundary documented here.
- Safety scan: zero .apk/.jks/keystore, zero non-git >5MB files, zero
  credential patterns (truncated token fragment in GITHUB_UPLOAD_PLAN.md
  redacted at a6958b4).
- Clean-extraction test (§28): unzip → git log/status OK → make -j2 build OK
  → fixtures 8/8 + 5/5 → simplestopwatch golden `2a12587a` EXACT → Telegram
  golden `088ea640` EXACT. ALL GREEN from the pristine ZIP.
