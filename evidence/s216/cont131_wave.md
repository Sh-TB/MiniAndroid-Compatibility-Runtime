# [CONT-131 wave] The four laws RE-LANDED on the S215d line (`01586a17`) — **apply-able T21/T22 patch parts SHIPPED this time**; PRE/POST pair measured on THIS line; golden ×3 byte-exact; the collapse face is EXTINCT on the tap chain

**Why a re-land**: the CONT-130 (`40fc17e3`) and CONT-130b (`81280736`) local commits were erased by the sandbox recycle before any push was possible. This wave re-implements all four laws on the **current main `01586a17`** (S215d tip, verified `vsync_keepalive_tick` = 0 hits on it, same grep law as the S215 verdict demanded). Local commit `62468458` carries the full delivery (laws + battery scripts + evidence); the PAT still lacks `contents:write` (push 403 — verified again this cycle), so per the T21/T22 format law the **parts ship here**.

## The parts (apply IN ORDER against `01586a17`; single `git apply` of parts 1→4 reproduces the delivery)

Each part is `git diff 01586a17 62468458 -- <file>` — verified `git apply --check` CLEAN in order on a fresh `01586a17` worktree.

**part1/4 — miniandroid/src/dex/dalvik_engine.h (76 lines)** — sha16 `4204890f8f935a17`

```diff
diff --git a/miniandroid/src/dex/dalvik_engine.h b/miniandroid/src/dex/dalvik_engine.h
index 56fc2125..0dface3c 100755
--- a/miniandroid/src/dex/dalvik_engine.h
+++ b/miniandroid/src/dex/dalvik_engine.h
@@ -2564,6 +2564,11 @@ public:
     // ────────────────────────────────────────────────────────────────────
     void awaitup_gate_begin(int64_t ms) {
         awaitup_deadline_hit_ = false;
+        // CONT-130b: fresh per-tap state — every tap re-arms the gate with
+        // the soft channel DISARMED (the previous window's soft stop left
+        // no artifact behind by law; begin() owns the reset too).
+        awaitup_soft_stop_ = false;
+        awaitup_soft_stop_active_ = false;
         if (ms > 0) {
             awaitup_deadline_ = std::chrono::steady_clock::now() +
                                 std::chrono::milliseconds(ms);
@@ -2584,6 +2589,59 @@ public:
     // Consulted by the interpreter loop next to the S60 wall check.
     void awaitup_gate_check();
 
+    // ────────────────────────────────────────────────────────────────────
+    // CONT-130b: AWAIT-UP-GATE SOFT DRAW-WINDOW STOP. Inside a draw window
+    // the gate unwinds GRACEFULLY at method boundaries — the fetch loop
+    // breaks on awaitup_soft_stop_, every enclosing frame exits by RETURN,
+    // NO exception is synthesized: the compose draw state survives the
+    // gate stop (the hard F084 unwind left MultiParagraphLayoutCache
+    // density=0.0 half-mutated and poisoned 4,685 later draws — the S215
+    // decode). The hard F084 channel remains as a DELAYED backstop (15 s
+    // grace) for a method body that never returns. Frame honesty is
+    // UNCHANGED: draw_window_budget_halted_ arms in BOTH channels (an
+    // unfinished frame is never presented — the F-NEW-298 law).
+    // ────────────────────────────────────────────────────────────────────
+    bool awaitup_soft_stop_ = false;        // armed: fetch loops break at the boundary
+    bool awaitup_soft_stop_active_ = false; // soft channel engaged in this window
+    std::chrono::steady_clock::time_point awaitup_hard_deadline_{};
+    // Draw-window boundary clear (dispatch_custom_view_draw exit): a
+    // soft-stopped window leaves NO artifact state; frame honesty stays
+    // armed for the presentation point (frame_honesty_begin owns that
+    // reset at the NEXT render pass).
+    void awaitup_soft_stop_clear() {
+        awaitup_soft_stop_ = false;
+        awaitup_soft_stop_active_ = false;
+    }
+
+    // ────────────────────────────────────────────────────────────────────
+    // CONT-130 F-NEW-277 slice-2: VSYNC-CONTINUITY KEEP-ALIVE (row #21).
+    // AOSP law: vsync belongs to the DISPLAY — a long DEX body (class-init
+    // chains, bitmap decode, big compute) must NOT starve the frame
+    // pipeline. The interpreter epilogue calls vsync_keepalive_tick();
+    // every 256K instructions (MINIANDROID_VSYNC_TICK_INTERVAL env-tunable,
+    // floor 4096) the tick fires the ONE canonical compose pump through
+    // the hook ExecutionEngine wired on the real-dalvik app path
+    // (pump_compose_frames(8) — G06 token routing + F-NEW-289 main-looper
+    // identity stay in one place, the CONT-129 re-land scope law). Guards:
+    // reentrancy flag, env opt-out (MINIANDROID_VSYNC_KEEPALIVE=0),
+    // pending-callback + queue scope guard. BYTE-INERT while the hook is
+    // unset (one null check per instruction — the CONT-42 zero-cost law).
+    // The INTERACTIVE-SESSION CLOCK (row #22 law) rides inside the tick:
+    // when a frame callback is pending AND the handler queue head is
+    // future-due, ONE bounded deterministic advance_virtual(next_ready -
+    // now) happens before the pump — the delay(100ms) dice / delay(500ms)
+    // AI chains resume while a frame callback is pending.
+    // ────────────────────────────────────────────────────────────────────
+    void vsync_keepalive_tick(uint64_t total_insns);
+    void set_vsync_keepalive_hook(std::function<int(int)> hook) {
+        vsync_keepalive_hook_ = std::move(hook);
+    }
+    std::function<int(int)> vsync_keepalive_hook_;  // = pump_compose_frames
+    bool vsync_tick_active_ = false;       // reentrancy guard (the pump interprets)
+    uint64_t vsync_insn_acc_ = 0;          // instructions since the last fire
+    int vsync_keepalive_enabled_ = -1;     // tri-state env verdict cache
+    uint64_t vsync_tick_interval_ = 0;     // env-tunable cadence cache (256K default)
+
     
     // Configuration
     struct Config {
```

**part2/4 — miniandroid/src/dex/dalvik_engine.cpp (171 lines)** — sha16 `b14853c9059728bf`

```diff
diff --git a/miniandroid/src/dex/dalvik_engine.cpp b/miniandroid/src/dex/dalvik_engine.cpp
index 47ca3562..eaf66467 100755
--- a/miniandroid/src/dex/dalvik_engine.cpp
+++ b/miniandroid/src/dex/dalvik_engine.cpp
@@ -17475,6 +17475,12 @@ int DalvikExecutionEngine::dispatch_custom_view_draw(uint32_t view_object_id) {
         ops = ok ? (int)canvas_shadow->ops().size() : 0;
     }
     draw_window_active_ = false;
+    // CONT-130b: a soft-stopped draw window leaves NO artifact state —
+    // the unwind already exited by return; clear the soft channel here so
+    // the next window starts clean (frame honesty stays armed for the
+    // presentation point — draw_window_budget_halted_ is NOT cleared here;
+    // frame_honesty_begin() owns that at the next render pass).
+    awaitup_soft_stop_clear();
     std::cerr << "[C013-ONDRAW] view=" << view_object_id << " class=" << cls
               << " dispatched=" << (ok ? "YES" : "NO") << " ops=" << ops << std::endl;
     // ── S152 TRAIN-70e v1 (T70-ATTACH) RETIRED: the D7-PLACECHECK
@@ -21009,8 +21015,52 @@ inline float bits_i2f(int32_t i) {
 // channel the S60 wall uses so the unwind semantics are the already-proven
 // F084 family path.
 void DalvikExecutionEngine::awaitup_gate_check() {
-    if (!awaitup_deadline_active_ || awaitup_deadline_hit_) return;
+    if (!awaitup_deadline_active_) return;
+    // CONT-130b: soft channel armed — only the hard backstop can escalate.
+    // The 15 s grace covers a method body that never returns; every method
+    // that DOES hit a boundary exits by return via the fetch-loop break.
+    if (awaitup_soft_stop_active_) {
+        if (std::chrono::steady_clock::now() >= awaitup_hard_deadline_) {
+            halted_ = true;
+            halted_on_return_ = false;
+            halt_reason_ =
+                "AWAIT-UP-GATE: soft-stop grace exhausted — hard F084 "
+                "backstop (15 s) fired; a method body never returned";
+            log("HALT(scoped-backstop): " + halt_reason_);
+            std::cerr << "[AWAIT-UP-GATE] soft-stop grace exhausted in "
+                      << current_class_ << "." << current_method_
+                      << " — hard F084 backstop fires" << std::endl;
+        }
+        return;
+    }
+    if (awaitup_deadline_hit_) return;
     if (std::chrono::steady_clock::now() < awaitup_deadline_) return;
+    // CONT-130b SOFT DRAW-WINDOW STOP: inside a draw window the gate
+    // unwinds GRACEFULLY at method boundaries — NO exception is
+    // synthesized (the F084 unwind left the compose draw state
+    // half-mutated: MultiParagraphLayoutCache density=0.0 poisoned 4,685
+    // later draws — the S215 decode). The draw state survives; frame
+    // honesty STILL arms (an unfinished frame is never presented —
+    // F-NEW-298 unchanged in both channels).
+    if (draw_window_active_) {
+        awaitup_soft_stop_ = true;
+        awaitup_soft_stop_active_ = true;
+        awaitup_deadline_hit_ = true;      // the gate fired (per-tap marker)
+        draw_window_budget_halted_ = true; // frame honesty — both channels
+        awaitup_hard_deadline_ = std::chrono::steady_clock::now() +
+                                 std::chrono::seconds(15);
+        log("AWAIT-UP-GATE(SOFT): draw-window budget reached — graceful "
+            "method-boundary unwind, draw state preserved");
+        std::cerr << "[AWAIT-UP-GATE-SOFT] draw-window budget reached in "
+                  << current_class_ << "." << current_method_
+                  << " — graceful unwind (no synthesized exception; draw "
+                     "state survives; hard F084 backstop in 15s)"
+                  << std::endl;
+        return;
+    }
+    // Outside any draw window: the S154 hard channel is preserved (the
+    // runaway is not a draw walk — the UP-priority unwind semantics are
+    // the already-proven F084 family path).
     awaitup_deadline_hit_ = true;
     if (draw_window_active_) draw_window_budget_halted_ = true;
     halted_ = true;
@@ -21044,10 +21094,73 @@ void DalvikExecutionEngine::awaitup_gate_abort_reset() {
     frame_unwind_exception_ = DalvikValue::make_null();
     exc_redirect_pending_ = false;
     exc_redirect_addr_ = 0;
+    // CONT-130b: the soft channel's flags clear here too (the tap path
+    // owns the per-tap state cycle begin → window → end → abort_reset).
+    awaitup_soft_stop_ = false;
+    awaitup_soft_stop_active_ = false;
     std::cerr << "[AWAIT-UP-GATE] artifact state reset — UP dispatch clean"
               << std::endl;
 }
 
+// ── CONT-130 F-NEW-277 slice-2: VSYNC-CONTINUITY KEEP-ALIVE (row #21) ───
+// Called from the interpreter instruction epilogue. AOSP law: vsync
+// belongs to the DISPLAY — a long DEX body (class-init chains, bitmap
+// decode, big compute) must NOT starve the frame pipeline; on a device
+// the display delivers vsync every 16.6 ms regardless of what the main
+// thread runs. Every 256K instructions the tick fires the ONE canonical
+// compose pump through the hook wired on the real-dalvik app path.
+// BYTE-INERT while the hook is unset (one null check per instruction).
+void DalvikExecutionEngine::vsync_keepalive_tick(uint64_t /*total_insns*/) {
+    if (!vsync_keepalive_hook_) return;  // zero-cost when unwired (CONT-42)
+    if (vsync_keepalive_enabled_ < 0) {
+        const char* off = std::getenv("MINIANDROID_VSYNC_KEEPALIVE");
+        vsync_keepalive_enabled_ =
+            (off && off[0] == '0' && off[1] == '\0') ? 0 : 1;
+        vsync_tick_interval_ = 262144;  // 256K-insn cadence
+        if (const char* e = std::getenv("MINIANDROID_VSYNC_TICK_INTERVAL")) {
+            unsigned long long v = strtoull(e, nullptr, 10);
+            if (v >= 4096) vsync_tick_interval_ = (uint64_t)v;  // floor 4096
+        }
+    }
+    if (vsync_keepalive_enabled_ == 0) return;
+    if (++vsync_insn_acc_ < vsync_tick_interval_) return;
+    vsync_insn_acc_ = 0;
+    if (vsync_tick_active_) return;  // reentrancy guard (the pump interprets)
+    // Scope guard: the keep-alive only matters while the compose family
+    // actually owns (part of) the screen — pending frame callbacks — or
+    // while the handler queue holds work the pipeline must drain.
+    auto* registry = get_shadow_registry();
+    auto* cs = registry ? registry->find_as<framework::ChoreographerShadow>()
+                        : nullptr;
+    auto* hs = registry ? registry->find_as<framework::HandlerShadow>() : nullptr;
+    const bool cb_pending = cs && cs->has_pending_callbacks();
+    const bool queue_work = hs && hs->queue_size() > 0;
+    if (!cb_pending && !queue_work) return;
+    vsync_tick_active_ = true;
+    // INTERACTIVE-SESSION CLOCK (row #22 law): when a frame callback is
+    // pending AND the handler queue head is future-due, ONE bounded
+    // deterministic advance(next_ready - now) before the pump — the
+    // delay(100ms) dice / delay(500ms) AI chains resume while a frame
+    // callback is pending (the compose family owns the screen).
+    if (cb_pending && queue_work) {
+        int64_t next_ready = hs->next_ready_ms();
+        int64_t now_ms = hs->virtual_now_ms();
+        if (next_ready > now_ms) {
+            hs->advance_virtual(next_ready - now_ms);
+            std::cerr << "[F-NEW-277-CLOCK] interactive session advance to "
+                      << "virtual_ms=" << next_ready
+                      << " (delta=" << (next_ready - now_ms)
+                      << "ms; frame callback pending)" << std::endl;
+        }
+    }
+    int fired = vsync_keepalive_hook_(8);  // the ONE canonical pump
+    if (fired > 0)
+        std::cerr << "[VSYNC-KEEPALIVE] tick fired " << fired
+                  << " compose frame(s) from the interpreter epilogue"
+                  << std::endl;
+    vsync_tick_active_ = false;
+}
+
 bool DalvikExecutionEngine::fetch_decode_execute(DalvikExecutionResult& result) {
     uint64_t f107_t0 = 0; phase_clock().enter(phase_clock().fetch_exec, f107_t0);
     struct F107Guard { PhaseClock::Phase& ph; uint64_t t0; ~F107Guard(){{ phase_clock().exit(ph, t0);}} } f107_guard{phase_clock().fetch_exec, f107_t0};
@@ -25363,6 +25476,12 @@ bool DalvikExecutionEngine::fetch_decode_execute(DalvikExecutionResult& result)
         result.total_instructions_executed++;
         result.total_opcodes_decoded++;
 
+        // CONT-130 F-NEW-277 slice-2: VSYNC-CONTINUITY keep-alive — vsync
+        // belongs to the display; a long DEX body must not starve the frame
+        // pipeline. BYTE-INERT when no hook is wired (zero-cost: one null
+        // check per instruction — the CONT-42 law).
+        vsync_keepalive_tick(result.total_instructions_executed);
+
         // EXP-045 Phase 2: Global instruction counter — log every 100K instructions
         // to track execution speed and progress.
         static thread_local uint64_t global_insn_counter = 0;
@@ -26345,6 +26464,12 @@ bool DalvikExecutionEngine::fetch_decode_execute(DalvikExecutionResult& result)
             awaitup_gate_check();
             if (awaitup_deadline_hit_) break;  // same graceful channel as the wall
         }
+        // CONT-130b: SOFT draw-window stop — enclosing frames unwind at the
+        // method boundary by RETURN (no synthesized exception, the draw
+        // state survives). Unconditional per-iteration check: the flag arms
+        // once and every frame exits normally, like a method that simply
+        // returns. Cleared at the draw-window boundary / abort_reset / begin.
+        if (awaitup_soft_stop_) break;
 
         // Check for return
         if (halted_on_return_) {
```

**part3/4 — miniandroid/src/runtime/execution_engine.h (30 lines)** — sha16 `f44512952585dded`

```diff
diff --git a/miniandroid/src/runtime/execution_engine.h b/miniandroid/src/runtime/execution_engine.h
index 19fa2209..dffad118 100755
--- a/miniandroid/src/runtime/execution_engine.h
+++ b/miniandroid/src/runtime/execution_engine.h
@@ -363,6 +363,12 @@ private:
     // F-NEW-307 (CONT-44): the app-op ledger of the last PRESENTED frame
     // (0 before any presentation) — the kept-frame census attribution source.
     uint64_t last_presented_app_draw_ops_ = 0;
+    // CONT-130 F-NEW-298-KEEP: uniform-face signature of the last PRESENTED
+    // frame. `true` before any presentation (the keep law cannot arm until
+    // a REAL face — non-uniform — has been presented). A 100%-uniform walk
+    // face (distinct=1: the #FAFAFA/#FAF9FD bare-window collapse) never
+    // replaces a presented non-uniform face (keep-last-complete law).
+    bool last_presented_face_uniform_ = true;
 
 public:
     // ═══════════════════════════════════════════════════════════════════
@@ -394,6 +400,12 @@ public:
         bool draw_budget_halt = false;        // the F084 halt fired inside THIS draw walk
         bool kept_prior_frame = false;        // presentation skipped; PNG holds the prior frame
         uint64_t kept_prior_app_draw_ops = 0; // the kept frame's app-op ledger count
+        // ── CONT-130 F-NEW-298-KEEP: keep-last-complete ──
+        // A walked-empty UNIFORM re-render (distinct=1: the bare-window
+        // collapse face) never replaces the presented surface. Honest
+        // per-frame record: this frame's walk produced the uniform face
+        // and the presentation was skipped (keep-last-complete law).
+        bool keep_last_complete = false;
         int  nodes_visited = 0;              // P0-7 census
         int  nodes_skipped_depth = 0;        // P0-7 census
         int  depth_max = 0;                  // P0-7 census
```

**part4/4 — miniandroid/src/runtime/execution_engine.cpp (105 lines)** — sha16 `a7d6b3c77ac9e6bd`

```diff
diff --git a/miniandroid/src/runtime/execution_engine.cpp b/miniandroid/src/runtime/execution_engine.cpp
index dd85bb8f..e803a176 100755
--- a/miniandroid/src/runtime/execution_engine.cpp
+++ b/miniandroid/src/runtime/execution_engine.cpp
@@ -667,6 +667,15 @@ bool ExecutionEngine::stage_execute_application_real_dalvik(ExecutionResult& res
             }
         }
         dalvik_engine_.set_per_dex_raw_data(std::move(per_dex_raw));
+        // CONT-130 F-NEW-277 slice-2: wire the VSYNC-CONTINUITY keep-alive
+        // hook — ONLY on the real-dalvik app path (GATE goldens and legacy
+        // runs keep the pre-law cadence byte-exact; the tick is guarded by
+        // the MINIANDROID_VSYNC_KEEPALIVE=0 opt-out and the pending/queue
+        // scope guard). The fire stays the ONE canonical pump
+        // (pump_compose_frames — G06 token routing + F-NEW-289 main-looper
+        // identity in one place, the CONT-129 re-land scope law).
+        dalvik_engine_.set_vsync_keepalive_hook(
+            [this](int max_frames) { return pump_compose_frames(max_frames); });
         dalvik_engine_.set_apk_path(result.apk_info.apk_path);
         // EXP-093/F011: Set manifest-derived package identity
         dalvik_engine_.set_package_info(
@@ -6077,6 +6086,68 @@ bool ExecutionEngine::stage_render_frame_impl(ExecutionResult& result, const Exe
                         // Copy FrameBuffer pixels (RGBA) back to framebuffer_ (uint8_t RGBA)
                         const auto& pixels = fb.get_pixels();
                         fb_pixels_total = pixels.size();
+                        // ── CONT-130 F-NEW-298-KEEP: KEEP-LAST-COMPLETE ────
+                        // A walked-empty UNIFORM re-render (distinct=1: the
+                        // 100% #FAFAFA framework / #FAF9FD app-theme bare
+                        // window background) NEVER replaces the presented
+                        // surface — AOSP/SurfaceFlinger: the compositor never
+                        // swaps a real frame for an empty one (the CONT-130
+                        // PRE decode: dooz tap chain collapsed to
+                        // d602648e/distinct=1 100% #FAFAFA, chrome GONE).
+                        // Arms ONLY when the compose family is live (frame
+                        // clock past base) AND the previous presented face
+                        // was NON-uniform; non-uniform transient walks
+                        // present as-is (frame honesty unchanged). Applied
+                        // at the per-frame boundary AND the F-NEW-497 drain
+                        // render — both present through this same point.
+                        size_t keep_distinct = 0;
+                        {
+                            std::map<uint32_t, size_t> keep_hist;
+                            for (const auto& px : pixels) {
+                                keep_hist[(uint32_t(px.r) << 16) |
+                                          (uint32_t(px.g) << 8) |
+                                          uint32_t(px.b)]++;
+                                if (keep_hist.size() > 1) {
+                                    keep_distinct = 2;  // non-uniform (early exit)
+                                    break;
+                                }
+                            }
+                            if (keep_distinct == 0)
+                                keep_distinct = keep_hist.size();  // 0 (empty) or 1
+                        }
+                        const bool face_uniform_298 = keep_distinct == 1;
+                        bool keep_298 = false;
+                        {
+                            auto* cs298 =
+                                shadow_registry_
+                                    ? shadow_registry_->find_as<
+                                          framework::ChoreographerShadow>()
+                                    : nullptr;
+                            const bool compose_live_298 =
+                                cs298 && cs298->last_frame_time_nanos() >
+                                             framework::ChoreographerShadow::
+                                                 kFrameBaseNanos;
+                            if (compose_live_298 &&
+                                !last_presented_face_uniform_ && face_uniform_298)
+                                keep_298 = true;
+                        }
+                        if (keep_298) {
+                            std::cerr << "[F-NEW-298-KEEP] walked-empty uniform "
+                                      << "face (distinct=1) — presentation "
+                                      << "SKIPPED, keeping the last complete "
+                                      << "frame (CONT-130 keep-last-complete)"
+                                      << std::endl;
+                            dalvik_engine_.sf_order_log(
+                                "PRESENT",
+                                "keep_last_complete=1 (uniform walk face)");
+                            fb_non_white = -1;   // honest signal: not presented
+                            fb_pixels_total = framebuffer_.size() / 4;
+                            frame_census_.keep_last_complete = true;
+                            frame_census_.kept_prior_frame = true;
+                            frame_census_.kept_prior_app_draw_ops =
+                                last_presented_app_draw_ops_;
+                        } else {
+                        last_presented_face_uniform_ = face_uniform_298;
                         // EXP-092: Debug — check if any non-white pixels exist in fb
                         int non_white = 0;
                         for (size_t i = 0; i < pixels.size(); i++) {
@@ -6121,6 +6192,7 @@ bool ExecutionEngine::stage_render_frame_impl(ExecutionResult& result, const Exe
                         }
                         std::cerr << "[EXP092-COPY] framebuffer_ has " << fb_non_white << " non-white pixels" << std::endl;
                         }
+                        }
                         // S135 §3: DRAW/MEASURE/LAYOUT confirmation — the
                         // composed frame IS the evidence the pipeline
                         // reached the end of the draw walk.
@@ -6680,6 +6752,7 @@ bool ExecutionEngine::stage_capture_output( ExecutionResult& result, const Execu
                     {"render_exception", frame_census_.render_exception},
                     {"budget_exhausted", frame_census_.budget_exhausted},
                     {"draw_budget_halt", frame_census_.draw_budget_halt},
+                    {"keep_last_complete", frame_census_.keep_last_complete},
                     {"presentation", frame_census_.kept_prior_frame
                                           ? "kept_prior_frame"
                                           : "this_frame"},
```


## Scope law honored (CONT-129 re-land scope, unchanged)

No new dispatch code: the keep-alive fire goes through the ONE canonical pump (`pump_compose_frames`; G06 token routing + F-NEW-289 main-looper identity stay in one place). All laws structural, scope-guarded, env-opt-out (`MINIANDROID_VSYNC_KEEPALIVE=0`), zero-cost when the hook is unset (one null check per instruction — the CONT-42 law). Epilogue placement: after `total_instructions_executed++`/`total_opcodes_decoded++`, ahead of the PROGRESS block.

## PRE/POST on THIS line (both binaries built from this exact tree)

Binary provenance: POST `4d9087c60482042b` (full -O2, -j1; first-build sha `c30939c73a755235` — the build is not byte-reproducible, provenance-only, pins are the contract), PRE `f43745f074eb8812` (same tree, four-law diff stashed). Battery: `scripts/cont131_battery.py` + `scripts/cont131_pre_battery.py`; evidence `evidence/cont131/`.

### dooz no-tap settle anchor (golden `a0fae9072313e2d1`)

| Row | PRE `f43745f0` | POST (laws armed) | Verdict |
|-----|----------------|--------------------|---------|
| no-tap golden ×3 | ×1 HOLD choreo=**4** (the starvation baseline) | **×3 HOLD byte-exact**, choreo=**14** each, ticks=6 each, walls 171.2/175.3/172.7 s, rerun-identical | **#21 CLOSED on the S215d line** — the vsync drip is LIVE and byte-inert for the golden |
| opt-out `MINIANDROID_VSYNC_KEEPALIVE=0` | — | HOLD choreo=**4**, ticks=**0** | env law byte-inert |
| ttt ×3 rerun-identity | — | identical faces ×3, uncaught=0 | neutrality spot PASS |

### dooz tap run (#573 recipe `765,1830@6 + 540,960@10`, 16 frames)

| Row | PRE (hard channel) | POST (soft stop) | Verdict |
|-----|--------------------|------------------|---------|
| gate channel | `[AWAIT-UP-GATE]` hard rows=**2**; F084 deferred `VirtualMachineError` unwind rows=**7** (`F084-HALT-RETURN … AWAIT-UP-GATE`) | `[AWAIT-UP-GATE-SOFT]` =**1** (`draw-window budget reached in Ly9;.i — graceful unwind`), artifact reset =1, **0 hard, 0 backstops, 0 F084 rows** | **row #24 law LIVE on the S215d line** |
| MultiParagraphLayoutCache poison | **48,944 ISEs** (`could not provide TextLayoutResult during the draw phase`, caller `Lv;.n` depth=233) | **0** — the draw state survives every gate stop | the poison is EXTINCT |
| collapse face | `d602648e` **PRESENTED** (frame_008: distinct=**1**, 100% `(250,250,250)` `#FAFAFA`) | **EXTINCT** — chain `a0fae907`×6 → `29e39938` → `85b05db9`×2 → `47d241ae`×7; frame_007 = distinct **111** (real pressed chrome) | **#23 CLOSED on the S215d line** |
| `[F-NEW-298-KEEP]` | 0 | **9** (uniform walks skipped, last complete frame kept) | keep-last-complete LIVE |
| `[VSYNC-KEEPALIVE]` ticks | 0 | **7** | continuity LIVE |
| `[F-NEW-277-CLOCK]` arms | 0 | **0** — honest: the UP → gesture-detection → onClick coroutine completion still does not reach the viewModel (row #24 core / #25 root); the clock had nothing to advance | **#22 stays honestly PARTIAL**, exactly the registered CONT-130b record |

Final POST tap face `47d241ae` = distinct 2 (`#FAF9FD` bare-window bg + 7 dark px) — non-uniform, so the keep law legally presents it; **the 9-cell board still never materializes (dice corpus 0)**: rows #24 core / #25 remain the frontier, unchanged from the accepted decode.

## Row ledger updates for #573

- **#21 (vsync continuity)**: CLOSED on the S215d line (this re-land carries PRE/POST on THIS line's records).
- **#23 (keep-last-complete)**: CLOSED on the S215d line (collapse face extinct on both arms where the law is armed).
- **#24 (soft draw-window stop)**: law re-landed and LIVE on the S215d line (48,944 → 0 poison ISEs is THIS line's PRE number — bigger than the registered 4,685 on the S213 lane line).
- **#22 (interactive clock)**: PARTIAL — armed 0× on both arms; gated by the row #24 core / #25 root (unchanged root).
- **#25 (slot-lambda / UP-dispatch resumption)**: OPEN — the next root attack remains the UP-dispatch coroutine resumption chain (how the interpreter parks/resumes the compose pointer coroutine across two separate `dispatchTouchEvent` invocations) → dice chain schedules (#22 closes end-to-end) → slot-lambda re-execution (#27 lever) → the 9-cell board.

## Request (the standard receipt flow)

apply-check → build (`make -j1`; `-j2` OOMs on this host) → the cont131 battery → FULL 6-pin gate → land. If main has moved past `01586a17`, expect context shifts around the instruction epilogue (A-R4/W12 territory) — the parts are sha16-tagged for the re-base audit.

When the lane lands this, the convergence note stands: re-run the A-R4 R5 isEnabled A/B in the same container — the accessibility-delegate family and the gesture-chain family share the Compose draw-state root.

— CONT-131 wave, the platform lane. Local commit `62468458` (laws + scripts + evidence) is ready to push the moment a `contents:write` grant exists.
