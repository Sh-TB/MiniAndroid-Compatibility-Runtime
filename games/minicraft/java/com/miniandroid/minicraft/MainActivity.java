package com.miniandroid.minicraft;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;

/** MiniCraft — house-building sandbox (S86 in-house game).
 *  Static state (runtime object-identity law); every action is a real
 *  button click: direction pad walks the build cursor, BLOCK cycles the
 *  material, PLACE/DIG edit the world, DEMO auto-builds the cottage. */
public class MainActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        CraftWorldView.genTerrain();

        findViewById(R.id.btn_left).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { CraftWorldView.moveCursor(0, -1); }
        });
        findViewById(R.id.btn_up).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { CraftWorldView.moveCursor(-1, 0); }
        });
        findViewById(R.id.btn_down).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { CraftWorldView.moveCursor(1, 0); }
        });
        findViewById(R.id.btn_right).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { CraftWorldView.moveCursor(0, 1); }
        });
        findViewById(R.id.btn_block).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { CraftWorldView.cycleBlock(); }
        });
        findViewById(R.id.btn_place).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { CraftWorldView.place(); }
        });
        findViewById(R.id.btn_dig).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { CraftWorldView.dig(); }
        });
        findViewById(R.id.btn_demo).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { CraftWorldView.buildDemoHouse(); }
        });
    }
}
