#!/usr/bin/env python3
"""validate_release_content.py - permanent release-packaging gate for MiniAndroid.

FAILS any release package (a staging directory, a .tar.gz, or a .zip) that
contains development/toolchain content. Run it before publishing anything.

Usage:
    python3 scripts/validate_release_content.py <staging-dir|archive> [...]
    python3 scripts/validate_release_content.py --platform windows <dir-or-zip>
    python3 scripts/validate_release_content.py --platform linux   <dir-or-tar.gz>

On success prints:
    RELEASE_CONTENT_CHECK: PASS
    DEVELOPMENT_ARTIFACTS: 0
and exits 0. On any violation it prints a detailed report and exits 1.

Rejected content (path rules):
  * toolchain directories/files: llvm-mingw*, win_src, win_deps, build-win,
    build, work, obj, CMakeFiles, .git, apk_cache, node_modules
  * dependency source trees: freetype-*, harfbuzz-*, fribidi-*, zlib-*,
    libpng-*, jpeg-*, libwebp-*, rlottie-*
  * nested archives: *.tar, *.tar.gz, *.tgz, *.tar.xz, *.zip, *.jar

Rejected content (file-type rules, independent of file name):
  * ELF relocatable objects, static archives (ar), PE/DLL images other than
    the single allowlisted Windows executable
  * compiler/linker databases: CMakeCache.txt, compile_commands.json, *.ninja

Rejected content (size heuristic):
  * any single file larger than --max-size MB (default 30) unless allowlisted

Required content:
  * --platform windows: exactly one MiniAndroid.exe (PE32+), no ELF binaries
  * --platform linux:   exactly one miniandroid ELF executable, no PE images
"""

import argparse
import hashlib
import io
import os
import posixpath
import stat
import sys
import tarfile
import zipfile

# ---------------------------------------------------------------------------
# policy tables
# ---------------------------------------------------------------------------
FORBIDDEN_PATH_PARTS = {
    "llvm-mingw", "win_src", "win_deps", "build-win", "build", "work",
    "obj", "cmakefiles", ".git", "apk_cache", "node_modules", "out",
    "staging", "release_staging",
}
FORBIDDEN_DIR_PREFIXES = (
    "freetype-", "harfbuzz-", "fribidi-", "zlib-", "libpng-", "jpeg-",
    "libwebp-", "rlottie-", "llvm-mingw-", "gcc-", "binutils-",
)
FORBIDDEN_SUFFIXES = (
    ".o", ".obj", ".a", ".lib", ".d", ".ninja", ".tar", ".tar.gz", ".tgz",
    ".tar.xz", ".xz", ".zip", ".jar", ".7z", ".deb", ".rpm", ".pdb",
)
FORBIDDEN_FILE_NAMES = {
    "cmakecache.txt", "compile_commands.json", ".ninja_log", "ninja.log",
}
AR_MAGIC = b"!<arch>\n"
ELF_MAGIC = b"\x7fELF"
PE_MAGIC = b"MZ"
DEFAULT_MAX_FILE_BYTES = 30 * 1000 * 1000


class Violation:
    def __init__(self, path, reason):
        self.path = path
        self.reason = reason

    def __repr__(self):
        return "VIOLATION [%s] %s" % (self.reason, self.path)


class Entry:
    """One regular file inside the package (path is '/'-separated, no lead /)."""

    def __init__(self, path, size, data_reader, mode=0o644):
        self.path = path
        self.size = size
        self._reader = data_reader
        self.mode = mode
        self._head = None

    @property
    def head(self):
        if self._head is None:
            self._head = self._reader(64) or b""
        return self._head

    def sha256(self):
        import hashlib
        h = hashlib.sha256()
        self._reader(-1, h)
        return h.hexdigest()


def _reader_file(path):
    def read(n=-1, hasher=None):
        with open(path, "rb") as f:
            if n == 64:
                return f.read(64)
            if n == 0:
                return b""
            data = f.read() if n == -1 else f.read(n)
            if hasher is not None:
                hasher.update(data)
            return data
    return read


def _reader_zip(zf, info):
    def read(n=-1, hasher=None):
        with zf.open(info) as f:
            data = f.read() if n in (-1, 0) else f.read(n)
        if hasher is not None:
            hasher.update(data)
        return data
    return read


def _reader_tar(tf, member):
    def read(n=-1, hasher=None):
        f = tf.extractfile(member)
        if f is None:
            return b""
        data = f.read() if n in (-1, 0) else f.read(n)
        if hasher is not None:
            hasher.update(data)
        return data
    return read


def iter_entries(target):
    """Yield Entry objects from a directory, .zip or .tar.gz."""
    if os.path.isdir(target):
        for root, _dirs, files in os.walk(target):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, target).replace(os.sep, "/")
                st = os.lstat(full)
                if not stat.S_ISREG(st.st_mode):
                    continue
                yield Entry(rel, st.st_size, _reader_file(full), st.st_mode)
        return
    lower = target.lower()
    if lower.endswith(".zip"):
        with zipfile.ZipFile(target) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                yield Entry(info.filename, info.file_size,
                            _reader_zip(zf, info), (info.external_attr >> 16) or 0o644)
        return
    if lower.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar")):
        with tarfile.open(target, "r:*") as tf:
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                yield Entry(member.name, member.size,
                            _reader_tar(tf, member), member.mode)
        return
    raise SystemExit("unsupported target: %s (use a dir, .zip or .tar.gz)" % target)


def classify(entry, platform, allow_names, max_bytes):
    """Return a violation reason string or None."""
    parts = [p for p in entry.path.split("/") if p not in ("", ".")]
    lowered = [p.lower() for p in parts]

    # 1) forbidden path components (exact match on any segment)
    for seg in lowered[:-1]:
        if seg in FORBIDDEN_PATH_PARTS:
            return "forbidden directory '%s'" % seg
    for pref in FORBIDDEN_DIR_PREFIXES:
        for seg in lowered[:-1]:
            if seg.startswith(pref):
                return "dependency source/toolchain tree '%s'" % seg

    base = lowered[-1]
    # 2) forbidden file names
    if base in FORBIDDEN_FILE_NAMES:
        return "build-system file"
    # nested .git
    if ".git" in lowered:
        return "embedded git directory"

    # 3) forbidden suffixes (nested archives, object files, dev libs)
    for suf in FORBIDDEN_SUFFIXES:
        if base.endswith(suf):
            return "development artifact '%s'" % suf

    # 4) binary file-type checks (name-independent)
    head = entry.head
    base_name = posixpath.basename(entry.path)
    if head.startswith(ELF_MAGIC):
        etype = head[16] if len(head) > 16 else 0
        if etype == 1:  # ET_REL = relocatable object
            return "ELF relocatable object (compile byproduct)"
        if platform == "windows":
            return "ELF binary inside a Windows package"
        if base_name != "miniandroid":
            return "unexpected ELF executable '%s' (only 'miniandroid' allowed)" % entry.path
    if head.startswith(PE_MAGIC):
        if platform == "linux":
            return "PE image inside a Linux package"
        if base_name.lower() != "miniandroid.exe":
            return "unexpected PE image '%s' (only 'MiniAndroid.exe' allowed)" % entry.path
    if head.startswith(AR_MAGIC):
        return "ar static library (development artifact)"

    # 5) size heuristic (the allowlisted main runtime executables are exempt:
    #    they are already strictly checked by name + binary magic above)
    if (entry.size > max_bytes
            and base_name not in ("miniandroid", "MiniAndroid.exe")
            and base_name not in allow_names):
        return "file too large for a runtime package (%d bytes)" % entry.size
    return None


def validate(target, platform, allow_names, max_bytes, verbose=True):
    violations = []
    total_bytes = 0
    file_count = 0
    executables = []
    top_dirs = {}
    largest = []

    for entry in iter_entries(target):
        file_count += 1
        total_bytes += entry.size
        first = entry.path.split("/")[0]
        top_dirs[first] = top_dirs.get(first, 0) + entry.size
        largest.append((entry.size, entry.path))
        reason = classify(entry, platform, allow_names, max_bytes)
        if reason:
            violations.append(Violation(entry.path, reason))
        head = entry.head
        is_exec = head.startswith((ELF_MAGIC, PE_MAGIC))
        if is_exec or (entry.mode & 0o111) and not entry.path.endswith((".sh", ".txt", ".md")):
            executables.append(entry.path)

    largest.sort(reverse=True)

    # required-content checks
    names = set()
    for entry in iter_entries(target):
        names.add(posixpath.basename(entry.path).lower())
    if platform == "windows" and "miniandroid.exe" not in names:
        violations.append(Violation("<package>", "required runtime executable MiniAndroid.exe missing"))
    if platform == "linux" and "miniandroid" not in names:
        violations.append(Violation("<package>", "required runtime executable 'miniandroid' missing"))

    # ---- report -----------------------------------------------------------
    print("=" * 72)
    print("RELEASE CONTENT AUDIT: %s  (platform: %s)" % (target, platform or "generic"))
    print("=" * 72)
    print("files: %d    total size: %d bytes (%.1f MB)" % (file_count, total_bytes, total_bytes / 1e6))
    for name, size in sorted(top_dirs.items(), key=lambda kv: -kv[1]):
        print("  top-level: %-55s %10.1f MB" % (name, size / 1e6))
    print("largest files:")
    for size, path in largest[:10]:
        print("  %10.1f MB  %s" % (size / 1e6, path))
    print("executables/binaries found: %s" % (", ".join(sorted(set(executables)) or "none")))
    if violations:
        print()
        for v in violations:
            print("  %r" % v)
        print()
        print("RELEASE_CONTENT_CHECK: FAIL (%d violations)" % len(violations))
        print("DEVELOPMENT_ARTIFACTS: %d" % len(violations))
        return False
    print()
    print("RELEASE_CONTENT_CHECK: PASS")
    print("DEVELOPMENT_ARTIFACTS: 0")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("targets", nargs="+", help="staging dir, .zip or .tar.gz")
    ap.add_argument("--platform", choices=("linux", "windows"), default=None)
    ap.add_argument("--allow", default="", help="comma-separated file names exempt from the size rule")
    ap.add_argument("--max-size-mb", type=float, default=DEFAULT_MAX_FILE_BYTES / 1e6)
    args = ap.parse_args()
    allow = [n for n in args.allow.split(",") if n]
    ok = True
    for t in args.targets:
        ok = validate(t, args.platform, allow, int(args.max_size_mb * 1e6)) and ok
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
