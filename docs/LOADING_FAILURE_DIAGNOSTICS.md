# LOADING FAILURE DIAGNOSTICS — first-divergence records from the probe wave

> LOADING-CAMPAIGN (2026-10-03). Each entry: the probe's observable face, the
> FIRST_DIVERGENCE found, the AOSP semantic, the fix, and the re-run verdict.
> This is the working record behind `docs/LOADING_ROOT_FANOUT.md`.

## D-1 read(byte[]) never fills the buffer

- FACE: `imgOut.write(readAll(assetStream))` produced a 0-byte file; every
  `bos.write(buf, 0, n)` stored 0 bytes; `toByteArray()` empty.
- FIRST_DIVERGENCE: `InputStream.read` law treated `read(byte[])`
  (this + array = 2 args) as the SINGLE-BYTE overload — the bulk-fill branch
  required `args.size() >= 4` (read(b,off,len) only). The caller's array was
  NEVER written; `n>0` returns were the single-byte 1.
- AOSP: `InputStream.read(b)` ≡ `read(b, 0, b.length)` (libcore).
- FIX: 2-arg OBJECT_REF branch fills `array[0..count-1]` from the cached byte
  source (3-way array-length law) and returns count/-1.
- AFTER: `afd-bytes=75`, `img_copy.png` 75 bytes, `read-ok=true`.

## D-2 ByteArrayOutputStream REC-MISS chain

- FACE: `[REC-MISS] Ljava/io/ByteArrayOutputStream;.<init>` → null array →
  `FileOutputStream.write` REC-MISS → 0-byte sink → `decodeFile NULL`.
- AOSP: BAOS is a plain in-memory OutputStream; toByteArray returns the
  buffer copy.
- FIX: full BAOS family in the bridge (`baos_buffers_` member): ctor,
  write(int)/write(b,off,len), toByteArray (REAL engine array with length
  fields), size, reset, toString; close = no-op (AOSP).
- AFTER: baos round-trip feeds the write family; img_copy.png 75 bytes.

## D-3 File.length() answered 0 for a 13-byte file

- FACE: `ren-dst.txt` is 13 bytes on disk; the probe read `ren-dst-length=0`.
- FIRST_DIVERGENCE: `File.length()` is `()J` — the law returned INT32, so the
  (result, adjunct) long register pair was never written; callers read 0.
- AOSP: long length() (UnixFileSystem.getLength).
- FIX: INT64 result (make_long) for length/lastModified; AFD
  getStartOffset/getLength likewise.
- AFTER: `ren-dst-length=13`, `openFd-offset=7417`, `openFd-length=75`.

## D-4 provider stage skipped on the default-Application path

- FACE: `provider-ran=0` (the flag set in ProbeProvider.onCreate stayed
  false); no `[S1-PROVIDER] installed` line.
- FIRST_DIVERGENCE: the install stage sat AFTER bind_manifest_application's
  `app_class.empty()` early return — apps WITHOUT a custom Application class
  (the probe, and most real APKs' default bind) never reached it. AOSP
  installs providers on EVERY bind.
- FIX: stage extracted to `install_content_providers()` called at bind
  entry (both paths).
- AFTER: `provider-ran=1`; `[S1-PROVIDER] installed com.probe.loading.
  ProbeProvider obj#10 onCreate OK`.

## D-5 /dev/urandom fake-EOF (overcorrection guard)

- FACE: after the containment law, `urandom-read=EOF` — the char device has
  no meaningful file_size, the old read path refused and served EOF.
- AOSP: /dev/urandom IS app-readable (sepolicy appdomain urandom_device
  r_file_perms); reads must return bytes, never EOF.
- FIX: non-regular-file branch in the byte-source law — bounded 8 KiB raw
  read (an infinite stream must not hang the assign()).
- AFTER: `urandom-read=OK`.

## D-6 String(byte[]) unmaterialized (cosmetic, law shape recorded)

- FACE: read-back strings rendered `Ljava/lang/String;@N` in the TextView
  although equality (`read-ok=true`) proves the bytes; String object
  rendering stays default-toString.
- FIRST_DIVERGENCE: `new-instance` + `<init>` identity — the caller keeps the
  ORIGINAL heap object; a make_string RETURN VALUE is discarded by the
  constructor protocol.
- FIX: materialize onto the receiver via the `__string_value__` heap
  convention (const-string bridge law) + return the string value.
- AFTER: byte equality passes; object-face rendering remains a display-layer
  artifact (tracked, not loading-critical).

## D-7 the gate's own diagnostic (meta)

- FACE: 3 probe asserts "failed" while the trace showed the PASS values.
- FIRST_DIVERGENCE: the gate extracted the TextView text with a regex that
  stops at the first `\"` escape inside the JSON string — everything after
  `prefs-esc=a<b>&c\"` was invisible to the asserts.
- FIX: proper JSON parse + node walk (children/nodes) in the gate.
- LESSON: evidence extraction is part of the evidence chain — a broken
  extractor fakes a regression exactly like a broken law fakes a success.
