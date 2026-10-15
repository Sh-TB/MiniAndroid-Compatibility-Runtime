#!/usr/bin/env python3
"""Checker self-tests for tools/check_repo_hygiene.py (C28, #386).

Positive cases: intentional, legitimate artifacts MUST pass.
Negative cases: forbidden generated residue MUST fail.

Runs check() against SYNTHETIC path lists — the real repo index is never
touched, so the test is safe to run anywhere. Path-existence-dependent
rules (oversize, secrets) are exercised via a temp fixture dir.

Exit 0 = all tests pass; 1 = any failure.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_repo_hygiene as hy  # noqa: E402

PASSED = []
FAILED = []


def expect(name, failures, should_contain):
    if should_contain is None:
        ok = len(failures) == 0
    else:
        ok = any(should_contain in f for f in failures)
    (PASSED if ok else FAILED).append(name)
    print(f"  {'PASS' if ok else 'FAIL'} — {name}"
          + ("" if ok else f" (failures={failures})"))


def main():
    with tempfile.TemporaryDirectory() as td:
        # --- negative cases (must FAIL) ---
        print("NEGATIVE cases:")
        expect("APK tracked",
               hy.check(["some/app.apk"], td), "APK/SO tracked")
        expect(".so tracked",
               hy.check(["lib/native.so"], td), "APK/SO tracked")
        expect("build dir tracked",
               hy.check(["build/foo.o", "miniandroid/build/x.ppm"], td),
               "build dir tracked")
        expect("raw log tracked",
               hy.check(["run/session/trace.log"], td), "raw log tracked")
        expect("zip archive tracked",
               hy.check(["tmp/handoff/res.zip"], td), "archive blob tracked")
        expect("__pycache__ path tracked",
               hy.check(["tools/verify/probes/__pycache__/verdict.cpython-312.pyc"], td),
               "python bytecode tracked")
        expect("standalone .pyc tracked",
               hy.check(["scripts/foo.pyc"], td), "python bytecode tracked")
        expect("generated .class outside allowance",
               hy.check(["tmp/probe_build/obj/Main.class"], td),
               "generated class tracked")
        expect("generated .class in fixtures build dir",
               hy.check(["fixtures/fx/build/classes/Main.class"], td),
               "generated class tracked")

        # --- positive cases (must PASS) ---
        print("POSITIVE cases:")
        expect("intentional interpreter DEX fixture",
               hy.check(["miniandroid/test_apks/exp052/case1_no_catch.dex"], td),
               None)
        expect("forensic evidence .class (allowlisted prefix)",
               hy.check(["docs/research/source-forensics/evidence/A10/x.class"], td),
               None)
        expect("upstream .class (allowlisted prefix)",
               hy.check(["upstream/s44/androidx/A.class"], td), None)
        expect("whitelisted distilled log",
               hy.check(["docs/evidence/mc4_telegram/tg_run1_distilled.log"], td),
               None)
        expect("runtime source over 5MB but allowlisted",
               hy.check(["miniandroid/src/dex/dalvik_engine.cpp"], td), None)
        expect("framework arsc allowlisted",
               hy.check(["miniandroid/framework_res/resources.arsc"], td), None)
        expect("pinned toolchain jar allowlisted",
               hy.check(["tools/toolchain/android-34.jar"], td), None)
        expect("kotlinc dist jar allowlisted",
               hy.check(["upstream/cont12_maven/kotlinc-dist/kotlinc/lib/"
                         "kotlin-compiler.jar"], td), None)
        expect("plain source files",
               hy.check(["miniandroid/src/api/api.cpp", "README.md",
                         "scripts/s59_games_register.py"], td), None)

        # --- existence-dependent rules via real temp files ---
        print("FILE-CONTENT cases:")
        big = os.path.join(td, "big_blob.bin")
        with open(big, "wb") as fh:
            fh.write(b"\0" * (hy.SIZE_LIMIT + 1024))
        expect("oversize unallowlisted file fails",
               hy.check(["big_blob.bin"], td), "oversize")
        expect("oversize allowlisted file passes",
               hy.check(["miniandroid/src/dex/dalvik_engine.cpp"], td), None)

        secret = os.path.join(td, "creds.py")
        with open(secret, "w") as fh:
            fh.write("token = 'ghp_" + "A" * 36 + "'\n")
        expect("secret pattern in non-doc file fails",
               hy.check(["creds.py"], td), "secret pattern")

        marker = os.path.join(td, "notes.md")
        with open(marker, "w") as fh:
            fh.write("token = 'ghp_" + "A" * 36 + "'\n")
        expect("doc-format files are not secret-scanned (documented scope)",
               hy.check(["notes.md"], td), None)

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
