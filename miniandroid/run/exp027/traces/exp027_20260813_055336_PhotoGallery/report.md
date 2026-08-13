# MiniAndroid Execution Report

## Application

- **APK:** `/home/z/my-project/miniandroid/download/exp027_real_apks/PhotoGallery.apk`
- **Package:** `com.photogallery.app`
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
| `DexParser` | 1 |
| `ExecutionEngine` | 4 |
| `TraceEngine` | 1 |

## Top Method Calls

| Method | Calls |
|--------|-------|
| `ExecutionEngine.stage_load_apk` | 2 |
| `DexParser.parse` | 1 |
| `ExecutionEngine.stage_generate_reports` | 1 |
| `ExecutionEngine.stage_parse_dex` | 1 |
| `TraceEngine.start_session` | 1 |

## Errors & Issues

### PARSE_ERROR

- **Message:** Invalid header size: 0
- **Location:** `DexParser.parse`
- **Fatal:** No

## Session Info

- **Session ID:** `EXP-001-20260813-055336-5054`
- **Generated:** 2026-08-13 05:53:36 UTC
