from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticViewSitemap, MedicineCategorySitemap, MedicineDetailSitemap
from core.seo_views import robots_txt, security_txt, humans_txt, structured_data_view
from core.health_views import health_check, health_quick
from django.http import JsonResponse, HttpResponse

def simple_health(request):
    """Simple health check for Railway startup"""
    return JsonResponse({"status": "ok", "message": "Service is running"})

def basic_health(request):
    """Ultra basic health check - just returns OK"""
    return HttpResponse("OK", content_type="text/plain")

@cache_control(max_age=604800, immutable=True, public=True)
@require_http_methods(["GET"])
def favicon_view(request):
    try:
        with open(settings.BASE_DIR / 'core' / 'static' / 'favicon.svg', 'rb') as f:
            return HttpResponse(f.read(), content_type='image/svg+xml')
    except FileNotFoundError:
        # Fallback to PNG if SVG not found
        try:
            with open(settings.BASE_DIR / 'core' / 'static' / 'favicon.png', 'rb') as f:
                return HttpResponse(f.read(), content_type='image/png')
        except FileNotFoundError:
            return HttpResponse("", status=404)

@cache_control(max_age=604800, immutable=True, public=True)
@require_http_methods(["GET"])
def manifest_view(request):
    try:
        with open(settings.BASE_DIR / 'core' / 'static' / 'pharma-manifest.json', 'rb') as f:
            return HttpResponse(f.read(), content_type='application/json')
    except FileNotFoundError:
        return HttpResponse("{}", content_type='application/json', status=404)

@cache_control(max_age=604800, immutable=True, public=True)
@require_http_methods(["GET"])
def sw_view(request):
    try:
        with open(settings.BASE_DIR / 'core' / 'static' / 'pharma-sw.js', 'rb') as f:
            return HttpResponse(f.read(), content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse("// Service worker not found", content_type='application/javascript', status=404)

# Sitemaps configuration
sitemaps = {
    'static': StaticViewSitemap,
    'categories': MedicineCategorySitemap,
    'medicines': MedicineDetailSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('favicon.ico', favicon_view, name='favicon'),
    path('manifest.json', manifest_view, name='manifest'),
    path('sw.js', sw_view, name='service_worker'),
    
    # SEO URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    # Aliases in case someone submits wrong path
    path('sitemap', sitemap, {'sitemaps': sitemaps}, name='sitemap_plain'),
    path('sitemap/', sitemap, {'sitemaps': sitemaps}),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('.well-known/security.txt', security_txt, name='security_txt'),
    path('humans.txt', humans_txt, name='humans_txt'),
    path('structured-data.json', structured_data_view, name='structured_data'),
    
    # Health Check - Multiple patterns to handle Railway's exact requests
    path('health', basic_health, name='basic_health_no_slash'),
    path('health/', basic_health, name='basic_health'),
    path('health/quick/', health_quick, name='health_quick'),
    path('health/simple/', simple_health, name='simple_health'),
    path('health/detailed/', health_check, name='health_check'),
]

# Serve static and media files
if settings.DEBUG:
    # Development serving
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'core' / 'static')
    urlpatterns += static(settings.STATIC_URL + 'images/', document_root=settings.BASE_DIR / 'static' / 'images')
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Production - rely on WhiteNoise for static files, still need media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
