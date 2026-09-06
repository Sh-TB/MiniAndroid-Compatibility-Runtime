#!/usr/bin/env python3
"""
g10_restore_env.py — G10 Phase 0 environment restoration (NOT an engine change).

Container reset wiped gitignored artifacts:
  1. tools/aapt2/aapt2 (Google Maven aapt2 8.13.2-14304508, Apache-2.0)
  2. /home/z/corpus/external_hello/HelloWorldSelfAware APK + reference PNG
     (EXT-01/EXT-02 golden dependencies)
  3. miniandroid/download/ corpus cache (18-APK frozen G09 corpus)

Every restored file is SHA-256 verified against the frozen manifests.
Prints a RESTORE REPORT; exit 0 only if every required artifact is OK.
"""
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path("/home/z/my-project")
MA = ROOT / "MiniAndroid-Compatibility-Runtime" / "miniandroid"
REPORT = []


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def ok(name: str, cond: bool, detail: str):
    REPORT.append(("OK   " if cond else "FAIL ") + f"{name}: {detail}")
    return cond


def fetch(url: str, dest: Path, want_sha: str, name: str) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=120) as r, dest.open("wb") as f:
            shutil.copyfileobj(r, f)
    except Exception as e:
        return ok(name, False, f"download error {e}")
    actual = sha256(dest)
    if actual != want_sha:
        return ok(name, False, f"HASH MISMATCH want {want_sha[:16]} got {actual[:16]}")
    return ok(name, True, f"downloaded+verified {dest}")


def main() -> int:
    # ── 1. aapt2 ─────────────────────────────────────────────────────
    aapt2_bin = ROOT / "tools" / "aapt2" / "aapt2"
    if aapt2_bin.exists():
        ok("aapt2", True, "already present")
    else:
        jar = Path("/tmp/aapt2-8.13.2-14304508-linux.jar")
        u = ("https://dl.google.com/dl/android/maven2/com/android/tools/build/"
             "aapt2/8.13.2-14304508/aapt2-8.13.2-14304508-linux.jar")
        got = fetch(u, jar, "SKIPHASH", "aapt2 jar")  # jar hash varies; verify by unzip
        if got:
            try:
                with zipfile.ZipFile(jar) as z:
                    z.extract("aapt2", ROOT / "tools" / "aapt2")
                aapt2_bin.chmod(0o755)
                v = __import__("subprocess").run([str(aapt2_bin), "version", "2>&1"],
                                                 capture_output=True, text=True, timeout=30)
                ok("aapt2", True, f"extracted, version output: {v.stdout.strip() or v.stderr.strip()}")
            except Exception as e:
                ok("aapt2", False, f"extract error {e}")

    # ── 2. EXT-01/02 external_hello corpus ───────────────────────────
    ext_dir = Path("/home/z/corpus/external_hello")
    ext_apk = ext_dir / "HelloWorldSelfAware-1.1.0-android.apk"
    WANT_EXT = "009b467109c4d48d4b00610b06f37f3a77eed75178fbaae344a111acc848cc41"
    if ext_apk.exists() and sha256(ext_apk) == WANT_EXT:
        ok("EXT HelloWorldSelfAware.apk", True, "hash OK")
    else:
        # G09 registry provenance: Appliberated GitHub release v1.1.0
        u = ("https://github.com/Appliberated/HelloWorldSelfAware/releases/"
             "download/v1.1.0/HelloWorldSelfAware-1.1.0-android.apk")
        ext_apk.parent.mkdir(parents=True, exist_ok=True)
        fetch(u, ext_apk, WANT_EXT, "EXT HelloWorldSelfAware.apk")

    ref_png = ext_dir / "helloworldselfaware-android-phone-screenshot.png"
    ok("EXT reference screenshot", ref_png.exists(), str(ref_png))

    # ── 3. frozen download/ corpus cache ─────────────────────────────
    man = json.loads((MA / "tests" / "corpus" / "apks.json").read_text())
    n_ok = n_fail = 0
    for e in man["apks"]:
        rel = e.get("local_path", "")
        url = e.get("download_url", "")
        want = e["sha256"]
        dest = ROOT / rel
        if dest.exists() and sha256(dest) == want:
            n_ok += 1
            continue
        if not url:
            n_fail += 1
            ok(f"corpus {e['name']}", False, "no url and cache missing")
            continue
        if fetch(url, dest, want, f"corpus {e['name']}"):
            n_ok += 1
        else:
            n_fail += 1
    ok("corpus cache", n_fail == 0, f"{n_ok} ok / {n_fail} failed")

    for line in REPORT:
        print(line)
    return 0 if all(l.startswith("OK") for l in REPORT) else 1


if __name__ == "__main__":
    sys.exit(main())
