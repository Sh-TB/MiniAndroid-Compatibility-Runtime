# WS-C3 CORPUS — وضعیت Corpus در کمپین Unified

**تاریخ:** 2026-08-27 · HEAD: `86bd646`

## ورودی جدید کمپین

| فیلد | مقدار |
|------|-------|
| App | Telegram |
| Version | 12.10.1 (versionCode 70389) |
| Package | org.telegram.messenger.web |
| Source | https://telegram.org/dl/android/apk (redirect → cdn4.telesco.pe) |
| APK SHA256 | `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6` |
| Size | 73,028,244 bytes |
| DEX count | 5 (classes..classes5.dex) |
| Manifest entries | 11,576 |
| Depth reached | L4 (resources) — اجرای login/SMS-family + رندر؛ input روی این build آزمایش نشد |
| First divergence | متن‌ها = نام فیلد R به‌جای مقدار (resource map per-version) |
| First failure | — (0 خطا) |
| Screenshot | run/uc_v12_run1/screenshot.png (3/3 SHA یکسان `06fb40da…`) |
| Manifest drift | manifest انتظار 10.14.5 (`193ad551…`) را داشت → HASH MISMATCH ثبت شد (§18) |

## نتیجه اجرا

| معیار | مقدار |
|-------|-------|
| exit code | 0 |
| classes loaded | 12,544 (5 DEX) |
| non-white pixels | 41,233 / 2,073,600 (1.99%) |
| trace events | 12,582 |
| errors | 0 |
| determinism | 3/3 identical SHA |
| RLottie pending views | 7 شناسایی‌شده |

## ساختار پیشنهادی فیلد برای هر ورودی corpus (per §7 charter)

```
name, version, package, source_url, source_repo, source_sha, apk_sha256,
size, dex_count, depth(L0-L10), first_divergence, first_failure,
screenshot_sha, run_count, deterministic(bool), notes
```

## گزارش صادقانه وضعیت قبلی (طبق §18)

- ادعای «100+ corpus» در اسناد قبلی هست ولی registry کاملش در clone نیست
  → شمارش فعلی قابل راستی‌آزمایی: **manifest entries محدود + 4 مورد**
  (`tests/corpus/apks.json`) + نتایج OA_API_MAP (8 app). وضعیت کلی:
  **UNKNOWN ≥ 8**، نه PASS.
- اولویت بعدی: آپلود CSV/JSON کامل نتایج corpus به `tests/corpus/results/`.
