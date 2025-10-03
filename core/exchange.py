import time
import requests
from django.conf import settings

# Simple in-memory cache
_CACHE = {
    'rates': None,
    'timestamp': 0
}
CACHE_TTL = 60  # seconds

COINGECKO_SIMPLE_PRICE_URL = 'https://api.coingecko.com/api/v3/simple/price'

# Default crypto targets we want to show on checkout
DEFAULT_CRYPTOS = ['bitcoin', 'ethereum', 'binancecoin', 'tron', 'tether', 'the-open-network', 'solana', 'dogecoin']


def _fetch_rates(vs_currency='usd', cryptos=None):
    """Fetch crypto prices (in vs_currency) from CoinGecko.
    Returns a dict like {'bitcoin': {'usd': 12345.6}, ...}
    """
    if cryptos is None:
        cryptos = DEFAULT_CRYPTOS
    now = time.time()
    if _CACHE['rates'] and (now - _CACHE['timestamp'] < CACHE_TTL):
        return _CACHE['rates']

    params = {
        'ids': ','.join(cryptos),
        'vs_currencies': vs_currency
    }
    headers = {}
    api_key = getattr(settings, 'COINGECKO_API_KEY', None)
    if api_key:
        # Use correct header for CoinGecko Demo API key
        headers['x-cg-demo-api-key'] = api_key

    try:
        resp = requests.get(COINGECKO_SIMPLE_PRICE_URL, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        rates = resp.json()
        _CACHE['rates'] = rates
        _CACHE['timestamp'] = now
        return rates
    except Exception:
        # On any error, return an empty dict so callers can handle it
        return {}


def convert_fiat_to_cryptos(amount, currency=None, cryptos=None):
    """Convert a fiat amount (e.g., 100 USD) into equivalent crypto amounts.

    Returns a dict: { 'bitcoin': {'price': 30000.0, 'amount': 0.00333, 'currency': 'usd'}, ... }
    """
    if currency is None:
        currency = getattr(settings, 'DEFAULT_CURRENCY', 'usd')
    if cryptos is None:
        cryptos = DEFAULT_CRYPTOS

    rates = _fetch_rates(vs_currency=currency, cryptos=cryptos)
    result = {}
    for coin in cryptos:
        coin_data = rates.get(coin)
        if coin_data:
            price = coin_data.get(currency)
            try:
                amount_crypto = None
                if price and price > 0:
                    amount_crypto = float(amount) / float(price)
                result[coin] = {
                    'price': price,
                    'amount': amount_crypto,
                    'currency': currency
                }
            except Exception:
                result[coin] = {'price': None, 'amount': None, 'currency': currency}
        else:
            result[coin] = {'price': None, 'amount': None, 'currency': currency}
    return result

def convert_usd_to_irr(amount_usd):
    """Convert USD amount to IRR using the exchange providers."""
    from decimal import Decimal
    from .exchange_providers import convert_usd_to_irr as _convert_usd_to_irr
    
    if not amount_usd:
        return None
    
    try:
        amount_decimal = Decimal(str(amount_usd))
        result = _convert_usd_to_irr(amount_decimal)
        if result:
            return result
    except Exception as e:
        # Log the error but continue to fallback
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"USD to IRR conversion failed, using fallback: {e}")
    
    # Fallback to a reasonable default rate if conversion fails
    # Use updated rate based on current market (around 117,000 IRR per USD as of 2025)
    fallback_rate = 117000
    irr_amount = int(round(float(amount_usd) * fallback_rate / 1000) * 1000)
    
    return {
        'irr_amount': irr_amount,
        'usd_amount': float(amount_usd),
        'rate': fallback_rate,
        'provider': 'fallback',
        'fetched_at': None
    }
