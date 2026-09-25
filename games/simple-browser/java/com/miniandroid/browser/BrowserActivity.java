package com.miniandroid.browser;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * S100 — MiniAndroid simple browser: loads a REAL website over HTTP(S)
 * through java.net.URL + HttpURLConnection + BufferedReader, then renders
 * the HTML stripped to readable text in a TextView.
 *
 * Deviation note (honest, documented): the fetch runs on the UI thread.
 * Real Android throws NetworkOnMainThreadException; the runtime does not
 * enforce that law yet (filed as a frontier note in the S100 report).
 * WebView is deliberately NOT used — the small-app/small-runtime law.
 */
public class BrowserActivity extends Activity {

    private EditText urlField;
    private TextView pageView;
    private Button goButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        urlField = (EditText) findViewById(R.id.url_field);
        pageView = (TextView) findViewById(R.id.page_view);
        goButton = (Button) findViewById(R.id.go_button);

        goButton.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                String target = urlField.getText().toString().trim();
                if (target.length() == 0) {
                    pageView.setText("ERROR: empty URL");
                    return;
                }
                if (target.indexOf("://") < 0) {
                    target = "https://" + target;
                }
                pageView.setText("Loading " + target + " ...");
                String html = fetch(target);
                if (html == null) {
                    pageView.setText("LOAD FAILED: " + target);
                } else {
                    String text = htmlToText(html);
                    if (text.length() > 6000) {
                        text = text.substring(0, 6000) + "\n... [truncated]";
                    }
                    pageView.setText(text);
                }
            }
        });
    }

    /** Real HTTP(S) GET through the java.net stack (libcore semantics). */
    private String fetch(String target) {
        try {
            URL url = new URL(target);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(15000);
            conn.setReadTimeout(15000);
            int code = conn.getResponseCode();
            InputStream is = conn.getInputStream();
            BufferedReader br = new BufferedReader(new InputStreamReader(is));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line);
                sb.append('\n');
                if (sb.length() > 200000) break;   // hard bound
            }
            br.close();
            return "HTTP " + code + " (" + conn.getContentLength() + " bytes)\n\n"
                    + sb.toString();
        } catch (Throwable t) {
            return null;
        }
    }

    /** Minimal HTML-to-text: strip tags + decode a few entities + squeeze. */
    private static String htmlToText(String html) {
        StringBuilder out = new StringBuilder(html.length());
        int i = 0;
        boolean inTag = false;
        while (i < html.length()) {
            char c = html.charAt(i);
            if (inTag) {
                if (c == '>') inTag = false;
            } else if (c == '<') {
                // capture tag name to inject separators for block tags
                int end = html.indexOf('>', i);
                if (end < 0) break;
                String tag = html.substring(i + 1, Math.min(end, i + 12));
                String low = tag.toLowerCase();
                if (low.startsWith("p") || low.startsWith("br")
                        || low.startsWith("div") || low.startsWith("h1")
                        || low.startsWith("h2") || low.startsWith("h3")
                        || low.startsWith("li") || low.startsWith("tr")) {
                    out.append('\n');
                }
                inTag = true;
                i = end;
            } else if (c == '&') {
                if (html.startsWith("&amp;", i)) { out.append('&'); i += 4; }
                else if (html.startsWith("&lt;", i)) { out.append('<'); i += 3; }
                else if (html.startsWith("&gt;", i)) { out.append('>'); i += 3; }
                else if (html.startsWith("&quot;", i)) { out.append('"'); i += 5; }
                else if (html.startsWith("&#39;", i)) { out.append('\''); i += 4; }
                else if (html.startsWith("&nbsp;", i)) { out.append(' '); i += 5; }
                else out.append(c);
            } else {
                out.append(c);
            }
            i++;
        }
        // squeeze blank lines + spaces
        StringBuilder slim = new StringBuilder(out.length());
        boolean lastSpace = false, atLineStart = true;
        for (int j = 0; j < out.length(); j++) {
            char c = out.charAt(j);
            if (c == ' ' || c == '\t') {
                if (!lastSpace && !atLineStart) slim.append(' ');
                lastSpace = true;
            } else if (c == '\n') {
                if (!atLineStart) slim.append('\n');
                atLineStart = true;
                lastSpace = false;
            } else {
                slim.append(c);
                lastSpace = false;
                atLineStart = false;
            }
        }
        return slim.toString();
    }
}
