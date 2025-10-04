import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'local_settings')
django.setup()

from django.contrib.auth import authenticate, login, get_user_model
from django.test import Client

User = get_user_model()
client = Client()

print('🔍 بررسی تفصیلی مشکل login:')
print('=' * 50)

# چک کردن کاربر موجود
user = User.objects.first()
print(f'✅ کاربر پیدا شده: {user.phone}')
print(f'Is active: {user.is_active}')
print(f'Password hash: {user.password[:20]}...')

# تست authenticate مستقیم
authenticated_user = authenticate(request=None, phone='09123456789', password='testpass123')
print(f'✅ Authenticate result: {authenticated_user}')

if authenticated_user:
    print('✅ Authentication موفق بود')
else:
    print('❌ Authentication ناموفق')
    # بررسی رمز عبور
    is_password_correct = user.check_password('testpass123')
    print(f'Password correct: {is_password_correct}')
    
    # تلاش با رمز عبور جدید
    user.set_password('newpass123')
    user.save()
    authenticated_user = authenticate(request=None, phone='09123456789', password='newpass123')
    print(f'✅ Authenticate with new password: {authenticated_user}')

# تست login با Client
login_success = client.login(phone='09123456789', password='newpass123')
print(f'✅ Client login success: {login_success}')

# بررسی session
if login_success:
    print(f'Session user ID: {client.session.get("_auth_user_id")}')