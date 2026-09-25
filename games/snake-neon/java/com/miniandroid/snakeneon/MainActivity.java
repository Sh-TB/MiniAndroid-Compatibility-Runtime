package com.miniandroid.snakeneon;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.widget.Button;

/**
 * Snake Neon (S98 GAMES-4) — a NEW snake variant built for the runtime,
 * mechanically distinct from Snake Deluxe:
 *
 *   1. WRAP-AROUND walls — leaving one edge re-enters the opposite edge
 *      (Snake Deluxe kills at walls; Neon never does).
 *   2. OBSTACLE BLOCKS — every 3rd food spawns a static magenta block
 *      (up to 4); hitting one ends the run.
 *   3. SPEED RAMPS — the tick shortens every 4 foods (260ms floor 140ms).
 *
 * Written against the documented runtime laws (games/README.md):
 *   Static-state law — ALL mutable game state lives in static fields
 *   (instance-field writes from the click listener are not visible to the
 *   onDraw render path on this runtime; OBJECT-IDENTITY frontier).
 *   Thread law — no new Thread(Runnable); the tick is a Handler
 *   postDelayed self-reposting chain on the main looper.
 */
public class MainActivity extends Activity {

    public static Handler ticker;
    public static Runnable tickTask;
    public static boolean running = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        NeonSnakeView.game = (NeonSnakeView) findViewById(R.id.game);

        tap(R.id.btn_left, 0);
        tap(R.id.btn_up, 1);
        tap(R.id.btn_down, 2);
        tap(R.id.btn_right, 3);
    }

    private void tap(int id, final int dir) {
        ((Button) findViewById(id)).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                NeonSnakeView.wantDir(dir);
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (!running) {
            running = true;
            ticker = new Handler();
            tickTask = new Runnable() {
                public void run() {
                    if (!running) return;
                    NeonSnakeView.step();
                    NeonSnakeView.game.invalidate();
                    ticker.postDelayed(this, NeonSnakeView.tickMs());
                }
            };
            ticker.postDelayed(tickTask, NeonSnakeView.tickMs());
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        running = false;
    }
}
