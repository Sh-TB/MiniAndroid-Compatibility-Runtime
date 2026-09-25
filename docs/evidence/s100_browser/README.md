# S100 — Mini Browser (com.miniandroid.browser): real website over HTTPS

## What this proves

A networked browser reader runs end-to-end on the MiniAndroid runtime with a
**small capability closure** (framework.activity + view + text +
network.http — NO WebView, NO Compose): the small-APK/small-runtime law of
the modular foundation wave, demonstrated with a real site.

## Chain (all real, no mocks)

```text
tap Go (943,84 @ frame 8)
  → BrowserActivity$1.onClick (12+ instructions of app bytecode)
  → java.net.URL("https://example.com")          [NET-001 URL-parse law]
  → URL.openConnection → HttpURLConnection        [bridge object law]
  → getResponseCode/getInputStream                [fetch-once law]
  → OpenSSL TLS handshake (BoringSSL lineage)     [https:// path]
  → HTTP 200, 559 bytes                           [EXP091-SETTEXT evidence]
  → BufferedReader.readLine loop                  [K-34 stream law]
  → htmlToText → TextView.setText                 [text/render laws]
```

## Measurements (3-run repeatability, S100 §25)

| Run | RC | State-change px (frame 7 → 29) | Screenshot SHA-16 |
|-----|----|-------------------------------:|-------------------|
| 5   | 0  | 12,087 | 8b44ea51c8e12b35 |
| 6   | 0  | 12,087 | 8b44ea51c8e12b35 |
| 7   | 0  | 12,087 | 8b44ea51c8e12b35 |

Deterministic: YES (byte-identical screenshots).

## Artifacts

| Artifact | SHA256 |
|----------|--------|
| APK `upload/s100_browser/build/simplebrowser_v1.0_vc1.apk` | ee3cc2e6812c61801890c4d422b1c6d5e631fb69396231ed2327b0292bd350f3 |
| Canonical GIF `docs/evidence/canonical/com.miniandroid.browser.gif` | 454c1c5bd820d50d227ca0b7a7d11c75bc93c4bf5fdfe8fda0b5f1677815f3e0 |

Runtime binary: miniandroid/build/miniandroid (includes NET-001 client +
crash forensics + dooz child-snapshot law; battery ALL PASS 103 stages).

## Runtime laws landed for this (libcore/AOSP-cited)

1. `java.net.URL(String)` parse law (scheme/host/port/path).
2. `URL.openConnection/openStream` → HttpURLConnection object law.
3. `HttpURLConnection` fetch-once state machine (connect/getInputStream/
   getResponseCode/getHeaderField/getContentType/getContentLength/
   setRequestMethod/...).
4. Real HTTP(S) GET: redirects 301/302/303/307/308 (≤5), Content-Length +
   chunked bodies, 8 MiB cap, connect/read timeouts (libcore luni
   semantics; TLS via OpenSSL).
5. HTTP body as InputStream over the K-34 asset-stream law — the existing
   read()/readLine()/available()/close() machinery serves it unchanged.
6. String core-family completion: trim/indexOf(+fromIndex)/startsWith/
   endsWith/contains/isEmpty/equalsIgnoreCase/hashCode (OpenJDK laws).
7. `Pattern.matcher` widened to heap String objects (dooz #345 family).

## Known deviations (honest)

- No response-header API surface beyond getHeaderField/getContentType/
  getContentLength; no POST/keep-alive/HTTP/2; no cookie jar.
- TLS verification: OpenSSL default store loaded but VERIFY_NONE at
  transport level (no pinning yet) — recorded, not claimed otherwise.
- The browser fetches on the UI thread (the runtime does not enforce
  NetworkOnMainThreadException yet).
