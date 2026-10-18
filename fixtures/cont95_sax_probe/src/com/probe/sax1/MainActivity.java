package com.probe.sax1;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;

import org.xml.sax.Attributes;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import org.xml.sax.XMLReader;
import org.xml.sax.helpers.DefaultHandler;

import java.io.InputStream;

import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;

/**
 * F-NEW-397 probe (CONT-95): a stream-backed InputSource parsed through
 * SAXParser/XMLReader must deliver the app's OWN ContentHandler the document's
 * REAL events (AOSP javax.xml.parsers + org.xml.sax law).
 *
 * Pre-fix ground truth: XMLReader.parse resolved stream bytes from a registry
 * NO site ever populated -> 0 events reached the handler (Telegram SvgHelper
 * casualty: pattern bitmap 0x0 -> createBitmap(0,0) IAE -> onCreate death).
 */
public class MainActivity extends Activity {
    private static final String TAG = "SAX1PROBE";

    private static int sStart = 0;
    private static int sEnd = 0;
    private static String sRootW = "?";
    private static String sRootH = "?";
    private static String sParseErr = "";
    private static final StringBuilder sNames = new StringBuilder();

    private static class CountingHandler extends DefaultHandler {
        @Override
        public void startElement(String uri, String localName, String qName,
                                 Attributes attributes) throws SAXException {
            sStart++;
            sNames.append(qName).append(',');
            if (sStart == 1) {
                sRootW = attributes.getValue("width");
                sRootH = attributes.getValue("height");
            }
            super.startElement(uri, localName, qName, attributes);
        }

        @Override
        public void endElement(String uri, String localName, String qName)
                throws SAXException {
            sEnd++;
            super.endElement(uri, localName, qName);
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            SAXParserFactory f = SAXParserFactory.newInstance();
            SAXParser p = f.newSAXParser();
            XMLReader xr = p.getXMLReader();
            xr.setContentHandler(new CountingHandler());
            InputStream is = getResources().openRawResource(
                    com.probe.sax1.R.raw.probe);
            xr.parse(new InputSource(is));
        } catch (Throwable t) {
            sParseErr = t.getClass().getSimpleName() + ":" + t.getMessage();
        }
        // Expected: 6 startElements (svg, g, path, path, rect, circle) and 6
        // endElements; root attrs width=1080 height=1920.
        boolean ok = (sStart == 6) && (sEnd == 6)
                && "1080".equals(sRootW) && "1920".equals(sRootH)
                && sParseErr.isEmpty();
        Log.i(TAG, "[SAX1] events=" + sStart + "/" + sEnd
                + " root=" + sRootW + "x" + sRootH
                + " names=" + sNames
                + " err=" + (sParseErr.isEmpty() ? "none" : sParseErr)
                + " verdict=" + (ok ? "PASS" : "FAIL"));
    }
}
