# Architectural Decision Records

Home for architectural decisions and accepted/rejected hypotheses.

Decision-type content currently lives in these canonical places:

- `runtime/EXP037_ARCHITECTURE_DECISION.md` — the JNI/ELF boundary decision
  (loader policy: boundary classification, no native-library loader).
- `architecture/` — runtime architecture notes that encode standing decisions
  (`dalvik_architecture_notes.md`, `miniandroid_vs_dalvik.md`).
- `../.agent/decisions.md` — session-level decision ledger (agent protocol state).

New ADRs should be added here as `ADR-NNN-title.md` with context, decision,
and consequences.
