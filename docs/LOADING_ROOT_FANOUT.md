# LOADING ROOT FANOUT — closure map of the 2026-10-03 implementation wave

> Companion to `docs/FILE_RESOURCE_LOADING_COMPATIBILITY.md` §5 (the 7 root
> families) — this file records what each fan-out family looks like AFTER the
> implementation wave, with the closing evidence.

| Family | Members at audit | State after wave | Closing evidence |
|---|---|---|---|
| FAKE-SUCCESS_RESOLUTION | R-1 (asset open), R-7 (list), S-8 (null-as-IMPL), ST-1 (abs-path hijack) | **R-1/R-7/ST-1 CLOSED** (probe: missing asset → FNFE-HONEST; list real; abs-ok=true). S-8 partially closed (Intent.getData real; full services table still open) | probe gate asserts; probe_r logs |
| FD_AND_STREAM_VOID | R-2 (PFD/AFD/openFd), R-5 (popen/4MiB fake-EOF), R-6 (two readLine), R-10 (decodeStream), ST-2 (write family), S-4 (content://) | **R-2/R-5/R-10/ST-2 CLOSED** (openFd+AFD+PFD real-fd laws; in-process ZIP extraction; read(byte[]) fill law; write family + restart counter). R-6 partially closed (canonical byte source now single; the second readLine body still exists but both consume the same source). S-4: content:// query/Cursor still honest-MISSING | probe afd-bytes=75, decodeFile/Stream=8x8, prefs-runs 1→2→3 |
| COMPONENT_CONTRACT_MISSING | S-1 (providers) | **S-1 LAUNCH LEG CLOSED** — install_content_providers at bind entry, every bind path, real DEX onCreate (androidx.startup class now runs when present). Broadcasts/services (S-3/S-13) and splits (S-11) remain OPEN | probe provider-ran=1; [S1-PROVIDER] installed log |
| PATH_LAW_INCOMPLETENESS | ST-1, ST-4 (alias/containment), ST-5 (external spellings), ST-11 (dataDir), ST-12 (name clamps) | **ST-4/ST-5/ST-11 CLOSED** — ONE `Storage::resolve_android_path` law consumed by File/streams/BitmapFactory/openInputStream/openFd/PFD; user-0 alias; DENIED categories. ST-12 (getDir clamp) open (documented deviation) | probe alias-exists, host-deny, ext round-trip; ApplicationInfo seeds |
| NATIVE_FICTION | S-2 (loadLibrary), R-5 | R-5 CLOSED (popen removed). S-2 OPEN (no dlopen layer yet — honest) | traces contain no unzip subprocess |
| SELECTION_FROZEN | R-8 (config), R-9 (density), R-12 (fonts), R-11 (framework values) | OPEN (unchanged this wave — separate campaign) | — |
| STATE_LAYER_DIVERGENCE | ST-6 (prefs), ST-7 (WAL/databases_dir), S-10 (localStorage) | **ST-6/ST-7 CLOSED** (atomic+escaped prefs with honest commit; real WAL pragma; single databases_dir authority). S-10 open | prefs escape round-trip; -wal files on store; remove/clear real |

## New laws discovered by the probe (registered this wave)

1. `InputStream.read(byte[]) ≡ read(b, 0, b.length)` fill law — the 2-arg
   overload must fill the array (previously fell to the single-byte law →
   unwritten buffers → 0-byte sinks everywhere).
2. `java.io.ByteArrayOutputStream` ctor/write/toByteArray/size/reset family.
3. `String(byte[])` ctors materialize via the `__string_value__` heap
   convention (new-instance identity law: the caller keeps the object; the
   string must land ON the object, not in the discarded return value).
4. `File.length()/lastModified()` are `()J` — the register-pair law requires
   INT64 results (an INT32 answer reads as 0).
5. `AssetFileDescriptor.getStartOffset()/getLength()` are `()J` — same law.
6. Character-device read law: /dev/urandom (AOSP sepolicy-legal) gets a
   bounded raw read; file_size-based gates must not fake-EOF it.

## Fix-order status (the audit's fan-out rank)

- FD_AND_STREAM_VOID → **closed** (launch leg)
- FAKE-SUCCESS_RESOLUTION → **closed** (asset/path face)
- COMPONENT_CONTRACT_MISSING → **closed** (provider launch leg)
- PATH_LAW_INCOMPLETENESS → **closed** (alias/containment/decodeFile)
- STATE_LAYER_DIVERGENCE → **closed** (prefs/WAL authority)
- NATIVE_FICTION → R-5 closed; S-2 open
- SELECTION_FROZEN → open (next campaign)
