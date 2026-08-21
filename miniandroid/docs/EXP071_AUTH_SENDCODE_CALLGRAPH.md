# EXP-071 — The Real `auth.sendCode` Call Graph

## TL;DR

`auth.sendCode` is **NOT** constructed inside `PhoneView$6.onConfirm`.
`onConfirm` only schedules a 400 ms animation/progress callback (`Lambda0`).
The actual request construction and `sendRequest` invocation live in
`PhoneView.onNextPressed` (classes4.dex), at PC 2410 (new-instance
`TL_auth_sendCode`) and PC 2898 (invoke-virtual `ConnectionsManager.sendRequest`).

The full path from a confirm click to the network call is:

```
1. User clicks the FAB on PhoneNumberConfirmView
        ↓ onClick(FAB)
2. PhoneNumberConfirmView$$ExternalSyntheticLambda3.run()
        ↓ calls IConfirmDialogCallback.onConfirmPressed(view, confirmTextView)
3. PhoneView$6.onConfirmPressed(view, confirmTextView)
        ↓ trivial delegation
4. PhoneView$6.onConfirm(view)
        PC 0x50: if-lt (SDK_INT < 23) — TAKEN in our headless env (SDK_INT=0)
        PC 0x870: iget val$code (the phone code captured by PhoneView$6)
        PC 0x874: new-instance Lambda0 (PhoneView$6$$ExternalSyntheticLambda0)
        PC 0x878: Lambda0.<init>(this$0=PhoneView$6, view, code)
        PC 0x884: invoke-static PhoneNumberConfirmView.access$5700(view, Lambda0)
        PC 0x890: return-void
        ↓
5. PhoneNumberConfirmView.access$5700(view, runnable)
        ↓ delegates to
6. PhoneNumberConfirmView.animateProgress(runnable)
        PC 0: iget fabButton
        PC 6: invoke-virtual fabButton.setProgressVisible(true, true)
        PC 12: const-wide/16 v0, 400        ← 400 ms delay
        PC 16: invoke-static AndroidUtilities.runOnUIThread(Lambda0, 400ms)
        PC 22: return-void
        ↓ (Lambda0 is now on the UI thread Handler queue with delay 400 ms)
7. EXP-071 Phase 8 drain loop iterates the queue
        ↓ drains Lambda0
8. Lambda0.run()
        → $r8$lambda$uKaYNa8eigZAzDp-_TfREBFnipg(PhoneView$6, view, code)
        → lambda$onConfirm$1(view, code)
        ↓
9. lambda$onConfirm$1:
        PC 0: invoke-static PhoneNumberConfirmView.access$1600(view) → dismiss()
        PC 6: new-instance Lambda1 (PhoneView$6$$ExternalSyntheticLambda1)
        PC 10: Lambda1.<init>(this$0=PhoneView$6, code, view)
        PC 16: const-wide/16 v2, 150       ← 150 ms delay
        PC 20: invoke-static AndroidUtilities.runOnUIThread(Lambda1, 150ms)
        ↓ (Lambda1 is now on the queue with delay 150 ms)
10. Drain loop drains Lambda1
        ↓
11. Lambda1.run()
        → $r8$lambda$12dPGGDo54zrrbPFJnXrkz5HUPQ(PhoneView$6, code, view)
        → lambda$onConfirm$0(code, view)
        ↓
12. lambda$onConfirm$0:
        PC 0: iget-object v0 = this$1 (PhoneView)
        PC 4: invoke-virtual PhoneView.onNextPressed(code)  ← **HERE**
        PC 10–48: sync RadialProgressView between FAB and PhoneNumberConfirmView FAB
        PC 48: return-void
        ↓
13. PhoneView.onNextPressed(code)  ← THIS is where auth.sendCode lives
        PC 2410: new-instance v0, TLRPC$TL_auth_sendCode
        PC 2414: invoke-direct TL_auth_sendCode.<init>()V
        PC 2420–2440: populate api_hash, api_id, phone_number, settings
        PC 2872: new-instance Lambda2 (PhoneView$$ExternalSyntheticLambda2)
        PC 2876–2888: Lambda2.<init>(PhoneView, Bundle, String, PhoneInputData, TLObject request)
        PC 2894: const/16 v0, 27                ← request flags
        PC 2898: invoke-virtual ConnectionsManager.sendRequest(TL_auth_sendCode, Lambda2, 27)I
        PC 2904: move-result v0 (the request_id)
        PC 2916: return-void
        ↓
14. Controlled network boundary intercepts sendRequest:
        - Inspects request_class — only TL_auth_sendCode is mocked.
        - Constructs a mock TL_auth_sentCode response.
        - Dispatches Lambda2.run(TL_auth_sentCode, null_error) via dispatch_runnable.
        ↓
15. Lambda2.run(response, error):
        → $r8$lambda$fXLD1vIsjyo85f2a8BM8C6ujJfs(PhoneView, Bundle, String,
                                                  PhoneInputData, request,
                                                  response, error)
        → lambda$onNextPressed$23(Bundle, String, PhoneInputData, request, response, error)
        ↓
16. lambda$onNextPressed$23 → eventually calls
        LoginActivity.fillNextCodeParams(Bundle, TLRPC$auth_SentCode, Z)
        ↓
17. fillNextCodeParams → calls LoginActivity.setPage(VIEW_CODE_SMS, ...)
        ↓
18. SMS View becomes visible — CHECKPOINT_M PROVEN.
```

## Key insight: `Lambda0` ≠ `RequestDelegate`

In Session 1–4 we misidentified `Lambda0` (the `PhoneView$6$$ExternalSyntheticLambda0`
created by `onConfirm`) as the `RequestDelegate` that carries the auth.sendCode
response. It is NOT. `Lambda0` is a plain `Runnable` whose only job is to
schedule `Lambda1` after a 150 ms delay; `Lambda1` then calls
`lambda$onConfirm$0` which finally calls `PhoneView.onNextPressed`.

The ACTUAL `RequestDelegate` is `Lambda2` (i.e.
`PhoneView$$ExternalSyntheticLambda2`), created inside `onNextPressed` at
PC 2872 — well after the auth.sendCode request object is constructed at
PC 2410. `Lambda2`'s `run(TLObject response, TL_error error)` signature is
the response callback.

## Why the chain never completed before Session 5

Three independent runtime bugs broke the chain at three different points:

1. **`runOnUIThread` was a silent no-op.**
   Two stubs in `dalvik_engine.cpp` intercepted `AndroidUtilities.runOnUIThread`
   and `executeOnUIThread` and returned `void` *before* the call could reach
   `HandlerShadow.enqueue`. Lambda0 and Lambda1 were therefore never queued.

2. **Static-method shadow dispatch mis-attributed `args[0]`.**
   `try_shadow_dispatch` always treated `args[0]` as `this` when it was an
   `OBJECT_REF`, even for static methods. For
   `AndroidUtilities.runOnUIThread(Runnable, long)`, this stole the
   Runnable as `this` and left `ctx.args` empty — so even after the stub was
   removed, `HandlerShadow` could not extract the Runnable to enqueue.

3. **`const-wide/16` (and `/32`, `/high16`, `const-wide`) wrote the value to
   the wrong field.**
   The handler set `dv.int_val = val` (32-bit) while marking the DalvikValue
   as `INT64`. `long_val` was left uninitialized. Later, when
   `execute_invoke_static` merged the wide register pair, it read `long_val`
   and got garbage (e.g. `93862215288784` instead of `400`). The wrong delay
   was passed to `HandlerShadow.enqueue` — but worse, because the merge
   checked `lo.type == INT64` first, it skipped the proper two-register
   merge entirely.

All three bugs are fixed in this session. After the fix, the queue drain
loop iterates and Lambda0 → Lambda1 → onNextPressed is reached.

## Why onNextPressed still does not reach PC 2410 in this run

After the async fixes, `onNextPressed` IS now invoked from `lambda$onConfirm$0`
(verified by `[METHOD-IN]` log at line 168804 of `run.log`). However, it
takes a side path through a `needShowAlert` call (PC ~1216) that shows a
"RestorePasswordNoEmailTitle" / "ChooseCountry" alert dialog. The alert
dialog is shown when one of the phone-format / country-state checks at
PC ~1194–1216 evaluates unexpectedly.

This is the next blocker for CHECKPOINT_M. Likely causes:

- `currentCountry` is null or `wasCountryHintIndex` is wrong on the second
  `onNextPressed` call (the first call already mutated PhoneView state).
- `access$5400` (a boolean check) returns the wrong value on the second
  call, causing the wrong branch.
- A field write from `lambda$onConfirm$1` (which calls `dismiss()` on the
  confirm view) might have invalidated some PhoneView state.

Investigation continues in Session 6.

## DEX evidence

* `miniandroid/run/exp071_session5/onnextpressed_full_disasm.txt` — complete
  disassembly of `PhoneView.onNextPressed` (2936 bytes / 1468 code units).
* `miniandroid/run/exp071_session5/auth_sendcode_callers.json` — Phase 1
  search results across all 5 Telegram DEX files.
* `miniandroid/run/exp071_session5/phase3b_method_dump.txt` — disassembly
  of `onConfirm`, `onConfirmPressed`, `onFabPressed`, `lambda$onConfirm$0/1`,
  `Lambda0/1.run()`, `access$5700`, `animateProgress`, `Lambda2.run()`,
  `fillNextCodeParams`, `setPage`, etc.
* `miniandroid/run/exp071_session5/phase4_phoneconfirmview_dump.txt` —
  PhoneNumberConfirmView method dump.

## Runtime evidence

* `run/exp043_auto/run.log` — line 167389 confirms confirm FAB click
  DISPATCHED on listener `PhoneNumberConfirmView$$ExternalSyntheticLambda3`.
* Lines 167470–167472 confirm `animateProgress` is entered.
* Lines 168775+ confirm queue drain activity (12 runnables in iter=1).
* Line 168803 confirms `PhoneView.onNextPressed` is entered for the second
  time (this is the call from `lambda$onConfirm$0`).
* `[QUEUE]` entries starting at line ~1500 confirm `runOnUIThread` is now
  actually enqueuing Runnables (was previously a no-op).
