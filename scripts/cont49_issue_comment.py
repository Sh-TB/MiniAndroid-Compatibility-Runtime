#!/usr/bin/env python3
"""cont49_issue_comment.py — post the CONT-49 line-by-line audit to Issue #375.

Lineage: continued from remote HEAD 44dd14db (CONT-48). Rebuilt binary
c0f31ade (identity proof) -> 6c478a22 (three generic laws). Every row is
STATUS — RESULT — EVIDENCE; nothing claimed DONE beyond its row.
"""
import json, subprocess

BODY = """## CONT-49 execution-stage audit — solitaire past the drawer wall: three generic resource/bridge laws

Continued from remote HEAD `44dd14db` (CONT-48), per the "continue from the latest remote HEAD" directive. Every row is **STATUS — RESULT — EVIDENCE** with exact artifacts. Work binary: rebuilt-from-HEAD `c0f31ade…` (identity proof) → fix binary `6c478a22…`. No APK-specific hacks, no fake objects, no forced lifecycle transitions — every law is structural.

### Phase 0 — reconciliation (measured, not assumed)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | origin/main == local == `44dd14db` after fetch+reset (the local container was the CONT-10-era snapshot `e99c2fbd` again — the recovery class CONT-43/45/46 recorded) | git fetch + rev-parse |
| TESTED | binary REBUILT from HEAD == recorded CONT-48 `c0f31ade222bdf9a` — build reproducibility proven after the reset wiped build/ | sha256sum |
| TESTED | tananaev `294a68bd` / simplecalc `68da25fd` / composeStopwatch `dbf937eb` refetched SHA-exact; reset-lost fixtures rebuilt (gate_a_probe, hmap_probe, fnew260/262 probes) | sha256sum; skill 13/13 after rebuild |
| TESTED | baseline gate: **33/33 anchors ×3 byte-identical + probe battery == records exactly + skill 13/13** | phase0 gate logs |
| TESTED | solitaire store base.apk `fdfaf7ca` LOST to the reset; exact bytes unrecoverable (F-Droid vc69/70/71/66/62 hashed — none match; no GitHub release assets) — **vc71 (`9d782be2`, 3.13) substituted with BEHAVIORAL EQUIVALENCE PROVEN: the recorded face `ba50a4d28ea62fe7` reproduces byte-identically on the CONT-48 binary, with the recorded F-NEW-309 IAE row** | run/cont49/sol71_r1 |

### Phase 1 — F-NEW-309 static decode (before any fix)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | the real XML drawer child is the NavigationView (`layout_gravity=0x00800003`); the AppBarLayout genuinely carries NO layout_gravity in real Android too | aapt2 dump xmltree |
| TESTED | DrawerLayout$g: own int field `a` ONLY; (Context,AttributeSet) ctor = super-bridge + obtainStyledAttributes(attrs, `[16842931]`=android:layout_gravity).getInt(0,0) → iput | cont46_disasm.py |
| TESTED | DEX-wide caller census (new `cont49_lp_caller_scan.py`): 17 callers of g(View)/j(View), ALL inside DrawerLayout; the throw rides `g(I) → c(gravity)=findDrawerWithGravity → j(found)` | scripts/cont49_lp_caller_scan.py |
| TESTED | PRE face: getLayoutParams answered a plain `ViewGroup$LayoutParams` (ROOT-055 fallback) → a gravity-0 child spuriously matched → the recorded IAE | run/cont49/sol71_r1/run.log:1093 |

### Phase 2 — F-NEW-309 FIX: the AOSP ViewGroup.generateLayoutParams law (probe FIRST)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | probe BUILT BEFORE patching (`fixtures/fnew309_probe`, the unrenamed DrawerLayout shape): PRE face P4 FAIL (`left lp class=android.view.ViewGroup$LayoutParams`) | run/cont49/probe_f309_pre |
| TESTED | FIX: `generate_child_layout_params` — structural LP-subclass discovery (parent's `$`-inner class, super MarginLayoutParams, (Context,AttributeSet) ctor; R8-renamed `DrawerLayout$g` found — no name conditions), REAL DEX ctor dispatch through AttributeSetStore/F-NEW-197 XML precedence, semantic w/h write-back, node stash; ROOT-055 answers the stashed object; Factory-law hook at inflate_element end with the view-ctor dual gate | dalvik_engine.cpp, android_shadows.{h,cpp}, layout_inflater.{h,cpp}, resource_runtime.{h,cpp}, execution_engine.cpp |
| TESTED | POST: **8/8 PASS ×3** (P1/P2 start=0x800003/8388611 exact, P3 end=8388613, P5 isDrawerView(left) true, **N1 absent-attr gravity stays 0**, **N2 isDrawerView(plain) false**, N3 class identity) | run/cont49/probe_f309_post* |
| TESTED | solitaire: `[F-NEW-309] generated LP parent=DrawerLayout lp=DrawerLayout$g` for every child; the recorded IAE **GONE** (0 THROWABLE rows vs 9) | run/cont49/sol_post2_r1..r3 |

### Phase 3 — the two follow-on faces, root-caused and fixed the same way

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | face past 309: DrawerLayout.onMeasure ISE "does not have a valid layout_gravity" — no getAbsoluteGravity bridge existed → **F-NEW-318**: real static bridge (START→LEFT/RTL:RIGHT, END→RIGHT/RTL:LEFT, no-rel-bit unchanged, other bits preserved) | dalvik_engine.cpp F-NEW-318 block |
| TESTED | face past 318: `Resources.getStringArray` REC-MISS → null array → aget NPE killed the settings singleton b.g (c/m.a pc=1200 → b.g.aR() null-recv) → **F-NEW-319**: ArscParser::resolve_string_array (canonical, type-gated, key-ordered, REFERENCE-dereferencing, GATE-A NotFoundException — never a silent null) + bridge materializing the F-036 heap-array convention | arsc_parser.{h,cpp}; dalvik_engine.cpp F-NEW-319 block |
| TESTED | POST: `String[15]`/`String[2]`… resolve, b.g initializes, 0 THROWABLE rows, 6 frames rendered | run/cont49/sol_post3_r1/run.log |

### Phase 4 — regression (closing binary `6c478a224ab1b3f4`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **33/33 canonical anchors ×3 byte-identical, ZERO DRIFT** (dooz 31ddd4d5 / micro da73010a / unote 4f1a9e4e / gmdice f3b483fe / opencalc a976d2f9 / tttdeluxe af609429 / flappycow 13cf4746 / g2048 59ca1526 / tanana 5f7e0114 / csw 3442d9a9 / simplecalc e847ca03) | final gate log |
| TESTED | probes == records; fnew260 13/0, fnew262 19/0, **fnew309 8/0**; skill 13/13 | same |
| TESTED | support group on ONE binary: **BMI `b52252c2` ×3 (REAL_APP_CONTENT held)**, notes `eb5ebd55` ×3 (androidx scope held), alex `c8d69f81` ×3, sol `ba50a4d2` ×3 | run/cont49/support |

### Cross-app impact + honest bounds

One binary carries three generic laws; every law touches exactly its surface (DEX-container inflation / getAbsoluteGravity calls / getStringArray calls) and the whole corpus minus solitaire is byte-identical ×3 — **BMI improved in CONT-47/48 and stayed; nothing regressed**. Honest bounds: (1) solitaire's screenshot face is UNCHANGED `ba50a4d2` ×3 — the MACHINE moved three divergence layers deeper (IAE → onMeasure ISE → settings NPE, all gone; now DrawerLayout.onMeasure + NavigationView real-DEX onMeasure + ContentFrameLayout 1080x1920 + computeScroll run); (2) the NEW first divergence is recorded for the next wave: `Landroid/support/v4/widget/ah;.a` null-recv (R8 ViewDragHelper, mLeftDragger/mRightDragger chain) at DrawerLayout.computeScroll pc=35 + `menu/h;.i` null-recv at design/internal/c$b.f pc=31; (3) the LP hook's margins come from the semantic model (the bridge still does not read XML w/h itself — ROOT-055 parity, recorded); (4) if the original solitaire bytes surface, re-pin and re-run.

**Registry 628→630** (F-NEW-309 ROOT-CAUSED-FIXED; F-NEW-318/319 appended ROOT-CAUSED-FIXED). Evidence: `evidence/cont49/CONT49_RESULT.md`. Commit `0e3ddb2d`.
"""

r = subprocess.run(
    ["curl", "-sf", "-X", "POST",
     "-H", "Authorization: token " + subprocess.run(
         ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
         capture_output=True, text=True).stdout.split("password=")[1].split()[0],
     "-H", "Accept: application/vnd.github+json",
     "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/375/comments",
     "-d", json.dumps({"body": BODY})],
    capture_output=True, text=True)
resp = json.loads(r.stdout)
print("comment id:", resp.get("id"), "| url:", resp.get("html_url"))
