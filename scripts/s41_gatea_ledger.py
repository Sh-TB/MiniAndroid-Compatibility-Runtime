#!/usr/bin/env python3
"""Post the GATE A (issue #370) completion ledger — 34 rows,
STATUS | RESULT | EVIDENCE | CURRENT HEAD | TEST COUNT."""
import subprocess, json, urllib.request, sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
out = subprocess.run(["git", "credential", "fill"],
                     input="protocol=https\nhost=github.com\n\n",
                     capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = [l.split("=", 1)[1] for l in out.splitlines() if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json", "User-Agent": "gatea"}

HEAD = "24326b44d2a5a1fd4ace6993578a0e9d477e56a8"
HEAD8 = HEAD[:8]
BIN = "768085b1207ad55d"
BATTERY_OK = "BATTERY GATE: ALL PASS (121 stages)" in open(
    "/home/z/my-project/run/gatea_battery_v3.log").read()

rows = [
(1, "laws read", "VERIFIED",
 f"CONSTITUTION_V2 + CODER_REQUEST_PROTOCOL + ONE-path law (data_root.h) + F-NEW-231/234/R-NEW-457 re-verified at CURRENT HEAD {HEAD8}; recorded in docs/INSTALL_ENVIRONMENT_CAPABILITY_GATE.md §1", ""),
(2, "install identity", "TESTED",
 "install commits base.apk copy-then-record with SHA integrity; record + live re-hash match on all 5 apps", "multi_app_proof.json shaMatch=true x5"),
(3, "source APK hiding", "TESTED",
 "source moved away after install; identity = package + data-root only; no source fallback exists (F-NEW-231)", "5/5 source_hidden=true"),
(4, "PackageManager", "TESTED",
 "getPackageInfo identity + GET_PROVIDERS providers array (authority singular field law) + provider attachInfo(Context,ProviderInfo) stage", "probe ID-04 + PROV-01 PASS"),
(5, "Context paths", "TESTED",
 "13-API dir family incl. NEW getDataDir/getCodeCacheDir/getNoBackupFilesDir/getFileStreamPath/databaseList/getObbDir; logical-path law (host spelling removed from app visibility)", "probe DIR-01..12 PASS"),
(6, "File APIs", "TESTED",
 "exists/isFile/isDirectory/canRead/canWrite/length(J)/list/listFiles/mkdir/mkdirs/createNewFile/delete/renameTo/abs/canonical/getName/isAbsolute", "probe FILE-01..11 PASS; lastModified=0 documented determinism law (INFO)"),
(7, "streams", "TESTED",
 "read/read(byte[])/read(off,len)/EOF=-1/available/skip/write(int)/write(byte[])/write(off,len)/flush/close/append; MODE_APPEND bit law FIXED 0x8000 (was 0x0800 trunc bug)", "probe IO-01..10 PASS"),
(8, "FD/PFD/AFD", "TESTED",
 "real host fds: openFd(stored)→AFD offset+declaredLength (NEW field law); AFD.createInputStream/getFileDescriptor; PFD.open/dup/close/getFd; compressed entries → AOSP FNFE (honest)", "probe FD-01..07 PASS/INFO; byte-equality residual = gap G-5"),
(9, "AssetManager", "TESTED",
 "list/open/openFd; stored+deflate; missing → FNFE; ASSETS-WITHOUT-ARSC law re-verified; provenance per access", "probe ASSET-01..05 PASS (list contains residual = gap G-6)"),
(10, "resources", "TESTED",
 "ARSC inventory + getIdentifier ANY type (R-4 FIXED, probe 0x7f030000) + getString NotFoundException (R-3 fake-'' REMOVED) + openRawResource real bytes via apk-entry law (was unreadable stream)", "probe RES-01..04 PASS"),
(11, "image/font/media inventory", "IMPLEMENTED",
 "pkginspect media section: class/size/method/expected-decoder per entry; decode exercised by probe IMG-01..03", "probe IMG PASS x3"),
(12, "SharedPreferences", "TESTED",
 "5 types + string-set + escaping (<&>) + commit truth + remove/clear + restart counter", "probe PREF-01..06 PASS (restart 1→2→3)"),
(13, "SQLite", "TESTED",
 "openOrCreateDatabase (NEW one-open-path law) + helper lifecycle + rawQuery cursor + databaseList sidecar filter + real db/WAL files + restart growth", "probe DB-01..03 PASS"),
(14, "external storage", "TESTED",
 "getExternalFilesDir create+write+read; getExternalCacheDir; getExternalMediaDirs; getObbDir (NEW); physical backing under virtual /storage/emulated/0", "probe DIR-09..12 PASS"),
(15, "URI/provider", "PARTIAL",
 "provider identity/install stage/attachInfo/authority PROVEN; content:// query-Cursor dispatch NOT implemented (loud, not silent) — gap G-3", "probe PROV-01 PASS; N-12 boundary row"),
(16, "native inventory", "TESTED",
 "pkginspect libs: ELF class/machine/SONAME/JNI dynsym (chess: 4 .so, aarch64+arm+x86, 61 JNI exports); loadLibrary honest UnsatisfiedLinkError with request→ABI→entry trace (fake success KILLED)", "probe NAT-01/02 PASS"),
(17, "manifest/components", "IMPLEMENTED",
 "activities(+actions)/services/receivers (NEW parse)/providers/permissions/meta-data/features/application; launchability answerable without rendering", "pkginspect manifest sections; multi-app rows"),
(18, "DEX/multidex", "IMPLEMENTED",
 "per-classesN.dex counts + native methods + class sample (flags/super); correlation via caller fields in file-io trace", "chess 1912 classes/57 native methods; blockblast 633"),
(19, "provenance graph", "IMPLEMENTED",
 "SOURCE_APK→INSTALL→INSTALLED_BASE_APK→{MANIFEST,DEX,RESOURCES,ASSETS,LIBS,APP_DATA}; every data file carries physical backing + provenance class", "pkginspect provenance + PROVENANCE_SCHEMA.jsonl"),
(20, "agent CLI/API", "IMPLEMENTED",
 "miniandroid pkginspect --what a,b,c --jsonl <out> [--apk direct-mode]; machine-readable JSON + JSONL streams", "docs/INSTALL_ENVIRONMENT_AGENT_GUIDE.md"),
(21, "universal trace", "IMPLEMENTED",
 "INSTALL_REQUEST→…→FIRST_DIVERGENCE 20-stage chain with typed results (SUCCESS/FAILURE/MISSING/DENIED/UNSUPPORTED) + MINIANDROID_FILE_IO per-op trace", "PROVENANCE_SCHEMA.jsonl"),
(22, "synthetic probe", "TESTED",
 "fixtures/gate_a_probe: real aapt2 APK, normal APIs, per-op try/catch, results via openFileOutput (physical proof); identity/dirs/file/stream/FD/assets/res/img/prefs/SQLite/external/provider/native/isolation/restart", "69 PASS / 0 FAIL / 2 INFO (documented laws)"),
(23, "multi-app proof", "TESTED",
 "5 families incl. mandatory render-FAIL case — inspection identical whether or not the app renders", "simple/chess(game-adjacent storage)/bouncy/memory/blockblast: 5/5 complete (multi_app_proof.json)"),
(24, "negative tests", "TESTED",
 "nonexistent package/file/asset/resource, closed+invalid FD, cross-package, traversal, host absolute, malformed APK x3, missing lib, invalid DB, missing prefs — all typed honest failures", "17/17 PASS (NEGATIVE_TESTS.jsonl)"),
(25, "isolation", "TESTED",
 "cross-package path exists()==false; traversal denied; host /etc denied + FNFE; store-level inspection scoped to requested package", "probe ISO-01..04 + N-11 PASS"),
(26, "restart", "TESTED",
 "write → physical file → restart → read same value (prefs counter + SQLite rows + files)", "probe runs 1→2→3; reinstall matrix"),
(27, "uninstall", "TESTED",
 "codePath + record + internal + 3 external trees removed; NOT_INSTALLED exit-2 honesty", "uninstall gate 16/16 + matrix rows"),
(28, "reinstall", "TESTED",
 "clean namespace (no leftover state), fresh app state per AOSP semantics", "reinstall matrix 8/8"),
(29, "current HEAD/build identity", "VERIFIED",
 f"HEAD {HEAD}; runtime binary sha16 {BIN}; evidence scripts persisted under scripts/s41_gatea_*.py", "git rev-parse HEAD"),
(30, "machine-readable evidence", "IMPLEMENTED",
 "9 canonical artifacts + harness JSON/JSONL + file_io.jsonl traces", "docs/INSTALL_ENVIRONMENT_*.jsonl/md"),
(31, "fake-success audit", "PASS",
 "probe found 11 divergences (host-path exposure, provider authority/attachInfo, obbdir, getIdentifier, NotFound, loadLibrary, MODE_APPEND trunc, AFD declaredLength, raw stream, PFD args, manifest components) — ALL fixed generically before any claim; remaining 3 gaps are loud, recorded, severity-ranked", "CAPABILITY_GATE.md §2; GAPS.md"),
(32, "final gap inventory", "PARTIAL",
 "8 gaps enumerated with API/law→impl→AOSP→evidence→families→severity→next action (G-3 content:// query MEDIUM, G-5 AFD byte-equality MEDIUM, G-6 array String equality LOW-MED, others LOW/document-deviation)", "docs/INSTALL_ENVIRONMENT_GAPS.md"),
(33, "capability percentage", "OBSERVED",
 "denominator = 60 API-matrix rows: 57 TESTED/PASS, 3 PARTIAL → ~95%; percentage NOT used as a completion claim", "API_MATRIX.jsonl"),
(34, "final honest status", "PARTIAL",
 "GATE A OPERATIONAL: install→hide→inspect→trace→provenance complete and machine-readable; 3 open gaps (G-3/G-5/G-6) keep strict PARTIAL — GATE B (render) and GATE C (visual) explicitly NOT claimed", "this ledger"),
]

lines = [f"## GATE A completion ledger — HEAD `{HEAD8}` (binary `{BIN}`)",
         "",
         f"Every row: STATUS | RESULT | EVIDENCE (— TEST COUNT where the row ran a test).",
         f"Regression gates at this HEAD: user pixel goldens **4/4 REAL_APP_CONTENT**, determinism anchors **5/5 ×3 byte-identical** (chess/dooz determinism-only), loading probe **23/23**, uninstall **16/16**"
         + (f", canonical battery **121/121 ALL PASS** (run/gatea_battery_v3.log)." if BATTERY_OK else "; canonical battery re-run in progress (log: run/gatea_battery_v3.log)."),
         ""]
for n, title, status, result, ev in rows:
    evtxt = f" — TEST COUNT/EVIDENCE: {ev}" if ev else ""
    lines.append(f"{n}. **{title}** — STATUS: {status}. RESULT: {result}. EVIDENCE: {evtxt}")

lines.append("")
lines.append("Final engineering question (issue text): **YES** for every inspection surface in the matrix above — "
             "an agent given an installed package identity can determine what exists, what was attempted, what "
             "physical backing was used, what failed, and the first missing capability, without guessing, with the "
             "3 named gaps (G-3/G-5/G-6) the only remaining inspection deltas, each with a next action in "
             "docs/INSTALL_ENVIRONMENT_GAPS.md. GATE B/C rendering is explicitly outside this ledger.")

body = "\n".join(lines)
req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/370/comments",
    data=json.dumps({"body": body}).encode(),
    headers={**HDRS, "Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req) as r:
    res = json.loads(r.read())
print("posted:", res["html_url"])
