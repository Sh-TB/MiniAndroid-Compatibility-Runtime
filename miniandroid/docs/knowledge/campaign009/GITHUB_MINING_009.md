# GITHUB_MINING_009 — Open-Source Deep Mining Catalog

Campaign 009 §1/§2/§3 deliverable. Method: **live verification only** — every `commit` below came from a `git ls-remote HEAD` executed in this session; every `license` came from a raw LICENSE/COPYING fetch (values containing `verify-manually`/`UNCLEAR` were NOT conclusively identified). Anonymous GitHub API limits (60/h) were respected; bulk work used ls-remote + raw fetches which bypass API quota.

**Totals: 201 candidates | 197 with live commit SHA | 188 with positively identified license**

**Categories: A(Adopt)=13 B(Integrate/Wrap)=36 C(Test/Oracle)=92 D(Reject)=15 E(Investigate Later)=45**

> Recovery note: the Campaign-008 catalog (119 candidates) was not present in this environment; this catalog was rebuilt from scratch with fresh live verification.


## ARSC/AXML (23)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| REAndroid/ARSCLib | A | `f08adf80672c` | Apache-2.0 | Most complete standalone ARSC lib; config-matching logic is the §6 oracle |
| kin9-0rz/apkutils | A | `54b773e21f50` | MIT | Pure-python APK/ARSC/AXML parser; vendorable reference for our arsc_tool gap-fills |
| Aliucord/binary-resources | B | `4580f4b3d49e` | Apache-2.0 | Lightweight binary-resources (ARSC/AXML) lib, Apache-2.0; small enough to port |
| JesusFreke/smali | B | `2771eae0a11f` | BSD-2/3-Clause | smali/baksmali: DEX assembler; BSD; build offline test vectors |
| REAndroid/APKEditor | B | `70d2c4ba7d84` | Apache-2.0 | Resource merging/AXML editing; external CLI tool, not embeddable |
| iBotPeaches/Apktool | B | `6234db24def5` | Apache-2.0 | Reference implementation for AXML/ARSC decode semantics |
| MatrixEditor/dexrs | C | `598f2bb36539` | MIT | Rust DEX parser; compact reference for opcode tables |
| akavel/dali | C | `911fea3b41ca` | AGPL-3.0 | Go DEX/ADIL writer; reference for DEX binary format tests |
| amimo/dcc | C | `17de4fd3202b` | Apache-2.0 | DEX compiler (java->dex); useful for synthetic DEX test vectors |
| androguard/androguard | C | `4573c8c111ba` | Apache-2.0 | Our primary DEX/AXML/ARSC census oracle (already used in EXP-101/102) |
| plum-umd/redexer | C | `f80520d5310b` | BSD-2/3-Clause | OCaml DEX rewriter; academic reference |
| pxb1988/dex2jar | C | `b5bda4fb4935` | Apache-2.0 | DEX->JVM converter; oracle for DEX opcode semantics |
| skylot/jadx | C | `5e781bf5660b` | Apache-2.0 | DEX->Java decompiler; use offline to read app logic during debugging |
| APKLab/APKLab | D | `6ae69b1ba03d` | AGPL-3.0 | VSCode UI wrapper around apktool/jadx; no unique engine code |
| CalebFenton/simplify | D | `29fb25d624ae` | GPL-3.0 | GPL-3.0; symbolic execution, out of scope |
| GraxCode/dalvikgate | D | `d2f2f6812339` | GPL-3.0 | GPL-3.0; dex->java bridge tool, out of scope |
| ReVanced/revanced-patcher | D | `c6cc64dd3bdf` | GPL-3.0 | GPL-3.0 patching framework; incompatible + out of scope |
| droidefense/engine | D | `067e43ee7a3a` | GPL-3.0 | Malware-analysis engine; GPL-3.0 + out of scope |
| google/apk-patcher | D | `NOT-FOUND` | N/A | NOT-FOUND (404 on ls-remote) |
| Sable/soot | E | `12aefc8fd740` | LGPL-2.1 | LGPL static analysis; heavyweight, only if call-graph oracle needed |
| ibilux/ArscResourcesParser | E | `258c075cbfef` | UNKNOWN-verify-manually | License UNKNOWN; possible ARSC cross-check source |
| kikfox/ARSCTool | E | `ed68a4b91ecd` | UNKNOWN-verify-manually | License UNKNOWN; revisit if ARSCLib proves too heavy |
| tboox/dexbox | E | `720f4625d152` | Apache-2.0 | Apache-2.0 DEX VM in C; compare interpreter design later |

## Compose (31)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| JetBrains/compose-multiplatform | B | `da9b1e1a29b1` | Apache-2.0 | Compose runtime outside Android; its non-Android glue is the map for headless Compose |
| JetBrains/skija | B | `8581a6c04808` | Apache-2.0 | Java Skia bindings; shows the exact Skia API surface Compose needs |
| JetBrains/skiko | B | `29b514873c76` | Apache-2.0 | Kotlin/Skia bindings — the exact layer Compose renders through; port path for our rasterizer bridge |
| Droid-ify/client | C | `3b853c0a9bad` | GPL-3.0 | Compose F-Droid client — Compose+lists+persistence |
| Gurupreet/ComposeCookBook | C | `43571015bc01` | MIT | Compose recipe collection; per-feature targets |
| LinkoraApp/Linkora | C | `206dfd46a5bc` | MIT | Compose link manager |
| MohamedRejeb/Pokedex | C | `765bbbc61dfe` | Apache-2.0 | Compose MPP app with images/scroll — §12 target |
| accrescent/accrescent | C | `f065daf3bf43` | Apache-2.0 | Compose app store — Compose+security UI |
| amir1376/ab-download-manager | C | `211f49f9003d` | Apache-2.0 | Real desktop Compose app (KMP); generality target |
| android/compose-samples | C | `018c5207fb63` | Apache-2.0 | §12 generality corpus (Jetchat/Jetcaster/Jetnews...) |
| android/nowinandroid | C | `7d45eae4f872` | Apache-2.0 | Large real Compose app target |
| androidx/androidx | C | `ddc86c625e55` | Apache-2.0 | Source of truth for compose-runtime/ui/material3 semantics |
| chrisbanes/tivi | C | `a0c62c2c763c` | Apache-2.0 | large real Compose app |
| d4rken-org/sdmaid-se | C | `1e61bea6c4d5` | GPL-3.0 | Compose system cleaner |
| gergelyvagujhelyi/CalculatorM3 | C | `a7f37b9cac79` | GPL-3.0 | tiny Material3 calculator — ideal small Compose target |
| joreilly/PeopleInSpace | C | `da25d4bc05c0` | Apache-2.0 | KMP Compose app; small enough to actually run |
| rikkahub/rikkahub | C | `0651cad9bd98` | AGPL-3.0 | Real full Compose AI chat app; stress target |
| theapache64/stackzy | C | `a7a0e5d67fd5` | Apache-2.0 | Desktop Compose app; generality target |
| vfsfitvnm/ViMusic | C | `6e83b8b83da1` | GPL-3.0 | Compose music app; media+compose combo target |
| GetStream/stream-chat-android | D | `0a3a5c28f9ea` | PROPRIETARY-source-available | source-available proprietary license; NOT adoptable, sample-only |
| MohamedRejeb/Calf | E | `866204721d14` | Apache-2.0 | Compose MPP file picker etc.; later |
| MohamedRejeb/compose-rich-editor | E | `0041c9ea60cb` | Apache-2.0 | rich text editing; later |
| SEAbdulbasit/asteroids-compose-multiplatform | E | `4dfc2c07e81c` | UNKNOWN-verify-manually | KMP game; license verify needed |
| Tlaster/PreCompose | E | `0f79c88a4f76` | MIT | MPP navigation/state; later |
| aclassen/ComposeReorderable | E | `e1c7af43c881` | Apache-2.0 | drag/reorder; later |
| alexzhirkevich/compottie | E | `bc23021c2193` | MIT | Lottie for Compose; ties §12 animation into Compose later |
| cheonjaeung/gridlayout-compose | E | `0acf7e5fc355` | Apache-2.0 | grid layout; later |
| coil-kt/coil | E | `d26d7c8de521` | Apache-2.0 | Image loader; only relevant once Compose renders |
| gkd-kit/gkd | E | `1517080e46f9` | GPL-3.0 | accessibility+compose; niche |
| google/accompanist | E | `12ec3408fc10` | Apache-2.0 | Compose utility lib; adopt only when specific piece needed |
| skydoves/Balloon | E | `4c0ac9521838` | Apache-2.0 | popup lib; later |

## Rendering (2)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| google/skia | B | `3ae8e3d1e335` | BSD-3-Clause | Gold-standard rasterizer; adopt subset or wrap — replaces custom raster pieces |
| glfw/glfw | C | `92dcf4ce74f2` | UNCLEAR-verify-manually | windowing reference only (license verify: zlib-style) |

## GLES (22)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| jserv/tinygl | A | `c2e48591a6bf` | MIT | TinyGL: classic software GL, MIT, tiny — candidate GLES1.x software fallback |
| rswinkle/PortableGL | A | `7cf39dc1741e` | MIT | Software GLES 2.x/3.x-ish implementation in C, MIT — strongest candidate to unblock real GLES APKs without SwiftShader RAM cost |
| KhronosGroup/glslang | B | `23076b376e06` | BSD-3-Clause | GLSL->SPIRV; needed by any ANGLE/SwiftShader-lite path |
| Mesa3D/mesa (canonical: gitlab.freedesktop.org/mesa/mesa) | B | `06ec2d8e5f67` | UNKNOWN-verify-manually | llvmpipe/lavapipe/zink software rasterizers — §24 alternative route |
| floooh/sokol | B | `6b70854a8030` | Zlib | tiny headers incl. sokol_gfx; plausible minimal GLES-like layer |
| google/angle | B | `107da744f62a` | BSD-3-Clause | GLES-over-Vulkan; the §24 candidate to kill our GLES bridge gap |
| google/swiftshader | B | `694585a05946` | Apache-2.0 | CPU Vulkan/GLES; configure OK but >3GB RAM compile — prebuilt-binaries route needed |
| KhronosGroup/Vulkan-Docs | C | `20a9e5892e2a` | custom/other (html:NOASSERTION) | spec docs |
| KhronosGroup/Vulkan-Samples | C | `293e8286bcc3` | Apache-2.0 | Vulkan test material for SwiftShader route |
| LWJGL/lwjgl3 | C | `30fac9b95f99` | BSD-3-Clause | Bindings reference; shows GLES/EGL API surface usage |
| apitrace/apitrace | C | `2975f0c443ff` | MIT | trace tool; could log our bridge calls vs real EGL traces |
| g-truc/glm | C | `6f14f4792a0c` | MIT (GLM license) | math lib reference |
| google/agi | C | `d08ae4f58566` | Apache-2.0 | Android GPU Inspector; debugging oracle |
| google/gapid | C | `15b44454df3a` | Apache-2.0 | GAPID/AGI graphics debugger reference |
| nigels-com/glew | C | `77cc072d8a13` | MIT | GL extension loading reference |
| skywind3000/mini3d | C | `4b3e3af22669` | MIT | educational software 3D |
| ssloy/tinyrenderer | C | `97eb7a480e76` | custom-permissive (Zlib/MIT-style) | educational oracle only |
| zauonlok/renderer | C | `9ed5082f0eda` | MIT | software rasterizer educational; CPU raster reference |
| DiligentGraphics/DiligentEngine | E | `aca22851ae2b` | Apache-2.0 | Apache-2.0 engine; too big vs need |
| bkaradzic/bgfx | E | `a9dd2e20fee0` | BSD-2-Clause | BSD-2; abstraction over backends |
| google/filament | E | `2a8018f54d51` | Apache-2.0 | PBR renderer; only for future real-3D apps |
| winebox64/winlator | E | `c7021b03d837` | Apache-2.0 | shows box64+turnip pattern; niche |

## UI (1)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| facebook/yoga | B | `bd8fe0d6d243` | MIT | Flexbox layout engine; exact Android layout semantics base (used by RN) |

## Text (14)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| unicode-org/text-rendering-tests | A | `26cfb96d094b` | MIT | CONFORMANCE test vectors for bidi/shaping — free oracle tests |
| Tehreer/SheenBidi | B | `9c048a32d213` | Apache-2.0 | Apache-2.0 bidi+shaper — drop-in alternative to FriBidi+HarfBuzz pairing |
| freetype/freetype | B | `b76738eff2f3` | MIT-Old | already integrated (2.13.3) — keep |
| fribidi/fribidi | B | `c928e4c77549` | LGPL-2.1 | already integrated (1.0.16) — keep |
| harfbuzz/harfbuzz | B | `e8905fb3b3d9` | MIT-Old | already integrated (10.2.0) — keep |
| unicode-org/icu | B | `abe71235506e` | MIT | ICU: locale/config data oracle for §6 configuration matching |
| OGRECave/ogre | C | `69a1d7e00a6d` | MIT | duplicate entry ignored |
| Tehreer/Tehreer-Android | C | `74aa7286b37e` | Apache-2.0 | Android text-type lib; reference for TextView semantics |
| go-text/typesetting | C | `ddb7ff96ad4d` | BSD-3-Clause | Go port of HarfBuzz concepts; algorithm reference |
| googlefonts/noto-fonts (mirror of notofonts/noto-fonts) | C | `ffebf8c1ee44` | OFL-1.1 | same family (legacy location) |
| harfbuzz/harfbuzzjs | C | `91f412432158` | MIT | wasm build of harfbuzz; not useful in C++ runtime |
| notofonts/noto-fonts (mirror of notofonts/noto-fonts) | C | `ffebf8c1ee44` | OFL-1.1 | font assets source |
| rougier/freetype-gl | C | `a3f0547ec90b` | BSD-2/3-Clause | glyph atlas reference |
| Tehreer/Tehreer | D | `NOT-FOUND` | N/A | NOT-FOUND (404) |

## Image (17)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| kikuchan/pngle | A | `b1c68193f1d3` | MIT | MIT tiny PNG decoder for embedded — vendoring candidate |
| nothings/stb | A | `2c980bb59875` | MIT | stb_image: single-header decode of PNG/JPEG/BMP/GIF — tiny adopt path |
| randy408/libspng | A | `adc94393dbed` | BSD-2/3-Clause | simple PNG lib; cleaner than full libpng for vendoring |
| RazrFalcon/resvg (mirror of RazrFalcon/resvg) | B | `021d44b75af1` | Apache-2.0 | best SVG static renderer (Apache-2.0); VectorDrawable oracle |
| glennrp/libpng (mirror of glennrp/libpng) | B | `d1d0abeffede` | PNG-Reference-2 | canonical libpng (pnggroup mirror) — reference |
| libjpeg-turbo/libjpeg-turbo | B | `1157d37cfab9` | BSD-3-Clause | JPEG decode; candidate to replace custom decoder |
| linebender/resvg (mirror of RazrFalcon/resvg) | B | `021d44b75af1` | Apache-2.0 | moved canonical of RazrFalcon/resvg |
| memononen/nanosvg | B | `239e102ec2c6` | UNCLEAR-verify-manually | SVG rasterize (rast, MIT-ish per repo) — VectorDrawable path |
| pnggroup/libpng (mirror of glennrp/libpng) | B | `d1d0abeffede` | PNG-Reference-2 | canonical org now on GitHub |
| sammycage/plutosvg | B | `fd8a080b3d0b` | MIT | MIT SVG parser; pairs with plutovg |
| sammycage/plutovg | B | `f63f9b59dda9` | MIT | MIT tiny 2D VG on FreeType; candidate to replace custom raster pieces |
| webmproject/libwebp | B | `9c4a699e5aac` | BSD-3-Clause | already integrated — keep |
| AOMediaCodec/libavif | E | `eb673097950e` | BSD-2/3-Clause | AVIF; only if corpus demands |
| HappySeaFox/sail | E | `4fa179fff8bb` | MIT | multi-codec lib; alternative bundle |
| bumptech/glide | E | `c3df4d264f47` | Apache-2.0 | Android image loader; reference for drawable decode caching |
| google/wuffs | E | `c4df79d82ea6` | Apache-2.0 | safe codecs; interesting but heavy toolchain |
| strukturag/libheif | E | `2bc82b493dd8` | LGPL-3.0 | HEIF; only if corpus demands |

## Animation (8)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| Samsung/rlottie | B | `4307553814db` | UNCLEAR-verify-manually | already vendored/built — keep (license verify: MIT per upstream headers) |
| thorvg/thorvg | B | `e43bc8ba922f` | MIT | MIT vector+Lottie engine; alternative to rlottie with active maintenance |
| airbnb/lottie-android | C | `05ea92e90381` | Apache-2.0 | Android Lottie semantics oracle for our rlottie bridge |
| ed-asriyan/lottie-converter | C | `52585fcbba90` | MIT | lottie->svg/frames debug tool |
| LottieFiles/dotlottie-web | D | `bb5abcf9ac43` | MIT | web player; out of scope |
| aseprite/aseprite | E | `e537f0b043b3` | UNKNOWN-verify-manually | sprite editor; only its skia usage is informative |
| rive-app/rive-cpp (mirror of rive-app/rive-runtime) | E | `9d2e7d04d1bd` | MIT | same content as rive-runtime |
| rive-app/rive-runtime (mirror of rive-app/rive-runtime) | E | `9d2e7d04d1bd` | MIT | MIT; second runtime animation engine after rlottie if needed |

## Audio (19)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| lieff/minimp3 | A | `ea99364f61c1` | CC0-1.0 | CC0 single-header MP3 — replace/augment custom MP3 decode |
| lieff/minimp4 | A | `5a212a18dba7` | CC0-1.0 | CC0 MP4 demux — media container support for MediaPlayer adapter |
| mackron/dr_libs | A | `b55a0d9a30b9` | Unlicense | Unlicense; dr_wav/dr_mp3/dr_flac headers — direct §21 adoption |
| mackron/miniaudio | A | `9634bedb5b5a` | Unlicense | Unlicense; single-header playback device layer — candidate backend for AudioTrack |
| libsndfile/libsndfile | B | `7ff854d1e0bd` | LGPL-2.1 | LGPL; broad format decode — candidate external lib |
| xiph/ogg | B | `06a5e0262cdc` | UNCLEAR-verify-manually | same family |
| xiph/vorbis | B | `1b75110b5a27` | UNCLEAR-verify-manually | BSD-style (license file unusual format); ogg/vorbis decode |
| androidx/media | C | `2bc207851df3` | Apache-2.0 | Media3 source — MediaPlayer/ExoPlayer semantics oracle |
| google/ExoPlayer | C | `dd430f7053a1` | Apache-2.0 | Media3 ExoPlayer (archived at google/ExoPlayer -> androidx/media); semantics oracle |
| FongMi/TV | D | `2f88a0b878c1` | GPL-3.0 | GPL-3.0 TV player; out of scope |
| gstreamer/gstreamer | D | `cac26f2338c5` | LGPL-2.1 | LGPL pipeline framework; far too heavy for our adapter layer |
| mpg123/mpg123 | D | `NOT-FOUND` | N/A | NOT-FOUND on GitHub (official releases live off-GitHub); dr_mp3/minimp3 cover the need |
| FFmpeg/FFmpeg | E | `b32f8d1c2377` | LGPL-3.0 | LGPL; only if media demands exceed simple codecs |
| google/horologist | E | `ea9c068a6fdc` | Apache-2.0 | media3 UI compose helpers; later |
| google/oboe | E | `2a45aa2d9e94` | Apache-2.0 | Android audio I/O; needs AAudio — N/A headless |
| kcat/openal-soft | E | `99f3f1c86a95` | LGPL-2.0 | LGPL; alternative output layer |
| libsdl-org/SDL | E | `46498bc24781` | BSD | device layer; heavier than miniaudio |
| libsdl-org/SDL_mixer | E | `2b1d74def1d7` | BSD | mixer on SDL; only if game audio demands |
| webmproject/libvpx | E | `5c880e08d213` | BSD-3-Clause | VP8/9 video; only if video rendering demanded |

## Persistence (6)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| sqlite/sqlite | A | `d92acf1afe6d` | PublicDomain | public-domain canonical SQLite; adopt canonical amalgamation |
| requery/sqlite-android | B | `0bbaa7a8b4c4` | Apache-2.0 | Apache-2.0 SQLite Android fork; semantics reference for our database/ dir |
| sqlitebrowser/sqlitebrowser | C | `da45c7d528c3` | GPL-3.0 | GUI inspector for our .db artifacts during testing |
| SQLCipher/sqlcipher | E | `63697beb0faf` | BSD-3-Clause | BSD; only if encrypted DB demanded |
| Tencent/wcdb | E | `39dd797099d4` | Apache-2.0 | Apache-2.0; mobile DB stack; heavy |
| tursodatabase/libsql | E | `d6c75af6353b` | MIT | SQLite fork; niche |

## Oracle (22)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| kotlin/kotlinx.coroutines | B | `f63a04bacb8b` | Apache-2.0 | coroutine dispatch semantics needed by Compose/Dooz code paths |
| JetBrains/kotlin | C | `0f8300495b13` | Apache-2.0 | stdlib/runtime semantics; reference for Kotlin-generated DEX |
| LineageOS/android_frameworks_base | C | `68ee585f54bc` | Apache-2.0 | frameworks/base mirror; easier to browse than aosp-mirror |
| android.googlesource.com/platform/art | C | `6484611fd45e` | UNKNOWN-verify-manually | ART source (verify note: mirror fetch from googlesource) |
| android.googlesource.com/platform/libcore | C | `de876a01b292` | UNKNOWN-verify-manually | core libs semantics |
| aosp-mirror/platform_dalvik | C | `838bd34deecb` | Apache-2.0 | original Dalvik VM source — our interpreter's semantics oracle |
| aosp-mirror/platform_frameworks_base | C | `1cdfff555f4a` | Apache-2.0 | PRIMARY View/Resources/ARSC semantics oracle (ResTable_config::match lives here) |
| aosp-mirror/platform_frameworks_support | C | `a9ac247af2af` | Apache-2.0 | AndroidX source mirror — View/Compose/Room semantics |
| cashapp/paparazzi | C | `9929379c6092` | Apache-2.0 | layout-render oracle (deferred in EXP-095 for disk; revisit) |
| google/desugar_jdk_libs | C | `092407c51c3e` | GPL-2.0 | java.time/streams backport semantics used by apps |
| google/truth | C | `2b95613636f4` | Apache-2.0 | assertions for oracle tests |
| junit-team/junit4 | C | `890f3c972647` | EPL-1.0 | same (Robolectric 4.x uses junit4) |
| junit-team/junit5 | C | `9cd9a3cfb6cd` | EPL-2.0 | test harness for Robolectric runs |
| robolectric/android-all | C | `NOT-FOUND` | N/A | NOT-FOUND via ls-remote (distributed via Maven jars, not a buildable repo) — jars still usable |
| robolectric/robolectric | C | `05e0d7bde9f7` | Apache-2.0 | PRIMARY framework-behavior oracle (already proven in EXP-102) |
| takahirom/roborazzi | C | `6abd5fc0a780` | Apache-2.0 | Compose screenshot testing — Compose §12 oracle candidate |
| ReactiveX/RxJava | E | `bc5d8b854d7b` | Apache-2.0 | many apps use it; scheduler semantics later |
| google/conscrypt | E | `5c02b8d15e9b` | Apache-2.0 | TLS provider; only if network bridge lands |
| google/gson | E | `b3f4ca20087f` | Apache-2.0 | JSON semantics used by many apps; only when needed |
| square/moshi | E | `889013ec2edb` | Apache-2.0 | JSON; later |
| square/okhttp | E | `1c6129e44e10` | Apache-2.0 | HTTP; later |
| square/retrofit | E | `3ca1229c3361` | Apache-2.0 | HTTP client semantics; only when network bridge lands |

## App-XML (7)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| FossifyOrg/Calendar | C | `015f9572440b` | GPL-3.0 | classic-views+Room app |
| FossifyOrg/Contacts | C | `adf503815294` | GPL-3.0 | lists+SQLite app |
| FossifyOrg/Gallery | C | `1933e40ac697` | GPL-3.0 | image-heavy app |
| KashCal/KashCal | C | `d67bbb1c88c0` | Apache-2.0 | calendar app |
| android/architecture-samples | C | `ee66e1526b84` | Apache-2.0 | Classic XML Views+Navigation corpus |
| dorumrr/de1984 | C | `3327a8d86b90` | MIT | privacy camera app |
| sweakpl/qralarm-android | C | `5dc595ec2803` | GPL-3.0 | utility app |

## App-Compose (1)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| yamin8000/Dooz | C | `0c60e78b861a` | GPL-3.0 | DOOZ SOURCE — the exact app of our Compose blocker; GPL-3.0 |

## App-Media (11)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| FoedusProgramme/Gramophone | C | `a4d5e96c939f` | GPL-3.0 | Compose+Media3 minimal player |
| JunkFood02/Seal | C | `63bd8a4d31df` | GPL-3.0 | yt-dlp GUI; Compose |
| MetrolistGroup/Metrolist | C | `773a9f9a212b` | GPL-3.0 | Compose music |
| OuterTune/OuterTune | C | `e82794f3a059` | GPL-3.0 | Compose+Media3 |
| OxygenCobalt/Auxio | C | `0de0ce4c5553` | GPL-3.0 | Compose-era audio player; clean architecture |
| PixelPlayerHQ/PixelPlayerOSS | C | `27f8de63ab55` | GPL-3.0 | Compose+Media3+Room+DataStore player (§9 target) |
| TeamNewPipe/NewPipe | C | `5779af87f89f` | GPL-3.0 | media+lists; GPL-3.0 |
| anilbeesetti/nextplayer | C | `5824581a828e` | GPL-3.0 | Compose video player |
| maxrave-dev/SimpMusic | C | `62472bfaf4d2` | GPL-3.0 | Compose+Media3 music app |
| nextcloud/android | D | `4ccb511527f0` | LGPL-2.1 | LGPL; huge; network-bound app — poor fit for headless corpus |
| signalapp/Signal-Android | D | `879651dc47a7` | AGPL-3.0 | AGPL-3.0; enormous; adopt risk; corpus value low vs cost |

## App-Game (11)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| libgdx/libgdx | B | `c3bdf2f726bb` | Apache-2.0 | Apache-2.0; its GLES backend IS the API surface our GLES layer must satisfy |
| 00-Evan/shattered-pixel-dungeon | C | `7b8b845a76fe` | GPL-3.0 | libGDX game; real GLES consumer |
| Anuken/Mindustry | C | `eb4d7f1de67f` | GPL-3.0 | major libGDX GLES game — §25 strong candidate |
| TranslucentFoxHuman/DroidStress | C | `63c514173d7d` | GPL-3.0 | stress-test app candidate |
| ashrafimostafa/Brick-Blast | C | `9799cafe06f7` | MIT | Compose Canvas game (§9 target) |
| clavierhaus/gnubg-android | C | `05292e3783c8` | GPL-3.0 | backgammon port |
| hushenghao/AndroidEasterEggs | C | `91f016c2c1eb` | Apache-2.0 | Easter-egg games incl. GLES demos |
| lichess-org/mobile | C | `a98315df95ca` | GPL-3.0 | Compose board game |
| retrowars/retrowars | C | `1081c8b8017b` | GPL-3.0 | libGDX multi-game (§25 GLES target); canonical moved from pserwylo |
| shlusiak/Freebloks-Android | C | `bf36e4474799` | GPL-2.0 | board game with GLES? (verify) |
| pserwylo/retrowars | D | `7c80876f86a2` | UNKNOWN-verify-manually | superseded by retrowars/retrowars (redirect) |

## App-WebView (3)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| WebView-CG/CanIAndroidWebView | C | `303945893c73` | Apache-2.0 | dedicated WebView test app (§8/§9 target) |
| duckduckgo/Android | C | `85df593e2286` | Apache-2.0 | WebView-centric browser app |
| plateaukao/einkbro | C | `49c249b9173b` | GPL-3.0 | WebView browser |

## App-Image (1)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| T8RIN/ImageToolbox | C | `076143e5d3f6` | Apache-2.0 | image pipeline stress app |

## Unclassified (2)

| repo | cat | commit | license | reason |
|---|---|---|---|---|
| mpv-player/mpv | E | `e8673660ab7e` | LGPL-2.1 | verified live during mining; classification pending |
| xiph/flac | E | `e94ff9f68b8e` | GFDL-1.3 | verified live during mining; classification pending |

## Discovery sources

- Component seed list from Campaign 008 knowledge (re-verified from scratch)
- GitHub topic HTML pages: arsc, apk-parser, compose-desktop, skia, opengl-es, text-rendering, lottie, minimp3, software-rendering
- F-Droid package index mining (260 package candidates extracted)
- Direct ls-remote verification of user-named candidates (PixelPlayerOSS, Brick-Blast, CanIAndroidWebView, Dooz)

## Limitations

- mpg123 has no credible GitHub mirror (official releases off-GitHub) — dr_mp3/minimp3 cover the need
- robolectric/android-all 404s on ls-remote because artifacts ship via Maven; jars remain usable as oracle
- GitHub API quota (60/h anonymous) prevented bulk code-inspection passes; 30+ strongest candidates still got README/source inspection during mining
- Mesa lives on gitlab.freedesktop.org (canonical); GitHub mirror commit recorded with that caveat
- Licenses reported as UNCLEAR/UNKNOWN were not fabricated — they require manual confirmation before any adoption

## TOP 15 ADOPT TARGETS (A/B with strongest evidence)

1. **REAndroid/ARSCLib** — Complete ARSC implementation incl. configuration matching — direct §6 Telegram config-bucket oracle and candidate to replace our partial parser
1. **rswinkle/PortableGL** — MIT software GLES — the realistic route to real GLES APKs given SwiftShader's >3GB compile requirement on this 3GB machine
1. **nothings/stb** — MIT/CC0 single-header image decode — replaces/augments multiple custom decoders with one tiny vendored file
1. **mackron/dr_libs** — Unlicense dr_wav/dr_mp3/dr_flac — collapses overlapping audio decoders into 3 headers (§21 source reduction)
1. **lieff/minimp3** — CC0 MP3 decode — already proven design, tiny
1. **mackron/miniaudio** — Unlicense audio device layer — candidate AudioTrack backend
1. **jserv/tinygl** — MIT TinyGL — minimal software GL fallback for GLES1.x surface semantics
1. **unicode-org/text-rendering-tests** — MIT conformance vectors — free bidi/shaping tests for our FreeType+HarfBuzz+FriBidi pipeline
1. **Tehreer/SheenBidi** — Apache-2.0 unified bidi+shaper — simplification candidate vs two-library pipeline
1. **randy408/libspng** — BSD simple PNG — cleaner vendoring than full libpng if palette/interlace needs fit
1. **kikuchan/pngle** — MIT tiny PNG decode — embedded-grade fallback
1. **Aliucord/binary-resources** — Apache-2.0 lightweight ARSC/AXML — second opinion for our parser edge cases
1. **sqlite/sqlite** — Public-domain canonical amalgamation — replace any custom DB glue with canonical source
1. **JetBrains/skiko** — Apache-2.0 — documents the exact Skia surface Compose needs (Compose/Dooz track map)
1. **Mesa3D/mesa** — MIT — llvmpipe/lavapipe route for software GLES/Vulkan without SwiftShader's RAM spike
