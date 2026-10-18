package com.probe.acts2;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;

/** F-145 probe leg A: red full-screen, launches B after 400ms. */
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout v = new LinearLayout(this);
        v.setBackgroundColor(Color.RED);
        setContentView(v);
        v.postDelayed(() -> startActivity(
                new android.content.Intent(this, SecondActivity.class)), 400);
    }
}
