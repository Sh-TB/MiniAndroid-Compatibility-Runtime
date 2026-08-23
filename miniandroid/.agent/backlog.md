# EXP-067 Backlog

Live list of blockers and TODOs. Update continuously.

## Active blockers (ranked by impact)

1. **Resource table semantics incomplete** — only strings/dimens/colors partially resolve; drawable/integer/boolean/style/theme/reference/array/plurals not implemented
2. **No real measure/layout engine** — renderer uses heuristic positioning; no MATCH_PARENT/WRAP_CONTENT/weight/margin semantics
3. **No AXML parser** — cannot inflate layouts from XML; Telegram uses programmatic Views but generic APKs need XML
4. **No generic LayoutInflater** — setContentView(R.layout.foo) doesn't work
5. **No drawable decoding** — ImageView placeholders are gray rectangles
6. **No real color resolution** — Resources.getColor returns default black
7. **View inheritance not tracked** — anonymous subclasses (PhoneView$1/$3) recognized by name pattern only
8. **No input system** — can't dispatch_text_input/click to EditText
9. **No click listener dispatch** — setOnClickListener captures but dispatchClick doesn't execute the callback
10. **No exception engine** — DEX try/catch handlers not implemented
11. **No reflection layer** — Class.forName/getMethod not implemented
12. **No SQLite** — only SharedPreferences
13. **No JNI/loadLibrary** — native methods all stubbed
14. **No Java networking** — Socket/HttpURLConnection not implemented

## Done (carried over from EXP-066)

- Multi-DEX const-string bug fixed (EXP-065)
- Multi-DEX const-class/check-cast/instance-of fixed (EXP-066)
- OutlineTextContainerView.setText capture (EXP-066)
- Phone number + Country labels visible (EXP-066)
