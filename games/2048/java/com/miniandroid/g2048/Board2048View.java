package com.miniandroid.g2048;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;

/**
 * 2048 game board — classic mechanics: 4x4 grid, tiles slide and merge,
 * +2/+4 spawn after every move, game over when no move is legal.
 * Static state (runtime law); renders via real Canvas.onDraw with the
 * classic per-value palette.
 */
public class Board2048View extends View {

    static final int N = 4;
    static final int C_BG     = 0xFFFAF8EF;
    static final int C_BOARD  = 0xFFBBADA0;
    static final int C_EMPTY  = 0xFFCDC1B4;
    static final int C_DIM    = 0xFF776E65;

    // classic 2048 tile palette (value -> bg color, fg color)
    static final int[] TILE_BG = {
        0xFFEEE4DA, // 2
        0xFFEDE0C8, // 4
        0xFFF2B179, // 8
        0xFFF59563, // 16
        0xFFF67C5F, // 32
        0xFFF65E3B, // 64
        0xFFEDCF72, // 128
        0xFFEDCC61, // 256
        0xFFEDC850, // 512
        0xFFEDC53F, // 1024
        0xFFEDC22E, // 2048
    };
    static final int[] TILE_FG = {
        0xFF776E65, 0xFF776E65, 0xFFF9F6F2, 0xFFF9F6F2, 0xFFF9F6F2,
        0xFFF9F6F2, 0xFFF9F6F2, 0xFFF9F6F2, 0xFFF9F6F2, 0xFFF9F6F2,
        0xFFF9F6F2,
    };

    static int[][] board = new int[N][N];   // tile values (0 = empty)
    static int score = 0;
    static boolean over = false;
    static boolean moved = false;           // did the last move change board
    static long seed = 0xC0FFEE11L;

    Paint p = new Paint();

    public Board2048View(Context c) {
        super(c);
        spawn();
        spawn();
    }

    static int nextRnd(int bound) {
        seed = (seed * 1103515245L + 12345L) & 0x7FFFFFFFL;
        return (int) (seed % (long) bound);
    }

    static void spawn() {
        int empty = 0;
        for (int r = 0; r < N; r++) for (int c = 0; c < N; c++) if (board[r][c] == 0) empty++;
        if (empty == 0) return;
        int pick = nextRnd(empty);
        int val = nextRnd(10) < 9 ? 2 : 4;
        int seen = 0;
        for (int r = 0; r < N; r++) {
            for (int c = 0; c < N; c++) {
                if (board[r][c] == 0) {
                    if (seen == pick) { board[r][c] = val; return; }
                    seen++;
                }
            }
        }
    }

    /** dir: 0=left, 1=up, 2=right, 3=down */
    public static void move(int dir) {
        if (over) return;
        moved = false;
        int n = N;
        for (int i = 0; i < n; i++) {
            int[] line = new int[n];
            for (int j = 0; j < n; j++) {
                if (dir == 0) line[j] = board[i][j];
                else if (dir == 2) line[j] = board[i][n - 1 - j];
                else if (dir == 1) line[j] = board[j][i];
                else line[j] = board[n - 1 - j][i];
            }
            int[] merged = mergeLine(line);
            for (int j = 0; j < n; j++) {
                if (dir == 0) board[i][j] = merged[j];
                else if (dir == 2) board[i][n - 1 - j] = merged[j];
                else if (dir == 1) board[j][i] = merged[j];
                else board[n - 1 - j][i] = merged[j];
            }
        }
        if (moved) spawn();
        if (!canMove()) over = true;
    }

    static int[] mergeLine(int[] line) {
        int[] out = new int[N];
        int pos = 0;
        int j = 0;
        while (j < N) {
            if (line[j] == 0) { j++; continue; }
            if (j + 1 < N && line[j] == line[j + 1]) {
                out[pos++] = line[j] * 2;
                score += line[j] * 2;
                moved = true;
                j += 2;
            } else {
                out[pos++] = line[j];
                moved = moved || out[pos - 1] != line[j] || pos - 1 != j;
                j++;
            }
        }
        // detect pure slide (no merge): any nonzero tile moved?
        for (int k = 0, jj = 0; jj < N; jj++) {
            if (line[jj] != 0) {
                if (k != jj) moved = true;
                k++;
            }
        }
        return out;
    }

    static boolean canMove() {
        for (int r = 0; r < N; r++) for (int c = 0; c < N; c++) {
            if (board[r][c] == 0) return true;
            if (c + 1 < N && board[r][c] == board[r][c + 1]) return true;
            if (r + 1 < N && board[r][c] == board[r + 1][c]) return true;
        }
        return false;
    }

    @Override
    protected void onDraw(Canvas cv) {
        int w = cv.getWidth();
        int h = cv.getHeight();
        cv.drawColor(C_BG);

        int pad = 30;
        int gap = 14;
        int boardW = w - 2 * pad;
        int cell = (boardW - 3 * gap) / N;
        int cellH = cell;
        int boardH = 4 * cell + 3 * gap;
        int boardTop = Math.max(140, (h - boardH - 40) / 2);

        // score header
        p.setStyle(Paint.Style.FILL);
        p.setColor(C_DIM);
        p.setTextSize(56);
        p.setFakeBoldText(true);
        cv.drawText("SCORE " + score, pad, 100, p);

        // board base
        p.setColor(C_BOARD);
        cv.drawRoundRect(pad - 10, boardTop - 10, pad + boardW + 10,
                         boardTop + boardH + 10, 22, 22, p);
        // empty cells
        p.setColor(C_EMPTY);
        for (int r = 0; r < N; r++) {
            for (int c = 0; c < N; c++) {
                float x = pad + c * (cell + gap);
                float y = boardTop + r * (cell + gap);
                cv.drawRoundRect(x, y, x + cell, y + cell, 14, 14, p);
            }
        }
        // tiles
        for (int r = 0; r < N; r++) {
            for (int c = 0; c < N; c++) {
                int v = board[r][c];
                if (v == 0) continue;
                float x = pad + c * (cell + gap);
                float y = boardTop + r * (cell + gap);
                int idx = Math.min(v, 2048);
                int li = Integer.numberOfTrailingZeros(idx) - 1;
                li = Math.max(0, Math.min(li, TILE_BG.length - 1));
                p.setColor(TILE_BG[li]);
                cv.drawRoundRect(x, y, x + cell, y + cell, 14, 14, p);
                p.setColor(TILE_FG[li]);
                float ts = v < 100 ? cell * 0.45f : v < 1000 ? cell * 0.38f : cell * 0.3f;
                p.setTextSize(ts);
                p.setFakeBoldText(true);
                String s = String.valueOf(v);
                float tw = s.length() * ts * 0.62f;
                cv.drawText(s, x + (cell - tw) / 2, y + cell / 2 + ts * 0.34f, p);
            }
        }

        if (over) {
            p.setColor(C_DIM);
            p.setTextSize(46);
            p.setFakeBoldText(false);
            cv.drawText("GAME OVER — NO MOVES LEFT", pad, boardTop + boardH + 80, p);
        }
    }
}
