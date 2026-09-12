# EXP-071 — Event Loop / Async Callback Semantics

## The missing piece

The MiniAndroid runtime was missing the Android UI thread Handler / event
loop semantics that Android apps rely on for scheduling work. Three
primitives were stubbed as no-ops:

- `Handler.post(Runnable)`
- `Handler.postDelayed(Runnable, long)`
- `AndroidUtilities.runOnUIThread(Runnable)` and the `(Runnable, long)`
  overload that Telegram uses for animation callbacks.

Without these, any code that posts a `Runnable` to the UI thread and
expects it to fire LATER silently dropped the runnable. The chain broke
at the first async hop.

## How Android does it

```
[Thread A] calls handler.post(runnable)
   ↓
   [Handler] enqueues the runnable on its Looper's MessageQueue,
              tagged with a `ready_at_ms` timestamp = now + delay_ms.
   ↓
[Looper loop (on the UI thread)] polls the MessageQueue.
   When a message is ready, it calls message.target.dispatchMessage(message),
   which eventually invokes runnable.run().
```

The Looper is the "event loop". For real Android apps the Looper blocks
until a message is ready; for a headless test runtime like ours, we
emulate this by draining the queue at well-defined synchronization points.

## How MiniAndroid does it (Session 5)

```
HandlerShadow (in android_shadows.cpp):
    - Holds a std::deque<QueuedRunnable> queue_.
    - enqueue(runnable_id, delay_ms, source):
        QueuedRunnable q = {runnable_id, ready_at_ms = now + delay_ms, ...};
        queue_.push_back(q);
    - drain_ready(out_drained):
        Move ready entries (ready_at_ms <= now) to a 'ready' vector.
        Return them in enqueue order (FIFO).

ApplicationRuntime (in application_runtime.cpp):
    - After each Phase (onCreate, click dispatch, etc.), call:
        drain_handler_queue_and_execute()
    - This iteratively drains the queue:
        loop:
            drained = drain_ready()
            if drained.empty(): break
            for each runnable_id in drained:
                dalvik_engine.dispatch_runnable(runnable_id)
                (which invokes run() on the heap object via try_recursive_invoke)
            repeat (the runnables may have scheduled more runnables)
        safety cap: 1000 iterations.
```

This gives us the key properties:

1. **Ordering.** Runnables are drained FIFO, matching real Android's
   MessageQueue behavior for our purposes.
2. **Re-entrancy.** When a drained Runnable's `run()` calls
   `runOnUIThread(another)`, that other runnable is enqueued and will be
   drained in a subsequent iteration of the loop.
3. **No real delays.** In our deterministic test runtime, all delays
   are treated as zero — we drain everything that's been queued. This
   matches real Android's behavior when the system is idle (the Looper
   would fire the runnable as soon as its `ready_at_ms` is reached).

## The full Telegram login async chain

The `onConfirm` → `auth.sendCode` chain is a textbook case of why event
loop support is needed:

```
PhoneView$6.onConfirm(PhoneNumberConfirmView)
    ↓
PC 0x874: new-instance Lambda0 (a Runnable)
PC 0x884: invoke-static PhoneNumberConfirmView.access$5700(view, Lambda0)
    ↓
PhoneNumberConfirmView.animateProgress(Lambda0)
    ↓
PC 16: invoke-static AndroidUtilities.runOnUIThread(Lambda0, 400ms)
    ↓ (Lambda0 is now on the queue)

[delay 400ms]

Lambda0.run()
    ↓
$r8$lambda$uKaYNa8...(PhoneView$6, view, code)
    ↓
lambda$onConfirm$1(view, code):
    PC 0: invoke-static PhoneNumberConfirmView.access$1600(view) → dismiss()
    PC 6: new-instance Lambda1 (a Runnable)
    PC 20: invoke-static AndroidUtilities.runOnUIThread(Lambda1, 150ms)
    ↓ (Lambda1 is now on the queue)

[delay 150ms]

Lambda1.run()
    ↓
$r8$lambda$12d...(PhoneView$6, code, view)
    ↓
lambda$onConfirm$0(code, view):
    PC 0: iget-object v0 = PhoneView
    PC 4: invoke-virtual PhoneView.onNextPressed(code)
    ↓
PhoneView.onNextPressed(code)
    PC 2410: new-instance TLRPC$TL_auth_sendCode
    PC 2898: invoke-virtual ConnectionsManager.sendRequest(req, Lambda2, 27)
```

Without the event loop, the chain breaks at the very first `runOnUIThread`
call. Lambda0 is enqueued but never executed, so Lambda1 is never created
and `onNextPressed` is never re-invoked.

## dispatch_runnable: a generic primitive

`DalvikExecutionEngine::dispatch_runnable(runnable_object_id, response_id=0, error_id=0)`
is a generic primitive — no Telegram-specific code. It:

1. Looks up the heap object by `runnable_object_id`.
2. Reads its `class_descriptor`.
3. Builds args:
   - For no-arg `Runnable.run()`: `args = [this]`.
   - For `RequestDelegate.run(TLObject, TL_error)`: `args = [this, response, error]`
     (or `[this, response, null]` if `error_id == 0`).
4. Calls `try_recursive_invoke(class, "run", args, ...)`.

This handles both:
- Plain `Runnable` (Lambda0, Lambda1, etc.).
- `RequestDelegate` (Lambda2, which takes the response+error pair when
  the controlled network boundary delivers a mock `TL_auth_sentCode`).

## Test observability

Every queue/drain event is logged to stderr:

- `[QUEUE] Runnable id=X enqueued (delay=Yms, queue_depth=Z, source=W)`
- `[QUEUE] Runnable id=X dequeued (ready for execution)`
- `[EXP071-DRAIN] iter=N drained M runnable(s)`
- `[EXP071-DRAIN] runnable id=X → EXECUTED`
- `[EXP071-RUN] event=RUNNABLE runnable=X class=Y args=N`
- `[EXP071-RUN] event=RUNNABLE result=DISPATCHED/FAILED class=Y`

This makes it possible to verify, end-to-end, that:

1. `runOnUIThread` was actually intercepted (not silently no-op'd).
2. The Runnable was enqueued with the correct delay.
3. The drain loop fired at the right phase.
4. `run()` was actually dispatched on the engine.

## Known limitations

- **No real time-based scheduling.** We treat all delays as zero and
  drain everything that's been queued. This is fine for deterministic
  tests but doesn't exercise time-based ordering. If a test cares about
  which of two runnables fires first, it must rely on enqueue order,
  not on delay.
- **No Looper.loop() emulation.** We don't have a real Looper that
  blocks waiting for messages. We drain at fixed synchronization points
  (after onCreate, after click dispatch, etc.). Code that expects the
  Looper to fire spontaneously (e.g. via `Handler.sendEmptyMessageDelayed`)
  won't see those messages unless we explicitly drain.
- **No cross-thread dispatch.** The `Handler` associated with a worker
  `Looper` would in real Android deliver to that worker thread. We
  deliver everything to the (only) main thread.
