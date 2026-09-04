package oracle;

import android.app.Activity;
import android.content.Context;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.shadows.ShadowLog;

import java.lang.reflect.Method;

/**
 * EXP-095 §22: Robolectric as a framework ORACLE for the MiniAndroid
 * compatibility runtime. This test reproduces the EXACT Telegram SmsView
 * layout structure (LoginActivity.java, LoginActivitySmsView.<init>)
 * and records the REAL Android measure/layout results for comparison
 * with MiniAndroid's layout engine (CM-019).
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 34)
public class SmsLayoutOracleTest {

    static final int SCREEN_W = 1080;
    static final int SCREEN_H = 1920;

    private void dump(String tag, View v) {
        System.out.printf("ORACLE %-14s %-28s pos=(%d,%d) size=%dx%d%n",
                tag, v.getClass().getSimpleName(),
                v.getLeft(), v.getTop(), v.getWidth(), v.getHeight());
    }

    private void dumpText(String tag, TextView v) {
        System.out.printf("ORACLE %-14s text=\"%s\" pos=(%d,%d) size=%dx%d%n",
                tag, v.getText(),
                v.getLeft(), v.getTop(), v.getWidth(), v.getHeight());
    }

    @Test
    public void smsScreenLayout() {
        ShadowLog.stream = System.out;
        Activity act = Robolectric.setupActivity(Activity.class);
        Context ctx = act.getApplicationContext();

        // Density in Robolectric default (mdpi, 160dpi) = 1.0 — same as
        // MiniAndroid's reported density.
        float density = ctx.getResources().getDisplayMetrics().density;
        System.out.printf("ORACLE density=%s width=%d height=%d%n",
                density,
                ctx.getResources().getDisplayMetrics().widthPixels,
                ctx.getResources().getDisplayMetrics().heightPixels);

        // == Reproduce LoginActivitySmsView (VERTICAL LinearLayout) ==
        LinearLayout smsView = new LinearLayout(ctx);
        smsView.setOrientation(LinearLayout.VERTICAL);
        smsView.setLayoutParams(new ViewGroup.LayoutParams(SCREEN_W, SCREEN_H));

        // 1) icon area: FrameLayout 64x64, createFrame(64, 64) → margins 0
        FrameLayout iconFrame = new FrameLayout(ctx);
        iconFrame.addView(new View(ctx), new FrameLayout.LayoutParams(64, 64));
        smsView.addView(iconFrame, new LinearLayout.LayoutParams(64, 64));

        // 2) title: createLinear(WRAP, WRAP, CENTER_HORIZONTAL|TOP, 0, 18, 0, 0)
        TextView title = new TextView(ctx);
        title.setText("Enter code");
        smsView.addView(title, lp(LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER_HORIZONTAL | Gravity.TOP, 0, 18, 0, 0));

        // 3) description: createLinear(WRAP, WRAP, CENTER_HORIZONTAL|TOP, side, 17, side, 0)
        TextView desc = new TextView(ctx);
        desc.setText("We’ve sent an SMS with an activation code to your phone +1 5551234567.");
        smsView.addView(desc, lp(LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER_HORIZONTAL | Gravity.TOP, 24, 17, 24, 0));

        // 4) code field container: createLinear(WRAP, 42, CENTER_HORIZONTAL, 0, 32, 0, 0)
        //    — a HORIZONTAL LinearLayout with 5 EditText-sized boxes (34x42)
        LinearLayout codeRow = new LinearLayout(ctx);
        codeRow.setOrientation(LinearLayout.HORIZONTAL);
        for (int i = 0; i < 5; i++) {
            View field = new View(ctx);
            LinearLayout.LayoutParams flp = new LinearLayout.LayoutParams(34, 42);
            flp.rightMargin = 7;
            codeRow.addView(field, flp);
        }
        smsView.addView(codeRow, lp(LinearLayout.LayoutParams.WRAP_CONTENT, 42,
                Gravity.CENTER_HORIZONTAL, 0, 32, 0, 0));

        // 5) bottom link
        TextView link = new TextView(ctx);
        link.setText("Didn't get the code?");
        smsView.addView(link, lp(LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER_HORIZONTAL | Gravity.TOP, 0, 28, 0, 0));

        // == Robolectric default screen is 320x470; force 1080x1920 via
        // explicit measure/layout at target size (same as our renderer). ==
        act.setContentView(smsView);
        smsView.measure(
                View.MeasureSpec.makeMeasureSpec(SCREEN_W, View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(SCREEN_H, View.MeasureSpec.EXACTLY));
        smsView.layout(0, 0, SCREEN_W, SCREEN_H);

        System.out.println("== ROBOLECTRIC (AOSP android-all) LAYOUT RESULTS ==");
        dump("root", smsView);
        dump("iconFrame", iconFrame);
        dumpText("title", title);
        dumpText("desc", desc);
        dump("codeRow", codeRow);
        for (int i = 0; i < codeRow.getChildCount(); i++) {
            dump("  field" + i, codeRow.getChildAt(i));
        }
        dumpText("link", link);

        // == Semantic API comparisons (AOSP vs MiniAndroid) ==
        System.out.println("== GRAVITY CONSTANTS ==");
        System.out.printf("ORACLE Gravity.CENTER_HORIZONTAL=0x%x CENTER=0x%x TOP=0x%x BOTTOM=0x%x LEFT=0x%x RIGHT=0x%x CENTER_VERTICAL=0x%x%n",
                Gravity.CENTER_HORIZONTAL, Gravity.CENTER, Gravity.TOP,
                Gravity.BOTTOM, Gravity.LEFT, Gravity.RIGHT, Gravity.CENTER_VERTICAL);

        System.out.println("== MATCH_PARENT / WRAP_CONTENT ==");
        System.out.printf("ORACLE MATCH_PARENT=%d WRAP_CONTENT=%d (expect -1/-2)%n",
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);

        System.out.println("== TextView.setText/getText identity ==");
        TextView tv = new TextView(ctx);
        String in = "We’ve sent an SMS with an activation code to your phone +1 5551234567.";
        tv.setText(in);
        CharSequence out = tv.getText();
        System.out.printf("ORACLE getText() == same object: %b, equals: %b%n",
                out == in, in.contentEquals(out));

        System.out.println("== String.replace(char,char) nbsp semantics ==");
        String nbsped = "+1 5551234567".replace(' ', '\u00A0');
        System.out.printf("ORACLE replace(' ', U+00A0) = \"%s\" codepoints=%d%n",
                nbsped.replace('\u00A0', '~'), nbsped.codePointCount(0, nbsped.length()));

        System.out.println("== LinearLayout.LayoutParams defaults ==");
        LinearLayout.LayoutParams def = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        System.out.printf("ORACLE default margins=(%d,%d,%d,%d) gravity=%d%n",
                def.leftMargin, def.topMargin, def.rightMargin, def.bottomMargin,
                def.gravity);

        System.out.println("== TextView default text color (unstyled) ==");
        System.out.printf("ORACLE default TextView text color set: %b%n",
                title.getTextColors().getDefaultColor() != 0);
    }

    private static LinearLayout.LayoutParams lp(int w, int h, int gravity,
                                               int l, int t, int r, int b) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(w, h);
        p.gravity = gravity;
        p.setMargins(l, t, r, b);
        return p;
    }
}
