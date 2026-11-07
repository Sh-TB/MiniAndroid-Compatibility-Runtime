#!/usr/bin/env python3
"""S188 W6: post the tracker comment to GitHub issue #559 (English only)."""
import json, subprocess
from pathlib import Path

BASE = Path('/home/z/my-project')

body = """## S188 W6 — anchor-id law + WindowInsets root/insets family (androguard-assisted)

**Method:** androguard 4.1.4 DEX/AXML ground truth (ISE thrower disasm, styleable `fill-array-data` payload decode, full layout decode, `h0` SDK-bucket decode) + live FIELD-TRACE (`MINIANDROID_FIELD_TRACE='Lb0/f;.f'`) on the W5 binary.

### What androguard reversed (again)
1. The ISE thrower is `Landroidx/coordinatorlayout/widget/CoordinatorLayout;->t()V` — anchor field = `Lb0/f;->f I`; `Lb0/f;` is the R8-renamed `CoordinatorLayout$LayoutParams` (super `MarginLayoutParams`). Its `(ctx,attrs)` ctor **iputs −1 into e(keyline)/f(anchorId) BEFORE any TypedArray read**.
2. The styleable authority `La0/a;->b [I` (CoordinatorLayout_Layout) decoded from the ctor's `fill-array-data-payload`: slot1 = `0x7f0302e8` = layout_anchor (`getResourceId` default −1), slot6 = keyline default −1.
3. Full AXML decode of `res/7s.xml` (resource-obfuscated name): DrawerLayout ▸ CoordinatorLayout ▸ LinearLayout/Toolbars/…/NavigationView — **NO `app:layout_anchor` on ANY child** → the "XML anchor never landed" theory was dead; anchorId had to come from the runtime side.
4. `h0` = R8 SDK-demux bucket; `h0.a(Insets)I` is the literal NPE site (`iget Insets.left; return`); `h0.c(WindowInsets)Insets` is a **one-line shim for `WindowInsets.getTappableElementInsets()`** (API 29).

### Live smoking gun (ts_w6ft)
`[FIELD-TRACE] get CoordinatorLayout.t Lb0/f;.f obj#1681 value=0` — anchorId read as heap-default **0**, never −1, zero `put` rows → the real DEX LP ctor never ran; ROOT-055 fallback materialized shadow-class LPs (`o1567/o1568/o1681…` churn, C++ names `anchorId/mAnchorId` only). The `"$"`-prefix LP discovery could never match an R8-renamed class → `findViewById(0)` → null → ISE ×2/run.

### Laws landed (commit 3bc08a1a)
- **F-NEW-578** R8-renamed LP discovery (dalvik_engine.cpp `generate_child_layout_params`): when the `$`-prefix net misses, scan the **parent's own methods** for `new-instance` (op 0x22) targets satisfying (super MarginLayoutParams + (ctx,attrs) direct ctor); the **real DEX LP ctor then runs** (defaults iput −1 + TypedArray reads) — AOSP's own binding. Diag: `lp=Lb0/f; via new-instance in generateDefaultLayoutParams()`.
- **F-NEW-580** root-insets in-window pre-attach face (View.getRootWindowInsets): parented nodes and the activity content root answer the root-insets object; true orphans keep AOSP null (cont104 `C104-PREATTACH null=true` preserved).
- **F-NEW-581** API-29 insets-family law (window_insets_shadow.cpp): `getInsets/getSystemWindowInsets/getTappableElementInsets/getMandatorySystemGestureInsets/getSystemGestureInsets/getStableInsets` all answer a **ZERO Insets object** (F-NEW-384 zero-inset model), never null; also fixes the PLURAL `getSystemWindowInsets()` swallowed by the legacy int-prefix branch.

### Verification
| metric | W5 (ts_w5v) | W6 (ts_w6d) |
|---|---|---|
| `CoordinatorLayout.t` ISE "Could not find …" | 2/run | **0** |
| `h0.a` NPE "Insets.left on null" | 1/run | **0** |
| uncaught in-flight | 6 | **3** |
| LP identity churn (view 725) | o1567/o1568/o1681… | **one object (F-NEW-309/322)** |
| tier | FLAT | FLAT (honest, DEFAULT_BACKGROUND_ONLY) |

Goldens: bouncy `8a6c24ac` + unote `3b8dcb0a` byte-exact; dooz `31ddd4d5` = W1-stable face (script pin corrected from pre-W1 `d602648e`).

### W7 frontier (chain already mapped with androguard)
×3 `f086-nextint-bound` IAE: `Lu3/a;.c(II)I` = `ThreadLocalRandom.current().nextInt(origin, bound)`; caller `MainActivity.w()V` reads Toolbar/LinearLayout `getWidth/getHeight` — bound computed from a 0-dimension view (dimension plumbing), then Phase-B FDT per-app record.

Evidence: `evidence/s188_w6/W6_LAWS.json` + runs `ts_w6{pre,ft,a..d}` + 4 androguard scripts.
"""
Path('/tmp/w6_comment.md').write_text(body)

TOKEN = subprocess.run(
    ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
    capture_output=True, text=True).stdout
TOKEN = [l.split("=", 1)[1] for l in TOKEN.splitlines()
         if l.startswith("password=")][0]
API = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
r = subprocess.run(
    ["curl", "-s", "-X", "POST", "-H", f"Authorization: token {TOKEN}",
     "-H", "Content-Type: application/json",
     "-d", json.dumps({"body": body}),
     f"{API}/issues/559/comments"], capture_output=True, text=True, timeout=60)
try:
    resp = json.loads(r.stdout)
    print('comment url:', resp.get('html_url', resp))
except Exception:
    print('raw:', r.stdout[:300], r.stderr[:200])
