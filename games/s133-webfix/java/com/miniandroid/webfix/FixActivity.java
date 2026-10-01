package com.miniandroid.webfix;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebView;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * S133 §22 CONTROL HARNESS — 14 capability-isolating pages, one WebView.
 *
 * Every button loads file:///android_asset/TEST-xx.html into the SAME
 * engine pipeline a live load uses (load_document → DOM/CSS/JS → layout →
 * paint → blit → framebuffer). Content is byte-deterministic; the render
 * signature of each page is a distinct color block set, so the screenshot
 * forensics alone identify which capability rendered.
 *
 * Flow: tap TEST-xx button → WebView.loadUrl → engine renders below.
 * The loadUrl of the ASSET law (S101/S109) is the control path; WEB-001
 * (network) is proven separately by the browser APK against localhost/z.ai.
 */
public class FixActivity extends Activity {

    private static final String[][] TESTS = {
        {"T01", "plain HTML"},
        {"T02", "CSS colors"},
        {"T03", "CSS layout"},
        {"T04", "text"},
        {"T05", "image"},
        {"T06", "SVG"},
        {"T07", "font"},
        {"T08", "JS mutation"},
        {"T09", "canvas"},
        {"T10", "scroll"},
        {"T11", "clip"},
        {"T12", "transform"},
        {"T13", "opacity"},
        {"T14", "large page"},
        {"T15", "module"},
        {"T16", "dyn import"},
        {"T17", "allSettled"},
    };

    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        webView = (WebView) findViewById(R.id.webview);

        LinearLayout list = (LinearLayout) findViewById(R.id.menu_list);
        // 7 rows x 2 buttons: compact menu strip
        for (int row = 0; row < 9; row++) {
            LinearLayout line = new LinearLayout(this);
            line.setOrientation(LinearLayout.HORIZONTAL);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT);
            line.setLayoutParams(lp);
            for (int col = 0; col < 2; col++) {
                final int idx = row * 2 + col;
                if (idx >= TESTS.length) break;
                Button b = new Button(this);
                b.setText(TESTS[idx][0] + " " + TESTS[idx][1]);
                b.setTextSize(11f);
                LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(
                        0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
                b.setLayoutParams(blp);
                b.setOnClickListener(new View.OnClickListener() {
                    public void onClick(View v) {
                        String page = TESTS[idx][0].replace("T", "TEST-") + ".html";
                        webView.loadUrl("file:///android_asset/" + page);
                    }
                });
                line.addView(b);
            }
            list.addView(line);
        }
        TextView hint = new TextView(this);
        hint.setText("Tap a test to load it into the WebView");
        hint.setTextSize(12f);
        list.addView(hint);
    }
}
