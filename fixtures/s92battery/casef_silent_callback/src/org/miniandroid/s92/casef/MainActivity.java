package org.miniandroid.s92.casef;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;

public class MainActivity extends Activity {
    private int hidden = 0;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Button b = (Button) findViewById(R.id.increment);
        b.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                hidden++;          // NO UI update on purpose (2+2 class)
            }
        });
    }
}
