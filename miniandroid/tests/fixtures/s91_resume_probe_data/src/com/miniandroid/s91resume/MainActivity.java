package com.miniandroid.s91resume;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        SharedPreferences sp = getSharedPreferences("resume", Context.MODE_PRIVATE);
        int r = sp.getInt("withadd", 0);
        SharedPreferences.Editor ed = sp.edit();
        ed.putInt("const", 42);
        ed.putInt("nostatic", r);
        ed.putInt("withadd", r + 1);
        ed.putInt("pureadd", 7 + 1);
        ed.commit();
    }
}
