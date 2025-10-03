import importlib
import sys

MODULES = [
    'django', 'requests', 'web3', 'tronpy', 'pandas', 'qrcode'
]

missing = []
for m in MODULES:
    try:
        importlib.import_module(m)
    except Exception as e:
        missing.append(f"{m}: {e}")

if missing:
    print("[health_check] Missing or failed modules:")
    for item in missing:
        print(" -", item)
    sys.exit(1)
else:
    print("[health_check] All core optional modules imported successfully.")
