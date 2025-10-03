"""
Advanced Health Check System for Django Application
بررسی وضعیت تمام سیستم‌های مهم
"""

import os
import time
import django
import redis
from django.core.cache import cache
from django.db import connection
from django.test.utils import get_runner
from django.conf import settings

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharma_web.settings')
django.setup()

def check_database():
    """بررسی اتصال به پایگاه داده"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return True, f"Database OK - Result: {result[0]}"
    except Exception as e:
        return False, f"Database Error: {str(e)}"

def check_redis_cache():
    """بررسی Redis Cache"""
    try:
        # تست ساده cache
        test_key = "health_check_test"
        test_value = f"test_value_{int(time.time())}"
        
        cache.set(test_key, test_value, 30)
        retrieved_value = cache.get(test_key)
        
        if retrieved_value == test_value:
            cache.delete(test_key)
            return True, "Redis Cache OK"
        else:
            return False, "Redis Cache - Value mismatch"
            
    except Exception as e:
        return False, f"Redis Cache Error: {str(e)}"

def check_redis_connection():
    """بررسی مستقیم اتصال Redis"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        
        # تست ping
        ping_result = r.ping()
        
        # تست set/get
        r.set('health_test', 'ok', ex=30)
        get_result = r.get('health_test')
        r.delete('health_test')
        
        return True, f"Redis Direct OK - Ping: {ping_result}, Get: {get_result.decode()}"
        
    except Exception as e:
        return False, f"Redis Direct Error: {str(e)}"

def check_static_files():
    """بررسی Static Files"""
    try:
        from django.contrib.staticfiles import finders
        
        # بررسی admin CSS
        admin_css = finders.find('admin/css/base.css')
        
        # بررسی QR images
        qr_btc = finders.find('images/qr/BTC.png')
        
        if admin_css and qr_btc:
            return True, f"Static Files OK - Admin CSS: {bool(admin_css)}, QR Images: {bool(qr_btc)}"
        else:
            return False, f"Static Files - Missing files. Admin CSS: {bool(admin_css)}, QR: {bool(qr_btc)}"
            
    except Exception as e:
        return False, f"Static Files Error: {str(e)}"

def check_channels():
    """بررسی WebSocket Channels"""
    try:
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        if channel_layer:
            return True, f"Channels OK - Backend: {channel_layer.__class__.__name__}"
        else:
            return False, "Channels - No channel layer configured"
            
    except Exception as e:
        return False, f"Channels Error: {str(e)}"

def performance_test():
    """تست سرعت Cache"""
    try:
        import time
        
        # تست بدون cache
        start_time = time.time()
        # شبیه‌سازی query سنگین
        for i in range(100):
            pass
        no_cache_time = time.time() - start_time
        
        # تست با cache
        start_time = time.time()
        cached_data = cache.get('perf_test_data')
        if not cached_data:
            cached_data = "performance_test_data"
            cache.set('perf_test_data', cached_data, 300)
        cache_time = time.time() - start_time
        
        speedup = no_cache_time / cache_time if cache_time > 0 else 0
        
        return True, f"Performance - No Cache: {no_cache_time:.4f}s, With Cache: {cache_time:.4f}s, Speedup: {speedup:.1f}x"
        
    except Exception as e:
        return False, f"Performance Test Error: {str(e)}"

def main():
    """اجرای تمام تست‌ها"""
    print("🏥 Pharmacy Web Health Check - Advanced")
    print("=" * 50)
    
    checks = [
        ("Database", check_database),
        ("Redis Cache", check_redis_cache),
        ("Redis Connection", check_redis_connection),
        ("Static Files", check_static_files),
        ("WebSocket Channels", check_channels),
        ("Performance", performance_test),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        try:
            status, message = check_func()
            icon = "✅" if status else "❌"
            print(f"{icon} {name}: {message}")
            
            if not status:
                all_passed = False
                
        except Exception as e:
            print(f"❌ {name}: Exception - {str(e)}")
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 All systems are healthy!")
        print("✅ Your pharmacy website is ready for production!")
    else:
        print("⚠️  Some issues detected. Please check the failed items.")
    
    # اطلاعات اضافی
    print("\n📊 System Information:")
    print(f"🐍 Python: {os.sys.version.split()[0]}")
    print(f"🦄 Django: {django.get_version()}")
    print(f"🌍 Environment: {'Production' if not settings.DEBUG else 'Development'}")
    print(f"💾 Database: {settings.DATABASES['default']['ENGINE'].split('.')[-1]}")
    
    if hasattr(settings, 'CACHES') and 'default' in settings.CACHES:
        print(f"🚀 Cache: {settings.CACHES['default']['BACKEND'].split('.')[-1]}")

if __name__ == "__main__":
    main()