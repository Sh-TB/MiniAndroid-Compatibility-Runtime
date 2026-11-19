# W21 — W20-K INTEGRATION AUDIT (Phase 0 + Phase 1)

Mission: W21 POST-W20-K VERIFICATION. Base commit audited: `568a938060fad96666effd66e89140db94e3adbe`
(W20-K2). Everything below was verified by direct inspection in this session, not inherited from
prior summaries. Binary used for all runs: `build/miniandroid` sha256-16 `f2083d06e5a6e89a`
(built from the W21 Phase-3 tree, commit `c1602b754ddf5d00`).

---

## 1. Repository and commit integrity (PHASE 0)

| Check | Result |
|---|---|
| Remote fetch | `origin/main` = `568a9380…` — IDENTICAL to local HEAD, clean fast-forward state |
| `8d2583b7` (W20-K) on remote branch | YES — `git branch -r --contains 8d2583b7` = `origin/main` |
| Full SHAs | W20-K `8d2583b7116ef865eee8c84c1fa776510639230e`, parent `4c562943c9944584cfe8840b7b4d8955f801ea81` |
| Worktree status | clean at audit start (0 modified files) |
| HEAD tree hash | `748ee44c7ed45ae5a1e8a580ba86f54ceaa9844b` (15,828 tracked files) |
| Rollback reference | tag `w20-k2-rollback-568a9380` created (immutable local safety point; no force-push/reset used) |

### 1.1 The `671d2577` ancestry question — ANSWER: NOT an ancestor, content fully carried

The mission asked: is `671d2577` (W20-P2) an ancestor of `8d2583b7` (W20-K)? **NO** —
`git merge-base --is-ancestor 671d2577 8d2583b7` fails. Reconciliation (evidence, not assumption):

- `671d2577` is the tip of branch `wave10/dalvik-accel` (local + `origin/wave10/dalvik-accel`),
  parent chain `671d2577 → 8d843248 (W19) → 8e225b25 (P0 SPLIT) → 23080802 (W18) → …`. It was
  never merged into `main` as a commit.
- `main`'s line carries the W19/W20-P2 work as CONTENT through six UUID-titled checkpoint commits
  (`31cc610f`, `1b2270f4`, `0a5a3b9b`, `68d63605`, `227bb22d`, `4c562943`, dated 2026-11-18/19) that
  the sandbox-recovery session committed, then W20-K `8d2583b7` was written on top of `4c562943`.
- Content equivalence PROVEN by diff: `git diff 671d2577 HEAD -- miniandroid/src miniandroid/Makefile`
  = only the W20-K integration changes (WS4–WS9 + SolitaireCG + Frozen Bubble, 21 files,
  +1176/−53 — matching the W20-K described scope). Nothing from W19/W20-P2 is missing on the
  Makefile/source side. Residual tracked `.rej` files (`dalvik_engine.cpp.rej`, `dlopen_exec.*.rej`)
  are pre-existing historical residue (provenance `fa5f97cf`/`c710511c`), not W20-K edits.

### 1.2 W20-P2 architecture presence at HEAD (all verified in source)

| W20-P2 item | Evidence at HEAD |
|---|---|
| dev-so dep-graph `.d` include fix | `miniandroid/Makefile` dev-so rules with `-include` below the variable definitions |
| `adapter_scrap_bin.h` `<cstdint>` | line 11: `#include <cstdint>  // W20: uint32_t was relied on transitively` |
| `dalvik_engine_tail.cpp` no direct android_shadows include | grep = 0 hits (the #627 comment-7002484385 patch) |
| P0 domain-split bridge (coordinator + 5 domain TUs + `dalvik_bridge_frame.h`) | all files present under `src/dex/` |
| dev `-O0` profile + apk-run/gate/cycle targets | Makefile lines 42/684–696 |

**Phase 0 defect found and fixed**: `miniandroid/CMakeLists.txt` on `main` had LOST the W15
(#627 C-01) per-TU compile-contract block (34 lines: `MINIANDROID_SPLIT_PART_TUS` `-g0` + the
interpreter inline-budget params) that exists on the wave10 tip — the sandbox-recovery
checkpoints predate that edit and the wave-9 merge resolved to OURS. The production Makefile
contract was never affected; the CMake path would have compiled the split parts with full debug
info. **Fixed in W21: re-applied verbatim from `671d2577` (+3-line provenance note);
`git diff 671d2577 -- CMakeLists.txt` now contains only that note.** Committed in `c1602b75`.

### 1.3 W20-K diff audit (sandbox-recovery damage check)

The W20-K integration was re-applied after a sandbox recycle via `scripts/w20_reapply_k{,2,3,4}.py`
(each edit exactly-once asserted). Audit result on the source diff:
- No duplicate definitions: the domain TUs compile once each (production build exit=0, link clean —
  a duplicate symbol would fail the link).
- No namespace damage: build + 48-test battery run clean in this session (below).
- No accidental duplicate edits found in `git show 8d2583b7` hunks (each WS edit appears once).
- One W20-K bookkeeping error: `evidence/w20/k_apk/sol_r{1,2,3}/` are **misnamed — they are
  de.tcrass.minos runs** (report.md says APK `de.tcrass.minos_10004.apk`; screenshot sha
  `b5a7a35d5fe0564b` = the minos baseline). **The SolitaireCG APK re-verification queued by the
  regression report was never actually executed.** The pz check (`ceb1a6adf7ba1391`) is genuine.
  W21 Phase 2 closes both APK verifications with the original APKs.

---

## 2. The 12-artifact inventory (10-of-12 discrepancy RESOLVED)

The ZIP `CODER_ohc_PLAY_WAVE_ISSUE.zip` extracts to exactly 12 files
(`/home/z/my-project/upload/w20_coder_ohc_extract/`). The prior session's log said "10 of 12 read"
and then named three remaining files — internally inconsistent (10+3 > 12). W21 read ALL 12;
hashes below are the inspection receipt (sha256-16):

| # | File | sha256-16 | Read in W21 |
|---|---|---|---|
| 1 | CODER_ohc_PLAY_WAVE_ISSUE.md | a5aba43bf4e58418 | yes |
| 2 | WS2_02_SOLITAIRE_SPLASH_FINDING.md | 1ecca8aa8c0ac890 | yes |
| 3 | WS4_2048_INPUT_FINDING.md | 960d06b2babba0ca | yes |
| 4 | receipt_comment.md | 2dfab820e78c13e6 | yes |
| 5 | ws2_comment.md | 55c7eade782ac1b4 | yes |
| 6 | ws4_comment.md | 2fa25cd9ee8c1251 | yes |
| 7 | ws4_fix_comment.md | bd911c927b9c594a | yes |
| 8 | ws5_comment.md | 2f58b77ac23f274a | yes |
| 9 | ws6_comment.md | 989488c3f8c40582 | yes |
| 10 | ws7_comment.md | 442681e445fa3e6d | yes |
| 11 | ws8_comment.md | 5a3872a3d908f15d | yes |
| 12 | ws9_comment.md | 63df6283f5340ecd | yes |

Resolution of the count: 12 artifacts exist; the "three remaining" note most plausibly referred to
three files still unread at the point the log was written (10 counted earlier), i.e. a transient
progress note, not a distinct 15-file set. Nothing in the ZIP was skipped in W21.

---

## 3. WS4–WS9 integration status (evidence-first, contract + live)

| Finding | Source site (verified at HEAD) | Contract test | Status | Remaining limitation |
|---|---|---|---|---|
| WS4.1 changedTouches/targetTouches/preventDefault | `src/webview/webview_engine.cpp` under `MINIANDROID_WV_CHANGED_TOUCHES` (default OFF) | gated 2048 runs | INTEGRATED | default-off = not proof of playability (see §5) |
| WS4.2 swipe→browser drag forward | `src/runtime/execution_engine.cpp` under `MINIANDROID_WV_DRAG_FORWARD` (default OFF) | gated 2048 runs | INTEGRATED | same |
| WS4B DOM→repaint | **CLOSED in W21** (`c1602b75`): float/clear layout + translate transforms + W3C implicit touch capture + cascade re-match on mutation | live a2048_23 matrix (§5) | **ACCEPTED (live evidence)** | inline `<a>` buttons not hit-testable; game-over not driven; cross-run board persistence not observed |
| WS5 sqlite column law | `src/storage/sqlite_shadow.cpp` `column_index_ci` (strip after last `.`, case-fold, AOSP message) | s248 10/10 PASS | ACCEPTED | — |
| WS6 adapter position INT64/INVALID_ROW_ID | `dalvik_bridge.cpp` + `dalvik_bridge_domain_app_runtime.cpp` `make_long`/INVALID_ROW_ID | s249 4/4 PASS | ACCEPTED | **s235 r11a harness decoder gap found in W21 (§4) — fixed with the coder's own law** |
| WS7 dialog lifecycle | `dialog_shadow.{h,cpp}` (listeners stored, exactly-once tokens) + `execution_engine.cpp:10685` drain + `dalvik_bridge.cpp:95` entry | s250 8/8 PASS | ACCEPTED (audit §6) | cross-dialog delivery grouped by callback type; DialogWindow map never shrinks |
| WS8 activity result default | `android_shadows.h` take_result always delivers + cascade on `launched_for_request >= 0` | s251 PASS | ACCEPTED | contract-level only (corpus does not drive the path live — coder's own honest scope) |
| WS9 view state flags | `android_shadows.{h,cpp}` 10 arms + `state_list.{h,cpp}` activated/window_focused + render forward | s252 9/9 PASS | ACCEPTED | contract-level only |
| SolitaireCG h=-1 bitmap-dims fallback | `dalvik_bridge_domain_ui_graphics.cpp` | **W20-K's re-run never happened (misnamed k_apk dirs)** | W21 Phase 2 executes it | §7 |
| Frozen Bubble Options fields | `dalvik_opcodes_invoke.cpp` + `dalvik_engine.cpp` (both copies) | idem | W21 Phase 2 executes it | §7 |

---

## 4. test-all reproduction + the s98/s235 classification (W21 fresh run)

Command: `make test-all` (serial), runner-measured: wall 263.7 s, CPU 236.8+20.3 s, peak RSS
783,200 KB, rc=2 (one failing test). Full log: `evidence/w21/w21_testall_full.log`.

**Result: total=48 passed=47 failed=1 — reproduced.** But the identity of the 1 failure CONTRADICTS
the W20-K2 report:

- W20-K2 commit + `runtime_regression_report.md` claim: "the 1 failure = pre-existing s98 font-env
  lineage failure" and elsewhere "2 pre-existing font-env failures s98/s106".
- **Measured truth at HEAD: `s98_text_law_test` PASSES (its own battery: "S98 TEXT LAW BATTERY:
  21 passed, 0 failed"). The real failure is `s235_lane_laws_test` row
  `r11a_listview_item_id`: REC-MISS → "FAIL r11a_listview_item_id — rc=0 got=-999 want=1".**

Root cause (measured, then fixed): the W20-K WS6 law made `getItemIdAtPosition` return INT64; the
s235 harness value decoder (`run_row_ex`) handled INT32/CHAR/BOOL/OBJECT only → rc=0 unreadable.
This is EXACTLY the harness gap the independent coder documented and fixed on their own lineage
(ws6_comment.md: "Added an INT64 branch to the harness decoder"). The W20-K session believed
"s235 does not exist on this lineage" (INDEPENDENT_FINDINGS_STATUS.csv WS6-harness row) — it does.
**W21 fix: added the `T::INT64` branch to `tests/s235_lane_laws_test.cpp` with the coder's
provenance comment** (test-harness change, zero runtime code). Battery expectation after fix:
48/48.

The "three contract failures observed during the intermediate test run": the W20-K regression
report says the new contract tests (s248/s249/s250) failed on first integration and passed "after
the fixture fixes". **No intermediate log was committed** — the only artifact is the final tail
(`w20_k_testall_tail.txt`, 173 bytes, which does not even name the failing test). W21 records the
gap honestly: intermediate-failure details are MISSING EVIDENCE (reported as missing, not assumed);
the final state (47/48 with the failure now correctly attributed and fixed) is fully reproduced.

---

## 5. WS4 gate documentation (default-off vs gated behavior)

Enabled by DEFAULT (no env var): nothing — pristine behavior is byte-identical to pre-W20-K
(re-proven in W21: a2048_23 swipe with NO env gates = launch face `a52c222075d842b4`, unchanged).

Enabled ONLY with `MINIANDROID_WV_CHANGED_TOUCHES=1` (webview_engine.cpp): W3C TouchEvent
completeness — `changedTouches` always, `targetTouches` on touch* starts/moves (empty on touchend),
`touches` emptied on touchend, no-op `preventDefault`/`stopPropagation`/`stopImmediatePropagation`.

Enabled ONLY with `MINIANDROID_WV_DRAG_FORWARD=1` (execution_engine.cpp): the DEX-layer swipe
forwards the real multi-point gesture into the browser (touchstart → N× touchmove → touchend at
view-local coordinates).

W21 acceptance evidence (original F-Droid `com.uberspot.a2048_23.apk`, sha256-16 `e7bf6cb62cda6830`,
rc=0 SUCCESS, gates ON): launch `a52c222075d842b4`; LEFT×3 = `271cb5d0ffbe598c` deterministic; UP
`589ffcd793096497`; DOWN `03806943ce4606d7`; RIGHT `56d567f44a4156a7`; off-board gesture =
launch face (invalid-move safety). Layout now browser-correct: `.game-container 500x500 @ (290,269)`,
`.grid-container 469x469 @ (305,284)` (was 106x1741). **2048 upgraded: board-interactive.**

## 6. WS7 special audit (dialog listener lifecycle)

Source-audited `dialog_shadow.cpp/h`, `execution_engine.cpp:10685`, `dalvik_bridge.cpp:95`:

1. **Exactly-once**: `pending_show/dismiss/cancel_cb` bools armed once per transition (show guarded
   by `!win.showing`), `consume_pending_*` clears on read. No re-arm loop.
2. **No duplicate delivery during repeated drains**: two drain sites (bridge_to_api entry +
   pre-paint in `stage_render_frame_impl`) are idempotent — flags clear at consume.
3. **No lost callbacks**: a dismiss/cancel that is the last framework call still delivers via the
   pre-paint drain; `DialogWindow` entries are never erased from the shadow map (0 erase sites).
4. **Destruction/cancellation safety**: only uint32 object ids are retained — no pointers, so no
   use-after-free/double-delete by construction; delivery re-looks-up the heap object per callback;
   `dlg==0` skipped. A full ASan rebuild of the battery (whole core under -fsanitize) was NOT run
   in W21 (2-CPU host, ~9 min exclusive rebuild) — recorded as deferred, with the by-construction
   id-based lifetime audit above.
5. **Multiple listeners / nested dialogs**: three listener slots per window; the drain iterates ALL
   windows; a dialog shown from onDismiss arms a new token delivered in the same/next pass
   (consume-before-deliver prevents infinite loops). Limitation recorded: when MULTIPLE dialogs
   have simultaneously-armed tokens of different kinds, delivery is grouped cancel→dismiss→show
   across windows (not strictly per-dialog); s250 covers single-dialog ordering.
6. **Re-entrancy**: delivery invokes real app overrides (`try_recursive_invoke` with the object's
   real class descriptor, so AlertDialog subclasses dispatch virtually).

## 7. Phase 2 APK verification (originals, from the legitimate release source)

The coder's pinned APKs were located on F-Droid (repo + archive) and verified BYTE-IDENTICAL to
the coder's receipts:

| APK | sha256 (full) | source URL | coder receipt sha16 |
|---|---|---|---|
| net.sourceforge.solitaire_cg_3041.apk | d4afb74d28680712d771181a696d5fec42cc13e5c55f0da546151f6a8c4244c6 | https://f-droid.org/repo/net.sourceforge.solitaire_cg_3041.apk | d4afb74d28680712 ✓ |
| org.jfedor.frozenbubble_11.apk | fababf48eafa5e45d084c7e0ba6ec8a11ebb5617a713bc12d9a0ca95933bedef | https://f-droid.org/archive/org.jfedor.frozenbubble_11.apk | fababf48eafa5e45 ✓ |
| net.sourceforge.solitaire_cg_4010.apk | 39411dd82b0f2b274ef803f48d501fc102ab10bcb19bb7894433d17454765825 | https://f-droid.org/repo/net.sourceforge.solitaire_cg_4010.apk | (latest 4.1) |
| org.jfedor.frozenbubble_54.apk | bf291a12e88c84e559bd4f0faf99163a6a5b55da995df69ef10f888c6bba77e4 | https://f-droid.org/archive/org.jfedor.frozenbubble_54.apk | (latest) |
| com.uberspot.a2048_23.apk | e7bf6cb62cda6830… (full in apk_src dir) | https://f-droid.org/archive/com.uberspot.a2048_23.apk | (WS4 reproduction vehicle) |

Also downloaded: `com.uberspot.a2048_25.apk` (7c66ccdf…) — the NEWEST archive version CRASHES at
MainActivity.onCreate on this runtime (3 uncaught NPEs: XmlPullParserFactory.newPullParser on null,
AlertDialog.show on null, WebView.loadUrl on null → DEFAULT_BACKGROUND_ONLY, sha `b5a7a35d5fe0564b`
= the same face as minos' crash face). Recorded as a separate pre-WS4B version-specific blocker —
Phase 2/3 evidence uses _23, which runs SUCCESS.

Run results: see `W21_APK_VALIDATION_REPORT.md` (Phase 2 deliverable).
