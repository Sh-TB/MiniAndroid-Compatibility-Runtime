# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/tmp/s115_apks/com.fr.laboussole.track_50020.apk`
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

- **Message:** Cannot find end of central directory
- **Location:** `ApkParser.parse`
- **Fatal:** No

## Session Info

- **Session ID:** `EXP-001-20260928-054000-6312`
- **Generated:** 2026-09-28 05:40:00 UTC
