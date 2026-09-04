# DO NOT REINVENT — UNIFIED_008

Every row = a problem we needed, the open-source project that already solves
it, whether WE actually tested it (not just read about it), and the decision.

| problem | existing project | what it does | tested here | decision | reason |
|---|---|---|---|---|---|
| resources.arsc full parse | **ARSCLib V1.4.0** | read/write ARSC + binary XML | **YES** — jar downloaded, ArscDump.java CLI built, gmdice table dumped | **ADOPT as oracle** | 8 types/73 entries for gmdice match MiniAndroid parser exactly; used for regression ground truth |
| ARSC decode to XML | **Apktool 3.0.3** | resource decode/rebuild | **YES** — decode run on gmdice | **ADOPT as oracle** | res/values/strings.xml = value ground truth (app_name="GM Dice"…) |
| ARSC value extraction for runtime | **androguard 4.1.4** | ARSCParser → all string/color/dimen/integer values | **YES** — in production | **ADOPT** | generated Telegram resource_values.json (11,314 strings); fixed the UNIFIED_007 "string values show names" PARTIAL |
| DEX disassembly | **androguard DEX** | full dalvik disassembly | **YES** — heavily used | **ADOPT as oracle** | root-caused all four gmdice state-change blockers from its output |
| resources.arsc value cache | own JSON file | — | n/a | **REMOVED from hand-maintenance** | now machine-generated from androguard (tools/u008_gen_resource_values.py) |
| DEX interpreter itself | *none usable* | Robolectric=JVM, art=kernel | evaluated | **BUILD GLUE ONLY** | no C++ embeddable dalvik interpreter exists; MiniAndroid's is the product |
| Compose runtime | **JetBrains Compose Multiplatform** | declarative UI on Skiko/Skia | source-reviewed | **REFERENCE ONLY (BLOCKED)** | Compose executes as compiled @Composable state machines + SlotTable; porting needs Composer+recomposer+Material3 draw — multi-month; precise blocker recorded |
| GLES 3.x on CPU | **SwiftShader 694585a** | CPU Vulkan/GLES | **YES** — cloned + cmake configure SUCCESS; compile blocked (3GB RAM) | **ADOPT ON BIGGER HOST** | exact blocker: Reactor/LLVM TUs >3GB; build recipe recorded in GLES_INVESTIGATION_008.md |
| GLES bridge alternative | **ANGLE** | GLES-on-Vulkan/desktop GL | source-reviewed | **REFERENCE** | pairs with SwiftShader (ANGLE+SwiftShader documented combo) |
| bidi | **FriBidi 1.0.16** | UAX#9 embedding levels | already ACTIVE | **KEEP** | proven (سلام دنیا, mixed bidi) |
| shaping | **HarfBuzz 10.2.0** | OpenType shaping | already ACTIVE | **KEEP** | proven |
| rasterization | **FreeType 2.13.3** | glyph outline rasterizer | already ACTIVE | **KEEP** | proven |
| Lottie | **Samsung rlottie 43075538** | Lottie player | already ACTIVE | **KEEP** | proven on Telegram SMS screen |
| PNG/JPEG/WebP | **libpng / libjpeg-turbo / libwebp** | decoders | already ACTIVE (system) | **KEEP** | no custom decoders to remove — already external |
| MP3/WAV/OGG/FLAC | **mpg123 / libsndfile** | decoders | already ACTIVE | **KEEP** | 47/47 audio tests |
| job store JSON | **nlohmann/json** | JSON read/write | already ACTIVE | **KEEP** | job server persistence |
| HTTP server for jobs | **cpp-httplib / civetweb** | embedded REST | scored | **NOT ADOPTED (yet)** | current hand-rolled REST passed 10/10 E2E; switch only if server grows |
| regex for String.split | **google/re2** | linear-time regex | identified | **ROADMAP** | current char-class split covers gmdice; re2 = upgrade when full regex needed |
| test framework | **googletest / Catch2** | C++ test harness | identified | **ROADMAP** | custom harness already zero-dep and green |
| font tables inspection | **fonttools** | CBDT/strike analysis | identified | **AUX** | used interactively for emoji fallback design |
| Java build/run for oracles | **Temurin JDK 21.0.5** | javac/javap/java | **YES** — downloaded | **AUX TOOL** | ARSCLib CLI build+run |
| GitHub API discovery | **git ls-remote** | rate-limit-free repo verification | **YES** — 114 repos verified | **ADOPTED for this env** | gh CLI absent + API limit 60/h exhausted |
