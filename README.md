# djphweb

## Quick Setup
```
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Health Check (Imports)
Run before deploy to ensure optional dependencies are present:
```
python health_check.py
```
Exit code 0 = OK, non‑zero = missing modules.

## Railway Deployment Notes
1. Make sure `requirements.txt` has no `bitcoinlib` (Python 3.12 incompatibility).
2. Set `Procfile` for Channels/WebSockets:
```
web: daphne -b 0.0.0.0 -p $PORT pharma_web.asgi:application
```
3. Redeploy with cache clear if dependencies changed.
4. (Optional) Define `DISABLE_CRYPTO=1` to skip heavy blockchain logic (add conditional checks in code if needed).

## Troubleshooting
- If build fails on a missing package: ensure it is pinned in `requirements.txt`.
- If runtime says `ModuleNotFoundError` for something listed: stale image/cache → trigger rebuild without cache.
- Use `health_check.py` inside container (Railway shell) to verify environment.
