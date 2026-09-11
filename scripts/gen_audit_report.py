#!/usr/bin/env python3
"""Generate a full per-item audit: every root R-NEW-001..286 with its real status,
plus the roadmap/campaign reconciliation summary. Honest, evidence-pinned, no fabrication."""
import re, json
from collections import Counter, OrderedDict

REPO = '/home/z/my-project/MiniAndroid-Compatibility-Runtime'
text = open(f'{REPO}/docs/root-searchlight/ROOT_WORKLIST.md').read()

entries = re.findall(r'^- \[(.)\] (R-NEW-\d+) — (.+?)\n((?:  - .*\n)+)', text, re.M)
rows = []
for chk, rid, title, rest in entries:
    st = re.search(r'Status: (\S+)', rest)
    pr = re.search(r'Priority: (\w+)', rest)
    cm = re.search(r'Commit: (\S+)', rest)
    ev = re.search(r'Evidence: (.+)', rest)
    rows.append(OrderedDict(
        id=rid, title=title.strip(), status=st.group(1) if st else '?',
        priority=pr.group(1) if pr else '?',
        commit=cm.group(1) if cm else '-',
        evidence=(ev.group(1).strip() if ev else '-'),
    ))

assert len(rows) == 286, f'expected 286, got {len(rows)}'
hist = Counter(r['status'] for r in rows)

FA = {
    'VERIFIED-FIXED': 'تعمیرشده با قانون + اثبات (VERIFIED-FIXED)',
    'VERIFIED-CORRECT': 'درست پیاده‌سازی‌شده و تمرین‌شده (VERIFIED-CORRECT)',
    'PARTIAL': 'هسته درست، لبه‌ها باز (PARTIAL)',
    'OBSERVED-FAIL': 'شکست زنده‌ی مشاهده‌شده (OBSERVED-FAIL)',
    'UNPROVEN': 'اثبات‌نشده (UNPROVEN)',
    'RESEARCHED-NOT-IMPLEMENTED': 'پژوهش‌شده بدون پیاده‌سازی (RESEARCHED)',
    'NOT-APPLICABLE': 'به‌دلیل معماری ناموجود (NOT-APPLICABLE)',
}

lines = []
A = lines.append
A('# گزارش حسابرسی کامل — همه‌ی اقلام دو فایل بزرگ، قلم‌به‌قلم')
A('')
A('**پاسخ صادقانه به این پرسش: «کدام‌ها انجام شد، کدام‌ها نشد؟»**')
A('')
A('این گزارش از روی فایل واقعی `docs/root-searchlight/ROOT_WORKLIST.md` در مخزن')
A('(`Sh-TB/MiniAndroid-Compatibility-Runtime`، commit `ab97aac3` = حالِ فعلیِ GitHub) تولید شده است.')
A('هیچ آیتمی با «حدس» تیک نخورده؛ هر وضعیت به commit و سند اثبات گره خورده است.')
A('')
A('---')
A('')
A('## ۰) دو تصحیح مهم درباره‌ی اعداد')
A('')
A('1. **عدد روت‌ها:** فایل MASTER ROOT SEARCHLIGHT شما **۲۷۸ روت** می‌گوید (`R-NEW-001 ... R-NEW-278`).')
A('   عدد «۲۶۷» در آن فایل، عنوانِ روتِ شماره‌ی ۲۶۷ («frame submission») است، نه تعداد کل.')
A('   در حین کار ۸ روت جدید هم کشف و ثبت شد (R-NEW-279..286، طبق §17 همان فایل که می‌گوید «۲۷۸ سقف نیست»).')
A('   **مجموع فعلی: ۲۸۶ روت.**')
A('2. **فایل «~۱۰۰ تاسک»:** منظور MASTER-ROADMAP v3 است — **۱۰۳ بخش شماره‌دار** با ۸۹۷ خط چک‌لیست.')
A('   این فایل عیناً به‌عنوان Issue #9 منتشر شد و در سشن 10 هر **۸۸۶ چک‌باکسِ** آن یکی‌یکی حسابرسی و')
A('   برچسب وضعیت واقعی گرفت: **۵۰۱ مورد [x] اثبات‌شده با رگرسیون**، بقیه با درجه‌ی صادقانه‌ی خودش (نه تیک انبوه).')
A('')
A('---')
A('')
A('## ۱) تصویر کلی: از ۲۸۶ روت، دقیقاً چه وضعیتی دارد؟')
A('')
A('| وضعیت | تعداد | معنی |')
A('|---|---|---|')
A(f"| {FA['VERIFIED-FIXED']} | {hist['VERIFIED-FIXED']} | اشکال واقعی بود، قانون عمومی فرود آمد + اثبات |")
A(f"| {FA['VERIFIED-CORRECT']} | {hist['VERIFIED-CORRECT']} | از قبل درست بود و با شواهد تمرین شد |")
A(f"| {FA['PARTIAL']} | {hist['PARTIAL']} | هسته اثبات شده، لبه‌ها باز است |")
A(f"| {FA['OBSERVED-FAIL']} | {hist['OBSERVED-FAIL']} | شکست زنده — هنوز خراب است |")
A(f"| {FA['UNPROVEN']} | {hist['UNPROVEN']} | هنوز اثباتی وجود ندارد |")
A(f"| {FA['RESEARCHED-NOT-IMPLEMENTED']} | {hist['RESEARCHED-NOT-IMPLEMENTED']} | بررسی شد، پیاده‌سازی نشد |")
A(f"| {FA['NOT-APPLICABLE']} | {hist['NOT-APPLICABLE']} | زیرسیستم در معماری فعلی وجود ندارد |")
A(f"| **جمع** | **286** | |")
A('')
A('⚠️ **نکته‌ی کلیدی:** ادعا نشده که «هر ۲۷۸ روت تست و بسته شد». کار انجام‌شده **نقشه‌برداری کامل با')
A('وضعیت صادقانه** بوده است: ۵۰ مورد تأییدشده، ۱۰۰ مورد نصفه، ۷۳ مورد اثبات‌نشده، ۶ مورد خرابِ زنده.')
A('پس «تموم‌شدنِ سریع» یک تصور است — چیزی که سریع انجام شد *فهرست‌برداری و درجه‌بندی صادقانه* بود،')
A('نه بستن همه‌ی روت‌ها.')
A('')
A('---')
A('')
A('## ۲) مواردی که صادقانه «انجام نشده» اند (مهم‌ترین‌ها)')
A('')
A('### ۲-۱) شکست‌های زنده (OBSERVED-FAIL) — ۶ مورد')
A('')
for r in rows:
    if r['status'] == 'OBSERVED-FAIL':
        A(f"- **{r['id']} [P{r['priority'][1] if r['priority'].startswith('P') else '?'}]** {r['title']}")
A('')
A('### ۲-۲) روت‌های P0 حل‌نشده (PARTIAL در اولویت بحرانی)')
A('')
for r in rows:
    if r['status'] == 'PARTIAL' and r['priority'] == 'P0':
        A(f"- **{r['id']}** {r['title']}")
A('')
A('### ۲-۳) خط مقدم فعلی (CURRENT FRONTIER)')
A('')
A('- **R-NEW-246 — first-frame completeness (P0)**: dooz در HEAD فعلی **0/2,073,600 پیکسل غیرسفید**')
A('  رندر می‌کند؛ فرزندان ComposeView = 0؛ بدون exception؛ انسداد بالادستِ draw است.')
A('  زنجیره‌ی علت: R-NEW-279 (ثبت‌کننده‌ی lifecycle callback) + R-NEW-285 (لغو frame-await با Job فعال).')
A('  **این یعنی هدف اصلی M9 (dooz قابل‌بازی / Hello World رنگی کامل) هنوز بسته نشده است.**')
A('')
A('---')
A('')
A('## ۳) فهرست کامل ۲۸۶ روت، قلم‌به‌قلم')
A('')
by_status = OrderedDict((k, []) for k in
    ['VERIFIED-FIXED','VERIFIED-CORRECT','PARTIAL','OBSERVED-FAIL','UNPROVEN','RESEARCHED-NOT-IMPLEMENTED','NOT-APPLICABLE'])
for r in rows:
    by_status[r['status']].append(r)

for st, group in by_status.items():
    A(f"### {FA[st]} — {len(group)} مورد")
    A('')
    for r in group:
        cm = f" | commit `{r['commit']}`" if r['commit'] != '-' else ''
        A(f"- {r['id']} [P{r['priority'][1] if r['priority'].startswith('P') else '?'}] — {r['title']}{cm}")
    A('')

A('---')
A('')
A('## ۴) فایل «~۱۰۰ تاسک» (MASTER-ROADMAP v3) — وضعیت')
A('')
A('- کل فایل: **۱۰۳ بخش شماره‌دار**، منتشرشده عیناً در Issue #9.')
A('- در سشن 10 (M3-S10-1) **هر ۸۸۶ چک‌باکس** حسابرسی شد و وضعیت واقعی §0.6 گرفت:')
A('  **۵۰۱ [x] اثبات‌شده با رگرسیون**؛ بقیه با برچسب درجه‌ی واقعی (PARTIAL/OBSERVED/…).')
A('- خانواده‌های بسته‌شده با قانون عمومی (نمونه‌های شاخص):')
A('  - خانواده‌ی DEX dispatch: F-041/F-056-style قوانین opcode')
A('  - MessageQueue/Handler: F-029a، ChessClock virtual-time')
A('  - Collections/OpenJDK: F-036 (iterator)، F-039 (singleton)، F-040 (Arrays.fill همه‌ی انواع)، F-053..F-057')
A('  - Exception honesty: F-016 (قوانین ۴گانه‌ی CRASH/PARTIAL)')
A('  - Shadow قفل‌ها: F-017 (LocksShadow) + قانون receiver-oid')
A('  - Choreographer frame-pump: F-050 (چهار روت عمومی از زنجیره‌ی first-frame dooz)')
A('  - ARSC/Resources: F-044/F-045 + hello_color golden (SHA 11e0056320d8546d)')
A('- باتری رگرسیون فعلی: **91/91 ALL PASS** در HEAD ادغامی.')
A('- بخش‌هایی از نقشه‌راه که هنوز بازند: خانواده‌ی Compose first-frame (بالا)، native/JNI path (بخش 37 نقشه‌ی راه قبلی)،')
A('  Telegram T-milestoneهای بالا (T6+)، ماتریس 2nd-APK (GATE I).')
A('')
A('## ۵) فایل MAIN CODER CAMPAIGN (۵۱ بخش) — وضعیت')
A('')
A('- بخش‌های 0–2 (قوانین/واقعیت/تاریخ): رعایت و اعمال شد (HEAD truth, Git safety, no force-push).')
A('- یافته‌های #1..#10 (sections 3–12): همگی به ثبت‌رسانی FINDING/FORGOTTEN تبدیل و روی خط F-0xx پیاده شد؛')
A('  مسیر متن (text pipeline)، measure/layout، relayout تغییر متن، فونت APK، DrawPath، android:onClick،')
A('  ARSC، multi-DEX resolution، Compose/RenderNode، طبقه‌بندی «صفحه‌سیاه = موفقیتِ دروغین» (بخش 14) همگی')
A('  به قانون دائمی تبدیل شدند (screenshot metrics + pixel count در باتری).')
A('- بخش 15 (مدل شواهد real-APK) و بخش 41 (E0..E5): در ROOT_EVIDENCE_INDEX و باتری اعمال شد.')
A('- بخش 16 (Telegrm Pillow-workaround ممنوع): رعایت شد — هیچ workaround پکیجی در repo نیست.')
A('- بخش 17 (T0..T10 Telegram): T0..T5 لبه‌ها پیشرفت جزئی؛ T6..T10 **باز**.')
A('- بخش 35 (Phase A..H کمپین full-render Telegram): **باز** (وابسته به خط مقدم first-frame).')
A('- بخش 36 (requirement فریم دوم): برای hello_color برقرار است؛ برای dooz هنوز نه (0 پیکسل).')
A('- بخش 37 (native/JNI): **باز** — inventory اولیه ثبت شده، پیاده‌سازی نشده.')
A('- بخش 38–39 (state mutation طلایی): اعمال شد در باتری (micro-proofs + persistence goldens).')
A('- بخش 40 (دانش‌نامه‌ی agent discoveries): FINDINGS_REGISTRY + FORGOTTEN ledger — انجام شد.')
A('- بخش 42 (اولویت P0/P1/P2): P0ها عمدتاً بسته یا در خط مقدم؛ P1/P2 بخشی در کار (FORGOTTEN ledger).')
A('- بخش 43–44 (ممنوعیت پچ اختصاصی Telegram / بازسازی UI بیرونی): رعایت شد — صفر استثنا.')
A('- بخش 45–46 (تست بعد از هر فیکس + tests تفکیک‌کننده): باتری 91/91 و goldenهای پیکسلی — انجام شد.')
A('- بخش 47–48 (انضباط commit/release): 192 commit با پیام واقعی؛ v0.0.3/v0.0.4 منتشرشده؛ asset Windows صادقانه «ناموجود» ثبت شد.')
A('- بخش 49 (worklog): worklog.md + ROOT_WORKLOG.md — انجام شد.')
A('- بخش 50–51 (خروجی نهایی / حالت خودکار): در جریان — هدف نهایی (dooz کامل) هنوز باز است.')
A('')
A('## ۶) سه تسکِ این سری (A/B/C) — انجام شدند و روی GitHub اند')
A('')
A('| تسک | نتیجه | commit |')
A('|---|---|---|')
A('| A — انتشار همه‌ی دستاوردهای قبلی | ۰ بدهی انتشار؛ remote = local؛ تأیید با ls-remote؛ توکن بیرون repo | `0383f19f` |')
A('| B — نقشه‌ی زنده‌ی 278+8 روت با وضعیت صادقانه | ROOT_WORKLIST.md + 4 ledger + root_registry.json | `bcfd4405` |')
A('| C — زیرساخت ابزار PHASE 0 + benchmark واقعی | tools/verify/* + doctor 17/17 + agent-index + TOOLING_BASELINE | `3ea1ffc3` |')
A('')
A('- Benchmark صادقانه: روی میکرو-تسک‌ها بهبود wall-clock دیده نشد (0.6x — python startup غالب بود)؛')
A('  سود اثبات‌شده: کاهش tool-call 4→1، کاهش context −44%/−92%، کش artifact مشترک. **هیچ عدد ساختگی ثبت نشد.**')
A('')
A('## ۷) چطور خودت راستی‌آزمایی کنی؟')
A('')
A('- فهرست کامل وضعیت‌ها: `docs/root-searchlight/ROOT_WORKLIST.md` (۲۸۶ قلم، هر کدام با Evidence/Commit/Next action)')
A('- شواهد: `docs/root-searchlight/ROOT_EVIDENCE_INDEX.md` و `FAILURE_LEDGER.md` (شکست‌ها و leadهای غلط هم نگه داشته شده‌اند)')
A('- نقشه‌ی راه ۱۰۳بخشی: Issue #9 (هر ۸۸۶ چک‌باکس با برچسب واقعی)')
A('- حالت HEAD روی GitHub: commit `ab97aac3` (main)')
A('- باتری رگرسیون: 91/91 در HEAD ادغامی — خروجی کامل در evidence/')
A('')

out = '/home/z/my-project/download/AUDIT_همه_اقلام_وضعیت_واقعی.md'
open(out, 'w').write('\n'.join(lines) + '\n')
print('written:', out)
print('status histogram:', dict(hist))
print('total rows:', len(rows))
