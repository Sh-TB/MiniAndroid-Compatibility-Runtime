package com.probe.f217

import android.app.Activity
import android.os.Bundle
import android.util.Log
import android.widget.TextView
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeoutOrNull
import kotlinx.coroutines.yield
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withLock

/**
 * F-NEW-217 T-01 probe — REAL kotlinx-coroutines 1.9.0 bytecode (exact
 * dooz23 pin), deterministic waiter-resume faces on one runBlocking event
 * loop. No threads, no timing races: B parks DETERMINISTICALLY because the
 * main coroutine holds the mutex while B attempts lock().
 *
 * FACE B (sanity): uncontended withLock x2 — acquire/release bookkeeping
 *   must return the mutex to the unlocked state. n must be 2.
 * FACE A (the recorded spin face): main holds → B's lock() suspends →
 *   B's CancellableContinuation is queued in SegmentedQueue (head != null,
 *   permits == 0 — the EXACT SPIN-REGS state recorded in F-NEW-217) →
 *   main unlock() = release() must tryResumeAcquire + completeResume +
 *   dispatch B. If the resume is lost, jobB.join() hangs; withTimeoutOrNull
 *   bounds it (if the timeout machinery itself fires) so the face records
 *   FAIL honestly instead of hanging the frame. If the resume double-fires,
 *   the second release() raises the recorded sibling ISE
 *   "The number of released permits cannot be greater than 1".
 * FACE C (Semaphore face): identical shape on Semaphore(1) — the
 *   SemaphoreAndMutexImpl path named in the F-NEW-217 evidence.
 */
class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val log = StringBuilder()

        // ---------- FACE B: uncontended acquire/release bookkeeping ----------
        try {
            val m = Mutex()
            var n = 0
            runBlocking {
                m.withLock { n += 1 }
                m.withLock { n += 1 }
            }
            val line = "F217-B-UNCONTENDED|" + (if (n == 2) "PASS" else "FAIL") + "|n=" + n + "|isLocked=" + m.isLocked
            log.append(line).append('\n'); Log.i("F217", line)
        } catch (t: Throwable) {
            val line = "F217-B-UNCONTENDED|THROW|" + t.javaClass.getName() + ":" + t.message
            log.append(line).append('\n'); Log.i("F217", line)
        }

        // ---------- FACE A: Mutex waiter-resume (the spin face) ----------
        try {
            val m = Mutex()
            val seq = StringBuilder()
            runBlocking {
                m.lock()
                val jobB = launch {
                    seq.append("B-try;")
                    m.lock()                  // main holds -> B suspends, waiter queued
                    seq.append("B-acquired;")
                    m.unlock()
                }
                yield()                        // B runs, parks deterministically
                seq.append("main-unlock;")
                m.unlock()                     // must resume B
                withTimeoutOrNull(5000L) { jobB.join() }
            }
            val s = seq.toString()
            val ok = s == "B-try;main-unlock;B-acquired;"
            val line = "F217-A-WAITER-RESUME|" + (if (ok) "PASS" else "FAIL") + "|seq=" + s + "|isLocked=" + m.isLocked
            log.append(line).append('\n'); Log.i("F217", line)
        } catch (t: Throwable) {
            val line = "F217-A-WAITER-RESUME|THROW|" + t.javaClass.getName() + ":" + t.message
            log.append(line).append('\n'); Log.i("F217", line)
        }

        // ---------- FACE C: Semaphore waiter-resume ----------
        try {
            val s = Semaphore(1)
            val seq2 = StringBuilder()
            runBlocking {
                s.acquire()
                val jobC = launch {
                    seq2.append("C-try;")
                    s.acquire()               // suspends -> waiter queued
                    seq2.append("C-acquired;")
                    s.release()
                }
                yield()
                seq2.append("main-release;")
                s.release()                   // must resume C
                withTimeoutOrNull(5000L) { jobC.join() }
            }
            val s2 = seq2.toString()
            val ok2 = s2 == "C-try;main-release;C-acquired;"
            val line = "F217-C-SEMAPHORE|" + (if (ok2) "PASS" else "FAIL") + "|seq=" + s2
            log.append(line).append('\n'); Log.i("F217", line)
        } catch (t: Throwable) {
            val line = "F217-C-SEMAPHORE|THROW|" + t.javaClass.getName() + ":" + t.message
            log.append(line).append('\n'); Log.i("F217", line)
        }

        val tv = TextView(this)
        tv.setText(log.toString())
        setContentView(tv)
    }
}
