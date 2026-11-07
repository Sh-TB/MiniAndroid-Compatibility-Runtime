#!/usr/bin/env node
/* S188-W11 impact review report — Persian RTL DOCX.
 * Cover: recipe R1 (mirrored for RTL) per docx skill design-system.
 * 3-section architecture: cover (no page#) -> TOC (Roman) -> body (Arabic).
 * Evidence: evidence/s188_w11/* + s188_w8/w9/w10 records.
 */
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, PageBreak, Header, Footer, PageNumber, NumberFormat,
  AlignmentType, HeadingLevel, WidthType, BorderStyle, ShadingType,
  TableLayoutType, SectionType, TableOfContents,
} = require("docx");
const fs = require("fs");

/* ---------- palette (tech report: cool + heavy + active) ---------- */
const P = {
  primary: "1B2A4A", body: "1C2430", secondary: "5B6B7D",
  accent: "2563EB", surface: "EEF3FB", altRow: "F7FAFD",
  coverBg: "0F1B33", coverTitle: "FFFFFF", coverSub: "C9D4E8",
  coverMeta: "AAB8D0", coverFooter: "8FA0BC",
  ok: "1F7A3D", warn: "9A5B00", bad: "A03030",
};
const FA_BODY = "Noto Naskh Arabic";
const FA_HEAD = "Noto Sans Arabic";
const MONO = "DejaVu Sans Mono";

/* ---------- helpers ---------- */
function fa(text, o = {}) {
  return new TextRun({
    text, rightToLeft: true,
    bold: o.bold || false, boldComplexScript: o.bold || false,
    italics: o.italics || false,
    size: o.size || 24, sizeComplexScript: o.size || 24,
    color: o.color || P.body,
    font: { ascii: o.mono ? MONO : (o.head ? FA_HEAD : FA_BODY),
            hAnsi: o.mono ? MONO : (o.head ? FA_HEAD : FA_BODY),
            cs: o.head ? FA_HEAD : FA_BODY, eastAsia: FA_BODY },
  });
}
function code(text, o = {}) {
  return new TextRun({
    text, size: o.size || 20, sizeComplexScript: o.size || 20,
    color: o.color || P.accent,
    font: { ascii: MONO, hAnsi: MONO, cs: MONO, eastAsia: MONO },
  });
}
function heading(text, level, opts = {}) {
  const sz = level === HeadingLevel.HEADING_1 ? 32 :
             level === HeadingLevel.HEADING_2 ? 28 : 26;
  return new Paragraph({
    heading: level, bidirectional: true,
    alignment: opts.center ? AlignmentType.CENTER : AlignmentType.START,
    spacing: { before: level === HeadingLevel.HEADING_1 ? 360 : 260,
               after: 140, line: 312 },
    children: [fa(text, { bold: true, size: sz, color: P.primary, head: true })],
  });
}
function body(children, o = {}) {
  const kids = Array.isArray(children) ? children : [fa(children)];
  return new Paragraph({
    bidirectional: true, alignment: o.align || AlignmentType.JUSTIFY,
    spacing: { line: 312, after: o.after == null ? 120 : o.after },
    children: kids,
  });
}
function cell(kids, o = {}) {
  return new TableCell({
    children: Array.isArray(kids) ? kids : [kids],
    shading: { type: ShadingType.CLEAR, fill: o.fill || "FFFFFF" },
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    width: o.w ? { size: o.w, type: WidthType.PERCENTAGE } : undefined,
    verticalAlign: "center",
  });
}
function para(kids, o = {}) {
  return new Paragraph({
    bidirectional: o.rtl !== false,
    alignment: o.align || AlignmentType.START,
    spacing: { line: 276 },
    children: Array.isArray(kids) ? kids : [kids],
  });
}
function cellText(txt, o = {}) {
  return para(fa(String(txt), o), { align: o.align });
}
function makeTable(headerCells, rows, widths, hdrSize = 20) {
  /* rows: array of rows; each row = array of Paragraph|kids wrapped in striped cells */
  const mkRow = (r, ri) => new TableRow({
    cantSplit: true,
    children: r.map((c, i) => cell(c, { fill: ri % 2 ? P.altRow : "FFFFFF", w: widths[i] })),
  });
  return new Table({
    visuallyRightToLeft: true,
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: P.primary },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: P.primary },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: "C9D2DE" },
      insideVertical: { style: BorderStyle.NONE },
    },
    rows: [
      new TableRow({
        tableHeader: true, cantSplit: true,
        children: headerCells.map((t, i) =>
          cell(cellText(t, { bold: true, size: hdrSize, color: P.primary }), { fill: P.surface, w: widths[i] })),
      }),
      ...rows.map(mkRow),
    ],
  });
}
function tableTitle(text) {
  return new Paragraph({
    bidirectional: true, keepNext: true, alignment: AlignmentType.START,
    spacing: { before: 160, after: 80, line: 312 },
    children: [fa(text, { bold: true, size: 21, color: P.secondary })],
  });
}

/* ---------- cover (R1 mirrored for RTL) ---------- */
function splitTitleLinesFa(title, cpl) {
  const words = title.split(" ");
  const lines = []; let cur = "";
  for (const w of words) {
    const t = cur ? cur + " " + w : w;
    if (t.length <= cpl) cur = t;
    else { if (cur) lines.push(cur); cur = w; }
  }
  if (cur) lines.push(cur);
  if (lines.length > 1 && lines[lines.length - 1].length <= 4) {
    const last = lines.pop();
    lines[lines.length - 1] += " " + last;
  }
  return lines;
}
function calcTitleLayoutFa(title, maxWidthTwips, preferredPt = 40, minPt = 24) {
  /* Persian Naskh avg glyph width ~ pt*11 twips (CJK rule pt*20 over-penalizes). */
  const charWidth = (pt) => pt * 11;
  let titlePt = preferredPt, lines;
  while (titlePt >= minPt) {
    const cpl = Math.floor(maxWidthTwips / charWidth(titlePt));
    if (cpl < 4) { titlePt -= 2; continue; }
    lines = splitTitleLinesFa(title, cpl);
    if (lines.length <= 3) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) {
    lines = splitTitleLinesFa(title, Math.floor(maxWidthTwips / charWidth(minPt)));
    titlePt = minPt;
  }
  return { titlePt, titleLines: lines };
}
function calcCoverSpacing(params) {
  const { titleLineCount = 1, titlePt = 36, hasSubtitle = false,
          hasEnglishLabel = false, metaLineCount = 0,
          fixedHeight = 800, pageHeight = 16838 } = params;
  const SAFETY = 1200;
  const usable = pageHeight - SAFETY;
  const titleH = titleLineCount * (titlePt * 23 + 200);
  const subH = hasSubtitle ? (12 * 23 + 600) : 0;
  const engH = hasEnglishLabel ? (9 * 23 + 600) : 0;
  const metaH = metaLineCount * (10 * 23 + 100);
  const content = titleH + subH + engH + metaH + fixedHeight + 3 * 300;
  const remaining = Math.max(usable - content, 400);
  const FOOTER_MIN = 800;
  const rawTop = Math.floor(remaining * 0.45);
  const rawBottom = Math.floor(remaining * 0.45);
  const bottomSpacing = Math.max(rawBottom, FOOTER_MIN);
  const topSpacing = Math.max(rawTop - Math.max(0, FOOTER_MIN - rawBottom), 400);
  return { topSpacing, bottomSpacing };
}
function buildCoverR1RTL(cfg) {
  const padL = 800, padR = 1200;
  const availableWidth = 11906 - padL - padR - 300;
  const { titlePt, titleLines } = calcTitleLayoutFa(cfg.title, availableWidth, 40, 24);
  const sp = calcCoverSpacing({
    titleLineCount: titleLines.length, titlePt,
    hasSubtitle: !!cfg.subtitle, hasEnglishLabel: !!cfg.englishLabel,
    metaLineCount: (cfg.metaLines || []).length, fixedHeight: 400,
  });
  const kids = [];
  kids.push(new Paragraph({ spacing: { before: sp.topSpacing } }));
  if (cfg.englishLabel) {
    kids.push(new Paragraph({
      bidirectional: true, alignment: AlignmentType.START,
      indent: { start: padR, end: padL }, spacing: { after: 500 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: P.accent, space: 8 } },
      children: [new TextRun({ text: cfg.englishLabel.split("").join("  "),
        size: 18, color: P.accent, font: { ascii: "Calibri", hAnsi: "Calibri" }, characterSpacing: 40 })],
    }));
  }
  titleLines.forEach((line, i) => {
    kids.push(new Paragraph({
      bidirectional: true, alignment: AlignmentType.START,
      indent: { start: padR },
      spacing: { after: i < titleLines.length - 1 ? 100 : 300,
                 line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
      children: [fa(line, { bold: true, size: titlePt * 2, color: P.coverTitle, head: true })],
    }));
  });
  if (cfg.subtitle) {
    kids.push(new Paragraph({
      bidirectional: true, alignment: AlignmentType.START,
      indent: { start: padR }, spacing: { after: 800, line: 312 },
      children: [fa(cfg.subtitle, { size: 24, color: P.coverSub })],
    }));
  }
  (cfg.metaLines || []).forEach((line) => {
    kids.push(new Paragraph({
      bidirectional: true, alignment: AlignmentType.START,
      indent: { start: padR + 200 }, spacing: { after: 80, line: 300 },
      border: { right: { style: BorderStyle.SINGLE, size: 8, color: P.accent, space: 12 } },
      children: [fa(line, { size: 22, color: P.coverMeta })],
    }));
  });
  kids.push(new Paragraph({ spacing: { before: sp.bottomSpacing } }));
  kids.push(new Paragraph({
    bidirectional: true, alignment: AlignmentType.START,
    indent: { start: padR, end: padL },
    border: { top: { style: BorderStyle.SINGLE, size: 2, color: P.accent, space: 8 } },
    spacing: { before: 200 },
    children: [
      new TextRun({ text: cfg.footerLeft || "", size: 16, color: P.coverFooter, font: { ascii: "Calibri", hAnsi: "Calibri" } }),
      new TextRun({ text: "                                        " }),
      new TextRun({ text: cfg.footerRight || "", size: 16, color: P.coverFooter, font: { ascii: "Calibri", hAnsi: "Calibri" } }),
    ],
  }));
  const noB = { style: BorderStyle.NONE };
  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: { top: noB, bottom: noB, left: noB, right: noB,
               insideHorizontal: noB, insideVertical: noB },
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: P.coverBg },
        borders: { top: noB, bottom: noB, left: noB, right: noB },
        children: kids,
      })],
    })],
  })];
}

/* ---------- footers ---------- */
function pageFooter(sz) {
  return new Footer({ children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ children: [PageNumber.CURRENT], size: sz, color: P.secondary })],
  })] });
}
const bodyHeader = new Header({ children: [new Paragraph({
  bidirectional: true, alignment: AlignmentType.START,
  border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: "C9D2DE", space: 4 } },
  children: [fa("گزارش بازبینی اثر — S188 / W11", { size: 18, color: P.secondary })],
})] });

/* ---------- data (all from evidence) ---------- */
const appRows = [
  ["com.justdeax.composeStopwatch", "COMPOSE", "F", "F", "F", "F", "0", "ثابت"],
  ["tibarj.tranquilstopwatch", "VIEW", "F", "F", "F", "F", "0", "ثابت"],
  ["com.qwde.ccm", "GODOT", "F", "F", "F", "F", "0", "ثابت"],
  ["eu.quelltext.memory", "HTML5 بسته‌بندی‌شده", "B", "B", "B", "B", "0", "ثابت"],
  ["cos.premy.mines", "WEBVIEW_NODE", "B", "B", "B", "B", "0", "ثابت"],
  ["eu.veldsoft.no.thanks", "COMPOSE", "B", "F", "B", "B", "0", "افت W7 — بازگشت در W10"],
  ["com.sidhant.queens", "FLUTTER", "F", "F", "F", "F", "0", "ثابت (VM پیش رفت)"],
  ["com.simondalvai.ball2box", "GODOT", "F", "F", "F", "F", "0", "ثابت"],
  ["xyz.deepdaikon.quinb", "FLUTTER", "F", "F", "F", "F", "1", "ثابت"],
  ["org.secuso.privacyfriendlybattleship", "VIEW", "F", "F", "F", "F", "0", "ثابت (۱۶۵ رنگ، ۰٫۱۲٪)"],
  ["crypto.o0o0o0o0o.games.blackjack", "HTML5 بسته‌بندی‌شده", "B", "B", "B", "B", "0", "ثابت"],
];
function appRowCells(r) {
  const tier = (t) => cellText(t, { size: 20, bold: true, color: t === "B" ? P.ok : P.secondary, align: AlignmentType.CENTER });
  return [
    para(code(r[0], { size: 15, color: P.body }), { align: AlignmentType.START }),
    cellText(r[1], { size: 17 }),
    tier(r[2]), tier(r[3]), tier(r[4]), tier(r[5]),
    cellText(r[6], { size: 18, align: AlignmentType.CENTER }),
    cellText(r[7], { size: 17 }),
  ];
}
const lawRows = [
  ["F-NEW-584", "سرشماری اسلات‌های JNI با نام دقیق اسلات", "علامت مبهم «ناسازگار» به فهرست دقیق تقاضاها تبدیل شد", "ادغام‌شده در باینری"],
  ["F-NEW-585", "شبح pthread-attr (باینری + libc لنگر)", "حذف EINVAL و BIONIC-ABORT در مسیر Flutter", "ادغام‌شده در باینری"],
  ["F-NEW-586", "چهره رشته UTF-16 + ارجاع ضعیف + قاب ارجاع محلی", "تقاضاهای سرشماری queens و quinb برآورده شد", "REAL_APK_PROVEN"],
  ["F-NEW-587", "پیش‌بارگذاری AOT snapshot با مسیر کامل", "خطای مقداردهی اولیه Dart VM snapshot حذف شد", "REAL_APK_PROVEN"],
  ["F-NEW-588", "قرارداد ALooper در حالت callback مطابق AOSP", "علت ریشه‌ای دو نخ ۱۰۰٪ CPU؛ عبور Dart VM از توقف پنج‌نخی", "REAL_APK_PROVEN"],
  ["F-NEW-589", "lane گرافیکی واقعی با OSMesa به‌جای shim", "Impeller بک‌اند OpenGLES را پذیرفت — برای نخستین‌بار", "REAL_APK_PROVEN"],
  ["F-NEW-590", "خواندن فیلد ایستا JNI (146..153) + بافر مستقیم (229..231)", "سرشماری env152/env230 به صفر رسید؛ پیام‌های واقعی موتور", "REAL_APK_PROVEN"],
  ["F-NEW-591", "قانون cap دوقراردادی ByteBuffer", "پیام‌های پلتفرم دیگر با ظرفیت صفر متولد نمی‌شوند", "REAL_APK_PROVEN"],
  ["F-NEW-592", "قانون مارشال شیء NULL", "کلاس خطای SIGSEGV در RunBundle حذف شد", "REAL_APK_PROVEN"],
  ["F-NEW-593", "قانون unwind-through-thunk (cfi + guard)", "SIGABRT به خطای نگه‌داشته‌شده صادقانه تبدیل شد", "REAL_APK_PROVEN"],
  ["F-NEW-594", "ایمنی نخی سطح JNI env", "حذف race سرشناسانه منجر به length_error", "ادغام‌شده در باینری"],
  ["F-NEW-595", "خانواده measure-answer (فعال‌سازی opt-in)", "اندازه‌های واقعی Toolbar/containers؛ رگرسیون blackjack گرفته شد", "ادغام‌شده (opt-in)"],
];
function lawRowCells(r) {
  return [
    para(code(r[0], { size: 16 }), { align: AlignmentType.START }),
    cellText(r[1], { size: 18 }),
    cellText(r[2], { size: 18 }),
    cellText(r[3], { size: 16, color: r[3] === "REAL_APK_PROVEN" ? P.ok : P.secondary }),
  ];
}
const goldenRows = [
  ["com.dozingcatsoftware.bouncy", "8a6c24ac", "8a6c24ac8a7d718e", "برقرار"],
  ["app.varlorg.unote", "3b8dcb0a", "3b8dcb0adbbc17a9", "برقرار"],
  ["io.github.yamin8000.dooz", "31ddd4d5", "31ddd4d5b8e6d18e", "برقرار"],
];
function goldenRowCells(r) {
  return [
    para(code(r[0], { size: 16, color: P.body })),
    para(code(r[1], { size: 16 }), { align: AlignmentType.CENTER }),
    para(code(r[2], { size: 16 }), { align: AlignmentType.CENTER }),
    cellText(r[3], { size: 18, bold: true, color: P.ok, align: AlignmentType.CENTER }),
  ];
}
const trajRows = [
  ["W8", "توقف پنج‌نخی: ۲ نخ ۱۰۰٪ CPU، پایان با timeout", "سرشماری JNI؛ پیش‌بارگذاری AOT؛ شبح pthread", "باز هم توقف — علت ناشناخته"],
  ["W9", "همان توقف", "F-NEW-588 (قرارداد ALooper) + F-NEW-589 (OSMesa واقعی)", "عبور از توقف؛ پذیرش Impeller؛ ۲ فریم پوسته؛ خروج تمیز"],
  ["W10", "bad_alloc در RunBundle", "F-NEW-590 تا 594؛ سرشماری ۱۲ → ۰", "۳ کلاس خطا حذف شد؛ ۲ فریم پایدار"],
  ["W11", "همان نخستین واگرایی", "بازتولید تازه: Impeller=1، frames=2، faults=0/0/1", "بازتولید کامل — بدون shim جدید"],
];
function trajRowCells(r) {
  return [
    cellText(r[0], { size: 18, bold: true, align: AlignmentType.CENTER }),
    cellText(r[1], { size: 18 }),
    cellText(r[2], { size: 18 }),
    cellText(r[3], { size: 18 }),
  ];
}

/* ---------- face images ---------- */

/* ---------- body content ---------- */
const bodyKids = [];

bodyKids.push(heading("۱. خلاصه مدیریتی — پاسخ کوتاه به پرسش اصلی", HeadingLevel.HEADING_1));
bodyKids.push(body([
  fa("پرسش این بازبینی: همه این پیشرفت‌ها — قوانین، شبح‌ها، ابزارها و ده‌ها موج کار — سرانجام چه اثری بر اجرای واقعی برنامه‌ها و بازی‌ها گذاشته است؟ پاسخ کوتاه و صادقانه چنین است: "),
  fa("خط پریدن و اجرای تمیز حالا برای هر ۱۱ اپلیکیشن واقعیbattery برقرار است", { bold: true }),
  fa(" — در اجرای تازه W11 هر ۱۱ عنوان با صفر تخطای مسیر، صفر خطای فرار (جز یک نشانه پایدار در quinb) و همان چهره‌های ثبت‌شده اجرا شدند. اما «اجرای تمیز» با «دیدن محتوای واقعی» یکی نیست: از این ۱۱ عنوان، ۴ عنوان (memory، mines، no.thanks، blackjack) چهره ساخت‌یافته واقعی می‌سازند و ۷ عنوان با چهره تک‌رنگ اجرا می‌شوند — یعنی موتور آن‌ها را بدون هیچ خطایی راه می‌اندازد، اما هنوز به رندر محتوای مالکِ اپلیکیشن نرسیده است."),
]));
bodyKids.push(body([
  fa("بزرگ‌ترین جهش واقعی در مسیر Flutter رخ داد: queens از «توقف پنج‌نخی با دو نخ ۱۰۰٪ CPU و پایان با timeout» به «عبور Dart VM از توقف، پذیرش بک‌اند OpenGLES توسط Impeller، رندر ۲ فریم پوسته و خروج تمیز» رسید — و این وضعیت در اجرای تازه W11 بایت‌به‌بایت بازتولید شد. با این حال "),
  fa("هنوز هیچ فریمی از کد خودِ اپلیکیشن Flutter رندر نشده است", { bold: true }),
  fa(" و نخستین واگرایی (std::bad_alloc در RunBundle) صادقانه ثبت شده و بدون shim جدید رها شده تا ابتدا ریشه‌یابی شود. سه لنگر طلایی (bouncy، unote، dooz) در بازسازی بایت‌دقیق باینری برقرار ماندند — یعنی هیچ‌یک از این پیشرفت‌ها قیمتِ شکستن رفتار پایدار را نداده است."),
]));

bodyKids.push(heading("۲. روش بازبینی — چگونه اثر را سنجیدیم", HeadingLevel.HEADING_1));
bodyKids.push(body([
  fa("برای اینکه پاسخ بر پایه شواهد باشد نه خاطره، کل زنجیره دوباره از نو اجرا شد. نخست باینری اصلی از سورس بازسازی شد و SHA-256 آن ("),
  code("73f4d87ac617ef4e"),
  fa(") با باینری تأییدشده پایان W10 بایت‌به‌بایت یکسان درآمد؛ لنگرهای libandroid ("),
  code("21496377b3024bea"),
  fa(") و libEGL ("),
  code("3b241394942e76e9"),
  fa(") نیز با رکوردهای W9 منطبق بودند. سپس سه نوع اجرای تازه گرفته شد: باتری کامل ۱۱ عنوان (ثبت تدریجی پس از هر اپ در "),
  code("evidence/s188_w11/W11_REVERIFICATION.json"),
  fa(")، بررسی سه لنگر طلایی ("),
  code("S188_GOLDEN_CHECK.json"),
  fa(")، و اجرای Flutter queens با پایش GL ("),
  code("W11_QUEENS_GL.json"),
  fa("). هیچ رکورد تاریخی بازنویسی نشد؛ نتایج تازه در پوشه جداگانه s188_w11 کنار رکوردهای W2/W7/W10 نگه داشته شد تا مقایسه پیش/پس ممکن باشد."),
]));
bodyKids.push(body([
  fa("معیار اثر همان معیار دستور اصلی است: نه تعداد کامیت‌ها و قوانین، بلکه «تعدادی که یک اپ واقعی جلوتر رفت». مقایسه سه نقطه زمانی انجام شد: پایه W2 (آغاز موج‌ها)، رکورد W7 (پیش از کار Flutter)، و رکورد W10 (پایین‌ترین نقطه ثبت‌شده پیش از این بازبینی). قاعده مقایسه: هیچ لنگر B نباید بیفتد؛ هر تغییر tier باید با کدام قانون توضیح‌پذیر باشد."),
]));

bodyKids.push(heading("۳. وضعیت امروز — جدول کامل ۱۱ اپلیکیشن", HeadingLevel.HEADING_1));
bodyKids.push(body([
  fa("جدول زیر هر ۱۱ عنوان را در چهار نقطه زمانی مقایسه می‌کند: پایه W2، رکورد W7، رکورد W10، و اجرای تازه همین بازبینی (W11). ستون «خطا» شمار نشانه‌های EXC-UNCAUGHT در اجرای تازه است. یک عنوان در W7 افت موقت داشت (no.thanks) که در W10 بازگردانده و تثبیت شد — نمونه کامل چرخه «کشف → ریشه‌یابی → بازگردانی»."),
]));
bodyKids.push(tableTitle("جدول ۱ — مقایسه چهره هر ۱۱ اپلیکیشن در چهار نقطه زمانی (اجرای تازه W11)؛ B = محتوای ساخت‌یافته، F = تک‌رنگ/خالی"));
bodyKids.push(makeTable(
  ["اپلیکیشن", "مسیر", "W2", "W7", "W10", "W11", "خطا", "جمع‌بندی"],
  appRows.map(appRowCells),
  [21, 12, 8, 8, 8, 8, 5, 30], 16
));
bodyKids.push(body([
  fa("دو چهره ساخت‌یافته به‌عنوان نمونه در ادامه نشان داده شده‌اند: mines با "),
  fa("۴۹.۸٪", { bold: true }),
  fa(" پیکسل غیرپس‌زمینه (۶۸۶ رنگ منحصربه‌فرد در چهره کامل) و no.thanks با ۱۳.۹٪. این دو تصویر از فریم‌بافر واقعی اجرای تازه برداشته شده‌اند — یعنی محتوای اپلیکیشن، نه تصویر جایگزین."),
], { after: 160 }));
bodyKids.push(new Table({
  visuallyRightToLeft: true,
  width: { size: 100, type: WidthType.PERCENTAGE },
  layout: TableLayoutType.FIXED,
  borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
             left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
             insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.SINGLE, size: 1, color: "C9D2DE" } },
  rows: [new TableRow({ cantSplit: true, children: [
    new TableCell({ children: [para(new ImageRun({ type: "jpg", data: fs.readFileSync("/home/z/my-project/evidence/s188_w10/face_cos.premy.mines.jpg"), transformation: { width: 144, height: 256 } }), { align: AlignmentType.CENTER }),
      para(fa("mines — B، ۴۹.۸٪ غیرپس‌زمینه", { size: 16, color: P.secondary }), { align: AlignmentType.CENTER })],
      margins: { top: 80, bottom: 80, left: 100, right: 100 }, width: { size: 50, type: WidthType.PERCENTAGE } }),
    new TableCell({ children: [para(new ImageRun({ type: "jpg", data: fs.readFileSync("/home/z/my-project/evidence/s188_w10/face_eu.veldsoft.no.thanks.jpg"), transformation: { width: 144, height: 256 } }), { align: AlignmentType.CENTER }),
      para(fa("no.thanks — B، ۱۳.۹٪ غیرپس‌زمینه", { size: 16, color: P.secondary }), { align: AlignmentType.CENTER })],
      margins: { top: 80, bottom: 80, left: 100, right: 100 }, width: { size: 50, type: WidthType.PERCENTAGE } }),
  ] })],
}));
bodyKids.push(body([
  fa("درباره ستون‌های «تک‌رنگ/خالی» باید صادق بود: طبق اصل UNOBSERVED ≠ PASS، چهره خالی به معنای شکست نیست — به معنای «محتوای مالک اپ هنوز مشاهده نشده» است. battleship نمونه مرزی است: ۱۶۵ رنگ در فریم هست، اما سهم غیرپس‌زمینه فقط ۰.۱۲٪ است و بنابراین درخواست ارتقای tier نمی‌کند. همین تمایز دقیق است که مانع از ابراز پیشرفت بیش از اندازه می‌شود."),
]));

bodyKids.push(heading("۴. سه لنگر طلایی — پایداری بایت‌دقیق", HeadingLevel.HEADING_1));
bodyKids.push(body([
  fa("هر تغییر در loader یا pthread یا رندر می‌تواند رفتار اپ‌های پایدار را بی‌صدا بشکند. برای همین سه عنوانِ مرجع بایت‌دقیق پین شده‌اند و در هر بازسازی چک می‌شوند. در موج W10 این چک شش بار (پس از هر قانون جدید) اجرا شد و همگی برقرار بودند؛ در این بازبینی نیز روی باینری بازسازی‌شده یک‌بار دیگر اجرا شد و نتیجه همان است:"),
]));
bodyKids.push(tableTitle("جدول ۲ — پین‌های طلایی روی باینری بازسازی‌شده (اجرای تازه)"));
bodyKids.push(makeTable(
  ["عنوان", "پین مرجع", "چهره اجرای تازه", "وضعیت"],
  goldenRows.map(goldenRowCells),
  [34, 20, 28, 18]
));
bodyKids.push(body([
  fa("نکته dooz: ۶ نشانه uncaught در چهره پایدار ثبت‌شده این عنوان است (وضعیت شناخته‌شده و ثابت از موج W1)؛ پین چهره برقرار است و این نشانه‌ها بخشی از همان رفتار مرجع‌اند. معنای عملی جدول بالا این است که کل موج‌های W8 تا W11 — شبح pthread، لنگر EGL/GLESv2، ALooper و OSMesa — هیچ ردی در رفتار سه مرجع باقی نگذاشته‌اند."),
]));

bodyKids.push(heading("۵. مسیر Flutter (queens) — از توقف پنج‌نخی تا Impeller", HeadingLevel.HEADING_1));
bodyKids.push(body([
  fa("این بخش پاسخ مستقیم به دستور W8 است: «مقداردهی اولیه Dart VM باید از توقف پنج‌نخی عبور کند، با trace قابل انتساب و شواهد تکرارپذیر». عبور انجام شد و انتساب کامل است: نمونه‌برداری /proc نشان داد دو نخ ۱.raster و 1.io با ۳۵۹ از ۳۵۹ نمونه در حالت running بودند؛ نمونه‌برداری ptrace هر دو نخ را روی همان نقطه ورود syscall لنگرlibc نگه داشت؛ ثبت syscall نشان داد هر دو در epoll_wait روی fd تایمرِ خودشان با timeout بی‌نهایت گیر کرده‌اند؛ و آزمون fd-state الگوی «فired-timerfd همیشه EPOLLIN» را ثابت کرد. ریشه: "),
  code("ALooper_addFd"),
  fa(" در لنگر ما callback را دور می‌ریخت ("),
  code("(void)callback"),
  fa(")، در حالی که موتور تایمرfd خود را در حالت CALLBACK ثبت می‌کند؛ تایمرِ روشن‌شده هرگز تخلیه نمی‌شد و epoll بلافاصله و برای همیشه برمی‌گشت — قفل Shell::Create روی نخ platform هرگز بسته نمی‌شد."),
]));
bodyKids.push(tableTitle("جدول ۳ — مسیر queens در چهار موج"));
bodyKids.push(makeTable(
  ["موج", "وضعیت در آمدن", "رویداد کلیدی", "نتیجه"],
  trajRows.map(trajRowCells),
  [8, 26, 34, 32]
));
bodyKids.push(body([
  fa("پس از عبور از توقف، مسیر GL واقعی باز شد: به‌جای گسترش بیشتر shim، کتابخانه واقعی OSMesa (Mesa 25.0.7 llvmpipe، GL 4.5) بدون root دانلود و بارگذاری شد و لنگرهای EGL/GLESv2 به اشاره‌گرهای واقعی GL وصل شدند — نتیجه: Impeller برای نخستین‌بار بک‌اند OpenGLES را پذیرفت و «Frames Rendered: 2» با خروج exit=1 تمیز ثبت شد. در W10 سه کلاس خطای بعدی (SIGSEGV شیء NULL، SIGABRT unwinding، length_error رقابت سرشناسانه) یکی‌یکی حذف شدند و سرشماری اسلات JNI از ۱۲ به ۰ رسید. وضعیت فعلی صادقانه این است: "),
  fa("فریم‌ورک Flutter هنوز اجرا نشده و ۲ فریم پوسته فریمِ اپلیکیشن نیست", { bold: true }),
  fa("؛ نخستین واگرایی باقی‌مانده std::bad_alloc درون فراخوان RunBundle است که هنوز انتساب نشده و طبق قانون «پیش از تعیین قرارداد گمشده shim اضافه نکن»، فقط پروب unwinding آماده شده است."),
]));

bodyKids.push(heading("۶. اثر مستقیم قوانین بر اجرای واقعی", HeadingLevel.HEADING_1));
bodyKids.push(body([
  fa("جدول زیر هر قانون این دوره را با «اثر قابل مشاهده بر اجرا» خلاصه می‌کند. ستون مرحله طبق زنجیره شواهد است: ادغام در سورس → ادغام در باینری → اثبات روی APK واقعی (REAL_APK_PROVEN). ده قانون به اثبات روی APK واقعی رسیدند و هر یک با نشانه قابل‌تکرار — نه با روایت — پشتیبانی می‌شود."),
]));
bodyKids.push(tableTitle("جدول ۴ — قوانین F-NEW-584 تا 595 و اثر اجرایی هر یک"));
bodyKids.push(makeTable(
  ["شناسه", "عنوان", "اثر بر اجرا", "مرحله"],
  lawRows.map(lawRowCells),
  [13, 28, 37, 22]
));

bodyKids.push(heading("۷. اثر androguard بر سرعت و صحت تحقیق", HeadingLevel.HEADING_1));
bodyKids.push(body([
  fa("تصمیم W8 برای ارتقای androguard به ابزار اصلی DEX عملاً روی سرعت کل دوره اثر گذاشت. آزمون رودررویی روی همان دیوارهای واقعی W6/W7: androguard پرسش‌های ۵گانه را با ۵/۵ دقیق در ۰.۵۹ ثانیه پاس داد؛ JADX فقط ۳/۵ در ۱۳.۷ ثانیه و در همان روش دیواری عبارت «Method not decompiled» داد و دو متد h0 را کامل از دست داد. یعنی هر ریشه‌یابی بعدی — از RNG قرارداد OpenJDK تا دیکد styleable و شمارش فراخوان‌های ایستا — با یک ابزارِ سریع و درست انجام شد. سیاست حاصل: androguard = oracle خودکار اصلی؛ DEX خام و Smali = منبع واقعیت؛ JADX = ابزار اختیاری خوانایی؛ و افزودن ابزار معکوس جدید بدون شکاف اثبات‌شده ممنوع. در W9/W10 تمام انتساب‌ها روی زمین DEX ایستادند و همین سبب شد بدون حدس‌زدن، قرارداد دقیق گمشده (ALooper callback mode) پیدا شود."),
]));

bodyKids.push(heading("۸. رگرسیون‌گیری زنده — داستان F-NEW-595", HeadingLevel.HEADING_1));
bodyKids.push(body([
  fa("بهترین اثبات ارزش باتری، رگرسیونی است که خودش گرفت. در W10 قانون اندازه‌گیر (measure-answer) به‌صورت پیش‌فرض‌روشن فعال شد و درخت ts پیشرفت واقعی کرد (پاسخ‌های اندازه واقعی، Toolbar با 1080x168) — اما باتری همان‌جا چهره blackjack را از B به F سقوط‌داده دید. تشخیص تماس‌گیرنده نخستین واگرایی را در همان کلاس‌های androidx نشان داد و قانون به opt-in بازگردانده شد؛ نتیجه نهایی W10: باتری CLEAN با صفر سقوط tier. چرخه کامل «تغییر → اجرای باتری → گرفتن رگرسیون → ریشه‌یابی → بازگردانی اثبات‌شده» بدون هیچ میان‌بر اجرا شد. اجرای تازه این بازبینی نیز همان جمع‌بندی را تکرار کرد: ۱۱/۱۱ بدون هیچ افت tier نسبت به رکورد W10."),
]));

bodyKids.push(heading("۹. مرزهای صادقانه — چه چیزی هنوز اجرا نمی‌شود", HeadingLevel.HEADING_1));
bodyKids.push(body([
  fa("برای اینکه «بازبینی اثر» به تبلیغ تبدیل نشود، فهرست کامل آنچه هنوز نه: (۱) Flutter: فریم‌ورک Dart اجرا نشده، هیچ پیکسلی از کد خودِ queens رندر نشده، tier همان NO_ROOT است؛ مانع فعلی bad_alloc در RunBundle است. (۲) Godot: زنجیره بارگذاری موتور ("),
  code("System.loadLibrary(\"godot\")"),
  fa(" → GodotLib.setup → شروع main-loop) هرگز امتحان نشده؛ فقط onCreate تمیز است و این وضعیت دقیقاً ثبت شده است. (۳) lane View: زنجیره dispatch رسم باقی است (APP_DRAW_OPS)؛ اندازه‌ها واقعی شده‌اند اما نقاشی کانتینرها هنوز به فریم نمی‌رسد. (۴) quinb: یک نشانه uncaught پایدار در هر اجرا. (۵) شش عنوان با چهره خالی: اجرای تمیز است اما محتوای دیدنی صفر است. این‌ها شکاف‌های شناخته‌شده با «مانع بعدی دقیق» ثبت‌شده‌اند، نه ابهام."),
]));

bodyKids.push(heading("۱۰. تفسیر نهایی و اولویت‌های بعدی", HeadingLevel.HEADING_1));
bodyKids.push(body([
  fa("جمع‌بندی اثر: پیشرفت‌های این دوره واقعی، قابل‌انتساب و تکرارپذیرند — اما متمرکز. سه ستون اثر مشخص است: تثبیت (۱۱/۱۱ اجرای تمیز، ۰ تخطای مسیر، لنگرها برقرار)، عبور مرز (Dart VM از توقف پنج‌نخی گذشته و Impeller پذیرفته شده) و زیرساخت تحقیق (androguard به‌عنوان oracle). در برابر، «دیدن محتوای اپ» هنوز فقط در ۴ عنوان از ۱۱ محقق شده و مسیر Flutter به فریم واقعی اپ نرسیده است. مطابق قاعده «پیشرفت واقعی نه فعالیت»، همین عدد ۴/۱۱ و وضعیت queens معیار موج بعد است، نه تعداد قوانین."),
]));
bodyKids.push(body([
  fa("اولویت‌های بعدی به‌ترتیب اثر بر اجرای واقعی:"),
], { after: 80 }));
[
  "اول: انتساب std::bad_alloc در RunBundle با پروب unwinding آماده‌شده (w10_throw_probe) — تنها مانع بین وضعیت فعلی و اجرای فریم‌ورک queens.",
  "دوم: زنجیره dispatch رسم در lane View (APP_DRAW_OPS) برای تبدیل اندازه‌های واقعی ts به پیکسل واقعی.",
  "سوم: زنجیره بارگذاری موتور Godot برای ball2box و ccm — بزرگ‌ترین گروه نادیده‌مانده (۲ عنوان).",
  "چهارم: نشانه uncaught پایدار quinb — کوچک، اما تنها خطای فرار باقی‌مانده در باتری.",
  "پنجم: تکمیل حساب ارتفاع split در F-NEW-595 پیش از فعال‌سازی پیش‌فرض — درس blackjack تکرار نشود.",
].forEach((t, i) => {
  bodyKids.push(new Paragraph({
    bidirectional: true, alignment: AlignmentType.START,
    spacing: { line: 312, after: 60 },
    indent: { start: 340 },
    children: [
      fa((i + 1) + ". ", { bold: true, color: P.accent }),
      fa(t),
    ],
  }));
});
bodyKids.push(body([
  fa("شواهد این بازبینی: "),
  code("evidence/s188_w11/W11_IMPACT_REVIEW.json"),
  fa(" (رکورد کامل با SHAها)، "),
  code("W11_REVERIFICATION.json"),
  fa(" (باتری تازه)، "),
  code("W11_QUEENS_GL.json"),
  fa(" (بازتولید Flutter)، و رکوردهای تاریخی s188_w2/w7/w8/w9/w10 که هرگز بازنویسی نشدند."),
], { after: 60 }));

/* ---------- document ---------- */
const doc = new Document({
  creator: "S188 MiniAndroid Runtime",
  title: "Impact review — S188 W11",
  styles: { default: { document: {
    run: { font: { ascii: FA_BODY, hAnsi: FA_BODY, cs: FA_BODY }, size: 24, color: P.body },
    paragraph: { spacing: { line: 312 } },
  } } },
  features: { updateFields: true },
  sections: [
    { properties: { page: { size: { width: 11906, height: 16838 },
        margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: buildCoverR1RTL({
        englishLabel: "IMPACT REVIEW — S188 W11",
        title: "بازبینی اثر پیشرفت موج‌ها بر اجرای واقعی برنامه‌ها و بازی‌ها",
        subtitle: "از W2 تا W11 — آنچه واقعاً در اجرا تغییر کرد و آنچه هنوز تغییر نکرده است",
        metaLines: [
          "شاخه main — HEAD 63da80da (2026-11-07)",
          "باینری اصلی SHA-16: 73f4d87ac617ef4e — بازسازی بایت‌دقیق تأیید شد",
          "۱۱ APK واقعی × اجرای تازه — ۳ لنگر طلایی بایت‌دقیق — ۰ تخطای مسیر",
          "شواهد: evidence/s188_w11 (این بازبینی) + رکوردهای W2 تا W10",
        ],
        footerLeft: "S188 — MiniAndroid Compatibility Runtime",
        footerRight: "2026-11-08",
      }) },
    { properties: { type: SectionType.NEXT_PAGE,
        page: { size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1417, right: 1701 },
          pageNumbers: { start: 1, formatType: NumberFormat.UPPER_ROMAN } } },
      footers: { default: pageFooter(17) },
      children: [
        new Paragraph({
          bidirectional: true, alignment: AlignmentType.CENTER,
          spacing: { before: 200, after: 300 },
          children: [fa("فهرست مطالب", { bold: true, size: 32, color: P.primary, head: true })],
        }),
        new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),
        new Paragraph({
          bidirectional: true, spacing: { before: 200 },
          children: [fa("یادآوری: این فهرست با کد فیلد ساخته می‌شود؛ برای به‌روزرسانی شماره صفحات روی فهرست راست‌کلیک کرده و «Update Field» را انتخاب کنید.", { italics: true, size: 18, color: "888888" })],
        }),
      ] },
    { properties: { type: SectionType.NEXT_PAGE,
        page: { size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1417, right: 1701 },
          pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } },
      headers: { default: bodyHeader },
      footers: { default: pageFooter(18) },
      children: bodyKids },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = "/home/z/my-project/download/S188_W11_گزارش_بازبینی_اثر_بر_اجرای_برنامه‌ها_و_بازی‌ها.docx";
  fs.writeFileSync(out, buf);
  console.log("WROTE", out, buf.length, "bytes");
});
