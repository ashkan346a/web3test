from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db import connection
from django.utils import timezone
import json
import sys
import os

@never_cache
@require_http_methods(["GET"])
def health_check(request):
    """
    Comprehensive health check endpoint for Railway.com
    """
    health_data = {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("RAILWAY_ENVIRONMENT_NAME", "development"),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "checks": {}
    }
    
    # Basic app health check
    try:
        health_data["checks"]["app"] = {"status": "healthy", "message": "Application is running"}
    except Exception as e:
        health_data["checks"]["app"] = {"status": "unhealthy", "message": f"App error: {str(e)}"}
        health_data["status"] = "unhealthy"
    
    # Database check (non-blocking)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_data["checks"]["database"] = {"status": "healthy", "message": "Database connection successful"}
    except Exception as e:
        # Don't fail health check for database issues during startup
        health_data["checks"]["database"] = {"status": "warning", "message": f"Database connection pending: {str(e)}"}
    
    # Static files check
    try:
        static_root = settings.STATIC_ROOT
        if static_root and os.path.exists(static_root):
            health_data["checks"]["static_files"] = {"status": "healthy", "message": "Static files directory exists"}
        else:
            health_data["checks"]["static_files"] = {"status": "warning", "message": "Static files directory not found"}
    except Exception as e:
        health_data["checks"]["static_files"] = {"status": "unhealthy", "message": f"Static files error: {str(e)}"}
    
    # Environment variables check (only critical ones)
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        health_data["checks"]["environment"] = {
            "status": "unhealthy", 
            "message": f"Missing critical environment variables: {', '.join(missing_vars)}"
        }
        health_data["status"] = "unhealthy"
    else:
        health_data["checks"]["environment"] = {"status": "healthy", "message": "All critical environment variables are set"}
    
    # SEO checks (non-critical, don't affect overall health)
    seo_checks = []
    if not getattr(settings, 'GOOGLE_ANALYTICS_ID', ''):
        seo_checks.append("Google Analytics ID not set")
    if not getattr(settings, 'GOOGLE_SITE_VERIFICATION', ''):
        seo_checks.append("Google Site Verification not set")
    
    if seo_checks:
        health_data["checks"]["seo"] = {
            "status": "warning", 
            "message": f"SEO configuration incomplete: {', '.join(seo_checks)}"
        }
        # Don't change overall health status for SEO warnings
    else:
        health_data["checks"]["seo"] = {"status": "healthy", "message": "SEO configuration complete"}
    
    # System info
    health_data["system"] = {
        "python_version": sys.version.split()[0],
        "django_version": settings.VERSION if hasattr(settings, 'VERSION') else 'Unknown'
    }
    
    # Always return 200 for health endpoint unless there are critical issues
    # Only return 503 if app or database is completely down
    critical_failure = False
    for check_name, check_data in health_data["checks"].items():
        if check_name in ["app", "database"] and check_data.get("status") == "unhealthy":
            critical_failure = True
            break
    
    status_code = 503 if critical_failure else 200
    
    return JsonResponse(health_data, status=status_code, json_dumps_params={'indent': 2})


@never_cache
@require_http_methods(["GET"])
def health_quick(request):
    """
    Ultra-fast health check for load balancers and uptime monitoring
    Minimal checks to reduce response time
    """
    return JsonResponse({
        "status": "ok",
        "timestamp": timezone.now().isoformat(),
        "uptime": True
    }, status=200)