"""
Exchange rate providers for various currencies including IRR (Iranian Rial)
"""
import requests
import time
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class IRRExchangeProvider:
    """
    Provider for USD to IRR conversion using multiple APIs with fallback
    """
    
    # ExchangeratesAPI keys
    EXCHANGERATES_API_KEYS = [
        "ebcc7b17b9c85664b29f0cc84123decd",
        "dd90b5c775f09c89280697791d7e32c6"
    ]
    
    # Navasan API keys
    NAVASAN_API_KEYS = [
        "freeBUs33WKTLZg7YfKLrLjVBIeD2xPj",
        "freelo2aeowdWjaASVzMu2SPHaz9DtCE",
        "freeho1O90E8Gy8FKn9rsGpCqNGqbPmz",
        "freeDWzZlxMatO6SmigGY8kEHbGT4gZo",
        "freehpGBDC9RxzpX1TVEtFeWWeI8Ng5i"
    ]
    
    CACHE_KEY = "usd_irr_rate"
    CACHE_TTL = 15 * 60  # 15 minutes
    
    def __init__(self):
        self.current_exchangerates_key_index = 0
        self.current_navasan_key_index = 0
    
    def _fetch_from_exchangerates_api(self) -> Optional[Dict[str, Any]]:
        """Fetch USD to IRR rate from ExchangeratesAPI"""
        for i in range(len(self.EXCHANGERATES_API_KEYS)):
            key_index = (self.current_exchangerates_key_index + i) % len(self.EXCHANGERATES_API_KEYS)
            api_key = self.EXCHANGERATES_API_KEYS[key_index]
            
            try:
                url = f"https://open.exchangeratesapi.io/v1/latest?access_key={api_key}&base=USD&symbols=IRR"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('success') and 'rates' in data and 'IRR' in data['rates']:
                    rate = data['rates']['IRR']
                    self.current_exchangerates_key_index = key_index
                    
                    return {
                        'rate': float(rate),
                        'provider': 'exchangerates_api',
                        'fetched_at': timezone.now().isoformat(),
                        'success': True
                    }
                else:
                    logger.warning(f"ExchangeratesAPI returned invalid data: {data}")
                    
            except Exception as e:
                logger.warning(f"ExchangeratesAPI key {key_index} failed: {e}")
                continue
        
        return None
    
    def _fetch_from_navasan(self) -> Optional[Dict[str, Any]]:
        """Fetch USD to IRR rate from Navasan API"""
        for i in range(len(self.NAVASAN_API_KEYS)):
            key_index = (self.current_navasan_key_index + i) % len(self.NAVASAN_API_KEYS)
            api_key = self.NAVASAN_API_KEYS[key_index]
            
            try:
                url = f"https://api.navasan.tech/latest/?api_key={api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Navasan API returns different formats, try various approaches
                if isinstance(data, dict):
                    irr_rate = None
                    
                    # Try nested structure first (original format)
                    if 'usd' in data and isinstance(data['usd'], dict):
                        irr_rate = data['usd'].get('irr') or data['usd'].get('IRR')
                    elif 'USD' in data and isinstance(data['USD'], dict):
                        irr_rate = data['USD'].get('irr') or data['USD'].get('IRR')
                    
                    # Try direct keys (current format from logs)
                    if not irr_rate:
                        # Look for usd_sell or usd_buy rates
                        if 'usd_sell' in data and isinstance(data['usd_sell'], dict):
                            irr_rate = data['usd_sell'].get('value')
                        elif 'usd_buy' in data and isinstance(data['usd_buy'], dict):
                            irr_rate = data['usd_buy'].get('value')
                        elif 'usd' in data and isinstance(data['usd'], dict):
                            irr_rate = data['usd'].get('value')
                    
                    # Convert to float if we found a rate
                    if irr_rate:
                        try:
                            rate_float = float(irr_rate)
                            self.current_navasan_key_index = key_index
                            
                            return {
                                'rate': rate_float,
                                'provider': 'navasan',
                                'fetched_at': timezone.now().isoformat(),
                                'success': True
                            }
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid IRR rate value: {irr_rate}")
                    
                    # If no rate found, log for debugging
                    logger.warning(f"Navasan API no IRR rate found in expected format")
                        
            except Exception as e:
                logger.warning(f"Navasan API key {key_index} failed: {e}")
                continue
        
        return None
    
    def get_usd_to_irr_rate(self) -> Optional[Dict[str, Any]]:
        """
        Get USD to IRR exchange rate with caching and fallback
        Returns: dict with rate, provider, fetched_at, success
        """
        # Try to get from cache first
        cached_data = cache.get(self.CACHE_KEY)
        if cached_data:
            logger.info(f"Using cached USD/IRR rate: {cached_data}")
            return cached_data
        
        # Try ExchangeratesAPI first
        logger.info("Fetching USD/IRR rate from ExchangeratesAPI")
        result = self._fetch_from_exchangerates_api()
        
        # If ExchangeratesAPI fails, try Navasan
        if not result:
            logger.info("ExchangeratesAPI failed, trying Navasan")
            result = self._fetch_from_navasan()
        
        # If both API providers fail, try database fallback
        if not result:
            logger.info("All IRR APIs failed, trying database fallback")
            result = self.get_latest_db_rate()
        
        # If everything fails, return None
        if not result:
            logger.error("All IRR exchange providers and database fallback failed")
            return None
        
        # Cache the successful result
        cache.set(self.CACHE_KEY, result, self.CACHE_TTL)
        logger.info(f"Cached USD/IRR rate from {result['provider']}: {result['rate']}")
        
        # Save to database
        self._save_rate_to_db(result)
        
        return result
    
    def _save_rate_to_db(self, rate_data: Dict[str, Any]) -> None:
        """Save exchange rate to database"""
        try:
            from .models import ExchangeRate
            from decimal import Decimal
            
            ExchangeRate.objects.create(
                from_currency='USD',
                to_currency='IRR',
                rate=Decimal(str(rate_data['rate'])),
                provider=rate_data['provider']
            )
            logger.info(f"Saved USD/IRR rate to database: {rate_data['rate']}")
        except Exception as e:
            logger.error(f"Failed to save rate to database: {e}")
    
    def get_latest_db_rate(self) -> Optional[Dict[str, Any]]:
        """Get the latest rate from database as fallback"""
        try:
            from .models import ExchangeRate
            
            latest_rate = ExchangeRate.objects.filter(
                from_currency='USD',
                to_currency='IRR'
            ).order_by('-fetched_at').first()
            
            if latest_rate:
                return {
                    'rate': float(latest_rate.rate),
                    'provider': latest_rate.provider,
                    'fetched_at': latest_rate.fetched_at.isoformat(),
                    'success': True,
                    'from_db': True
                }
        except Exception as e:
            logger.error(f"Failed to get rate from database: {e}")
        
        return None


def convert_usd_to_irr(amount_usd: Decimal) -> Optional[Dict[str, Any]]:
    """
    Convert USD amount to IRR using the exchange provider
    
    Args:
        amount_usd: The USD amount to convert
        
    Returns:
        dict with irr_amount, rate_info, or None if conversion fails
    """
    if not amount_usd or amount_usd <= 0:
        return None
    
    provider = IRRExchangeProvider()
    rate_data = provider.get_usd_to_irr_rate()
    
    if not rate_data or not rate_data.get('success'):
        return None
    
    rate = Decimal(str(rate_data['rate']))
    irr_amount = amount_usd * rate
    
    # Round to nearest 1000 IRR as requested
    irr_amount_rounded = int(round(irr_amount / 1000) * 1000)
    
    return {
        'irr_amount': irr_amount_rounded,
        'usd_amount': float(amount_usd),
        'rate': float(rate),
        'provider': rate_data['provider'],
        'fetched_at': rate_data['fetched_at']
    }


# Backwards compatibility - expose the main function
def get_usd_to_irr_conversion(amount_usd: Decimal) -> Optional[Dict[str, Any]]:
    """Alias for convert_usd_to_irr for backwards compatibility"""
    return convert_usd_to_irr(amount_usd)