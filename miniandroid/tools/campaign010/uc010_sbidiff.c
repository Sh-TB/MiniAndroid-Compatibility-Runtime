/* CAMPAIGN 010 R4 — bidi differential: FriBidi vs SheenBidi on the
   Persian §14 proof strings (Arabic-script RTL + digits + mixed Latin). */
#include <stdio.h>
#include <string.h>
#include <fribidi.h>
#include <SheenBidi/SBAlgorithm.h>
#include <SheenBidi/SBParagraph.h>
#include <SheenBidi/SBLine.h>

static void hexdump(const unsigned int* lv, int n, char* out) {
    for (int i = 0; i < n; i++) out += sprintf(out, "%d,", (int)lv[i]);
    *out = 0;
}

int main(void) {
    const char* cases[] = {
        "سلام دنیا",                 /* pure Persian */
        "Hello سلام",                /* mixed LTR+RTL */
        "نسخه ۱۲.۱۰.۱",             /* Persian + Eastern digits */
        "سلام Telegram دنیا",        /* RTL embed LTR embed RTL */
    };
    for (int c = 0; c < 4; c++) {
        const char* s = cases[c];
        int len = strlen(s);
        FriBidiChar fb_in[64], fb_par[64];
        FriBidiCharType base = FRIBIDI_PAR_ON;
        int n = fribidi_charset_to_unicode(FRIBIDI_CHARSET_UTF8, s, len, fb_in);
        FriBidiLevel fb_levels[64];
        fribidi_get_par_embedding_levels(fb_in, n, &base, fb_levels);

        SBUCodepointMap map = {0, NULL};
        SBAlgorithm* alg = SBAlgorithmCreate((SBUCodepoint*)fb_in, n, &map);
        SBParagraph* par = SBAlgorithmCreateParagraph(alg, 0, n, SBDirectionDefault);
        SBLine* line = SBParagraphCreateLine(par, 0, SBParagraphGetLength(par));
        const SBRun* run = SBLineGetRunsPtr(line, NULL);
        int runs = SBLineGetRunCount(line);
        (void)run;
        char fb_hex[512], sb_hex[512];
        // FriBidi levels per char
        for (int i = 0; i < n && i < 32; i++) fb_hex[i] = '0' + (fb_levels[i] % 8);
        fb_hex[n < 32 ? n : 32] = 0;
        // SheenBidi: resolve level of first run offset 0 char via levels lookup
        SBLocator loc; SBLineGetLocator(line, &loc);  // deprecated-ish; use runs
        int sb0 = -1;
        const SBRun* runs_p = SBLineGetRunsPtr(line, NULL);
        for (int r = 0; r < runs; r++)
            for (int i = runs_p[r].offset; i < runs_p[r].offset + runs_p[r].length; i++)
                if (i == 0) sb0 = (int)runs_p[r].level;
        (void)sb0;
        (void)loc;
        printf("case%d len=%d runs_sb=%d fribidi_levels=%s par_dir_sb=%s\n",
               c, n, runs, fb_hex,
               SBParagraphGetDirection(par) == SBDirectionRTL ? "RTL" : "LTR");
        SBLineRelease(line); SBParagraphRelease(par); SBAlgorithmRelease(alg);
    }
    return 0;
}
