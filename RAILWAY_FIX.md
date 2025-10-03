# مراحل رفع خطای Railway Build

## 🚨 خطای فعلی:
```
ERROR: Could not find a version that satisfies the requirement django-sitemap>=0.3.0
```

## ✅ راه حل:

### 1. پکیج اشتباه حذف شد:
- `django-sitemap` پکیج معتبری نیست
- Django به طور پیش‌فرض sitemap دارد (`django.contrib.sitemaps`)

### 2. فایل requirements.txt اصلاح شد:
✅ پکیج `django-sitemap` حذف شد
✅ تکراری‌ها بررسی شد

### 3. فایل railway.json بهینه شد:
- `pip install --upgrade pip` اضافه شد
- Health check path به `/health/` تغییر کرد
- Start command بهینه شد

## 🚀 مراحل Deploy مجدد:

### قدم 1: Push تغییرات
```bash
git add .
git commit -m "Fix Railway build: remove invalid django-sitemap package"
git push origin main
```

### قدم 2: Re-deploy در Railway
- Railway به طور خودکار build مجدد می‌کند
- یا می‌توانید در dashboard روی "Redeploy" کلیک کنید

### قدم 3: مانیتور کردن build
Build باید موفقیت‌آمیز باشد و این پیام‌ها را ببینید:
```
✅ Successfully installed Django-5.1
✅ Successfully installed daphne-4.1.2
✅ Build completed successfully
```

## 🔍 اگر هنوز مشکل دارید:

### بررسی Python version:
Railway معمولاً Python 3.11 استفاده می‌کند. اگر مشکل دارید، این فایل را ایجاد کنید:

**runtime.txt:**
```
python-3.11
```

### حذف پکیج‌های غیرضروری (در صورت نیاز):
اگر هنوز مشکل دارید، این پکیج‌ها را موقتاً کامنت کنید:
```
# web3==6.20.1
# tronpy==0.5.0
# pandas==2.2.2
```

## ✅ تست نهایی:
پس از deploy موفق، این URLها را تست کنید:
- `/health/` - باید status 200 برگرداند
- `/sitemap.xml` - باید sitemap XML نمایش دهد
- `/robots.txt` - باید محتوای robots نمایش دهد