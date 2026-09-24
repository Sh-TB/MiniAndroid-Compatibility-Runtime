package org.miniandroid.s92.good;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

public class MainActivity extends Activity {
    private int count = 0;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        final TextView tv = (TextView) findViewById(R.id.counter);
        Button b = (Button) findViewById(R.id.increment);
        b.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                count++;
                tv.setText("counter: " + count);
            }
        });
    }
}
