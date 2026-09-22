package com.miniandroid.snakedeluxe;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.Window;
import android.widget.Button;
import android.app.AlertDialog;

/**
 * Snake Deluxe — a full-graphics Snake for the MiniAndroid compatibility
 * runtime. Real Android app: Activity + custom View.onDraw(Canvas) +
 * background game thread + D-pad buttons + game-over dialog. No third-party
 * dependencies (pure android.jar surface).
 */
public class MainActivity extends Activity {

    GameView game;
    Handler main;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        game = (GameView) findViewById(R.id.game);
        main = new Handler(Looper.getMainLooper());

        GameView.host = this;

        findViewById(R.id.btn_start).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { GameView.toggleStart(); }
        });
        findViewById(R.id.btn_top).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { GameView.pushDir(0, -1); }
        });
        findViewById(R.id.btn_left).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { GameView.pushDir(-1, 0); }
        });
        findViewById(R.id.btn_right).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { GameView.pushDir(1, 0); }
        });
        findViewById(R.id.btn_bottom).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { GameView.pushDir(0, 1); }
        });

        game.startTicker();
    }

    /** Game-over dialog — shown on the main looper by the game thread. */
    public void showGameOver(final int score, final int best) {
        main.post(new Runnable() {
            public void run() {
                AlertDialog.Builder b = new AlertDialog.Builder(MainActivity.this);
                b.setTitle("Game Over");
                b.setMessage("Score: " + score + "   Best: " + best);
                b.setCancelable(false);
                b.setPositiveButton("Restart", new android.content.DialogInterface.OnClickListener() {
                    public void onClick(android.content.DialogInterface d, int w) {
                        game.resetAndStart();
                    }
                });
                b.show();
            }
        });
    }
}
