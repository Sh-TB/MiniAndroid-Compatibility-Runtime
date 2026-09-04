# Light open-source corpus — real-execution proof

Every image in this directory is a direct MiniAndroid framebuffer PNG
capture. Nothing is composited, retouched, or externally re-rendered. The
only post-runtime step is arranging the already-captured frames into strips
(`miniandroid/scripts/make_light_corpus_sheets.py` copies pixels 1:1 and
draws captions beside the frames).

## What is proven

| App | Source | Size | Launch | Real text | Interaction state changes | Deterministic replay |
|-----|--------|------|--------|-----------|---------------------------|----------------------|
| simplestopwatch | F-Droid omegacentauri.mobi.simplestopwatch | 172 KB | exit 0 | YES (Start/Reset/.0 labels) | 3 (Start→Stop/Lap→Continue/Reset→Start/Delay) | YES |
| gmdice | F-Droid de.duenndns.gmdice (MIT) | 64 KB | exit 0 | YES | 3 (roll/menu state) | YES |
| unote | F-Droid app.varlorg.unote (GPL) | 163 KB | exit 0 | YES (checkbox labels) | 1 (Add-note handler fired) | YES |
| chessclock | F-Droid com.chessclock.android | 124 KB | exit 0 | YES (per-panel time text) | 2 | YES |
| microtimer | F-Droid dubrowgn.microtimer | 209 KB | exit 0 | YES | renders (no listener fire at launch state) | YES |
| bgclock | F-Droid nl.hansdezwart.bgclock | 1.0 MB | exit 0 | background only (clock face is a WebView — capability gap) | no | YES |
| headingcalculator | F-Droid org.debian.eugen.headingcalculator | 65 KB | exit 0 | custom-view surfaces pending onDraw chain | no | YES |
| tinymusicplayer | F-Droid com.martinmimigames.tinymusicplayer | 17 KB | exit 0 | pending | no | YES |
| stopwatch (muellerma) | F-Droid com.github.muellerma.stopwatch | 738 KB | exit 1 (pre-existing partial) | — | no | YES |
| simplekeyboard | F-Droid rkr.simplekeyboard.inputmethod | 662 KB | exit 0 | pending | no | YES |
| notes (billthefarmer) | F-Droid org.billthefarmer.notes | 217 KB | exit 0 | pending | no | YES |
| tictactoe (emmanuelmess) | F-Droid com.emmanuelmess.tictactoe | 4.5 MB | exit 0 | blank (Compose — known blocked class) | no | YES |

APK SHA-256 values for every app are pinned in `EVIDENCE.json`
(`apps.<name>.apk_sha256`) and were verified at download time by
`scripts/download_test_apks.py` against the F-Droid registry.

## Proof chains (runtime-produced)

- `simplestopwatch_click_sequence.png` — 7 frames: launch →
  `onButtonStart` click → the app's OWN DEX handler swaps the toolbar to
  Stop/Lap (36,595 px change) → pause → Continue/Reset → Start/Delay.
- `gmdice_click_sequence.png` — 7 frames: roll/menu state transitions,
  background color state flips, menu item sets grow (7→14→20 visible
  strings), all driven by dispatched clicks on real DEX listeners.
- `unote_click_sequence.png` — 7 frames: Add-note handler dispatch (the
  XML `android:onClick` path resolves the method on the hosting Activity,
  exactly per AOSP).
- `chessclock_click_sequence.png` — 7 frames: per-panel state transitions.

## Reproduce

```bash
export MINIANDROID_APK_CACHE=/path/to/apk_cache   # APKs stay external
make -C miniandroid
bash miniandroid/scripts/run_light_corpus_evidence.sh          # 2x click runs per app
python3 miniandroid/scripts/analyze_light_corpus.py \
    miniandroid/run/light_corpus/evidence/*/runA               # pixel evidence
python3 miniandroid/scripts/build_light_corpus_evidence.py     # EVIDENCE.json/md
python3 miniandroid/scripts/make_light_corpus_sheets.py        # these sheets
```

Determinism law: run A and run B dispatch identical clicks; their frame
SHA-256 sequences are byte-identical (`deterministic_replay: true` per app
in `EVIDENCE.json`).

## Runtime fixes this session (all generic, no app special-casing)

1. **Real text pipeline integrated** — `src/fonts/text_shaper.*`
   (FriBidi → HarfBuzz → FreeType) was orphaned out of the build; the
   8x16 BitmapFont answered all text geometry. Now compiled in, and a
   shared `fonts::layout_text()` (word wrap, real advances, real line
   height) drives BOTH measure and draw — measured geometry and painted
   pixels cannot disagree.
2. **AOSP MeasureSpec measure pass** — EXACTLY/AT_MOST/UNSPECIFIED mode
   propagation (ViewGroup.getChildMeasureSpec), LinearLayout weights,
   real text desired size, ScrollView UNSPECIFIED child law, and a
   render-time re-measure (AOSP relayout-after-invalidation) so
   runtime-populated views (setText after setContentView) get real
   geometry instead of the 0x0 they measured before their text existed.
3. **RelativeLayout dependency rules** — layout_below/above/toRightOf/
   toLeftOf/alignParent* parsed from AXML (compiled id references resolved
   through resources.arsc id→name) and applied with a fixed-point pass.
4. **App font assets** — any `assets/**/*.ttf|otf` in an APK registers as
   the app font family (AOSP Typeface.createFromAsset equivalence);
   FACE_APP resolution falls back to the system chain when absent.
5. **Canvas.drawPath** — real path recording (moveTo/lineTo/quadTo/close)
   + even-odd scanline fill so apps that draw their own glyphs execute
   their real onDraw bytecode into real pixels.
6. **XML android:onClick drive** — the click-sequence proof path now
   dispatches XML handler methods on the hosting Activity (real `this`),
   not just DEX-registered listeners.

## Honest remaining gaps (documented, not hidden)

- simplestopwatch's big digits: `BigTextView` (custom view) needs the
  `setText(String[])/lines → onDraw` DEX chain; the surface shows an
  honest labeled placeholder meanwhile.
- bgclock's clock face is a WebView surface — WebView is a documented
  capability gap.
- stopwatch-muellerma exits 1 (pre-existing partial execution; unchanged
  from the prior baseline run).
- tictactoe renders blank (Compose rendering — known blocked class,
  pre-existing).
- RelativeLayout multi-anchor cases (view 11 in uNote overlapping the
  toolbar) need the full AOSP anchor solver; the common below/above/
  alignParent subset works.
