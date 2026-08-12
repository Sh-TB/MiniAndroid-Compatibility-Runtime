# EXP-022: Complete Application List Report

**Experiment:** EXP-022 APK Corpus Audit  
**Generated:** 2026-08-12T14:04:27.249684Z  
**Status:** ✅ TRANSPARENT AUDIT

---

## Executive Summary

| Metric | Count |
|--------|-------|
| **Total Applications** | 36 |
| **Real Executed** | 2 |
| **Static Analysis Only** | 34 |
| **Not Loaded** | 0 |

> ⚠️ **Transparency Note:** Most applications are PROJECTIONS/ESTIMATES based on API profiles. Only HelloWorld.apk was actually executed on MiniAndroid runtime.

---

## Complete Application Table

| APK | Package | Static Analysis | Loaded | Real Execution | Result | Source |
|-----|---------|----------------|--------|----------------|--------|--------|
| HelloWorld.apk | com.example.helloworld | YES | YES | YES | PASS | LOCAL_FILE |
| helloworld_HW-001 | com.example.helloworld.hw-001 | YES | YES | YES | PASS | EXP-020_CORPUS_PROJECTION |
| helloworld_HW-002 | com.example.helloworld.hw-002 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| helloworld_HW-003 | com.example.helloworld.hw-003 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| helloworld_HW-004 | com.example.helloworld.hw-004 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| helloworld_HW-005 | com.example.helloworld.hw-005 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| helloworld_HW-006 | com.example.helloworld.hw-006 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| helloworld_HW-007 | com.example.helloworld.hw-007 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| helloworld_HW-008 | com.example.helloworld.hw-008 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| calculator_CALC-001 | com.example.calculator.calc-001 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| calculator_CALC-002 | com.example.calculator.calc-002 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| calculator_CALC-003 | com.example.calculator.calc-003 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| calculator_CALC-004 | com.example.calculator.calc-004 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| calculator_CALC-005 | com.example.calculator.calc-005 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| notes_NOTE-001 | com.example.notes.note-001 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| notes_NOTE-002 | com.example.notes.note-002 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| notes_NOTE-003 | com.example.notes.note-003 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| notes_NOTE-004 | com.example.notes.note-004 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| notes_NOTE-005 | com.example.notes.note-005 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| todo_TODO-001 | com.example.todo.todo-001 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| todo_TODO-002 | com.example.todo.todo-002 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| todo_TODO-003 | com.example.todo.todo-003 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| todo_TODO-004 | com.example.todo.todo-004 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| settings_SET-001 | com.example.settings.set-001 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| settings_SET-002 | com.example.settings.set-002 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| settings_SET-003 | com.example.settings.set-003 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| settings_SET-004 | com.example.settings.set-004 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| games_GAME-001 | com.example.games.game-001 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| games_GAME-002 | com.example.games.game-002 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| games_GAME-003 | com.example.games.game-003 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| games_GAME-004 | com.example.games.game-004 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| games_GAME-005 | com.example.games.game-005 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| games_GAME-006 | com.example.games.game-006 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| additional_ADD-001 | com.example.additional.add-001 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| additional_ADD-002 | com.example.additional.add-002 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |
| additional_ADD-003 | com.example.additional.add-003 | YES | PARTIAL | NO | NOT EXECUTED | EXP-020_CORPUS_PROJECTION |


---

## Status Legend

| Status | Meaning |
|--------|---------|
| **REAL_EXECUTED** | APK file exists, was loaded into MiniAndroid, DEX instructions executed |
| **STATIC_ONLY** | APK metadata analyzed, DEX structure examined, but NOT executed |
| **LOADED_ONLY** | APK parsed but onCreate not called |
| **UNKNOWN** | Insufficient data to determine status |

---

*Report generated by EXP-022 audit pipeline*
