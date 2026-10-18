#!/usr/bin/env python3
"""CONT-94 registry update: F-NEW-396 (activity-identity fabrication law)
registered ROOT-CAUSED-FIXED, plus the app-registry Telegram/Forkgram
status refresh from the current-head evidence.

Root: F-NEW-396
  The runtime served Fragment.getParentActivity() (and the two bridge
  twins) with get_or_create_singleton("Lorg/telegram/ui/LaunchActivity;")
  — a hard-coded Telegram class key. The DEX-0 launch path (the one that
  actually launched Telegram/Forkgram/any manifest-activity APK from DEX 0
  of classes.dex) allocated the live activity, printed [U0113-ACTIVITY],
  but NEVER stored api_singletons_[<activity descriptor>] — only the
  multi-DEX and legacy-scan paths did. First getParentActivity() call
  therefore cache-MISSED and FABRICATED a fresh uninitialized object of
  the hard-coded class. App-visible face (Telegram checkSystemBarColors):
  instanceof-LaunchActivity TRUE (right class, wrong instance) -> invokes
  LaunchActivity.H(Z Z Z)V on the empty object -> field p0 reads null ->
  ActionBarLayout.w() on null receiver -> f141 NPE x3 -> APP-BOUNDARY
  unwind x3 -> login UI construction killed -> framebuffer 188/2073600
  non-white (not a render).

Fix (generic, 4 sites, zero app conditionals):
  1. DEX-0 launch path now stores api_singletons_[cls.name] (identity law,
     same as the other two launch paths) — [C94-SINGLETON] LAUNCH-STORE row.
  2. Primary getParentActivity intercept answers the LIVE activity from
     ActivityShadow::current_activity_id() (the same identity
     performLaunchActivity records), class resolved from the heap object.
     Null before attachment (AOSP not-attached contract).
  3-4. The two bridge twins get the same live-identity law.

Named residuals:
  - doneButtonVisible[0..9] boolean-array attach on the getParentActivity
    receiver is an EXP-071-era APP-SPECIFIC patch (hard-coded Telegram
    field name) — retained unchanged this wave to preserve the recorded
    login-flow behavior; fixture-first generalization is a named follow-up.
  - Telegram login form renders top-anchored (bounds/offset frontier) and
    one string resource resolves to the honest "[resid:0x...]" fallback.
"""
import hashlib
import json

REG = "canonical/root_cause_registry.json"
MIR = "root_registry.json"

d = json.load(open(REG))
rows = d["roots"]


def upsert(rid, patch):
    for r in rows:
        if r.get("id") == rid:
            r.update(patch)
            return r
    r = {"id": rid}
    r.update(patch)
    rows.append(r)
    return r


upsert("F-NEW-396", {
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "title": "Activity-identity fabrication: getParentActivity answered a fresh uninitialized hard-coded-class object (right class, wrong instance) because the DEX-0 launch path never stored the activity singleton",
    "layer": "framework/activity-identity",
    "root_cause": (
        "Three intercept sites served getParentActivity() with "
        "get_or_create_singleton(\"Lorg/telegram/ui/LaunchActivity;\") — a "
        "hard-coded class key. The DEX-0 launch path (the path that actually "
        "launched the manifest activity for multi-DEX APKs whose activity is "
        "in classes.dex) allocated the live activity, printed "
        "[U0113-ACTIVITY] #694, ran <init> + onCreate on it, but NEVER "
        "executed api_singletons_[result.main_class] = activity_obj_id (only "
        "the multi-DEX path at ~2307 and the legacy-scan path at ~2463 "
        "stored it). Probe proof (run/cont94/tg_official_diag2/diag3): first "
        "getParentActivity call logged [C94-SINGLETON] MISS '(no cache "
        "entry)' and allocated obj#7307 with default fields ([R414-INIT-"
        "DEFAULT] re-materialized even the c0 ArrayList at H pc=0). "
        "Telegram s2.checkSystemBarColors (decode: pc 0..22: getParentActivity "
        "-> instanceof LaunchActivity -> check-cast -> H(Z Z Z)V) passed its "
        "instanceof guard (the synthetic IS the right class) and invoked "
        "LaunchActivity.H(Z Z Z)V on the empty object; H's iget p0 read null "
        "and the ActionBarLayout.w() invoke raised f141-null-recv NPE — "
        "3x (three fragment presentations: receivers 7101/7305/8929), each "
        "unwinding to the onCreate frame boundary as APP-BOUNDARY ('ART "
        "process-death law; status downgraded'), killing the login UI "
        "construction; framebuffer stayed at 188/2073600 non-white pixels "
        "(not a render)."),
    "fix": (
        "Generic, 4 sites, zero app conditionals: (1) F-NEW-396 identity law "
        "at the DEX-0 launch path: api_singletons_[cls.name] = "
        "activity_obj_id + [C94-SINGLETON] LAUNCH-STORE row (same contract "
        "the multi-DEX and legacy paths already had). (2) Primary "
        "getParentActivity intercept answers the LIVE activity via "
        "ActivityShadow::current_activity_id() with the class resolved from "
        "the heap object; answers null in the not-attached window (AOSP "
        "contract). (3)+(4) the bridge and shadow-dispatch twins get the "
        "same live-identity law. [C94-PARENT] rows are bounded (8) "
        "diagnostics."),
    "evidence": (
        "run/cont94/tg_official_1 (pre, 31 uncaught, 188 px) -> "
        "run/cont94/tg_post1 (post, 15 uncaught, 9340 px, 0 f141 rows, 0 "
        "EXC-UNWIND rows); run/cont94/fk_pre (188 px) -> run/cont94/fk_post "
        "(15599 px, 5 uncaught); fixture com.probe.c94p (apk "
        "run/cont94/c94parent.apk sha16 a90f3d0eaf113ed0): pre "
        "'[C94-PROBE] identity=OTHER-SAME-CLASS marker=null' -> post "
        "'[C94-PROBE] identity=THIS marker=C94-MARKER-V1'; screenshots "
        "run/cont94/tg_post1/screenshot.png (real login widgets: '+' "
        "country-code box, phone field borders, accent text) and "
        "run/cont94/fk_post/screenshot.png ('Your Number' header, phone "
        "field, QRLoginButton)."),
    "test": (
        "Full battery at post binary 7cf6fe7f3d6abb81: wall 12/12 MATCH, "
        "goldens 4/4 (helloworld canonical 83720c1028f832d0), negatives "
        "19/19, reinstall 8/8, MG-310 7/7 GREEN, MG-150 3/3 GREEN, c72priv "
        "13 rows 0-BAD, selftests 13/13, F-NEW-376 70/70, c74esc containment "
        "rows all OK, clock1 virtual clock rows OK, swipe1 law rows OK "
        "(dx=-16/dy=+25, vx=+1055.77/vy=-1562.49; e2 residual unchanged), "
        "as2048_47 0 uncaught — zero drift."),
    "named_residuals": [
        "doneButtonVisible[0..9] attach on the getParentActivity receiver is an "
        "EXP-071-era app-specific patch (hard-coded Telegram field name) — "
        "retained unchanged; fixture-first generalization follow-up registered.",
        "Telegram/Forkgram login form renders top-anchored (fragment view "
        "bounds/offset frontier) — the next UI frontier, not this root.",
        "One Forkgram string resolves to the honest '[resid:0x2131745245]' "
        "fallback (string-resource resolution residual, pre-existing).",
        "UnsatisfiedLinkError on ApplicationLoader.onCreate (native libs "
        "boundary) and the play-billing UnsupportedOperationException chain "
        "are unchanged pre-existing boot-init boundaries.",
    ],
})

d["count"] = len(rows)
d["total"] = len(rows)
json.dump(d, open(REG, "w"), indent=1, ensure_ascii=False)

# mirror
m = json.load(open(MIR))
if "roots" in m:
    for r in m["roots"]:
        if r.get("id") == "F-NEW-396":
            r.update(next(x for x in rows if x["id"] == "F-NEW-396"))
            break
    else:
        m["roots"].append(next(x for x in rows if x["id"] == "F-NEW-396"))
    m["count"] = len(m["roots"])
    m["total"] = len(m["roots"])
    json.dump(m, open(MIR, "w"), indent=1, ensure_ascii=False)

sha16 = hashlib.sha256(open(REG, "rb").read()).hexdigest()[:16]
print("registry rows:", len(rows), "sha16:", sha16)
