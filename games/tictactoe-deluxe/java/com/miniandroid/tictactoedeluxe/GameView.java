package com.miniandroid.tictactoedeluxe;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.os.Handler;
import android.os.Looper;
import android.view.View;

/**
 * TicTacToe Deluxe game surface — real Canvas.onDraw rendering:
 * dark panel, 3x3 grid with inner shadows, hand-drawn X (two rounded
 * strokes) and O (ring), winning-line strike, per-player score HUD,
 * turn indicator and status banner.
 *
 * RUNTIME LAW NOTES (S80/S83):
 * - All game state lives in STATIC fields (engine SGET/SPUT storage is
 *   class-global — the click-listener instance-mutation frontier).
 * - Input arrives from the 9 cell buttons + NEW GAME + MODE toggle via
 *   click listeners (the proven dispatch path; onTouchEvent on a custom
 *   View is shadow-swallowed, so buttons are the lawful input surface).
 * - AI replies via a self-reposting main-looper Handler (no threads).
 */
public class GameView extends View {

    // ---- geometry --------------------------------------------------------
    static final int TICK_MS = 120;

    // ---- palette ----------------------------------------------------------
    static final int C_BG      = 0xFF0B1120;
    static final int C_PANEL   = 0xFF17223B;
    static final int C_GRID    = 0xFF3B4C6B;
    static final int C_GRID_HI = 0xFF5B719A;
    static final int C_X       = 0xFF38BDF8;
    static final int C_X_DIM   = 0xFF1E6E9E;
    static final int C_O       = 0xFFF472B6;
    static final int C_O_DIM   = 0xFF9C4672;
    static final int C_WIN     = 0xFFFACC15;
    static final int C_TEXT    = 0xFFF8FAFC;
    static final int C_SUB     = 0xFF94A3B8;
    static final int C_CELLBG  = 0xFF111B31;

    // ---- static game state -----------------------------------------------
    // board cells: 0 empty, 1 = X, 2 = O.  Index = row*3 + col.
    static int[] board = new int[9];
    static int turn = 1;              // 1 = X, 2 = O
    static int winner = 0;            // 0 none/draw undecided, 1 X, 2 O, 3 draw
    static int winA = -1, winB = -1;  // winning line endpoints (cell indices)
    static int scoreX = 0, scoreO = 0, scoreD = 0;
    static boolean vsAI = true;       // MODE: true = VS PHONE (AI plays O)
    static boolean locked = false;    // input locked (anim/AI thinking)
    static long seed = 0x51CEB00L;
    static Handler h;
    static MainActivity host;

    Paint p = new Paint();

    public GameView(Context c) {
        super(c);
        h = new Handler(Looper.getMainLooper());
    }

    // ---- deterministic app-local PRNG (LCG, glibc constants) --------------
    static int nextRnd(int bound) {
        seed = (seed * 1103515245L + 12345L) & 0x7FFFFFFFL;
        return (int) (seed % (long) bound);
    }

    // ---- game control ------------------------------------------------------
    public static void newRound() {
        for (int i = 0; i < 9; i++) board[i] = 0;
        turn = 1;
        winner = 0;
        winA = -1; winB = -1;
        locked = false;
        if (vsAI && turn == 2) scheduleAI();
    }

    public static void toggleMode() {
        vsAI = !vsAI;
        scoreX = 0; scoreO = 0; scoreD = 0;
        newRound();
        if (host != null) host.onModeChanged();
    }

    /** Cell button tap → play. Buttons are 1..9 in the layout, map to 0..8. */
    public static void playCell(int idx) {
        if (locked || winner != 0) return;
        if (idx < 0 || idx > 8 || board[idx] != 0) return;
        if (vsAI && turn == 2) return;             // AI's turn — buttons dead
        place(idx);
        maybeAI();
    }

    static void place(int idx) {
        board[idx] = turn;
        int w = winCheck();
        if (w == 1) { winner = 1; scoreX++; winLine(w); locked = true; announce(); }
        else if (w == 2) { winner = 2; scoreO++; winLine(w); locked = true; announce(); }
        else if (w == 3) { winner = 3; scoreD++; locked = true; announce(); }
        else { turn = (turn == 1) ? 2 : 1; }
    }

    static void maybeAI() {
        if (winner != 0) return;
        if (vsAI && turn == 2) scheduleAI();
    }

    static void scheduleAI() {
        locked = true;
        h.postDelayed(new Runnable() {
            public void run() { aiMove(); }
        }, 420);
    }

    static void aiMove() {
        if (winner != 0) { locked = false; return; }
        int idx = bestMove();
        board[idx] = 2;
        int w = winCheck();
        if (w == 2) { winner = 2; scoreO++; winLine(w); locked = true; announce(); return; }
        if (w == 3) { winner = 3; scoreD++; locked = true; announce(); return; }
        turn = 1;
        locked = false;
    }

    /** AI: win > block > center > corner (LCG-shuffled) > side. */
    static int bestMove() {
        // 1. immediate win
        for (int i = 0; i < 9; i++) {
            if (board[i] == 0) {
                board[i] = 2;
                boolean won = winCheck() == 2;
                board[i] = 0;
                if (won) return i;
            }
        }
        // 2. block X win
        for (int i = 0; i < 9; i++) {
            if (board[i] == 0) {
                board[i] = 1;
                boolean lost = winCheck() == 1;
                board[i] = 0;
                if (lost) return i;
            }
        }
        // 3. center
        if (board[4] == 0) return 4;
        // 4. random free corner
        int[] corners = new int[4];
        int n = 0;
        int[] ids = {0, 2, 6, 8};
        for (int k = 0; k < 4; k++) if (board[ids[k]] == 0) corners[n++] = ids[k];
        if (n > 0) return corners[nextRnd(n)];
        // 5. first free side
        int[] sides = {1, 3, 5, 7};
        for (int k = 0; k < 4; k++) if (board[sides[k]] == 0) return sides[k];
        // 6. any free
        for (int i = 0; i < 9; i++) if (board[i] == 0) return i;
        return 4;
    }

    /** 0 = game on, 1 = X wins, 2 = O wins, 3 = draw. */
    static int winCheck() {
        int[][] L = {
            {0,1,2},{3,4,5},{6,7,8},   // rows
            {0,3,6},{1,4,7},{2,5,8},   // cols
            {0,4,8},{2,4,6}            // diagonals
        };
        for (int k = 0; k < 8; k++) {
            int a = L[k][0], b = L[k][1], c = L[k][2];
            if (board[a] != 0 && board[a] == board[b] && board[b] == board[c]) {
                return board[a];
            }
        }
        boolean full = true;
        for (int i = 0; i < 9; i++) if (board[i] == 0) { full = false; break; }
        return full ? 3 : 0;
    }

    static void winLine(int w) {
        int[][] L = {
            {0,1,2},{3,4,5},{6,7,8},
            {0,3,6},{1,4,7},{2,5,8},
            {0,4,8},{2,4,6}
        };
        for (int k = 0; k < 8; k++) {
            int a = L[k][0], b = L[k][1], c = L[k][2];
            if (board[a] != 0 && board[a] == board[b] && board[b] == board[c]) {
                winA = a; winB = c;
                return;
            }
        }
    }

    static void announce() {
        if (host == null) return;
        final int w = winner;
        final int sx = scoreX, so = scoreO, sd = scoreD;
        h.postDelayed(new Runnable() {
            public void run() { host.showRound(w, sx, so, sd); }
        }, 350);
    }

    // ---- rendering ----------------------------------------------------------
    @Override
    protected void onDraw(Canvas cv) {
        int w = cv.getWidth();
        int hgt = cv.getHeight();
        p.setStyle(Paint.Style.FILL);
        cv.drawColor(C_BG);

        int pad = 30;
        int hudH = 150;
        int botH = 96;
        int bx = pad, by = hudH;
        int bw = w - 2 * pad, bh = hgt - hudH - botH;
        int cell = Math.min(bw, bh) / 3;
        int gx = bx + (bw - cell * 3) / 2;
        int gy = by + (bh - cell * 3) / 2;

        // panel
        p.setColor(C_PANEL);
        cv.drawRoundRect(gx - 22, gy - 22, gx + cell * 3 + 22, gy + cell * 3 + 22,
                         34, 34, p);

        // cells (subtle darker tiles)
        for (int r = 0; r < 3; r++) {
            for (int c = 0; c < 3; c++) {
                int idx = r * 3 + c;
                p.setColor(C_CELLBG);
                cv.drawRoundRect(gx + c * cell + 6, gy + r * cell + 6,
                                 gx + (c + 1) * cell - 6, gy + (r + 1) * cell - 6,
                                 18, 18, p);
                drawMark(cv, idx, gx + c * cell, gy + r * cell, cell, r, c);
            }
        }

        // grid lines (on top of tiles, under marks would be ideal; fine here)
        p.setStrokeWidth(7);
        p.setColor(C_GRID);
        p.setStyle(Paint.Style.STROKE);
        for (int i = 1; i <= 2; i++) {
            cv.drawLine(gx + i * cell, gy + 10, gx + i * cell, gy + cell * 3 - 10, p);
            cv.drawLine(gx + 10, gy + i * cell, gx + cell * 3 - 10, gy + i * cell, p);
        }

        // outer frame highlight
        p.setStrokeWidth(6);
        p.setColor(C_GRID_HI);
        cv.drawRoundRect(gx - 22, gy - 22, gx + cell * 3 + 22, gy + cell * 3 + 22,
                         34, 34, p);
        p.setStyle(Paint.Style.FILL);

        // winning strike
        if (winner == 1 || winner == 2) {
            if (winA >= 0 && winB >= 0) {
                float ax = gx + (winA % 3) * cell + cell / 2f;
                float ay = gy + (winA / 3) * cell + cell / 2f;
                float bxx = gx + (winB % 3) * cell + cell / 2f;
                float byy = gy + (winB / 3) * cell + cell / 2f;
                p.setStrokeWidth(14);
                p.setColor(C_WIN);
                cv.drawLine(ax, ay, bxx, byy, p);
            }
        }

        // HUD: scoreboard + turn pill
        p.setStyle(Paint.Style.FILL);
        p.setColor(C_X);
        cv.drawRoundRect(24, 34, 24 + 190, 128, 24, 24, p);
        p.setColor(C_O);
        cv.drawRoundRect(w - 24 - 190, 34, w - 24, 128, 24, 24, p);
        p.setColor(C_SUB);
        cv.drawRoundRect(w / 2 - 90, 34, w / 2 + 90, 128, 24, 24, p);

        p.setColor(0xFF0B1120);
        p.setTextSize(40);
        p.setFakeBoldText(true);
        cv.drawText("X  " + scoreX, 52, 96, p);
        cv.drawText(scoreO + "  O", w - 148, 96, p);
        p.setTextSize(34);
        cv.drawText(scoreD + " D", w / 2 - 52, 94, p);

        // status line
        p.setColor(C_TEXT);
        p.setTextSize(38);
        String st;
        if (winner == 1) st = "X WINS!";
        else if (winner == 2) st = vsAI ? "PHONE WINS!" : "O WINS!";
        else if (winner == 3) st = "DRAW!";
        else st = vsAI ? (turn == 1 ? "YOUR MOVE (X)" : "THINKING...")
                       : (turn == 1 ? "X TO MOVE" : "O TO MOVE");
        float stw = st.length() * 21.0f;
        cv.drawText(st, w / 2 - stw / 2, hgt - 34, p);
    }

    /** Draw one mark (X/O) inside the cell at (cx, cy) with size `cell`. */
    void drawMark(Canvas cv, int idx, int cx, int cy, int cell, int row, int col) {
        int v = board[idx];
        if (v == 0) return;
        float m = cell * 0.26f;             // margin
        float x0 = cx + m, y0 = cy + m;
        float x1 = cx + cell - m, y1 = cy + cell - m;
        boolean dim = (winner != 0) && !(idx == winA || idx == winB)
                      && (winner == 1 || winner == 2);
        if (v == 1) {
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(cell * 0.11f);
            p.setColor(dim ? C_X_DIM : C_X);
            float r = cell * 0.055f;
            // stroke 1 (rounded joins via small circles at the ends)
            cv.drawLine(x0, y0, x1, y1, p);
            cv.drawLine(x1, y0, x0, y1, p);
            cv.drawCircle(x0, y0, r, p);
            cv.drawCircle(x1, y0, r, p);
            cv.drawCircle(x0, y1, r, p);
            cv.drawCircle(x1, y1, r, p);
        } else {
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(cell * 0.11f);
            p.setColor(dim ? C_O_DIM : C_O);
            float cxm = cx + cell / 2f, cym = cy + cell / 2f;
            float rad = cell * 0.30f;
            cv.drawCircle(cxm, cym, rad, p);
        }
        p.setStyle(Paint.Style.FILL);
    }
}
