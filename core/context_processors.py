from . import exchange


def crypto_conversions(request):
    """Context processor returning crypto equivalents for the current cart total.
    Reads `cart_total` from session (expected numeric) and returns a mapping under
    'crypto_conversions' for templates to show.
    """
    try:
        total = float(request.session.get('cart_total', 0))
    except Exception:
        total = 0.0
    conversions = exchange.convert_fiat_to_cryptos(total)
    return {'crypto_conversions': conversions}


def user_has_address(request):
    """Return True if the authenticated user appears to have an address on file.
    This is permissive and checks common attribute names on a related profile
    or on the user object itself to avoid template errors.
    """
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        # For anonymous users, treat as having address so we don't prompt them.
        return {'user_has_address': True}

    # Try related profile object if present
    profile = getattr(user, 'profile', None)
    if profile:
        for attr in ('address', 'address_line1', 'address1', 'address_line'):
            if getattr(profile, attr, None):
                return {'user_has_address': True}

    # Fallback: check common fields directly on the user model
    for attr in ('address', 'address_line1', 'address1'):
        if getattr(user, attr, None):
            return {'user_has_address': True}

    return {'user_has_address': False}


def seo_settings(request):
    """
    Context processor برای تنظیمات SEO
    """
    from django.conf import settings
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'PharmaWeb'),
        'SITE_DESCRIPTION': getattr(settings, 'SITE_DESCRIPTION', ''),
        'SITE_KEYWORDS': getattr(settings, 'SITE_KEYWORDS', ''),
        'SITE_URL': getattr(settings, 'SITE_URL', ''),
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', ''),
        'GOOGLE_SITE_VERIFICATION': getattr(settings, 'GOOGLE_SITE_VERIFICATION', ''),
        'BING_SITE_VERIFICATION': getattr(settings, 'BING_SITE_VERIFICATION', ''),
    }
