# Redis Caching Implementation Guide

## 📋 Overview
This document outlines the Redis caching implementation for the pharmacy web application using django-redis.

## 🛠️ Implementation Details

### 1. Dependencies
- `django-redis==5.4.0` added to requirements.txt
- Redis server (configured via REDIS_URL environment variable)

### 2. Settings Configuration
```python
# Redis cache configuration in settings.py
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }
    
    # Store sessions in Redis for better performance
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
```

### 3. View-Level Caching
The `buy_medicine` view is cached using `@cache_page(60 * 10)` decorator:
- Cache duration: 10 minutes
- Automatically handles different URL parameters
- Significantly reduces server load for medicine listing

### 4. Low-Level Caching
#### Medicine Groups Cache
- **Key**: `medicines:groups:all`
- **Duration**: 5 minutes (300 seconds)
- **Function**: `get_cached_medicine_groups()`
- **Purpose**: Cache expensive JSON processing operations

#### Cache Keys Used
- `medicines:groups:all` - All medicine groups and variants
- `medicines:list:top200` - Top 200 medicines for listings

### 5. Template Fragment Caching
Categories section cached with:
```django
{% cache 600 medicine_categories_fragment lang %}
<!-- Heavy HTML rendering -->
{% endcache %}
```

### 6. Cache Management Commands

#### Clear Cache
```bash
python manage.py clear_cache                # Clear medicine cache
python manage.py clear_cache --medicines    # Clear medicine cache only
python manage.py clear_cache --all         # Clear all cache
```

#### Warm Cache
```bash
python manage.py warm_cache_medicines       # Pre-load medicine data
```

## 🧪 Testing

### Manual Testing
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set("test-cache", "ok", 30)
>>> cache.get("test-cache")  # Should return "ok"
```

### Automated Testing
```bash
python test_redis_cache.py
```

## 🚀 Performance Benefits

### Before Caching
- JSON parsing on every request
- Heavy data processing for 2000+ medicine variants
- Repeated template rendering

### After Caching
- JSON data cached for 5 minutes
- Page-level caching for 10 minutes
- Template fragments cached for 10 minutes
- Sessions stored in Redis (faster than database)

## 📊 Expected Performance Improvements
- **Response Time**: 60-80% faster for medicine listing pages
- **Server Load**: 70% reduction in CPU usage for cached requests
- **Memory Usage**: More efficient memory usage with Redis
- **Database Load**: Reduced database queries for sessions

## 🔧 Cache Invalidation Strategy

### Automatic Invalidation
- Time-based expiration (5-10 minutes)
- Cache keys designed to avoid conflicts

### Manual Invalidation
```python
from core.views import clear_medicine_cache
clear_medicine_cache()  # Clear medicine-related caches
```

### Deployment Invalidation
- Use management commands during deployment
- Consider warming cache after deployment

## 🛡️ Best Practices

### Do's
✅ Use descriptive cache keys with prefixes
✅ Set appropriate expiration times
✅ Monitor cache hit rates
✅ Clear cache during deployments when data changes
✅ Use template fragment caching for heavy HTML sections

### Don'ts
❌ Cache user-specific data without user ID in key
❌ Set cache duration too long for frequently changing data
❌ Cache QuerySets directly (serialize to dicts/lists)
❌ Forget to handle cache misses gracefully

## 🔍 Monitoring

### Cache Statistics
```python
from django_redis import get_redis_connection
r = get_redis_connection("default")
info = r.info()
print(f"Cache hit ratio: {info['keyspace_hits']/(info['keyspace_hits']+info['keyspace_misses'])}")
```

### Key Monitoring
```bash
# Redis CLI commands
redis-cli KEYS "medicines:*"        # List medicine cache keys
redis-cli TTL "medicines:groups:all" # Check expiration time
```

## 🚨 Troubleshooting

### Common Issues
1. **Cache not working**: Check REDIS_URL environment variable
2. **High memory usage**: Reduce cache duration or optimize data structure
3. **Stale data**: Implement proper cache invalidation
4. **Connection errors**: Verify Redis server is running and accessible

### Debug Mode
Set `DEBUG=True` to disable some caching behaviors during development.

## 📈 Production Considerations

### Railway Deployment
- Redis service automatically configured via REDIS_URL
- Monitor Redis memory usage in Railway dashboard
- Consider Redis persistence settings for production

### Scaling
- Redis can handle thousands of concurrent connections
- Consider Redis Cluster for very high traffic
- Monitor cache hit rates and adjust strategies accordingly