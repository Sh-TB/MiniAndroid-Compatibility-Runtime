package com.miniandroid.f45_exceptions_pkg;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        TextView tv = new TextView(this);
        String result;
        try {
            int[] arr = new int[3];
            arr[5] = 1;                      // AIOOBE
            result = "NO_THROW";
        } catch (ArrayIndexOutOfBoundsException e) {
            result = "CAUGHT_AIOOBE";
        } finally {
            // finally path
        }
        setContentView(tv);
        tv.setText("EXC=" + result);
    }
}
