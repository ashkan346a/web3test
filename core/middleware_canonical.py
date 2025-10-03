"""
Middleware to force canonical domain redirects
This ensures all traffic goes to the main domain and prevents duplicate content issues
"""
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin


class CanonicalDomainMiddleware(MiddlewareMixin):
    """
    Force redirect from Railway domain to canonical domain
    This prevents Google from indexing both domains
    """
    
    def process_request(self, request):
        # Skip redirects for health checks
        if request.path.startswith('/health'):
            return None
            
        try:
            current_host = request.get_host()
        except Exception:
            # Skip for test environments or invalid hosts
            return None
            
        # Skip for test environments and localhost
        if current_host in ['testserver', 'localhost', '127.0.0.1']:
            return None
            
        # Skip for internal Railway requests
        if 'railway.internal' in current_host:
            return None
            
        # Get the canonical domain
        canonical_domain = getattr(settings, 'CANONICAL_DOMAIN', 'medpharmaweb.shop')
        
        # Force redirect from old Railway domain to new domain
        if current_host == 'pharmaweb.up.railway.app':
            canonical_url = f"https://{canonical_domain}{request.get_full_path()}"
            return HttpResponsePermanentRedirect(canonical_url)
            
        # Force redirect from www to non-www (or vice versa)
        if current_host == f'www.{canonical_domain}':
            canonical_url = f"https://{canonical_domain}{request.get_full_path()}"
            return HttpResponsePermanentRedirect(canonical_url)
            
        return None