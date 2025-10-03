# Google Search Console Verification

برای تأیید مالکیت سایت در Google Search Console، می‌توانید از یکی از روش‌های زیر استفاده کنید:

## 1. HTML Tag Method
این کد را در بخش `<head>` فایل `base.html` اضافه کنید:
```html
<meta name="google-site-verification" content="YOUR-VERIFICATION-CODE" />
```

## 2. HTML File Method  
فایل HTML با نام مشخص شده توسط گوگل را در root directory قرار دهید.

## 3. DNS Method
یک رکورد TXT در DNS تنظیمات دامنه خود اضافه کنید.

## مراحل:
1. به [Google Search Console](https://search.google.com/search-console) بروید
2. سایت خود را اضافه کنید: `https://medpharmaweb.shop`
3. روش verification را انتخاب کنید
4. کد یا فایل را اضافه کنید
5. verify کلیک کنید

## پس از verification:
- Sitemap را submit کنید: `https://medpharmaweb.shop/sitemap.xml`
- Index coverage را بررسی کنید
- Performance reports را مشاهده کنید