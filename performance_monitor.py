"""
Performance Monitor for Django Pharmacy Website
مانیتورینگ عملکرد و آمار سیستم
"""

import os
import time
import django
import psutil
from django.core.cache import cache
from django.db import connection
from django.conf import settings

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharma_web.settings')
django.setup()

def get_system_stats():
    """آمار سیستم"""
    try:
        # CPU و Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_used': memory.used,
            'memory_total': memory.total,
            'memory_percent': memory.percent,
            'disk_used': disk.used,
            'disk_total': disk.total,
            'disk_percent': (disk.used / disk.total) * 100
        }
    except:
        return None

def test_database_performance():
    """تست سرعت Database"""
    try:
        # تست ساده
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_content_type")
            result = cursor.fetchone()
        db_time = time.time() - start_time
        
        return {
            'db_query_time': db_time,
            'db_status': 'OK',
            'tables_count': result[0] if result else 0
        }
    except Exception as e:
        return {
            'db_query_time': 0,
            'db_status': f'Error: {str(e)}',
            'tables_count': 0
        }

def test_cache_performance():
    """تست سرعت Cache"""
    try:
        # تست Write
        start_time = time.time()
        test_data = "x" * 1000  # 1KB data
        cache.set('perf_test_write', test_data, 300)
        write_time = time.time() - start_time
        
        # تست Read
        start_time = time.time()
        retrieved_data = cache.get('perf_test_write')
        read_time = time.time() - start_time
        
        # پاک کردن
        cache.delete('perf_test_write')
        
        return {
            'cache_write_time': write_time,
            'cache_read_time': read_time,
            'cache_status': 'OK' if retrieved_data == test_data else 'FAILED',
            'data_integrity': retrieved_data == test_data
        }
    except Exception as e:
        return {
            'cache_write_time': 0,
            'cache_read_time': 0,
            'cache_status': f'Error: {str(e)}',
            'data_integrity': False
        }

def get_cache_stats():
    """آمار Cache"""
    try:
        from django_redis import get_redis_connection
        
        redis_conn = get_redis_connection("default")
        info = redis_conn.info()
        
        return {
            'redis_version': info.get('redis_version', 'Unknown'),
            'used_memory': info.get('used_memory_human', 'Unknown'),
            'connected_clients': info.get('connected_clients', 0),
            'total_commands_processed': info.get('total_commands_processed', 0),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
        }
    except:
        return {'status': 'Redis not available'}

def benchmark_page_load():
    """شبیه‌سازی سرعت لود صفحه"""
    try:
        # شبیه‌سازی بدون Cache
        start_time = time.time()
        
        # شبیه‌سازی queries مختلف
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_content_type")
            cursor.execute("SELECT COUNT(*) FROM auth_permission")
        
        no_cache_time = time.time() - start_time
        
        # شبیه‌سازی با Cache
        start_time = time.time()
        
        # بررسی cache
        cached_result = cache.get('page_benchmark')
        if not cached_result:
            cached_result = {'content_types': 10, 'permissions': 50}
            cache.set('page_benchmark', cached_result, 300)
        
        cache_time = time.time() - start_time
        
        speedup = no_cache_time / cache_time if cache_time > 0 else 0
        
        return {
            'no_cache_time': no_cache_time,
            'cache_time': cache_time,
            'speedup': speedup,
            'cache_efficiency': ((no_cache_time - cache_time) / no_cache_time) * 100 if no_cache_time > 0 else 0
        }
    except Exception as e:
        return {'error': str(e)}

def display_performance_report():
    """نمایش گزارش کامل عملکرد"""
    print("🚀 Django Pharmacy Performance Monitor")
    print("=" * 60)
    
    # System Stats
    print("\n💻 System Resources:")
    system_stats = get_system_stats()
    if system_stats:
        print(f"   CPU Usage: {system_stats['cpu_percent']:.1f}%")
        print(f"   Memory: {system_stats['memory_percent']:.1f}% ({system_stats['memory_used']//1024//1024} MB / {system_stats['memory_total']//1024//1024} MB)")
        print(f"   Disk: {system_stats['disk_percent']:.1f}% ({system_stats['disk_used']//1024//1024//1024} GB / {system_stats['disk_total']//1024//1024//1024} GB)")
    else:
        print("   ⚠️ System stats not available")
    
    # Database Performance
    print("\n🗄️ Database Performance:")
    db_stats = test_database_performance()
    print(f"   Query Time: {db_stats['db_query_time']:.4f} seconds")
    print(f"   Status: {db_stats['db_status']}")
    print(f"   Tables: {db_stats['tables_count']}")
    
    # Cache Performance
    print("\n🚀 Cache Performance:")
    cache_stats = test_cache_performance()
    print(f"   Write Time: {cache_stats['cache_write_time']:.4f} seconds")
    print(f"   Read Time: {cache_stats['cache_read_time']:.4f} seconds")
    print(f"   Status: {cache_stats['cache_status']}")
    print(f"   Data Integrity: {'✅' if cache_stats['data_integrity'] else '❌'}")
    
    # Redis Stats
    print("\n📊 Redis Statistics:")
    redis_stats = get_cache_stats()
    if 'status' not in redis_stats:
        print(f"   Version: {redis_stats['redis_version']}")
        print(f"   Memory Used: {redis_stats['used_memory']}")
        print(f"   Connected Clients: {redis_stats['connected_clients']}")
        print(f"   Commands Processed: {redis_stats['total_commands_processed']:,}")
        
        # محاسبه hit rate
        hits = redis_stats.get('keyspace_hits', 0)
        misses = redis_stats.get('keyspace_misses', 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        print(f"   Hit Rate: {hit_rate:.1f}% ({hits:,} hits, {misses:,} misses)")
    else:
        print(f"   {redis_stats['status']}")
    
    # Page Load Benchmark
    print("\n⚡ Page Load Performance:")
    benchmark = benchmark_page_load()
    if 'error' not in benchmark:
        print(f"   Without Cache: {benchmark['no_cache_time']:.4f} seconds")
        print(f"   With Cache: {benchmark['cache_time']:.4f} seconds")
        print(f"   Speedup: {benchmark['speedup']:.1f}x faster")
        print(f"   Cache Efficiency: {benchmark['cache_efficiency']:.1f}%")
    else:
        print(f"   Error: {benchmark['error']}")
    
    # Configuration Info
    print("\n⚙️ Configuration:")
    print(f"   Debug Mode: {'ON' if settings.DEBUG else 'OFF'}")
    print(f"   Database: {settings.DATABASES['default']['ENGINE'].split('.')[-1]}")
    
    if hasattr(settings, 'CACHES') and 'default' in settings.CACHES:
        cache_backend = settings.CACHES['default']['BACKEND'].split('.')[-1]
        print(f"   Cache Backend: {cache_backend}")
        
        if 'LOCATION' in settings.CACHES['default']:
            location = settings.CACHES['default']['LOCATION']
            if isinstance(location, str) and location.startswith('redis://'):
                print(f"   Redis URL: {location[:20]}...")
    
    print("\n" + "=" * 60)
    print("✅ Performance monitoring completed!")

if __name__ == "__main__":
    display_performance_report()