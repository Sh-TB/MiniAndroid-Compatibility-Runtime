# library_ecosystem — S186 permanent build-on-demand registry

Laws: S185 SQLite Rule (issue #536) + S186 directive (PART 1-15).
This directory holds METADATA ONLY (Rule 4: nothing bulky in git).
Sources/builds live in external cache dirs; every entry must be reproducible
from scripts/ + pinned upstream URL + revision.

## Files
- registry.json — one record per library, PART 2 template + 6-level status
- capability_matrix.json — capability -> consumers -> candidate -> fan-out
- dependency_graph.json — real DT_NEEDED + transitive + vendored + host natives
- locks/ — pinned revisions (upstream URL + tag + hash)
- reports/ — wave audits (WAVE1_AUDIT.json)
- scripts/ — acquisition/build recipes

## Registry snapshot (2026-11-06)
19 INTEGRATED / 22 total;
ABSENT: rlottie, SDL (no consumer proven yet — do not acquire without a real APK need).
Levels reached are command-verified: ldd + nm -D U-families + nm T-counts.

## Operations (conceptual, PART 4)
library search/inspect/acquire/build/load-test/probe/integrate/trace/prune/report
are implemented with existing project conventions: scripts/s183_build_gdx_host.sh
(fetch-if-missing) is the reference pattern for acquire+build; battery scripts are
the load-test/probe pattern; trace-before-prune is Rule 3.
