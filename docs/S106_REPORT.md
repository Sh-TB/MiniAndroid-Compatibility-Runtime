# S106 REPORT — 51 EVIDENCED ISSUE CLOSURES + 5 REAL ENGINE FIXES

Head at close: `7a0a8dab`. All output text English (user directive).
User directive honored: (1) push all pending work; (2) close >=50 open
GitHub issues WITH evidence ("نه اینکه همینطوری" — not superficially);
(3) report the real game-execution impact of every change.

---

## 1. CLOSURE LEDGER (299 → 248 open; 51 closed, every one with evidence)

| Batch | Tickets | Evidence standard |
|-------|---------|-------------------|
| Root tickets (fresh HEAD runs) | #352, #349, #350, #347 | 3-run semantic invariants + per-root commit SHAs + F-Droid re-fetch SHA |
| GIF family | #263, #264, #265 | pixel-level disposal laws G1–G3 on real GIF89a containers |
| Vector/drawable/state-list/mipmap/adaptive | #291–#310, #313, #267, #268 (19) | aapt2-built fixture, binary AXML, raster assertions |
| Text/font | #269, #270, #273, #274, #275–#277, #279, #280, #285–#287 (12) | real TextShaper/layout_text metrics |
| Canvas/filter | #314, #315–#318 (5) | affine composition + nearest-sampling laws |
| Input | #319, #321 (2) | TouchDispatcher + handler drain |
| Audio | #331, #332, #333 (3) | state machines + real RIFF/WAVE decode |
| Layout/net | #242, #289, #266 (3) | traversal flag + live local HTTP server |

Every closing comment names: the exact checkpoint, the battery stage, the
commit SHA, the upstream law, and (where applicable) the fix found. Registry
synced: `docs/MICRO_GAP_REGISTRY.json` CLOSED 32 → 79 (PARTIAL 70 → 27).

---

## 2. REAL APK IMPACT (user's primary metric)

Fresh runs at the close HEAD, 3× each, deterministic invariants:

```
io.github.yamin8000.dooz_23:        6 errors x3 (unchanged from S105 best;
  + dooz_23_toplevel:                exception-set hash d5c33116c62eff1d x3;
                                     screenshot SHA 59fdbfcd60b86a23 x3)
de.georgsieber.ballbreak:           SUCCESS, 0 errors x3 (SHA fe797c19...)
com.vayunmathur.games.solitaire:    0 errors x3 (vc 20260804 re-fetched,
                                     SHA e8753685... matches FIX-005 record)
io.github.hathibelagal.mykanji:     SUCCESS rc=0 x3; decor-toolbar ISE
                                     family GONE (0 occurrences; the
                                     remaining rows are one handled NPE)
com.helddertiewelt.mentalmath:      32 errors x3 — Hilt ISE STILL PRESENT;
                                     ticket #351 honestly stays open
```

**Zero regressions from this wave's 5 engine fixes**: the fixes changed only
law-violating behavior no corpus title exercised visibly (none of the
affected titles draw through a rotated canvas, use stroke-only vectors, hit
the maxLines cap edge, or rely on requestLayout-triggered re-measure today —
each becomes a load-bearing capability the moment an app uses it).

---

## 3. THE 5 REAL ENGINE BUGS THE FENCES FOUND (root → law → fix)

1. **Stroke-only vector paths drew NOTHING** (`vector_decode.cpp`): the
   rasterizer `if (!pd.has_fill) continue;` skipped the stroke block —
   violating AOSP VectorDrawable fill/stroke independence. Every
   stroke-only icon in every app was silently invisible.
2. **Canvas rotation turned the WRONG WAY** (`canvas_shadow.h` Affine2D):
   `pre_rotate` composed M·Rᵀ (counter-clockwise) while the documented law
   — Android/Skia — is clockwise in y-down. No test had pinned the
   direction since S68; the fence did.
3. **maxLines off-by-one** (`text_shaper.cpp layout_text`): a capped block
   emitted one extra EMPTY line (lines.size() == maxLines+1), violating
   StaticLayout's lines.size() <= maxLines.
4. **`View.requestLayout()` was a silent no-op** (`android_shadows.cpp`):
   the bridge answered handled-void without raising the R-NEW-302
   `layout_dirty` traversal flag — DEX-driven requestLayout never
   re-measured. Fixed + the invalidate law documented (redraw-only).
5. **Missing capabilities implemented**: group `android:alpha` inheritance
   (multiplicative through the group chain), `state_checked` in the
   state-list API (AOSP Checkable family), and the audio module wired into
   the canonical build (audio_engine.cpp existed but was never compiled).

Plus TWO UPSTREAM stb_image bugs fixed in the vendored copy (GIF work):
- dispose-2 restored the pre-frame canvas instead of the background
  (now spec-true transparent black per GIF89a/Skia);
- `two_back` cached a pointer across realloc — an OOB heap read on EVERY
  disposal-3 GIF (upstream master still has it); replaced with a
  realloc-safe per-GIF snapshot.

---

## 4. NEW ENGINE CAPABILITY (beyond the tickets)

**Real animated-GIF decode** (`GifDecoder`, `gif_decoder.{h,cpp}`): the
S68-era "GIF format not supported (no decoder wired)" branch is replaced by
a full GIF89a LZW + GCE decoder with disposal semantics, wired through the
ONE format-detecting decoder (§13 named-error law preserved for corrupt
containers — proven by the G6 checkpoints). 17/17 law checkpoints PASS,
including frame counts, per-frame delays (10 cs → 100 ms), and the three
disposal classes from decoded pixels.

---

## 5. GATES

```
battery:      BATTERY GATE ALL PASS (rc=0) — 105 canonical + 5 new s106
              stages (gif 17, drawables 39, text2 14, canvas/input/audio 21,
              layout/net 11) = 102 new checkpoints
fixtures:     EXT-01/02 re-fetched after container reset, SHA-pinned
              (APK 009b4671…, reference 121d479c… — both match the record)
toolchain:    aapt2 8.13.2 / ECJ 3.33 / r8 8.13.23 (s106_drawables fixture
              compiled+linked with the real toolchain)
regression:   post-fix x3 runs — see §2; zero regressions
```

## 6. HONEST REMAINERS (not closed, with reasons)

- #351 (mentalmath Hilt ISE): re-verified still failing at this head.
- MG-024/025 (NinePatch), MG-060 (letterSpacing), MG-076 (textColor alpha
  render-side), MG-077/078/079 (spans), MG-072 (tab stops), MG-150
  (translated hit testing), MG-147 (multi-pointer — dispatcher is an
  honest single-pointer model), MG-116 (per-view redraw flag), MG-169/170
  (Bundle process-restart fence), MG-228/229 (frame-order/detection
  fences), MG-298/299/310 (system/edge fences): PARTIAL/OBSERVED/PENDING —
  each needs its implementation or process-restart fixture first; closing
  them now would be the superficial kind the user forbade.
- New frontiers recorded from fresh traces: mykanji's one handled
  XmlPullParser.getEventType null NPE; solitaire's compose chain now
  reaching `Recomposer.composeInitial$runtime → processCompositionError`.
