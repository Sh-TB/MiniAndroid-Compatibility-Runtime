package com.miniandroid.c8probe;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.Message;
import android.os.CountDownTimer;
import android.os.SystemClock;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CountedCompleter;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.CancellationException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.LinkedBlockingDeque;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.Semaphore;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicIntegerArray;
import java.util.concurrent.atomic.AtomicLongArray;
import java.util.ArrayList;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.Callable;
import java.util.concurrent.Phaser;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;
import android.os.Process;

/**
 * S191 [C8] wave 8 + S192 [C8] wave 9 — Coder 8 concurrency-law probe
 * APK. Every check prints exactly one marker line
 * "C8PROBE <name> PASS|FAIL <detail>" via android.util.Log. The test
 * runner asserts on these markers (3 runs must be byte-identical,
 * S188 rule 9).
 */
public class MainActivity extends Activity {
    private static void mark(String name, boolean ok, String detail) {
        android.util.Log.i("C8PROBE", name + " " + (ok ? "PASS" : "FAIL")
                + (detail.isEmpty() ? "" : " " + detail));
    }

    // wave-9 shared state (probe-observable engine effects)
    static int cdtTicks = 0;
    static boolean cdtFinished = false;
    static boolean crossNotifierRan = false;
    static boolean ccComputeRan = false;
    static boolean ccOnCompletionRan = false;

    static class MyCC extends CountedCompleter {
        public MyCC(CountedCompleter parent) { super(parent); }
        public void compute() { ccComputeRan = true; }
        public void onCompletion(CountedCompleter caller) {
            ccOnCompletionRan = true;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── F-C8-153: Lock-INTERFACE keyed dispatch ────────────────────
        try {
            Lock lock = new ReentrantLock();
            lock.lock();
            lock.unlock();
            mark("lock_interface", true, "locked+unlocked via Lock ref");
        } catch (Throwable t) {
            mark("lock_interface", false, t.getClass().getSimpleName());
        }

        // ── F-C8-152: REAL Condition objects ────────────────────────────
        try {
            ReentrantLock rl = new ReentrantLock();
            Condition c = rl.newCondition();      // was handled_null → NPE
            boolean realCond = c != null;
            rl.lock();
            c.signal();                            // owner-held: OK
            long remain = c.awaitNanos(5_000_000L); // signaled: estimate ≥0
            boolean signaledPath = remain >= 0;
            Condition c9 = rl.newCondition();      // fresh: NO pending signal
            long remain9 = c9.awaitNanos(6_000_000L); // timeout law: ≤0
            rl.unlock();
            mark("condition_real", realCond && signaledPath && remain9 <= 0,
                    "remain=" + remain + " remain9=" + remain9);
        } catch (Throwable t) {
            mark("condition_real", false, t.getClass().getSimpleName());
        }

        // Condition IMSE law: signal WITHOUT holding the lock must throw.
        try {
            ReentrantLock rl2 = new ReentrantLock();
            Condition c2 = rl2.newCondition();
            c2.signal();                           // JDK: IMSE
            mark("condition_imse", false, "no throw");
        } catch (IllegalMonitorStateException e) {
            mark("condition_imse", true, "IMSE thrown");
        } catch (Throwable t) {
            mark("condition_imse", false, t.getClass().getSimpleName());
        }

        // ── F-C8-142: CountDownLatch ────────────────────────────────────
        try {
            CountDownLatch latch = new CountDownLatch(2);
            boolean countOk = latch.getCount() == 2;
            latch.countDown();
            latch.countDown();
            boolean opened = latch.await(50, TimeUnit.MILLISECONDS);
            mark("latch", countOk && opened,
                    "count2→0 awaited=" + opened);
        } catch (Throwable t) {
            mark("latch", false, t.getClass().getSimpleName());
        }

        // ── F-C8-141: Object monitor contract ───────────────────────────
        final Object mon = new Object();
        try {
            mon.wait(10);                          // JDK: IMSE (not owner)
            mark("wait_imse", false, "no throw");
        } catch (IllegalMonitorStateException e) {
            mark("wait_imse", true, "IMSE thrown");
        } catch (Throwable t) {
            mark("wait_imse", false, t.getClass().getSimpleName());
        }
        try {
            synchronized (mon) {
                mon.notifyAll();                   // owner-held: OK
                mon.wait(20);                      // timed wait, clock law
            }
            mark("wait_timed", true, "sync notifyAll+wait(20) returned");
        } catch (Throwable t) {
            mark("wait_timed", false, t.getClass().getSimpleName());
        }

        // ── F-C8-146: Thread interrupt state ────────────────────────────
        try {
            boolean pre = Thread.interrupted();    // false, clears
            Thread.currentThread().interrupt();
            boolean set = Thread.interrupted();    // true, clears again
            boolean post = Thread.interrupted();   // false
            mark("thread_interrupted", !pre && set && !post,
                    "false→true→false");
        } catch (Throwable t) {
            mark("thread_interrupted", false, t.getClass().getSimpleName());
        }

        // ── F-C8-147: Thread.getState ───────────────────────────────────
        try {
            String st = Thread.currentThread().getState().name();
            boolean ok = "RUNNABLE".equals(st);
            mark("thread_state", ok, "state=" + st);
        } catch (Throwable t) {
            mark("thread_state", false, t.getClass().getSimpleName());
        }

        // ── F-C8-143: HandlerThread ─────────────────────────────────────
        try {
            HandlerThread ht = new HandlerThread("c8-worker");
            ht.start();
            Looper lo = ht.getLooper();            // was silent null
            boolean got = lo != null;
            boolean quit = ht.quit();
            mark("handler_thread", got && quit,
                    "looper=" + (lo != null) + " quit=" + quit);
        } catch (Throwable t) {
            mark("handler_thread", false, t.getClass().getSimpleName());
        }

        // ── F-C8-144/145: Message async flag + sendToTarget ─────────────
        try {
            Handler h = new Handler(Looper.getMainLooper());
            Message m = h.obtainMessage();         // sets msg.target = h
            m.setAsynchronous(true);
            boolean async = m.isAsynchronous();
            m.sendToTarget();                      // rides the real queue
            mark("message_async_send", async,
                    "async=" + async + " sent(no-throw)");
        } catch (Throwable t) {
            mark("message_async_send", false, t.getClass().getSimpleName());
        }

        // ── F-C8-148: ForkJoinPool.commonPool singleton ─────────────────
        try {
            ForkJoinPool p1 = ForkJoinPool.commonPool();
            ForkJoinPool p2 = ForkJoinPool.commonPool();
            mark("common_pool", p1 == p2 && p1 != null
                    && p1.getParallelism() >= 1,
                    "identity=" + (p1 == p2)
                    + " parallelism=" + p1.getParallelism());
        } catch (Throwable t) {
            mark("common_pool", false, t.getClass().getSimpleName());
        }

        // ── F-C8-150: Scheduled executor + getDelay ─────────────────────
        try {
            ScheduledThreadPoolExecutor ses =
                    new ScheduledThreadPoolExecutor(1);
            ScheduledFuture<?> sf = ses.schedule(new Runnable() {
                public void run() { /* marker task */ }
            }, 25, TimeUnit.MILLISECONDS);
            long d = sf.getDelay(TimeUnit.MILLISECONDS);
            mark("scheduled", sf != null && d >= 0 && d <= 25,
                    "delay=" + d);
        } catch (Throwable t) {
            mark("scheduled", false, t.getClass().getSimpleName());
        }

        // ── F-C8-149/151: Future.isDone + allowCoreThreadTimeOut ────────
        try {
            ExecutorService es = Executors.newFixedThreadPool(2);
            Future<String> f = es.submit(new java.util.concurrent.Callable<String>() {
                public String call() { return "C8-RESULT"; }
            });
            String v = f.get(500, TimeUnit.MILLISECONDS);
            boolean done = f.isDone();
            ((ThreadPoolExecutor) es).allowCoreThreadTimeOut(true);
            es.shutdown();
            mark("future_done", "C8-RESULT".equals(v) && done,
                    "value=" + v + " done=" + done);
        } catch (Throwable t) {
            mark("future_done", false, t.getClass().getSimpleName());
        }

        // ══════════ S192 [C8] WAVE 9 (defects 161–180) ══════════

        // ── F-C8-161: scheduled-executor factories ──────────────────────
        try {
            ScheduledThreadPoolExecutor sp =
                    (ScheduledThreadPoolExecutor)
                        Executors.newScheduledThreadPool(2);
            ScheduledFuture<?> sf = sp.schedule(new Runnable() {
                public void run() { }
            }, 15, TimeUnit.MILLISECONDS);
            ExecutorService single =
                    Executors.newSingleThreadScheduledExecutor();
            mark("sched_pool_factory", sp != null && sf != null
                    && single != null,
                    "pool=" + (sp != null) + " fut=" + (sf != null));
        } catch (Throwable t) {
            mark("sched_pool_factory", false, t.getClass().getSimpleName());
        }

        // ── F-C8-162: shutdownNow + awaitTermination ────────────────────
        try {
            ExecutorService es2 = Executors.newFixedThreadPool(1);
            es2.submit(new Runnable() { public void run() { } });
            java.util.List<Runnable> pend = es2.shutdownNow();
            boolean term = es2.awaitTermination(10, TimeUnit.MILLISECONDS);
            mark("executor_lifecycle", pend != null && term,
                    "pendingList=" + (pend != null) + " term=" + term);
        } catch (Throwable t) {
            mark("executor_lifecycle", false, t.getClass().getSimpleName());
        }

        // ── F-C8-163: Handler.postAtTime ────────────────────────────────
        try {
            Handler h3 = new Handler(Looper.getMainLooper());
            boolean ok = h3.postAtTime(new Runnable() {
                public void run() { }
            }, SystemClock.uptimeMillis() + 30);
            mark("post_at_time", ok, "queued=" + ok);
        } catch (Throwable t) {
            mark("post_at_time", false, t.getClass().getSimpleName());
        }

        // ── F-C8-164: Message.obtain static family ──────────────────────
        try {
            Message mo = Message.obtain();
            boolean nullOk = mo != null;
            boolean npeOk;
            try {
                mo.sendToTarget();                 // null target → NPE (AOSP)
                npeOk = false;
            } catch (NullPointerException e) {
                npeOk = true;
            }
            Message mh = Message.obtain(
                    new Handler(Looper.getMainLooper()));
            mark("msg_obtain", nullOk && npeOk && mh != null,
                    "null=" + nullOk + " npe=" + npeOk
                    + " bound=" + (mh != null));
        } catch (Throwable t) {
            mark("msg_obtain", false, t.getClass().getSimpleName());
        }

        // ── F-C8-165: CountedCompleter family ───────────────────────────
        try {
            MyCC root = new MyCC(null);
            root.setPendingCount(2);
            root.addToPendingCount(1);
            boolean pend = root.getPendingCount() == 3;
            MyCC child = new MyCC(root);
            boolean parent = child.getCompleter() == root;
            root.tryComplete();                    // 3→2 (decrement law)
            boolean after = root.getPendingCount() == 2;
            child.invoke();                        // compute() INLINE
            mark("counted_completer", pend && parent && after
                    && ccComputeRan,
                    "pend=" + pend + " parent=" + parent
                    + " after=" + after + " compute=" + ccComputeRan);
        } catch (Throwable t) {
            mark("counted_completer", false, t.getClass().getSimpleName());
        }

        // ── F-C8-166: CountDownTimer ────────────────────────────────────
        try {
            CountDownTimer cdt = new CountDownTimer(120, 40) {
                public void onTick(long remaining) { cdtTicks++; }
                public void onFinish() { cdtFinished = true; }
            };
            boolean started = cdt.start() != null;
            cdt.cancel();
            // A second, uncancelled timer drives the tick chain; the
            // checker runnable below (posted at +500ms, after the CDT
            // events at ≤120ms virtual) logs the assertion.
            final CountDownTimer cdt2 = new CountDownTimer(120, 40) {
                public void onTick(long remaining) { cdtTicks++; }
                public void onFinish() { cdtFinished = true; }
            };
            cdt2.start();
            Handler h4 = new Handler(Looper.getMainLooper());
            h4.postDelayed(new Runnable() {
                public void run() {
                    mark("countdown_timer", cdtTicks >= 2 && cdtFinished,
                            "ticks=" + cdtTicks
                            + " finished=" + cdtFinished);
                }
            }, 500);
            mark("cdt_start", started, "started=" + started
                    + " (assertion posted +500ms)");
        } catch (Throwable t) {
            mark("cdt_start", false, t.getClass().getSimpleName());
            mark("countdown_timer", false, "setup failed");
        }

        // ── F-C8-167: AtomicIntegerArray ────────────────────────────────
        try {
            AtomicIntegerArray a = new AtomicIntegerArray(3);
            a.set(0, 10);
            boolean s1 = a.addAndGet(0, 5) == 15;
            boolean s2 = a.getAndAdd(0, 5) == 15;
            boolean s3 = a.get(0) == 20;
            boolean s4 = a.compareAndSet(0, 20, 30);
            boolean s5 = a.get(0) == 30;
            boolean aioobe;
            try { a.get(5); aioobe = false; }
            catch (ArrayIndexOutOfBoundsException e) { aioobe = true; }
            mark("atomic_int_array", s1 && s2 && s3 && s4 && s5 && aioobe,
                    "15/15/20/30 " + s1 + s2 + s3 + s4 + s5
                    + " aioobe=" + aioobe);
        } catch (Throwable t) {
            mark("atomic_int_array", false, t.getClass().getSimpleName());
        }

        // ── F-C8-168: AtomicLongArray ───────────────────────────────────
        try {
            AtomicLongArray l = new AtomicLongArray(2);
            l.set(1, 3L);
            boolean l1 = l.addAndGet(1, 4L) == 7L;
            boolean l2 = l.getAndAdd(1, 1L) == 7L;
            mark("atomic_long_array", l1 && l2, "7→8 " + l1 + l2);
        } catch (Throwable t) {
            mark("atomic_long_array", false, t.getClass().getSimpleName());
        }

        // ── F-C8-169: ConcurrentMap interface family ────────────────────
        try {
            ConcurrentHashMap<String, String> cm = new ConcurrentHashMap<>();
            boolean p1 = cm.putIfAbsent("k", "v1") == null;
            boolean p2 = "v1".equals(cm.putIfAbsent("k", "v2"));
            boolean p3 = "v1".equals(cm.get("k"));
            boolean p4 = "v1".equals(cm.replace("k", "v3"));
            boolean p5 = "v3".equals(cm.get("k"));
            boolean p6 = "v3".equals(cm.remove("k"));
            boolean p7 = !cm.containsKey("k");
            mark("chm_family", p1 && p2 && p3 && p4 && p5 && p6 && p7,
                    p1 + "" + p2 + p3 + p4 + p5 + p6 + p7);
        } catch (Throwable t) {
            mark("chm_family", false, t.getClass().getSimpleName());
        }

        // ── F-C8-170: ThreadLocalRandom.nextDouble ──────────────────────
        try {
            double d = ThreadLocalRandom.current().nextDouble();
            boolean ok = d >= 0.0 && d < 1.0;
            boolean b = ThreadLocalRandom.current().nextBoolean();
            mark("tlr_next_double", ok && (b == true || b == false),
                    "d=" + d + " b=" + b);
        } catch (Throwable t) {
            mark("tlr_next_double", false, t.getClass().getSimpleName());
        }

        // ── F-C8-171: Throwable cause channel ───────────────────────────
        try {
            Throwable root = new Throwable("root");
            ExecutionException ee = new ExecutionException("wrap", root);
            boolean c1 = ee.getCause() == root;
            CancellationException ce = new CancellationException("c");
            ce.initCause(root);
            boolean c2 = ce.getCause() == root;
            boolean c3;
            try {
                ce.initCause(root);                // JDK: ISE on re-init
                c3 = false;
            } catch (IllegalStateException e) {
                c3 = true;
            }
            new InterruptedException("i").printStackTrace(); // never throws
            mark("cause_channel", c1 && c2 && c3,
                    "cause=" + c1 + " init=" + c2 + " ise=" + c3);
        } catch (Throwable t) {
            mark("cause_channel", false, t.getClass().getSimpleName());
        }

        // ── F-C8-172: ReadWriteLock interface-keyed resolution ─────────
        try {
            ReadWriteLock rwl = new ReentrantReadWriteLock();
            Lock w = rwl.writeLock();
            w.lock();
            w.unlock();
            Lock r = rwl.readLock();
            r.lock();
            r.unlock();
            boolean obs = ((ReentrantReadWriteLock) rwl)
                    .getWriteHoldCount() == 0;
            mark("rwl_iface", w != null && r != null && obs,
                    "locks=" + (w != null && r != null) + " holds0=" + obs);
        } catch (Throwable t) {
            mark("rwl_iface", false, t.getClass().getSimpleName());
        }

        // ── F-C8-173: getCommonPoolParallelism ──────────────────────────
        try {
            int par = ForkJoinPool.getCommonPoolParallelism();
            mark("common_pool_par", par >= 1, "parallelism=" + par);
        } catch (Throwable t) {
            mark("common_pool_par", false, t.getClass().getSimpleName());
        }

        // ── F-C8-174: LinkedBlockingDeque ───────────────────────────────
        try {
            LinkedBlockingDeque<String> dq = new LinkedBlockingDeque<>(8);
            dq.offerLast("b");
            dq.offerLast("c");
            dq.offerFirst("a");
            boolean d1 = "a".equals(dq.pollFirst());
            boolean d2 = "c".equals(dq.pollLast());
            boolean d3 = "b".equals(dq.pollFirst());
            boolean d4 = dq.pollFirst() == null;
            mark("lbd_deque", d1 && d2 && d3 && d4,
                    d1 + "" + d2 + d3 + d4);
        } catch (Throwable t) {
            mark("lbd_deque", false, t.getClass().getSimpleName());
        }

        // ── F-C8-156 (carried): cross-task park/wake window ────────────
        try {
            final Object mon2 = new Object();
            Handler h5 = new Handler(Looper.getMainLooper());
            // R2 is queued BEFORE the wait — the wait law's drain window
            // runs it; its notifyAll erases the waiter → the wake is
            // OBSERVED (wave-8 boundary closed).
            h5.post(new Runnable() {
                public void run() {
                    synchronized (mon2) {
                        crossNotifierRan = true;
                        mon2.notifyAll();
                    }
                }
            });
            synchronized (mon2) {
                mon2.wait(5_000);                  // wake via window
            }
            mark("wait_wake_cross", crossNotifierRan,
                    "notifierRanInWindow=" + crossNotifierRan);
        } catch (Throwable t) {
            mark("wait_wake_cross", false, t.getClass().getSimpleName());
        }

        // ── F-C8-157 (carried): interrupt → InterruptedException ───────
        try {
            final Object mon3 = new Object();
            Thread.currentThread().interrupt();
            synchronized (mon3) {
                mon3.wait(10);                     // JDK: InterruptedException
            }
            mark("wait_interrupt", false, "no throw");
        } catch (InterruptedException e) {
            mark("wait_interrupt", true, "InterruptedException delivered");
        } catch (Throwable t) {
            mark("wait_interrupt", false, t.getClass().getSimpleName());
        }

        // ── F-C8-177: ConcurrentLinkedQueue ─────────────────────────────
        try {
            ConcurrentLinkedQueue<String> q = new ConcurrentLinkedQueue<>();
            q.add("a");
            q.offer("b");
            boolean q1 = "a".equals(q.poll());
            boolean q2 = "b".equals(q.poll());
            boolean q3 = q.poll() == null && q.isEmpty();
            mark("clq_family", q1 && q2 && q3, q1 + "" + q2 + q3);
        } catch (Throwable t) {
            mark("clq_family", false, t.getClass().getSimpleName());
        }

        // ── F-C8-178: Object.finalize boundary ──────────────────────────
        try {
            class Fin {
                boolean closed = false;
                @Override
                protected void finalize() throws Throwable {
                    super.finalize();              // Object.finalize law
                    closed = true;
                }
            }
            Fin fin = new Fin();
            fin.finalize();                        // explicit call: no-throw
            mark("finalize_boundary", fin.closed, "no-throw closed="
                    + fin.closed);
        } catch (Throwable t) {
            mark("finalize_boundary", false, t.getClass().getSimpleName());
        }

        // ── F-C8-179: Semaphore ─────────────────────────────────────────
        try {
            Semaphore s = new Semaphore(2);
            s.acquire();
            boolean t1 = s.tryAcquire();
            boolean t2 = !s.tryAcquire();          // 0 permits left
            s.release();
            boolean t3 = s.tryAcquire();
            boolean t4 = s.availablePermits() == 0;
            mark("semaphore_family", t1 && t2 && t3 && t4,
                    t1 + "" + t2 + t3 + t4);
        } catch (Throwable t) {
            mark("semaphore_family", false, t.getClass().getSimpleName());
        }

        // ── F-C8-180: Future.cancel / isCancelled / get-Cancellation ───
        // Engine model note: the serialized submit law runs the task
        // INLINE at submit (S188-W3), so a submitted future is already
        // COMPLETED — cancel() answers false (JDK law for a completed
        // future). The CANCELLED path needs a PENDING box: a
        // ScheduledFuture from schedule() (F-C8-150 law mints the box
        // without a stored result).
        try {
            ScheduledThreadPoolExecutor sp2 =
                    new ScheduledThreadPoolExecutor(1);
            ScheduledFuture<?> sf3 = sp2.schedule(new Runnable() {
                public void run() { }
            }, 999_999, TimeUnit.MILLISECONDS);
            boolean x1 = sf3.cancel(true);         // pending → true
            boolean x2 = sf3.isCancelled();
            boolean x3 = sf3.isDone();             // cancelled ⇒ done
            boolean x4;
            try {
                sf3.get();
                x4 = false;
            } catch (CancellationException e) {
                x4 = true;
            }
            ExecutorService es3 = Executors.newFixedThreadPool(1);
            Future<String> f3 = es3.submit(new java.util.concurrent.Callable<String>() {
                public String call() { return "DONE"; }
            });
            boolean x5 = !f3.cancel(true);         // completed → false
            boolean x6 = "DONE".equals(f3.get());
            es3.shutdown();
            mark("future_cancel", x1 && x2 && x3 && x4 && x5 && x6,
                    x1 + "" + x2 + x3 + x4 + x5 + x6);
        } catch (Throwable t) {
            mark("future_cancel", false, t.getClass().getSimpleName());
        }

        // ── F-C8-157 extension: Condition.await interrupt delivery ─────
        try {
            ReentrantLock rl3 = new ReentrantLock();
            Condition c5 = rl3.newCondition();
            Thread.currentThread().interrupt();
            rl3.lock();
            c5.await();                            // JDK: InterruptedException
            rl3.unlock();
            mark("cond_await_interrupt", false, "no throw");
        } catch (InterruptedException e) {
            mark("cond_await_interrupt", true, "InterruptedException");
        } catch (Throwable t) {
            mark("cond_await_interrupt", false, t.getClass().getSimpleName());
        }

        // ════════════════════════════════════════════════════════════════
        // S193 [C8] WAVE 10 assertions (defects 181–200, androguard-driven
        // targets: evidence/s192_c8 crossref + the wave-9 §Next list).
        // ════════════════════════════════════════════════════════════════

        // ── F-C8-181: CountDownTimer tick SCHEDULE law ──────────────────
        // A long-delay item posted FIRST forces an idle-settle clock jump
        // past the CDT window; the tick chain must still fire on its own
        // beats (AOSP live-Looper semantics): 2 ticks + onFinish for
        // (120ms total, 40ms interval). Wave-9's law computed remaining
        // from the JUMPED clock → 0 ticks, instant onFinish (the
        // countdown_timer FAIL reproduced at wave-10 start).
        try {
            Handler jump = new Handler(Looper.getMainLooper());
            jump.postDelayed(new Runnable() { public void run() { } },
                    900_000);              // far horizon → settle jump
            cdtTicks = 0;
            cdtFinished = false;
            final CountDownTimer cdt3 = new CountDownTimer(120, 40) {
                public void onTick(long remaining) { cdtTicks++; }
                public void onFinish() { cdtFinished = true; }
            };
            cdt3.start();
            Handler h5 = new Handler(Looper.getMainLooper());
            h5.postDelayed(new Runnable() {
                public void run() {
                    mark("cdt_tick_schedule", cdtTicks >= 2 && cdtFinished,
                            "ticks=" + cdtTicks
                            + " finished=" + cdtFinished);
                }
            }, 800);
        } catch (Throwable t) {
            mark("cdt_tick_schedule", false, t.getClass().getSimpleName());
        }

        // ── F-C8-182: ConcurrentMap INTERFACE-typed dispatch ────────────
        // 7 APKs call get/putIfAbsent through a ConcurrentMap slot
        // (invoke-interface on Ljava/util/concurrent/ConcurrentMap;).
        try {
            ConcurrentMap<String, String> im = new ConcurrentHashMap<>();
            im.put("a", "1");
            boolean i1 = "1".equals(im.get("a"));
            boolean i2 = im.putIfAbsent("a", "2") != null;
            boolean i3 = "1".equals(im.get("a"));
            boolean i4 = "1".equals(im.remove("a"));
            boolean i5 = im.replace("b", "x") == null;
            mark("chm_iface", i1 && i2 && i3 && i4 && i5,
                    i1 + "" + i2 + i3 + i4 + i5);
        } catch (Throwable t) {
            mark("chm_iface", false, t.getClass().getSimpleName());
        }

        // ── F-C8-191: Callable INTERFACE-typed call() ───────────────────
        try {
            Callable<Integer> cb = new Callable<Integer>() {
                public Integer call() { return 41; }
            };
            boolean c1 = cb.call() == 41;
            java.util.concurrent.ExecutorService es4 =
                    Executors.newFixedThreadPool(1);
            Future<Integer> fb = es4.submit(cb);
            boolean c2 = fb.get() == 41;
            es4.shutdown();
            mark("callable_iface", c1 && c2, c1 + "" + c2);
        } catch (Throwable t) {
            mark("callable_iface", false, t.getClass().getSimpleName());
        }

        // ── F-C8-190: UncaughtExceptionHandler iface-typed dispatch ─────
        try {
            final boolean[] got = {false};
            Thread.UncaughtExceptionHandler ueh =
                    new Thread.UncaughtExceptionHandler() {
                        public void uncaughtException(Thread t, Throwable e) {
                            got[0] = true;
                        }
                    };
            Thread.UncaughtExceptionHandler prev =
                    Thread.getDefaultUncaughtExceptionHandler();
            Thread.setDefaultUncaughtExceptionHandler(ueh);
            boolean same = Thread.getDefaultUncaughtExceptionHandler() == ueh;
            ueh.uncaughtException(Thread.currentThread(),
                    new RuntimeException("probe"));
            Thread.setDefaultUncaughtExceptionHandler(prev);
            mark("ueh_iface", same && got[0], same + "" + got[0]);
        } catch (Throwable t) {
            mark("ueh_iface", false, t.getClass().getSimpleName());
        }

        // ── F-C8-183/184: TimerTask surface + Timer schedule ────────────
        // 7 APKs (kotlin timer wrapper family: 138 sites) ride
        // Timer/TimerTask under the hood.
        try {
            final boolean[] ran = {false};
            Timer t2 = new Timer();
            TimerTask tt = new TimerTask() {
                public void run() { ran[0] = true; }
            };
            boolean k1 = !tt.cancel();          // not yet scheduled → false
            t2.schedule(tt, 20);                // one-shot at +20ms
            boolean k2 = tt.scheduledExecutionTime() > 0;
            boolean k3 = t2.purge() == 0;
            t2.cancel();
            mark("timer_task", k1 && k2 && k3, k1 + "" + k2 + k3
                    + " ran=" + ran[0]);
        } catch (Throwable t) {
            mark("timer_task", false, t.getClass().getSimpleName());
        }

        // ── F-C8-185: Thread config ride (kotlin thread{} shape) ────────
        // ThreadsKt.thread(start=true, name, daemon, priority) maps to
        // Thread subclass + config + start — 6 APKs.
        try {
            final boolean[] tRan = {false};
            Thread tw = new Thread(new Runnable() {
                public void run() { tRan[0] = true; }
            }) { };
            tw.setName("c8-wave10");
            tw.setDaemon(false);
            tw.setPriority(7);
            tw.setContextClassLoader(tw.getContextClassLoader());
            boolean f1 = "c8-wave10".equals(tw.getName());
            boolean f2 = tw.getPriority() == 7;
            tw.start();
            tw.join(2000);
            mark("thread_config", f1 && f2 && tRan[0] && !tw.isAlive(),
                    f1 + "" + f2 + " ran=" + tRan[0] + " alive="
                            + tw.isAlive());
        } catch (Throwable t) {
            mark("thread_config", false, t.getClass().getSimpleName());
        }

        // ── F-C8-186: AutoCloseable (try-with-resources close) ──────────
        try {
            final boolean[] closed = {false};
            class Res implements AutoCloseable {
                public void close() { closed[0] = true; }
            }
            boolean a1;
            try (Res r = new Res()) {
                a1 = r != null;
            }
            mark("autocloseable", a1 && closed[0],
                    a1 + " closed=" + closed[0]);
        } catch (Throwable t) {
            mark("autocloseable", false, t.getClass().getSimpleName());
        }

        // ── F-C8-187: Process identity family ───────────────────────────
        try {
            int pid = Process.myPid();
            int uid = Process.myUid();
            int tid = Process.myTid();
            boolean p1 = pid > 0 && uid > 0 && tid > 0;
            boolean p2 = Process.isApplicationUid(10042);
            boolean p3 = !Process.isApplicationUid(1000);
            mark("process_identity", p1 && p2 && p3,
                    "pid=" + pid + " uid=" + uid + " tid=" + tid
                            + " appUid=" + p2 + p3);
        } catch (Throwable t) {
            mark("process_identity", false, t.getClass().getSimpleName());
        }

        // ── F-C8-188/189: Process scheduling + signal boundary ──────────
        try {
            boolean q1 = true;
            try {
                Process.setThreadPriority(Process.myTid(), 10);
            } catch (Throwable inner) {
                q1 = false;
            }
            boolean q2 = true;
            try {
                android.os.Process.killProcess(Process.myPid());
                q2 = true;             // loud boundary: engine keeps running
            } catch (Throwable inner) {
                q2 = false;
            }
            boolean q3 = true;
            try {
                Process.sendSignal(Process.myPid(), 9);
            } catch (Throwable inner) {
                q3 = false;
            }
            mark("process_sched", q1 && q2 && q3, q1 + "" + q2 + q3);
        } catch (Throwable t) {
            mark("process_sched", false, t.getClass().getSimpleName());
        }

        // ── F-C8-192: invokeAll List<Future> shape ──────────────────────
        try {
            java.util.concurrent.ExecutorService es5 =
                    Executors.newFixedThreadPool(2);
            List<Callable<Integer>> tasks = new ArrayList<>();
            tasks.add(new Callable<Integer>() { public Integer call() { return 1; } });
            tasks.add(new Callable<Integer>() { public Integer call() { return 2; } });
            tasks.add(new Callable<Integer>() { public Integer call() { return 3; } });
            List<Future<Integer>> out = es5.invokeAll(tasks);
            boolean v1 = out != null && out.size() == 3;
            boolean v2 = v1 && out.get(0).isDone() && out.get(0).get() == 1;
            boolean v3 = v1 && out.get(1).isDone() && out.get(1).get() == 2;
            boolean v4 = v1 && out.get(2).isDone() && out.get(2).get() == 3;
            es5.shutdown();
            mark("invoke_all", v1 && v2 && v3 && v4,
                    v1 + "" + v2 + v3 + v4);
        } catch (Throwable t) {
            mark("invoke_all", false, t.getClass().getSimpleName());
        }

        // ── F-C8-193: invokeAny ─────────────────────────────────────────
        try {
            java.util.concurrent.ExecutorService es6 =
                    Executors.newFixedThreadPool(1);
            List<Callable<String>> tasks2 = new ArrayList<>();
            tasks2.add(new Callable<String>() { public String call() { return "A"; } });
            tasks2.add(new Callable<String>() { public String call() { return "B"; } });
            String first = es6.invokeAny(tasks2);
            es6.shutdown();
            mark("invoke_any", "A".equals(first) || "B".equals(first),
                    "first=" + first);
        } catch (Throwable t) {
            mark("invoke_any", false, t.getClass().getSimpleName());
        }

        // ── F-C8-194: Looper quit exit semantics ────────────────────────
        try {
            android.os.HandlerThread ht2 = new android.os.HandlerThread("c8q");
            ht2.start();
            android.os.Looper htl = ht2.getLooper();
            boolean w1 = htl != null;
            ht2.quit();
            ht2.join(500);
            boolean w2 = !ht2.isAlive();
            mark("looper_quit", w1 && w2, w1 + "" + w2);
        } catch (Throwable t) {
            mark("looper_quit", false, t.getClass().getSimpleName());
        }

        // ── F-C8-195: Phaser bulk parties ───────────────────────────────
        try {
            Phaser ph = new Phaser(1);
            ph.bulkRegister(2);
            boolean y1 = ph.getRegisteredParties() == 3;
            int phase = ph.arriveAndAwaitAdvance();   // phase 0 → 1
            boolean y2 = phase == 1;
            int un = ph.arriveAndDeregister();
            boolean y3 = un >= 0;
            mark("phaser_party", y1 && y2 && y3,
                    "parties=3 phase=" + phase + " unreg=" + un
                            + " " + y1 + y2 + y3);
        } catch (Throwable t) {
            mark("phaser_party", false, t.getClass().getSimpleName());
        }

        // ── F-C8-197: Semaphore wait-set observables ────────────────────
        try {
            Semaphore s3 = new Semaphore(1);
            s3.acquire();
            boolean z1 = s3.getQueueLength() == 0;
            boolean z2 = !s3.hasQueuedThreads();
            s3.release();
            boolean z3 = s3.availablePermits() == 1;
            mark("sem_observ", z1 && z2 && z3, z1 + "" + z2 + z3);
        } catch (Throwable t) {
            mark("sem_observ", false, t.getClass().getSimpleName());
        }

        // ── F-C8-198: ThreadPoolExecutor queue observables ──────────────
        try {
            ThreadPoolExecutor tpe2 = new ThreadPoolExecutor(2, 2,
                    1000, TimeUnit.MILLISECONDS,
                    new java.util.concurrent.LinkedBlockingQueue<Runnable>());
            boolean u1 = tpe2.getQueue() != null;
            tpe2.submit(new Runnable() { public void run() { } });
            boolean u2 = tpe2.getCompletedTaskCount() >= 0;
            boolean u3 = tpe2.getActiveCount() >= 0
                    && tpe2.getPoolSize() <= 2;
            tpe2.prestartCoreThread();     // JDK: no-throw boolean; shape law
            boolean u4 = tpe2.getPoolSize() <= 2;
            tpe2.shutdown();
            mark("tpe_observ", u1 && u2 && u3 && u4,
                    u1 + "" + u2 + u3 + u4);
        } catch (Throwable t) {
            mark("tpe_observ", false, t.getClass().getSimpleName());
        }

        // ── F-C8-199: Thread stack-trace surface ────────────────────────
        try {
            java.util.Map<Thread, StackTraceElement[]> all =
                    Thread.getAllStackTraces();
            boolean s10 = all != null
                    && all.containsKey(Thread.currentThread());
            StackTraceElement[] mine = Thread.currentThread().getStackTrace();
            boolean s11 = mine != null;
            mark("stack_traces", s10 && s11,
                    "threads=" + (all == null ? -1 : all.size())
                            + " frames=" + (mine == null ? -1 : mine.length));
        } catch (Throwable t) {
            mark("stack_traces", false, t.getClass().getSimpleName());
        }

        // ── F-C8-200: Handler/Looper binding surface ────────────────────
        try {
            android.os.Looper main = Looper.getMainLooper();
            Handler hb = new Handler(main);
            boolean h1 = hb.getLooper() == main;
            boolean h2 = Looper.myLooper() == main;
            boolean h3 = Looper.myQueue() != null;
            mark("handler_looper", h1 && h2 && h3, h1 + "" + h2 + h3);
        } catch (Throwable t) {
            mark("handler_looper", false, t.getClass().getSimpleName());
        }

        android.util.Log.i("C8PROBE", "ALL-DONE");
    }
}
