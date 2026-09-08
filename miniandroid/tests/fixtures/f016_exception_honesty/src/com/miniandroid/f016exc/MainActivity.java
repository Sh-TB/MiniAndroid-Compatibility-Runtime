package com.miniandroid.f016exc;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

/**
 * F016 exception-honesty fixture (M3 FINDING-016, ROADMAP family G).
 *
 * REAL DEX bytecode throws an uncaught exception through a three-deep
 * call chain: onCreate → chainA → chainB → chainC(throws). No frame in
 * the app declares a try/catch, so per ART the exception escapes the
 * outermost app frame and the process dies.
 *
 * Laws proven by the battery stage:
 *  1. The exception is REAL app bytecode (athrow of
 *     java.lang.IllegalStateException("F016-UNCAUGHT") — message visible
 *     in the [EXCEPTION] traces and crash.log), not a runtime synthetic.
 *  2. Dalvik unwind law: every handler-less frame unwinds (mid-stack
 *     "unwind continues"), instead of the old FRAME-2 "caller continues".
 *  3. Exception-honesty law (default mode): the run must NOT report plain
 *     SUCCESS — status downgrades to PARTIAL with the in-flight count and
 *     a crash.log entry.
 *  4. ART process-death law (strict mode, MINIANDROID_EXC_STRICT=1): the
 *     run CRASHes with a nonzero exit code.
 *
 * The TextView is set BEFORE the throw so the pre-throw visual state is
 * observable in frames (state-before-death).
 */
public class MainActivity extends Activity {

    private TextView tvState;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        tvState = (TextView) findViewById(R.id.tv_state);
        tvState.setText("F016 armed");
        chainA(41);
        // Unreachable in ART: the process died in chainC.
        tvState.setText("F016 survived");
    }

    private void chainA(int x) {
        chainB(x + 1);
    }

    private void chainB(int x) {
        chainC(x + 1);
    }

    private void chainC(int x) {
        if (x == 43) {
            throw new IllegalStateException("F016-UNCAUGHT x=" + x);
        }
        tvState.setText("F016 no-throw x=" + x);
    }
}
