#!/usr/bin/env python3
"""SUCCESS-PATH + SECONDARY DEEP AUDIT + F-NEW-197 wave registry update.
Adds the user-mandated campaign work items (F-NEW-198..214) and updates
F-NEW-197 with the six generic laws this wave landed (3-run proven,
zero golden regressions). Syncs canonical/root_cause_registry.json and
root_registry.json (bidirectional sync law).
"""
import json
from pathlib import Path

R = Path("/home/z/my-project")
CANON = R / "canonical/root_cause_registry.json"
MIRROR = R / "root_registry.json"

d = json.loads(CANON.read_text())
roots = d["roots"]

def find(rid):
    for x in roots:
        if x["id"] == rid:
            return x
    return None

# ── 1) F-NEW-197 wave update ─────────────────────────────────────────────
f197 = find("F-NEW-197")
f197["status"] = "PARTIAL"
f197["law"] = (
    "F-NEW-197 WAVE 2 (SUCCESS-PATH methodology: source-first, "
    "SOURCE->CODE PATH->LAW->REPRO->TRACE->FIX->3-RUN). Six generic laws "
    "IMPLEMENTED+TESTED, all package-agnostic:\n"
    "  1. TYPEDARRAY STALE-PRESENCE LAW: the TypedArray heap object is a "
    "recycled singleton; AOSP TypedArray.obtain rewrites EVERY slot per call "
    "(AttributeResolution.cpp: unfilled = TYPE_NULL/absent). array_present[i] "
    "is now written UNCONDITIONALLY per slot (1 resolved / 0 absent) — "
    "presence from an earlier obtain can never leak (opencalc face: call 1 "
    "resolved 0x01010054; call 2 styleable[0]=0x010100af hit=no inherited "
    "present=1 value=0 -> getInt answered 0 -> setGravity(0) -> ISE 'gravity "
    "must be set to either top or bottom' -> APP BOUNDARY).\n"
    "  2. XML-ATTRIBUTESET PRECEDENCE LAW: obtainStyledAttributes resolves "
    "each styleable slot with the AOSP order (1) XML AttributeSet value, "
    "(2) style, (3) theme, (4) absent -> caller default. The inflater passes "
    "the tag's parsed AXML attrs (attr_resid + typed value) through "
    "CustomViewCtorHook -> AttributeSetStore -> the F-NEW-175 producer. "
    "Evidence: gravity slot now answers 48 (Gravity.TOP) from the XML "
    "([F175-READ] stored=48 present=1); absent slots honor caller defaults "
    "(def=400 -> 400).\n"
    "  3. CONFIG-CONTEXT LAW: Context.createConfigurationContext never "
    "answers null (AOSP ContextImpl); dual-view implemented in both dispatch "
    "layers; one FRESH context per call; S110 base-context map records the "
    "receiver. Face: appcompat attachBaseContext2 chain "
    "(AppCompatActivity=Lg/m; pc=180 createConfigurationContext -> pc=184 "
    ".getResources()) NPE'd -> attach aborted (f141 family, same signature "
    "as the solitaire support-chain record).\n"
    "  4. NEW-THEME LAW: Resources.newTheme() answers a non-null Theme "
    "(AOSP Resources.java); ContextThemeWrapper.getTheme()'s "
    "mTheme=newTheme(); mTheme.setTo() NPE'd (Ll/c;.b pc=26).\n"
    "  5. CLASS-TOKEN getClass LAW: Object.getClass on a CLASS_REF receiver "
    "answers Ljava/lang/Class; (a Class object's runtime class IS "
    "java.lang.Class) — never null (Gson $Gson$Types.getRawType "
    "type.getClass().getName() probe NPE'd).\n"
    "  6. CLASS-TOKEN INSTANCEOF LAWS: (a) CLASS_REF with ref_id==0 "
    "classifies as the java.lang.Class token (heap-backed or not); "
    "(b) desc-only OBJECT_REF (oid=0, desc present) classifies by its "
    "creation-site descriptor.\n"
    "EVIDENCE: opencalculator vc53 uncaught-in-flight exceptions 3 -> 1 "
    "across the wave; laws130 51/51; goldens x3 BYTE-IDENTICAL (dooz "
    "d602648e8e401895, ssw 10446aaf0cd642cc, headingcalc be1cea9cf994b26a, "
    "microtimer da73010a37dd0189, whatsapp 31ddd4d5b8e6d18e); opencalc x3 "
    "deterministic b5a7a35d5fe0564b.\n"
    "REMAINING SUB-FRONTIERS (refined, machine-readable):\n"
    "  A. GENERIC-TYPE REFLECTION FAMILY: Class.getGenericSuperclass / "
    "ParameterizedType.getActualTypeArguments / .getRawType are UNBRIDGED "
    "(null) -> Gson TypeToken (j1/a;.<init> -> Le1/d;.g) IAE "
    "'Expected a Class, ParameterizedType, or GenericArrayType' in "
    "MainActivity.onResume; the instanceof diag proves the argument register "
    "arrives degenerate (oid=0 desc=empty) from the unbridged chain. "
    "Needed: real ParameterizedType heap objects carrying type-argument "
    "identity.\n"
    "  B. TREE-BUILD GAP: the frame remains the shared empty-shell SHA "
    "b5a7a35d5fe0564b (DEFAULT_BACKGROUND_ONLY) — the XML tree the inflater "
    "builds still does not reach the authoritative draw walk (2-node visited "
    "family). Next probe: R005-DECOR view=927 under decor=899 vs the walk's "
    "effective_content_root."
)
f197["evidence"] = (
    "Wave-2 runs: /tmp/fn197/op3..op9 + det1..det3; "
    "[F175-READ] getInt idx=0 stored=48 present=1 answered=48 (XML law); "
    "[F-NEW-197] XML AttributeSet values=4..9; crash.log error count 3->1; "
    "GATE: goldens x3 byte-identical + laws130 51/51 + opencalc x3 "
    "b5a7a35d5fe0564b."
)

# ── 2) New campaign items ────────────────────────────────────────────────
NEW = [
    # SECONDARY DEEP AUDIT (user mandate, 10 items)
    dict(id="F-NEW-198", status="PENDING", priority="P1",
         layer="runtime/legacy-rendering-path",
         title="DEEP-AUDIT P0-1: ApplicationRuntime legacy rendering path — "
               "prove by call graph + runtime trace that no real APK "
               "execution can reach render_pipeline_->render, 'Hello "
               "MiniAndroid'/'main'/'activity_main' layout fallbacks, "
               "stubbed onCreate, or perform_layout() claiming "
               "measure/layout without executing it; if reachable, route "
               "through the canonical Window->ViewTree->measure->layout->"
               "draw->capture path; a synthetic frame must NEVER classify "
               "as REAL_APP_CONTENT.",
         law="V8 authority audit (SECONDARY CAMPAIGN) proved ApplicationRuntime "
             "REFERENCE_ONLY (unreachable from cmd_run) and ExecutionEngine "
             "the only screenshot path — the per-site probe list above "
             "(Hello MiniAndroid/main/activity_main/perform_layout) still "
             "requires the itemized site-level proof.",
         evidence="docs/SECONDARY_CAMPAIGN_V3_V8_AUTHORITY_AUDIT.md",
         fanout="single authoritative-path guarantee for every APK"),
    dict(id="F-NEW-199", status="PENDING", priority="P0",
         layer="runtime/arch-task-executor",
         title="DEEP-AUDIT P0-2: ArchTaskExecutorShadow::dispatch treats "
               "executeOnDiskIO(Runnable) as effectively no-op — background "
               "work disappears, so an AndroidX app that computes on a "
               "background executor and posts the result to main leaves the "
               "UI white forever. Implement minimum generic deterministic "
               "semantics: main executor + background executor + completion "
               "back to main queue; the Runnable must actually execute.",
         law="Deterministic virtual execution is the project law — real OS "
             "threads not required, but background Runnable must execute "
             "(acceptance: post background -> executes -> state changes -> "
             "main callback -> visible UI change; 3-run deterministic proof).",
         evidence="user mandate (SECONDARY DEEP AUDIT)",
         fanout="every AndroidX WorkManager/ArchExecutor app"),
    dict(id="F-NEW-200", status="PENDING", priority="P1",
         layer="runtime/truth-contract",
         title="DEEP-AUDIT P0-3: forbid STUBBED+return-true+SUCCESS "
               "transitions — required state vocabulary EXECUTED / "
               "EXECUTED_WITH_STUB / NOT_EXECUTED / FAILED / BLOCKED; a "
               "STUBBED operation may allow diagnostic continuation but "
               "must not independently produce RENDER_SUCCESS / "
               "REAL_APP_CONTENT / VERIFIED / FRAME_RENDERED unless real "
               "app content is proven; add a regression test.",
         law="S135 provenance + wave-A census verdict laws cover the render "
             "gate; the EXECUTED_WITH_STUB distinction and its regression "
             "test remain.",
         evidence="PHASE 11 stub census (34 sites: 12 lawful-void / 21 "
                  "state-capture / 1 fixed)",
         fanout="cross-cutting evidence-honesty law"),
    dict(id="F-NEW-201", status="PENDING", priority="P1",
         layer="window/identity",
         title="DEEP-AUDIT P0-4 (extended proofs beyond F-NEW-183): the one "
               "canonical content parent per live window must survive "
               "repeated findViewById(android.R.id.content), getContentView, "
               "setContentView, findViewById, ComposeView.setContent, and "
               "AppCompat subDecor creation — object identity preserved; no "
               "package checks.",
         law="F-NEW-183 (item-22 wave A) proved ONE stable content object "
             "per window (subtree search -> per-window map -> "
             "materialize-once); the extended sequence test battery "
             "(ComposeView/AppCompat subDecor) is the remaining work.",
         evidence="[P0-2-CONTENT] REUSED trace; goldens x3",
         fanout="Compose/AppCompat/ViewBinding family"),
    dict(id="F-NEW-202", status="PENDING", priority="P1",
         layer="runtime/virtual-time",
         title="DEEP-AUDIT P1-5: HandlerShadow::settle advances virtual time "
               "by an extremely large amount — prove normal screenshot "
               "capture cannot execute delayed navigation/splash-removal/"
               "animations/state mutations early; separate FRAME ADVANCE "
               "from END-OF-RUN SETTLE; deterministic regression "
               "postDelayed(A,100)+postDelayed(B,10000) with explicit "
               "frame-0/frame-1/final-settle state transitions.",
         law="A normal frame must execute only work due for that frame "
             "(AOSP Choreographer/MessageQueue semantics).",
         evidence="user mandate (SECONDARY DEEP AUDIT)",
         fanout="splash-navigation family; timing-dependent UIs"),
    dict(id="F-NEW-203", status="PENDING", priority="P1",
         layer="runtime/thread-identity",
         title="DEEP-AUDIT P1-6: ArchTaskExecutorShadow::isMainThread / "
               "ThreadShadow::currentThread / LooperShadow convert identity "
               "UNKNOWN into FALSE -> background dispatch -> executor gap -> "
               "UI callback never runs. Introduce explicit MAIN/BACKGROUND/"
               "UNKNOWN diagnostic state; never silently convert UNKNOWN "
               "into BACKGROUND; expose the first divergence.",
         law="Identity-unknown must be observable, not silently converted "
             "(same honesty family as the V6 context-fallback law).",
         evidence="user mandate (SECONDARY DEEP AUDIT)",
         fanout="executors/AsyncTask/Coroutine ICC family"),
    dict(id="F-NEW-204", status="PENDING", priority="P2",
         layer="diagnostics/logging",
         title="DEEP-AUDIT P1-7: audit unconditional std::cerr/std::cout in "
               "HandlerShadow/ActivityShadow/ViewShadow/rendering + dispatch "
               "hot paths; replace unbounded per-call logs with "
               "ERROR/FIRST-DIVERGENCE/BOUNDED/SUMMARY classes; logging must "
               "not alter runtime timing or create apparent hangs.",
         law="S135 bounded ring (rt_cap_=512) + distilled TRACE_SUMMARIES "
             "are the backbone; the hot-path per-call audit is the "
             "remaining sweep.",
         evidence="PHASE 14 logging contract (worklog FINAL-CAMPAIGN-PHASES5-20)",
         fanout="all long runs"),
    dict(id="F-NEW-205", status="PENDING", priority="P1",
         layer="lifecycle/viewtree-owner",
         title="DEEP-AUDIT P1-8: view_tree_lifecycle_owner installation must "
               "be window-canonical — owner lookup from Compose/AndroidX "
               "lifecycle/ViewTree owners must reach the same object through "
               "Window->DecorView->Content->View tree; if Activity-as-view "
               "is the intentional MiniAndroid equivalent, document and "
               "prove the invariant against AOSP ViewTree traversal "
               "semantics.",
         law="AOSP ViewTreeLifecycleOwner.get walks the View tree ancestors; "
             "the F-105 activity-as-view shared-id-space law must be proven "
             "consistent with it.",
         evidence="user mandate (SECONDARY DEEP AUDIT); R-NEW-379 evidence",
         fanout="Compose family"),
    dict(id="F-NEW-206", status="PENDING", priority="P1",
         layer="layout/traversal",
         title="DEEP-AUDIT P1-9: cross-check the traversal order against "
               "AOSP ViewRootImpl — attach -> measure -> layout -> "
               "pre-draw/state checks -> draw -> capture; requestLayout "
               "DURING layout must schedule a second layout pass (AOSP "
               "supports re-entrant valid requesters), not mark layout "
               "complete and move on; no simplistic measure-once/layout-once/"
               "draw-once model where Android semantics require another "
               "pass.",
         law="AOSP ViewRootImpl performTraversals / requestLayout during "
             "layout (second-pass law).",
         evidence="user mandate (SECONDARY DEEP AUDIT)",
         fanout="dynamic-layout family (GONE toggle F-NEW-185, adapters)"),
    dict(id="F-NEW-207", status="PENDING", priority="P1",
         layer="gate/visual-truth",
         title="DEEP-AUDIT P1-10: final visual gate — never accept status "
               "bar/navigation bar/placeholder pixels/diagnostic overlay/"
               "synthetic text/framework chrome as REAL_APP_CONTENT; require "
               "VIEWTREE_REACHED + MEASURE_REACHED + LAYOUT_REACHED + "
               "DRAW_REACHED + APP_DRAW_CALL_OBSERVED + APP_PIXEL_PROVENANCE "
               "+ VISIBLE_CONTENT_PIXELS > chrome-only + 3-run proof; the "
               "45px status-bar false-positive (F-NEW-169) must remain "
               "permanently covered by regression.",
         law="F-NEW-193 content-bounds pixel-ownership verdict law "
             "implements the gate; the dedicated 45px regression check "
             "needs explicit permanent coverage.",
         evidence="V10 five-app gate; F-NEW-169 45px record",
         fanout="every visual verdict"),
    # SUCCESS-PATH campaign (user mandate)
    dict(id="F-NEW-208", status="PENDING", priority="P0",
         layer="campaign/success-path",
         title="SUCCESS-PATH SP-1+SFC-1/2: build the success corpus + "
               "per-title success signature — every title with real L4 "
               "evidence (VERIFIED / TESTED L4=true / PARTIAL L4=true / "
               "hello_smoke / hello_widgets / successful games) recorded with "
               "the full field set: APK SHA, execution mode, renderer family, "
               "Activity, content_view_id, effective_content_root, ViewTree "
               "shape/classes, measure/layout/draw counts, Canvas/Drawable/"
               "Text/image/Surface/GL/WebView op families, Bitmap decode "
               "path, resource/theme usage, input path, state mutation, "
               "invalidate/requestLayout path, frame-to-frame delta, "
               "executed framework APIs, DEX methods/opcodes, REC-MISS, "
               "fallback usage, exceptions, authoritative renderer, "
               "screenshot SHA, 3-run reproducibility. Never count a frame "
               "as success merely because a PNG exists.",
         law="SUCCESS-PATH FIRST mandate: find the common runtime path/"
             "capability set shared by real successful frames BEFORE "
             "attacking failed APKs.",
         evidence="user mandate (SUCCESS-PATH FIRST + SUCCESS-FIRST "
                  "COMPATIBILITY)"),
    dict(id="F-NEW-209", status="PENDING", priority="P0",
         layer="campaign/success-path",
         title="SUCCESS-PATH SP-2/3/12 + SFC-3/4/5: prove the common "
               "successful chain (APK->manifest->Application->Activity->"
               "Window->Decor/content root->attachment->setContentView->"
               "ViewTree->measure->layout->draw traversal->app-owned draw "
               "op->framebuffer mutation->capture, each stage PASS/FAIL/"
               "NOT_USED/UNKNOWN); build the success-vs-white capability "
               "matrix; cluster successful titles into runtime families "
               "(XML widget / ImageView-Bitmap / custom Canvas / SurfaceView "
               "/ game-loop / theme-heavy / activity-transition / dynamic "
               "Drawable / WebView / Compose / GL) derived from RUNTIME "
               "EVIDENCE, never package names; find similar titles per "
               "family; compare at the FIRST divergence (target X, not the "
               "blank screenshot); separate white-screen families "
               "VIEWTREE_NOT_REACHED / MEASURE_NOT_RUN / LAYOUT_NOT_RUN / "
               "DRAW_NOT_RUN / APP_DRAW_OPS=0 / APP_DRAW_OPS>0-but-blank / "
               "REAL-FRAME-but-incomplete into distinct root families.",
         law="Family generalization law: if 8/10 similar APKs render, "
             "strengthen the shared implementation instead of debugging "
             "each APK individually.",
         evidence="user mandate; F-NEW-197 family A+E attribution",
         fanout="families x corpus"),
    dict(id="F-NEW-210", status="PENDING", priority="P1",
         layer="campaign/success-path",
         title="SUCCESS-PATH SP-4/5/6/7/8: authority-accounting audits — "
               "renderer-family selection must use only runtime semantics "
               "(no package/app names, class-name guesses, newest object "
               "id, last setParams receiver, diagnostic placeholders, "
               "synthetic demo renderer deciding the authoritative root); "
               "log window_id/decor_id/content_id/effective_root_id/"
               "root_class/attached/visible/measured/laid_out for every "
               "successful frame (downgrade evidence rather than guess); "
               "classify every frame_census_.app_draw_ops increment as "
               "APP_REAL_DRAW / FRAMEWORK_DRAW / FALLBACK_DRAW / "
               "DIAGNOSTIC_DRAW / UNKNOWN with only APP_REAL_DRAW "
               "satisfying the render gate (fix the accounting law if any "
               "framework default/background/text/fallback can increment "
               "it); classify legacy paths (ApplicationRuntime/"
               "RenderPipeline/software_renderer/synthetic api::View) as "
               "AUTHORITATIVE/LEGACY/TEST-ONLY/DEMO/DEAD with exactly ONE "
               "authoritative framebuffer owner.",
         law="REAL_DALVIK must have exactly ONE authoritative framebuffer "
             "owner; a legacy renderer must never allow real-app-failed -> "
             "synthetic-draws -> success.",
         evidence="user mandate; V8 authority audit (partial)"),
    dict(id="F-NEW-211", status="PENDING", priority="P1",
         layer="campaign/success-path",
         title="SUCCESS-PATH SP-9/10: investigate the successful apps' "
               "upstream source (TicTacToe Classic, Simple Stopwatch, "
               "billthefarmer Notes, Dodge, one Compose/failed counterpart) "
               "— map each source operation (XML hierarchy / programmatic "
               "View / Canvas.onDraw / SurfaceView / ImageView / TextView / "
               "WebView / Compose) to the MiniAndroid runtime operation to "
               "derive reusable Android semantic laws (NOT package-specific "
               "adapters); then derive the COMMON MINIMUM RENDER CONTRACT "
               "from evidence (Activity has Window -> real Decor/content "
               "root -> attached -> measure -> layout -> View.draw -> "
               "at least one app-owned visual primitive reaches the "
               "authoritative buffer -> that buffer is captured -> no "
               "synthetic pixels -> any earlier failure = NOT_RENDERED).",
         law="Source-first methodology law; the contract is DERIVED, not "
             "assumed.",
         evidence="user mandate"),
    dict(id="F-NEW-212", status="PENDING", priority="P1",
         layer="campaign/success-path",
         title="SUCCESS-PATH SP-11 + SFC-9: high-fan-out missing-laws "
               "search — once the successful path is known, inspect failed "
               "titles that should use the same path; prioritize generic "
               "laws affecting many apps (activity/window/content "
               "attachment, visibility, measure/layout dimensions, "
               "ViewGroup child traversal, draw ordering, Canvas "
               "save/restore, Paint defaults, text measurement, Drawable "
               "resolution, ImageView resource resolution, Bitmap density, "
               "TypedArray, Context/Application identity, Fragment host, "
               "lifecycle generated adapters, Handler/Looper/"
               "Choreographer, invalidate/requestLayout, post/postDelayed, "
               "configuration/density, theme/background resolution, "
               "exception propagation, DEX register semantics, class "
               "initialization, reflection/Unsafe field identity); rank by "
               "fan-out x evidence x proximity-to-draw; per-family metric: "
               "titles tested / reaching L3 / L4 / L6, real visual pass "
               "rate, common APIs, common renderer, common missing "
               "capabilities, regressions.",
         law="Rank by technical fan-out, never by app fame.",
         evidence="user mandate"),
    dict(id="F-NEW-213", status="PENDING", priority="P1",
         layer="campaign/success-path",
         title="SUCCESS-PATH SP-13 + SFC-6/7: SUCCESS-PATH REPORT (A working "
               "titles examined; B exact renderer family of each; C common "
               "successful stages; D first stage where white titles "
               "diverge; E common capabilities missing from failed titles; "
               "F existing runtime laws already covering them; G missing "
               "generic laws; H false-success paths discovered; I legacy/"
               "synthetic renderer contamination; J highest fan-out root "
               "causes; K tests required; L 3-run proof plan) + the "
               "success-path protection regression set (one XML widget "
               "app, one ImageView-heavy app, one custom Canvas game, one "
               "SurfaceView game, one themed app, one multi-Activity app, "
               "hello_widgets, hello_smoke) run before every generic "
               "subsystem change — a fix is rejected if it regresses any "
               "working family; forbidden: package==/class==Telegram/"
               "WhatsApp/title==/SmsView/PhoneView hacks.",
         law="Protect-successful-paths law; generalization by semantic "
             "Android behavior only.",
         evidence="user mandate"),
    dict(id="F-NEW-214", status="PENDING", priority="P2",
         layer="campaign/success-path",
         title="SUCCESS-PATH SFC-8: logs-as-data law — distill run logs "
               "into bounded records (first_divergence, execution_family, "
               "API census, ViewTree census, render census, resource "
               "census, exception census, REC-MISS census, frame metrics, "
               "SHA, state-change evidence); keep raw traces outside the "
               "canonical repository unless required as provenance.",
         law="No thousands of raw lines stored or manually inspected.",
         evidence="user mandate"),
]

added = 0
for it in NEW:
    if not find(it["id"]):
        it.setdefault("test", "3-run protocol")
        it.setdefault("source", "user campaign mandate")
        it.setdefault("current", "")
        it.setdefault("risk", "")
        it.setdefault("fix", "")
        it.setdefault("after", "")
        it.setdefault("before", "")
        it.setdefault("affected_titles", "")
        it.setdefault("api", "")
        it.setdefault("upstream_source",
                      "AOSP frameworks/base (per-entry law text)")
        roots.append(it)
        added += 1

d["total"] = len(roots)
# status counts
from collections import Counter
sc = Counter(x.get("status", "?") for x in roots)
d["status_counts"] = dict(sc)

CANON.write_text(json.dumps(d, indent=1, ensure_ascii=False))
# mirror sync (bidirectional law)
mirror = json.loads(MIRROR.read_text())
mirror["roots"] = roots
if "total" in mirror:
    mirror["total"] = len(roots)
if "total_roots" in mirror:
    mirror["total_roots"] = len(roots)
if "status_counts" in mirror:
    mirror["status_counts"] = dict(sc)
MIRROR.write_text(json.dumps(mirror, indent=1, ensure_ascii=False))
print(f"added {added} entries; total {len(roots)}")
print("F-NEW-197 status:", f197["status"])
