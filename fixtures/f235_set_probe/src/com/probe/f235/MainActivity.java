package com.probe.f235;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends Activity {
    static List<String> out = new ArrayList<String>();
    static int pass = 0, fail = 0;

    static final F235Core.Row ROW = new F235Core.Row() {
        public void row(String id, boolean ok, String detail) {
            out.add("F235|" + id + "|" + (ok ? "PASS" : "FAIL") + "|" + detail);
            if (ok) pass++; else fail++;
        }
    };

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        out.clear(); pass = 0; fail = 0;
        try {
            F235Core.run(ROW);
        } catch (Throwable t) {
            out.add("F235|HARNESS|FAIL|" + t.getClass().getName()
                    + ": " + t.getMessage());
            fail++;
        }
        out.add("F235|SUMMARY|" + (fail == 0 ? "PASS" : "FAIL")
                + "|" + pass + " pass, " + fail + " fail");
        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        TextView tv = new TextView(this);
        tv.setText(sb.toString());
        setContentView(tv);
        try {
            java.io.FileOutputStream fos =
                openFileOutput("f235_results.jsonl", MODE_PRIVATE);
            fos.write(sb.toString().getBytes("UTF-8"));
            fos.close();
        } catch (Throwable t) { }
    }
}
