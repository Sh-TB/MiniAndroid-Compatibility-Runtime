package org.miniandroid.s92.casea;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;

/** S92 case A: the button (id=hidden) is fully covered by an opaque
 *  overlay View. Taps may still fire the callback (blind tap), but the
 *  overlay makes the button invisible to pixels, so the verifier MUST
 *  NOT count this as a visible interaction (required_verdict REJECT).
 *  Fixture repair (S-HYGIENE): previous source referenced R.id.counter
 *  / R.id.increment which do not exist in this case's layout (compile
 *  failure after container reset); semantics unchanged. */
public class MainActivity extends Activity {
    private int count = 0;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Button b = (Button) findViewById(R.id.hidden);
        b.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                count++;   // state-only change; NO visual change (covered)
            }
        });
    }
}
