import os
import django
from django.contrib.auth import get_user_model
from core.forms import AddressForm

# ست کردن تنظیمات جنگو
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pharma_web.settings")
django.setup()

User = get_user_model()

# create test user
u, created = User.objects.get_or_create(
    phone="+999000000001",
    defaults={
        "email": "",
        "first_name": "",
        "last_name": "",
        "address": "",
    },
)

if created:
    u.set_password("pass12345")
    u.save()

print("Before:", u.first_name, u.last_name, u.email, u.address)

# simulate POST to update
form = AddressForm(
    {
        "first_name": "Ali",
        "last_name": "Ahmadi",
        "email": "ali@example.com",
        "address": "Tehran, Iran",
    },
    instance=u,
)

print("is_valid", form.is_valid(), form.errors)

if form.is_valid():
    uu = form.save()
    uu.refresh_from_db()
    print("After:", uu.first_name, uu.last_name, uu.email, uu.address)
else:
    print("Invalid form")
