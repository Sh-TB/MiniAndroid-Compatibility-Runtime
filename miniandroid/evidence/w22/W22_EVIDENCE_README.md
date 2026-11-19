# W22 evidence directory — what is committed vs local

Committed (curated knowledge):
- `W22_FINAL_MISSION_REPORT.md` — the A/B/C/D mission report (all numbers measured).
- `W22_KNOWLEDGE_INTEGRATION_LEDGER.csv` — canonical per-finding integration ledger (24 rows).
- `W22_BUILD_BASELINE.md` + `W22_BUILD_BASELINE.csv` — B1/B2 baseline + per-TU bottleneck profile.
- `W22_BUILD_OPTIMIZATION_RESULTS.csv` — the full experiment matrix (adopted / rejected / blocked, each with its measurement).
- `build_bench.jsonl` — per-build rusage records (wall/CPU/RSS/rc per make invocation).
- `w22_w9bench.log` — dev-so cycle benchmark log (medians, phases, no-op, APK parity).
- `b6_results.jsonl` + selected logs (prod build, dev-so clean, ccache cold/warm, test-all, engine syntax check) — force-added per the W21 evidence precedent (`*.log` is gitignored; evidence logs are deliberate).

Local-only (per the S230/WP0 no-giant-export law, mirrors `evidence/s230/`):
- Repo-root `evidence/w22/issues_raw/` — the raw authenticated GitHub API exports
  (629-issue inventory pages, per-issue bodies/comments, 177 attachment PNGs).
- Repo-root `evidence/w22/patches/` + `issues_inventory.tsv` + `target_digest.md` —
  committed copies exist there AND under `download/w22/`; the repository copy of
  patches/digest/inventory IS committed (small, text-only knowledge).
- Raw per-line build logs beyond the selected set above stay local; the JSONL
  records + the report numbers are the canonical evidence.

Reproduce anything: scripts `scripts/w22_*.py|sh` (fetch/digest/extract,
reconstruct, build runner, B1 experiments, TU profile, B6 gates).
