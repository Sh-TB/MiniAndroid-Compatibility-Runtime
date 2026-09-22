package com.miniandroid.tetris;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.app.AlertDialog;

/** Mini Tetris — real Android app for the MiniAndroid runtime (S80).
 *  Static game state + main-looper postDelayed ticker (runtime laws). */
public class MainActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        TetrisView.host = this;

        findViewById(R.id.btn_left).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { TetrisView.move(-1); }
        });
        findViewById(R.id.btn_right).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { TetrisView.move(1); }
        });
        findViewById(R.id.btn_rotate).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { TetrisView.rotate(); }
        });
        findViewById(R.id.btn_drop).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { TetrisView.softDrop(); }
        });
        findViewById(R.id.btn_start).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { TetrisView.toggleStart(); }
        });

        ((TetrisView) findViewById(R.id.game)).startTicker();
    }

    public void showGameOver(final int score, final int lines) {
        Handler h = new Handler(Looper.getMainLooper());
        h.post(new Runnable() {
            public void run() {
                AlertDialog.Builder b = new AlertDialog.Builder(MainActivity.this);
                b.setTitle("Game Over");
                b.setMessage("Score: " + score + "   Lines: " + lines);
                b.setCancelable(false);
                b.setPositiveButton("Restart", new android.content.DialogInterface.OnClickListener() {
                    public void onClick(android.content.DialogInterface d, int w) {
                        TetrisView.resetAndStart();
                    }
                });
                b.show();
            }
        });
    }
}
