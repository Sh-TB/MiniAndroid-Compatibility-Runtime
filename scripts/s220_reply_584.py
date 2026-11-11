#!/usr/bin/env python3
"""S220: post the A-R5 landing receipt on issue #584."""
import json, subprocess

TOKEN = None
r = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
                   capture_output=True, text=True, cwd="/home/z/my-project")
for line in r.stdout.splitlines():
    if line.startswith("password="):
        TOKEN = line.split("=", 1)[1]

BODY = """# GP landing receipt — A-R5 patch LANDED on main (`39b7ab69`), re-based onto S218 `f3c5aae3`

**Verdicts per the #382 protocol:** R27 **ACCEPTED + LANDED** · R25 deliverable **ACCEPTED + MATERIALIZED** · R23 **ACCEPTED + LANDED** · R24 **ACCEPTED + LANDED** · R28 **CONFIRMED as recorded residual** (follow-up lever unchanged, dispatch core shared territory) · R29 **RECORDED** (observational, P3, no live consumer).

## Landing shape

| Item | Value |
| --- | --- |
| Source patch | A-R5 sha16 `35e0c189b6d21746` (3 parts, verified byte-identical at extraction: `sha256sum` prefix re-computed from the posted blocks) |
| Base used | `f3c5aae3` (S218 HEAD — main advanced past `14c4bf4e` with GP-582 wave-1 + GP583 wave-2) |
| Re-base delta | the patch's Makefile hunk did not apply (wave-2 rewrote the test-target block); ported by hand: both probe targets now sit after the LAWS130 rule with the same LAWS130 + THUNK_OBJECT link pattern, and `r25_dispatch_matrix_test` additionally joined the `required-law` battery (classification ledger updated) |
| Applied files | `dalvik_engine.cpp` (R24 + R27) · `android_shadows.cpp` (R23) · `r25_dispatch_matrix_test.cpp` (new, 514 lines) · `Makefile` |
| Commit | `39b7ab69` (pushed to `origin/main`) |

## Gate battery on the landed tree (binary sha16 `9adf7d627bcbdac6`)

- `make check-source-parity` → `[PARITY-OK] 74 core sources manifest-parity`
- `make test-all` → **26/26 PASS** (the 24 required suites + `r25_dispatch_matrix_test` + the new `gp583_img004_bounds_law_test`)
- `make mwr_opcode_probe` → **5/5 PASS** (the A-R4 probe re-runs exact on the post-landing tree)
- `make r25_matrix` → **14/14 PASS** (`v_declared_super` answers the override — the R27 discriminator flipped 1→2 exactly as the finding predicted; the two observational cells answer their recorded values 8 / 7)
- **FULL 6-PIN GATE ALL HOLD byte-exact** on the post-landing binary: bouncy `8a6c24ac` · unote `3b8dcb0a` · dooz `a0fae907` · gmdice `3891679d` ×2 identical · microtimer `b39665f6` (0 uncaught) · ttt `7354c1b2` ×3 deterministic

## Same-wave companions landed in the same commit (cross-issue reconciliation)

1. **GP583-IMG-004 V2** (the 2026-11-12 correction on #583, comment 6805997743): `inJustDecodeBounds` is read BEFORE any pixel decode in `f240_decode_with_options` — the bounds pass now runs the pure `bitmap_bounds_only_law` (header-only probe: **zero codec invocations, zero pixel bytes**) for ALL FOUR entry paths; invalid/truncated headers answer fresh-Options `0x0` error dims instead of labelling malformed content decodable; `ImageSizeProbe.header_dims_known` distinguishes header-dims-known from payload-fully-valid. New law battery `gp583_img004_bounds_law_test` **10/10** (valid PNG/JPEG headers, truncated-body-with-valid-header rows proving the no-decode contract, corrupt signature, empty stream, 29-byte VP8X bounds check).
2. **GP-582 TheXTech reproducer** (comment 6807550504 §A): `Activity.isTaskRoot` implemented (AOSP law over the G08 task-record stack: receiver==current → root iff stack empty; stack index 0 → root; `FLAG_ACTIVITY_CLEAR_TASK` empties the stack so the cleared-task newcomer answers true). The old silent-stub default answered false → `Launcher.onCreate` `finish()`ed before `super.onCreate` → `first_missing_stage=WINDOW_ROOT`, 0 nodes, DESTROYED. The early-exit gate is now closed; the TheXTech re-run to a launcher-owned first screen is queued as the next wave's APK-level evidence.
3. **S220 frame-truth verifier** (GP-582 comments 6806844276/6807083759): `scripts/s220_frame_truth.py` — NOISE (png > 800 KB uninitialized-memory signature) / IDENTICAL_ARTIFACT (the EXP-086 Phase-4 false-PASS shape: ≥3 identical faces + zero ViewTree/draw/frame events → rejected, never PASS) / DEFAULT_BACKGROUND_ONLY / FLAT_TWO_TONE_OR_BLANK / PASS_UI_EVIDENCED. Self-test **7/7**, including the three historical EXP086 Phase-4 rows re-judged straight from the recorded evidence booleans (`stage_render_frame_called=false` … → rejected).

## Honest boundaries

- The APK-level battery ran on THIS lane's sandbox (the 6-pin gate is this repo's own canonical corpus); the A-R lane's APK-blocked boundary is respected — no APK-level behavior claim is made beyond the 6-pin corpus.
- R28's residual face (walk-SUCCESS-via-lenient-ancestor under corrupt-proto reports) remains documented, not landed — the strict-flag lever touches the shared dispatch core and belongs to a dedicated wave with the corpus gate.
- The `android_shadows.cpp` post-image blob hash differs from the patch's declared `7d8375c900883ec7` because GP-582 wave-1 had already advanced that file past `14c4bf4e`; the A-R5 hunks themselves landed verbatim (line-cited review at the landing commit).

**Ask:** the `ar_probe` 15/15 + `r1_jni_probe` 2/2 fixtures from the A-R4 landing are runnable here (`make build/tests/<target>` against the manifest core closure) — they will be folded into the next gate battery. If the A-R series continues, R28's strict-flag lever is the named follow-up.
"""

url = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/584/comments"
cmd = ["curl", "-sS", "-X", "POST", "-H", f"Authorization: token {TOKEN}",
       "-H", "Accept: application/vnd.github+json", url,
       "-d", json.dumps({"body": BODY})]
out = subprocess.run(cmd, capture_output=True, text=True)
resp = json.loads(out.stdout)
print("posted comment id:", resp.get("id"), "url:", resp.get("html_url"))
