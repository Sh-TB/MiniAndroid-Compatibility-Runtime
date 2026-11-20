# BLOCKED AND PENDING — exact missing dependencies

## BLOCKED

| ID | Item | Exact blocker | Evidence already obtained | What unlocks it |
|---|---|---|---|---|
| AUD-06 | CMake graph: ~52 test links + OOM claim | cmake binary ABSENT in sandbox (tools/dl wiped by recycle) | source-level facts confirmed (AUD-01/02) | reinstall cmake; configure; count link ops; measure memory |
| AUD-26 | RC-12 ScaleType oracle verification | verifier/scaletype_oracle.py + apps/probe_scaletype ABSENT; 4 commits (46ca6258 73dcadb6 1439627a d77edba6) not in mainline | git cat-file ×4 = MISSING; files absent | obtain the coder's branch/fork containing the 4 commits |
| AUD-35 | #628 --frames 12 setGraph claim | exact TicTacToe (emmanuelmess) APK absent; substitute (itsfrz) is a different app (rc=1, 0 setGraph hits) | substitute run log preserved | original APK; then frames-12 vs mainline A/B |
| AUD-37/39 | #618 Counter / #597 OpenCalc re-verification | APK corpus absent from sandbox | tracker states fetched (both closed/open as documented) | restore handoff APK corpus |

## PENDING

| ID | Item | Missing step |
|---|---|---|
| AUD-42 | #634 drawable-reference/cycle-protection source audit | dedicated source pass per mission §C |
| AUD-47 | UBSan E-05 profile (7/7 claim) | add optional UBSAN=1 Makefile profile; rerun the 7 tests |
| AUD-49 | BUG-7 duplicate shadow_registry.h dedupe | repoint consumers to the authoritative copy + rebuild |
| AUD-29/31/33 | item-level unit tests for gravity call sites / ScrollView offsets / TypedValue reference chain | the #632 task list keeps these open per item |
| #626 PR | merge readiness | rebase onto current HEAD + gate on the dev-so path (numbers partially superseded by W24 dev-so measurements) |
