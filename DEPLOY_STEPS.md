# 🚀 مراحل مرحله‌به‌مرحله Deploy در Railway.com

## قدم 1: آماده‌سازی Repository

### ✅ چک کردن فایل‌های ضروری:
```bash
# در terminal پروژه:
ls -la
```

باید این فایل‌ها وجود داشته باشند:
- ✅ `requirements.txt`
- ✅ `railway.json`
- ✅ `manage.py`
- ✅ `Procfile` (اختیاری)

### 🔄 Push به GitHub:
```bash
git add .
git commit -m "Add SEO optimizations and Railway config"
git push origin main
```

## قدم 2: تنظیمات Railway.com

### 🌐 ایجاد پروژه جدید:
1. وارد [Railway.com](https://railway.app) شوید
2. **New Project** → **Deploy from GitHub repo**
3. Repository `djweb3.3` را انتخاب کنید
4. **Deploy Now** را کلیک کنید

### ⚙️ تنظیمات Environment Variables:

در قسمت **Variables** این مقادیر را **دقیقاً** اضافه کنید:

```bash
# 🔧 تنظیمات اصلی
DEBUG=False
DJANGO_SETTINGS_MODULE=pharma_web.settings
PYTHONPATH=/app

# 🔐 امنیت (مقادیر واقعی را جایگزین کنید)
DJANGO_SECRET_KEY=your-super-secure-secret-key-here-at-least-50-characters-long-and-random
DATABASE_URL=postgresql://postgres:password@localhost:5432/pharmaweb

# 🌐 SEO Settings
SITE_NAME=PharmaWeb
SITE_DESCRIPTION=فروشگاه آنلاین دارو و تجهیزات پزشکی - خرید امن با بهترین قیمت و ارسال سریع
SITE_KEYWORDS=دارو، تجهیزات پزشکی، فروشگاه آنلاین، بهداشت، سلامت، داروخانه آنلاین، PharmaWeb
SITE_URL=https://your-app-name.up.railway.app

# 📊 Analytics (بعداً تکمیل کنید)
GOOGLE_ANALYTICS_ID=
GOOGLE_SITE_VERIFICATION=
BING_SITE_VERIFICATION=
```

### 🗄️ اضافه کردن PostgreSQL Database:
1. در همان پروژه **Add Service** → **Database** → **PostgreSQL**
2. Railway به طور خودکار `DATABASE_URL` را تنظیم می‌کند

## قدم 3: تنظیمات Domain

### 🌍 Custom Domain (medpharmaweb.shop):
1. در Railway: **Settings** → **Domains**
2. **Custom Domain** را کلیک کنید
3. `medpharmaweb.shop` را وارد کنید
4. همچنین `www.medpharmaweb.shop` را اضافه کنید

### 🔧 تنظیمات DNS:
در پنل مدیریت دامنه خود:

```dns
Type: CNAME
Name: @
Value: your-app-name.up.railway.app

Type: CNAME
Name: www  
Value: your-app-name.up.railway.app
```

### 📝 بروزرسانی Environment Variables:
پس از تنظیم domain:
```bash
SITE_URL=https://medpharmaweb.shop
```

## قدم 4: تأیید Deploy

### ✅ چک کردن Deploy:
1. در Railway logs را مشاهده کنید
2. باید پیام‌های زیر را ببینید:
```
✅ Medicines.json loaded
✅ Collecting static files
✅ Running migrations
✅ Application started
```

### 🌐 تست سایت:
این URLها باید کار کنند:
- https://medpharmaweb.shop/
- https://medpharmaweb.shop/health/
- https://medpharmaweb.shop/sitemap.xml
- https://medpharmaweb.shop/robots.txt

## قدم 5: Google Search Console

### 📋 ثبت سایت:
1. بروید به [Google Search Console](https://search.google.com/search-console)
2. **Add Property** → **URL prefix**
3. `https://medpharmaweb.shop` را وارد کنید

### 🔍 Verification:
1. روش **HTML tag** را انتخاب کنید
2. کد مثل `google1234567890abcdef.html` را کپی کنید
3. کد را در Railway environment variable قرار دهید:
```bash
GOOGLE_SITE_VERIFICATION=google1234567890abcdef
```
4. Deploy را منتظر بمانید (5-10 دقیقه)
5. در Google Search Console روی **Verify** کلیک کنید

### 🗺️ Submit Sitemap:
1. در Google Search Console: **Sitemaps**
2. `sitemap.xml` را اضافه کنید
3. **Submit** کلیک کنید

## قدم 6: Google Analytics

### 📊 ایجاد Account:
1. بروید به [Google Analytics](https://analytics.google.com)
2. **Create Account**
3. Account Name: `PharmaWeb`
4. Property Name: `PharmaWeb Website`
5. Website URL: `https://medpharmaweb.shop`

### 🏷️ دریافت Tracking ID:
1. Measurement ID را کپی کنید (مثل `G-XXXXXXXXXX`)
2. در Railway environment variables:
```bash
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
```

## قدم 7: Bing Webmaster Tools

### 🔍 ثبت سایت:
1. بروید به [Bing Webmaster](https://www.bing.com/webmasters)
2. **Add Site** → `https://medpharmaweb.shop`
3. کد verification را دریافت کنید
4. در Railway:
```bash
BING_SITE_VERIFICATION=your-bing-code
```

## قدم 8: Final Check

### ✅ چک لیست نهایی:
- [ ] سایت روی https://medpharmaweb.shop قابل دسترسی است
- [ ] Health check: https://medpharmaweb.shop/health/ وضعیت 200 برمی‌گرداند
- [ ] Sitemap: https://medpharmaweb.shop/sitemap.xml کار می‌کند
- [ ] Google Search Console تأیید شده
- [ ] Google Analytics نصب شده
- [ ] Environment variables همه تنظیم شده‌اند

### 🚨 عیب‌یابی:
اگر مشکلی دارید:
1. Railway logs را بررسی کنید
2. Environment variables را چک کنید
3. Health endpoint را تست کنید
4. DNS propagation را بررسی کنید (تا 48 ساعت)

### 📞 دستورات مفید:
```bash
# مشاهده logs در Railway CLI
railway logs --follow

# تست health check محلی
curl https://medpharmaweb.shop/health/

# تست sitemap
curl https://medpharmaweb.shop/sitemap.xml
```

---

## 🎉 تبریک! 

سایت شما حالا کاملاً SEO optimized و آماده دیده شدن در گوگل است!

**مراحل بعدی:**
1. صبر کنید 24-48 ساعت تا indexing شروع شود
2. محتوای بیشتری اضافه کنید
3. کیفیت تصاویر را بهبود دهید
4. Performance را بهینه کنید

**برای پشتیبانی بیشتر، فایل `RAILWAY_SEO_SETUP.md` را مطالعه کنید.**