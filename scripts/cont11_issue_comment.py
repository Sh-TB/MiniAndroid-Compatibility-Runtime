#!/usr/bin/env python3
"""CONT-11 WAVE 7 — post the wave ledger to issues #379/#375."""
import subprocess, json, sys

def token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no github credential")

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

BODY = """## CONT-11 / WAVE 7 banked — remote main ee7bf6c3

**FINAL DECISION (§17E): KEEP MINIANDROID PATH** — measured, not assumed.

### A. External runtime feasibility (bounded experiment)
Source-inspected candidates (clones: A2OH/dalvik-universal, A2OH/westlake, Mihon-Runner; ART fetched file-by-file). Full table in `evidence/cont11/CONT11_EXECUTION_LEDGER.md`:
- **No open-source project runs real Compose APKs on a host without Android OS.**
- Strongest prior art **A2OH/westlake** (Apache-2.0, real 177MB Play APK, Kotlin/coroutines/Dagger, View UI): its own numbers prove the **android.* framework bridge (2,056 shim classes / 193K LOC of AOSP Java) is the dominant cost and is INDEPENDENT of the VM choice** — MiniAndroid already owns that layer; an external VM keeps it AND adds a guest-identity boundary on every API call.
- ART host reuse = 11 missing layers (framework.jar, system_server, Binder, ~200 libandroid_runtime natives, HWUI/SF, Choreographer, ViewRootImpl glue, bionic deltas, APEX, ashmem/memfd).
- Empirical root density from our own registry (573 roots / ~12 apps) ≈ 1 root per 60–100 bridged framework classes → **a VM swap eliminates zero registered roots**.
- kotlinx.coroutines needs no port: it executes verbatim as DEX inside the APK (dooz 1.9.0, R8-renamed StateFlowImpl confirmed on sun.misc.Unsafe CAS). Oracle role only.
- REJECTED/IRRELEVANT per §1 rules: DroidVM/Skydnir (VM managers), droidsaw (decompiler), AndroidRecomp (native ARM recompiler), Anbox/Waydroid/redroid/Cuttlefish (full Android OS), dex2jar paths (identity broken). Robolectric/Compose Desktop/ART/westlake retained as ORACLES.

### B. Primary path verified at HEAD (§2)
Clean rebuild from e99c2fbd reproduced the frozen CONT-10 binary `aed46450c103f2ea` **byte-identically**; dooz baseline ×3 anchor `d602648e8e401895` zero-drift, fallback-free by construction; CONT-10 f259 probe **7/7**; gate A **98/0/1**; negatives **19/19**; skill **13/13**; anchors opencalc/chess/dooz/microtimer/unote ×3 byte-identical.

### D. MiniAndroid generic path (fixes, all generic)
- **F-NEW-264c ROOT-CAUSED-FIXED (proven)**: receiver-based gate extension for the ArrayList/LinkedList copy cascade — a DEX-defined collection subclass receiver (`class GuestB extends ArrayList`) dispatched by runtime class, missed the declaring-class string gate, addAll was a **silent no-op**. Mirrors the F-097 TreeSet law (is_subclass_of). Probe flip: fnew259g rows R (shadow→guest size 0→2) and S (guest→guest 0→3) PASS.
- **F-NEW-264/264b IMPLEMENTED (defensive, honestly no-fire in-suite)**: move-exception integrity delivery (a caught Throwable must be a real object, ART/JVM law) + stale-mirror registry fallback in the copy cascade (OpenJDK c.toArray() law).
- **F-NEW-264d REGISTERED (§8 audit)**: plain-Java collection probe (18 rows / 15 types): 15 FAIL **grouped into 6 semantic laws** (read-your-mutation coherence; iterator write-back; Java-8 default-method family; deque views; hash view coherence; missing subList/Stream families) — one law = one bounded generic fix each, banked for the next wave. PASS today: entrySet iteration, LinkedHashMap order, LinkedHashSet order.
- New findings: 259g-a (get(I) out-of-range no IOOBE), 259g-b (java.util.Vector NPE).

### Dooz first divergence RE-ROOTED (F-NEW-265) — the draw path is exonerated
Full link-by-link runtime proof at 1.11.4: dispatchDraw runs per frame; the coordinator walk reaches InnerNodeCoordinator.performDraw; **canvas.translate executes on the live compose-canvas wrapper** (Ly3;.f(FF) ×4/frame); the walk faithfully honors `child.isPlaced` (real DEX field chain → FALSE). The tree never draws because **the measure/layout pass dies mid-flight**: text-layout ctor `Lm7;.<init>` receives a null text CharSequence (Lkb; built with a NULL String, caller Lvs0.c) → the **legal** R8 kotlin null-check (`getClass`) throws → the engine's deferred-throw semantics continue the throwing frame (multi-NPE blast radius) → a NULL Throwable reaches the compose report helper `Lel0.Y(Throwable)` → cascade kills measure → `Lt4.onMeasure` → placement never completes → isPlaced false → 0 content draws. W6's "canvas bridge never constructed" was a downstream consequence. Next arms: (a) deferred-throw aborts the frame at the throw point (ART-faithful); (b) catch-handler argument = real in-flight throwable; (c) why Lvs0.c composes null text.

### §12 fan-out
- sudoku_secuso (Kotlin-heavy game, coroutines): **REAL_APP_CONTENT ×3** `45962e018344e94d` at the fixed binary; stopwatch (Kotlin+coroutines) deterministic ×3.
- Independent Compose APKs (sudokusolver `d114d479df66b0f6`, blockblast `64589a3a7e5c0f73`): **BLOCKED-APK-ABSENT** — F-Droid fetch stalled twice, SHAs recorded, fetch script left in place. Honest.

Registry 566 → **573** (+264, 264b, 264c, 264d, 265, 259g-a, 259g-b). Evidence: `evidence/cont11/CONT11_EXECUTION_LEDGER.md`, `wave7_summary.json`, probes `fixtures/fnew259g_probe` + `fixtures/fcol_audit_probe`. Remote main `6a66806a..ee7bf6c3`, secret-guard PASS.
"""

def post(issue):
    tok = token()
    out = subprocess.run(
        ["curl", "-sfSL", "-X", "POST",
         "-H", f"Authorization: token {tok}",
         "-H", "Accept: application/vnd.github+json",
         "-d", json.dumps({"body": BODY}),
         f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"],
        capture_output=True, text=True)
    try:
        j = json.loads(out.stdout)
        return j.get("html_url") or j.get("message", "unknown error")
    except Exception:
        return f"HTTP-FAIL: {out.stderr[:200]}"

for issue in (379, 375):
    print(issue, "->", post(issue))
