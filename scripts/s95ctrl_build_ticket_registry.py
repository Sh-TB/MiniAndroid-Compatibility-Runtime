#!/usr/bin/env python3
"""s95ctrl_build_ticket_registry.py — S95-CTRL §7/§8 canonical ticket registry builder.

Emits docs/TICKET_REGISTRY.json — the canonical machine-readable problem state.
Ownership law (S95 §21):
  - title-level evidence      -> docs/evidence/canonical/registry.json + docs/ACHIEVEMENTS.md
  - engine-root-level history -> root_registry.json (append-only, 420 roots)
  - PROBLEM/CAPABILITY state  -> docs/TICKET_REGISTRY.json (this file)
  - strategic layers          -> docs/MINIANDROID_0_TO_100.md
Ticket IDs are stable and never reused. Every field is either evidence-backed
or explicitly NOT_MEASURED / NOT_PROVEN — never invented.
"""
import json
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], cwd=REPO,
                      capture_output=True, text=True).stdout.strip()
OUT = os.path.join(REPO, "docs", "TICKET_REGISTRY.json")

STATUS_VOCAB = ["UNKNOWN", "UNTESTED", "OBSERVED", "PARTIAL", "FAILED",
                "ROOT_CAUSE_FOUND", "IMPLEMENTED", "TESTED", "VERIFIED",
                "BLOCKED", "PENDING", "CLOSED", "SUPERSEDED"]

EVIDENCE_LEVELS = {
    "E0": "hypothesis", "E1": "source evidence", "E2": "unit test",
    "E3": "runtime trace", "E4": "real APK execution",
    "E5": "deterministic repeated APK execution",
    "E6": "corpus fan-out / cross-APK verification",
}

REUSE_VOCAB = ["DIRECT_REUSE", "ADAPT", "PORT_ALGORITHM", "PORT_TEST",
               "PORT_FIXTURE", "REFERENCE_ONLY"]

AOSP = "aosp-mirror/platform_frameworks_base"
AOSP_SHA = "1cdfff555f4a21f71ccc978290e2e212e2f8b168"  # pinned S94/S95

def t(id_, subsystem, capability, priority, status, evidence_level, *,
      why, semantic, current, first_divergence="NOT_PROVEN",
      root_cause="NOT_PROVEN", upstream=None, reuse="REFERENCE_ONLY",
      impl_plan="NOT_RECORDED", test_plan="NOT_RECORDED",
      fan_out=None, dod="NOT_RECORDED", help_, created="2026-09-25",
      sources=(), apk_evidence=()):
    return {
        "id": id_, "subsystem": subsystem, "capability": capability,
        "priority": priority, "status": status,
        "evidence_level": evidence_level,
        "created": created, "last_verified_commit": HEAD,
        "why_it_matters": why,
        "semantic_contract": semantic,
        "current_miniland_behavior": current,
        "first_divergence": first_divergence,
        "root_cause": root_cause,
        "upstream_sources": list(upstream or []),
        "reuse_strategy": reuse,
        "implementation_plan": impl_plan,
        "test_plan": test_plan,
        "corpus_fan_out": fan_out or {"potential": "NOT_MEASURED",
                                      "executed": 0, "improved": 0},
        "definition_of_done": dod,
        "contributor_help": help_,
        "evidence_artifacts": list(apk_evidence),
        "source_docs": list(sources),
    }

tickets = [
    # ---------------- GRAPHICS ----------------
    t("GFX-001", "graphics", "programmatic UI color-scheme execution "
      "(custom-view onDraw dispatch + runtime setTextColor/setBackgroundColor)",
      "P1", "ROOT_CAUSE_FOUND", "E4",
      why="Any app that paints through its own View.onDraw or re-themes itself "
          "programmatically renders as a placeholder; visual-verdict chain stops "
          "at PLACEHOLDER_CONTENT.",
      semantic="AOSP View.draw() dispatches onDraw(Canvas) on the derived class; "
               "TextView.setTextColor applies to subsequent draws.",
      current="BigTextView.onDraw never dispatched: run log "
              "[C013-ONDRAW] dispatched=NO ops=0; runtime setTextColor calls "
              "never reach the paint; full-screen #f0f0f0 placeholder dominates.",
      first_divergence="View.draw dispatch: subclass onDraw hook not invoked "
                       "for app-defined custom views.",
      root_cause="Custom-view onDraw dispatch + programmatic paint mutation "
                 "unimplemented (single named gap, S95 wave D layer 4).",
      upstream=[{"repo": AOSP, "file": "core/java/android/view/View.java",
                 "symbol": "View.draw(Canvas) / onDraw dispatch",
                 "head_sha": AOSP_SHA, "note": "pinned-SHA raw fetch (S94)"}],
      reuse="PORT_ALGORITHM",
      impl_plan="Wire onDraw dispatch for app-defined View subclasses; apply "
                "programmatic setTextColor/setBackgroundColor to the live paint.",
      test_plan="Unit: onDraw dispatch shadow test. Fixture: custom-view "
                "draws a colored bar. APK: simplestopwatch must flip "
                "PLACEHOLDER_CONTENT x2 to readable text.",
      fan_out={"potential": "every custom-view app (NOT_MEASURED)",
               "executed": 1, "improved": 0},
      dod="simplestopwatch verdict leaves FAILED; PLACEHOLDER_CONTENT count 0; "
          "battery 99/99 stays green; control APKs stable.",
      help_="Needs runtime knowledge (View draw pipeline)",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md"],
      apk_evidence=["simplestopwatch: before/after captures, run/s95/"
                    "before_after_summary.json"]),

    t("GFX-002", "graphics/layout", "LinearLayout weight-distribution measure",
      "P1", "ROOT_CAUSE_FOUND", "E4",
      why="Weighted LinearLayouts are ubiquitous (menus, button rows, form "
          "layouts); wrong measure lays children off-screen or stacked.",
      semantic="AOSP LinearLayout: weight distribution gives each weighted "
               "child leftover/sum-of-weights, not the full leftover.",
      current="dodge menu panel: each weighted button measured ~1645 px and "
              "laid out to y=6737 (off-screen), drawn over the play field.",
      first_divergence="measureHorizontal/Vertical weight pass.",
      root_cause="Weighted child measured at full leftover instead of "
                 "leftover/sum-weights (S95 §3 dodge cause (b)).",
      upstream=[{"repo": AOSP,
                 "file": "core/java/android/widget/LinearLayout.java",
                 "symbol": "measureHorizontal/measureVertical weight law",
                 "head_sha": AOSP_SHA}],
      reuse="PORT_ALGORITHM",
      impl_plan="Implement leftover/sum-weights distribution + "
                "measureWithLargestChild semantics.",
      test_plan="Fixture APK with 3 weighted buttons in a row: assert equal "
                "thirds via view-tree bounds; APK: dodge menu panel.",
      fan_out={"potential": "all weighted-layout apps (NOT_MEASURED)",
               "executed": 1, "improved": 0},
      dod="dodge menu panel laid out on-screen; WRONG_CLIP residual 0; "
          "battery green.",
      help_="Needs runtime knowledge (measure pass)",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md"]),

    t("GFX-003", "graphics", "GIF frame disposal semantics (dispose 0-3)",
      "P1", "OBSERVED", "E4",
      why="12 VERIFIED-INTERACTIVE titles are animated GIF-driven; compositor "
          "currently minimal — subtle disposal bugs corrupt frames silently.",
      semantic="GIF disposal methods 0-3 with restore-to-background / "
               "previous semantics per frame, as Wuffs/Pillow implement.",
      current="Compositor handles the common cases; disposal-2/3 edge "
              "semantics not proven by test.",
      upstream=[{"repo": "google/wuffs", "file": "internal/cgen/base...",
                 "symbol": "wuffs_gif__decoder", "note": "437-file test corpus"},
                {"repo": "python-pillow/Pillow", "file": "src/PIL/GifImagePlugin.py",
                 "symbol": "_seek disposal handling"},
                {"repo": "golang/go", "file": "src/image/gif/reader.go"}],
      reuse="PORT_ALGORITHM",
      impl_plan="Port Wuffs disposal table into the GIF compositor; keep "
                "deterministic frame hashing.",
      test_plan="Port Pillow test_file_gif.py fixtures as golden frames; "
                "re-run 12 GIF titles (fan-out E6).",
      fan_out={"potential": "12 GIF titles (S93 measured)", "executed": 0,
               "improved": 0},
      dod="Disposal fixtures byte-deterministic; 12 GIF titles no-regression; "
          "at least one title with disposal-2 content verified.",
      help_="Needs graphics + testing",
      sources=["docs/GRAPHICS_SOURCE_ROADMAP.md", "docs/GRAPHICS_SOURCE_REGISTRY.md"]),

    t("GFX-004", "graphics", "NinePatch chunk parse + stretch fidelity",
      "P2", "UNTESTED", "E0",
      why="NinePatch is the standard button/background asset family; no "
          "real-APK failure recorded YET — this ticket demands the smallest "
          "test, it does not claim breakage.",
      semantic="NPng chunk parses patch ranges; draw stretches only patch "
               "regions, 1:1 elsewhere.",
      current="Law L-S94-NINEPATCH-1 registered (S94); implementation depth "
              "not verified by a dedicated fixture.",
      upstream=[{"repo": "houstudio/cdroid", "symbol": "NinePatch view/ninepatch",
                 "note": "58-file deep clone, C++ reference (LGPL-2.1)"},
                {"repo": AOSP, "file": "graphics/java/android/graphics/NinePatch.java"}],
      reuse="ADAPT",
      impl_plan="Build a NinePatch fixture APK via the aapt2 toolchain; "
                "compare rendered bands against cdroid reference behavior.",
      test_plan="Fixture with stretched button background; pixel-band golden.",
      fan_out={"potential": "every stock-widget app (NOT_MEASURED)",
               "executed": 0, "improved": 0},
      dod="Dedicated fixture green + one real NinePatch-using APK verified.",
      help_="Good first task (fixture + comparison)"),

    t("GFX-005", "graphics-verify", "adaptive ink floor vs readable chevron "
      "glyphs (urlchecker <, /, >)", "P2", "OBSERVED", "E4",
      why="The S93 verifier flags glyphs a human reads fine — false positives "
          "erode trust in verdicts; must be fixed at truth level, not by "
          "threshold gaming.",
      semantic="A glyph is readable iff a glyph-truth oracle (OCR-grade) "
               "matches, independent of ink-coverage heuristics.",
      current="Chevron ink ratios 0.0033/0.0016 < 0.004 floor -> UNREADABLE_TEXT "
              "flags although visually readable (white-on-dark).",
      first_divergence="S93 adaptive ink floor vs true glyph identity.",
      upstream=[{"repo": "tesseract-ocr/tesseract", "symbol": "TessBaseAPI::Recognize",
                 "note": "OCR cross-check law (S94 registry)"}],
      reuse="ADAPT",
      impl_plan="Add glyph-truth check (small OCR pass or reference-glyph NCC "
                "at glyph scale) that can override the ink floor.",
      test_plan="urlchecker chevron case must flip to readable WITHOUT "
                "lowering the global floor; adversarial tamper tests stay red.",
      fan_out={"potential": "thin-glyph UIs (NOT_MEASURED)", "executed": 1,
               "improved": 0},
      dod="urlchecker false flags 0; S93 adversarial battery still 100%.",
      help_="Needs graphics/testing knowledge",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md §7.3"]),

    t("GFX-006", "graphics", "shader / color-filter family (LinearGradient, "
      "RadialGradient, BitmapShader, ColorMatrix)", "P2", "UNTESTED", "E0",
      why="Buttons with gradient draws and image effects are common in "
          "mid-tier apps; predictive ticket, not a recorded failure.",
      semantic="Shader local matrix + tile modes drive Paint fill; "
               "ColorMatrix maps RGBA per pixel.",
      current="Paint shader objects accepted but likely ignored at raster.",
      upstream=[{"repo": "google/skia", "symbol": "SkGradientShader"},
                {"repo": "houstudio/cdroid", "note": "C++ shader refs"}],
      reuse="PORT_ALGORITHM",
      impl_plan="Fixture-first: one gradient fixture, measure divergence, "
                "then port minimal Skia gradient law.",
      test_plan="Gradient fixture band-golden; control APK no-regression.",
      fan_out={"potential": "NOT_MEASURED", "executed": 0, "improved": 0},
      dod="Fixture green + one real shader-using APK if corpus contains one.",
      help_="Good first task (reproduce) + graphics"),

    # ---------------- TEXT ----------------
    t("TEXT-001", "text", "HarfBuzz/Minikin shaping wire-up (complex scripts)",
      "P1", "PARTIAL", "E2",
      why="Arabic/Indic scripts shape contextually; MiniAndroid has FriBidi+"
          "HarfBuzz+FreeType linked (R4 POC proven) but the runtime text path "
          "does not shape — any RTL/Indic app will render isolated forms.",
      semantic="hb_ot_shape_internal maps a codepoint run to positioned "
               "glyph IDs per font rules; minikin Layout.cpp does the same "
               "for Android (pinned fetch, S94).",
      current="text_shaper.cpp uses FreeType directly per codepoint; shaping "
              "POC exists but is not wired into the TextView draw path.",
      first_divergence="No shaping stage between text run and glyph raster.",
      upstream=[{"repo": "harfbuzz/harfbuzz", "symbol": "hb_ot_shape_internal",
                 "note": "in-house 3058 test files (S94)"},
                {"repo": "google/minikin", "file": "libs/minikin/Layout.cpp",
                 "note": "AOSP googlesource pinned fetch (S94)"}],
      reuse="DIRECT_REUSE",
      impl_plan="Wire the R4 shaping POC into text_shaper behind a "
                "script-detection gate; fall back to per-codepoint for Latin.",
      test_plan="HarfBuzz in-house tests for the shaping gate; Persian/Arabic "
                "fixture APK; screenshot band golden.",
      fan_out={"potential": "RTL/Indic apps (NOT_MEASURED)", "executed": 0,
               "improved": 0},
      dod="Shaped fixture verified; Latin corpus no-regression.",
      help_="Advanced (text engine) · Needs source research",
      sources=["docs/GRAPHICS_SOURCE_REGISTRY.md"]),

    t("TEXT-002", "text", "bidi/RTL paragraph direction + alignment",
      "P2", "UNTESTED", "E0",
      why="RTL layout direction flips paddings, text alignment and view "
          "order; predictive ticket.",
      semantic="FriBidi paragraph direction law; layout mirroring per "
               "Android supports-rtl.",
      current="FriBidi linked; layout mirroring unverified.",
      upstream=[{"repo": "fribidi/fribidi"}],
      reuse="PORT_ALGORITHM",
      impl_plan="Fixture-first RTL layout test.",
      test_plan="RTL fixture APK; view-tree mirrored bounds.",
      fan_out={"potential": "NOT_MEASURED", "executed": 0, "improved": 0},
      dod="RTL fixture green.", help_="Good first task (reproduce)"),

    # ---------------- AUDIO / VIDEO / MEDIA ----------------
    t("AUDIO-001", "audio", "real-APK audio validation of the S-era audio "
      "engine (MediaPlayer/SoundPool/AudioTrack state machines)", "P2",
      "UNTESTED", "E2",
      why="The audio engine implements AOSP-faithful state machines with real "
          "codecs (mpg123/libsndfile) and unit tests, but NO real-APK audio "
          "title has been executed to prove it at E4+.",
      semantic="MediaPlayer IDLE->INITIALIZED->PREPARED->STARTED<->PAUSED->"
               "PLAYBACK_COMPLETED legal-transition table.",
      current="State machine level IMPLEMENTED+TESTED (unit); APK level "
              "NOT_MEASURED.",
      upstream=[{"repo": AOSP, "file": "media/java/android/media/MediaPlayer.java",
                 "head_sha": AOSP_SHA}],
      reuse="PORT_TEST",
      impl_plan="Pick 1-2 corpus titles with SoundPool/MP audio; capture "
                 "audio state traces during real runs.",
      test_plan="State-trace golden per title; PLAYBACK_COMPLETED crossing.",
      fan_out={"potential": "games with sfx (NOT_MEASURED)", "executed": 0,
               "improved": 0},
      dod="At least one real APK audio state trace recorded at E4.",
      help_="Needs testing + audio",
      sources=["miniandroid/src/audio/audio_engine.h"]),

    t("AUDIO-002", "audio", "SoundPool stream concurrency + rate limits",
      "P3", "UNTESTED", "E0",
      why="Games fire overlapping streams; predictive ticket.",
      semantic="Max concurrent streams per SoundPool; oldest-stream eviction.",
      current="Unit-level only.", upstream=[{"repo": AOSP,
      "file": "media/java/android/media/SoundPool.java"}],
      reuse="PORT_TEST",
      impl_plan="Concurrency fixture.", test_plan="Overlap trace golden.",
      fan_out={"potential": "NOT_MEASURED", "executed": 0, "improved": 0},
      dod="Fixture green.", help_="Needs testing"),

    t("VIDEO-001", "video", "video decode + frame presentation "
      "(MediaPlayer video surface)", "P2", "UNKNOWN", "E0",
      why="Video apps exist in the target corpus family; MiniAndroid has no "
          "video pipeline today — registered as a known frontier, not a bug.",
      semantic="Container demux -> decode -> frame scheduling vs audio clock "
               "-> surface presentation timestamps.",
      current="No video subsystem; audio state machine exists.",
      upstream=[{"repo": "androidx/media3", "symbol": "ExoPlayer pipeline",
                 "note": "reuse matrix: ADAPT"},
                {"repo": "FFmpeg/FFmpeg", "symbol": "avcodec decode loop",
                 "note": "REFERENCE_ONLY license check required (LGPL/GPL)"},
                {"repo": "libsdl-org/SDL", "symbol": "SDL_QueueAudio clock",
                 "note": "REFERENCE_ONLY"}],
      reuse="ADAPT",
      impl_plan="Reuse matrix FIRST (task §12): Media3 timestamp logic, "
                "ffmpeg decode, SDL clock; decide minimal pipeline; license "
                "gate before any code.",
      test_plan="Big Buck Bunny 5s clip fixture; frame PTS golden.",
      fan_out={"potential": "NOT_MEASURED", "executed": 0, "improved": 0},
      dod="Reuse matrix committed; 5s clip plays with monotonic PTS.",
      help_="Advanced (media)"),

    # ---------------- NETWORK ----------------
    t("NET-001", "network", "real HTTP(S) client stack (DNS, TCP, TLS, "
      "redirects, timeouts, headers, chunked)", "P0", "OBSERVED", "E4",
      why="urlchecker's CORE function is real URL checking; Telegram and any "
          "modern app assumes networking. Today network APIs are shadow-"
          "recorded (URL strings captured) with no real I/O.",
      semantic="HttpURLConnection semantics: connect, headers, redirects, "
               "error streams, timeouts per AOSP/libcore behavior.",
      current="Shadow layer stores loadUrl/postUrl/openConnection targets "
              "(android_shadows web_url/web_data); no socket is opened; "
              "apps observe success=false paths.",
      first_divergence="No real connect at the socket boundary.",
      upstream=[{"repo": "curl/curl", "note": "license clean (curl), ADAPT "
                 "candidate; conformance test corpus"},
                {"repo": "openssl/openssl", "note": "TLS; Apache-2.0"},
                {"repo": "boostorg/asio", "note": "async TCP; Boost-1.0"}],
      reuse="ADAPT",
      impl_plan="Minimal real stack: blocking HTTP/1.1 + TLS via openssl "
                "(or mbedtls) + system DNS; expose through the existing "
                "shadow API surface; record every exchange as evidence.",
      test_plan="curl-conformance subset against httpbin fixtures; "
                "urlchecker real-URL execution; offline error paths.",
      fan_out={"potential": "urlchecker + Telegram + diagnostic target",
               "executed": 0, "improved": 0},
      dod="urlchecker performs a REAL HEAD request and renders the verdict; "
          "no regression in offline corpus.",
      help_="Advanced (network/TLS) · Needs source research",
      sources=["docs/audit/RUNTIME_FAILURE_REGISTRY.md"]),

    t("NET-002", "network", "INTERNET DIAGNOSTIC APK target (planned "
      "diagnostic instrument)", "P1", "PENDING", "E0",
      why="A purpose-built diagnostic app measures DNS/TCP/HTTP/TLS/redirect/"
          "timeout/IPv4-IPv6 behavior as an instrument, exactly like the "
          "in-house games instrument the engine.",
      semantic="Each screen exercises one network semantic and REPORTS the "
               "observed result on-screen (self-describing evidence).",
      current="Target registered this wave; app not yet built.",
      upstream=[{"repo": "curl/curl", "note": "reference semantics"}],
      reuse="PORT_FIXTURE",
      impl_plan="Build in-house diagnostic APK (games/ pipeline) against the "
                "shadow API now, re-run against NET-001 when real.",
      test_plan="Per-screen state assertions; screenshot evidence chain.",
      fan_out={"potential": "instrument for all network tickets", "executed": 0,
               "improved": 0},
      dod="Diagnostic APK executes; each network stage reports a verdict "
          "on-screen.", help_="Good first task (build fixture app)"),

    # ---------------- WEB ----------------
    t("WEB-001", "web", "SIMPLE BROWSER APK target (URL entry, HTML, basic "
      "CSS, text, fonts, images, links, scroll, page lifecycle)", "P1",
      "PENDING", "E0",
      why="A simple browser is the highest-signal real-APK target for text, "
          "layout, images and networking at once; task §13 directive.",
      semantic="HTML5 parsing (utf-8, tree construction) + minimal CSS box "
               "layout + navigation history + page lifecycle callbacks.",
      current="Target registered this wave; no browser engine implemented "
              "(directive: do NOT write one from scratch).",
      upstream=[{"repo": "litehtml/litehtml", "note": "C++ html+css renderer, "
                 "BSD — strongest DIRECT_REUSE candidate"},
                {"repo": "lexbor/lexbor", "note": "C html parser, Apache-2.0"},
                {"repo": "servo/html5ever", "note": "spec-compliant parser; "
                 "Rust — ADAPT/REFERENCE"},
                {"repo": "chromium/chromium", "note": "AwContents reference "
                 "only — too large to embed"}],
      reuse="ADAPT",
      impl_plan="Commit a reuse matrix (task §13): evaluate litehtml vs "
                "lexbor+custom-lite-css; license check pinned; then wire to "
                "Canvas/TextView stack.",
      test_plan="wpt subset for the parser (E6); local-page fixture APK; "
                "screenshot band goldens.",
      fan_out={"potential": "instrument for text/layout/image tickets",
               "executed": 0, "improved": 0},
      dod="Reuse matrix committed; browser APK loads a LOCAL page and "
          "renders text+image+link navigation.",
      help_="Advanced (browser/layout) · Needs source research"),

    t("WEB-002", "web", "WebView client callback family "
      "(shouldOverrideUrlLoading, onPageFinished, progress)", "P2",
      "UNTESTED", "E3",
      why="Apps embedding WebView depend on callback ordering; shadow layer "
          "already tracks loadUrl targets.",
      semantic="Callback order: shouldOverrideUrlLoading -> onPageStarted -> "
               "onProgressChanged -> onPageFinished.",
      current="loadUrl/loadData tracked (S-era shadow work); callbacks "
              "synthesized but order fidelity unverified.",
      upstream=[{"repo": AOSP, "file": "core/java/android/webkit/WebView.java",
                 "head_sha": AOSP_SHA, "note": "reference"},
                {"repo": "chromium/chromium", "symbol": "AwContents",
                 "note": "REFERENCE_ONLY"}],
      reuse="PORT_TEST",
      impl_plan="Fixture page with known callback order; assert trace order.",
      test_plan="Callback-order golden.", fan_out={"potential": "NOT_MEASURED",
      "executed": 0, "improved": 0},
      dod="Callback-order fixture green.", help_="Needs testing"),

    t("DEX-002", "dex/runtime", "reflection edge signatures (generic "
      "signatures, array classes, varargs mirror)", "P2", "PARTIAL", "E2",
      why="F-103 closed the Class type-question family; generic/array/"
          "varargs edges remain unproven and apps lean on them.",
      semantic="Class<?> laws over the real hierarchy: getGenericSuperclass, "
               "array component naming, Method.invoke varargs boxing.",
      current="f103_* regressions green; edge families untested.",
      first_divergence="NOT_PROVEN (predictive)",
      upstream=[{"repo": "openjdk/jdk", "file": "java.lang.Class",
                 "note": "REFERENCE_ONLY"}],
      reuse="PORT_TEST",
      impl_plan="Extend f103 fixture battery with edge signatures.",
      test_plan="Reflection edge battery (deterministic).",
      fan_out={"potential": "serialization/DI-heavy apps", "executed": 0,
               "improved": 0},
      dod="Edge battery green; battery stays 99/99.",
      help_="Good first task (write tests)"),

    t("NET-003", "network", "DNS failure propagation + timeout semantics",
      "P2", "UNTESTED", "E0",
      why="Apps must observe deterministic failure paths (UnknownHostException, "
          "SocketTimeoutException) or they hang; currently shadow layer "
          "returns synthetic failure only.",
      semantic="libcore DNS resolution error mapping; connect/read timeouts "
               "per HttpURLConnection contract.",
      current="No real resolver; error mapping untested.",
      first_divergence="NOT_PROVEN (predictive)",
      upstream=[{"repo": "curl/curl", "note": "timeout semantics reference"},
                {"repo": "openjdk/jdk", "file": "networking libs",
                 "note": "error mapping law"}],
      reuse="PORT_TEST",
      impl_plan="Implement together with NET-001 stack; offline fixtures "
                "first.", test_plan="Offline + slow-DNS fixtures.",
      fan_out={"potential": "NOT_MEASURED", "executed": 0, "improved": 0},
      dod="Offline fixture produces the correct typed failure at E4.",
      help_="Advanced (network)"),

    t("TEXT-003", "text", "ellipsize / maxLines / lineSpacing laws", "P3",
      "UNTESTED", "E0",
      why="Corpus apps use multi-line trimmed text everywhere; predictive "
          "ticket before a text-dense app join fails.",
      semantic="AOSP Layout ellipsize END/START/MIDDLE + maxLines clamp + "
               "lineSpacingExtra/Multiplier.",
      current="TextView renders lines; ellipsize behavior unverified.",
      first_divergence="NOT_PROVEN (predictive)",
      upstream=[{"repo": AOSP,
                 "file": "core/java/android/text/Layout.java",
                 "head_sha": AOSP_SHA}],
      reuse="PORT_TEST",
      impl_plan="Ellipsize fixture with known truncation points.",
      test_plan="Band-golden fixture; view-tree line count.",
      fan_out={"potential": "NOT_MEASURED", "executed": 0, "improved": 0},
      dod="Fixture green.", help_="Good first task (reproduce)"),

    # ---------------- DEX / RUNTIME / CONCURRENCY ----------------
    t("DEX-001", "dex/runtime", "Compose / ART-idiom execution frontier "
      "(dooz, Telegram OBSERVED at L1)", "P1", "OBSERVED", "E4",
      why="Modern app share is Compose-heavy; the frontier blocks whole "
          "app families, not single bugs.",
      semantic="Compose slots its composition into the view hierarchy via "
               "ART idioms (default interface methods, varhandle-like "
               "access, lambda linkage) — MiniAndroid must execute them or "
               "record the frontier honestly.",
      current="dooz + Telegram load and launch (L1 OBSERVED) then stop at "
              "unimplemented idioms; root registry tracks per-idiom roots.",
      first_divergence="Per-idiom; tracked as root_registry R-NEW-* entries.",
      upstream=[{"repo": "JetBrains/kotlin", "symbol": "lambda/default-method "
                 "codegen", "note": "ADAPT"},
                {"repo": "aosp-mirror/platform_art", "note": "REFERENCE_ONLY"}],
      reuse="PORT_ALGORITHM",
      impl_plan="Frontier triage: rank missing idioms by dooz/telegram "
                "call-graph frequency; implement top-N as semantic laws.",
      test_plan="Per-idiom semantic tests (existing 96-stage family).",
      fan_out={"potential": "dooz, Telegram + modern corpus (NOT_MEASURED)",
               "executed": 2, "improved": 0},
      dod="dooz or Telegram advances one verified state level.",
      help_="Advanced (DEX/ART semantics)",
      sources=["docs/ACHIEVEMENTS.md"]),

    t("CONC-001", "concurrency", "coroutine/Continuation scheduling "
      "semantics", "P2", "UNTESTED", "E0",
      why="Kotlin apps are coroutine-first; predictive ticket before a "
          "coroutine app is added to the corpus.",
      semantic="Coroutine suspension resumes on the dispatcher; "
               "cancellation is cooperative; Sequential flow ordering.",
      current="Locks/atomics shadows exist (locks_shadow, atomic_shadow); "
              "coroutine state machines unverified.",
      upstream=[{"repo": "Kotlin/kotlinx.coroutines",
                 "symbol": "Dispatchers, CancellableContinuation",
                 "note": "Apache-2.0; PORT_TEST"}],
      reuse="PORT_TEST",
      impl_plan="Fixture app launching a coroutine that mutates UI state.",
      test_plan="Resume-order + cancellation fixtures.",
      fan_out={"potential": "NOT_MEASURED", "executed": 0, "improved": 0},
      dod="Coroutine fixture reaches STATE_CHANGED evidence level.",
      help_="Advanced (concurrency)"),

    t("CONC-002", "concurrency", "volatile/JMM visibility ordering", "P2",
      "UNTESTED", "E0",
      why="Single-threaded interpreter hides visibility bugs until real "
          "multi-threaded apps run; predictive ticket.",
      semantic="JMM happens-before edges for volatile/synchronized/final.",
      current="atomic_shadow provides CAS primitives; visibility ordering "
              "untested.",
      upstream=[{"repo": "openjdk/jdk", "file": "src/hotspot share orderAccess",
                 "note": "REFERENCE_ONLY"}],
      reuse="REFERENCE_ONLY",
      impl_plan="Stress fixture with two interpreter threads + volatile flag.",
      test_plan="Visibility assertion harness (deterministic interleaving).",
      fan_out={"potential": "NOT_MEASURED", "executed": 0, "improved": 0},
      dod="Stress fixture deterministic across 3 runs.",
      help_="Advanced (runtime)"),

    # ---------------- STORAGE / JNI ----------------
    t("STORE-001", "storage", "SQLite transaction/locking semantics beyond "
      "the Room fixture", "P2", "PARTIAL", "E2",
      why="Room/SQLite law fixture is green in the battery (F-026+F-027); "
          "transactions/locking/concurrency remain unproven.",
      semantic="ACID transaction semantics; WAL/journal locking; "
               "ON CONFLICT clauses.",
      current="sqlite_shadow covers the executed fixture paths.",
      upstream=[{"repo": "sqlite/sqlite", "note": "public domain; test corpus"}],
      reuse="PORT_TEST",
      impl_plan="Port sqlite test transactions subset as fixtures.",
      test_plan="Transaction rollback fixture; concurrency smoke.",
      fan_out={"potential": "NOT_MEASURED", "executed": 0, "improved": 0},
      dod="Transaction fixture green; battery stays 99/99.",
      help_="Good first task (write tests)"),

    t("JNI-001", "jni", "native library loading (System.loadLibrary) + "
      "JNI bridge", "P2", "PARTIAL", "E2",
      why="Games ship native engines; without JNI they are blocked at load. "
          "jni_bridge.h exists; no real native APK executed.",
      semantic="System.loadLibrary resolves SONAME, dlopens, binds exported "
               "JNI symbols; JNIEnv table semantics.",
      current="Bridge header present; dlopen path unverified against a real "
              "lib.",
      upstream=[{"repo": AOSP, "file": "core/jni/", "note": "REFERENCE_ONLY"},
                {"repo": "libgdx/libgdx", "note": "real-world JNI usage map"}],
      reuse="ADAPT",
      impl_plan="Hello-JNI fixture APK with a tiny .so; execute through the "
                "bridge.", test_plan="JNI fixture call/return golden.",
      fan_out={"potential": "native-game corpus family", "executed": 0,
               "improved": 0},
      dod="Fixture JNI call round-trips at E4.",
      help_="Advanced (native)"),

    t("COMPOSE-001", "compose", "Compose composition frontier (dooz, "
      "Telegram OBSERVED at L1)", "P1", "BLOCKED", "E4",
      why="Compose-family apps cannot advance past launch until the ART-idiom "
          "frontier shrinks; blocks a whole app family rather than single "
          "bugs.",
      semantic="Compose runtime slots composition into the view hierarchy "
               "through standard runtime facilities (lambdas, default "
               "methods, signature-polymorphic calls).",
      current="dooz + Telegram load and launch (L1 OBSERVED) then stop at "
              "unimplemented idioms.",
      first_divergence="Per-idiom; tracked via root_registry R-NEW-* entries.",
      root_cause="Subsumes DEX-001 idiom triage; not independently "
                 "root-caused.",
      upstream=[{"repo": "JetBrains/compose-multiplatform-core",
                 "note": "FORK_OF androidx compose core (S94 verified)"},
                {"repo": "aosp-mirror/platform_art", "note": "REFERENCE_ONLY"}],
      reuse="PORT_ALGORITHM",
      impl_plan="Blocked on DEX-001 triage: rank missing idioms by call-graph "
                "frequency, implement top-N as laws.",
      test_plan="Per-idiom semantic tests; dooz/telegram advance markers.",
      fan_out={"potential": "Compose-family corpus (NOT_MEASURED)",
               "executed": 2, "improved": 0},
      dod="One Compose-family title advances one verified state level.",
      help_="Advanced (DEX/ART semantics)",
      sources=["docs/ACHIEVEMENTS.md"]),

    t("MEDIA-001", "media", "container/metadata probing "
      "(MediaMetadataRetriever semantics)", "P3", "UNKNOWN", "E0",
      why="Video/music apps query metadata before playback; predictive "
          "ticket registered with VIDEO-001.",
      semantic="Retriever returns duration/title/cover-frame for supported "
               "containers; error behavior on unsupported input.",
      current="No metadata subsystem.",
      first_divergence="NOT_PROVEN (predictive)",
      upstream=[{"repo": "FFmpeg/FFmpeg", "symbol": "avformat probing",
                 "note": "REFERENCE_ONLY, license gate"},
                {"repo": "androidx/media3", "note": "Extractor family; ADAPT"}],
      reuse="ADAPT",
      impl_plan="Decide with VIDEO-001 reuse matrix; metadata-only first.",
      test_plan="MP4/MP3 header fixture probing.",
      fan_out={"potential": "NOT_MEASURED", "executed": 0, "improved": 0},
      dod="Metadata fixture returns duration+title for an MP3 and MP4.",
      help_="Advanced (media)"),

    # ---------------- APP / GAME MASTER TICKETS (§15) ----------------
    t("APP-0001", "app-master", "simplestopwatch — parent failure record",
      "P1", "ROOT_CAUSE_FOUND", "E4",
      why="Parent record for the simplestopwatch failure family (S93-S95).",
      semantic="n/a (parent record)", current="Layers 1-3 fixed (theme "
      "default, textColorPrimary, ImageButton fill); layer 4 = GFX-001.",
      root_cause="See GFX-001 (single named gap).",
      upstream=[], reuse="REFERENCE_ONLY",
      fan_out={"potential": "1 title", "executed": 1, "improved": 1},
      dod="All sub-tickets CLOSED.", help_="See GFX-001",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md §3"]),

    t("APP-0002", "app-master", "urlchecker — parent failure record", "P2",
      "PARTIAL", "E4",
      why="Parent record for urlchecker; its core function needs real "
          "networking (NET-001) and its verifier flags need GFX-005.",
      semantic="n/a (parent record)",
      current="WRONG_COLOR family eliminated (S95); residual UNREADABLE_TEXT "
              "false positives + WRONG_CLIP 1 node.",
      fan_out={"potential": "1 title", "executed": 1, "improved": 1},
      dod="urlchecker SEMANTIC_PASS with REAL url checks (needs NET-001).",
      help_="See NET-001, GFX-005",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md §3"]),

    t("GAME-0001", "game-master", "dodge — parent failure record", "P1",
      "PARTIAL", "E4",
      why="Parent record for dodge; two stacked root causes, one fixed.",
      semantic="n/a (parent record)",
      current="Button-minHeight fixed (44->126 px measured); menu-panel "
              "weight bug = GFX-002 (open).",
      fan_out={"potential": "1 title", "executed": 1, "improved": 1},
      dod="dodge SEMANTIC_PASS.", help_="See GFX-002",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md §3"]),

    t("GAME-0002", "game-master", "bouncy — parent failure record", "P2",
      "PARTIAL", "E4",
      why="Parent record for bouncy (S93-S95).",
      semantic="n/a (parent record)",
      current="3x WRONG_COLOR eliminated (S95); residual WRONG_CLIP 1 node "
              "(possibly GFX-002-adjacent measure semantics).",
      fan_out={"potential": "1 title", "executed": 1, "improved": 1},
      dod="bouncy SEMANTIC_PASS.", help_="Needs graphics",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md §4"]),

    t("GAME-0003", "game-master", "bobball — parent failure record", "P2",
      "CLOSED", "E5",
      why="Parent record; all 4 WRONG_CLIP flags eliminated via "
          "L-S95-BTNMIN-1 (48dip law).",
      semantic="n/a (parent record)",
      current="6/6 text nodes TEXT_VISUALLY_VERIFIED; verdict PARTIAL(0).",
      fan_out={"potential": "1 title", "executed": 1, "improved": 1},
      dod="CLOSED with S95 evidence chain.",
      help_="No help needed (closed)",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md §3"]),

    t("GAME-0004", "game-master", "mini-tetris — parent failure record",
      "P3", "CLOSED", "E5",
      why="ANIMATION_FROZEN classification REFUTED: original S92/S93 tap hit "
          "no touch target; with corrected taps the game animates (6 unique "
          "frames/24, x3 deterministic).",
      semantic="n/a (parent record)",
      current="Harness law fixed in s95_capture.py; verdict PARTIAL(0).",
      fan_out={"potential": "1 title", "executed": 1, "improved": 1},
      dod="CLOSED (refutation evidence recorded).",
      help_="No help needed (closed)",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md §3.5"]),

    t("GAME-0005", "game-master", "minicraft — parent failure record", "P3",
      "CLOSED", "E5",
      why="Same refutation as GAME-0004: world state advances (Blocks 0->2, "
          "house built) x3 deterministic runs.",
      semantic="n/a (parent record)", current="Verdict PARTIAL(0).",
      fan_out={"potential": "1 title", "executed": 1, "improved": 1},
      dod="CLOSED.", help_="No help needed (closed)",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md §3.5"]),

    t("GAME-0006", "game-master", "hotdeath — parent failure record", "P3",
      "CLOSED", "E5",
      why="WRONG_COLOR root cause (vector/adaptive decode gap) fixed S95; "
          "verdict FAIL->PASS with measured luminance delta 239.5->55.5.",
      semantic="n/a (parent record)", current="SEMANTIC_PASS.",
      fan_out={"potential": "1 title", "executed": 1, "improved": 1},
      dod="CLOSED.", help_="No help needed (closed)",
      sources=["docs/GRAPHICS_SOURCE_LIBRARY_VALIDATION.md §3"]),
]

# ---- integrity checks before emit -------------------------------------
ids = [x["id"] for x in tickets]
assert len(ids) == len(set(ids)), "duplicate ticket IDs"
for x in tickets:
    assert x["status"] in STATUS_VOCAB, (x["id"], x["status"])
    assert x["reuse_strategy"] in REUSE_VOCAB, (x["id"], x["reuse_strategy"])
    assert x["priority"] in ("P0", "P1", "P2", "P3"), x["id"]
    prefix = x["id"].split("-")[0]
    assert prefix.isalpha() and prefix.isupper(), x["id"]

registry = {
    "schema": "miniandroid.tickets.v1",
    "generated_utc": subprocess.run(
        ["git", "log", "-1", "--format=%cI"], cwd=REPO,
        capture_output=True, text=True).stdout.strip(),
    "head": HEAD,
    "canonical_ownership": {
        "title_level_evidence": "docs/evidence/canonical/registry.json + docs/ACHIEVEMENTS.md",
        "engine_root_history": "root_registry.json (append-only)",
        "problem_state": "docs/TICKET_REGISTRY.json (this file)",
        "strategic_layers": "docs/MINIANDROID_0_TO_100.md",
        "source_reuse": "docs/GRAPHICS_SOURCE_REGISTRY.json",
        "achievement_narrative": "docs/ACHIEVEMENTS.md",
        "wave_status": "docs/ROADMAP_STATUS.md",
    },
    "status_vocabulary": STATUS_VOCAB,
    "evidence_levels": EVIDENCE_LEVELS,
    "reuse_vocabulary": REUSE_VOCAB,
    "count": len(tickets),
    "tickets": tickets,
}

with open(OUT, "w") as f:
    json.dump(registry, f, indent=1, sort_keys=False)
    f.write("\n")

from collections import Counter
st = Counter(x["status"] for x in tickets)
pr = Counter(x["priority"] for x in tickets)
print(f"wrote {OUT}")
print(f"tickets: {len(tickets)}  statuses: {dict(st)}")
print(f"priorities: {dict(pr)}")
