# MiniAndroid Modular Foundation (S98-FUTURE, implemented S100)

> Status markers used throughout: **CURRENT** (exists and evidenced today),
> **FOUNDATION** (metadata/contracts landed this wave), **FUTURE**
> (designed, deliberately NOT implemented — never presented as done).

## 1. The architectural law (S100 §90)

> MiniAndroid SHALL NOT equate Android compatibility breadth with mandatory
> runtime bulk. Common foundational semantics remain in Core; optional,
> expensive, uncommon, or domain-specific semantics are represented as
> independently versioned **capabilities** with explicit dependencies,
> provenance, tests, size attribution, and per-APK selection.

> Capability existence SHALL NOT be confused with capability usage. Static
> API references, resolved dependencies, runtime-loaded capabilities, and
> semantically verified behavior remain **separately observable**.

## 2. Canonical artifacts (FOUNDATION)

| Artifact | Role | Law |
|----------|------|-----|
| [CAPABILITY_REGISTRY.json](CAPABILITY_REGISTRY.json) | machine-readable capability graph: id, layer, status, requires/provides, api_prefixes (API→capability map), hot/cold, size class, source authority | one source of truth per fact: status mirrors the canonical matrix; structure is canonical here |
| [CORE_MANIFEST.json](CORE_MANIFEST.json) | Core boundary; every component answers "is this Core? which capability owns it?" | candidate extractions MARKED, never silently moved (§76 do-not-break-the-monolith) |
| [SIZE_BASELINE.json](SIZE_BASELINE.json) | measured baseline: unstripped/stripped/gzip/text/rodata/data/bss/symbols | numbers derived from the measured binary, never invented (§9) |
| [tools/s100_size_gate.py](../tools/s100_size_gate.py) | size gate + delta + DEPENDENCY_AMPLIFICATION flag | a capability must not silently inflate Core (§10/§12) |
| [tools/s100_apk_profile.py](../tools/s100_apk_profile.py) | per-APK profile: static capabilities → dependency closure (≠ observed) | static ≠ observed (§14); Do-not-hardcode-N-APIs (§70) |
| [S100_APK_PROFILES.json](S100_APK_PROFILES.json) | benchmark profiles (browser / dooz / mykanji / 2048 / tictactoe) | §81 real-APK validation |
| [scripts/s100/s100_foundation_tests.py](../scripts/s100/s100_foundation_tests.py) | 21 tests incl. adversarial: duplicate capability, unknown dependency, cycle detection, missing field, corrupt status, static-vs-observed confusion, missing measurement | §79/§80 |

## 3. What the benchmarks already prove (CURRENT)

| APK | closure | cold capabilities pulled |
|-----|--------:|--------------------------|
| **Mini Browser** (networked app) | **9** | **none** — no WebView, no Compose, no audio |
| dooz (compose game) | 19 | compose.runtime, media.audio |
| TicTacToe | 19 | graphics.opengl, media.audio (static refs only) |
| MyKanji / 2048 | 22 | webview (static refs, never executed) |

The Mini Browser is the living minimality benchmark: a networked,
interactive, REAL-website-loading app whose runtime needs 9 of 26
capabilities — the small-APK/small-runtime principle demonstrated with
measured evidence (3/3 byte-identical runs, docs/evidence/s100_browser/).

## 4. Future contracts (FUTURE — designed, not implemented)

* **Capability pack format** (§16): `manifest / implementation / resources /
  data / native / tests / provenance / license / hashes` — content-addressed
  by SHA256; identity = (capability, version, sha256).
* **Capability lockfile** (§15): per-APK `capabilities.lock` = closure +
  versions + provider + ABI + hash → reproducible execution.
* **Lazy initialization interface** (§32): `resolveCapability() /
  loadCapability() / getCapabilityProvider()` — the current resolver stays
  monolithic internally; the contract is reserved (§46).
* **Local cache / acquisition** (§20/§21): offline-first is permanent law —
  no runtime may require the network merely because a capability exists
  externally; remote download is **NOT STARTED** by design (§47/§77).
* **Failure modes** (§22): structured diagnostics
  `CAPABILITY_MISSING / … / UNSUPPORTED_API` reserved in the registry;
  the crash-forensics ring (S100) is the existing root of that chain.
* **Versioning** (§17/§18): Core version, capability version, ABI
  constraints, minimum_core_version fields exist in the schema; resolver
  enforcement is FUTURE.

## 5. Core contamination rule (CURRENT, ongoing)

Every new API implementation answers (§22): which capability owns it? which
dependencies does it add? which APKs need it? can it reuse an existing
implementation? what does it cost? — Recent proof: `http_client.cpp` was
born inside the `network.http` capability as a physically separate file;
`crash_forensics.cpp` in core/diagnostics; neither touched other components.
