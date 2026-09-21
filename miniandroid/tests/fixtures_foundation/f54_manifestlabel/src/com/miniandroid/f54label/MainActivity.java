package com.miniandroid.f54label;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        // The A7 proof lives in the MANIFEST path: the application label is a
        // REFERENCE (@string/app_name) resolved through resources.arsc by the
        // engine's PackageParser-law wiring. This activity renders the same
        // string so the frame also carries visual evidence of the value.
        setContentView(R.layout.activity_main);
    }
}
