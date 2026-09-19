# FOUNDATION_RESOURCE_MATRIX — canonical (S67)

Verified via f31 (string/color refs), f32 (dimen API), f01/f03 (hex colors),
f27 (multi-layout), plus S65/S66 corpus cross-validation.

| Contract | Status | Evidence / Law |
|---|---|---|
| AXML string/int/bool/dim/color typed values | PROVEN | census file:line + fixtures |
| match_parent(-1)/wrap_content(-2) sentinels | PROVEN | INT_DEC-before-string law |
| gravity/orientation/visibility enums | PROVEN (S67 F-124 fix) | visibility attr space {0,1,2}→View {0,4,8}; was raw passthrough |
| @string/@color/@dimen/@drawable refs | PROVEN | f31 bg + text resolve |
| @style refs + style parent chain | PROVEN | bag_parent + apply_style loop |
| style="@style/Foo" on views | PROVEN | typed-ref + raw-string branches |
| attrs-from-theme (obtainStyledAttributes) | PROVEN | theme bag_value path |
| ?attr/ in layouts at inflate | MISSING (A1) | no theme-attr branch; mis-queried as resid |
| @android: framework resources | MISSING (B12) | no framework ARSC loaded |
| View-level android:theme | MISSING (B11) | not implemented |
| getDimensionPixelSize density law | PROVEN (S67 A2 fix) | f32: 100dp→263px exact ((int)(262.5+0.5), AOSP); was args[0]-this bug + unconverted seed |
| getDimensionPixelSize fallback | PARTIAL | 24px default still silent on unresolved (A8, now loud-logged) |
| Resources.getColor | PROVEN | ARSC-first + name-map fallback |
| Resources.getDrawable | PROVEN | canonical select_file |
| Resources.getString/Context.getString | PROVEN | f31 API path |
| getIdentifier | PARTIAL (C10) | real id resolution vs legacy stub dual-path |
| Theme.getColor | WRONG (A10) | stub 0xFF000000 |
| Theme.resolveAttribute | MISSING (A10) | not implemented |
| Resources.getSystem | MISSING (A10) | not implemented |
| fraction TypedValue | MISSING (C11) | dead code, no consumers |
| fontScale (sp) | PARTIAL (C12) | fixed 1.0 |
| Manifest label via resources | MISSING (A7) | REFERENCE→"@0x…" literal |
| Manifest icon | MISSING (A7) | not parsed |
| drawable density variants | PROVEN | select_file config law + intrinsic scaling |
