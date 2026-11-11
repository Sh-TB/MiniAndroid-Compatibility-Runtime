#!/usr/bin/env python3
"""S220: post wave receipts on #582 and #583."""
import json, subprocess

TOKEN = None
r = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                   capture_output=True, text=True, cwd="/home/z/my-project")
for line in r.stdout.splitlines():
    if line.startswith("password="):
        TOKEN = line.split("=", 1)[1]

def post(issue, body):
    url = f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments"
    cmd = ["curl", "-sS", "-X", "POST", "-H", f"Authorization: token {TOKEN}",
           "-H", "Accept: application/vnd.github+json", url,
           "-d", json.dumps({"body": body})]
    out = subprocess.run(cmd, capture_output=True, text=True)
    resp = json.loads(out.stdout)
    print(f"#{issue} comment id:", resp.get("id"))

BODY_582 = """# GP — S220 wave receipt: TheXTech early-exit gate CLOSED (real launcher UI rendered), frame-truth verifier landed, DEX-003 fuzz battery, dooz state advance, A-R5 + IMG-004 landed

**Commits:** `39b7ab69` + `05ef1e86` (pushed). Binary sha16 `9adf7d627bcbdac6`.

## 1. Cross-app root #1 (§2.1 Activity/task/window/root) — IMPLEMENTED / TESTED / OBSERVED

**`Activity.isTaskRoot()` implemented** (AOSP law over the G08 task-record stack: receiver==current → root iff stack empty; stack index 0 → root; `FLAG_ACTIVITY_NEW_TASK|CLEAR_TASK` empties the stack so the cleared-task newcomer answers true). The old silent-stub answered false → TheXTech `Launcher.onCreate` `finish()`ed before `super.onCreate` — exactly the early exit your §A source read predicted.

**APK-level evidence on the pinned `ru.wohlsoft.thextech.fdroid` APK (same artifact as W16):**

| Face | W16 (pre-fix) | S220 (post-fix) |
| --- | --- | --- |
| unique colors | 1 | **754** |
| non-bg share | 0.0 | **99.9%** |
| activity_finish calls | (finished early) | **0** |
| `initUiSetup` | never | **ran (2 dispatches)** |
| first_missing_stage | WINDOW_ROOT | none recorded |

**OBSERVED:** the rendered frame is the launcher's OWN UI — sky background, TheXTech logo, **"Start game"** and **"Settings"** buttons (`evidence/s220/runs/s220_thextech_isTaskRoot/screenshot.png`, 1080×1920). This is your demanded case (1): "launcher with no game package, which should still show its own UI". Route advance: DESTROYED-before-content → **app-owned first screen**. Honest next blocker for case (2): input dispatch into the SDL route (0 tap/motion receipts on that route — the SDL/native surface does not consume View-route taps yet).

## 2. The EXP-086 false-PASS family — verifier regression LANDED (your comment 6806844276 demand)

`scripts/s220_frame_truth.py` — verdicts NOISE (png > 800 KB, the uninitialized-memory signature; the same root as the 1080×2400 full-res noise-push problem) / **IDENTICAL_ARTIFACT** (≥3 identical faces + zero ViewTree/draw/frame events → rejected — the exact EXP-086 Phase-4 shape, judged straight from the recorded evidence booleans of the historical JSON: all three gmdice/TicTacToe/Telegram rows now answer rejected) / DEFAULT_BACKGROUND_ONLY / FLAT_TWO_TONE_OR_BLANK / PASS_UI_EVIDENCED. Self-test **7/7**. The three identical 10,535-byte PNGs shape can never be labelled PASS again.

## 3. GP-DEX-003 — fuzz battery LANDED (queued item closed)

`tests/gp_dex003_fuzz_law_test.cpp` **11/11**: header-coherence rows (header_size 0x69, wrong endian tag, file_size beyond actual / below header), UINT32_MAX `string_ids_size` + near-max `string_ids_off` (the 64-bit count×item_size OOM-guard rejects BEFORE allocation), misaligned `type_ids` table, truncation faces (8/0x20/0x40/0x6F — every one answers `is_valid=false` + a recorded `validation_error`, never a clean parse), and a 512-input deterministic LCG header fuzz (no crash, no hang — ASan/UBSan-safe by construction of the no-crash contract). The pre-existing FIND-REUSE-005 section-table law is what the rows pin; the fuzz battery is the new net.

## 4. Dooz — state advance + the named next blocker (comments 6807083759/6807550504 §H)

- **Correction to the historical label:** the gold pin `a0fae907` IS the real launch UI (TopAppBar "Dooz" + settings/theme icons + BottomAppBar + "New game" FAB) — the "Compose white screen" label predates the current binary; the pinned face is the full initial chrome with the board correctly hidden per upstream law.
- **New Game tap evidence (this wave):** tap dispatches; **10 frame changes** after the tap (the composition is alive and animating); **uncaught 6 → 0**; the `La;` unwind family is fully handled by catch-alls (control-flow, not crashes).
- **Named next blocker (your §2.3 item):** the post-NewGame transition freezes mid-flight — elements half-slid, board never composes (LazyGrid=0 hits). The demanded proof chain (suspend getters → prepareGame → StateFlow emission → `dummyDiceRolling` 5×100ms delay/resumptions → AnimatedVisibility target=Visible) needs the **one deterministic event-time model**: delayed coroutine work must become due during the pump. That is the next wave's single root, with the exact instrumentation chain you specified.

## 5. Cross-issue reconciliation (same commit)

- **#584 A-R5 patch LANDED** (verdicts: R27 ACCEPTED+LANDED / R23+R24 ACCEPTED+LANDED / R25 MATERIALIZED 14/14; `r25_matrix` + `mwr_opcode_probe` now `make` targets; receipt posted there).
- **#583 IMG-004 V2** per the 2026-11-12 correction: `inJustDecodeBounds` read BEFORE any pixel decode, all four entry paths, bounds-only header law + 10/10 battery.
- **Regression:** `make test-all` **26/26** (24 required + r25 matrix + img004 bounds); `mwr_opcode_probe` **5/5**; `r25_matrix` **14/14**; **FULL 6-PIN GATE ALL HOLD byte-exact** (bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 identical / microtimer `b39665f6` 0-uncaught / ttt `7354c1b2` ×3 deterministic).

## 6. Queued ledger status (this issue's remaining items)

- GP-DEX-003 → **CLOSED** (fuzz battery; the structural laws were already landed, the net now exists).
- GP-DEX-001/002 → covered by the same landed table law + now fuzz-pinned (row-level re-verification available on request).
- GP-INT-005/008..011, GP-EXC-005..009 (incl. GP-EXC-008 TextWatcher), GP-APK-001/003/004/006 per-callsite, GP-JNI-004 fork-isolation, GP-MEM teardown free-loop → **still queued**; the dooz event-time model (§4) is scheduled as the next single-root wave ahead of them per the app-first priority.
- W21 (the #575 dependency): part 17 never arrived; S210 proved the symbol chain build-specific (`Lm7;.j` absent from the pinned corpus build) → **SUPERSEDED**; the lane is asked to re-anchor on the pinned corpus APK with the NEW evidence above.
"""

BODY_583 = """# GP — S220 wave receipt on this issue: IMG-004 V2 landed per the 2026-11-12 correction + the integration-chain diagnosis is working (TheXTech/dooz evidence)

**Commits:** `39b7ab69` + `05ef1e86` (pushed). Binary sha16 `9adf7d627bcbdac6`.

## 1. IMG-004 V2 — IMPLEMENTED / TESTED (your correction comment 6805997743, all five amendment points)

- **Point 1 honored:** NO decodeResource/decodeFile special-case — the bounds flag is read at the TOP of the shared `f240_decode_with_options` request path, so all FOUR entry paths inherit the contract.
- **Point 2/3 honored:** the bounds pass now runs the pure `bitmap_bounds_only_law` (header-only `probe_image_size` parser) BEFORE `decode_image_bytes` is reachable — **zero codec invocations, zero pixel allocation**, raw `outWidth/outHeight/outMimeType` from the header, null return.
- **Point 4 honored:** `ImageSizeProbe.header_dims_known` distinguishes header-dims-known from payload-fully-valid (documented in the struct contract); invalid/truncated headers answer fresh-Options `0x0` error dims (AOSP native leaves the out fields untouched on codec-creation failure — the caller's own `outWidth <= 0` check takes its documented path); malformed content is never labelled fully decoded.
- **Point 5 honored:** `tests/gp583_img004_bounds_law_test.cpp` **10/10** — valid PNG/JPEG header rows, a valid-header-with-zero-payload row (proving the no-decode contract), truncated-header, corrupt-signature, empty-stream, and a 29-byte VP8X window bounds check.

## 2. The §1 integration-chain diagnosis, validated by this wave's outcomes

Your central thesis ("apply-clean is not build-clean; text-only transfer is not an implementation; the chain breaks at lane boundaries") was exercised end-to-end this wave:

- **#584's A-R5 patch** (a lane delivery with apply-check + blob hashes) needed a real **re-base + build + gate battery** to land (the wave-2 Makefile had moved under it) — the hand-ported Makefile hunk + 26/26 battery + 6-pin gate is exactly the "patch → main-tree apply → complete build → executable test" chain your §1 demands, and it caught the divergence the lane could not see.
- **The W21 16/17 stranded diff** (your §1.3 example) is now formally **SUPERSEDED**: part 17 never arrived (nothing on #575 since the S216 request) AND the S210 symbol correction stands (`Lm7;.j` does not exist in the pinned `io.github.yamin8000.dooz_23` build). Assembling a stale 16-part diff against a proven-wrong symbol chain would have violated your §0 "exact APK path, package, version, SHA before a code patch is authorized" law. The lane is asked to re-anchor on the pinned corpus build.

## 3. App-visible progress through the shared chain (not lane metrics)

- **TheXTech** (pin `ru.wohlsoft.thextech.fdroid`): `Activity.isTaskRoot` implemented on the G08 task-record stack → the Launcher no longer `finish()`es before `super.onCreate` → **the launcher's own UI renders** (754 unique colors vs 1 pre-fix; logo + Start game/Settings buttons; `initUiSetup` ran). Pre-fix face was DESTROYED/`WINDOW_ROOT`/1-color. Route advance with zero app-specific code.
- **Dooz** (pin `io.github.yamin8000.dooz_23`): gold pin `a0fae907` re-identified as the REAL launch chrome (the stale "white screen" label corrected); New Game tap dispatches with 10 recomposition frames; uncaught 6 → 0. Next single root: the post-NewGame transition freeze = the deterministic event-time model (delayed coroutine work must become due during the pump) — the exact lever your §2.3 names, with dooz's 5×100ms dice delays as the discriminating test.
- **False-pass prevention:** the frame-truth verifier (`scripts/s220_frame_truth.py`, self-test 7/7) rejects the EXP-086 Phase-4 shape (≥3 identical faces + zero draw/frame/ViewTree events) and the >800KB noise face — the "visually meaningful intermediate ≠ final output" family now has a permanent negative net.

## 4. Regression + remaining open on this issue

- `make test-all` **26/26** (incl. the new img004 bounds law + the r25 dispatch matrix), `mwr_opcode_probe` **5/5**, `r25_matrix` **14/14**, **FULL 6-PIN GATE ALL HOLD byte-exact** (bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 / microtimer `b39665f6` / ttt `7354c1b2` ×3).
- Still open (unchanged, queued): **GP583-ARCH-002** (the two-heap reconciliation — the RuntimeGeneration/ObjectHandle design needs its own wave; not silently patched against the wrong heap), the wave-7 HEAP items, and the remaining per-callsite classification families. The event-time model wave is scheduled first per the app-first priority.
"""

post(582, BODY_582)
post(583, BODY_583)
