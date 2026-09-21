# Tool Utilization Matrix (S74 FOLLOW-UP §14)

Chain: Tool -> Capability -> Knowledge/Law -> Application -> Evidence.

Summary: **8 USED**, 3 RESEARCHED_ONLY, 1 AVAILABLE_NOT_USED. No inflation: unused tools are labeled.

| Tool | Verdict | Laws learned | Consumers | Note |
|---|---|---|---|---|
| androidx | **USED** | 3 | 3 | consumer chain: FragmentManager subset law; Unote/TriPeaks/Telegram androidx families |
| aosp | **USED** | 7 | 6 | consumer chain: F-148/F-149 laws -> Snake layout; F-136/F-114 laws -> Unote strings/prefs; |
| art | **USED** | 6 | 3 | consumer chain: F-141 invoke-null-receiver law -> all real-APK apps; F-146/F-147 Dooz fron |
| asc | **RESEARCHED_ONLY** | 0 | 1 | per §43: research assistant only; OBSERVED->UPSTREAM confirmations mediated through it, no |
| build-toolchain | **USED** | 0 | 5 | consumer chain: aapt2/ECJ/D8/stubs -> every fixture + snake/unote-class APK builds at HEAD |
| codesearch-toolchain | **RESEARCHED_ONLY** | 0 | 0 | source-lookup sessions only (law provenance hunts); no direct runtime consumer |
| compose | **RESEARCHED_ONLY** | 1 | 1 | studied as Dooz rendering context (APP-DOOZ-COMPOSE-CHAIN record); no Compose runtime path |
| dalvik | **USED** | 2 | 4 | consumer chain: DEX/interpreter laws -> every real-dalvik execution in the corpus |
| external-runtimes | **AVAILABLE_NOT_USED** | 0 | 0 | surveyed for semantic reference only; no adoption, no consumers — honest AVAILABLE_NOT_USE |
| kotlin | **USED** | 1 | 2 | consumer chain: Kotlin-object/property-reader laws -> Dooz/Unote chains |
| kotlinx-coroutines-atomicfu | **USED** | 1 | 1 | consumer chain: AtomicReferenceArray semantics -> Dooz state queue law record |
| openjdk | **USED** | 3 | 2 | consumer chain: F-113 SecureRandom -> gmdice roll; boxed-reader family laws |

Examples (taskbook §14):

- `AOSP -> ConstraintLayout/View measurement -> F-148/F-149 -> androidgamesnake -> screenshot + trace + replay`
- `Kotlin/Coroutines/AtomicFU -> AtomicReferenceArray semantics -> F-028 family record -> dooz -> trace/source evidence (Compose chain)`
- `external-runtimes -> (none) -> (none) -> (none) -> AVAILABLE_NOT_USED (honest)`

Machine-readable: `docs/compatibility/TOOL_UTILIZATION.json`.
