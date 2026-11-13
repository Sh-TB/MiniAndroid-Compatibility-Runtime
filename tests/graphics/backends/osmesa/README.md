# OSMesa — optional headless real-GL test backend (opt-in)

## Role

Mesa's off-screen software OpenGL interface. NOT a runtime dependency of
MiniAndroid (the renderer is PortableGL + the engine's own GLES bridge).
OSMesa is an independent graphics oracle used by optional anchor probes
(scripts/cont83_egl_anchor.c, scripts/cont83_glesv2_anchor.c) and by this
standalone sanity test.

## Clean-room bootstrap (no root, Debian 13 trixie, verified 2026-11-13)

```bash
apt-get download libosmesa6 libosmesa6-dev libgl-dev
mkdir -p osmesa_sys && for d in libosmesa6*.deb libgl-dev*.deb; do dpkg -x "$d" osmesa_sys/; done
g++ -o test_osmesa test_osmesa.c -Iosmesa_sys/usr/include \
    -Losmesa_sys/usr/lib/x86_64-linux-gnu -lOSMesa \
    -Wl,-rpath,"$ORIGIN/osmesa_sys/usr/lib/x86_64-linux-gnu"
./test_osmesa   # expect: OSMESA REAL GL OK
```

Verified output (2026-11-13, this repository's CI-class container):

```
GL_VENDOR:   Mesa
GL_RENDERER: llvmpipe (LLVM 19.1.7, 256 bits)
GL_VERSION:  4.5 (Compatibility Profile) Mesa 25.0.7-2+deb13u1
GLSL:        4.50
readback px: 51 102 204 255 (expect 51 102 204 255)
OSMESA REAL GL OK
```

## Why the vendored copy was removed (#587 R26)

The previous `third_party/osmesa/` bundle (94.39 MiB path bytes) contained six
tracked paths sharing one 15,693,864-byte ELF blob (sha256 75dd953d…, fake
`.so.6`/`.so.8`/`.so.8.0.0` names), duplicate Debian packages AND fully
extracted package trees, plus a prebuilt test ELF. A whole-repository search
(all source, Makefile/CMakeLists, scripts, workflows, configs) found no build
or runtime consumer. The bootstrap route above reproduces the identical
packages bit-for-bit (deb sha256 match proven) and the test passes.

## Provenance

See MANIFEST.json for pinned versions, package SHA-256 and license pointers.
