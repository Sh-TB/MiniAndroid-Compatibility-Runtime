#!/usr/bin/env python3
"""laudit_post_comment.py — post the FILE/RESOURCE/MEDIA LOADING AUDIT wave report to issue #354."""
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


BODY = """## LOAD-AUDIT wave — FULL FILE/RESOURCE/MEDIA LOADING AUDIT delivered (audit-only phase, zero app-specific code)

Directive executed: the triple-attached audit campaign (INSTALLED-APP FILESYSTEM P0 + SUPPLEMENT FILE/RESOURCE/MEDIA §0–44 + ULTIMATE AUDIT §0–148). **No code changed; no package-specific anything; registry untouched this phase (audit-only).** Commit `26e03696` pushed.

### 1. Source census (ULTIMATE §1 — SOURCE_FILE_CENSUS)

**164 files / 137,756 lines** audited; the real build graph is the Makefile (**64 TUs compiled**). Dead code found and documented: **13 dead .cpp (8,164 lines)**; `audio_engine.cpp` + `gles20_bridge.cpp` are compiled-but-zero-caller; CMakeLists references **6 nonexistent files** (stale); `docs/foundation/source_inventory.json` is actually an APK ledger, not an inventory.

### 2. SPLIT-BRAIN VERDICT (ULTIMATE §3 WORLD A vs WORLD B) — PROVEN

**Canonical production run path = WORLD B**: `cmd_run → ExecutionEngine → DalvikExecutionEngine`. WORLD A (`ApplicationContext`/`FileSandbox`/`api` SharedPreferences) is **test-only, unreachable** from the APK run path; `ApplicationRuntime` is megabatch-only legacy. The APK-visible Context is a **DEX-heap object served by `bridge_to_api`** (proven at runtime, not by class name). `ResourceRuntime` is a **process-wide singleton** re-initialized only on `apk_path` change (cross-package pollution risk documented as finding).

### 3. Deliverables (all pushed)

| File | Content |
|---|---|
| `docs/REAL_ANDROID_LOADING_ORACLE.md` | AOSP semantic oracle: 14 subsystem law families (AssetManager2, ResourcesImpl, fonts, bitmaps, audio, files, SQLite, prefs, native libs, URIs, services, components, splits, threads) + the 12 universal questions answered from AOSP sources |
| `docs/FILE_RESOURCE_LOADING_COMPATIBILITY.md` | full MiniAndroid-vs-oracle diff matrix: **38 structural roots in 7 fan-out families** + WE-FORGOT-THIS 20 items + the live-proof table + the required §8 final answers |
| `docs/LOAD_COMPATIBILITY_MATRIX.jsonl` | 36 machine-readable layer rows (layer → law → MiniAndroid status → root) |
| `scripts/load_audit_proof.sh` | reproducible installed-identity + provenance proof suite |

### 4. Top P0 structural findings (54 line-cited findings; the class that matters)

1. **P-1**: `File.getAbsolutePath()` hijacked by the EXP-043 stub → constant `/tmp/miniandroid/files` (dalvik_engine.cpp:38652 shadows the real law at 39908; the F-NEW-234 branch is unreachable from the hijack site).
2. **P-2**: `FileOutputStream` / `openFileOutput` / `openFileInput` / `fileList` / `deleteFile` **do not exist** — the whole write path is void.
3. **R-1**: `AssetManager.open()` fake-success — 3 duplicate sites, no FileNotFoundException contract.
4. **FD family void**: `openFd/openRawResourceFd/ParcelFileDescriptor/AssetFileDescriptor` = zero hits.
5. **No ContentProvider installation stage** — `androidx.startup.InitializationProvider` never runs.
6. Two divergent live `readLine` impls; assets via uncapped `popen(unzip)`.
7. Prefs non-atomic + unescaped XML + `commit()` always true + `clear()` no-op.
8. WAL flag recorded-never-set; `databases_dir` set by 3 competing parties.
9. `Intent.getData()` hardwired null; system services null-marked-IMPLEMENTED.
10. `-night`/`-land` buckets unreachable + first-config fallback; `decodeStream` unsupported; density hardcoded 420; external-storage two spellings break stream round-trips; no `/data/user/0` alias mapping.

### 5. Root families (fan-out rank = fix order)

**FD_AND_STREAM_VOID** → **FAKE-SUCCESS_RESOLUTION** → **COMPONENT_CONTRACT_MISSING** → PATH_LAW_INCOMPLETENESS → NATIVE_FICTION → SELECTION_FROZEN → STATE_LAYER_DIVERGENCE. The first two gate persistence, assets, media and decodeStream; they are the fix-queue head.

### 6. Runtime live proofs (LOAD-AUDIT-2, HEAD `3f05679f`, source APKs physically hidden)

- **opencalc** installed → `base.apk` SHA == source SHA (`2642613868a8a80f`); **x3 runs rc=0, frame `e364b001ee7abd66` ×3 == registry golden** (installed-identity determinism).
- **chess** installed, source hidden: `b5a7a35d5fe0564b` ×3 == golden. **telegram** (64MB) installed, source hidden: `bbb6cd10a834963d` == golden.
- **P-3 live provenance** (telegram file-IO JSONL, 185 ops): 7 asset OPENs — ALL with provenance `@ apk=<INSTALLED base.apk>` + real app DEX callers; ALL 7 entries cross-verified present in the installed APK → **no fake-success observed live** (R-1 stays code-proven, honestly labeled RUNTIME-NOT-OBSERVED-THIS-CORPUS).
- **files→APK asset fallback law observed live** (`bluebubbles.attheme`): files EXISTS=FAILURE → assets OPEN @ installed APK = SUCCESS (correct first-launch law).
- **ST-4 live**: telegram opened **`/dev/urandom` as a raw host path (SUCCESS)** — absolute host paths bypass the sandbox containment, proven at runtime (dalvik_engine:39849).

### 7. Q44 final answer (SUPPLEMENT §44) — honest labels, no 100% claimed

- **WHICH**: resource ids via ARSC+config correct for values/files; `getIdentifier` partial; asset paths verbatim without the existence contract.
- **WHERE**: F-NEW-234 package sandbox correct for the Context family; absolute Android paths NOT mapped (alias/`/data/user/0`/virtual-volume laws partial).
- **HOW**: real stdio for files, ARSC→APK-extract for resources, popen(unzip) for assets, **no fd layer at all**.
- **WHETHER**: CRC32 on APK extraction ✓, gfx byte_source on decoded images ✓; **asset streams/fonts/audio/SQLite UNPROVENANCED**.
- **PROVEN**: install identity, per-package sandbox, multi-DEX+clinit, ARSC best-match, theme/attr chain, inflate chain, WebView engine, network, ZIP self-access, 3-run determinism.
- **PARTIAL**: Context dir family, config selection, fonts, images, SQLite WAL, WebView, prefs, provenance coverage. **BROKEN (P0)**: ST-1, ST-2, R-1, R-2, S-1. **UNKNOWN**: real-app fan-out per family until the corpus re-runs land.

### 8. Next wave (queued)

Fix queue by fan-out: **FD_AND_STREAM_VOID** (real fd layer + stream contracts) and **FAKE-SUCCESS_RESOLUTION** (typed FileNotFoundException contracts, kill the stub hijack) → **COMPONENT_CONTRACT_MISSING** (provider installation stage) → PATH_LAW_INCOMPLETENESS (`/data/user/0` alias + absolute-path mapping law). All generic infrastructure; regression gates = the byte-identical golden suite.
"""

if __name__ == "__main__":
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 354
    res = gh(f"issues/{issue}/comments", {"body": BODY}, method="POST")
    print("POSTED comment id:", res["id"], "url:", res["html_url"])
