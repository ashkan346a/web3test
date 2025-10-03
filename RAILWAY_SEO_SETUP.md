# 🚂 راهنمای کامل تنظیمات Railway.com برای SEO

## مرحله 1: تنظیمات Environment Variables در Railway

وارد پنل Railway.com شوید و در بخش **Variables** این مقادیر را اضافه کنید:

### 🔧 متغیرهای اصلی:
```
DEBUG=False
DJANGO_SETTINGS_MODULE=pharma_web.settings
PYTHONPATH=/app
```

### 🌐 تنظیمات SEO:
```
SITE_NAME=PharmaWeb
SITE_DESCRIPTION=فروشگاه آنلاین دارو و تجهیزات پزشکی - خرید امن با بهترین قیمت
SITE_KEYWORDS=دارو، تجهیزات پزشکی، فروشگاه آنلاین، بهداشت، سلامت، داروخانه آنلاین
SITE_URL=https://medpharmaweb.shop
```

### 📊 Google Analytics & Search Console:
```
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
GOOGLE_SITE_VERIFICATION=your-google-verification-code
BING_SITE_VERIFICATION=your-bing-verification-code
```

### 🔐 امنیت:
```
DJANGO_SECRET_KEY=your-super-secure-secret-key-here
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

## مرحله 2: Domain Configuration

### ✅ تنظیم Custom Domain:
1. در Railway.com، بخش **Settings** → **Domains**
2. **Custom Domain** را کلیک کنید
3. دامنه `medpharmaweb.shop` را اضافه کنید
4. DNS records را در provider دامنه تنظیم کنید:

```
Type: CNAME
Name: @
Value: your-app.up.railway.app

Type: CNAME  
Name: www
Value: your-app.up.railway.app
```

### 🔒 SSL Certificate:
Railway به طور خودکار SSL certificate ایجاد می‌کند.

## مرحله 3: تنظیمات Deploy

### 🚀 Build Command:
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

### ▶️ Start Command:
```bash
python manage.py migrate --noinput && gunicorn pharma_web.wsgi:application --bind 0.0.0.0:$PORT
```

## مرحله 4: پس از Deploy

### 1. Google Search Console:
1. بروید به [Google Search Console](https://search.google.com/search-console)
2. **Add Property** → **URL prefix**
3. `https://medpharmaweb.shop` را وارد کنید
4. از روش **HTML tag** استفاده کنید
5. کد verification را در `GOOGLE_SITE_VERIFICATION` قرار دهید
6. پس از تأیید، Sitemap را submit کنید: `https://medpharmaweb.shop/sitemap.xml`

### 2. Google Analytics:
1. بروید به [Google Analytics](https://analytics.google.com)
2. **Create Account** → **Create Property**
3. نام: `PharmaWeb`
4. Website URL: `https://medpharmaweb.shop`
5. **Measurement ID** (G-XXXXXXXXXX) را کپی کنید
6. در Railway variables قرار دهید: `GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX`

### 3. Bing Webmaster Tools:
1. بروید به [Bing Webmaster](https://www.bing.com/webmasters)
2. **Add Site** → `https://medpharmaweb.shop`
3. کد verification را دریافت کنید
4. در Railway قرار دهید: `BING_SITE_VERIFICATION=your-code`

## مرحله 5: تست عملکرد SEO

### 🔍 URLs مهم برای تست:
- **Sitemap**: https://medpharmaweb.shop/sitemap.xml
- **Robots**: https://medpharmaweb.shop/robots.txt
- **Security**: https://medpharmaweb.shop/.well-known/security.txt

### 🛠️ ابزارهای تست:
1. [Google PageSpeed Insights](https://pagespeed.web.dev/)
2. [Google Rich Results Test](https://search.google.com/test/rich-results)
3. [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)

## مرحله 6: مانیتورینگ

### 📈 Railway Logs:
در Railway dashboard می‌توانید logs را مشاهده کنید:
```bash
# برای مشاهده logs آنلاین:
railway logs --follow
```

### 🚨 Health Check:
Railway به طور خودکار سلامت اپلیکیشن را بررسی می‌کند.

## مرحله 7: بهینه‌سازی بیشتر

### ⚡ Performance:
1. **Static Files**: Railway از CDN استفاده می‌کند
2. **Compression**: در settings.py فعال شده
3. **Caching**: Redis cache اضافه کنید (اختیاری)

### 🔧 Commands مفید:
```bash
# Submit sitemap manually
railway run python manage.py submit_sitemap --ping-google

# Check site health  
railway run python manage.py check --deploy

# View site statistics
railway run python manage.py shell -c "from django.contrib.auth import get_user_model; print(f'Users: {get_user_model().objects.count()}')"
```

## ❗ نکات مهم:

1. **Environment Variables**: همیشه sensitive data را در environment variables قرار دهید
2. **Static Files**: برای production از CDN استفاده کنید
3. **Database**: بدون backup تغییری ندهید
4. **Monitoring**: Google Search Console را روزانه بررسی کنید
5. **Updates**: هر تغییری را ابتدا در development تست کنید

## 🆘 در صورت مشکل:

1. Railway logs را بررسی کنید
2. Environment variables را چک کنید  
3. Health check endpoint را تست کنید
4. DNS propagation را بررسی کنید (24-48 ساعت طول می‌کشد)

---

**✅ پس از انجام این مراحل، سایت شما کاملاً آماده SEO و دیده شدن در گوگل خواهد بود!**