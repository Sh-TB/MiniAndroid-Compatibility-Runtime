#!/usr/bin/env python3
"""CONT-95: register F-NEW-397 (SAX stream-bytes dead registry) as
ROOT-CAUSED-FIXED, mirror to canonical/, bump totals."""
import json, hashlib, shutil

REG = "root_registry.json"
CANON = "canonical/root_cause_registry.json"

with open(REG) as f:
    r = json.load(f)

row = {
    "id": "F-NEW-397",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "title": "org.xml.sax XMLReader.parse resolved stream bytes from a registry NO site ever populated — every stream-backed SAX parse delivered 0 events to the app's own ContentHandler",
    "layer": "framework/xml-sax",
    "root_cause": "XMLReader.parse(InputSource) read its document bytes from the static s109_stream_bytes map (dalvik_engine.cpp ~38448). Ground truth: that map had exactly three references in the whole engine — the declaration and two reads — and NO write site ever existed. Every parse over a stream-backed InputSource therefore saw bytes=0 (log '[S109-SAX] parse: no handler (yes) or bytes (0)') and the app's ContentHandler received zero events while parse() returned void normally (silent no-op). Ground-truth casualty chain (Telegram 12.10.5 vc71059, Night-theme boot, pref state theme=Night): SvgHelper (org.telegram.messenger.SvgHelper, pure-Java SAX client) pattern decode got 0 events -> MotionBackgroundDrawable (obfuscated Lorg/telegram/ui/Components/yc0;) field u held a degenerate bitmap (non-null, 0x0) -> o6.I (wallpaper build, decode verified: unit 951 invoke-static Bitmap.createBitmap(w,h,ARGB_8888) with w/h = u.getWidth()/getHeight() guarded by if-nez u at unit ~911) called createBitmap(0,0) -> S109-CB-IAE IllegalArgumentException (AOSP law CORRECT: w<=0 must throw) -> RAW DEX TRY-TABLE PARSE (scripts/cont95_raw_try_generic.py, androguard-independent) proves NO try coverage at o6.I unit 951 (8 tries, all end <= 873) AND LaunchActivity.onCreate unit 1375 (4 tries, all end <= 1107) -> unwind to APP-BOUNDARY -> LaunchActivity.onCreate killed -> white frame (1431 status-bar px pre-fix fresh; 0 px with the 30s wall consumed mid-parse). The DAY-theme archived CONT-94 face avoided the branch (different wallpaper path) which is why the regression only surfaced on the Night/pref-state boot.",
    "fix": "ONE law, zero app conditionals (dalvik_engine.cpp, XMLReader.parse block): when s109_stream_bytes has no entry, resolve the stream through the ONE asset-byte law already serving InputStream.read — resolve_asset_stream(stream_oid, path, pos) then cached_asset_bytes(path) (GATE A openRawResource registers 'apk-entry:res/<name>' keys; the apk-entry branch extracts REAL ZIP bytes). The app's own SAX tokenizer dispatch (already fully implemented: minimal XML tokenizer + startElement/endElement/Attributes dispatch into the app's DEX handler) then runs unchanged.",
    "evidence": {
        "fixture": "com.probe.sax1 (fixtures/cont95_sax_probe; apk run/cont95/sax1.apk sha16 2d8c7e72afbb2229; build scripts/cont95_build_probe.sh — real aapt2 compile/link + ECJ + D8 with a res/raw SVG)",
        "fixture_ab": "PRE (binary 7cf6fe7f3d6abb81): '[SAX1] events=0/0 root=?x? names= err=none verdict=FAIL' (run/cont95/sax1_pre). POST (binary aa9ade61b147c12b): '[SAX1] events=6/6 root=1080x1920 names=svg,g,path,path,rect,circle err=none verdict=PASS' (run/cont95/sax1_final2).",
        "real_apk": "upload/telegram_official.apk (org.telegram.messenger.web 12.10.5 vc71059, sha16 e37aced2a49c1dbb): pre-fix 'parse: no handler (yes) or bytes (0)' + createBitmap(0,0) IAE at o6.I -> APP-BOUNDARY boot death; post-fix '[S109-SAX] parse OK: 746 elements -> Lorg/telegram/messenger/SvgHelper$SVGHandler; (507258 bytes)' — the app's OWN SVG handler executed 4.7M API calls of real DEX work, boot reaches onStart/onResume, 6 uncaught (named billing/native/firebase boundaries only), 0 createBitmap IAE (run/cont95/tg_post_240s, tg_post_s94state).",
        "decode_scripts": ["scripts/cont95_raw_try_generic.py (androguard-independent raw try/handler probe)", "scripts/cont95_decode_o6I.py", "scripts/cont95_o6I_disasm.py", "scripts/cont95_decode_o6_full.py"],
    },
    "honest_notes": "THREE named residuals, none hidden: (1) THROUGHPUT — the 507KB pattern SVG costs the DEX interpreter ~12.6M+ instructions (SvgHelper$ParserHelper char loops); the 30s canonical gate cuts it mid-parse with the HONEST F084 wall-stop (322 VME rows pre-bump run), boot completes at --max-seconds 240 (0 WALL-STOP). This is the CONT-87 Track 3 frontier with a concrete face, NOT fixed by this wave. (2) The F084 wall-stop currently re-fires per check while the parse loop runs (319 VirtualMachineError rows at 30s) — recorded, not changed. (3) The login-content render gap (CONT-88 T3 bounds/offset) and LOC_ERR string-resource faces (CONT-88 T6) are UNCHANGED by this fix — the app state after the fix is a rendered low-power sheet (Night/pref path) or pre-login (fresh), both honest. The engine adds NO SVG semantics of its own (AOSP org.xml.sax is a generic contract).",
    "binary_after": "aa9ade61b147c12b",
    "binary_before": "7cf6fe7f3d6abb81",
    "wave": "CONT-95",
}

existing = [x for x in r["roots"] if x.get("id") == "F-NEW-397"]
if existing:
    r["roots"] = [row if x.get("id") == "F-NEW-397" else x for x in r["roots"]]
else:
    r["roots"].append(row)
r["total"] = len(r["roots"])

out = json.dumps(r, indent=1, ensure_ascii=False)
with open(REG, "w") as f:
    f.write(out)
shutil.copyfile(REG, CANON)

sha = hashlib.sha256(out.encode()).hexdigest()[:16]
print(f"registry roots={r['total']} sha16={sha} F-NEW-397 registered")
