#!/bin/sh

# Enable debug mode
set -ex

echo "=== RAILWAY DEPLOYMENT DEBUG ==="
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Working Directory: $(pwd)"
echo "Environment Variables:"
env | grep -E "(PORT|DATABASE_URL|RAILWAY|DJANGO|DEBUG)" || echo "No relevant env vars found"

echo ""
echo "=== Python Information ==="
python --version
python -c "import sys; print('Python path:', sys.path[:3])"

echo ""
echo "=== File System Check ==="
ls -la
echo "App directory contents:"
ls -la /app/ || echo "No /app directory"

echo ""
echo "=== Django Settings Test ==="
python -c "
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharma_web.settings')

try:
    from django.conf import settings
    print('✅ Settings imported')
    print(f'DEBUG: {settings.DEBUG}')
    print(f'SECRET_KEY set: {bool(settings.SECRET_KEY)}')
    print(f'DATABASE_URL: {os.getenv(\"DATABASE_URL\", \"Not set\")[:50]}...')
except Exception as e:
    print(f'❌ Settings import failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "=== Django Setup Test ==="
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharma_web.settings')

try:
    django.setup()
    print('✅ Django setup successful')
except Exception as e:
    print(f'❌ Django setup failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "=== Database Connection Test ==="
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharma_web.settings')
django.setup()

from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'⚠️ Database connection failed: {e}')
    print('Continuing anyway...')
"

echo ""
echo "=== ASGI Application Test ==="
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharma_web.settings')
django.setup()

try:
    from pharma_web.asgi import application
    print('✅ ASGI application loaded successfully')
    print(f'Application type: {type(application)}')
except Exception as e:
    print(f'❌ ASGI application failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "=== URL Patterns Test ==="
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharma_web.settings')
django.setup()

try:
    from django.urls import reverse
    health_url = reverse('basic_health')
    print(f'✅ Health URL: {health_url}')
except Exception as e:
    print(f'❌ URL reverse failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "=== Starting Server ==="
echo "PORT: ${PORT:-8000}"
echo "Command: daphne -b 0.0.0.0 -p ${PORT:-8000} --access-log --proxy-headers pharma_web.asgi:application"

# Run migrations first
echo "Running migrations..."
python manage.py migrate --noinput || echo "Migration failed"

# Try to start server with verbose output
echo "Starting Daphne server..."
exec daphne \
    -b 0.0.0.0 \
    -p ${PORT:-8000} \
    --access-log \
    --proxy-headers \
    -v 2 \
    pharma_web.asgi:application