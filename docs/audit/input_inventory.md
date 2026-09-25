# R500 INPUT INVENTORY (audit/input_inventory.md)

## SOURCE FILE STATUS

The supplied research document ("500 findings" input) is NOT PRESENT as a file
in this environment. Exhaustive search trail (campaign date, this wave):

- upload/ (10 pasted/uploaded docs): none contain the graphics/500 findings
- docs/ (all subdirs incl. research/, audit/, s103/): no such file
- run/: no such file
- repo-wide symbol grep for EGL_BAD_ALLOC / DEVICE_LOST / SurfaceTexture.updateTexImage /
  triple buffering / ETC1 research claims: 0 hits outside engine code

RECOVERABLE INPUT = two sources, both authenticated:

1. SRC-A — the research-report item set recovered from the committed
   campaign record docs/s103/S103_MAXEXT_EVIDENCE.md and worklog.md:
   U-001..U-008 (8), N-001..N-005 (5), FL-001..FL-005 (5) = 18 items.
2. SRC-B — the audit directive's own explicit "MUST be independently tested"
   enumerations (sections 8-14), which quote the supplied file's items:
   graphics 37, reflection 17, DEX 18, view/window 14, resource/theme 14,
   threading/looper 13, JNI/storage 5 = 118 items.

## COUNTS

```text
claimed item count in file      = 500 (claim only)
physical findings recoverable   = 136
unique findings                 = 136 (all rows kept; duplicates LINKED not dropped)
duplicates (linked via duplicate_of) = 7
truncated / unrecoverable items = 364
actionable MiniAndroid candidates = computed after audit (see RESEARCH_500_AUDIT.json)
INPUT_TRUNCATED = YES — the file ends before item 500 / full text not recoverable.
```

RULES APPLIED (binding):
- No missing finding is invented. The 364 unrecoverable slots are recorded as
  TRUNCATED_INPUT and get no rows, no names, no fabricated content.
- Every recoverable item gets a stable ID R500-001..R500-136 and an explicit
  disposition in docs/RESEARCH_500_AUDIT.json / .md (nothing silently disappears).
- Duplicate detection links rewordings to a canonical row + ROOT_CLUSTER.

## ID MAP

| range | source | domain |
|---|---|---|
| R500-001..018 | SRC-A (research report) | U-001..U-008, N-001..N-005, FL-001..FL-005 |
| R500-019..055 | directive §8 | graphics (37) |
| R500-056..072 | directive §9 | reflection (17) |
| R500-073..090 | directive §10 | DEX/ART (18) |
| R500-091..104 | directive §11 | view/window/lifecycle (14) |
| R500-105..118 | directive §12 | resource/theme (14) |
| R500-119..131 | directive §13 | threading/looper (13) |
| R500-132..136 | directive §14 | JNI/storage/SQLite (5) |
