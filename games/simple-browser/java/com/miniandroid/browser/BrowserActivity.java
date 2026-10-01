package com.miniandroid.browser;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebView;
import android.widget.Button;
import android.widget.EditText;

/**
 * S133 VC2 — Mini Browser full-page render: the URL bar drives
 * android.webkit.WebView.loadUrl; the runtime's WebView engine parses the
 * fetched document into a live DOM, applies CSS, executes JS (QuickJS),
 * lays out and paints the page into the framebuffer (WEB-001 law).
 *
 * Same app identity as the S100 VC1 text-reader (com.miniandroid.browser):
 * VC2 is the capability upgrade, not a new browser.
 *
 * Deviation note (honest, inherited from VC1): the load runs on the UI
 * thread; real Android throws NetworkOnMainThreadException — the runtime
 * does not enforce that law yet (S100 report frontier note).
 */
public class BrowserActivity extends Activity {

    private EditText urlField;
    private WebView webView;
    private Button goButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        urlField = (EditText) findViewById(R.id.url_field);
        webView = (WebView) findViewById(R.id.webview);
        goButton = (Button) findViewById(R.id.go_button);

        goButton.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                navigate();
            }
        });
    }

    /** Canonical navigation law: normalize the scheme, then loadUrl. */
    private void navigate() {
        String target = urlField.getText().toString().trim();
        if (target.length() == 0) {
            return;
        }
        if (target.indexOf("://") < 0) {
            target = "https://" + target;
        }
        webView.loadUrl(target);
    }
}
