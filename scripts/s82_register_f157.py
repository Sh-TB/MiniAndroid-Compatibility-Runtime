#!/usr/bin/env python3
"""s82_register_f157.py — register F-NEW-157 (libGDX AndroidGraphics EGL/VP
frontier) discovered by the S82 P9 hard-gate execution (§49 Gate A).

Evidence chain (run/s82/MAND-001/run1/crash.log):
  NPE unwound Lcom/badlogic/gdx/backends/android/AndroidGraphics;.createGLSurfaceView
  (invoke_pc=0x0, depth=6) -> AndroidGraphics;.<init> -> AndroidApplication;.init
  -> .initialize -> escapes app boundary at
  Lse/tube42/p9/android/MainActivity;.onCreate invoke_pc=0x15 [APP-BOUNDARY].

This is the libGDX GL-surface creation family (S80 already saw the frontier
with emmanuelmess tictactoe = libGDX GL/EGL). F-NEW-156 stays the GENERIC
onCreate-unwind family; F-NEW-157 is the libGDX-specific producer.
"""
import json

REG = "/home/z/my-project/root_registry.json"
S82 = "/home/z/my-project/docs/corpus/s82/title_registry.json"

entry = {
    "id": "F-NEW-157",
    "title": "libGDX AndroidGraphics.createGLSurfaceView NPE (EGL/GLSurfaceView frontier): app-boundary unwind at MainActivity.onCreate — libGDX AndroidBackend GL surface creation chain unimplemented",
    "status": "OBSERVED-FAIL",
    "priority": "P0",
    "evidence": ("S82 hard-gate P9 (MAND-001, se.tube42.p9.android v0.1.1 vc11, "
                 "APK sha256 e69e40836e31337eb6d536b5637a3f6ba7b6484b54d172dd24238c0cb2dd5a76): "
                 "run/s82/MAND-001/run1/crash.log 6 errors, EXC-UNWIND chain "
                 "AndroidGraphics.createGLSurfaceView(pc=0x0,d6) -> AndroidGraphics.<init>(0x5a/0x1,d5/d4) "
                 "-> AndroidApplication.init(0x25,d3) -> initialize(0x1,d2) -> "
                 "EXC-UNCAUGHT-TOP at se.tube42.p9.android.MainActivity.onCreate(0x15,d1) "
                 "[APP-BOUNDARY]. Screen: TWO_COLOR uniq=2 text_px=0 (§16 blank face). "
                 "S80 precedent: com.emmanuelmess.tictactoe libGDX GL/EGL frontier. "
                 "Fanout: any libGDX AndroidApplication.initialize game (P9 + future corpus games)."),
    "producer": "com.badlogic.gdx.backends.android.AndroidGraphics.createGLSurfaceView",
    "consumer": "libGDX games' MainActivity.onCreate",
    "law_needed": ("GLSurfaceView/EGL surface creation shadow: AndroidApplication.initialize "
                   "contract -> AndroidGraphics -> GLSurfaceView(EGL14/EGLDisplay or stub "
                   "GL surface) -> GL10 rendering hook, or an honest deterministic "
                   "GL-unavailable surface placeholder with documented boundary."),
}

d = json.load(open(REG))
roots = d["roots"]
if not any(r.get("id") == "F-NEW-157" for r in roots):
    roots.append(entry)
d["count"] = len(roots) if "count" in d else d.get("count")
json.dump(d, open(REG, "w"), indent=1)
print("registry roots:", len(roots), "(F-NEW-157 registered)")

# fanout: P9 record points at F-NEW-157 (+156 family), not generic-only
s82 = json.load(open(S82))
for t in s82["TITLES"]:
    if t["TITLE_ID"] == "MAND-001":
        t["F_IDS"] = ["F-NEW-156", "F-NEW-157"]
        t["FIRST_FAILING_METHOD"] = ("com.badlogic.gdx.backends.android."
                                     "AndroidGraphics.createGLSurfaceView NPE -> "
                                     "MainActivity.onCreate [APP-BOUNDARY]")
        t["PRODUCER"] = "libGDX AndroidGraphics (EGL/GLSurfaceView chain)"
        t["CONSUMER"] = "se.tube42.p9.android.MainActivity.onCreate"
        t["OBSERVED"] = ("TWO_COLOR blank face (uniq=2, text_px=0). onCreate NPE unwind: "
                         "libGDX AndroidApplication.initialize -> AndroidGraphics."
                         "createGLSurfaceView NullPointerException escapes app boundary. "
                         "8 frames painted but no game UI inflated (§16 blank-face law).")
json.dump(s82, open(S82, "w"), indent=1)
print("P9 record updated with F-NEW-157 attribution")
