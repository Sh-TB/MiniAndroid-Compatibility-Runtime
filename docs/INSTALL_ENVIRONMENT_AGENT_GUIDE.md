# INSTALL-ENVIRONMENT AGENT GUIDE (GATE A) — issue #370 §15

How an agent inspects an installed Android package with MiniAndroid —
machine-readable at every step, independent of whether the app renders.

## 0. One-time: obtain the binary

```bash
cd /home/z/my-project/miniandroid && make -j2   # build/miniandroid
```

## 1. Install an APK (package store law)

```bash
miniandroid install /path/to/app.apk --data-root /tmp/store
# JSON on stdout: {"install":"SUCCESS","package":...,"apkSha256":...,
#                  "codePath":"/data/app/<pkg>/base.apk",...}
```
Post-install identity = **package name + data-root only**. The source APK
can be deleted/moved — nothing reads it back (F-NEW-231 commit law:
copy-then-record, integrity re-hash at install).

## 2. Inspect the installed package (THE gate-A surface)

```bash
miniandroid pkginspect --package <pkg> --data-root /tmp/store \
    [--what identity,manifest,entries,dex,resources,assets,libs,media,\
data,external,dbs,prefs,provenance] \
    [--jsonl out.jsonl]      # full-fidelity stream, one JSON object/line
```
- `--what all` (default) = every section. Sections are independent —
  `--what dbs` answers only databases.
- `--apk <path>` inspects an APK **without** installing (DIRECT_APK mode).
- Absent package → exit 1 + `Package not installed` on stderr (AOSP
  NAME_NOT_FOUND; no fake JSON).
- Every item row carries its physical backing + provenance class
  (`INSTALLED_APK`, `APP_DATA_FILE`, `EXTERNAL_APP_FILE`, `RESOURCE`, …).

Section contents:
| section | answers |
|---|---|
| identity | package, logical+host codePath, live SHA-256 vs record, version/SDK, main activity, label |
| manifest | activities(+actions/main/launcher), services, receivers, providers(+authorities), permissions, meta-data, features |
| entries | every ZIP entry: method STORED/DEFLATE, sizes, CRC32, class (DEX/ASSET/RES/NATIVE_LIB/…) |
| dex | per classesN.dex: strings/types/protos/fields/methods/classes counts, native methods, class sample (name/flags/super) |
| resources | ARSC packages/types/entries with config buckets (whole-table inventory) |
| assets | assets/** entries with size + compression |
| libs | lib/<abi>/*.so: SHA-256, ELF class/machine, SONAME, JNI export count (+ symbol rows in JSONL) |
| media | image/font/audio/video inventory with expected decoder |
| data | /data/data/<pkg> tree: logical path, physical backing, size, SHA-256 |
| external | Android/{data,media,obb}/<pkg> trees |
| dbs | databases/*.db: SQLite header validity, -wal/-shm/-journal companions, SHA-256 |
| prefs | shared_prefs/*.xml per-key inventory (type/key/value) |
| provenance | canonical graph: SOURCE_APK → INSTALL → INSTALLED_BASE_APK → {MANIFEST,DEX,RESOURCES,ASSETS,LIBS,APP_DATA} |

## 3. Run / trace (works even if the app will fail to render)

```bash
MINIANDROID_FILE_IO=/tmp/out/file_io.jsonl \
miniandroid run --package <pkg> --data-root /tmp/store -o /tmp/out \
    --dump-view-tree [--trace] [--max-seconds 120]
```
- `file_io.jsonl`: one record per file op —
  `{"seq","op":OPEN|READ|WRITE|STAT|LIST|EXISTS|MKDIR|CREATE|DELETE|RENAME|NATIVE,
    "path","result":SUCCESS|FAILURE,"subsystem","caller","package"}`.
- `view_tree.json`, `screenshot.png`, `trace.jsonl` as usual (GATE B/C
  observability; GATE A does not depend on them).

## 4. Package lifecycle

```bash
miniandroid list-packages --data-root /tmp/store        # JSON array
miniandroid uninstall --package <pkg> --data-root /tmp/store
#   exit 0 = removed (codePath + record + data + external trees)
#   exit 2 = NOT_INSTALLED (honest PMS verdict)
```

## 5. First-divergence / what-failed workflow

1. `pkginspect --what identity` → is the package + integrity intact?
2. `pkginspect --what manifest` → which component was expected to run?
3. `run … MINIANDROID_FILE_IO=…` → which op failed first (typed FAILURE +
   caller class.method)?
4. Compare with the negative contract rows
   (`docs/INSTALL_ENVIRONMENT_NEGATIVE_TESTS.jsonl`) — missing files give
   FileNotFoundException, unknown resources NotFoundException, missing
   natives UnsatisfiedLinkError, foreign paths DENIED. A silent null/"" is
   a runtime bug, not an answer.
5. `pkginspect --what dbs,prefs,data` → what state actually landed on disk
   (SQLite header validity, WAL companions, pref XML keys).

## 6. Evidence provenance

Every artifact in this gate carries identity: HEAD commit, runtime binary
sha16, evidence-generation script path. Executed evidence lives under
`run/gatea/` (probe store + runs), `run/gatea/multiapp_evidence/` (5-app
proof), `run/gatea/negative/`, `run/gatea/reinstall_matrix/`.
