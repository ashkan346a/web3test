"""
Performance optimization middleware for better Google crawling
"""
import time
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.conf import settings


class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware to optimize performance for search engines
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Start timing the request
        """
        request._start_time = time.time()
        
        # Quick responses for common bot requests
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Fast response for health checks
        if request.path in ['/health', '/health/', '/health/quick/']:
            return HttpResponse("OK", content_type="text/plain")
            
        # Skip processing for certain static files
        if request.path.endswith(('.css', '.js', '.png', '.jpg', '.svg', '.ico')):
            return None
            
        return None
    
    def process_response(self, request, response):
        """
        Add performance headers
        """
        # Calculate request duration
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        # Add caching headers for static content
        if request.path.startswith('/static/') or request.path in ['/robots.txt', '/sitemap.xml']:
            response['Cache-Control'] = 'public, max-age=86400'
        
        # Add SEO-friendly headers
        if response.status_code == 200:
            # Tell search engines this is a valid page
            response['X-Robots-Tag'] = 'index, follow'
            
        # Compress responses for better performance
        if not getattr(settings, 'DEBUG', False):
            response['Vary'] = 'Accept-Encoding'
            
        return response


class SEOMiddleware(MiddlewareMixin):
    """
    Middleware to enhance SEO aspects
    """
    
    def process_response(self, request, response):
        """
        Add SEO-related headers
        """
        # Add canonical header for duplicate content prevention
        if response.status_code == 200 and request.method == 'GET':
            canonical_url = request.build_absolute_uri(request.path)
            response['Link'] = f'<{canonical_url}>; rel="canonical"'
        
        # Add structured data hint
        if 'text/html' in response.get('Content-Type', ''):
            response['X-Content-Type-Options'] = 'nosniff'
            
        return response