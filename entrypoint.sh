#!/bin/sh
set -e

echo "Waiting for database and running migrations (with retries)..."
max_retries=12
retry_delay=5
for i in $(seq 1 $max_retries); do
    if python manage.py migrate --noinput; then
        echo "Migrations applied"
        break
    else
        if [ "$i" -eq "$max_retries" ]; then
            echo "Migration failed after $max_retries attempts. Continuing to start app..."
        else
            echo "Migration attempt $i failed. Retrying in ${retry_delay}s..."
            sleep $retry_delay
        fi
    fi
done

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser (if not exists)..."
set +e
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    exists = User.objects.filter(phone='09123456789').exists()
    if not exists:
        User.objects.create_superuser(phone='09123456789', password='Admin123!')
        print('Superuser created')
    else:
        print('Superuser already exists')
except Exception as e:
    print(f'Skipping superuser creation due to error: {e}')
"
set -e

echo "Starting server on PORT=${PORT:-8080}..."
exec daphne -b 0.0.0.0 -p ${PORT:-8080} --proxy-headers pharma_web.asgi:application
