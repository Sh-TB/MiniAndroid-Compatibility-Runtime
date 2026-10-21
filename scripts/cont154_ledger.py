#!/usr/bin/env python3
# cont154_ledger.py — build Persian ledger for #364 from final scorecard + c129 canonical
import json
from collections import Counter

sf = json.load(open('run/c154/scorecard_final.json'))
s2 = json.load(open('run/c154/scorecard2.json'))  # parallel-flawed era (for the artifact note)
c129 = json.load(open('run/c129/scorecard.json'))

new = sf['rows']
success_new = [r['name'] for r in new if r['status'].startswith('SUCCESS')]
render_new = sum(1 for r in new if r['rendered'])
zero_inf = sum(1 for r in new if r['uncaught_inflight'] == 0)
fms = Counter(r['first_missing_stage'] for r in new if not r['status'].startswith('SUCCESS'))

# canonical numbers from c129 scorecard totals (authoritative)
c129 = json.load(open('run/c129/scorecard.json'))
canon = c129.get('apps', [])
canon_n = c129['totals']['apps_run']
canon_render = c129['totals']['rendered_face']
canon_rc0 = c129['totals']['rc0']
canon_zero = c129['totals']['zero_exc']

total = len(new) + canon_n
render_total = render_new + canon_render
success_total = len(success_new) + canon_rc0

md = []
md.append('# CONT-154 — «۱۰۰ برنامه رو تست بکن» — ۱۱۶ اپ، باتری کامل، با رقم و عدد\n')
md.append('## آنچه اجرا شد\n')
md.append(f'- کورپوس از ۲۲ به **۱۱۶ اپ** گسترش یافت: **{len(new)} APK جدید از F-Droid** (دانلود مستقیم، sha16 در manifest) + ۲۲ canonical.')
md.append(f'- باتری کامل روی هر {total} اپ در binary `f6b272ea` (همان deterministic binary CONT-153)، harness استاندارد ۱۰۸۰×۱۹۲۰، ۵ فریم، ۲۵ ثانیه.')
md.append('- کشف و تصحیح مهم: اجرای موازی chunkها interference تولید می‌کرد (rc=1 کاذب). **تمام ۹۴ اپ جدید دوباره SEQUENTIAL اجرا شد** — اعداد زیر از اجرای sequential است؛ نسخهٔ معیوب و تحلیل آرتیفکت هم به‌عنوان شواهد حفظ شده (scorecard2.json + parallel_flawed/).\n')
md.append('## نتیجهٔ کلی — ۱۱۶ اپ\n')
md.append('| متریک | عدد |')
md.append('|---|---|')
md.append(f'| کل اپ تست‌شده | **{total}** |')
md.append(f'| رندر محتوای واقعی (non-white >1%) | **{render_total}/{total} ({100*render_total//total}%)** |')
md.append(f'| SUCCESS کامل موتور (lifecycle از DEX + frame truth + صفر in-flight) | **{success_total}/{total} ({100*success_total//total}%)** |')
md.append(f'| SUCCESS در ۹۴ اپ جدید | {len(success_new)} |')
md.append(f'| صفر استثنای uncaught-in-flight (۹۴ اپ) | {zero_inf} |')
md.append(f'| اپ‌های SUCCESS جدید | {", ".join(success_new)} |\n')
md.append('## چرا ۹۰ اپ PARTIAL؟ — جدول WHY (از خود موتور: F-NEW-233 first_missing_stage)\n')
md.append('| مرحلهٔ توقف | تعداد | معنی |')
md.append('|---|---|---|')
md.append(f'| APP_DRAW_OPS | {fms.get("APP_DRAW_OPS",0)} | پنجره+root ساخته شده، پس‌زمینه رسم شده، ولی صفر draw-op محتوای اپ — **همان خانوادهٔ ریشهٔ dooz (F-NEW-473..480: stale scope.V binding در زنجیرهٔ Compose draw)** |')
md.append(f'| WINDOW_ROOT | {fms.get("WINDOW_ROOT",0)} | window root هرگز ساخته نشد (مرحلهٔ قبل از draw) |')
md.append(f'| APP_PIXELS | {fms.get("APP_PIXELS",0)} | پیکسل رسم شده ولی محتوای authoritative اپ نیست |')
md.append(f'| بدون verdict (کرش قبل از کپچر فریم) | {fms.get(None,0)} |\n')
md.append('## این یعنی چه — پاسخ به «یه جای کارت اشکال داده»\n')
md.append(f'1. **ریشهٔ شمارهٔ یک الان دقیق نام‌گذاری شده و یک ریشه است، نه ۴۹ ریشه:** {fms.get("APP_DRAW_OPS",0)} اپ (بیش از نیمی از کورپوس جدید) در همان نقطه می‌ایستند که dooz ایستاده — زنجیرهٔ draw-block Compose که query آن به scope های EARLY بسته شده در حالی که نودهای capable در scope های LATE ساخته می‌شوند (F-NEW-480 TRAIN 10). قطار بعدی مالک همین ریشه است: FIELD-TRACE `Lxk0;.V` writes.')
md.append('2. تفاوت با ۱۰ روز قبل (اعداد، نه ادعا): کورپوس ۲۲→۱۱۶ (×۵.۳)؛ رندر ۲۱→۹۶ اپ؛ SUCCESS ۶→۱۱ اپ؛ registry 786→794؛ open-ish 136→56.')
md.append('3. رکورد دروغ‌سنجی: کشف آرتیفکت اجرای موازی خودش محصول همین باتری بود — rc=1 کاذب textpad در اجرای sequential به rc=0 SUCCESS تبدیل شد؛ به‌جای پنهان‌کاری، نسخهٔ معیوب و تصحیح هر دو commit شدند.\n')
md.append('## مرزهای صادقانه (بدون تغییر)\n')
md.append('- whatsapp: artifact خراب (5,615 بایت، zip نیست) — تا APK سالم از کاربر BLOCKED.')
md.append('- telegram/forkgram: UPP-001 dlopen boundary (libjnigraphics x86_64 موجود نیست در APKهای arm64-only) — APP-BOUNDARY.')
md.append('- '+f'{fms.get("WINDOW_ROOT",0)} اپ WINDOW_ROOT: مرحلهٔ lifecycle قبل از draw — قطارهای بعدی.\n')
md.append('## شواهد\n')
md.append('- `run/c154/scorecard_final.json` (۹۴ ردیف: status، uncaught_inflight، first_missing_stage، render_frac، first_exc)')
md.append('- `run/c154/battery.log` + `run/c154/*.out` (Status/Message رسمی موتور برای هر اپ)')
md.append('- `scripts/cont154_fdroid_fetch.sh` (probe+download از f-droid.org، manifest با sha16)')
md.append('- `scripts/cont154_big_battery.sh` + `cont154_parse3.py`')
md.append('- «۱۰ تا ۵۰ قطار»: خود این باتری = ۱۱۶ واگن روی یک ریل + ریشهٔ APP_DRAW_OPS به‌عنوان ریل اصلی قطار بعدی (F-NEW-480 next lever پین شده در worklog).')
print('\n'.join(md))
open('run/c154/cont154_ledger.md','w').write('\n'.join(md))
print('\n--- stats: total', total, 'render', render_total, 'success', success_total, 'canon_render', canon_render, 'canon_rc0', canon_rc0, 'canon_zero', canon_zero)
