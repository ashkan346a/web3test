from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods
from django.template.response import TemplateResponse
from django.urls import reverse
from django.conf import settings
import json

@cache_control(max_age=86400)  # Cache for 24 hours
@require_http_methods(["GET"])
def robots_txt(request):
    """Generate robots.txt dynamically with Google-friendly settings"""
    host_url = f"{request.scheme}://{request.get_host()}"
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /chat/",
        "Disallow: /cart/",
        "Disallow: /checkout/",
        "Disallow: /profile/",
        "Disallow: /order/",
        "Disallow: /private/",
        "",
        f"Sitemap: {host_url}/sitemap.xml",
        "",
        "# Crawl-delay for non-Google bots only (Googlebot ignores this)",
        "User-agent: Bingbot",
        "Crawl-delay: 1",
        "",
        "User-agent: Yandex",
        "Crawl-delay: 1",
        "",
        "User-agent: DuckDuckBot",
        "Crawl-delay: 1",
    ]
    content = '\n'.join(lines).rstrip() + '\n'
    return HttpResponse(content, content_type='text/plain')

@cache_control(max_age=3600)  # Cache for 1 hour
@require_http_methods(["GET"])
def security_txt(request):
    """Generate security.txt for security researchers"""
    host_url = f"{request.scheme}://{request.get_host()}"
    lines = [
        "Contact: mailto:support@medpharmaweb.shop",
        "Expires: 2026-12-31T23:59:59.000Z",
        "Preferred-Languages: fa, en",
        f"Canonical: {host_url}/.well-known/security.txt",
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')

@cache_control(max_age=86400)  # Cache for 24 hours
@require_http_methods(["GET"])
def humans_txt(request):
    """Generate humans.txt"""
    lines = [
        "/* TEAM */",
        "Developer: PharmaWeb Team",
        "Contact: support@medpharmaweb.shop",
        "Location: Iran",
        "",
        "/* SITE */",
        "Last update: 2025/09/28",
        "Language: Persian / Farsi",
        "Doctype: HTML5",
        "IDE: VS Code",
        "",
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')

def structured_data_view(request):
    """Generate JSON-LD structured data for the website"""
    site_url = getattr(settings, 'SITE_URL', f"{request.scheme}://{request.get_host()}")
    structured_data = {
        "@context": "https://schema.org",
        "@type": "OnlineStore",
        "name": "PharmaWeb",
        "description": "فروشگاه آنلاین دارو و تجهیزات پزشکی",
        "url": site_url,
        "logo": f"{site_url}/static/pharma-favicon.svg",
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "Customer Service",
            "availableLanguage": ["Persian", "English"]
        },
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "IR"
        },
        "sameAs": [
            # Add your social media URLs here
        ]
    }
    
    return HttpResponse(
        json.dumps(structured_data, ensure_ascii=False, indent=2),
        content_type='application/ld+json'
    )