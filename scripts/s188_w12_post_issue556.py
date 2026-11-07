#!/usr/bin/env python3
"""S188 W12: post the MISSING wave tracker comments (W8-W12) to the
master-directive issue #556 (route-aware execution graph + real recovery).
English only, per the tracker convention."""
import json, subprocess

TOKEN = subprocess.run(
    ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
    capture_output=True, text=True).stdout
TOKEN = [l.split("=", 1)[1] for l in TOKEN.splitlines()
         if l.startswith("password=")][0]
API = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"

COMMENTS = [
# ─────────────────────────────── W8 ───────────────────────────────
"""## S188 W8 — DEX oracle head-to-head + Flutter-lane frontier wave (F-NEW-584..587, F-NEW-585)

**Method:** androguard 4.1.4 vs jadx 1.5.3 head-to-head on 5 real W6/W7 wall questions (tranquilstopwatch 2.4MB DEX) + live slot census on the queens/quinb Flutter lanes (evidence/s188_w8/ORACLE_HEAD_TO_HEAD.json).

### Oracle verdict (adopts androguard as the primary DEX oracle)
- androguard 4.1.4: **5/5 EXACT in 0.59s** — pinned the ISE thrower (CoordinatorLayout.t, 204 ins), h0.a/c pc-level decode, styleable payload bytes, zero-static-caller census.
- jadx 1.5.3: 3/5 in 13.7s — FAILED the exact wall method ("Method not decompiled", CoordinatorLayout.t) and DROPPED h0.a/h0.c from its output; strong only on readability.
- Verdict: androguard = primary automation oracle (pc fidelity + never drops + scriptable + 23x faster); jadx = readability complement; raw DEX/Smali = fact source. Conclusions must cite the supporting source.

### Laws landed (commits 9651895d, 75608485..75606485)
- **F-NEW-584** slot census: per-slot UNSUPPORTED thunks + atexit census — blind hits → exact demand lists (queens: env165 GetStringChars ×5 + env226 NewWeakGlobalRef ×1; quinb: env19 PushLocalFrame ×1).
- **F-NEW-586** the demanded slots implemented (UTF-16 transcode face 165/166, weak refs 226/227, local-ref frames 19/20) — queens UNSUPPORTED 6→0, quinb 1→0.
- **F-NEW-587** Flutter AOT lane — libapp.so pre-loaded by FULL PATH at loadLibrary("flutter") — "VM snapshot invalid" GONE, "Check failed: vm" GONE; **the Dart VM crosses its creation wall for the first time**.
- **F-NEW-585** bionic pthread-attr shadow family (src/jni/pthread_shadow.c) in exe + anchor libc.so — the 4-byte bionic attrs vs 56-byte glibc attrs stack corruption (Dart synchronization_posix.cc:87 EINVAL abort) fixed via side-registry attr shadowing; hot-path lock/unlock passthrough. The anchor libc.so wins the binding (DT_NEEDED dependency scope precedes the exe global scope).

### Status (issue-556 trackers)
- Flutter route: BLOCKED→CHAIN_ADVANCED (VM creation wall crossed; new frontier: the Dart thread pool is REAL — 5+ threads, futex waits + epoll message loops — but 2 threads spin ~100% CPU inside VM init; spin attribution = next).
- Engineering: queens/quinb slots SOURCE_INTEGRATED (uncaught marked). Goldens byte-exact; battery CLEAN.
- Evidence: evidence/s188_w8/ORACLE_HEAD_TO_HEAD.json + ADVANCED_STATS.json.
""",

# ─────────────────────────────── W9 ───────────────────────────────
"""## S188 W9 — the five-thread stall ATTRIBUTED + FIXED; the real-GL lane; queens runs to CLEAN EXIT (F-NEW-588, F-NEW-589)

**Method:** no gdb/perf in the container — built a ptrace//proc sampler (scripts/s188_w9*.py): thread census, RIP sampling with maps-file-offset symbolization, orig_rax syscall capture, fd census, eventfd counters.

### Attribution (7-investigation record)
- The spinning pair = 1.raster + 1.io (359/359 'running' snapshots); platform thread parked in futex timed-wait; **1.ui never created**.
- Single process — the W8 "guarded child + sigsuspend" narrative was WRONG (no sigsuspend in src/; fork-probe children exit instantly).
- RIP sampling: every thread parked at one libc trampoline (`__syscall_cancel_arch`, identified by live-memory byte match). Lesson recorded: symbolization MUST carry the maps file-offset column.
- orig_rax: raster/io = epoll_wait(fd7/fd10, maxevents=1, timeout=-1); three (epoll+eventfd+timerfd) triples = three MessageLoopAndroid loops on OUR anchor libandroid; stack walk libflutter → anchor libandroid ALooper → anchor libc pthread shadow → cancel stub.
- eventfd counts 0 → NOT the undrained-wake mechanism.

### Laws landed (commit bade5413)
- **F-NEW-588 — ALooper CALLBACK-mode contract (the exact missing contract):** the W2 ALooper_addFd DISCARDED the callback; the engine registers its timerfd in CALLBACK mode and the callback drains the fd — a fired level-triggered timerfd stays EPOLLIN forever → epoll_wait returns instantly forever → 100% CPU spin → Shell::Create latch never closes. Also: AOSP return constants (WAKE -1/CALLBACK -2/TIMEOUT -3/ERROR -4), pollAll (dartjni face), EINTR retry, EVENT↔EPOLL translation, fd table 256. Anchor rebuilt 21496377b3024bea.
- **F-NEW-589 — the real-GL lane (SQLite law: Load Real):** next divergence was Impeller's proc table ("Could not resolve glGetActiveUniform" → SIGSEGV on a vtable dispatch). OSMesa (Mesa 25.0.7 llvmpipe, GL 4.5) installed WITHOUT root (apt-get download + dpkg -x); EGL anchor rewritten (real contexts/surfaces/SwapBuffers, thread-local current); GLESv2 anchor serves libflutter's full 106-symbol UND gl* census as typed delegators; exe PortableGL untouched (JS lane safe).

### Result (honest) + status
- queens runs to **CLEAN EXIT (exit=1, no kill) for the first time**; "Using the Impeller rendering backend (OpenGLES)" (first time); SurfaceView.getHolder chains; asyncWaitForVsync registered; BootOrder 7/7; Frames Rendered: 2. Tier stays NO_ROOT (WINDOW_ROOT) — no app-owned frame claimed; VM startup is NOT a Flutter visual recovery.
- pthread_shadow audit: passthrough hot path unchanged; destroy→close safe; no recursion; documented gaps (CAP 1024 overflow path, settype-before-init, missing getters) — shadow UNCHANGED this wave.
- Regression: goldens ALL HOLD (bouncy 8a6c24ac / unote 3b8dcb0a / dooz 31ddd4d5); queens/no.thanks/ball2box milestones clean.
- Evidence: evidence/s188_w9/W9_FRONTIER.json + W9[A-F]_*.json.
""",

# ─────────────────────────────── W10 ──────────────────────────────
"""## S188 W10 — env census cleared + RunBundle through 3 fault classes + the measure frontier honestly scoped (F-NEW-590..595)

**Method:** androguard-decoded arg semantics for RunBundleAndSnapshotFromLibrary (raw DEX = fact source) + live exit-census attribution + the full regression battery.

### Laws landed (commits 7acac683, e3b20249, 63da80da)
- **F-NEW-590/591 (env152/env230 cleared to 0):** env152 = libflutter's UpdateDisplayMetrics reading refreshRateFPS/displayWidth/displayHeight/displayDensity (REAL DEX statics: FlutterJNI.display* ×8, real display-config fallback 1080x1920 @2.625/60fps); env230 = DartMessenger#send platform messages read by the REAL nativeDispatchPlatformMessage; direct-Buffer snapshots into REAL malloc memory (F-NEW-591 allocate-family both-conventions cap law — buffers were born cap=0; after: real payloads cap 49/39/54/25).
- **F-NEW-592/593/594 (RunBundle advanced through 3 fault classes):** (1) null-object SIGSEGV at fault_addr=0x500000000 → null-object marshal law; (2) std::terminate SIGABRT — the asm thunk had no .eh_frame → unwind-through-thunk (.cfi + guard try/catch); (3) length_error at the slot-152 call site → env-surface thread safety (intern race = real platform/raster/io threads). First divergence honestly recorded: std::bad_alloc inside RunBundle (probe built: scripts/w10_throw_probe.c; no shim added).
- **F-NEW-595 (the ts measure chain):** the default-ON flip advanced ts to REAL measures (ActionBarOverlayLayout 0x0→1080x1920, Toolbar 1080x168, ContentFrameLayout 1080x1752) BUT the battery caught blackjack's B face collapsing (B_STRUCTURED→FLAT); the caller diag pinned the divergence INSIDE the same androidx classes (ActionBarOverlayLayout height-split: content spec EXACTLY(0), accumulation 1920→3840). The flip was REVERTED battery-verified (opt-in MINIANDROID_MCM_LAW=1). The regression law executed end to end: catch → root-cause → minimal unit → re-verify.
- **W10-D (Godot):** ball2box state preserved unchanged (GodotApp.onCreate clean, 0 uncaught, ROUTE GODOT primary; no engine-load attempt in the window).

### Status
- Flutter route: CHAIN_ADVANCED (env census 0; RunBundle dispatching into the engine); framework_executing=false; tier NO_ROOT.
- Evidence: evidence/s188_w10/{W10_LAWS,W10_RUN,W10_TS_DIMENSION,W10_BATTERY,W10_ANDROGUARD_RUNBUNDLE,W10_ANDROGUARD_TS_MEASURE}.json.
""",

# ─────────────────────────────── W11 ──────────────────────────────
"""## S188 W11 — impact back-review of the whole-wave progress (fresh re-verification on a byte-exact rebuild)

**Method:** sandbox-recycle rebuild → binary SHA verified byte-exact (73f4d87ac617ef4e) → fresh full battery + goldens + queens GL re-verification (no cached evidence).

### Fresh results
- Battery **11/11 apps, tier verdict HOLD ×11, drops=0**; quinb uncaught=1 reproduced (recorded stable state, not a regression).
- Goldens **ALL HOLD** on the rebuilt binary (bouncy 8a6c24ac + unote 3b8dcb0a + dooz 31ddd4d5).
- queens GL reproduces: impeller_accepted=1, frames_rendered=2, run_bundle_fault=0, dispatch_platform_fault=0, guarded_call_faults=1 (the recorded std::bad_alloc first divergence, honestly reproduced pre-fix).

### Impact chain (per the issue-556 trackers)
- W2 baseline: 11 apps launch OK, 4 B_STRUCTURED faces, route violations 0.
- W5–W7: FM factory + CoordinatorLayout/Insets walls + OpenJDK RNG contract — no.thanks dipped FLAT at W7 and recovered B_STRUCTURED by W10 (recovered anchor).
- W8: slot census + queens/quinb slots + Flutter AOT preload + pthread shadow; androguard 5/5 0.59s vs jadx 3/5 13.7s + 2 wrong decompiles → primary oracle.
- W9: F-NEW-588 (the two 100%-CPU spinner threads root-caused) + F-NEW-589 (OSMesa real-GL) → Dart VM advanced past the five-thread stall, Impeller ACCEPTED, 2 frames, queens CLEAN EXIT.
- W10: env census cleared + RunBundle 3 fault classes + ts measure chain opt-in.
- Honest limits: flutter framework_executing=false (real_app_frame=false); Godot engine-load never attempted; ts draw dispatch remaining; UNOBSERVED ≠ PASS maintained throughout.
- Evidence: evidence/s188_w11/{W11_IMPACT_REVIEW,W11_QUEENS_GL,W11_REVERIFICATION}.json (commit 28952e8a).
""",

# ─────────────────────────────── W12 ──────────────────────────────
"""## S188 W12 — the RunBundle bad_alloc ROOT-CAUSED (arena lifetime contract, F-NEW-596) + the height-split COMPLETED (F-NEW-598) + measure law default-ON + the Godot chain decoded — 30 executed tasks

**Method:** a new operator-new/__cxa_throw interposer probe (LD_PRELOAD, probe-only) with true-RA capture + /proc/self/maps resolution; F-NEW-596 box hexdump attribution; androguard decode of BOTH androidx versions' ActionBarOverlayLayout.onMeasure; androguard Godot chain decode; the full battery.

### F-NEW-596 (Flutter lane) — the W10 first divergence RESOLVED
- The huge allocation caught live: `_Znwm(size=0x7f... = a POINTER value)`; the true-RA capture proved the exe unwind frames are stale interpreter values (mid-instruction "return addresses").
- The box hexdump did the attribution: the SAME interned id pointer read box_len=38 (healthy) then box_len=0x7ff...d19d20 (smashed) — the 39-byte platform-message state had reused the freed chunk.
- ROOT CAUSE: box_string() registered EVERY box in the per-call arena and arena_clear() (the local-ref sweep after EVERY native dispatch) deleted them — including the interner's ids and cached class tokens = USE-AFTER-FREE (explains the W10 "second batch bad_allocs while the first reads fine" face exactly).
- Law: interner ids + class tokens are GLOBAL-scope handles — allocated OUTSIDE the arena (box_string_permanent); interned class tokens give pointer identity per name with the PLAIN-name payload (a first-attempt "C:" key-prefix payload leak was caught live — GetFieldID(C:io/flutter/...) — and corrected in the same wave).
- Post-fix: corrupt-box 0, guarded faults 0, Impeller ACCEPTED, frames 2, goldens ALL HOLD. Snapshot census: queens libapp.so ships the OLD pair (_kDartSnapshotData/_kDartSnapshotText, 3 dynsym exports); libflutter 3.13.4 carries the _kDartSnapshot* dlsym strings in-binary — no shim until an attributable engine-side snapshot failure appears.

### F-NEW-598 (the measure frontier) — the W10 height-split first divergence COMPLETED
- androground ground truth: the height-split is mContentInsets.set(mBaseContentInsets) then top += mActionBarTop.getMeasuredHeight() (the not-overlay path; ts's fullscreen path reads the theme bar height instead).
- The 1920 came from the S109 FrameLayout super.onMeasure law answering max(spec, children) under AT_MOST — AOSP resolveSizeAndState semantics is min(spec, want), want = max(child + lp margins) + padding.
- The F-NEW-598 MCM-input diag made the collapse chain fully visible live (bar 1920 → content margins 1920 → vpad 1920→3840→5760 → content spec EXACTLY(0) → 1080x0 at y=3840).
- Result: **blackjack exit=0 (first CLEAN EXIT)**, uncaught 0, B face with 69 colors / 23% non-bg (green felt + cards); ts real measures hold; **MINIANDROID_MCM_LAW retired to default-ON (opt-out =0)**.

### Verification (the regression law, end to end)
- Goldens ALL HOLD ×2 this wave (bouncy 8a6c24ac + unote 3b8dcb0a + dooz 31ddd4d5).
- W12 battery **11/11 CLEAN — zero tier drops** vs the W2/W10 floor; no.thanks ADVANCED to C_TEXT_ON_FLAT.
- Route matrix 11/11 with ROUTE_VIOLATION=0.

### The Godot chain (decoded + stall attributed, no shim)
- androguard decode: Godot.onCreate → initializeGodot() → **GodotLib.initialize(Activity, Godot, AssetManager, GodotIO, GodotNetUtils, DirectoryAccessHandler, FileAccessHandler, Z)** — the native bootstrap; GodotLib.setup comes from the surface path.
- Live census: onCreate ok, 0 uncaught, ROUTE GODOT primary — but ZERO GodotLib calls: the stall is attributed to [S186I-STUB] androidx FragmentManager.dispatchStateChange — the androidx state machine never moved the Godot fragment past CREATED (only the ReportFragment drained through F-NEW-304), so initializeGodot never ran. Next blocker named exactly: the androidx pending-actions → app-fragment lifecycle movement (onAttach/onCreate/onCreateView).

### Status + evidence
- Flutter: RunBundle fault RESOLVED — the lane now waits on the Dart isolate snapshot pair (the engine dlsym's it itself); Godot: BLOCKER_ATTRIBUTED; ts draw chain: APP_DRAW_OPS (theme-attr backgrounds + fragment onDraw) recorded as the next blocker.
- Evidence: evidence/s188_w12/{W12A_F596_ARENA_LIFETIME,W12B_F598_HEIGHT_SPLIT,W12C_GODOT_CHAIN,W12_T1_THROW_PROBE,W12_T2_ANDROGUARD_RUNBUNDLE,W12_T7_ANDROGUARD_TS_MEASURE,W12_T8_F598_BJ_DIAG,W12_T9_MCM_RETRIAL,W12_T16_GODOT_RUN,W12_BATTERY,W12_ROUTE_MATRIX}.json + w12_*.console.log (commit cbc9058e).
""",
]

for i, body in enumerate(COMMENTS):
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", "-H", f"Authorization: token {TOKEN}",
         "-H", "Content-Type: application/json", "-d", json.dumps({"body": body}),
         f"{API}/issues/556/comments"], capture_output=True, text=True, timeout=60)
    try:
        resp = json.loads(r.stdout)
        url = resp.get('html_url')
        if url:
            print(f'comment {i+1}/{len(COMMENTS)} posted:', url)
        else:
            print(f'comment {i+1} resp:', str(resp)[:200])
    except Exception:
        print(f'comment {i+1} raw:', r.stdout[:300], r.stderr[:200])
