# CONT-156 canonical battery — telegram raw log excluded (secret guard)
The raw `run/c156/canon/telegram.log` was blocked by scripts/security/check_secrets.sh
(Authorization-shaped app-content string, same pattern as the CONT-129 adjudication).
The run itself is recorded: rc=1, face16=20ac8cbbbb692e63, anchor 20ac8cbbbb MATCH
(wall evidence in the CONT-156 wall runs), --max-seconds 60 wall parameter
(CONT-129 harness adjudication). The sanitized face + anchor verdict stand; the raw
log stays out of git per the fail-closed secret-guard law. Values were never printed.
