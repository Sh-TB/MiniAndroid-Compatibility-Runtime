package com.miniandroid.f27nav;
import android.app.Activity; import android.content.Intent; import android.os.Bundle;
import android.view.View; import android.widget.Button;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main);
        Button go = (Button) findViewById(R.id.go);
        go.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, SecondActivity.class));
            }
        });
    }
}
