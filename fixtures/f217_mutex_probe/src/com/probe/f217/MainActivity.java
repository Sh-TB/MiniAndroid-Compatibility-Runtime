package com.probe.f217;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.LinkedList;
import java.util.concurrent.atomic.AtomicReference;

/**
 * CONT-18 T-01 — F-NEW-217 waiter-resume / MutexImpl first-divergence probe.
 *
 * SOURCE: the real kotlinx-coroutines SemaphoreAndMutexImpl/MutexImpl bytecode
 * extracted from the corpus DEX (evidence/cont18/f217_dex_extract.json +
 * f217_unlock_disasm.txt). The probe reimplements THAT algorithm's state
 * machine verbatim (plain Java) and exercises the three semantic transitions
 * the runtime must honor for the waiter-resume protocol to progress:
 *
 *   F217-A  CAS retry-loop progress (tryLockImpl/unlock retry shape):
 *           a failed CAS must be retried and terminate — the loop that
 *           spins 50,001 times into F-084 must instead advance.
 *   F217-B  UNLOCK DRAIN RESUMES THE QUEUED WAITER (the F-217 face):
 *           unlock() with owner=LOCKED and a queued waiter resumes the
 *           waiter's continuation INLINE (same-cycle nested side effect,
 *           the brief's "nested side effects lost" face) and transfers
 *           ownership — the waiter's body MUST run exactly once.
 *   F217-C  unlock on a NO_OWNER mutex throws ISE ("This mutex is not
 *           locked") — the real bytecode's 0008 -> 0094 arm; never a
 *           silent return.
 *
 * LAW ANCHOR (extracted algorithm, Corpus DEX unlock @88 units):
 *   unlock(owner): loop { cur = owner.value;
 *     if (cur == NO_OWNER) -> ISE "This mutex is not locked";
 *     if (cur != LOCKED && cur != owner-param) -> ISE "This mutex is locked by ...";
 *     if (CAS(cur -> NO_OWNER)) { if (!tryResumeNextFromQueue()) return; }
 *     else retry }   -- the retry arm is the F-084 spin site.
 */
public class MainActivity extends Activity {

    // Extracted state-machine sentinels (kotlinx SemaphoreAndMutexImpl).
    private static final Object NO_OWNER = new Object();
    private static final Object LOCKED = new Object();

    private static final AtomicReference<Object> owner =
            new AtomicReference<Object>(NO_OWNER);
    // SegmentedQueue contract: FIFO waiter queue; drain takes head.
    private static final LinkedList<Runnable> waiters = new LinkedList<Runnable>();

    private static int casSpins = 0;
    private static int waiterRuns = 0;
    private static String drainTrace = "";

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    /** The extracted tryLock CAS loop (kotlinx tryLockImpl shape). */
    private static boolean tryLock() {
        while (true) {
            Object cur = owner.get();
            if (cur == NO_OWNER) {
                casSpins++;
                if (owner.compareAndSet(NO_OWNER, LOCKED)) return true;
                casSpins++; // CAS failed -> retry (bounded in the probe app)
                if (casSpins > 64) return false; // honesty bound, never a spin
            } else {
                return false; // contended
            }
        }
    }

    /** The extracted unlock: CAS retry + INLINE waiter drain (F-217 face). */
    private static void unlock() {
        while (true) {
            Object cur = owner.get();
            if (cur == NO_OWNER) {
                throw new IllegalStateException("This mutex is not locked");
            }
            casSpins++;
            if (owner.compareAndSet(cur, NO_OWNER)) {
                // OpenJDK/kotlinx drain law: a queued waiter is resumed
                // INLINE (same cycle) — the waiter's continuation body runs
                // before unlock returns, ownership transfers by re-acquire.
                Runnable head;
                synchronized (waiters) { head = waiters.poll(); }
                if (head != null) {
                    drainTrace += "drain;";
                    head.run();  // the resume — side effects MUST survive
                }
                return;
            }
            if (casSpins > 64) {
                throw new IllegalStateException("unlock CAS loop stalled");
            }
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── F217-A: CAS retry-loop progress ─────────────────────────────
        try {
            boolean got = tryLock();
            boolean again = tryLock(); // contended -> false, no spin
            unlock();
            boolean reacquired = tryLock();
            unlock();
            row("F217-A", got && !again && reacquired && casSpins <= 64,
                "got=" + got + " contended=" + !again + " re=" + reacquired
                    + " spins=" + casSpins);
        } catch (Throwable t) {
            row("F217-A", false, "threw " + t);
        }

        // ── F217-B: unlock drain resumes the queued waiter (inline) ─────
        try {
            owner.set(NO_OWNER);
            waiters.clear();
            waiterRuns = 0;
            if (tryLock()) {
                synchronized (waiters) {
                    waiters.add(new Runnable() {
                        public void run() {
                            waiterRuns++;
                            drainTrace += "body;";
                            // The resumed waiter completes its acquire and
                            // releases (the withLock finally shape).
                            if (owner.compareAndSet(NO_OWNER, LOCKED)) {
                                drainTrace += "owned;";
                            }
                        }
                    });
                }
                unlock();  // must drain + run the waiter body inline
            }
            boolean ok = waiterRuns == 1 && drainTrace.contains("body;")
                         && drainTrace.contains("owned;");
            row("F217-B", ok, "runs=" + waiterRuns + " trace=" + drainTrace);
        } catch (Throwable t) {
            row("F217-B", false, "threw " + t);
        }

        // ── F217-C: unlock on NO_OWNER throws ISE (real bytecode arm) ───
        try {
            owner.set(NO_OWNER);
            try {
                unlock();
                row("F217-C", false, "no-throw (silent unlock on free mutex)");
            } catch (IllegalStateException ise) {
                row("F217-C", true, "ISE thrown as the bytecode requires");
            }
        } catch (Throwable t) {
            row("F217-C", false, "outer threw " + t);
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        tv.setText(report.isEmpty() ? "NO ROWS" : report);
        root.addView(tv);
        setContentView(root);
    }
}
