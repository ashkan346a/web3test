# Railway Deployment Fix - Updated v2

## مشکلات برطرف شده:

### 1. Health Check های چندگانه
- `/health/` - Ultra basic health check (فقط "OK" برمی‌گرداند)
- `/health/simple/` - JSON health check ساده
- `/health/detailed/` - Health check کامل با جزئیات database

### 2. Startup Process محکم‌تر
- Django setup verification قبل از startup
- انتظار محدود برای database (15 attempt)
- Non-blocking database check
- Detailed logging در startup

### 3. Server Options
- Default: Daphne (ASGI/WebSocket support)
- Fallback: Gunicorn (تنظیم `USE_GUNICORN=true`)
- ASGI fallback در صورت مشکل channels

### 4. فایل‌های بهبود یافته:

#### `Dockerfile`:
- استفاده از entrypoint script
- Static files collection در build time
- Non-root user security

#### `entrypoint.sh`:
- Enhanced logging و monitoring
- Smart database wait strategy
- Flexible server selection

#### `pharma_web/asgi.py`:
- Fallback mechanism برای channels
- Error handling بهتر

#### `pharma_web/urls.py`:
- سه سطح health check
- Ultra-simple `/health/` endpoint

## مراحل Deploy:

### 1. Push تغییرات:
```bash
git add .
git commit -m "Fix Railway deployment - improved health check and startup process"
git push origin main
```

### 2. Railway Environment Variables:
مطمئن شوید این متغیرها در Railway تنظیم شده‌اند:
- `DATABASE_URL` (خودکار تنظیم می‌شود)
- `SECRET_KEY`
- `RAILWAY_ENVIRONMENT_NAME=production`
- `DEBUG=False`
- `PORT` (خودکار تنظیم می‌شود)

### 3. Monitor Deployment:
- لاگ‌های deployment را در Railway dashboard نظارت کنید
- health check در `/health/` باید پاسخ بدهد
- اگر همچنان مشکل داشت، `/health/detailed/` را چک کنید

## تست محلی:
```bash
# تست Django startup
python test_startup.py

# تست health endpoints
curl http://localhost:8000/health/
curl http://localhost:8000/health/detailed/
```

## Notes:
- Health check حالا non-blocking است برای database
- Startup process منتظر می‌ماند تا database آماده شود
- Static files در build time جمع‌آوری می‌شوند
- Error handling بهتر برای production

## اگر همچنان مشکل دارید:
1. لاگ‌های Railway را بررسی کنید
2. متغیرهای محیطی را چک کنید
3. از `/health/detailed/` برای دیاگ استفاده کنید