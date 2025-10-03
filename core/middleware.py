from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import HttpResponse


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware to handle health check requests directly
    without going through CommonMiddleware which causes redirects
    """
    
    def process_request(self, request):
        """Process health check requests directly"""
        if request.path_info == '/health' or request.path_info == '/health/':
            return HttpResponse("OK", content_type="text/plain", status=200)
            
        # Handle other health check endpoints
        if request.path_info.startswith('/health/'):
            return None  # Let them pass through to normal views
        
        # Handle favicon.ico to prevent 301 redirects 
        if request.path_info == '/favicon.ico':
            try:
                from django.conf import settings
                with open(settings.BASE_DIR / 'core' / 'static' / 'favicon.svg', 'rb') as f:
                    return HttpResponse(f.read(), content_type='image/svg+xml')
            except FileNotFoundError:
                try:
                    with open(settings.BASE_DIR / 'core' / 'static' / 'favicon.png', 'rb') as f:
                        return HttpResponse(f.read(), content_type='image/png')
                except FileNotFoundError:
                    return HttpResponse("", status=404)
        
        return None

class SEOMiddleware(MiddlewareMixin):
    """
    Middleware to add SEO-friendly headers to responses
    """
    
    def process_response(self, request, response):
        # Add security headers
        if not settings.DEBUG:
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add caching headers for static content
        if request.path.startswith('/static/') or request.path.endswith('.css') or request.path.endswith('.js'):
            response['Cache-Control'] = 'public, max-age=31536000'  # 1 year
        
        # Add no-cache headers for user-specific pages
        no_cache_paths = ['/profile/', '/cart/', '/checkout/', '/admin/']
        if any(request.path.startswith(path) for path in no_cache_paths):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            # Reduce crawl waste: don't index these user-specific pages
            response['X-Robots-Tag'] = 'noindex, nofollow, nosnippet'
        
        # Avoid indexing internal API endpoints by default
        if request.path.startswith('/api/'):
            response['X-Robots-Tag'] = 'noindex, nofollow'
        
        return response