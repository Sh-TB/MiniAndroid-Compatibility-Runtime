#!/usr/bin/env python3
"""S188 W5: post the tracker comment to GitHub issue #559 (English only)."""
import json, subprocess
from pathlib import Path

BASE = Path('/home/z/my-project')
ev = json.loads((BASE / 'evidence/s188_w5/W5_FM_FACTORY.json').read_text())

body = f"""## S188 W5 — inflation ctor overload authority + fragment-container factory law (androground-assisted)

**Method:** DEX ground truth from **androguard 4.1.4** (`b1/t0`, `b0/k`, `FragmentContainerView`, `Lb1/g0` disassembly) + runtime probe chain (`NEW-WATCH` / `FIELD-TRACE` / `NULLFIELD`).

### W4 hypothesis correction
`b1/t0;` (FragmentManager) field `c : Lb0/k;` is **not** a FragmentHostCallback — it is the R8 horizontal-merge **state bucket** (`mAdded` ArrayList / `mActive` HashMap holder), initialized by the FM ctor itself (pc 4–7: `new Lb0/k;(1)`). No attachHost law exists in this build. The activity's FM (`obj#202`, built by `Lb1/c0;.<init>`) was healthy all along — field `c` = `obj#204` proven by FIELD-TRACE.

### Root cause (live probes + androguard disasm)
1. C++ `run_custom_view_constructor` passed `{{recv,ctx,attrs}}` (arg_count=3, **no descriptor**)
2. matcher's `param_count == arg_count` "static-like" branch accepted `FCV.<init>(ctx,attrs,FragmentManager)` — an **instance** ctor
3. EXP-078 largest-bytecode preference picked it (bigger body than the 2-arg)
4. callee frame mapped the FragmentManager param to a **default register** → fm garbage
5. `A(I)`: read `this.c` → null → read `c.a` → NPE `field Lb0/k;.a on null object reference` at `b1/t0.A pc=2`
6. APP-BOUNDARY unwind ×2/run (ClockFragment + StopwatchFragment containers, `res/7s.xml`)

### Laws landed (commit 78f7ad0f)
- **F-NEW-576** inflation ctor overload authority — exact AOSP inflation descriptors `((Context,AttributeSet)V` → `(Context)V)` so F-023 exact-descriptor authority selects deterministically; legacy arg-only fallback retained
- **F-NEW-577** fragment-container factory law — `<init>(ctx,attrs,<X>)V` with `X` an app-DEX class → the unique initialized `X` heap instance (earliest creation_sequence) rides in as the 3rd param (FragmentLayoutInflaterFactory semantics)
- honest trace: `[W5-FM-FACTORY] class=... fm_ctor=... fm=obj#202 used=1 path=factory` (×2)

### Verification
| metric | before | after |
|---|---|---|
| `b1/t0.A pc=2` NPE | 2/run | **0** |
| uncaught in-flight | 8 | **6** |
| fragment lifecycle | blocked at inflation | **onAttach → onCreateView → onStart → onResume** |
| tier | FLAT | FLAT (honest) |

Goldens: bouncy `8a6c24ac` + unote `3b8dcb0a` byte-exact; dooz = W1-stable face `31ddd4d5` unchanged. Binary `eea50f7de1583b24`.

### W6 frontier (live-trace recorded)
1. `CoordinatorLayout.t` ISE *"Could not find CoordinatorLayout descendant view with id null to anchor view"* — `app:layout_anchor` reference never landed in LayoutParams (styleable slot resolution vs obfuscated resources)
2. `Landroidx/lifecycle/h0;.a` NPE *"Insets.left on null"* — `DrawerLayout.getRootWindowInsets()` answered null; WindowInsetsCompat root law needed

Evidence: `evidence/s188_w5/W5_FM_FACTORY.json`, 7 androguard dissection scripts, probe logs `ts_w5*.log`.
"""
Path('/tmp/w5_comment.md').write_text(body)

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
