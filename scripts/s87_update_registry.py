#!/usr/bin/env python3
"""s87_update_registry.py — fold S87 source-probe results into the canonical
registry (honest gate levels; A/B-proven law references; fresh divergences).
"""
import json

CAN = "/home/z/my-project/docs/evidence/canonical"
reg = json.load(open(f"{CAN}/registry.json"))
reg["wave"] = "S87"
by_pkg = {t["package"]: t for t in reg["titles"]}

LAWS = ("F-NEW-171 (APXACT depth underflow) + F-NEW-172 (FragmentActivity "
        "super-chain) + F-NEW-173 (ViewConfiguration object) + F-NEW-174 "
        "(beneath finisher) — all A/B-proven at S87 HEAD")

UPD = {
    "org.secuso.privacyfriendlydame": dict(
        last_success_stage=(
            "S87: Splash→TutorialActivity real navigation + U007 inflate "
            "(6 views) + Skip/Next buttons painted (uniq 213; was "
            "engine-default blank)"),
        first_divergence=(
            "ViewPager adapter page content (TextView text, page icon) not "
            "painted — TEXT_PIXELS=0 at frame_007 (open)"),
        root_cause=LAWS + "; remaining: pager page text render",
        notes=(
            "S87 source-first probe (vc101, APK SHA matches S85 pin "
            "41727c0121fef8ab…); upstream SecUSo/privacy-friendly-dame read "
            "(BaseActivity→pfacore DrawerActivity; SplashActivity routes "
            "then finish()); S54 gate: no artifact until L2+")),
    "org.secuso.privacyfriendly2048": dict(
        last_success_stage=(
            "S87: secuso tutorial screen painted (uniq 160, Skip button; "
            "was engine-default blank)"),
        first_divergence=(
            "F084 interpreter halt: infinite loop PC=0x2 in "
            "com.bumptech.glide.load.engine… + "
            "com.bumptech.glide.GeneratedAppGlideModuleImpl CNFE (deferred)"),
        root_cause=LAWS + "; remaining: Glide engine loop (open)",
        notes=(
            "S87 source-first probe (vc100, APK SHA matches pin "
            "02c799d3d582669d…); upstream SecUSo/privacy-friendly-2048 "
            "(same pfacore scaffold as dame)")),
    "io.github.hathibelagal.mykanji": dict(
        last_success_stage=(
            "S87: root view tree inflates (LinearLayout → full-screen "
            "WebView); was silent depth-underflow blank"),
        first_divergence=(
            "WebView content blank — local asset HTML not rendered "
            "(F085 WebView path exercised; content pipeline open)"),
        root_cause=LAWS + "; remaining: WebView asset content",
        notes=(
            "S87 source-first probe (vc7, APK SHA matches pin "
            "b20274a0885d03ba…); upstream hathibelagal-dev/MyKanji — main "
            "UI is a WebView over local HTML (upstream source read)")),
    "eu.veldsoft.no.thanks": dict(
        last_success_stage=(
            "S87: SplashActivity inflates ConstraintLayout→WebView tree "
            "(was silent depth-underflow blank)"),
        first_divergence=(
            "androidx.savedstate.Recreator_LifecycleAdapter CNFE "
            "(Lifecycling.generatedConstructor) + TypedArray.getIndexCount "
            "on null obtainStyledAttributes result (open)"),
        root_cause=LAWS + "; remaining: savedstate adapter + TypedArray null",
        notes=(
            "S87 source-first probe (vc1); upstream "
            "VelbazhdSoftwareLLC/No-Thanks-for-Android (veldsoft control: "
            "3 sibling titles already render)")),
    "de.tobiasbielefeld.solitaire": dict(
        session="S87-source-probe",
        last_success_stage="S87 re-probe vc71: 8 frames, near-blank class",
        first_divergence=(
            "Context.getResources on null receiver + Window.getCallback NPE "
            "inside android/support v7 chain (f141 family, open)"),
        notes=(
            "S87 re-probe at HEAD; upstream TobiasBielefeld/Simple-Solitaire "
            "read (GameActivity statics need a live Context before the "
            "support shadow answers)")),
    "jwtc.android.chess": dict(
        session="S87-source-probe",
        last_success_stage="S87 re-probe vc298: 8 frames, near-blank class",
        first_divergence=(
            "TypedArray.hasValue on null obtainStyledAttributes result + "
            "Field.get null in obfuscated Lk3/a;.<clinit> (open)"),
        notes=(
            "S87 re-probe at HEAD; upstream jcarolus/android-chess read "
            "(classic View board game; ChessBoardView is a plain onDraw "
            "Canvas — renders once TypedArray/obtainStyledAttributes law "
            "lands)")),
    "com.galaxyrio.sudokusolver": dict(
        session="S87-source-probe",
        last_success_stage="S87 re-probe vc6: 8 frames, near-blank class",
        first_divergence=(
            "kotlin.reflect.jvm.internal.ReflectionFactoryImpl CNFE "
            "(R350-FORNAME family) + Field.get null in Ld31; (open)"),
        notes=(
            "S87 re-probe at HEAD; upstream Galaxy-rio/SudokuYou (Kotlin "
            "app; kotlin-reflect stdlib init needs the FORNAME bridge "
            "extended beyond the Build family)")),
    "com.newsblur": dict(
        session="S87-source-probe",
        last_success_stage="S87 re-probe vc289: 8 frames, near-blank class",
        first_divergence=(
            "Cursor.moveToNext on null (SQLiteDatabase query path) ×deferred "
            "+ AtomicReferenceFieldUpdater REC-MISS storm (open)"),
        notes=(
            "S87 re-probe at HEAD (text-heavy heavy app control); upstream "
            "samuelclay/NewsBlur; SQLite cursor law is the first divergence")),
    "app.halma": dict(
        session="S87-source-probe",
        last_success_stage="S87 re-probe vc15: 8 frames, near-blank class",
        first_divergence=(
            "com.badlogic.gdx.backends.android.AndroidInput.onResume on "
            "null receiver (F-NEW-157 libGDX/EGL frontier family)"),
        notes=(
            "S87 re-probe at HEAD; upstream Crazy-Marvin/Halma (libGDX "
            "game — gated by the documented GL frontier)")),
    "com.sidhant.bubbleshooter": dict(
        session="S87-source-probe",
        last_success_stage="S87 re-probe vc23: 8 frames, rc=0, no exceptions",
        first_divergence=(
            "silent near-blank: zero exceptions, zero render nodes, "
            "Enum.ordinal REC-MISS ×18 (unlocalized — needs deeper trace)"),
        notes=(
            "S87 re-probe at HEAD; upstream sidhant947/BubbleShooter "
            "(SurfaceView-family game; lifecycle completes but nothing "
            "inflates — honest open)")),
}

for pkg, upd in UPD.items():
    t = by_pkg.get(pkg)
    if not t:
        print("MISSING", pkg); continue
    t.update(upd)
    print("updated", pkg)

json.dump(reg, open(f"{CAN}/registry.json", "w"), indent=1)
print("registry saved: wave=S87, titles=", len(reg["titles"]))
