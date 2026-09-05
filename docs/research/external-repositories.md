# External Repositories — Canonical Inventory

Campaign: DEEP REPOSITORY RESEARCH & KNOWLEDGE TRANSFER (2026-09-05).
Law: exact URL first, identity verified, revision locked, then source study.
No repository was substituted. Where the mandated URL was unavailable the row
is marked `REPOSITORY_UNAVAILABLE` / `REPOSITORY_URL_UNVERIFIED` per §29.

Every clone fetched in this session lives outside the MiniAndroid tree in
`../research-clones/` (references only; nothing imported wholesale).

## Locked inventory

| # | Project | Exact URL | Revision studied | Access | Identity check | Status |
|---|---------|-----------|------------------|--------|----------------|--------|
| 1 | MiniAndroid (parent) | https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime | local main `82334321a3f83a299131a4150bb2934ed893bcb5` | local clone | N/A (parent project) | ACTIVE |
| 2 | WineDroid | https://github.com/rickbergs/winedroid | `a784c0b956893733cc12ccd3bec7695b0791f978` (2026-07-14, "docs: rewrite project README") | git clone (shallow) | README self-identifies: AOT "APK → DEX → C → ELF x86-64", author Richard Bergamaschi, Rust workspace `crates/{winedroid-core,winedroid-cli,winedroid-compiler}` | REPOSITORY_AVAILABLE (SOURCE_READ, all 21 .rs files) |
| 3 | AOSP frameworks/base | https://android.googlesource.com/platform/frameworks/base/ (mirror studied: https://github.com/aosp-mirror/platform_frameworks_base) | mirror `1cdfff555f4a21f71ccc978290e2e212e2f8b168` (2025-03-26) | git clone (shallow) | Android framework Java sources (View/ViewGroup/Resources/graphics/os) | REPOSITORY_AVAILABLE (SOURCE_READ, targeted files) |
| 4 | AOSP ART | https://android.googlesource.com/platform/art/ | `6484611fd45e69db9f33f98bfd6864014b030ecf` (2025-03-26) | git clone (shallow, official googlesource) | `libdexfile/`, `runtime/`, `dex2oat/`, `compiler/` | REPOSITORY_AVAILABLE (SOURCE_READ, verifier + loader). NOTE: `aosp-mirror/platform_art` on GitHub does not exist (HTTP 404 verified) — official googlesource URL used, exactly as mandated |
| 5 | AOSP Dalvik | https://android.googlesource.com/platform/dalvik/ (mirror: https://github.com/aosp-mirror/platform_dalvik) | mirror default branch, shallow | git clone | historical Dalvik docs/opcode material | REPOSITORY_AVAILABLE (SOURCE_READ, docs) |
| 6 | AOSP frameworks/native | https://android.googlesource.com/platform/frameworks/native/ | `4f463a6b1de9198963dc6aff74154a504ba3f8f6` (2025-03-25) | git clone (shallow, official googlesource) | `libs/binder`, `services/surfaceflinger`, `include/android` | REPOSITORY_AVAILABLE (SOURCE_READ, structure + key headers) |
| 7 | AOSP frameworks/av | https://android.googlesource.com/platform/frameworks/av/ | not cloned this session (media stack out of current MiniAndroid critical path) | URL verified reachable | — | REPOSITORY_AVAILABLE (NOT YET STUDIED; deferred, see gap analysis) |
| 8 | Android Emulator (qemu) | https://android.googlesource.com/platform/external/qemu/ | branch `emu-master-dev` @ `ae9d18d2b6261179fbd57fffec720a04f7bfb053` (2025-03-27, "Bump Emulator to 35.6.3 Canary"). NOTE: default branch HEAD is stale (2015); development happens on `emu-master-dev` | git clone (shallow) + branch fetch | `android/android-emu/`, `android-emugl/`, `android-grpc/` | REPOSITORY_AVAILABLE (SOURCE_READ, structure + key modules) |
| 9 | Cuttlefish | https://android.googlesource.com/device/google/cuttlefish/ | `a1162ca7a4e6297f1699b65052a8c2dd466fd518` (2025-03-26) | git clone (shallow) | `host/` (commands, frontend, libs), `guest/` (hals, services) | REPOSITORY_AVAILABLE (SOURCE_READ, structure + host/guest boundary) |
| 10 | CrosVM | https://github.com/google/crosvm | `9d4dc5fedc493bfcb1e983970fcec79cf4cf9c6c` (2026-09-04) | git clone (shallow) | `ARCHITECTURE.md` + Rust workspace (process-per-device, minijail) | REPOSITORY_AVAILABLE (SOURCE_READ, architecture doc + layout) |
| 11 | AVF / Virtualization | https://android.googlesource.com/platform/packages/modules/Virtualization/ | `175a51b30123fa6b02b541f1969665708f7ec2c3` (2025-03-26) | git clone (shallow) | `guest/`, `microdroid/`, `docs/` | REPOSITORY_AVAILABLE (SOURCE_READ, structure + docs) |
| 12 | Waydroid | https://github.com/waydroid/waydroid | `e7d73e7ff9d23003356d716e5a40fa5ca7ad17e0` | git clone (shallow) | Python tooling `tools/actions/{session_manager,container_manager,app_manager}.py`, LXC container model | REPOSITORY_AVAILABLE (SOURCE_READ, structure + tooling) |
| 13 | JADX | https://github.com/skylot/jadx | `8f7ea4e2c4bb82ca935aaeee98d9e8d3f3f3fba8` | git clone (shallow) | `jadx-core` `core/dex/`, `core/xmlgen/{ResTableBinaryParser,BinaryXMLParser}.java` | REPOSITORY_AVAILABLE (SOURCE_READ, targeted) |
| 14 | APKTool | https://github.com/iBotPeaches/Apktool | `baa603f353a51b932f136584358acf025c748895` | git clone (shallow) | `brut.apktool/apktool-lib/.../res/decoder/BinaryResourceParser.java` (+ chunk pull parser) | REPOSITORY_AVAILABLE (SOURCE_READ, targeted) |
| 15 | Bundletool | https://github.com/google/bundletool | `586a43a450712a1067f3d92cf7574dee68226302` | git clone (shallow) | `src/main/java/com/google/devtools/build/android/bundletool/` | REPOSITORY_AVAILABLE (SOURCE_READ, structure) |
| 16 | SIM-USE | https://github.com/SimulaVR/sim-use | none — repository became unavailable DURING this session: first batch clone listed a `sim-use` directory, subsequent verification of the same URL returned HTTP 404 and git prompts for credentials (repo not found) on two retries 20s apart | git clone attempts + HTTP probe | identity could not be re-verified after the 404 | **REPOSITORY_UNAVAILABLE** (no substitution made; `lycorp-jp/sim-use` is a DIFFERENT project and was NOT used) |
| 17 | Skydnir | https://github.com/ryo100794/skydnir | default HEAD, shallow (URL locked from MiniAndroid's own prior records `docs/research/COMPATIBILITY_REFERENCE_MATRIX.md`) | git clone (shallow) | "Zero-kernel userspace runtime for mobile devices" | REPOSITORY_AVAILABLE (SOURCE_READ, structure; license custom → no reuse) |
| 18 | DroidVM | https://github.com/Droid-VM/DroidVM | default HEAD, shallow (URL locked from MiniAndroid prior records) | git clone (shallow) | Gunyah/GenieZone/KVM hypervisor manager | REPOSITORY_AVAILABLE (SOURCE_READ, structure; orthogonal problem) |
| 19 | DroidSaw | https://github.com/droidsaw/droidsaw | `50eb045b5672431ea787c2696100baed44163918` (2026-06-11) | git clone (shallow) | Pure-Rust DEX/Hermes decompiler; BSD-3-Clause; README claims 5,767 F-Droid DEX files round-trip bit-identically | REPOSITORY_AVAILABLE (SOURCE_READ, README + layout) |
| 20 | AndroidRecomp | (no canonical URL) | — | GitHub search (MiniAndroid history first: zero hits; then web search) | Only unrelated game-console "Recomp-Android" ports exist (UnleashedRecomp-Android, Zelda64Recomp-Android) — none is an Android-APK recompilation project | **REPOSITORY_URL_UNVERIFIED** |
| 21 | ReSource | (no canonical URL) | — | MiniAndroid history: zero hits; web search: only Apktool/ARSCLib issues; four guessed owner/repo probes 404 | no identity-verifiable project | **REPOSITORY_URL_UNVERIFIED** |
| 22 | Reveree | (no canonical URL) | — | MiniAndroid history: zero hits; web search: generic RE tooling only | no identity-verifiable project | **REPOSITORY_URL_UNVERIFIED** |
| 23 | libarsc (auxten) | https://github.com/auxten/libarsc | default HEAD, shallow (locked from MiniAndroid prior records) | git clone (shallow) | aapt-derived C++ ResTable parser | REPOSITORY_AVAILABLE (SOURCE_READ via prior session + structure re-check) |
| 24 | ARSCLib | https://github.com/REAndroid/ARSCLib | default HEAD, shallow (locked from MiniAndroid prior records) | git clone (shallow) | Java ARSC read/write/create library (Apache-2.0) | REPOSITORY_AVAILABLE (SOURCE_READ via prior session + structure re-check) |

## Repository discovery rule record (§18)

For rows 17, 18, 23, 24 the canonical URL was taken from MiniAndroid's own
research records (`docs/research/COMPATIBILITY_REFERENCE_MATRIX.md`, Task 9-a
session) **before** any fresh fetch, then re-verified by cloning.
For rows 20–22 the same rule was applied and produced **no** verifiable
identity; per law they are marked `REPOSITORY_URL_UNVERIFIED` and no
similarly-named project was substituted.

## License summary (re-verified this session where a LICENSE file was present in the clone)

| Project | License at studied revision | Consequence for MiniAndroid (MIT) |
|---|---|---|
| WineDroid | Apache-2.0 | concepts AND code patterns adaptable with attribution |
| AOSP family (fw base, ART, dalvik, fw native, qemu/cuttlefish/AVF) | Apache-2.0 (qemu also carries GPL components inherited from upstream QEMU for the guest device models) | Apache parts adaptable; qemu GPL parts = concepts only |
| CrosVM | BSD-3-Clause | adaptable with attribution |
| Waydroid | GPL-3.0 | concepts only, zero import |
| JADX | Apache-2.0 | adaptable (oracle-first policy retained) |
| APKTool | Apache-2.0 | adaptable |
| Bundletool | Apache-2.0 | adaptable |
| DroidSaw | BSD-3-Clause | adaptable with attribution |
| Skydnir | custom "all rights reserved" | observation only |
| DroidVM | GPL-3.0 (README) | concepts only |
| droidsaw companion crates | BSD-3-Clause per README | adaptable |
| ARSCLib / auxten libarsc | Apache-2.0 | adaptable |
| SimulaVR/sim-use | unknown (repository unavailable) | n/a |
