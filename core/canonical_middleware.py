"""
Canonical Domain Middleware
Forces redirect from Railway domain to canonical domain for SEO
"""
from django.shortcuts import redirect
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CanonicalDomainMiddleware(MiddlewareMixin):
    """
    Redirects requests from Railway domain to canonical domain
    This fixes the Google Search Console duplicate canonical URL issue
    """
    
    def process_request(self, request):
        # Skip if not GET request
        if request.method != 'GET':
            return None
            
        # Get current host
        try:
            current_host = request.get_host()
        except:
            return None
            
        # Skip for development and test environments
        if (current_host in ['testserver', '127.0.0.1', 'localhost'] or
            current_host.startswith(('testserver', '127.0.0.1:', 'localhost:')) or
            settings.DEBUG):
            return None
            
        # Get canonical domain from settings
        canonical_domain = getattr(settings, 'CANONICAL_DOMAIN', None)
        if not canonical_domain:
            return None
            
        # List of Railway domains to redirect from
        railway_domains = [
            'pharmaweb.up.railway.app',
            'djweb3-3-production.up.railway.app',
        ]
        
        # Only redirect if current host is a Railway domain that's different from canonical
        if current_host in railway_domains and current_host != canonical_domain:
            # Build canonical URL
            canonical_url = f"https://{canonical_domain}{request.get_full_path()}"
            # Return permanent redirect (301)
            return redirect(canonical_url, permanent=True)
            
        return None