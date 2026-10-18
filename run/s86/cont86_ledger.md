# CONT-86 RESULT — #364: فهرست باقی‌مانده‌ها (اول) + لیست کاری بزرگ با تایید/رد تک‌تک

HEAD `origin/main` · binary sha256-16 `d22b36be55764348` · registry **692+4 → 702 roots** (F-NEW-390/391/392/393/394/395 + 17 re-grade)

## ۰. بیس‌لاین
انجام CONT-83 (`928379d680b7cb74`) سبز بود؛ این موج روی باینری نهایی خودش (`d22b36be55764348`) تمام گیت‌ها را دوباره گرفته: **wall 12/12 · goldens 4/4 · negatives 19/19 · reinstall 8/8 · MG-310 7/7 · MG-150 3/3 · c72priv 12-OK/0-BAD · selftests 13/13 — صفر drift.**

## ۱. باقی‌مانده‌ها (اول — دقیقاً چیزهایی که هنوز تمام نشده)
| # | مورد | وضعیت | چرا مانده |
|---|------|-------|-----------|
| R1 | **F-NEW-395** (جدید، از decode این موج) | CONFIRMED_OPEN_GAP P2 | استثنای deferred که داخل `<clinit>` raise می‌شود، catch-allِ همان فریم را نمی‌بیند (Luu;.<clinit> forName("java.lang.Thread") → CNFE «uncaught» با وجود catch در pc=28). اصلاحش مسیر clinit-frame deferred-raise را دستکاری می‌کند — خطر رگرسیون روی خانواده F-NEW-376؛ جدا ثبت شد تا موج بعد با fixture اختصاصی برود |
| R2 | GLSL compile (پیکسل GLES20) | BLOCKED (نام‌برده از CONT-83) | PortableGL GLSL کامپایل نمی‌کند؛ دو گزینه ثبت‌شده (ترجمه GLSL→C یا Mesa-llvmpipe) هر دو project-scale/RAM-bound |
| R3 | ES1-FFP translation | BLOCKED (frontier) | زیرمجموعه ES1 زنده؛ ترجمه کامل FFP = پروژه مستقل |
| R4 | AndroidGraphics object-graph fields (tower3d) | OPEN | خروجی زنجیره F-NEW-387/389؛ فیلدهای آبجکت گراف تکمیل نشده |
| R5 | F-NEW-381 throughput wall | CONFIRMED_NOT_FIXED | ~310K inst/s پابرجا؛ profile CONT-77 FLAT بود؛ تغییر representation بدون شواهد پروفایل جدید، طبق خود directive انجام نمی‌شود |
| R6 | F-145 screenshot top-of-stack (multi-activity) | OPEN P1 | این موج دست نخورد |
| R7 | F-NEW-214 logs-as-data | PENDING P2 | این موج دست نخورد |
| R8 | F-NEW-192 draw/z-order audit residue | REGISTERED P2 | این موج دست نخورد |
| R9 | R-NEW-456 z.ai Svelte-5 boot | BLOCKED | وابستگی باندل خارجی، نه عیب runtime |
| R10 | خانواده Compose dooz (F-NEW-265/277/288/378/316/317/374/217/250/314) | CLASSIFIED (frontier P0/P1) | مرز محتوای dooz؛ نیازمند موج‌های اختصاصی Compose (همان نقشه CONT-77) |
| R11 | UPP-001-class native parity (JNI surface کامل) | CONFIRMED_ADVANCED/residual | مرز اسمی؛ parity کامل = پروژه |

## ۲. لیست کاری بزرگ — تایید/رد تک‌تک (این موج + re-grade های صادقانه)
| مورد | حکم | تایید/رد | دلیل در یک خط |
|------|-----|---------|----------------|
| **T8 SWIPE** (CONT-84: CONFIRMED_NOT_FIXED) | → **APPROVED تایید** | ✅ | F-NEW-390 ROOT-CAUSED-FIXED: قرارداد receiver در marshaling کال‌بک gesture (شیفت یک‌اسلاتی همه پارامترها)؛ fixture `com.probe.swipe1` + `--swipe`: onScroll dx=-16/dy=+25 (قانون AOSP)، onFling vx=+1055.77/vy=-1562.49 — قبل از فیکس: dx مقدار Y، dy/vy خالی(NaN)، e2=(0,0) |
| **85-T10 virtual clock** | → **APPROVED تایید** | ✅ | fixture `com.probe.clock1` PASS 4/4: uptime +120ms با sleep، elapsedRealtime≥uptime، currentTimeMillis پل ساعت میزبان، nanoTime مونوتونیک — residual ثبت‌شده بسته شد |
| **T5 AndStatus2048** (CONT-84: BLOCKED_NEEDS_EVIDENCE) | → **APPROVED تایید** | ✅ | decode کامل با androguard + چهار قانون عمومی F-NEW-391..394 (getenv / getSystemAvailableFeatures / ByteBuffer wrap+duplicate+ByteOrder / forName Thread) — NPE 22→5→2→**0**، بوت تمیز بدون uncaught |
| F-NEW-390 gesture callback receiver contract | ROOT-CAUSED-FIXED | ✅ | ریشه یکتا: args[0]=receiver باید listener باشد؛ [C86-GCB] ثابت کرد tracker درست بود |
| F-NEW-391 System.getenv | ROOT-CAUSED-FIXED | ✅ | AOSP: Map غیر-null؛ ریشه واقعی NPE زنجیره logging-init |
| F-NEW-392 getSystemAvailableFeatures | ROOT-CAUSED-FIXED | ✅ | FeatureInfo[] غیر-null؛ حلقه دوم زنجیره |
| F-NEW-393 ByteBuffer wrap/duplicate + ByteOrder | ROOT-CAUSED-FIXED | ✅ | حلقه سوم/چهارم؛ [C86-BRIDGE] مسیر ثابت شد |
| F-NEW-394 forName(java.lang.Thread) | ROOT-CAUSED-FIXED | ✅ | پل کلاس framework مدل‌شده؛ AOSP: forName برای کلاس platform هرگز CNFE نمی‌دهد |
| F-NEW-395 deferred-exception در clinit | CONFIRMED_OPEN_GAP | ❌ رد (باز) | ثبت با decode؛ اصلاح پرمخاطره → موج بعد با fixture |
| F-NEW-156 chessclock onCreate NPE | ALREADY_FIXED_AND_TESTED | ✅ | اجرای تازه: SGET مقدار می‌دهد (obj_id=11)، صفر APP-BOUNDARY؛ صورت `fe3ae1167c9e968c` |
| F-NEW-157 libGDX createGLSurfaceView NPE | SUPERSEDED-BY-EVIDENCE | ✅ | اجرای تازه: بدون NPE؛ catch-all خود libGDX نیتِیو را می‌گیرد؛ صورت `b5a7a35d5fe0564b` بایت‌برابر رکورد CONT-17 |
| F-144 GL/EGL surface family | SUPERSEDED-BY-EVIDENCE | ✅ | خانواده F-NEW-387/388/389 پوشش داد؛ residual=GLSL (ثبت) |
| F-NEW-169 WhatsApp invalid APK | NOT-APPLICABLE | ✅ رد | آرتیفکت ورودی خراب است (ZIP magic) — عیب runtime نیست |
| R-NEW-047/048/049/050/064/114..121 (13 ردیف) | SUPERSEDED-BY-EVIDENCE | ✅ | قانون ELF64/DT_NEEDED ایزوله F-NEW-387 همان تحقیق را پیاده کرد (اثبات: libgdx.so واقعی tower3d) |
| R-NEW-164 tooling class G | SUPERSEDED-BY-EVIDENCE | ✅ | INFRA-GFXTRACE-1 تحویل شد |
| R-NEW-165/166 differential harness | SUPERSEDED-BY-EVIDENCE | ✅ | خانواده گیت wall/goldens/negatives/reinstall + A/B بایت‌برابر موجود است |
| FOUNDATION-6 semantic-probe runner | REJECTED_WITH_REASON | ❌ رد | هدفش (پروب معنایی + first-missing) توسط INFRA-GFXTRACE-1 + ناوگان fixture + گیت goldens پوشش داده می‌شود؛ runner جدا = تکرار |

## ۳. پرسنتاژ
- **کارهای این موج: ۶ ریشه جدید + ۱۷ re-grade — ۵/۶ تایید (ROOT_CAUSED-FIXED) و ۱ باز ثبت‌شده با decode کامل (F-NEW-395)**
- **بسته‌شدن‌های backlog این موج: T8 ✅ · 85-T10 ✅ · T5 ✅ · F-NEW-156 ✅ · F-NEW-157 ✅ · F-144 ✅ · F-NEW-169 ✅ · 13×R-NEW-047..121 ✅ · R-NEW-164/165/166 ✅ · FOUNDATION-6 ❌(رد با دلیل) = 19 تایید + 2 رد صادقانه از 21 قلم پردازش‌شده (90% تایید)**
- **رگرسیون باینری نهایی `d22b36be55764348`: wall 12/12، goldens 4/4، negatives 19/19، reinstall 8/8، MG-310 7/7، MG-150 3/3، c72priv 12-OK/0-BAD، selftests 13/13 — صفر drift**
- **regression anchor های تازه: swipe1 (`a37fe754e7c8aa74`)، clock1 (`ddcb941947bf153a`) — هر دو در evidence ثبت شدند**

## ۴. یادداشت‌های صداقت
- e2 در onScroll/onFling مختصات DOWN را حمل می‌کند (payload ۴-float جا برای مختصات جاری ندارد) — residual نام‌برده: گسترش emit به ۶ float؛ دلتاها/سرعت‌ها (مقادیر اصلی مصرف‌کننده) درست‌اند
- duplicate() در مدل shadow خودِ بافر را برمی‌گرداند — واگرایی دو cursor = residual نام‌برده
- سقف [REC-MISS] (400) ردیف‌های بعدی را خاموش می‌کند — census نویز دارد؛ حکم‌ها روی decode + ردیف‌های صریح اند، نه غیاب ردیف
- getenv خالی deterministic است (not واقعی host env) — قانون sandbox؛ getenv(String) جدا مانده
- chessclock/tictactoe/andstatus صورت‌ها static/NO_ROOT-کلاس‌اند — مرز محتوای render جدا از ریشه‌های بسته‌شده این موج است
- وابستگی decode: androguard 4.1.4 نصب شد — ابزار decode برای موج‌های بعد هم هست

fixtures: `fixtures/cont86_swipe_probe` (com.probe.swipe1) · `fixtures/cont86_clock_probe` (com.probe.clock1) · scripts: `cont86_build_probes.sh`، `cont86_decode_andstatus.py`، `cont86_registry_update.py` · evidence: `run/cont86/` (as2048_post*.log زنجیره 22→5→2→0)
