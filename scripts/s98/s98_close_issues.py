#!/usr/bin/env python3
"""s98_close_issues.py — close MG issues with evidence comments (env-token law).

Usage: GH_TOKEN=... python3 s98_close_issues.py <batch>
  batch 'text'    -> MG-051,073,080-085 (commit 4ac6c542)
  batch 'layout'  -> MG-123..129       (commit 62ef579f + test commit)
"""
import json
import os
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = os.environ.get("GH_TOKEN", "")
ROOT = "/home/z/my-project"
HDR = {"Authorization": f"Bearer {TOKEN}",
       "Accept": "application/vnd.github+json",
       "User-Agent": "miniandroid-s98-closer"}

EVIDENCE = {
    "MG-051": ("CJK fallback face load + fallback-chain law",
               "REAL BUG: the R-NEW-398 CJK fallback ROUTING was wired but the "
               "WenQuanYi Zen Hei FACE WAS NEVER LOADED — cjk_available_ could "
               "never become true, so every CJK ideograph stayed .notdef "
               "(silent draw-skip class). Fix: face loaded with the base faces "
               "(text_shaper.cpp). Fence: s98 text battery T1/T2 — "
               "shape(\"AΩЖ中\") → notdef==0 through the fallback chain."),
    "MG-073": ("ellipsize IMPLEMENTED (TextUtils.TruncateAt law)",
               "REAL GAP: ellipsize did not exist anywhere in the runtime. "
               "Implemented: android:ellipsize AXML attr (start/middle/end/"
               "marquee ordinals) → ViewNode → fonts::layout_text (single "
               "source of truth with the measure pass) truncates the over-wide "
               "last line with U+2026 for END/START/MIDDLE; maxLines==1 "
               "singleLine NO-WRAP law added (a word-wrap silently dropped "
               "every word past the overflow). Fence: battery stage "
               "'s98 text laws' T3-T7+T14 (END keeps head / START keeps tail / "
               "MIDDLE keeps both / NONE preserved / cap drops segment / "
               "empty box)."),
    "MG-080": ("combining marks shape law",
               "Fence: battery T8 — \"cafe\\u0301\" (e + U+0301) shapes with "
               "finite width and the mark attached to its base cluster."),
    "MG-081": ("RTL first-strong direction law",
               "Fence: battery T9 — Persian سلام shapes with rtl_base==true "
               "via FriBidi first-strong detection."),
    "MG-082": ("Arabic joining advance law",
               "Fence: battery T10 — width(دد joined) < width(د د spaced): "
               "HarfBuzz produces connected forms, not isolated glyphs."),
    "MG-083": ("emoji-presentation claim law",
               "REAL BUG: the emoji block ran only when notdef_count>0, but "
               "DejaVu maps U+1F600 to a bogus non-notdef glyph (gid 5857) "
               "that swallowed the emoji slot. Fix: emoji face claims "
               "Default_Emoji_Presentation codepoints per the AOSP fonts.xml "
               "chain independent of .notdef. Fence: battery T11."),
    "MG-084": ("surrogate pair single-cluster law",
               "Fence: battery T12 — U+1F600 (UTF-16 surrogate pair as UTF-8) "
               "shapes to exactly ONE emoji cluster, never two halves."),
    "MG-085": ("UTF-8/UTF-16 boundary + phantom-NUL REAL-BUG fix",
               "REAL BUG: hb_buffer_add_utf32 was fed vis.size()=N+1 while "
               "log2vis fills only N entries — a PHANTOM U+0000 cluster rode "
               "at the end of EVERY shaped string (extra .notdef glyph, "
               "garbage advance in every TextView width corpus-wide, emoji "
               "fallback occasionally attaching to the NUL cluster). Fix: "
               "shape exactly src.size(). Fence: battery T13 — mixed "
               "1/2/3/4-byte string keeps cluster count == codepoint count."),
    "MG-123": ("scroll offsets IMPLEMENTED (View.java L14600+ law)",
               "REAL GAP: scrollTo/scrollBy/getScrollX/getScrollY did not "
               "exist. Implemented: ViewShadow dispatch (scrollTo sets, "
               "scrollBy adds, getters read), ViewNode scroll_x/y, and the "
               "draw-walk content law: child origin = untranslated + "
               "Σancestor translations − Σancestor scrolls (cumulative "
               "RenderTask off_tx/ty/off_sx/sy). Fence: battery stage 's98 "
               "scroll/transform laws' T1-T3,T8 (state/accumulate/defaults/"
               "walk inputs)."),
    "MG-124": ("translationX property + draw-walk law",
               "setTranslationX/getTranslationX (default 0, View.java "
               "mTransformationInfo) + the translation shifts self+subtree "
               "in the draw walk (pop-time origin shift, push-time cumulative "
               "delta). Fence: battery T4a/T4b + T8."),
    "MG-125": ("translationY property + draw-walk law",
               "setTranslationY/getTranslationY + walk delta (same law as "
               "translationX). Fence: battery T4b + T8."),
    "MG-126": ("scaleX property law",
               "setScaleX/getScaleX with the View.java default 1 (state + "
               "getters live; matrix render application on the axis-aligned "
               "walk is the recorded frontier, tracked in the registry). "
               "Fence: battery T5a/T5b."),
    "MG-127": ("scaleY property law",
               "setScaleY/getScaleY (default 1). Fence: battery T5a/T5b."),
    "MG-128": ("rotation property law",
               "setRotation/getRotation (default 0°). Fence: battery T6a/T6b."),
    "MG-129": ("pivot property law",
               "setPivotX/Y + getPivotX/Y. Fence: battery T7."),
}


def api(path, payload=None, method=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=HDR,
                                 method=method or ("POST" if data else "GET"))
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
        return json.loads(body) if body else {}


def main():
    batch = sys.argv[1] if len(sys.argv) > 1 else "text"
    mg_list = (["MG-051", "MG-073"] + [f"MG-{i:03d}" for i in range(80, 86)]
               if batch == "text"
               else ["MG-123"] + [f"MG-{i:03d}" for i in range(124, 130)])
    imap = json.load(open(f"{ROOT}/scripts/s98/issue_map.json"))["issues"]
    for mg in mg_list:
        n = imap.get(mg)
        if not n:
            print(f"skip {mg}: no issue"); continue
        title, body = EVIDENCE[mg]
        comment = (f"**CLOSED — S98 micro-gap batch ({batch})**\n\n"
                   f"**Fix**: {title}\n\n{body}\n\n"
                   f"- Commits: 4ac6c542 (text) / 62ef579f+3ac93d34 (layout)\n"
                   f"- Battery: canonical battery ALL PASS at the closing "
                   f"HEAD; new named stages 's98 text laws (expect 21)' and "
                   f"'s98 scroll/transform laws (expect 13)' green\n"
                   f"- Registry: docs/MICRO_GAP_REGISTRY.json statuses "
                   f"updated to CLOSED with before/after + evidence")
        api(f"issues/{n}/comments", {"body": comment})
        api(f"issues/{n}", {"state": "closed"}, method="PATCH")
        print(f"closed #{n} ({mg})")
    print("DONE", batch)


if __name__ == "__main__":
    main()
