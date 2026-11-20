# NEXT INTEGRATION PLAN — v2 (dependency-ordered)
1. **MG-011 verification closure (AUD-55)** — this session applied the fix; the build+battery
   chain is the proof; then a direct-vs-referenced PathData parity test (battery extension).
2. **#634 MG-012 re-implementation from the documented law** — animated-vector root acceptance,
   shared resolver-layer fix (`looks_like_entry` predicate), cycle depth-guard, AVD still-frame =
   referenced VD with own attributes; port the s257 V0-V4 law rows into TEST_LAW.
3. **#295/#296/#297 stroke laws** — cap/join/trim emitters with the right-normal sign law;
   extend s257 to strokeLineJoin/trimPath rows.
4. **BUG-7 dedupe (AUD-49)** — repoint consumers to the authoritative shadow_registry.h.
5. **CMake WEBP parity (AUD-07)** — add -DMINIANDROID_HAVE_WEBP to CMakeLists; proof = section
   compare vs the Make build (cmake now available — AUD-52 infrastructure).
6. **#626 PR rebase** — wave10 dev-so profiles onto current HEAD; the 15-commit branch is the base.
7. **RC-12 / layout apps** — only from the original coder environment; no substitutes.
8. **UBSAN=1 profile (AUD-47)** — optional sanitizer profile; rerun the E-05 seven.
9. **-Werror/CI (AUD-45)** — after the R1-R4 dead-code triage.
Standing rules: ABBA order for timing claims; evidence logs force-added; Production and Dev-So
reported separately; no semantic weakening for build speed; tracker closure is never runtime proof.
