# #372 CROSS-MATCH EXECUTED — 10 deep candidates vs 538-root registry (A–F law)

STATUS: VERIFIED | RESULT: every externally-researched candidate cross-matched; NO duplicate roots created. Full machine-readable table: `docs/DEEP_ROOT_CROSSMATCH.jsonl` (commit 58b5c14e).

| Candidate | Class | Disposition |
|---|---|---|
| gralloc usage-dependent allocation | E NOT APPLICABLE | host software framebuffer; no gralloc layer |
| synchronization fences / back-pressure | E NOT APPLICABLE | deterministic pump-ordered frames |
| composition/transaction commit | E NOT APPLICABLE | no compositor; draw-order laws cover |
| RRO/idmap/resource mutation | E NOT APPLICABLE | no RRO runtime; ARSC-native resolution |
| linker namespace / DT_NEEDED | B SAME_ROOT | S-2 dlopen/JNI_OnLoad law + per-lib ELF inspection |
| Binder/system-service availability | B SAME_ROOT | #370 B5 ActiveServices/broadcasts probes |
| display/surface identity | B SAME_ROOT | surface/window-background laws |
| white/black from prerequisite mismatch | B SAME_ROOT | WS audit (see below) |
| **ABI advertisement vs execution truth** | **D NEW ROOT → R-NEW-465** | **IMPLEMENTED+TESTED** (pkginspect prerequisites; redroid-class live proof) |
| colorspace/premultiplication | C WATCH | no divergence; deliberately not implemented |

## WS-002 answer (the issue's central question)

8 corpus faces classified with first-divergence + prerequisite evidence (`docs/WS_PREREQUISITE_AUDIT.md`):
- **5 ordinary runtime roots** (prereq layer CLEAN — ViewTree/lifecycle, Compose, Fragment, WindowInsets(fixed), window chain)
- **2 environment-caused/dual** (ARM-only native without bridge — install-OK/fail-at-launch LIVE-proven on EggReturnsHome; Vulkan-native engine on GLES2-only environment)
- 1 duplicate (recorded).

White/black is therefore predominantly ordinary runtime roots in this corpus; the prerequisite layer now machine-readably separates environment-caused faces BEFORE any run (`pkginspect --apk <path> --what prerequisites` → nativeAbiVerdict + environmentMismatches + recommendedNextProbe).

Also landed under #372's contract this wave: R-NEW-463 (M3-19 CLASS_REF re-entrancy law — fossifyclock A/B-fixed) and R-NEW-464 (Method.getModifiers, PARTIAL with boundary). Final regression green at binary `4c01757e8f11c8a0`.
