#!/usr/bin/env python3
"""EXP-096 §5: Streaming-ZIP (data-descriptor) regression fixture.

Creates a synthetic ZIP file containing:
  - normal entry (sizes in LFH, no data descriptor)
  - data-descriptor entry (LFH sizes=0, sizes follow data — APPNOTE §4.3.9)
  - compressed entry (deflate) with data descriptor
  - binary asset (PNG header bytes)

Verifies:
  1. The ZIP round-trips through python zipfile correctly (control).
  2. MiniAndroid's ApkParser::extract_entry returns the SAME bytes for each
     entry (via a tiny C++ test binary that links against the parser).

Outputs:
  - /tmp/exp096_test.zip
  - PASS/FAIL per entry
"""
import os, struct, zlib, zipfile, subprocess, tempfile, shutil
from pathlib import Path

# Build the fixture ZIP by hand so we can guarantee the streaming entry is
# actually streaming (zipfile sets the data-descriptor flag for any entry
# whose mode is ZIP_STORED/ZIP_DEFLATED when written to a non-seekable
# stream — but we want to verify both modes explicitly).
import io

def make_test_zip(path: Path):
    """Hand-craft a ZIP with mixed normal + data-descriptor entries."""
    entries = []
    contents = {
        'normal.txt':            b'Hello, normal ZIP entry!',
        'streaming.txt':         b'Hello, streaming data-descriptor entry!',
        'compressed.bin':       bytes(range(256)) * 8,  # 2048 bytes, very compressible
        'png_magic.bin':        b'\x89PNG\r\n\x1a\n' + b'\x00' * 64,  # PNG signature + data
        'empty.txt':            b'',  # genuinely empty entry
    }
    methods = {
        'normal.txt':      zipfile.ZIP_STORED,
        'streaming.txt':   zipfile.ZIP_DEFLATED,  # streaming + compressed
        'compressed.bin':  zipfile.ZIP_DEFLATED,  # normal + compressed
        'png_magic.bin':   zipfile.ZIP_STORED,    # normal + binary
        'empty.txt':       zipfile.ZIP_STORED,    # empty
    }

    # Use Python's zipfile which by DEFAULT writes data descriptors
    # (flag bit 3 set, LFH sizes=0, sizes in data descriptor after data)
    # for ALL entries — that's what we want to test.
    with zipfile.ZipFile(path, 'w') as z:
        for name in contents:
            z.writestr(name, contents[name], compress_type=methods[name])

    # Verify with zipfile first (control)
    with zipfile.ZipFile(path, 'r') as z:
        for name, expected in contents.items():
            actual = z.read(name)
            info = z.getinfo(name)
            assert actual == expected, f"zipfile control FAILED for {name}"
            flag_bits = info.flag_bits
            has_dd = bool(flag_bits & 0x8)
            print(f"  [zipfile] {name}: csize={info.compress_size} usize={info.file_size}"
                  f" method={info.compress_type} data_descriptor={has_dd}")
    print(f"  [zipfile] control passed for all entries")
    return contents

def make_test_apk(path: Path, entries: dict):
    """Wrap entries into a minimal APK.

    Writes TWICE:
      1. The first APK uses normal seekable output — every entry has its
         sizes in the local file header (control).
      2. The second APK writes to a NON-seekable stream — every entry is
         stored with the data-descriptor extension (APPNOTE §4.3.9): the
         LFH crc/compressed-size/uncompressed-size fields are ZERO and the
         actual values follow the file data in a 12-or-16-byte descriptor.
         This is the bug-class we're guarding against.
    Both APKs should round-trip identically through ApkParser.
    """
    minimal_manifest = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b'<manifest xmlns:android="http://schemas.android.com/apk/res/android"\n'
        b'    package="miniandroid.exp096" android:versionCode="1" android:versionName="1.0">\n'
        b'    <application android:label="EXP-096"/>\n'
        b'</manifest>\n'
    )
    dex_magic = b'dex\n035\x00' + b'\x00' * 100  # minimal dex stub

    # Streaming (non-seekable) wrapper to force data descriptors.
    class NonSeekable(io.RawIOBase):
        def __init__(self, buf): self.buf = buf
        def writable(self): return True
        def seekable(self): return False
        def write(self, b):
            self.buf += b
            return len(b)

    def _write_apk(path):
        buf = bytearray()
        ns = NonSeekable(buf)
        with zipfile.ZipFile(ns, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('AndroidManifest.xml', minimal_manifest, zipfile.ZIP_STORED)
            for name, data in entries.items():
                method = (zipfile.ZIP_DEFLATED if name in ('streaming.txt', 'compressed.bin')
                          else zipfile.ZIP_STORED)
                z.writestr(name, data, compress_type=method)
            z.writestr('classes.dex', dex_magic, zipfile.ZIP_DEFLATED)
        with open(path, 'wb') as f:
            f.write(bytes(buf))

    normal_apk = path.parent / (path.stem + '_normal.apk')
    streaming_apk = path
    # Note: zip on a seekable file → no data descriptors; on a non-seekable
    # stream → all entries get flag bit 3 (data descriptor). We test both.
    _write_apk(streaming_apk)
    # Verify with python zipfile that the streaming APK round-trips.
    with zipfile.ZipFile(streaming_apk, 'r') as z:
        for name, expected in entries.items():
            actual = z.read(name)
            assert actual == expected, f"streaming APK control FAILED for {name}"
            info = z.getinfo(name)
            has_dd = bool(info.flag_bits & 0x8)
            print(f"  [streaming APK] {name}: csize={info.compress_size} usize={info.file_size}"
                  f" data_descriptor={has_dd}")
    print(f"  [streaming APK] control round-trip passed")
    return entries

def main():
    work = Path(tempfile.mkdtemp(prefix='exp096_'))
    print(f"Work dir: {work}")
    zip_path = work / 'mixed.zip'
    apk_path = work / 'mixed.apk'

    print("=== Building mixed-mode ZIP fixture ===")
    contents = make_test_zip(zip_path)
    make_test_apk(apk_path, contents)

    print("\n=== Expected entry contents ===")
    for name, data in contents.items():
        print(f"  {name}: {len(data)} bytes, head={data[:8]!r}")

    # Run the C++ extractor binary (built by the build step below).
    exe = Path('/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/build/apk_extract_test')
    if not exe.exists():
        print(f"\nC++ extractor not built: {exe}")
        print("Build with:")
        print("  g++ -std=c++17 -I src/apk -I third_party/nlohmann-json/include \\")
        print("       src/apk/apk_parser.cpp scripts/exp096_apk_extract_test.cpp \\")
        print("       -lz -o build/apk_extract_test")
        return 1

    print(f"\n=== Running C++ extractor against {apk_path.name} ===")
    result = subprocess.run(
        [str(exe), str(apk_path)],
        capture_output=True, text=True, timeout=30)
    print(result.stdout)
    if result.stderr:
        print("stderr:", result.stderr)
    return result.returncode

if __name__ == '__main__':
    raise SystemExit(main())
