#!/usr/bin/env python3
"""make_arm_stubs.py — deterministic ARM stub payloads for the LAW-001
arm_only_scope_probe fixture.

The stubs are NOT claimed to be executable ARM code. They are fixed-content
payload files whose only jobs are (1) to give the APK real, inspectable
lib/armeabi-v7a/ and lib/arm64-v8a/ entries — the ABI-tree evidence LAW-001
classifies on — and (2) to make the fixture byte-deterministic across
rebuilds (fixed 64-byte payload, no timestamps, no host entropy).

If the LAW-001 scope gate were ever bypassed, these payloads would honestly
fail at dlopen on the x86_64 host (they are not valid host ELF objects) —
the pre-LAW-001 honest-refusal behavior, never a fabricated success.
"""
import sys

# 64-byte deterministic payload per ABI; ELF-magic-free ON PURPOSE: these are
# declared stubs (not forged ELF objects) — forging a fake aarch64 ELF header
# would claim more than the fixture proves.
if __name__ == "__main__":
    base = sys.argv[1]
    for abi in ("armeabi-v7a", "arm64-v8a"):
        tag = b"v7a" if abi == "armeabi-v7a" else b"a64"
        data = (b"MINIANDROID-LAW001-ARM-SCOPE-STUB/" + tag + b"/"
                + b"N" * (64 - 34 - len(tag) - 1))  # exact 64-byte payload
        assert len(data) == 64, len(data)
        with open(f"{base}/{abi}/libprobe.so", "wb") as f:
            f.write(data)
        print(f"wrote {base}/{abi}/libprobe.so ({len(data)} bytes)")
