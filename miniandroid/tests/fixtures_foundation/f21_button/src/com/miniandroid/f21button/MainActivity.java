package com.miniandroid.f21button;
import android.app.Activity; import android.os.Bundle; import android.view.View;
import android.widget.Button; import android.widget.TextView;
public class MainActivity extends Activity {
    private int count = 0;
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main);
        Button btn = (Button) findViewById(R.id.btn);
        final TextView state = (TextView) findViewById(R.id.state);
        btn.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                count++;
                state.setText("STATE=" + count);
            }
        });
    }
}
