package com.probe.f252;

/**
 * F-NEW-252 wave-2 probe core (CONT-7 WAVE 2 sections 6/7).
 *
 * Section 7 CAS contract (directive-required, on ONE logical field):
 *   initial = 1
 *   CAS(expected=1, update=0) => true ;  read => 0
 *   CAS(expected=1, update=2) => false;  read => 0
 *   CAS(expected=0, update=2) => true ;  read => 2
 * plus AtomicIntegerFieldUpdater get/set/compareAndSet/getAndIncrement/
 * getAndDecrement and plain interpreter reads/writes against the SAME
 * field — the F-NEW-251 invariant (one logical slot across all layers).
 *
 * Section 6 ServiceLoader semantics:
 *   positive: META-INF/services/com.probe.f252.Svc present with
 *             com.probe.f252.SvcImpl → loader must discover + instantiate.
 *   negative: no provider file for SvcMissing → empty iterator, expected
 *             semantic failure (hasNext()==false), not a crash.
 *
 * Param-null integrity (the F-NEW-252 law, synthetic):
 *   a null passed through a parameter slot, stored to a field after
 *   intermediate invokes, then read back MUST be null (identity + branch).
 */
public final class F252Core {

    public interface Row { void row(String id, boolean ok, String detail); }

    // ── §7 target field: ONE logical slot, touched by plain + updater ──
    public volatile int counter = 1;

    public static final java.util.concurrent.atomic.AtomicIntegerFieldUpdater<F252Core> UPD =
        java.util.concurrent.atomic.AtomicIntegerFieldUpdater.newUpdater(
            F252Core.class, "counter");

    public void run(Row row) {
        casContract(row);
        updaterOps(row);
        paramNullIntegrity(row);
        serviceLoaderPositive(row);
        serviceLoaderNegative(row);
    }

    private void casContract(Row row) {
        // reset to the directive's initial state
        UPD.set(this, 1);
        boolean c1 = UPD.compareAndSet(this, 1, 0);
        int r1 = UPD.get(this);
        row.row("CAS1", c1 && r1 == 0, "CAS(1->0)=" + c1 + " read=" + r1);

        boolean c2 = UPD.compareAndSet(this, 1, 2);
        int r2 = UPD.get(this);
        row.row("CAS2", !c2 && r2 == 0, "CAS(1->2)=" + c2 + " read=" + r2);

        boolean c3 = UPD.compareAndSet(this, 0, 2);
        int r3 = UPD.get(this);
        row.row("CAS3", c3 && r3 == 2, "CAS(0->2)=" + c3 + " read=" + r3);
    }

    private void updaterOps(Row row) {
        // start from a known value: plain write (interpreter layer)
        this.counter = 10;
        int g = UPD.get(this);
        UPD.set(this, 20);
        int afterSet = this.counter;
        int gi = UPD.getAndIncrement(this);
        int afterInc = UPD.get(this);
        int gd = UPD.getAndDecrement(this);
        int afterDec = UPD.get(this);
        boolean ok = g == 10 && afterSet == 20 && gi == 20
                && afterInc == 21 && gd == 21 && afterDec == 20;
        row.row("UPD", ok,
            "get=" + g + " set→" + afterSet
            + " getAndInc=" + gi + "/" + afterInc
            + " getAndDec=" + gd + "/" + afterDec);
    }

    // ── param-null integrity (F-NEW-252 law) ────────────────────────────
    public Object slot;

    /** intermediate callee so the param outlives invokes in the caller */
    private int touch(Object o) { return o == null ? 7 : 1; }

    public void take(Object p) {
        int mid = touch(p);          // an invoke BEFORE the store
        this.slot = p;               // store the param AFTER an invoke
        this.slot = (mid == 7) ? p : this.slot;  // branch on the invoke result
    }

    private void paramNullIntegrity(Row row) {
        this.slot = new Object();
        take(null);
        boolean isNull = this.slot == null;
        boolean castOk = false;
        try {
            Object x = (String) this.slot;   // null cast must succeed
            castOk = (x == null);
        } catch (Throwable t) { castOk = false; }
        row.row("PNULL", isNull && castOk,
            "slot==null:" + isNull + " castNull:" + castOk);
    }

    // ── §6 ServiceLoader ────────────────────────────────────────────────
    private void serviceLoaderPositive(Row row) {
        try {
            java.util.Iterator<Svc> it =
                java.util.ServiceLoader.load(Svc.class).iterator();
            boolean has = it.hasNext();
            Svc impl = has ? it.next() : null;
            String tag = impl == null ? "-" : impl.tag();
            row.row("SLPOS", has && impl instanceof SvcImpl && "svcimpl".equals(tag),
                "hasNext=" + has + " impl=" + (impl == null ? "null"
                    : impl.getClass().getName()) + " tag=" + tag);
        } catch (Throwable t) {
            row.row("SLPOS", false, t.getClass().getName() + ": " + t.getMessage());
        }
    }

    private void serviceLoaderNegative(Row row) {
        try {
            java.util.Iterator<SvcMissing> it =
                java.util.ServiceLoader.load(SvcMissing.class).iterator();
            boolean has = it.hasNext();
            row.row("SLNEG", !has, "no provider → hasNext=" + has
                + " (expected false, no crash)");
        } catch (Throwable t) {
            row.row("SLNEG", false, t.getClass().getName() + ": " + t.getMessage());
        }
    }
}
