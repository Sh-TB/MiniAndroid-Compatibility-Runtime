# Decisions Log — EXP-038

## DEC-001: Use cached ZIP central directory
**Date:** 2026-08-15
**Context:** BLOCKER-023 — APK parser hangs on 82MB Telegram APK
**Decision:** Cache parsed ZIP entries in a map<string, ZipEntry> on first parse.
**Rationale:** extract_entry_from_memory currently re-parses 11,531 entries per lookup. Caching reduces this to O(1) lookup.
**Trade-offs:** Slightly more memory usage (11K entries ~1MB), but massive speed improvement.

## DEC-002: Merge DexReports for MultiDex
**Date:** 2026-08-15
**Context:** BLOCKER-024 — Only classes.dex loaded, Telegram has 5 DEX files
**Decision:** Load all classes*.dex files, parse each separately, merge into a combined DexReport.
**Rationale:** Runtime needs visibility into all 41,078 classes. Individual DexReports can't resolve cross-DEX references.
**Trade-offs:** More complex merge logic, but necessary for real app support.

## DEC-003: activity-alias tracking
**Date:** 2026-08-15
**Context:** BLOCKER-022 — Telegram uses activity-alias for launcher entries
**Decision:** Track activity-alias elements in manifest parser, use targetActivity as real entry point.
**Status:** IMPLEMENTED (commit 133ec32)
