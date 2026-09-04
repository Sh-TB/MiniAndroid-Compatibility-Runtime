# MiniAndroid Mission

## Goal

Build a lightweight Wine-like Android compatibility runtime that can execute
real Android applications natively on Linux without emulation.

Primary validation target: Telegram APK (org.telegram.messenger.web).

## Success Definition

A successful change is NOT a commit, refactor, unit test, or new API stub.
A successful change is: **Telegram execution moves further** — more APK loaded,
more classes executed, lifecycle advances, previous crashes disappear, deeper
crashes appear.

## Operating Mode

Autonomous runtime engineer. OBSERVE → MEASURE → UNDERSTAND → HYPOTHESIZE →
EXPERIMENT → IMPLEMENT → VERIFY → CONTINUE. Never stop after one fix.

## Hierarchy of Needs

1. APK parsing (DONE — EXP-001 to EXP-007)
2. Process startup — Application, Activity, Context (PARTIAL — EXP-019, EXP-037)
3. Managed runtime — DEX, ClassLoader, method resolution (DONE — EXP-030 to EXP-035)
4. Android framework — Activity, Service, Handler, Looper, PackageManager (PARTIAL — EXP-042)
5. Native boundary — JNI registration, native methods, .so loading (NOT STARTED)
6. Rendering — Surface, Canvas, OpenGL/Vulkan (FUTURE)

Always fix the lowest blocking layer first.

## Compatibility Philosophy

Build Android compatibility, NOT Telegram compatibility.
Never hardcode Telegram behavior. Never bypass crashes blindly.
Every fix should help other applications too.
