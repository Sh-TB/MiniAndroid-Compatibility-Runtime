package c7.w12;

/** CODER7 WAVE-12 — the conformance-battery recorder (the same law as
 *  the WAVE-9/10/11 Rec: statics survive the whole run; String.concat,
 *  no StringBuilder; flush() APPENDS so every row lands verbatim). */
public class Rec {
    public static String out = "";
    public static int flushes = 0;

    public static void line(String op, String verdict, String d) {
        String row = "C7W12|".concat(op).concat("|").concat(verdict)
                .concat("|").concat(d == null ? "null" : d)
                .concat("\n");
        out = out.concat(row);
    }

    public static void ok(String op, String d) { line(op, "PASS", d); }
    public static void bad(String op, String d) { line(op, "FAIL", d); }

    public static void flush(android.content.Context ctx, String name) {
        try {
            java.io.FileOutputStream fos = ctx.openFileOutput(
                name, android.content.Context.MODE_APPEND);
            fos.write(out.getBytes("UTF-8"));
            fos.close();
            flushes++;
            out = "";
        } catch (Throwable t) {
            // No silent fabrication: a failed flush leaves the file short
            // and the verdicts honestly absent.
        }
    }
}
