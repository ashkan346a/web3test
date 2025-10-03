import json
import os
import time
import requests
DISABLE_CRYPTO = os.environ.get('DISABLE_CRYPTO') == '1'
if not DISABLE_CRYPTO:
    from web3 import Web3
    from tronpy import Tron
    from tronpy.providers import HTTPProvider
    from tronpy.keys import PrivateKey
else:
    Web3 = None
    Tron = None
    HTTPProvider = None
    PrivateKey = None
if not DISABLE_CRYPTO:
    try:
        from bitcoinlib.wallets import Wallet, wallet_create_or_open
        from bitcoinlib.keys import HDKey
    except Exception:
        Wallet = None
        wallet_create_or_open = None
        HDKey = None
else:
    Wallet = None
    wallet_create_or_open = None
    HDKey = None
from io import BytesIO
import qrcode
from datetime import datetime
from pathlib import Path
import logging
import uuid
import hashlib
import re
import threading
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import random
try:
    import pandas as pd
except ImportError:
    pd = None

import hashlib

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیمات
TOKEN = '8418626591:AAGZRc_TuRs66iu6QA35WmtN-1NdFxhx0Fg'
BITCOIN_MAIN_WALLET = 'bc1q68p8twvd9ydfpeekuamkqwgu9wr2tzylnw3fsr'
ETH_MAIN_WALLET = '0x92c9901894dC0b0ee68865a6DC486CEF0DD73009'
MAIN_WALLET = 'TXyorCxyVGHXyeooHsUyf1edpj79WnrRQh'
INFURA_API_KEY = '77c2f23f6e6343829fa6647fe49605bc'
BNB_MAIN_WALLET = '0xa057416eE6e8b625C61d966aF921837B1e1C993'
ADMIN_CHAT_ID = -1001969616125
BLOCKCYPHER_API_TOKEN = '0aee4ba7149a4234bc725938176fd58c'
BSCSCAN_API_KEYS = ['CICNT83I67CTP8A9FWD5J77JH6KPWHRYKW', 'IAEFHYJC5C2QHJJQQESWMC4WXBDVGNM45N', 'MN9GH6RFUV96UVTR3B7NWAIDI6TWZ6A516']

TRONGRID_API_KEYS = [
    "231f7199-08ba-43b6-90b4-ee7024f125b4",
    "d5b5c7da-8c29-4462-bb08-7d9b1fc2201f",
    "c39cf3ad-28a8-4622-8080-b84f438728db"
]

COINGECKO_API_KEY = "CG-L36bK4soP7T2Lb7bH782g5fe"
RATES_CACHE_FILE = Path('rates_cache.json')
CACHE_DURATION = 300
ORDERS_FILE = Path('orders.json')
BITCOIN_ADDRESSES_FILE = Path('bitcoin_addresses.json')
ETH_ADDRESSES_FILE = Path('eth_addresses.json')
BNB_ADDRESSES_FILE = Path('bnb_addresses.json')
USER_ADDRESSES_FILE = Path('user_addresses.json')
USERS_FILE = Path('users.json')
USER_INFO_FILE = Path('user_info.json')

def get_exchange_rates():
    if RATES_CACHE_FILE.exists():
        with RATES_CACHE_FILE.open('r', encoding='utf-8') as f:
            cached = json.load(f)
            if time.time() - cached.get('timestamp', 0) < CACHE_DURATION:
                return cached['currencies']
    try:
        # request TON, SOL, DOGE ids along with existing ones
        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum,tron,tether,binancecoin,the-open-network,toncoin,solana,dogecoin"
            "&vs_currencies=usd"
        )
        # Use correct header for CoinGecko Demo API key
        headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
        response = requests.get(url, headers=headers, timeout=10).json()
        rates = {
            'BTC': {'USD': response['bitcoin']['usd']},
            'ETH': {'USD': response['ethereum']['usd']},
            'TRX': {'USD': response['tron']['usd']},
            'USDT': {'USD': response['tether']['usd']},
            'BNB': {'USD': response['binancecoin']['usd']},
            'SOL': {'USD': response['solana']['usd']},
            'DOGE': {'USD': response['dogecoin']['usd']}
        }
        # map TON from whichever id is available
        ton_usd = None
        try:
            ton_usd = response.get('toncoin', {}).get('usd')
        except Exception:
            ton_usd = None
        if ton_usd is None:
            ton_usd = response.get('the-open-network', {}).get('usd')
        if ton_usd is not None:
            rates['TON'] = {'USD': ton_usd}
        else:
            # fallback to last cache or a sane default if none
            rates['TON'] = {'USD': 2.5}
        with RATES_CACHE_FILE.open('w', encoding='utf-8') as f:
            json.dump({'currencies': rates, 'timestamp': time.time()}, f)
        return rates
    except Exception as e:
        logger.error(f"Error fetching rates: {e}")
        return {
            'BTC': {'USD': 60000},
            'ETH': {'USD': 3000},
            'TRX': {'USD': 0.1},
            'USDT': {'USD': 1.0},
            'BNB': {'USD': 500},
            'TON': {'USD': 2.5},
            'SOL': {'USD': 200},
            'DOGE': {'USD': 0.3}
        }

def convert_usd_to_crypto(usd_amount, currency, rates):
    """Convert a USD amount to a crypto amount using provided rates.
    Returns (amount, decimals) where amount is rounded to a realistic display precision.
    """
    try:
        rate = rates.get(currency, {}).get('USD')
        if not rate or float(rate) == 0:
            return None, None
        amount = float(usd_amount) / float(rate)
        # realistic display precision per currency
        decimals_map = {
            'BTC': 8,
            'ETH': 6,
            'BNB': 6,
            'TRX': 6,
            'USDT': 6,
            'TON': 6,
            'SOL': 6,
            'DOGE': 8
        }
        decimals = decimals_map.get(currency, 6)
        return round(amount, decimals), decimals
    except Exception as e:
        logger.error(f"Error converting USD to {currency}: {e}")
        return None, None


# توابع بررسی پرداخت‌ها
def get_trx_transactions(address, retries=3):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    api_key = random.choice(TRONGRID_API_KEYS)
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions?only_confirmed=true"
    headers = {"TRON-PRO-API-KEY": api_key}
    try:
        resp = session.get(url, headers=headers, timeout=10).json()
        transactions = resp.get("data", [])
        logger.info(f"TRX transactions for {address}: {len(transactions)} found")
        return transactions
    except Exception as e:
        logger.error(f"Error fetching TRX transactions for {address}: {e}")
        return []

def get_usdt_transactions(address, retries=3):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    api_key = random.choice(TRONGRID_API_KEYS)
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20?contract_address=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    headers = {"TRON-PRO-API-KEY": api_key}
    try:
        resp = session.get(url, headers=headers, timeout=10).json()
        transactions = resp.get("data", [])
        logger.info(f"USDT transactions for {address}: {len(transactions)} found")
        return transactions
    except Exception as e:
        logger.error(f"Error fetching USDT transactions for {address}: {e}")
        return []

def get_btc_transactions(address, retries=3):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/full?token={BLOCKCYPHER_API_TOKEN}"
    try:
        resp = session.get(url, timeout=10).json()
        transactions = resp.get("txs", [])
        logger.info(f"BTC transactions for {address}: {len(transactions)} found")
        return transactions
    except Exception as e:
        logger.error(f"Error fetching BTC transactions for {address}: {e}")
        return []

def get_eth_transactions(address, retries=3):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=desc&apikey={INFURA_API_KEY}"
    try:
        resp = session.get(url, timeout=10).json()
        transactions = resp.get("result", [])
        logger.info(f"ETH transactions for {address}: {len(transactions)} found")
        return transactions
    except Exception as e:
        logger.error(f"Error fetching ETH transactions for {address}: {e}")
        return []

def get_bnb_transactions(address, retries=3):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    api_key = random.choice(BSCSCAN_API_KEYS)
    url = f"https://api.bscscan.com/api?module=account&action=txlist&address={address}&sort=desc&apikey={api_key}"
    try:
        resp = session.get(url, timeout=10).json()
        transactions = resp.get("result", [])
        logger.info(f"BNB transactions for {address}: {len(transactions)} found")
        return transactions
    except Exception as e:
        logger.error(f"Error fetching BNB transactions for {address}: {e}")
        return []



def get_rates_with_meta():
    """Return current rates (from get_exchange_rates) and the cache timestamp if available."""
    rates = get_exchange_rates()
    ts = 0
    try:
        if RATES_CACHE_FILE.exists():
            with RATES_CACHE_FILE.open('r', encoding='utf-8') as f:
                cached = json.load(f)
                ts = cached.get('timestamp', 0)
    except Exception as e:
        logger.debug(f"Could not read rates cache timestamp: {e}")
        ts = int(time.time())
    return rates, ts


# توابع بررسی پرداخت‌ها
def get_trx_transactions(address, retries=3):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    api_key = random.choice(TRONGRID_API_KEYS)
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions?only_confirmed=true"
    headers = {"TRON-PRO-API-KEY": api_key}
    try:
        resp = session.get(url, headers=headers, timeout=10).json()
        transactions = resp.get("data", [])
        logger.info(f"TRX transactions for {address}: {len(transactions)} found")
        return transactions
    except Exception as e:
        logger.error(f"Error fetching TRX transactions for {address}: {e}")
        return []

def get_usdt_transactions(address, retries=3):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    api_key = random.choice(TRONGRID_API_KEYS)
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20?contract_address=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    headers = {"TRON-PRO-API-KEY": api_key}
    try:
        resp = session.get(url, headers=headers, timeout=10).json()
        transactions = resp.get("data", [])
        logger.info(f"USDT transactions for {address}: {len(transactions)} found")
        return transactions
    except Exception as e:
        logger.error(f"Error fetching USDT transactions for {address}: {e}")
        return []

def get_btc_transactions(address, retries=3):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/full?token={BLOCKCYPHER_API_TOKEN}"
    try:
        resp = session.get(url, timeout=10).json()
        transactions = resp.get("txs", [])
        logger.info(f"BTC transactions for {address}: {len(transactions)} found")
        return transactions
    except Exception as e:
        logger.error(f"Error fetching BTC transactions for {address}: {e}")
        return []

def get_eth_transactions(address, retries=3):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=desc&apikey={INFURA_API_KEY}"
    try:
        resp = session.get(url, timeout=10).json()
        transactions = resp.get("result", [])
        logger.info(f"ETH transactions for {address}: {len(transactions)} found")
        return transactions
    except Exception as e:
        logger.error(f"Error fetching ETH transactions for {address}: {e}")
        return []

def get_bnb_transactions(address, retries=3):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    api_key = random.choice(BSCSCAN_API_KEYS)
    url = f"https://api.bscscan.com/api?module=account&action=txlist&address={address}&sort=desc&apikey={api_key}"
    try:
        resp = session.get(url, timeout=10).json()
        transactions = resp.get("result", [])
        logger.info(f"BNB transactions for {address}: {len(transactions)} found")
        return transactions
    except Exception as e:
        logger.error(f"Error fetching BNB transactions for {address}: {e}")
        return []

def check_payment(order):
    currency = order['currency']
    address = order['address']
    expected_amount = order['amount']
    
    if currency == 'TRX':
        transactions = get_trx_transactions(address)
        for tx in transactions:
            if tx.get('ret', [{}])[0].get('contractRet') == 'SUCCESS':
                if tx['raw_data']['contract'][0]['type'] == 'TransferContract':
                    amount = tx['raw_data']['contract'][0]['parameter']['value']['amount'] / 1_000_000
                    if amount >= expected_amount:
                        return True
    elif currency == 'USDT':
        transactions = get_usdt_transactions(address)
        for tx in transactions:
            if tx.get('ret', [{}])[0].get('contractRet') == 'SUCCESS':
                if tx['raw_data']['contract'][0]['type'] == 'TriggerSmartContract':
                    # Extract USDT amount from data field (simplified)
                    contract_data = tx['raw_data']['contract'][0]['parameter']['value']['data']
                    if contract_data.startswith('a9059cbb'):
                        amount_hex = contract_data[72:136]
                        if amount_hex:
                            amount = int(amount_hex, 16) / 1_000_000
                            if amount >= expected_amount:
                                return True
    elif currency == 'BTC':
        transactions = get_btc_transactions(address)
        for tx in transactions:
            if tx.get('confirmations', 0) > 0:
                total_received = sum(output.get('value', 0) for output in tx.get('outputs', []) 
                                  if output.get('addresses', [None])[0] == address)
                if total_received / 100_000_000 >= expected_amount:
                    return True
    elif currency == 'ETH':
        transactions = get_eth_transactions(address)
        for tx in transactions:
            if int(tx.get('confirmations', 0)) > 0:
                if tx.get('to', '').lower() == address.lower():
                    amount = int(tx.get('value', 0)) / 10**18
                    if amount >= expected_amount:
                        return True
    elif currency == 'BNB':
        transactions = get_bnb_transactions(address)
        for tx in transactions:
            if int(tx.get('confirmations', 0)) > 0:
                if tx.get('to', '').lower() == address.lower():
                    amount = int(tx.get('value', 0)) / 10**18
                    if amount >= expected_amount:
                        return True
    return False
