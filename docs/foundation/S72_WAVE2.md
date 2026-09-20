# S72 — Wave 2: F-142 REAL-APK FIX (RelativeLayout margins + ImageView measure caps)

Session date: 2026-09-20. Start HEAD: 4c8c0e02 (constitution adopted) → this wave.
Directive honored: analysis time was spent ONLY where it converted to runtime
improvement on a real APK (constitution #169 operating loop; one loop per wave).

## 1. Constitution V2 adopted (memory)

User uploaded MASTER CODER CONSTITUTION V2 (169 rules). Stored verbatim at
repo root `CONSTITUTION_V2.md`, committed to git (durable memory across
sessions/compaction). Memory protocol: every agent must read worklog.md +
CONSTITUTION_V2.md; constitution wins on conflict; the 10 absolute
prohibitions (#168) and 9 always-on priorities apply to every commit.

## 2. Wave-1 conclusion CORRECTED by fresh evidence (#155/#156)

Wave-1 registered F-142 as "ImageView src→bitmap resolution never happens
→ 0 px". Fresh-binary re-investigation DISPROVED the mechanism:

- AXML evidence (scripts/s72_w2_dump_axml.py): activity_game.xml has 41
  ImageViews with `android:src="@7F0400XX"` (typed REFERENCE) — drawables
  live in `res/mipmap-mdpi-v4/` (engine ARSC resolver IS type-agnostic and
  resolved them; androguard's ARSCParser fails on this APK — engine tool used
  instead, RULE 3).
- Pre-fix frame pump: fishrings ALREADY painted ONE fish + logo
  (frame_008 = 2,068,844 px nonwhite). The wave-1 "0.0%" dashboard value had
  measured `screenshot.ppm` — the SPLASH window surface — not the active
  window (see §5, F-145).
- [U007-LAYOUT] margin dump (probe extended, env-gated): margins parsed
  CORRECTLY (m=184,184 = 70dip × 2.625) — parse was never the gap.

## 3. Real roots found (first divergence, upstream-backed) — FIXED

### F-142a: RL final-layout fixpoint drops margins
`x = cl` / `y = ct` in the RelativeLayout fixed-point overrode the
margin-correct measure-time cached edges for alignParentLeft/Top, center and
flow-top/left branches. AOSP RelativeLayout.java applyHorizontal/Vertical
SizeRules law: `mLeft = paddingLeft + leftMargin`; flow default = same;
center offsets by margins. Evidence: 41 fish/arrow views at (0,0) while the
only bottom/right-anchored view (ebinqoLogo) landed correctly (0,1747).
Fix: margins added to those branches (same law the LL/FL branches already
apply — engine-internal consistency + upstream contract).

### F-142b: ImageView measure caps (maxWidth/maxHeight/adjustViewBounds)
Never parsed anywhere. AOSP ImageView.java onMeasure L1141+ law implemented:
intrinsic desired → widthFit/heightFit caps → aspect-true opposite-axis
rescale (adjustViewBounds) → spec clamp. ViewNode/Attrs fields added; dims
parsed through the ONE canonical dimension law; booleans per MASTER-2
compiled-bool law. Evidence: topaclockwise 600x424 under maxWidth=42dip/
maxHeight=60dip measured 896x1113 pre-fix; 110x78 post-fix = exact AOSP fit.

## 4. REAL APP RESULT (KPI-1/KPI-2)

fishrings_v1.23_vc6 real-Dalvik, canonical 9-frame recipe, current binary:

| metric | pre-fix | post-fix |
|---|---|---|
| frame_008 nonwhite | 2,068,844 | 2,072,819 |
| game board | 1 fish stacked at (0,0) + logo | 4 fish groups + rings + arrows + logo, AOSP positions |
| determinism ×3 | — | BYTE-IDENTICAL (sha a341e3ad9092f640 ×3) |

Render evidence: `pos=(184,184) size=(110x78)` etc. — margins + caps exact.

## 5. Corpus regression (RULE 123/142): zero regressions

All 9 previously-rendering apps frame_008 nonwhite PRE (s71_live) vs POST
(this wave): bouncy 2073600=2073600, gmdice 182095=182095, microtimer
1041073=1041073, opmt 213286=213286, unote 236520=236520, stopwatch
23472=23472, dooz 197=197, tripeaks 205273=205273, tictactoe 0=0.
ZERO pixel deltas. Battery: all fixture stages PASS (M3 6/6 — its checker
regex was updated for the extended [U007-LAYOUT] margin field; the M3 run
itself was correct, no behavioral regression). EXT-01/02 remain the known
environmental failures (missing external fixture in fresh container).

Wave-1 dashboard delta table corrected (#162 — contradiction reported, not
hidden): tripeaks 0.0% → 205,273 was NOT caused by this fix; the pre-fix
frame was already 205,273. The dashboard had measured the splash surface for
multi-window apps.

## 6. New law registered: F-145 (OPEN, P1) — capture-surface law

Final screenshot captures the FIRST window (splash), not the top-of-stack
window: fishrings post-fix frame_008 = 2,072,819 px but screenshot.ppm = 0
(white splash); tripeaks 205,273 vs 0; dooz 197 vs 92. AOSP law: screenshots
capture the focused/top-of-stack window. Impact: KPI-2 misreported for every
multi-activity app. Next-wave candidate (small, generic, high honesty value).

## 7. FOUNDATION STATUS

NOT COMPLETE — frontier moved: fishrings = real visible UI (KPI-2 +1);
 RelativeLayout margin law + ImageView measure-cap law closed as generic
root laws with zero regressions. Remaining top priorities (evidence-ranked):
F-145 (capture surface, P1), F-141 (null-receiver NPE law, P0), F-143
(service family), F-144 (GL family, P2).

## 8. Commits / push

See git log for this wave (src fix + registry + this doc + scripts).
Push status recorded in the commit message and worklog (no secrets in repo).
