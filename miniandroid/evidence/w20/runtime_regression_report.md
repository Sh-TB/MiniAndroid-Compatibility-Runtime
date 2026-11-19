# W20 runtime regression report — baseline state
- Build: exit=0 539.7s / peak 1.46GB (evidence/w20/w20_k_build.log).
- test-all: 48 tests (43 prior + 5 W20-K contract tests) — final tally in
  evidence/w20/w20_k_testall_tail.txt (2 pre-existing font-env failures
  s98/s106 are lineage failures, unchanged).
- Dev profile parity (prior session): 5-APK gate 11/11 hashes identical at
  the -O0 dev profile.
- APK spot-checks this session: evidence/w20/k_apk/ (SolitaireCG 3x + pz).
- Build metrics stay SEPARATE from runtime metrics (mission rule).
