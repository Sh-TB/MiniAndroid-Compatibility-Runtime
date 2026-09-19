package com.miniandroid.f38_identity_pkg;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
public class MainActivity extends Activity {
    public static class Box { public int v; }
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        TextView tv = new TextView(this);
        Box a = new Box(); a.v = 7;
        Box c = a;                 // identity: same reference
        c.v = 42;                  // mutates a.v too
        Box d = new Box(); d.v = 42;
        boolean same = (a == c);       // true
        boolean diff = (a == d);       // false (equal fields, different identity)
        tv.setText("IDENT=" + same + "," + diff + ",v=" + a.v);
        setContentView(tv);
    }
}
