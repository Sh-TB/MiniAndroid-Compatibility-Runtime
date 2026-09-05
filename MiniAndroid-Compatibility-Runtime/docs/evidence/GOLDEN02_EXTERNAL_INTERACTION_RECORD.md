# GOLDEN-02 — EXTERNAL INTERACTIVE VISUAL — LONG-PRESS → CALLBACK → TOAST

Campaign: MASTER VISUAL COMPATIBILITY CAMPAIGN · Date: 2026-09-06
Fixture: `EXT-01-HELLOWORLDSELFAWARE-1.1.0` (frozen, SHA-256
`009b4671…cc41` — same APK as GOLDEN-01, no substitution).
Head: this record committed with the interaction implementation (see C6).

## A. Interaction chain (proven from APK bytes, scripts/dump_apk_interaction.py)

```
Lcom/appliberated/helloworldselfaware/MainActivity;
  implements Landroid/view/View$OnLongClickListener;      (type_list @0xa6c)
onCreate:  invoke-virtual TextView.setOnLongClickListener(this)
onLongClick(View)Z:                                        (code @0x7bc)
  Utils.copyText(this, getString(copy_label), text.getText())
    → Build.VERSION.SDK_INT (34) modern branch
    → ClipData.newPlainText(label, text)   [outline m @0x96c]
    → ClipboardManager.setPrimaryClip      [outline m @0x9a0]
  Toast.makeText(getApplicationContext(), toast_copied, LENGTH_LONG).show()
  return true                                              (const/4 v1,0x1 @[21]; return v1 @[29])
```

Oracle: `scripts/dump_apk_interaction.py` — 7/7 chain links PASS,
independent of the runtime parser.

## B. Event path (this HEAD)

```
--long-press 540,960
  → ACTION_DOWN: hit test over ViewShadow tree (AOSP touch law:
    CLICKABLE or LONG_CLICKABLE, deepest visible view wins)
    → target view 4 (Landroid/widget/TextView;, full-screen, bounds 0,0 1080x1920)
  → 500ms ViewConfiguration.getLongPressTimeout law (recorded, deterministic)
  → performLongClick → dalvik_engine.dispatch_long_click(4):
      real listener object (heap id 3, class MainActivity)
      → try_recursive_invoke("onLongClick", args=(listener, view))
      → [CLIPBOARD] ClipData.newPlainText obj=9 label="hello world" text=…
      → [CLIPBOARD] setPrimaryClip clip=9  ← REAL STATE MUTATION
      → [TOAST] makeText obj=10 resid=2131034115 + show()
      → onLongClick return type=1 val=1 → consumed=true
  → ACTION_UP: click SUPPRESSED (AOSP mHasPerformedLongPress law)
  → re-render: toast window painted by DialogShadow → frame_001.png
```

## C. Rule-10 quantitative validation (scripts/compare_ext01_interaction.py,
`interaction/interaction_golden.json` committed; NEVER a single number)

| Quantity | Value |
|---|---|
| frame size | 1080×1920 (both) |
| background (modal) | rgb(0,0,0) both |
| changed pixels | 12,488 |
| changed bbox | (428,1768)–(650,1823) = 222×55 px |
| toast band | y ≥ 1440 (bottom quarter) ✓ inside |
| centering | bbox center x=539 vs 540 → centered ✓ |
| text block above band | pixel-identical ✓ |
| hello message text | unchanged ✓ |

Verdict: **PASS (12/12 static checks)** — dimensions, background, changed
pixels exist, bottom-band confinement, centering, text-block unchanged,
dispatched, consumed, click-suppressed, press on-screen, target is
TextView, hello text unchanged.

## D. Determinism (Rule 12)

3 independent runs (runA, detB, detC) `--long-press 540,960`:

| run | target | dispatched | consumed | suppressed | diff_px | frame_001 SHA |
|---|---|---|---|---|---|---|
| runA | 4 | true | true | true | 12488 | `e242ac1e…d7a0` |
| detB | 4 | true | true | true | 12488 | `e242ac1e…d7a0` |
| detC | 4 | true | true | true | 12488 | `e242ac1e…d7a0` |

frame_000 and frame_001 byte-identical across all 3 runs (unique SHA count
= 1 each). Dynamic values (ANDROID_ID text) excluded from comparison by
design; static geometry fully checked.

## E. Generic platform behavior added (no fixture-specific code)

1. `dispatch_long_click(view_id, consumed&)` — AOSP View.performLongClick
   law; real registered listener object; listener's boolean return is the
   consumed value (BOOLEAN or raw INT32 accepted — untyped Dalvik cells).
2. Long-press gesture driver `stage_long_press` + `--long-press <x>,<y>`:
   hit test → 500ms law → dispatch → UP suppression per
   mHasPerformedLongPress.
3. Hit-test touchability extended: LONG_CLICKABLE views are touch targets
   (AOSP View.isTouchable); view with ONLY a long-click listener is
   hittable (the EXT-01 pattern).
4. ClipboardShadow (new): ClipData.newPlainText, ClipboardManager
   .setPrimaryClip/getPrimaryClip/getText, legacy
   android.text.ClipboardManager.setText — registered on BOTH engine
   registries (main.cpp + ApplicationRuntime).
5. Toast rendering (pre-existing DialogShadow law) paints the transient
   window into the SAME framebuffer render pipeline.

## F. Claim discipline

- `runtime-proven (interaction)`: the external APK's own listener, its own
  onLongClick bytecode, the platform clipboard state mutation, and the
  platform-rendered toast window are exercised through MiniAndroid's real
  event path with deterministic reproduction.
- NOT claimed: pixel-identity of toast typography to a device reference
  (no trusted long-press reference screenshot exists for this fixture;
  toast uses the runtime's bitmap font — recorded residual, not tuned).
- NOT claimed: ACTION_MOVE cancellation semantics (out-of-bounds cancel)
  — single-point gesture driver; queued for a later input gate.
