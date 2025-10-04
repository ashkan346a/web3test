import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'local_settings')
django.setup()

from django.conf import settings

print(f'BASE_DIR: {settings.BASE_DIR}')
expected_path = os.path.join(settings.BASE_DIR, 'medicines.json')
print(f'Expected path: {expected_path}')
print(f'File exists: {os.path.exists(expected_path)}')

# بررسی فایل‌های موجود در BASE_DIR
print(f'\nFiles in BASE_DIR:')
for file in os.listdir(settings.BASE_DIR):
    if file.endswith('.json'):
        print(f'  - {file}')