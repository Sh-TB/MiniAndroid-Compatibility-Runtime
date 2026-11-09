# CODER 8 — S200 wave-15 unified diff part 2/11 — the waves-11+12+13+14+15 cumulative REBASED patch vs main `9bc2a115` (SHA256 `0aca6d8ce05707f8e53d69e0f57b7c2251f2371fe7f714d1e557c922e102b86a`; concatenate 1→11 then apply ONCE)

```diff
+                          << simple << "\" (oid-identity law)" << std::endl;
+            }
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+
+        // ── F-C8-213 — kotlinx Dispatchers shapes ───────────────────────
+        // kotlinx-coroutines law (Dispatchers.kt): getDefault/getIO/getMain
+        // /getUnconfined answer the singleton dispatcher objects. 51 + 30 +
+        // 6 + 6 sites / 3 APKs. Laws: four REAL singleton dispatcher
+        // objects (identity-stable); dispatch() rides the one-queue law —
+        // Unconfined runs the block INLINE (the unconfined contract),
+        // Default/IO enqueue on the deterministic queue, Main posts on the
+        // MAIN looper queue (AOSP Looper.getMainLooper law); isDispatch
+        // Needed: Unconfined false, everything else true (kotlinx contract).
+        if (class_name == "Lkotlinx/coroutines/Dispatchers;" &&
+            (method == "getDefault" || method == "getIO" ||
+             method == "getMain" || method == "getUnconfined")) {
+            const std::string cls =
+                method == "getDefault"
+                    ? "Lkotlinx/coroutines/Dispatchers$Default;"
+                    : method == "getIO"
+                          ? "Lkotlinx/coroutines/Dispatchers$IO;"
+                          : method == "getMain"
+                                ? "Lkotlinx/coroutines/Dispatchers$Main;"
+                                : "Lkotlinx/coroutines/Dispatchers$Unconfined;";
+            uint32_t d = get_or_create_singleton(cls).object_id;
+            if (d == 0) {
+                d = heap_.allocate(cls, pc_, 0);
+            }
+            if (c8_kx_log_ < 8) {
+                ++c8_kx_log_;
+                std::cerr << "[C8-KX] Dispatchers." << method
+                          << " → o" << d << " (" << cls << ")"
+                          << std::endl;
+            }
+            result = DalvikValue::make_object(d, cls);
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        if (class_name.rfind("Lkotlinx/coroutines/Dispatchers$", 0) == 0) {
+            const uint32_t recv =
+                (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
+                    ? args[0].object_id : 0;
+            if (method == "dispatch" && recv != 0) {
+                // dispatch(context, block) — block = LAST object arg.
+                uint32_t blk = 0;
+                for (auto it = args.rbegin(); it != args.rend(); ++it) {
+                    if (it->type == DalvikType::OBJECT_REF &&
+                        it->object_id != 0 && it->object_id != recv) {
+                        blk = it->object_id;
+                        break;
+                    }
+                }
+                const bool unconfined =
+                    class_name == "Lkotlinx/coroutines/Dispatchers$Unconfined;";
+                if (unconfined) {
+                    // The UNCONFINED contract: run the block inline, in the
+                    // caller's context, never re-enqueued.
+                    DalvikValue bret;
+                    DalvikExecutionResult bres;
+                    std::string bcls = "Ljava/lang/Object;";
+                    if (heap_.has_object(blk))
+                        if (const auto* b = heap_.get(blk))
+                            bcls = b->class_descriptor;
+                    std::vector<DalvikValue> bargs{
+                        DalvikValue::make_object(blk, bcls)};
+                    bool ran = try_recursive_invoke(bcls, "run", bargs, bret,
+                                                    bres, "()V");
+                    if (!ran)
+                        std::cerr << "[C8-KX] Unconfined dispatch o" << blk
+                                  << " — block NOT run (LOUD gap)"
+                                  << std::endl;
+                    std::cerr << "[C8-KX] Unconfined.dispatch o" << blk
+                              << " → INLINE (unconfined law)" << std::endl;
+                } else {
+                    if (auto* hs = shadow_registry_
+                                       ? shadow_registry_->find_as<
+                                             framework::HandlerShadow>()
+                                       : nullptr) {
+                        hs->enqueue(blk, 0, "Dispatchers.dispatch");
+                        std::cerr << "[C8-KX] " << class_name
+                                  << ".dispatch o" << blk
+                                  << " → deterministic queue (one-queue law)"
+                                  << std::endl;
+                    }
                 }
+                result = DalvikValue::make_void();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "isDispatchNeeded") {
+                const bool unconfined =
+                    class_name == "Lkotlinx/coroutines/Dispatchers$Unconfined;";
+                result = DalvikValue::make_bool(!unconfined);
                 status = ApiCallTrace::Status::IMPLEMENTED;
                 return true;
             }
         }
 
+        // ── F-C8-215/216 — kotlinx DefaultExecutor surface ──────────────
+        // kotlinx-coroutines law (DefaultExecutor.kt): the singleton
+        // EventLoop thread. getThread/getInstance answer the SAME thread
+        // object (identity law); schedule/invokeOnTimeout enqueue the
+        // block at the converted delay (the audited F-C8-207 conversion);
+        // DefaultExecutorKt.getDefaultDelay = Long.getLong(
+        // "kotlinx.coroutines.DefaultExecutor.keepAlive", 1000L) — the
+        // S72-W3 evidence path already documents the 1000L default.
+        if (class_name.rfind("Lkotlinx/coroutines/DefaultExecutor", 0) == 0) {
+            const uint32_t recv =
+                (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
+                    ? args[0].object_id : 0;
+            if (class_name == "Lkotlinx/coroutines/DefaultExecutorKt;" &&
+                (method == "getDefaultDelay" ||
+                 method == "initializeDefaultDelay")) {
+                if (c8_kx_log_ < 8) {
+                    ++c8_kx_log_;
+                    std::cerr << "[C8-KX] DefaultExecutorKt." << method
+                              << " → 1000L (keepAlive default law)"
+                              << std::endl;
+                }
+                result = DalvikValue::make_long(1000);
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "getThread" || method == "getInstance" ||
+                method == "<init>") {
+                uint32_t t = get_or_create_singleton(
+                                 "Lkotlinx/coroutines/DefaultExecutor;")
+                                 .object_id;
+                if (t == 0) {
+                    t = heap_.allocate(
+                        "Lkotlinx/coroutines/DefaultExecutor;", pc_, 0);
+                    if (auto* ts = shadow_registry_
+                                       ? shadow_registry_->find_as<
+                                             framework::ThreadShadow>()
+                                       : nullptr) {
+                        ts->note_thread_seen(t);
+                        ts->set_thread_name(t, "DefaultDispatcher");
+                        ts->set_thread_daemon(t, true);
+                    }
+                }
+                if (method == "<init>") {
+                    result = DalvikValue::make_void();
+                } else {
+                    result = DalvikValue::make_object(
+                        t, "Lkotlinx/coroutines/DefaultExecutor;");
+                }
+                if (c8_kx_log_ < 8) {
+                    ++c8_kx_log_;
+                    std::cerr << "[C8-KX] DefaultExecutor." << method
+                              << " → o" << t
+                              << " (singleton thread identity law)"
+                              << std::endl;
+                }
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "schedule" ||
+                method == "invokeOnTimeout" ||
+                method == "scheduleResumeAfterDelay") {
+                // schedule(Runnable, time, unit) / invokeOnTimeout(time,
+                // block, context) — the block is POSITIONAL args[1] (the
+                // first-draft reverse scan captured the TimeUnit enum
+                // object instead of the Runnable — the wave-11 probe
+                // re-run caught it: the block never fired). The delay
+                // rides the audited exact conversion (F-C8-207).
+                uint32_t blk = (args.size() >= 2 &&
+                                args[1].type == DalvikType::OBJECT_REF)
+                                   ? args[1].object_id : 0;
+                int64_t amt = 0;
+                for (const auto& v : args) {
+                    if (v.type == DalvikType::INT64) amt = v.long_val;
+                    else if (v.type == DalvikType::INT32) amt = v.int_val;
+                }
+                DalvikValue unit = args.size() >= 4 ? args[3]
+                                                    : DalvikValue();
+                if (method != "schedule") unit = DalvikValue();
+                int64_t ms = c8_unit_ms(DalvikValue::make_long(amt), unit);
+                if (method != "schedule") ms = amt;  // nanos form
+                if (auto* hs = shadow_registry_
+                                   ? shadow_registry_->find_as<
+                                         framework::HandlerShadow>()
+                                   : nullptr) {
+                    hs->enqueue(blk, ms, "DefaultExecutor.schedule");
+                    std::cerr << "[C8-KX] DefaultExecutor." << method
+                              << " block=o" << blk << " delay=" << ms
+                              << "ms (deterministic-queue law)" << std::endl;
+                }
+                result = DalvikValue::make_void();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "isShutDown" || method == "isShutdownRequested" ||
+                method == "isShuttingDown") {
+                // [S197-C8] F-C8-269 — reads the REAL shutdown state the
+                // shutdownError law stamps (the wave-8 constant-false
+                // contract preserved for the pre-shutdown executor).
+                result = DalvikValue::make_bool(c8_defexec_shutdown_);
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "isEmpty") {
+                // Serialized law: the queue drain empties at every
+                // boundary — the executor's task queue is empty between
+                // boundaries (LOUD: the concurrent truth is unknowable).
+                std::cerr << "[C8-KX] DefaultExecutor.isEmpty → true "
+                             "(serialized boundary law)" << std::endl;
+                result = DalvikValue::make_bool(true);
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "dispatch" || method == "dispatchYield" ||
+                method == "enqueue" || method == "acknowledgeShutdownIfNeeded" ||
+                method == "notifyStartup" || method == "shutdown") {
+                if (method == "dispatch" || method == "dispatchYield" ||
+                    method == "enqueue") {
+                    uint32_t blk = 0;
+                    for (auto it = args.rbegin(); it != args.rend(); ++it) {
+                        if (it->type == DalvikType::OBJECT_REF &&
+                            it->object_id != 0 && it->object_id != recv) {
+                            blk = it->object_id;
+     
+                        }
+                    }
+                    if (auto* hs = shadow_registry_
+                                       ? shadow_registry_->find_as<
+                                             framework::HandlerShadow>()
+                                       : nullptr)
+                        hs->enqueue(blk, 0, "DefaultExecutor.dispatch");
+                    std::cerr << "[C8-KX] DefaultExecutor." << method
+                              << " block=o" << blk
+                              << " → deterministic queue" << std::endl;
+                } else {
+                    std::cerr << "[C8-KX] DefaultExecutor." << method
+                              << " → loud no-op boundary (serialized model)"
+                              << std::endl;
+                }
+                result = DalvikValue::make_void();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+        }
+
+        // ── F-C8-217 — CoroutineScheduler$WorkerState enum surface ──────
+        // The 6 constants materialize via the kOrdinals CYCLE-E law
+        // (sget-object). The valueOf(String)/values()/ordinal() accessors
+        // complete the enum contract (identity-coherent with the sget
+        // law — same cached objects).
+        if (class_name.rfind(
+                "Lkotlinx/coroutines/scheduling/CoroutineScheduler$WorkerState",
+                0) == 0) {
+            if (method == "ordinal") {
+                const uint32_t recv =
+                    (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
+                        ? args[0].object_id : 0;
+                DalvikValue ov = c8_getf(recv, "ordinal");
+                result = DalvikValue::make_int(
+                    ov.type == DalvikType::INT32 ? ov.int_val : 0);
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "valueOf") {
+                const std::string nm =
+                    (!args.empty() && args[0].type == DalvikType::STRING_REF)
+                        ? args[0].string_val : "";
+                static const struct {
+                    const char* n;
+                    int o;
+                } kStates[6] = {{"INIT", 0}, {"SLEEPING", 1}, {"PARKING", 2},
+                                {"CPU_ACQUIRED", 3}, {"BLOCKING", 4},
+                                {"TERMINATED", 5}};
+                for (const auto& s : kStates) {
+                    if (nm == s.n) {
+                        uint32_t e = heap_.allocate(class_name, pc_, 0);
+                        heap_.set_object_field(
+                            e, "ordinal", DalvikValue::make_int(s.o));
+                        heap_.set_object_field(
+                            e, "enum_name",
+                            DalvikValue::make_string(s.n, 0));
+                        result = DalvikValue::make_object(e, class_name);
+                        status = ApiCallTrace::Status::IMPLEMENTED;
+                        return true;
+                    }
+                }
+                result = DalvikValue::make_null();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "values") {
+                static const struct {
+                    const char* n;
+                    int o;
+                } kStates[6] = {{"INIT", 0}, {"SLEEPING", 1}, {"PARKING", 2},
+                                {"CPU_ACQUIRED", 3}, {"BLOCKING", 4},
+                                {"TERMINATED", 5}};
+                const uint32_t arr = heap_.allocate(
+                    "[Lkotlinx/coroutines/scheduling/CoroutineScheduler$"
+                    "WorkerState;", pc_, 0);
+                heap_.set_object_field(arr, "__array_length__",
+                                       DalvikValue::make_int(6));
+                for (int i = 0; i < 6; ++i) {
+                    uint32_t e = heap_.allocate(class_name, pc_, 0);
+                    heap_.set_object_field(e, "ordinal",
+                                           DalvikValue::make_int(i));
+                    heap_.set_object_field(e, "enum_name",
+                                           DalvikValue::make_string(
+                                               kStates[i].n, 0));
+                    heap_.set_object_field(
+                        arr, "array[" + std::to_string(i) + "]",
+                        DalvikValue::make_object(e, class_name));
+                }
+                result = DalvikValue::make_object(
+                    arr,
+                    "[Lkotlinx/coroutines/scheduling/CoroutineScheduler$"
+                    "WorkerState;");
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+        }
+
+        // ── F-C8-205 — java.util.concurrent.ExecutorCompletionService ───
+        // OpenJDK law (ExecutorCompletionService.java): submit() wraps the
+        // task, runs it, and puts the COMPLETED Future on the internal
+        // completion queue; take()/poll() dequeue in COMPLETION order.
+        // Serialized law (S188-W3 inline-run precedent): submit runs the
+        // task inline via the REAL DEX body, completes the Future, and
+        // appends it to the engine-member completion queue; take/poll
+        // dequeue head-first (take on an EMPTY queue = loud boundary —
+        // the concurrent blocking wait has no serialized counterpart).
+        if (class_name == "Ljava/util/concurrent/ExecutorCompletionService;") {
+            const uint32_t recv =
+                (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
+                    ? args[0].object_id : 0;
+            if (method == "<init>") {
+                if (recv != 0)
+                    std::cerr << "[C8-ECS] new ExecutorCompletionService o"
+                              << recv << " (completion-queue law)" << std::endl;
+                result = DalvikValue::make_void();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "submit" && recv != 0) {
+                // submit(Callable|Runnable[, result]) — task = FIRST
+                // object arg; result (optional) = SECOND object arg.
+                uint32_t task = 0, pres = 0;
+                std::vector<uint32_t> objs;
+                for (size_t i = 1; i < args.size(); ++i) {
+                    if (args[i].type == DalvikType::OBJECT_REF &&
+                        args[i].object_id != 0)
+                        objs.push_back(args[i].object_id);
+                }
+                if (!objs.empty()) task = objs[0];
+                if (objs.size() >= 2) pres = objs[1];
+                // Mint the FutureTask box (the wave-5 FutureRecord law
+                // owns its lifecycle; here we complete it INLINE).
+                uint32_t fut = heap_.allocate(
+                    "Ljava/util/concurrent/FutureTask;", pc_, 0);
+                if (heap_.has_object(task)) {
+                    const auto* tobj = heap_.get(task);
+                    // Run the REAL task body. R8-renamed anonymous classes
+                    // carry no 'Callable' substring — try the Callable
+                    // contract FIRST (call), then the Runnable contract
+                    // (run); the wave-11 probe re-run documented a
+                    // ran=NO when the name-shape check picked run() for a
+                    // Callable (future completed with an empty result).
+                    DalvikValue cret;
+                    DalvikExecutionResult cres;
+                    std::vector<DalvikValue> cargs{
+                        DalvikValue::make_object(task,
+                                                 tobj->class_descriptor)};
+                    bool ran = try_recursive_invoke(tobj->class_descriptor,
+                                                    "call", cargs, cret,
+                                                    cres);
+                    if (!ran)
+                        ran = try_recursive_invoke(tobj->class_descriptor,
+                                                   "run", cargs, cret,
+                                                   cres);
+                    // Complete the Future through the SAME channel the
+                    // submit→Future law uses (future_results_ — the
+                    // F-C8-149 isDone + Future.get laws read it).
+                    future_results_[fut] = cret;
+                    std::cerr << "[C8-ECS] submit o" << task
+                              << " (call→run contract)"
+                              << " ran=" << (ran ? "yes" : "NO")
+                              << " → future o" << fut
+                              << " COMPLETED (inline law)" << std::endl;
+                }
+                // Completion-order append (OpenJDK QueueingFuture.put).
+                c8_ecs_queue_[recv].push_back(fut);
+                result = DalvikValue::make_object(
+                    fut, "Ljava/util/concurrent/FutureTask;");
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if ((method == "take" || method == "poll") && recv != 0) {
+                auto& q = c8_ecs_queue_[recv];
+                if (q.empty()) {
+                    if (method == "take") {
+                        std::cerr << "[C8-ECS] take on EMPTY completion "
+                                     "queue — LOUD boundary (serialized "
+                                     "model: nothing will complete later)"
+                                  << std::endl;
+                        result = DalvikValue::make_null();
+                    } else {
+                        result = DalvikValue::make_null();
+                    }
+                    status = ApiCallTrace::Status::IMPLEMENTED;
+                    return true;
+                }
+                const uint32_t fut = q.front();
+                q.erase(q.begin());
+                std::cerr << "[C8-ECS] " << method << " → future o" << fut
+                          << " (completion order)" << std::endl;
+                result = DalvikValue::make_object(
+                    fut, "Ljava/util/concurrent/FutureTask;");
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+        }
+
+        // ── F-C8-206 — MessageQueue IdleHandler family (port-back) ──────
+        // AOSP law (MessageQueue.java): addIdleHandler(handler) registers
+        // an IdleHandler; when the queue runs out of messages the looper
+        // dispatches queueIdle() on each registered handler IN REGISTRATION
+        // ORDER; a false return removes the handler. Wave-3 carried this
+        // law on the OLD line; THIS line (bare d3a8d0ec + waves 8..10)
+        // never received the port — addIdleHandler fell through as silent
+        // void and the idle episode never dispatched. The dispatch point
+        // lives at the frame-boundary pump (execution_engine.cpp): a
+        // boundary whose drain found ZERO entries = the idle episode.
+        if (class_name == "Landroid/os/MessageQueue;" &&
+            (method == "addIdleHandler" || method == "removeIdleHandler")) {
+            const uint32_t recv =
+                (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
+                    ? args[0].object_id : 0;
+            uint32_t h = 0;
+            for (size_t i = 1; i < args.size(); ++i) {
+                if (args[i].type == DalvikType::OBJECT_REF &&
+                    args[i].object_id != 0) {
+                    h = args[i].object_id;
+                    break;
+                }
+            }
+            if (method == "addIdleHandler") {
+                if (h != 0) {
+                    c8_idle_handlers_.push_back(h);
+                    std::cerr << "[C8-IDLE] addIdleHandler o" << h
+                              << " (queue o" << recv
+                              << ", registry=" << c8_idle_handlers_.size()
+                              << ")" << std::endl;
+                }
+            } else {
+                bool removed = false;
+                for (auto it = c8_idle_handlers_.begin();
+                     it != c8_idle_handlers_.end(); ++it) {
+                    if (*it == h) {
+                        c8_idle_handlers_.erase(it);
+                        removed = true;
+                        break;
+                    }
+                }
+                std::cerr << "[C8-IDLE] removeIdleHandler o" << h
+                          << " removed=" << (removed ? "yes" : "no")
+                          << std::endl;
+            }
+            result = DalvikValue::make_void();
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+
+        // ── F-C8-207 — TimeUnit public conversion surface ───────────────
+        // OpenJDK law (TimeUnit.java): the 7 constants carry fixed
+        // conversion factors; toMillis/toNanos/toMicros/toSeconds/
+        // toMinutes/toHours/toDays truncate toward zero; convert(amount,
+        // unit) rescales across units. The c8_unit_ms DELAY helper was
+        // audited + fixed above (the wave-8..10 kFactor table floored
+        // sub-ms amounts to 0). This law completes the PUBLIC surface so
+        // app-side conversions answer the JDK truth.
+        if (class_name == "Ljava/util/concurrent/TimeUnit;" &&
+            (method == "toMillis" || method == "toNanos" ||
+             method == "toMicros" || method == "toSeconds" ||
+             method == "toMinutes" || method == "toHours" ||
+             method == "toDays" || method == "convert")) {
+            const uint32_t recv =
+                (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
+                    ? args[0].object_id : 0;
+            DalvikValue ov = c8_getf(recv, "ordinal");
+            const int ord = (ov.type == DalvikType::INT32 && ov.int_val >= 0 &&
+                             ov.int_val < 7)
+                                ? ov.int_val : 2;
+            // Unit scale in nanoseconds (JDK declaration order 0..6).
+            static const int64_t kNs[7] = {1LL, 1000LL, 1000000LL,
+                                           1000000000LL, 60000000000LL,
+                                           3600000000000LL, 86400000000000LL};
+            int64_t amt = 0;
+            if (args.size() >= 2) {
+                if (args[1].type == DalvikType::INT64)
+                    amt = args[1].long_val;
+                else if (args[1].type == DalvikType::INT32)
+                    amt = args[1].int_val;
+            }
+            if (method == "convert") {
+                // convert(amount, unit) → THIS-unit amount (JDK division
+                // law, truncating): result = amt * kNs[uord] / kNs[ord].
+                DalvikValue uv = c8_getf(
+                    (args.size() >= 3 &&
+                     args[2].type == DalvikType::OBJECT_REF)
+                        ? args[2].object_id : 0,
+                    "ordinal");
+                const int uord =
+                    (uv.type == DalvikType::INT32 && uv.int_val >= 0 &&
+                     uv.int_val < 7)
+                        ? uv.int_val : 2;
+                if (kNs[uord] >= kNs[ord]) {
+                    result = DalvikValue::make_long(
+                        amt * (kNs[uord] / kNs[ord]));
+                } else {
+                    result = DalvikValue::make_long(
+                        amt / (kNs[ord] / kNs[uord]));
+                }
+            } else {
+                // toX: convert THIS unit → target unit (JDK division law,
+                // truncating): result = amt * kNs[ord] / kNs[tgt].
+                // (The wave-11 first draft INVERTED these branches — the
+                // wave-11 probe re-run caught it: NANOSECONDS.toMillis
+                // (1500000) answered 1.5e12 instead of 1.)
+                static const int kTarget[7] = {0, 1, 2, 3, 4, 5, 6};
+                const int tgt = method == "toNanos"     ? kTarget[0]
+                                : method == "toMicros"  ? kTarget[1]
+                                : method == "toMillis"  ? kTarget[2]
+                                : method == "toSeconds" ? kTarget[3]
+                                : method == "toMinutes" ? kTarget[4]
+                                : method == "toHours"   ? kTarget[5]
+                                                        : kTarget[6];
+                if (kNs[ord] >= kNs[tgt]) {
+                    result = DalvikValue::make_long(
+                        amt * (kNs[ord] / kNs[tgt]));
+                } else {
+                    result = DalvikValue::make_long(
+                        amt / (kNs[tgt] / kNs[ord]));
+                }
+            }
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+
+
+        // AOSP law (Process.java): myPid/myUid/myTid answer the OS ids;
+        // isApplicationUid(uid) = uid >= FIRST_APPLICATION_UID (10000);
+        // setThreadPriority(tid, prio) lowers the nice level (no getter
+        // in the AOSP surface); killProcess/sendSignal terminate. 4
+        // APKs/45 sites (androguard crossref). Serialized-engine laws:
+        // ONE process → deterministic pid/uid constants; tids ride the
+        // ThreadShadow tid table (main = 1, monotonic); the kill laws
+        // are LOUD boundary records (the engine cannot suicide — never
+        // silent, never a throw: real apps call these in exit flows).
+        if (class_name == "Landroid/os/Process;") {
+            auto* ts_p = shadow_registry_
+                             ? shadow_registry_->find_as<
+                                   framework::ThreadShadow>()
+                             : nullptr;
+            if (method == "myPid" || method == "myUid" ||
+                method == "myTid" || method == "isApplicationUid" ||
+                method == "setThreadPriority" || method == "killProcess" ||
+                method == "sendSignal") {
+                static thread_local uint64_t proc_log = 0;
+                bool do_log = proc_log < 12;
+                if (method == "myPid") {
+                    if (do_log) { ++proc_log;
+                        std::cerr << "[C8-PROC] myPid → 1 (serialized "
+                                     "single-process law)" << std::endl; }
+                    result = DalvikValue::make_int(1);
+                } else if (method == "myUid") {
+                    if (do_log) { ++proc_log;
+                        std::cerr << "[C8-PROC] myUid → 10042 (app-uid "
+                                     "law, isApplicationUid-coherent)"
+                                  << std::endl; }
+                    result = DalvikValue::make_int(10042);
+                } else if (method == "myTid") {
+                    int32_t tid = ts_p
+                        ? ts_p->tid_of(ts_p->current_thread_id()) : 1;
+                    if (do_log) { ++proc_log;
+                        std::cerr << "[C8-PROC] myTid → " << tid
+                                  << " (ThreadShadow tid table)"
+                                  << std::endl; }
+                    result = DalvikValue::make_int(tid);
+                } else if (method == "isApplicationUid") {
+                    int32_t uid = (!args.empty() &&
+                                   args[0].type == DalvikType::INT32)
+                                      ? args[0].int_val : 0;
+                    // AOSP: FIRST_APPLICATION_UID = 10000.
+                    bool app = uid >= 10000;
+                    if (do_log) { ++proc_log;
+                        std::cerr << "[C8-PROC] isApplicationUid(" << uid
+                                  << ") → " << app << " (AOSP 10000 law)"
+                                  << std::endl; }
+                    result = DalvikValue::make_bool(app);
+                } else if (method == "setThreadPriority") {
+                    int32_t tid = (args.size() >= 2 &&
+                                   args[0].type == DalvikType::INT32)
+                                      ? args[0].int_val : 0;
+                    int32_t prio = (args.size() >= 2 &&
+                                    args[1].type == DalvikType::INT32)
+                                       ? args[1].int_val
+                                       : (args.size() >= 1 &&
+                                          args[0].type == DalvikType::INT32
+                                              ? args[0].int_val : 0);
+                    c8_native_thread_prio_[tid] = prio;
+                    if (do_log) { ++proc_log;
+                        std::cerr << "[C8-PROC] setThreadPriority tid="
+                                  << tid << " prio=" << prio
+                                  << " (loud store — no OS nice)"
+                                  << std::endl; }
+                    result = DalvikValue::make_void();
+                } else if (method == "killProcess") {
+                    if (do_log) { ++proc_log;
+                        std::cerr << "[C8-PROC] killProcess — LOUD "
+                                     "boundary: serialized engine cannot "
+                                     "suicide; run continues" << std::endl; }
+                    result = DalvikValue::make_void();
+                } else {  // sendSignal
+                    if (do_log) { ++proc_log;
+                        std::cerr << "[C8-PROC] sendSignal — LOUD "
+                                     "boundary record (no OS signal)"
+                                  << std::endl; }
+                    result = DalvikValue::make_void();
+                }
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+        }
+
+        // ════════════════════════════════════════════════════════════════
+        // [S195-C8] WAVE 12 laws (F-C8-221..240) — androguard-driven.
+        // Baseline evidence (measured, not assumed): the wave-12 probe
+        // APK ran against the UNPATCHED wave-11 binary FIRST — 97
+        // markers, 82 PASS / 14 FAIL deterministic ×3 (marker sha16
+        // 7d52c8e53be42df1); crossref baseline on this line 2706
+        // CLASS_ABSENT / 276 PRESENT. Contracts: kotlinx-coroutines-core
+        // channels (Channels.kt/Channel.kt/ProducerScope.kt), flow
+        // (Flow.kt/Builders.kt/SharedFlow.kt), JobSupport.kt,
+        // CancellableContinuationImpl.kt, EventLoop.kt, selects/Select.kt,
+        // internal (Symbol.kt/ThreadSafeHeap.kt/ThreadContext.kt),
+        // SystemProps.kt, BuildersKt.launch, DelayKt. All laws: loud
+        // diagnostics, engine-member state (F-025), no app-specific
+        // branches (S188 rule 5).
+        // ════════════════════════════════════════════════════════════════
+        auto c8_recv = [&]() -> uint32_t {
+            return (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
+                       ? args[0].object_id : 0;
+        };
+        // 2-arg captured-block dispatch (kotlin Function2 contract: the
+        // block runs its REAL DEX invoke body — receiver + 2 params).
+        // args[0] IS the block receiver (virtual invoke — the
+        // c8_kt_block_dispatch arg shape), then the 2 lambda params.
+        auto c8_kx_block2 = [&](uint32_t blk, DalvikValue p1, DalvikValue p2,
+                                DalvikValue& ret) -> bool {
+            if (blk == 0 || !heap_.has_object(blk)) return false;
+            std::string bcls = "Ljava/lang/Object;";
+            if (const auto* b = heap_.get(blk))
+                if (!b->class_descriptor.empty())
+                    bcls = b->class_descriptor;
+            DalvikExecutionResult bres;
+            std::vector<DalvikValue> bargs{
+                DalvikValue::make_object(blk, bcls), p1, p2};
+            return try_recursive_invoke(bcls, "invoke", bargs, ret, bres);
+        };
+
+        // ── F-C8-225 — ProduceKt.produce mints a REAL ProducerScope ─────
+        // kotlinx law (Produce.kt): produce(block) creates a
+        // ProducerScope bound to a fresh channel. The serialized law
+        // mints scope+channel NOW (identity-stable); block EXECUTION is
+        // an honest boundary — the scope is an EMPTY producer, never
+        // silently "run"; the channel surface is the deterministic
+        // counterpart consumers drive.
+        if (class_name == "Lkotlinx/coroutines/channels/ProduceKt;" &&
+            (method == "produce" || method == "produce$default")) {
+            std::vector<DalvikValue> a = args;
+            if (method.rfind("$default") != std::string::npos &&
+                a.size() >= 2)
+                a.resize(a.size() - 2);
+            uint32_t blk = 0;
+            for (auto it = a.rbegin(); it != a.rend(); ++it)
+                if (it->type == DalvikType::OBJECT_REF &&
+                    it->object_id != 0) {
+                    blk = it->object_id;
+                    break;
+                }
+            uint32_t ch = heap_.allocate(
+                "Lkotlinx/coroutines/channels/Channel;", pc_, 0);
+            uint32_t scope = heap_.allocate(
+                "Lkotlinx/coroutines/channels/ProducerScope;", pc_, 0);
+            c8_kx_scope_chan_[scope] = ch;
+            heap_.set_object_field(
+                scope, "__chan__",
+                DalvikValue::make_object(
+                    ch, "Lkotlinx/coroutines/channels/Channel;"));
+            if (blk != 0)
+                heap_.set_object_field(
+                    scope, "__kt_block__",
+                    DalvikValue::make_object(blk, "Ljava/lang/Object;"));
+            std::cerr << "[C8-KXCH] produce → scope=o" << scope
+                      << " channel=o" << ch << " block=o" << blk
+                      << " (empty-producer boundary, LOUD)" << std::endl;
+            result = DalvikValue::make_object(
+                scope, "Lkotlinx/coroutines/channels/ProducerScope;");
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        // F-C8-222 — ProducerScope.send/getChannel: the REAL FIFO enqueue
+        // on the scope's channel (FIFO-order law); send-after-cancel is a
+        // LOUD rejection (kotlinx cancel law).
+        if (class_name.rfind(
+                "Lkotlinx/coroutines/channels/ProducerScope", 0) == 0) {
+            const uint32_t recv = c8_recv();
+            auto itc = c8_kx_scope_chan_.find(recv);
+            const uint32_t ch =
+                (itc != c8_kx_scope_chan_.end()) ? itc->second : 0;
+            if (method == "getChannel" && recv != 0 && ch != 0) {
+                result = DalvikValue::make_object(
+                    ch, "Lkotlinx/coroutines/channels/Channel;");
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "send" && recv != 0 && ch != 0) {
+                uint32_t val = 0;
+                for (size_t i = 1; i < args.size(); ++i)
+                    if (args[i].type == DalvikType::OBJECT_REF &&
+                        args[i].object_id != 0) {
+                        val = args[i].object_id;
+                        break;
+                    }
+                if (c8_kx_chan_cancelled_[ch]) {
+                    std::cerr << "[C8-KXCH] send scope=o" << recv
+                              << " → REJECTED (channel o" << ch
+                              << " cancelled — kotlinx cancel law)"
+                              << std::endl;
+                    result = DalvikValue::make_null();
+                } else {
+                    c8_kx_chan_buf_[ch].push_back(val);
+                    if (c8_kxch_log_ < 32) {
+                        ++c8_kxch_log_;
+                        std::cerr << "[C8-KXCH] send scope=o" << recv
+                                  << " ch=o" << ch << " val=o" << val
+                                  << " → FIFO depth "
+                                  << c8_kx_chan_buf_[ch].size()
+                                  << " (FIFO-order law)" << std::endl;
+                    }
+                    result = DalvikValue::make_void();
+                }
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+        }
+        // F-C8-221 — ReceiveChannel/ChannelIterator: identity-stable
+        // iterator per channel; hasNext/next drain the FIFO in send
+        // order; empty drain → hasNext false / next LOUD null (AOSP
+        // BlockingQueue-order contract, serialized).
+        if ((class_name.rfind(
+                 "Lkotlinx/coroutines/channels/ReceiveChannel", 0) == 0 ||
+             class_name == "Lkotlinx/coroutines/channels/Channel;")) {
+            const uint32_t recv = c8_recv();
+            if (method == "iterator" && recv != 0) {
+                uint32_t& it = c8_kx_chan_iter_[recv];
+                if (it == 0)
+                    it = heap_.allocate(
+                        "Lkotlinx/coroutines/channels/ChannelIterator;",
+                        pc_, 0);
+                std::cerr << "[C8-KXCH] iterator channel=o" << recv
+                          << " → o" << it << " (identity-stable)"
+                          << std::endl;
+                result = DalvikValue::make_object(
+                    it,
+                    "Lkotlinx/coroutines/channels/ChannelIterator;");
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "cancel" && recv != 0) {
+                c8_kx_chan_cancelled_[recv] = true;
+                std::cerr << "[C8-KXCH] cancel channel=o" << recv
+                          << " (kotlinx cancel law — no further receives)"
+                          << std::endl;
+                result = DalvikValue::make_void();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+        }
+        if (class_name ==
+                "Lkotlinx/coroutines/channels/ChannelsKt;" &&
+            method == "cancelConsumed") {
+            const uint32_t ch = c8_recv();
+            c8_kx_chan_cancelled_[ch] = true;
+            std::cerr << "[C8-KXCH] cancelConsumed channel=o" << ch
+                      << " (kotlinx cancel law)" << std::endl;
+            result = DalvikValue::make_void();
+            status = ApiCallTrace::Status::IMPLEMENTED;
+            return true;
+        }
+        if (class_name ==
+            "Lkotlinx/coroutines/channels/ChannelIterator;") {
+            const uint32_t recv = c8_recv();
+            uint32_t ch = 0;
+            for (auto& kv : c8_kx_chan_iter_)
+                if (kv.second == recv) {
+                    ch = kv.first;
+                    break;
+                }
+            if (method == "hasNext" && recv != 0) {
+                bool has = false;
+                if (ch != 0 && !c8_kx_chan_cancelled_[ch])
+                    has = !c8_kx_chan_buf_[ch].empty();
+                if (c8_kxch_log_ < 48) {
+                    ++c8_kxch_log_;
+                    std::cerr << "[C8-KXCH] hasNext o" << recv
+                              << " ch=o" << ch << " → "
+                              << (has ? "yes" : "no") << std::endl;
+                }
+                result = DalvikValue::make_bool(has);
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "next" && recv != 0) {
+                uint32_t val = 0;
+                bool has = false;
+                if (ch != 0 && !c8_kx_chan_cancelled_[ch]) {
+                    auto& buf = c8_kx_chan_buf_[ch];
+                    if (!buf.empty()) {
+                        val = buf.front();
+                        buf.erase(buf.begin());
+                        has = true;
+                    }
+                }
+                if (!has)
+                    std::cerr << "[C8-KXCH] next o" << recv
+                              << " — EMPTY drain → null (LOUD boundary)"
+                              << std::endl;
+                result = has ? DalvikValue::make_object(
+                                   val, "Ljava/lang/Object;")
+                             : DalvikValue::make_null();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+        }
+        // ── F-C8-223/224 — ChannelResult box identity family ────────────
+        // kotlinx law (ChannelResult.kt): a boxed result carries
+        // (value, closed); isSuccess = value && !closed; the mangled
+        // factory/boundary names (box-impl/unbox-impl/closed-*/success-*)
+        // mint/read the same fields — engine-law-only surface (Java probe
+        // code cannot spell the mangled names; the crossref PRESENT flip
+        // carries that half of the proof).
+        if (class_name.rfind(
+                "Lkotlinx/coroutines/channels/ChannelResult", 0) == 0) {
+            const uint32_t recv = c8_recv();
+            if (method == "<init>" && recv != 0) {
+                heap_.set_object_field(recv, "__cr_closed__",
+                                       DalvikValue::make_bool(false));
+                heap_.set_object_field(recv, "__cr_hasvalue__",
+                                       DalvikValue::make_bool(false));
+                std::cerr << "[C8-KXCH] ChannelResult.<init> o" << recv
+                          << " (fresh box law)" << std::endl;
+                result = DalvikValue::make_void();
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if ((method == "isSuccess" || method == "isSuccess-impl" ||
+                 method == "isClosed" || method == "isClosed-impl" ||
+                 method == "isFailed" || method == "isFailed-impl") &&
+                recv != 0) {
+                const bool closed =
+                    c8_getf(recv, "__cr_closed__").bool_val;
+                const bool hasval =
+                    c8_getf(recv, "__cr_hasvalue__").bool_val;
+                result = DalvikValue::make_bool(
+                    method.rfind("isSuccess", 0) == 0 ? (!closed && hasval)
+                        : method.rfind("isClosed", 0) == 0 ? closed
+                        : (closed && !hasval));
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
+            if (method == "box-impl") {
+                uint32_t box = heap_.allocate(
+                    "Lkotlinx/coroutines/channels/ChannelResult;", pc_, 0);
+                uint32_t v = 0;
+                for (const auto& av : args)
+                    if (av.type == DalvikType::OBJECT_REF &&
+                        av.object_id != 0) {
+                        v = av.object_id;
+                        break;
+                    }
+                heap_.set_object_field(box, "__cr_closed__",
+                                       DalvikValue::make_bool(false));
+                heap_.set_object_field(box, "__cr_hasvalue__",
+                                       DalvikValue::make_bool(v != 0));
+                if (v != 0)
+                    heap_.set_object_field(
+                        box, "__cr_value__",
+                        DalvikValue::make_object(v,
+                                                 "Ljava/lang/Object;"));
+                result = DalvikValue::make_object(
+                    box, "Lkotlinx/coroutines/channels/ChannelResult;");
+                status = ApiCallTrace::Status::IMPLEMENTED;
+                return true;
+            }
```