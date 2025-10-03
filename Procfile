# اجرای اپ با Daphne (ASGI) - بهتر برای WebSocket
web: daphne -b 0.0.0.0 -p $PORT pharma_web.asgi:application

# گزینه جایگزین با Gunicorn (بهتر برای HTTP)
# web: gunicorn pharma_web.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120

# اجرای migration و collectstatic در مرحله release
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
