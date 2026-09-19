package com.miniandroid.f31res;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main);
        // API-path cross-check: same string via getResources()
        TextView tv = (TextView) findViewById(R.id.res_tv);
        if (tv != null) tv.setText(R.string.greeting);
    }
}
