# APK Toolchain Study — Apktool, JADX, Bundletool (and the fixtures tooling lesson)

Sources: Apktool `baa603f`, JADX `8f7ea4e`, Bundletool `586a43a`
(structure + targeted files), plus MiniAndroid's own
`scripts/build_fixture_apk.sh` lessons (D8 8.3.37 jar-based class
collection fix from the prior campaign).

## TOOL-001 — Apktool resource pipeline shape
- `brut.apktool/apktool-lib/.../res/ResDecoder.java` orchestrates:
  ARSC/table decode (BinaryResourceParser), binary-XML decode
  (BinaryXmlResourceParser + pull decoders), nine-patch, raw files.
- `BinaryResourceParser.java` pins the ARSC constants MiniAndroid must
  honor (NO_ENTRY, OFFSET16, SPARSE, SPEC_PUBLIC/STAGED_API — see
  ARSC-001) and stages decode through a chunk pull parser
  (`ResChunkPullParser`) — one bounded reader shared by ARSC and AXML.
- Transfer: the shared bounded-chunk-reader pattern unifies our
  arsc_parser + axml_parser bounds-checking; currently duplicated.
  Status: REIMPLEMENT CONCEPT (refactor candidate, low priority).

## TOOL-002 — JADX as the expectation oracle (license situation improved)
- jadx-core `core/xmlgen/ResTableBinaryParser.java`: table parse with
  per-chunk skip-to-end discipline + library-chunk support;
  `BinaryXMLParser` + `ManifestAttributes` for AXML.
- `core/dex/` (attributes/instructions/nodes/regions/trycatch/visitors)
  is the decompiler spine — for MiniAndroid the value is the IR shape:
  instructions→regions (structured control flow)→visitors, and the
  trycatch attribute model.
- License: Apache-2.0 at HEAD (confirmed at prior session re-read; this
  session's clone carries the same). Import remains UNNECESSARY — jadx is
  used as an independent expectation generator for ViewTree/strings/
  resources diffs (queued as the jadx-vs-runtime differential test).
- Status: ORACLE FIRST (unchanged policy).

## TOOL-003 — Bundletool relevance check
- Structure surveyed: `src/main/java/com/google/devtools/build/android/
  bundletool/` — APK-set/split-APK generation, manifest merge, module
  splitting.
- Verdict for MiniAndroid: split-APKs matter ONLY if the corpus contains
  AAB-derived APKSets (none currently: all corpus APKs are single-APK).
  The one durable lesson: Bundletool validates manifest/resource
  consistency BEFORE packaging — MiniAndroid's fixture builder should
  fail-fast on inconsistent fixture manifests the same way.
- Status: NOT APPLICABLE YET (with a fail-fast lesson adopted in spirit).

## TOOL-004 — Fixture tooling engineering lesson (our own, corroborated)
`build_fixture_apk.sh` must collect classes via the jar (D8 8.3.37 rejects
directories) — discovered empirically in the prior campaign; Apktool's
`AaptInvoker`/`AaptManager` shows the same "know the container/tool
version" discipline on the aapt side. The standing Cycle E fixture-tool
issue (if still open at HEAD) is to be fixed in the tool ONLY, keeping
fixture semantics stable.
- Status: LESSON RECORDED (owner: build tooling).
