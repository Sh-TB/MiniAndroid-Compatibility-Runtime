#!/usr/bin/env python3
"""S222-B: anti-phantom verification of the 50 GP findings (#582 id 6812887007)
against CURRENT main source. Each row: grep for the claimed pattern; report
PRESENT / ABSENT / SUPERSEDED-FIXED (fix signature found)."""
import subprocess, re, os

BASE = "/home/z/my-project/miniandroid"
def grep(pattern, path, extra=()):
    """return True if pattern found in path (or path pattern across src)."""
    cmd = ["grep", "-rn", "-e", pattern, os.path.join(BASE, path)] + list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()][:3]

# (id, claim-pattern, file, fix-signature-pattern)
CHECKS = [
 ("APP-001", "execute_on_create", "src/runtime", "diagnostic"),
 ("APP-002", "run() not yet wired", "src/runtime", None),
 ("APP-003", "onStart", "src/runtime/application_runtime.cpp", None),
 ("APP-005", "LoginActivity", "src/runtime/application_runtime.cpp", None),
 ("APP-006", "gotNextPage", "src", None),
 ("APP-007", "LoginActivity", "src/runtime/application_runtime.cpp", None),
 ("APP-008", "clickable", "src/dex/dalvik_engine.cpp", None),
 ("APP-009", "TextWatcher", "src/dex/dalvik_engine.cpp", "dispatch_text_watcher"),
 ("APP-010", "256", "src/dex/dalvik_engine.cpp", None),
 ("INPUT-001", "rotation", "src/framework/touch_dispatcher.cpp", None),
 ("INPUT-002", "hit", "src/framework/touch_dispatcher.cpp", None),
 ("INPUT-003", "100000", "src/framework/touch_dispatcher.cpp", None),
 ("INPUT-004", "was_in_tap_region", "src/framework/gesture_detector_shadow.cpp", None),
 ("SCROLL-001", "420", "src/framework/scroller_shadow.h", None),
 ("SCROLL-002", "sqrt", "src/framework/scroller_shadow.h", None),
 ("ANIM-001", "duration", "src/framework/animator_shadow.cpp", None),
 ("ANIM-003", "addListener", "src/framework/animator_shadow.cpp", None),
 ("ANIM-004", "playTogether", "src/framework/animator_shadow.cpp", None),
 ("GL-001", "glSurfaceCreated", "src/dex/dalvik_engine.cpp", None),
 ("GL-004", "glRenderMode", "src/gles/gl_surface_shadow.cpp", None),
 ("GL-005", "requestRender", "src/gles/gl_surface_shadow.cpp", None),
 ("GL-006", "glQueuedEvent", "src/gles/gl_surface_shadow.cpp", None),
 ("GL-008", "setFixedSize", "src/gles/surface_view_shadow.cpp", None),
 ("GL-009", "setZOrderOnTop", "src/gles/surface_view_shadow.cpp", None),
 ("GL-010", "GL_NO_ERROR", "src/gles/gl_surface_shadow.cpp", None),
 ("GL-011", "read_array_elems", "src/gles/gl_surface_shadow.cpp", None),
 ("GL-012", "gl_view_mirror_write", "src/gles/gl_surface_shadow.cpp", None),
 ("WEB-001", "createObjectURL", "src/webview/webview_engine.cpp", None),
 ("WEB-002", "readAsDataURL", "src/webview/webview_engine.cpp", None),
 ("WEB-003", "Worker", "src/webview/webview_engine.cpp", None),
 ("WEB-004", "createOscillator", "src/webview/webview_engine.cpp", None),
 ("WEB-005", "captureStream", "src/webview/webview_engine.cpp", None),
 ("WEB-007", "pushState", "src/webview/webview_engine.cpp", None),
 ("WEB-008", "setLineDash", "src/webview/webview_engine.cpp", None),
 ("WEB-009", "clip", "src/webview/canvas2d.cpp", None),
 ("WEB-010", "strokeText", "src/webview", None),
 ("WEB-011", "stroke_text", "src/webview/canvas2d.cpp", None),
 ("AUDIO-001", "SoundPool", "src/audio/audio_engine.cpp", None),
 ("AUDIO-002", "AudioTrack", "src/audio/audio_engine.cpp", None),
 ("AUDIO-003", "MediaPlayer", "src/audio/audio_engine.cpp", None),
 ("RES-001", "shape", "src/resources/layout_inflater.cpp", "ShapeDrawable"),
 ("RES-003", "ValueAnimator", "src/framework/animator_shadow.cpp", None),
]

print(f"{'ID':12s} {'STATUS':12s} evidence")
for fid, pat, path, fixsig in CHECKS:
    hits = grep(pat, path)
    status = "ABSENT" if not hits else "PRESENT"
    ev = hits[0][:110] if hits else ""
    if fixsig:
        fhits = grep(fixsig, path)
        if fhits:
            status += "+FIXED"
    print(f"{fid:12s} {status:12s} {ev}")
