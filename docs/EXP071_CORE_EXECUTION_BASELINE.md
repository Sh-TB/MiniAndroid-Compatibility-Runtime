# EXP-071 Core Execution Baseline (Frozen)

**Frozen at:** commit `7353945` (EXP-077)
**Date:** 2026-08-22
**Status:** EXP071_CORE_EXECUTION_PROVEN

## Git State

- **HEAD:** `73539458e498b2048340e785a07677dd2654b0b0`
- **Branch:** main
- **Working tree:** clean (except runtime/data/shared_prefs)

## Core Execution Evidence

### 1. auth.sendCode Chain

The following execution chain is proven from the EXP-071 final_1 run:

```
phone input (+15551234567)
→ phone validation (codeField.length()==1, phoneField.length()==10)
→ confirm click on FragmentFloatingButton
→ onConfirm
→ Lambda0 → runOnUIThread(400ms) → Lambda0.run()
→ lambda$onConfirm$1 → Lambda1 → runOnUIThread(150ms) → Lambda1.run()
→ lambda$onConfirm$0 → onNextPressed #2 (1468 instructions)
→ countries.txt loaded (237 lines)
→ TL_help_getNearestDc → mock TL_nearestDc{country=US}
→ setCountry("US") → countryState=0 (LOADED)
→ TLRPC$TL_auth_sendCode.<init> — REAL auth.sendCode CONSTRUCTED
→ ConnectionsManager.sendRequest INTERCEPTED
→ mock TL_auth_sentCode{resp_id=3465}
→ Lambda2.run(response, null) — real RequestDelegate callback
→ LoginActivity.fillNextCodeParams (588 instructions)
→ LoginActivitySmsView created in view hierarchy
```

### 2. View Tree Evidence

EXP-071 final_1 view tree (2284 nodes):
- **53 SmsView-class nodes** (LoginActivitySmsView + child views)
- **183 LoginActivity nodes** (LoginActivity + all its inner classes)
- **23 PhoneView nodes** (phone input views)
- **2 FragmentFloatingButton nodes** (the Next/Confirm buttons)
- **4 text-bearing nodes:**
  - TextView: "+" (country code prefix)
  - PhoneView$1: "1" (country code)
  - PhoneView$3: "5551234567" (phone number)
  - TextView: "View"

### 3. Shadow Report

- Calls dispatched: 857,768
- Calls handled: 105,412 (12.3% coverage)
- Calls fallback: 752,356

### 4. Runtime State

- Final state: COMPLETED
- Has error: false
- Exit code: 0

### 5. Screenshot SHA256 (BROKEN — see EXP-074)

The screenshot.png SHA256 `c3c208a169a7dadd...` is a **broken PNG** (invalid IDAT zlib data, PIL cannot decode). This was proven in EXP-074 PHASE 0. The screenshot is NOT valid visual proof.

**RENDER = NOT_PROVEN**
**OCR = NOT_PROVEN**

## What IS Proven (Logic Only)

| Dimension | Status | Evidence |
|-----------|--------|----------|
| LOGIC | ✅ PROVEN | Full bytecode chain executes (onCreate → onConfirm → Lambda0/1 → onNextPressed → auth.sendCode → sendRequest → Lambda2 → fillNextCodeParams) |
| CALLBACK | ✅ PROVEN | Lambda2.run(response, null) dispatched with mock TL_auth_sentCode |
| VIEW | ✅ PROVEN | view_tree.json has 2284 nodes, 53 SmsView, 183 LoginActivity, 2 FAB |
| RENDER | ❌ NOT_PROVEN | screenshot.png is a broken PNG (invalid IDAT) |
| OCR | ❌ NOT_PROVEN | OCR was never run (broken PNG) |
| REPRODUCIBILITY | ⚠️ PARTIAL | Logic reproducible (3/3 same instruction counts). Visual NOT reproducible (same broken stub). |

## What Must Be Preserved

These generic fixes are CRITICAL and must not be broken by future changes:

1. **CollectionShadow Map.get(String)** — HashMap.get("US") returns the country entry
2. **CollectionShadow Map.put(String value)** — proper string-value storage
3. **current_invoke_is_static_ nested-call isolation** — static methods don't steal args[0] as receiver
4. **Per-DEX const-string resolution** — reads from raw DEX data, not merged table
5. **try_shadow_dispatch two-pass with is_static** — correct static vs instance dispatch
6. **HandlerShadow deterministic drain** — async Runnable scheduling works
7. **dispatch_runnable** — Lambda0/Lambda1/Lambda2 callbacks fire correctly
8. **Controlled network boundary** — sendRequest intercepted, mock response delivered

## Regression Protection

If any future change breaks the auth.sendCode chain:
1. Restore this commit (`7353945`)
2. Re-run the EXP-071 test
3. Verify 53 SmsView nodes still exist in the view tree
4. Verify Lambda2 and fillNextCodeParams still execute
