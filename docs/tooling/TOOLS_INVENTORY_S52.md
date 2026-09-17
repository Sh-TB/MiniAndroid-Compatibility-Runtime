# TOOLS_INVENTORY_S52 — tools/ & scripts/ audit (compact)

Scope: every source-controlled tool location audited for role, duplication, and
canonical placement (S52 §10 policy). Heavy toolchains: the repo contains
**zero** LLVM/toolchain binaries (S51 purge removed them; provenance +
bootstrap documented instead).

## Locations & roles

| Location | Files | Role | Status |
|---|---|---|---|
| `tools/` (root) | 10 (`doctor.sh`, `verify/` harness + probes) | source-controlled verification harness | **CANONICAL** for generic tooling |
| `scripts/build/` | 4 | toolchain bootstrap (`bootstrap_toolchain.sh` — re-fetches aapt2/ecj/r8/robolectric from documented sources; no binaries in git) | CANONICAL |
| `scripts/test/` | 16 | battery runner + gates | CANONICAL |
| `scripts/release/` | 7 | packaging + guards | CANONICAL |
| `scripts/maintenance/` | 7 | archive/link checks | CANONICAL |
| `scripts/security/` | 6 | secret scanning | CANONICAL |
| `scripts/verify/` | 18 | verification utilities | CANONICAL |
| `scripts/forensic/` | 22 | reusable forensics (dex/try/axml dumps) | CANONICAL for forensics |
| `scripts/` root loose | 85 | **era session tools** (s27→s51 one-shot disasm/patch/register scripts, cited by session records as method evidence) | HISTORY-era; frozen. New tools must NOT land here |
| `miniandroid/scripts/` | 62 | EXP-era experiment drivers | HISTORY-era; referenced by era docs |
| `miniandroid/tools/` | ~14 | EXP-era analysis tools | HISTORY-era |
| LOCAL-ONLY (gitignored) | — | `local/ASC/` (Droid ASC venv + checkout), `tools/aapt2/`, `tools/d8/`, `tools/ecj/`, `tools/android-34.jar`, `miniandroid/build/`, `miniandroid/runtime/` | LOCAL-ONLY per policy (binaries never committed) |

## Duplication findings (S52)

| Candidate set | Result | Action |
|---|---|---|
| `scripts/dex_method_dump.py` vs `scripts/forensic/dex_method_dump.py` | DIFFER (era-evolved variants) | KEEP both — duplication NOT proven (policy: merge only after proof) |
| `scripts/dump_method.py` vs `miniandroid/tools/dump_method_bytecode.py` vs `dump_method_v2.py` | all DIFFER (v1/v2/v3 evolution) | KEEP, recorded as one era-evolution family |
| session tools vs category dirs | overlap of *purpose*, not *content* | KEEP frozen; new work goes to category dirs |

## Canonical-location rule (binding from S52)

- generic verification tooling → `tools/`
- battery/test → `scripts/test/` · forensics → `scripts/forensic/` · release →
  `scripts/release/` · maintenance → `scripts/maintenance/` · security →
  `scripts/security/`
- session one-shot scripts: only with a session ID prefix, inside the matching
  category dir, and only when cited as method evidence by a session record.
- any toolchain binary/bundle: LOCAL-ONLY + documented provenance +
  reproducible bootstrap script (see `scripts/build/bootstrap_toolchain.sh`).
