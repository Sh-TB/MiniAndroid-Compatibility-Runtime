# S76 WAVE REPORT — the queued leads EXECUTED: dooz producer trace → two root fixes, gmdice roll made visible, snake Dialog restart exercised, icon decode capability

Generated: 2026-09-21 · Local HEAD at wave start: b326acfd (5 commits ahead of
origin/main c67230be — the S75 publish debt, still tokenless this session).

## 0. Mandate

User directive: "continue" — execute every queued item. The S75
report §"Next" listed five leads; this wave executed the four actionable
ones (the fifth — GH_TOKEN issue comments — stays publish-debt, §6):

1. dooz F-146 upstream producer trace (coroutine path)
2. gmdice ListView roll-render path
3. snake Dialog-restart hypothesis
4. icon bitmap decode capability

## 1. Lead 1 — dooz F-146 ROOT-CAUSED and FIXED (R-NEW-390 + R-NEW-391)

The producer trace (scripts/s76_g8_disasm.py, full disasm of Lg8;.a — 926
units, all 475 instruction slots decoded with resolved refs):

- F-146 site pc=569: `invoke-virtual v4, Ljava/lang/Object;->getClass()`
  (the runtime diag's receiver register is v4; the def is pc=568
  `move-result-object v4` ← pc=565 `File.getAbsoluteFile()`).
- The chain: the DataStore file-name lambda reads its suspended result,
  casts to File, does `getName()` (R-NEW-347, S42), slices the extension,
  matches "preferences_pb", then calls **getAbsoluteFile()** and
  `getClass()` on the result.
- ROOT: `java.io.File.getAbsoluteFile()` (the File-RETURNING variant) had
  NO implementation — R-NEW-347 covered only the String variant
  `getAbsolutePath` → the invoke answered null → getClass on null → the
  F-146 NPE escape that killed the composition.

Fixes (law-cited, minimal):
- **R-NEW-390** `getAbsoluteFile()`: fresh File heap object with the
  absolute path (OpenJDK law: `new File(fs.resolve(f.getPath()))`, never
  null) — dalvik_engine.cpp R-NEW-347 block.
- **R-NEW-391** `getCanonicalFile()/getCanonicalPath()`: the NEXT link of
  the same chain — the DataStore multi-instance singleton guard
  (`Lot;.a`: `Liu;->e` Le40; → g8.a → getCanonicalFile pc=30 →
  getAbsolutePath pc=37) NPEd on the null canonical File (caught by the
  catch-all, retried, F084-bounded Lsr.run spin). Canonical ≡ absolute in
  the app-data sandbox (no symlinks; documented equivalence).

Proof (docs/evidence/s76/dooz_f146_upstream/):
- `[R347-FILE] getAbsoluteFile path="...settings.preferences_pb" -> File o894`
  and `getCanonicalFile -> File o895/o897` — the guard PASSES.
- The g8.a pc=569 escape is GONE; the chain runs into DataStore protobuf
  schema init (`androidx.datastore.preferences.protobuf.*` forName family,
  all handled deferred).
- NEW first divergence **F-152**: `Llt0;.w pc=808` null receiver —
  previously masked BY F-146 (the unwind killed composition before this
  code ran). Registered as the next dooz lead, producer trace open.

## 2. Lead 2 — gmdice roll made VISIBLE (R-NEW-392 + R-NEW-393)

The S75 record: clicks dispatch on the real listener path but frames are
byte-identical. The S76 trace (three stacked roots, each proven by the
runtime log + the app's DEX):

1. `Button.getText()` — the TextView getText intercept matched class names
   but "Button" is a SUBCLASS: subsumption law missing → REC-MISS null →
   `CharSequence.toString` NPE → event loop died on the FIRST click.
   **R-NEW-392**: getText/length intercepts now walk the DEX superclass
   chain (`is_subclass_of(class, Landroid/widget/TextView;)`, EXP-068 map).
2. With getText fixed the roll EXECUTED (`DSADiceSet.roll`: Random.nextInt
   ×3 + StringBuilder) but died at `roll() pc=13` — `resultview.setText`
   on NULL: onCreate had died earlier mid-loop. Root: `getBackground()`
   REC-MISS null → `Drawable.setColorFilter` NPE at onCreate pc=88 →
   buttons[1..4]/button_more/resultview never assigned.
   **R-NEW-393**: `View.getBackground()` themed-widget non-null law
   (fresh Drawable heap object; Button/TextView/EditText/ImageView
   family) + `Drawable.setColorFilter(int, PorterDuff$Mode)` (records the
   tint; framebuffer tint application honestly NOT claimed) +
   `setTransformationMethod` acknowledged.
3. Proof (docs/evidence/s76/gmdice_roll_visible/):
   - `[R393-BG] getBackground view=39..43 -> Drawable o46..o51` +
     `[R393-TINT]` — onCreate COMPLETES: 5/5 buttons clickable (was 1/5).
   - First click diff_px **1,511,441** (S75: 0); the roll result renders:
     TextView "Roll it!" → **"6"** (1d6) → **"5"** (next 1d6) — a SECOND
     fully interactive app on the runtime (the S43 tic-tac-toe precedent).

## 3. Lead 3 — snake Dialog-restart hypothesis CONFIRMED and EXERCISED (R-NEW-394)

Static DEX proof (the app's own code): `SnakePanelView.showMessageDialog`
→ `post(SnakePanelView$1)` → `AlertDialog.Builder.setMessage("Game Over!")
.setCancelable(false).setPositiveButton("重新开始", $1$1)
.setNegativeButton("退出", $1$2).create().show()`; `$1$1.onClick` →
`dismiss(); reStartGame()`. The restart actuator is the DIALOG's positive
button — the S73/S75 START@99 tap targeted the WRONG WINDOW.

The S75 frames/manifest.json already showed the dialog WAS rendered from
frame 94 (view ids 700001/700003/700004) — but taps were DEAD: the hit
test only walked the activity tree (target=0), and the decor ViewNodes
had no bounds at all.

Fix **R-NEW-394** (AOSP law: dialog decor laid out in its own window;
WindowManager topmost-window touch routing):
- DialogWindow records decor node ids at build; `layout_decor_nodes()`
  assigns REAL bounds mirroring the painter geometry (button row at
  b−112, thirds split in neutral/negative/positive order);
- `decor_root_at(x,y)` + the F117 tap site route the dispatch root to the
  topmost showing dialog covering the point (`[R394-TAP]`).

Proof (docs/evidence/s76/snake_dialog_restart/, two real runs of the
identical S73/S75 23-tap schedule + death taps D@90 L@91 U@92):
- Run A: game-over at frame 94 (exact S73/S75 match), dialog at
  (80,848 920×224).
- Run B: tap (758,1022)@99 on the positive button → **RESTART OBSERVED
  at frame 99** — snake back at the initial row (y=10), fresh game in
  motion to frame 115+ (wall wrap at frame 108, 2 captures, 25 turns).
- HONEST RESIDUAL **F-153**: the dialog painter's bare BitmapFont has NO
  CJK glyphs → the "重新开始"/"退出" labels paint 0 pixels (pixel-scanned;
  the ASCII "Game Over!" message paints). Input path unaffected; the
  label fix belongs to the font/CJK family.

## 4. Lead 4 — icon bitmap decode capability PROVEN (A7b)

The S75 A7 scope note ("decode is a separate capability") is now probed:
the **A7b identity chain** runs at the same ResourceRuntime site —
`icon resid → arsc.select_file(resid, entries, device_config()) →
extract_entry_cached → decode_image_bytes` (the exp088-era decoder) →
dims + color type + FNV-1a of the decoded RGBA logged:

- f54 fixture and gmdice both: `[A7b] icon @0x7f020002 ->
  res/drawable-hdpi-v4/logo.png (7432 bytes) DECODED 72x72 rgba
  rgba_bytes=20736 fnv1a=0x8a66dfd69a301225` — identical checksum across
  apps (determinism).
- Honest scope: this proves the decode CAPABILITY (real, decodable,
  deterministic pixels); Bitmap/Drawable heap objects and launcher-icon
  painting remain future semantic steps. The f54 verifier gate was
  strengthened to assert the A7b DECODED line (replacing the weaker
  resid-capture gate).

## 5. Regression (zero regressions, gates re-run after EVERY code change)

| Gate | Result |
|---|---|
| Foundation battery (26 fixtures, final binary) | 26/26 rc=0 |
| Pixel/semantic verifier (f54 A7b gate strengthened) | 24/24 PASS |
| Level C snake fidelity replay (committed schedule) | BYTE-IDENTICAL 90/90 |
| Registry | 397 → 404 roots (R-NEW-390..394, F-152, F-153; F-146 → ROOT-CAUSED-FIXED) |

Toolchain note: the container reset wiped the binary again —
bootstrap_toolchain.sh (foreground) + `make -j2` rebuild; baseline
re-established before any change.

## 6. Honest gaps / not done

- **Publish debt still stands**: no GH_TOKEN in this session (constitution
  §52 — token never stored). 5 S75 commits + this wave's commits await one
  tokened `git push origin main`. S75 issue comments likewise.
- **F-152** (dooz `Llt0;.w pc=808` null receiver): the new first
  divergence, producer trace OPEN.
- **F-153** (dialog CJK label paint): painter BitmapFont lacks CJK glyphs;
  labels invisible; input path proven unaffected.
- **Lsr.run F084 spin** (dooz actor worker): still present after the
  fixes; bounded by F084; likely downstream of F-152-class compose-chain
  gaps.
- Icon Bitmap/Drawable OBJECT semantics (heap object painting) — the
  capability is proven; the object law is future work.
- `Integer.parseInt` / `Random` REC-MISS family in gmdice prefs parsing —
  non-fatal this run; noted as future law candidates.

## 7. Artifacts index

- docs/evidence/s76/dooz_f146_upstream/ (probe logs, pre/post-fix crash
  chains, g8/ot disasm dumps, screenshots)
- docs/evidence/s76/gmdice_roll_visible/ (frames 0-3 + manifest with the
  visible roll results, run log, view tree)
- docs/evidence/s76/snake_dialog_restart/ (run_a/run_b, per-frame
  timeline, s76_dialog_restart_report.json)
- scripts/s76_g8_disasm.py (standalone dalvik disassembler with exact
  opcode-size table + ref resolution; --code-off direct mode)
- scripts/s76_snake_dialog_restart.py (two-stage dialog restart probe)
- scripts/s76_registry_update.py (registry delta, append-only)
- Code: dalvik_engine.cpp (R-NEW-390/391/392/393), android_shadows.cpp
  (R-NEW-393), dialog_shadow.{h,cpp} + execution_engine.cpp (R-NEW-394,
  A7b)
