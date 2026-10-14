package com.probe.fragtx;

import android.app.Activity;
import android.app.FragmentManager;
import android.app.FragmentTransaction;
import android.os.Bundle;

/**
 * F-NEW-304 (CONT-42) — the platform FragmentTransaction pending-op law,
 * probe-proven end to end. The transaction chain runs in onCreate (the
 * tananaev MainActivity shape); the fragment lifecycle rows land as the
 * engine drains the committed queue at the host's CREATED/STARTED/RESUMED
 * windows; the identity rows run in onResume (after the started drain).
 * Rows print via System.out (engine println → host stdout law) so the
 * runner can grep them from run.log.
 */
public class MainActivity extends Activity {
    static final StringBuilder REPORT = new StringBuilder();
    static void row(String id, boolean pass, String detail) {
        REPORT.append(id).append('|').append(pass ? "PASS" : "FAIL")
              .append('|').append(detail).append('\n');
    }

    ProbeFragment frag;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);
        try {
            FragmentManager fm = getFragmentManager();
            row("FT-01", fm != null, "fm non-null=" + (fm != null));
            FragmentTransaction tx = fm.beginTransaction();
            row("FT-02", tx != null, "tx non-null=" + (tx != null));
            frag = new ProbeFragment();
            FragmentTransaction t2 = tx.add(android.R.id.content, frag, "probefrag");
            row("FT-03", t2 == tx, "fluent same-object=" + (t2 == tx));
            int id = tx.commit();
            row("FT-04", id >= 0, "commit id=" + id);
        } catch (Throwable t) {
            row("FT-01", false, "threw " + t);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        // The started-stage drain has run by now (the host's onStart window
        // precedes onResume) — every fragment lifecycle row is final here.
        try {
            android.app.Fragment f =
                getFragmentManager().findFragmentByTag("probefrag");
            row("FT-10", f == frag, "findFragmentByTag identity=" + (f == frag));
            row("FT-11", frag.isAdded() && frag.getView() != null,
                "isAdded=" + frag.isAdded()
                + " view non-null=" + (frag.getView() != null));
        } catch (Throwable t) {
            row("FT-10", false, "threw " + t);
        }
        java.io.PrintStream out = System.out;
        for (String line : REPORT.toString().split("\n")) {
            if (!line.isEmpty()) out.println(line);
        }
    }
}
