# NEXT INTEGRATION PLAN — v2.1 (dependency-ordered; S14 state)
1. **MG-011 verification closure (AUD-55)** — fix applied + battery 49/49 (S12); a direct-vs-referenced
   PathData parity test (battery extension) remains the optional follow-up.
2. **#634 MG-012 re-implementation from the documented law** — animated-vector root acceptance,
   shared resolver-layer fix (`looks_like_entry` predicate), cycle depth-guard, AVD still-frame =
   referenced VD with own attributes; port the s257 V0-V4 law rows into TEST_LAW.
3. **#295/#296/#297 stroke laws** — cap/join/trim emitters with the right-normal sign law;
   extend s257 to strokeLineJoin/trimPath rows.
4. ~~**BUG-7 dedupe (AUD-49)**~~ DONE (S14): the stale copy was committed EMPTY and had ZERO
   includers — removed, battery 49/49 re-verified. No repointing was needed.
5. **CMake WEBP parity (AUD-07)** — add -DMINIANDROID_HAVE_WEBP to CMakeLists; proof = section
   compare vs the Make build (cmake now fully exercised: AUD-52 measured + RSS + ctest done).
6. **#626 PR rebase** — wave10 dev-so profiles onto current HEAD; the 15-commit branch is the base.
7. **RC-12 / layout apps** — only from the original coder environment; no substitutes.
8. ~~**UBSAN=1 profile (AUD-47)**~~ DONE (S14): `make UBSAN=1` (-fsanitize=undefined
   -fno-sanitize-recover=all, tree build_ubsan/); E-05 probes 7/7 + old-form abort rc=
   0 machine-reproduce the hub's claim; the FULL 49-test battery built and ran
   clean under the sanitizer (probes rc=0, battery 49/49 rc=0); w15 extended to 7 engine-tested const/high16 vectors.
9. **-Werror/CI (AUD-45)** — after the R1-R4 dead-code triage.
Standing rules: ABBA order for timing claims; evidence logs force-added; Production and Dev-So
reported separately; no semantic weakening for build speed; tracker closure is never runtime proof.
