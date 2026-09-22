package com.miniandroid.tictactoedeluxe;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;

/**
 * TicTacToe Deluxe — Activity host: 9 cell buttons (proven click-listener
 * dispatch), NEW GAME + MODE toggle, round-end dialog. Board rendering is
 * GameView.onDraw over static state (S80 runtime law).
 */
public class MainActivity extends Activity {

    GameView game;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        game = (GameView) findViewById(R.id.game);

        GameView.host = this;

        int[] ids = {R.id.c1, R.id.c2, R.id.c3, R.id.c4, R.id.c5,
                     R.id.c6, R.id.c7, R.id.c8, R.id.c9};
        for (int i = 0; i < ids.length; i++) {
            final int idx = i;
            findViewById(ids[i]).setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) { GameView.playCell(idx); }
            });
        }

        findViewById(R.id.btn_new).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { GameView.newRound(); }
        });
        findViewById(R.id.btn_mode).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { GameView.toggleMode(); }
        });

        GameView.newRound();
    }

    public void onModeChanged() {
        Button mode = (Button) findViewById(R.id.btn_mode);
        mode.setText(GameView.vsAI ? "MODE: VS PHONE" : "MODE: 2 PLAYER");
    }

    /** Round-end dialog (draws over the frozen board). */
    public void showRound(final int w, final int sx, final int so, final int sd) {
        String msg;
        if (w == 1) msg = "X wins!   Score  X " + sx + " : " + so + " O   (D " + sd + ")";
        else if (w == 2) msg = (GameView.vsAI ? "Phone wins!" : "O wins!")
                               + "   Score  X " + sx + " : " + so + " O   (D " + sd + ")";
        else msg = "Draw!   Score  X " + sx + " : " + so + " O   (D " + sd + ")";

        AlertDialog.Builder b = new AlertDialog.Builder(MainActivity.this);
        b.setTitle("Round over");
        b.setMessage(msg);
        b.setCancelable(false);
        b.setPositiveButton("NEXT ROUND", new android.content.DialogInterface.OnClickListener() {
            public void onClick(android.content.DialogInterface d, int which) {
                GameView.newRound();
            }
        });
        b.show();
    }
}
