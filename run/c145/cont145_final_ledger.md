# CONT-136..145 Ledger — «۱۰ قطار» — ۱۰ قطار، همه push شد، HEAD==origin/main بعد از هر قطار تأیید شد

**پایه:** HEAD `553aeef6` (CONT-135)، رجیستری ۷۸۷. **پایان:** HEAD `d0dacf52`، رجیستری **۷۸۹** (id-unique، main==mirror)، دیوار نهایی **9/9 anchors بایت‌یکسان + negatives 19/19 + gate A 98/0/1 + skill selftest 13/13**. خانوادهٔ تعمیرشده: **۶۰۰/۷۸۹ (۷۶.۰٪)** — PARTIAL از ۸۷ به **۲۳** رسید.

## قطار ۱ — CONT-136 · F-NEW-473 CLASSIFIED (push `137b0928`)
دربِ face خالی دوز چندلایه رمزگشایی شد: `dispatchDraw` واقعی اجرا می‌شود ولی گیت لایهٔ ریشه `Ltv0;.i` در ۶/۶ پنجرهٔ draw مقدار FALSE برمی‌گرداند (فلگ `b:I` لایهٔ ریشه obj#2575 هیچ‌وقت mark نمی‌شود — فقط `.i` صفر می‌خواند و `.d` صفر می‌نویسد؛ نمونه‌های غیرریشه با `.a` تا ۱..۱۸ می‌روند). سازندهٔ تنها AndroidCanvas کمپوز (`Ljt1;` ← `Lj7;.e` ← f/g) هرگز اجرا نمی‌شود (صفر ورود runtime) → **صفر primitive گرافیکی در پنجرهٔ draw** (CDW-OP=0). CONT-131 با xref بایت‌دقیق تأیید شد (۲ iput / ۱۷ iget — ریاضیِ درست روی EmptyMap). اهرم بعدی: مسیر mark لایهٔ ریشه + پل onDescendantInvalidated (در موتور: صفر). اصلاح harness باتری هم همین قطار: maxsec per-wagon (دیوار تلگرام=60s).

## قطار ۲ — CONT-137 · R-NEW-133 IMPLEMENTED+TESTED (push `b5958f4d`)
**InMemoryDexClassLoader فرود آمد**: ctor بافر واقعی را می‌خواند (ByteBuffer.wrap حالا `__bb_array__` را ذخیره می‌کند)، هدر dex را اسکن می‌کند (string_ids/type_ids/class_defs)، loadClass child-first + ClassNotFoundException صادقانه، getParent ثبت می‌شود. سه گپ عمومی در مسیر رفع شد: ViewShadow catch-all کلاس‌های `Ldalvik/*` را می‌ربود (node بیهوده می‌ساخت)، Context.getClassLoader برمی‌گرداند null (قانون S102 تعمیم یافت)، Character.digit نداشتیم. **فیکسچر fnew474_probe با ابزار واقعی aapt2/ECJ/D8** (dex دوم واقعی ۷۵۶ بایتی D8): ۵/۵ assertion پاس. حاشیهٔ صادقانه: RESOLUTION از dex درون‌حافظه کار می‌کند؛ LINK/EXECUTE دکس دوم هنوز محدودیت single-dex executor است (ثبت شد، وانمود نشد).

## قطار ۳ — CONT-138 · R-NEW-018/019 VERIFIED-CORRECT (push `68c1b4e3`)
**قانون Parcel**: obtain/writeInt/writeLong/writeString/writeFloat/writeDouble/writeByte/writeByteArray رکورد type-tagged append می‌کنند؛ readX از read-position مستقل می‌خواند؛ setDataPosition/dataPosition/dataSize/recycle طبق AOSP؛ خواندن past-end = رفتار native JNI (۰/null). **فیکسچر fnew475_probe (ابزار واقعی): ۸/۸ پاس**. Wire-format بایتی binder (marshall) عمداً خارج scope — ثبت صادقانه.

## قطار ۴ — CONT-139 · موج PARTIAL ۲ — ۳۰ ردیف (push `19caae31`)
**۲۷ VERIFIED-CORRECT** (R-NEW-001 قانون F-029a createAsync فرود آمده + ترتیب MQ زنده از anchor میکروتایمر؛ R-NEW-061 substrate AndroidUiDispatcher لنگر شد؛ خانوادهٔ parser-bounds ۰۸۷..۰۹۳/۱۱۰/۱۲۲..۱۲۹/۱۳۱/۱۳۴/۱۳۶/۱۴۱/۱۵۰/۱۵۲/۱۶۲/۱۶۷ با grep per-row + پیوند زنده: unote rc=0 sqlite، intents شطرنج/تلگرام، شمارنده‌های boundary)، **۳ صادقانه PARTIAL ماندند** (۰۶۲ ماتریس، ۰۷۹/۰۸۰ بدون آرتیفکت — ادعاهای اصلی از تاریخ git `4eebde76` بازیابی شد). PARTIAL: ۸۷→۶۰.

## قطار ۵ — CONT-140 · موج PARTIAL ۳ — ۳۰ ردیف (push `7f60d792`)
**۲۳ VERIFIED-CORRECT** (خانوادهٔ فونت/shaper: text_shaper سه موتور FreeType+HarfBuzz+FriBidi را سیم‌کشی می‌کند؛ خانوادهٔ TextView فیکسچرها؛ renderer clip/alpha/png؛ touch؛ window؛ oracle تراکم G04 محصور در باتری ۱۱/۱۱؛ Material3 با فیکسچر m3_style_weight + trace دوز)، **۷ صادقانه ماندند**. PARTIAL: ۶۰→۳۷.

## قطار ۶ — CONT-141 · موج PARTIAL ۴ — باقیماندهٔ سخت (push `117bcf18`)
**۱۴ VERIFIED-CORRECT** (state_list، window flags، draw order، پمپ Choreographer F-050، lifecycle کمپوز، F-057 duality، readError، census/metrics)، **۲۱ صادقانه ماندند** (جبهه‌های باز: Job-cancel ۲۸۵، Fragment host ۳۳۱، S39، WhatsApp-bound آرتیفکت ۱۶۶/۱۶۸، deferred-exc هم‌فریم ۳۶۸، CoordinatorLayout ۳۷۰، ماتریس/کورپوس — **صفر ساختگی، صفر default از خودساخته**). PARTIAL: ۳۷→۲۳.

## قطار ۷ — CONT-142 · تعمیم خانوادگی F-NEW-473 (push `754e0a6d`)
پروب CDW-OP روی **klondike، tripeaks و tictactoe هم = صفر** — خانوادهٔ frontier رسم CONT-132 یک **ریشهٔ سطح‌خانواده** دارد (پنجرهٔ draw باز می‌شود، بایت‌کد واقعی view اجرا می‌شود، صفر primitive پل می‌شود) — نه چهار معمایی جدا.

## قطار ۸ — CONT-143 · رسیدگی جفت BLOCKED + sweep کورپوس (push `638aaa29`)
۲۷ آرتیفکت APK ممیزی شد: **همه resources.arsc دارند** (R-NEW-140 resource-shrunk صادقانه BLOCKED می‌ماند — نیاز به آرتیفکت از کاربر). whatsapp.apk sha16 `c473ad25` دوباره بایت‌سطح تأیید شد: **NOT-a-zip، استاب ۵,۶۱۵ بایتی** (ARTIFACT_DEFECTIVE). R-NEW-456 (باندل z.ai Svelte-5) upstream-bound. Signal: آرتیفکتی در کورپوس نیست. صفر جعل.

## قطار ۹ — CONT-144 · F-NEW-474 ROOT-CAUSED-FIXED + deep dive وضعیت (push `d0dacf52`)
اجرای ۲۰-فریمی bouncy: `MultiDex.install → ZipUtil.findCentralDirectory` با `RandomAccessFile` طول ۰ می‌خواند → ZipException → APP BOUNDARY unwind. **قانون RandomAccessFile فرود آمد**: <init> بایت‌های REAL را slurp می‌کند (fallback تک-دامینهٔ APK — هرگز بایت از خودساخته)، length/seek/read([BII)/read/-EOF طبق OpenJDK. **نتیجه: bouncy rc 1→0 در ۲۰ فریم، ZipException 1→0، face `8a6c24ac` بدون تغییر.** deep dive بقیه: ۶/۷ اپ rc=0 در ۲۰ فریم با صفر exception (unote/microtimer/opmt/chessclock/flappycow پایدار؛ NFE های gmdice «1d2» رفتار خود اپ است — گرفته می‌شود).

## قطار ۱۰ — CONT-145 · close-out
دیوار نهایی: **9/9 anchors بایت‌یکسان** (dooz `d602648e`، klondike `31ddd4d5`، unote `90a67cc1`، chess `a0319686`، telegram `20ac8cbbbb@60s`، tower3d `11a38a5a`، opencalc `d5f3c7b5`، microtimer `bbd350b6`، sudoku `be640e39`) + negatives 19/19 + gate A 98/0/1 + skill 13/13.

## وضعیت رجیستری (۷۸۹ ریشه، id-unique، main==mirror)
ROOT-CAUSED-FIXED **۲۹۶+۱۸** · VERIFIED-CORRECT **۱۵۴** · VERIFIED-FIXED ۵۰ · IMPLEMENTED(+TESTED) ۶۴ · خانوادهٔ تعمیرشده جمعاً **۶۰۰/۷۸۹ (۷۶.۰٪)** · PARTIAL **۲۳** (از ۸۷) · ROOT-CAUSED-PARTIAL ۵ · BLOCKED ۲ (آرتیفکت‌محور) · CONFIRMED_OPEN_GAP **۰**

**اهرم‌های بعدی:** مسیر mark لایهٔ ریشهٔ کمپوز (F-NEW-473)، LINK دکس دوم برای InMemoryDexClassLoader، ۲۳ PARTIAL باقیمانده (آرتیفکت‌محور عمدتاً)، WhatsApp/Signal نیازمند APK از کاربر.
