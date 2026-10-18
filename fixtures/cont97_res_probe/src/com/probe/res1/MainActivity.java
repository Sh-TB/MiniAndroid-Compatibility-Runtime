package com.probe.res1;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

/**
 * CONT-97 T3 (F-NEW-399 candidate): TextView.setText(@StringRes int) must
 * resolve the string NOW (AOSP Resources law) — the visible text is the
 * table's string, not a [resid:0x...] placeholder. Verdict rows go to
 * stdout; the row contract:
 *   [RES1] direct=...          setText(R.string.hello_res) then getText()
 *   [RES1] string-then-res=... string setText followed by resid setText
 *                              (AOSP: the resid OVERWRITES the string —
 *                              setText always replaces the text)
 *   [RES1] verdict=PASS|FAIL
 */
public class MainActivity extends Activity {
    private static String row(String tag, CharSequence v) {
        return "[RES1] " + tag + "=" + v;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView tv = new TextView(this);

        // Row 1: direct resid setText — the law under test.
        tv.setText(R.string.hello_res);
        String direct = String.valueOf(tv.getText());
        System.out.println(row("direct", direct));

        // Row 2: AOSP overwrite semantics — setText(int) after setText(CharSequence).
        TextView tv2 = new TextView(this);
        tv2.setText("STRING-FIRST");
        tv2.setText(R.string.plain_res);
        String second = String.valueOf(tv2.getText());
        System.out.println(row("string-then-res", second));

        boolean ok = "RES1-HELLO-STRING-V1".equals(direct)
                && "PLAIN-TEXT-LAW".equals(second);
        System.out.println("[RES1] verdict=" + (ok ? "PASS" : "FAIL")
                + " direct_ok=" + "RES1-HELLO-STRING-V1".equals(direct)
                + " overwrite_ok=" + "PLAIN-TEXT-LAW".equals(second));

        setContentView(tv);
    }
}
