package com.probe.c124;

import android.app.Activity;
import android.os.Bundle;

/**
 * CONT-124 F-NEW-469 probe: three-level interface chain assignability.
 *
 * I1 <- I2 extends I1 <- I3 extends I2; Impl implements I3.
 * JVMS 5.1 / ART Class.isAssignableFrom: Impl IS-A I1 through the
 * transitive superinterface chain — an aput-object of Impl into I1[]
 * must SUCCEED. The pre-fix engine checked only DIRECTLY declared
 * interfaces per walk node and threw a BOGUS ArrayStoreException
 * (live face: dooz v23 Liw0;.b, Lf6; -> [Lxt0; via Lbu0;->Lvt0;->Lxt0;).
 * Negative control: an unrelated class into I1[] must STILL throw.
 */
public class MainActivity extends Activity {
    public interface I1 { int id(); }
    public interface I2 extends I1 {}
    public interface I3 extends I2 {}
    public static class Impl implements I3 {
        public int id() { return 42; }
    }
    public static class Other { }

    private static void report(String name, boolean pass, String detail) {
        System.out.println("C124-PROBE " + name + " "
            + (pass ? "PASS" : "FAIL") + " " + detail);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // 1. direct store: Impl into I3[] (its own interface).
        try {
            I3[] direct = new I3[2];
            direct[0] = new Impl();
            report("direct-store", direct[0].id() == 42,
                    "stored+dispatched");
        } catch (ArrayStoreException e) {
            report("direct-store", false, "bogus AIOOBE: " + e.getMessage());
        }

        // 2. THE F-NEW-469 LAW: Impl into I1[] — assignability flows
        //    through I3 -> I2 -> I1 transitively.
        try {
            I1[] wide = new I1[2];
            wide[0] = new Impl();
            report("transitive-store", wide[0].id() == 42,
                    "grandparent-interface store legal");
        } catch (ArrayStoreException e) {
            report("transitive-store", false,
                    "BOGUS AIOOBE (pre-fix face): " + e.getMessage());
        }

        // 3. negative control: unrelated class into I1[] must throw.
        //    Array covariance makes the store compile-legal (Object[] alias);
        //    the runtime store-check must still raise ArrayStoreException.
        try {
            I1[] neg = new I1[1];
            Object[] covariant = neg;
            covariant[0] = new Other();
            report("negative-store", false,
                    "illegal store SILENTLY PASSED (dishonest)");
        } catch (ArrayStoreException e) {
            report("negative-store", true,
                    "AIOOBE correctly raised for unrelated type");
        }

        // 4. interface dispatch through the chain (I1 receiver, Impl body).
        try {
            I1[] arr = new I1[1];
            arr[0] = new Impl();
            int v = arr[0].id();
            report("chain-dispatch", v == 42, "id()=" + v);
        } catch (Throwable t) {
            report("chain-dispatch", false, t.toString());
        }
    }
}
