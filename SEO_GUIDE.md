# راهنمای SEO برای PharmaWeb

این راهنما شامل تمام بهینه‌سازی‌های انجام شده برای بهبود SEO سایت است.

## ✅ موارد پیاده سازی شده

### 1. Meta Tags و Open Graph
- عناوین بهینه شده برای هر صفحه
- توضیحات منحصر به فرد
- کلمات کلیدی مناسب
- Open Graph برای شبکه‌های اجتماعی
- Twitter Cards
- Canonical URLs

### 2. Structured Data (JSON-LD)
- Schema.org markup برای:
  - Website
  - OnlineStore
  - Product
  - Organization

### 3. Sitemap XML
- سه نوع sitemap:
  - Static pages sitemap
  - Medicine categories sitemap
  - Individual medicines sitemap
- خودکار و دینامیک

### 4. فایل‌های مهم SEO
- `robots.txt` - راهنمای ربات‌های جستجو
- `security.txt` - اطلاعات امنیتی
- `humans.txt` - اطلاعات تیم توسعه

### 5. Performance و Security
- HTTPS enforcement
- Security headers
- Caching headers
- HSTS headers

### 6. URLs دوستدار SEO
- Canonical URLs
- Clean URL structure
- Proper redirects

## 🔧 نحوه استفاده

### مشاهده Sitemap
```
https://medpharmaweb.shop/sitemap.xml
```

### ارسال Sitemap به موتورهای جستجو
```bash
python manage.py submit_sitemap --ping-google --submit-bing
```

### بررسی robots.txt
```
https://medpharmaweb.shop/robots.txt
```

## 📊 ابزارهای مفید برای بررسی SEO

### Google Tools
1. [Google Search Console](https://search.google.com/search-console)
2. [Google PageSpeed Insights](https://pagespeed.web.dev/)
3. [Rich Results Test](https://search.google.com/test/rich-results)

### سایر ابزارها
1. [Bing Webmaster Tools](https://www.bing.com/webmasters)
2. [Schema.org Validator](https://validator.schema.org/)
3. [Open Graph Debugger](https://developers.facebook.com/tools/debug/)

## 🎯 مراحل بعدی (پیشنهادی)

1. **تصاویر بهینه شده**: اضافه کردن alt text و تصاویر WebP
2. **سرعت**: بهینه‌سازی بیشتر loading times
3. **محتوا**: اضافه کردن blog یا صفحات محتوایی
4. **Internal Linking**: بهبود لینک‌های داخلی
5. **Mobile Optimization**: بهینه‌سازی برای موبایل
6. **Analytics**: نصب Google Analytics 4

## 🔍 بررسی وضعیت فعلی

### چک لیست SEO
- [x] Meta tags
- [x] Open Graph
- [x] Structured Data
- [x] Sitemap XML
- [x] Robots.txt
- [x] Security headers
- [x] HTTPS
- [ ] Google Analytics
- [ ] Search Console verification
- [ ] Page speed optimization
- [ ] Image optimization

## 📞 پشتیبانی

برای سوالات SEO با تیم توسعه تماس بگیرید.