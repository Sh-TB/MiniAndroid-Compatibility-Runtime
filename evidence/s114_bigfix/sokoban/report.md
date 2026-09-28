# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/tmp/apks/org.asafonov.sokoban_4.apk`
- **Package:** `UnknownApp`
- **Status:** **FAILURE** ❌

## Metrics

| Metric | Value |
|--------|-------|
| APIs Called | 0 |
| Frames Rendered | 0 |
| Execution Time | 0ms |
| Memory Peak | 0.00 B |
| Errors | 1 |
| Warnings | 0 |

## API Trace Summary

| Class | Calls |
|-------|-------|
| `ApkParser` | 1 |
| `ExecutionEngine` | 2 |
| `TraceEngine` | 1 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ApkParser.parse` | 1 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_load_apk` | 1 |
| `TraceEngine.start_session` | 1 |

## Errors & Issues

### PARSE_ERROR

- **Message:** Invalid ZIP magic bytes - not a valid APK/ZIP file
- **Location:** `ApkParser.parse`
- **Fatal:** No

## Session Info

- **Session ID:** `EXP-001-20260928-004259-1353`
- **Generated:** 2026-09-28 00:42:59 UTC
