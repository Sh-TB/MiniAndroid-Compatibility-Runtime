#!/usr/bin/env python3
"""loading_exec_report.py — post the LOADING-CAMPAIGN implementation wave
completion ledger to issue #354 (CODER_REQUEST_PROTOCOL ledger format)."""
import json, subprocess, sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None


def gh(path, body=None, method="GET"):
    import urllib.request
    url = f"https://api.github.com/repos/{REPO}/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token()}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


BODY = """## LOADING-CAMPAIGN implementation wave — AUDIT → IMPLEMENTATION → RUNTIME PROOF → WORKING/FAILING COMPARISON → REGRESSION (completion ledger)

Commit `81134ac5` (rebased on the new Coder-protocol HEAD). **No app-specific code; no package conditionals; every law AOSP-cited; no fake-success.** This comment follows the CODER_REQUEST_PROTOCOL ledger format (STATUS + one-line result + evidence per numbered requirement).

### Completion ledger

| # | Requirement | STATUS | Result + evidence |
|---|---|---|---|
| 1 | ONE canonical path law (§5) — /data/data ≡ /data/user/0, user/<id>, user_de, /data/app, /storage/emulated/0, /system, device nodes; DENIED for anything else; every consumer routed | **IMPLEMENTED+TESTED** | `Storage::resolve_android_path` (data_root.h/.cpp) consumed by File family, streams, openInputStream, BitmapFactory (decodeFile/openFd/PFD), prefs, SQLite authority; probe asserts `alias-exists=true`, `abs-ok=true` |
| 2 | Host-escape closure (§6) with BEFORE/AFTER /dev/urandom probe | **IMPLEMENTED+TESTED** | BEFORE (audit): urandom raw SUCCESS = escape. AFTER: `/etc/hostname` → `FileNotFoundException` (EACCES face), `/etc` exists=false/mkdirs=false, `/home` list=null; `/dev/urandom` remains ALLOWED (AOSP sepolicy appdomain urandom_device r_file_perms — it is NOT a violation on real Android) with a bounded raw-read law; probe `host-deny=FNFE-HONEST`, `urandom-read=OK` |
| 3 | File/Context write family (§4): FileOutputStream/FileWriter, openFileOutput/openFileInput/fileList/deleteFile, File delete/renameTo/length/isFile/lastModified/list/listFiles | **IMPLEMENTED+TESTED** | probe `write-length=14` (hello-probe-42 on store), `ren-dst-length=13`, `deleteFile-again=false` (honest), `fileList-has-probe=1`; `/tmp/miniandroid/files` fallback DELETED |
| 4 | AssetManager real (§7): open existing/missing/nested/large/list/openFd/AFD-stream | **IMPLEMENTED+TESTED** | missing → `FileNotFoundException` (both open sites unified, R-1 closed); `asset-list-has-text=1` + nested; `openFd off=7417 len=75`, AFD stream bytes == entry bytes (PNG magic `89 50`); popen(unzip) REMOVED (in-process ZIP, R-5 closed); 4MiB fake-EOF REMOVED (256MiB honest refusal + char-device law) |
| 5 | Stream+FD layer (§10) | **IMPLEMENTED+TESTED** | PFD open/getFd/dup/close on REAL host fds; AFD createInputStream; openRawResourceFd (stored-only law); `read(byte[]) ≡ read(b,0,b.length)` fill law (probe-discovered divergence D-1) |
| 6 | decodeStream/decodeFile (§9) | **IMPLEMENTED+TESTED** | engine-registered stream-bytes resolver drains open_assets_ (asset/file/apkfd) → decoder: `decodeStream=8x8`, `decodeFile=8x8` from probe bytes — bytes→decoder→Bitmap→view→pixels chain per 21-P0-6 |
| 7 | SharedPreferences (§13): atomic, escaped, commit-truth, remove/clear, restart | **IMPLEMENTED+TESTED** | atomic tmp+rename, XML escape/unescape round-trip (`prefs-esc=a<b>&c"d'e`), `commit()` returns real write outcome, remove/clear erase for real (`prefs-clear-killed-esc=1`, `prefs-post-clear=survived`) |
| 8 | Databases (§14): single authority + WAL | **IMPLEMENTED+TESTED** | competing `set_package_info` databases_dir setter REMOVED (ONE authority: set_context_package); real `PRAGMA journal_mode=WAL` on request — `-wal`/`-shm` files materialized on microtimer store; `probe_db.sqlite` persists |
| 9 | External storage (§15) | **IMPLEMENTED+TESTED** | write→close→restart→read through the ONE law; `ext-file-exists=true`, `ext-read` content match; decodeFile agrees on the same mapping |
| 10 | ContentProvider/URI (§16): provider installation stage | **IMPLEMENTED+TESTED (launch leg)** | manifest `<provider>` parse + `install_content_providers()` at bind entry on EVERY bind path (probe-proven default-Application early-return divergence D-4) → real DEX `<init>`+onCreate BEFORE Application.onCreate; `provider-ran=1`. content:// query/Cursor remains honest-MISSING (open frontier) |
| 11 | Intent.getData + ApplicationInfo identity (S-5/S-7/ST-11) | **IMPLEMENTED** | getData returns the recorded Uri; dataDir `/data/data/<pkg>`, credentialProtected, deviceProtected `/data/user_de/0`, processName, className seeded |
| 12 | Write→read→RESTART ×3 real packages + synthetic (§11) | **OBSERVED** | synthetic probe: prefs-runs **1→2→3** across 3 restarts on ONE store; real packages: opencalc `<pkg>_preferences.xml`, chess `chess_pgn.db`+`ChessPlayer.xml`, microtimer `app-data(-wal/-shm)`, unote `notes.db` persisted on stores (`docs/INSTALL_TREE_PROOF.jsonl`) |
| 13 | Package isolation + uninstall/reinstall (§12) | **PARTIAL** | isolation proven (`isolation-other-pkg=false`, per-package store law F-NEW-234/231); uninstall command remains PENDING (F-NEW-234 wave leftover) — reinstall-clean proof blocked on it |
| 14 | WORKING-vs-FAILING comparison (§1/§19/§20): why working apps worked | **OBSERVED** | `docs/WORKING_VS_FAILING_LOADING_MATRIX.jsonl` (8 rows) + `docs/WORKING_APP_LOADING_EXPLANATIONS.md` — trace-backed: opencalc=prefs+ARSC only; chess/microtimer/unote=SQLite (already real); telegram=existing-assets+prefs; **none exercised the voided P0 APIs** (ST-1/ST-2/R-2 zero hits in their traces) |
| 15 | White/grey screens: loading vs NOT-loading (§21) | **OBSERVED** | `docs/WHITE_SCREEN_LOADING_ROOTS.md` — sudoku/whatsapp = `WINDOW_ROOT` (NOT file bugs, F-NEW-233 verdicts); telegram frontier = `ACTIVITY_NAVIGATION`; the loading-caused class (silent-empty assets/configs, 0-byte decodes) proven by probe and CLOSED generically |
| 16 | Synthetic probes mandatory (§23) | **TESTED** | `fixtures/loading_probe` (aapt2+ECJ+D8, provider + 18 probe groups); gate `scripts/loading_probe_runner.sh` = **23/23 ALL PASS** (fixed a real gate bug: JSON `\\\"`-truncation faked 3 FAILs — D-7) |
| 17 | No fake success (§26) | **IMPLEMENTED** | every unsupported op = honest MISSING or the AOSP failure contract; loud diagnostics at every DENIED/EOF/refusal |
| 18 | Corpus regression (§27): goldens ×3 | **TESTED — ZERO DRIFT** | opencalc `e364b001ee7abd66` ×3, chess `b5a7a35d5fe0564b` ×3, dooz `d602648e8e401895` ×3, microtimer `da73010a37dd0189` ×3, unote `4f1a9e4e8f64fae8` ×3, telegram `bbb6cd10a834963d` ×1 — ALL byte-identical with the entire fix wave in (`scripts/working_vs_failing_probe.sh`) |
| 19 | Deliverables (§28) | **IMPLEMENTED** | WORKING_VS_FAILING_LOADING_MATRIX.jsonl, WORKING_APP_LOADING_EXPLANATIONS.md, LOADING_API_COVERAGE_MATRIX.jsonl (38 APIs), AUDIT_REQUIREMENT_COVERAGE.jsonl, INSTALL_TREE_PROOF.jsonl, LOADING_RUNTIME_TRACE.jsonl, LOADING_ROOT_FANOUT.md, LOADING_FAILURE_DIAGNOSTICS.md, WHITE_SCREEN_LOADING_ROOTS.md + loading_probe_runner.sh / working_vs_failing_probe.sh / storage_tree_proof.sh; FILE_RESOURCE_LOADING_COMPATIBILITY §9/§10; FINAL_COMPATIBILITY_CAMPAIGN §16; CAMPAIGN_STATE; registry R-NEW-457 (529→530) |
| 20 | Final answers (§30 A–M) | **OBSERVED** | A–E: per-app trace explanations (see #14 + explanations doc); F: probe first-divergences = the failing class; G: #1–11; H: coverage matrix open rows (native/dlopen, content:// query, splits, broadcasts/services, config/fonts); I/J: white-screen table (loading-caused vs not, with proof); K: YES — MINIANDROID_FILE_IO + F-NEW-233 verdict give first-missing per frame; L: YES — provenance classes (APK asset @ installed apk / sandbox file / external / db / prefs / framework / DENIED host); M: YES — consumption proven to bitmap pixels (decodeStream/decodeFile 8x8) and persisted-state reads (restart counter) |

### Probe-discovered NEW LAWS (registered, docs/LOADING_FAILURE_DIAGNOSTICS.md)

1. **read(byte[]) fill law** — the 2-arg overload fell to the single-byte law, leaving caller buffers unwritten (0-byte sinks feeding toByteArray/decodeFile chains).
2. **ByteArrayOutputStream family** (REC-MISS chain → null array → write REC-MISS).
3. **String(byte[]) materialization** onto the receiver via `__string_value__` (new-instance identity law).
4. **()J INT64 register-pair law** — File.length()/lastModified(), AFD getStartOffset()/getLength() answered INT32 → callers read 0 for real files.
5. **Char-device read law** — /dev/urandom bounded raw read (never fake-EOF, never hang).

### Honest frontier (NOT claimed)

S-2 native dlopen/JNI layer; S-4 content:// query/Cursor/FileProvider; S-11 split APKs; S-3/S-13 broadcasts/services lifecycle; SELECTION_FROZEN (config qualifiers/density/fonts); S-10 localStorage; ST-10 sqlite/font provenance traces; uninstall command (blocks the §12 reinstall leg). All listed in the coverage matrix with open roots.
"""

if __name__ == "__main__":
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 354
    res = gh(f"issues/{issue}/comments", {"body": BODY}, method="POST")
    print("POSTED comment id:", res["id"], "url:", res["html_url"])
