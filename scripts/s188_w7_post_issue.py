#!/usr/bin/env python3
"""S188 W7: post the tracker comment to GitHub issue #559 (English only)."""
import json, subprocess
from pathlib import Path

body = """## S188 W7 — two-arg nextInt contract law + R8 ctor-inlined LP gravity authority (androguard-assisted)

**Method:** androguard 4.1.4 DEX ground truth (kotlin.random singleton demux, `MainActivity.w()V` full decode, DrawerLayout LP authority + styleable payload) + OpenJDK jdk14u source for the `ThreadLocalRandom` contract + live `[W7-TLR]` trace and the EXP088 Phase-B click battery.

### What androguard reversed
1. **RNG singleton demux:** `t3/e.<clinit>` (kotlin.random.Random) — SDK ≥ 34 → `t3/c`, else → `u3/a`. Our runtime reports SDK < 34 → the `Lu3/a;` singleton always serves; it OVERRIDES `c(II)I` → `ThreadLocalRandom.current().nextInt(origin, bound)`. Static caller scan: ZERO callers (virtual dispatch only).
2. **The bug:** the F-086 bridge treated any 2+-arg `nextInt` as the single-arg form and read `args[1]` (the **origin**) as the bound → `nextInt(0, 1)` threw `"bound must be positive"`. OpenJDK jdk14u ThreadLocalRandom.java:336: two-arg check is `origin >= bound → IAE(BAD_RANGE)`, `BAD_RANGE = "bound must be greater than origin"` (:1051). `MainActivity.w()V`'s `Math.max(0, …)` clamps put the zero-dim path exactly on `c(0, 1)` — legal once the bridge is contract-exact (live `[W7-TLR] nextInt(origin=0, bound=1) caller=Lu3/a;.c` ×2 confirms; `getInteger(0x7F090010) → 10` matches the ARSC resolve).
3. **DrawerLayout LP:** `Lv0/d;` (R8-renamed `DrawerLayout.LayoutParams`) declares **ZERO ctors** — R8 inlined the `(ctx,attrs)` ctor into `DrawerLayout.generateLayoutParams(AttributeSet)` itself (`new → MarginLayoutParams.(ctx,attrs) → iput a=0 → obtainStyledAttributes(attrs, E) → ta.getInt(0,0) → iput → recycle`). Styleable authority: `DrawerLayout.E = {16842931 = 0x010100B3 = android:layout_gravity}`; res/7s.xml: NavigationView(7F08015B) is a DIRECT DrawerLayout child with `layout_gravity = 0x00800005 = Gravity.END`. Both the `$`-prefix net and the F-NEW-578 own-ctor scan miss this shape → gravity stayed heap-default 0 → `m(View)` false → "View NavigationView@811 is not a drawer" + openDrawer(END) "No drawer view found with gravity RIGHT" IAE ×2 past the app boundary (revealed by F-NEW-582 peeling the nextInt wall).

### Laws landed (commit 649d33d5)
- **F-NEW-582** (nextInt bridge): two-arg `nextInt(origin, bound)` per OpenJDK — `origin >= bound → IAE("bound must be greater than origin", f086-nextint-range)`; result mapped into `[origin, bound)` via internalNextInt (power-of-two fast path + rejection sampling on `r>>>1`, uint32 wraparound == Java int semantics). Single-arg F-086/F-113 law + deterministic xorshift stream untouched. Diag: `MINIANDROID_W7_TRACE=1` → `[W7-TLR]` rows.
- **F-NEW-583** (`generate_child_layout_params`): R8 ctor-inlined LP authority — the parent's own **REAL** `generateLayoutParams(AttributeSet)` DEX body executes on the real parent object (view id == heap oid) with the child's XML AttributeSetStore attrs; the returned object IS the child LP (gravity included); ROOT-055 semantic w/h write-back preserved; CONT-49 materialization stands as the honest fallback.

### Verification
| metric | W6 (ts_w6d) | W7 (ts_w7c/ts_w7d) |
|---|---|---|
| `f086-nextint-bound` IAE | 3/run | **0** |
| drawer IAE ("not a drawer" + "No drawer view…RIGHT") | 2/run (revealed post-peel) | **0** |
| uncaught in-flight | 3 | **0** (both runs) |
| Phase-B click battery (drawer toggle → c4/w) | 2 IAEs | **clean, 0 IAE rows** |
| tier | FLAT | FLAT (honest, DEFAULT_BACKGROUND_ONLY) |

Goldens: bouncy `8a6c24ac` + unote `3b8dcb0a` + dooz `31ddd4d5` byte-exact (binary `864d65fe7ebd8e3d`). 11-title battery: **CLEAN** — zero tier regressions (mines/memory/blackjack B anchors hold).

### Next frontier
Tier unlock = the dimension/draw chain: `w()` now completes with margins 0 (AOSP-honest for zero-dim views), but the clock face (ClockFragment/StopwatchFragment in FragmentContainerView) still answers `app_draw_ops=0`. Next wave: real measure/layout dimensions for the DrawerLayout ▸ CoordinatorLayout tree → first authoritative app content (B-tier candidate), then Phase-B FDT per-app record.

Evidence: `evidence/s188_w7/W7_LAWS.json` + `W7_RUNS.json` + `W7_BATTERY.json` + runs `ts_w7{c,d}` + 3 scripts.
"""
Path('/tmp/w7_comment.md').write_text(body)

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
