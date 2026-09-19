package com.miniandroid.f26lifecycle;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
public class MainActivity extends Activity {
    private int ctor = 0;
    private int field = 5;
    public MainActivity() { ctor = 6; }
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        TextView tv = new TextView(this);
        // LC28/LC29: constructor + field initializers ran before onCreate (F-118)
        tv.setText("INIT=" + ctor + "," + field);
        setContentView(tv);
    }
}
