# Railway Deployment Guide for Pharma Web

## Environment Variables to set in Railway Dashboard:

### Required Variables:
```
DATABASE_URL=postgresql://postgres:ZGmJqtekgpNcyoFAeXfuUaiROJIPukuM@trolley.proxy.rlwy.net:46158/railway
DEBUG=False
DJANGO_SECRET_KEY=django-insecure-pharma-web-demo-secret
```

### Optional Variables (for security):
```
BITCOIN_MAIN_WALLET=bc1qwc2lqwjxwc29tnxn6p2kstsrqcc0ems5957r5m
ETHEREUM_MAIN_WALLET=0xaF99374Dd015dA244cdA1F1Fc2183b423a17A10D
TRON_MAIN_WALLET=TW88rRvvvoo3dRpippmQJUNmowdmgaCjhE
BLOCKCYPHER_API_TOKEN=0aee4ba7149a4234bc725938176fd58c
INFURA_API_KEY=77c2f23f6e6343829fa6647fe49605bc
COINGECKO_API_KEY=CG-L36bK4soP7T2Lb7bH782g5fe
BSCSCAN_API_KEY_1=CICNT83I67CTP8A9FWD5J77JH6KPWHRYKW
BSCSCAN_API_KEY_2=IAEFHYJC5C2QHJJQQESWMC4WXBDVGNM45N
BSCSCAN_API_KEY_3=MN9GH6RFUV96UVTR3B7NWAIDI6TWZ6A516
TRONGRID_API_KEY_1=231f7199-08ba-43b6-90b4-ee7024f125b4
TRONGRID_API_KEY_2=d5b5c7da-8c29-4462-bb08-7d9b1fc2201f
TRONGRID_API_KEY_3=c39cf3ad-28a8-4622-8080-b84f438728db
```

## Automatic Variables (set by Railway):
- RAILWAY_PUBLIC_DOMAIN
- RAILWAY_PRIVATE_DOMAIN  
- RAILWAY_PROJECT_NAME
- RAILWAY_ENVIRONMENT_NAME
- RAILWAY_SERVICE_NAME
- PORT (automatically set by Railway)

## Deployment Process:
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Railway will automatically deploy using Procfile
4. Access your app at: https://pharmaweb.up.railway.app

## Files Required for Railway:
- ✅ Procfile (exists)
- ✅ requirements.txt (exists)  
- ✅ entrypoint.sh (exists)
- ✅ settings.py (configured)

## Database:
- ✅ PostgreSQL configured
- ✅ Migrations will run automatically on deploy
- ✅ Superuser will be created automatically

## Static Files:
- ✅ WhiteNoise configured for static file serving
- ✅ collectstatic will run automatically on deploy

## Security:
- ✅ DEBUG=False for production
- ✅ ALLOWED_HOSTS configured
- ✅ CSRF_TRUSTED_ORIGINS configured
- ✅ SSL/HTTPS settings enabled