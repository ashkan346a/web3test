from typing import Any, Optional , Dict
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _
import json
from pathlib import Path
from django.utils import timezone
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
import re
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class SiteSettings(models.Model):
    """تنظیمات کلی سایت"""
    name = models.CharField(max_length=100, default="تنظیمات سایت", help_text="نام تنظیمات")
    
    # تنظیمات پرداخت
    card_to_card_enabled = models.BooleanField(
        default=True, 
        verbose_name="فعال‌سازی پرداخت کارت به کارت",
        help_text="آیا پرداخت کارت به کارت در صفحه checkout نمایش داده شود؟"
    )
    
    # سایر تنظیمات آینده
    maintenance_mode = models.BooleanField(
        default=False, 
        verbose_name="حالت نگهداری",
        help_text="فعال‌سازی حالت نگهداری سایت"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"
    
    def __str__(self):
        return f"تنظیمات سایت - {self.name}"
    
    def save(self, *args, **kwargs):
        # اطمینان از وجود تنها یک رکورد تنظیمات
        if not self.pk and SiteSettings.objects.exists():
            # اگر رکورد جدید است و قبلاً رکوردی وجود دارد، آن را به‌روزرسانی کن
            existing = SiteSettings.objects.first()
            existing.card_to_card_enabled = self.card_to_card_enabled
            existing.maintenance_mode = self.maintenance_mode
            existing.name = self.name
            existing.save()
            return existing
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """گرفتن تنظیمات فعلی (یا ایجاد پیش‌فرض)"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'name': 'تنظیمات اصلی سایت',
                'card_to_card_enabled': True,
                'maintenance_mode': False,
            }
        )
        return settings


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # اضافه
    created = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=200)  # یا ForeignKey به مدل محصول شما
    name = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)

class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)
    address = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phone or self.user.phone

class CustomUserManager(BaseUserManager):
    def _create_user(self, phone, password, **extra_fields):
        if not phone:
            raise ValueError('The given phone must be set')
        
        # اعتبارسنجی شماره تلفن
        if not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValueError('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
            
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self._create_user(phone, password, **extra_fields)



class CustomUser(AbstractUser):
    username = None
    phone = models.CharField(
        max_length=15, 
        unique=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$','Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')]
    )
    address = models.TextField(max_length=500, blank=True, null=True)
    language = models.CharField(max_length=5, default='fa')
    logout_history = models.JSONField(default=list, blank=True)
    is_blocked = models.BooleanField(default=False, help_text="مسدود شده توسط پشتیبان")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone

    def clean(self):
        super().clean()
        # اعتبارسنجی شماره تلفن
        if not re.match(r'^\+?1?\d{9,15}$', self.phone):
            raise ValidationError({
                'phone': 'Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.'
            })

PAYMENT_CHOICES = [
    ('TRX', 'TRX'),
    ('USDT', 'USDT'),
    ('BTC', 'BTC'),
    ('ETH', 'ETH'),
    ('BNB', 'BNB'),
]

ORDER_STATUS = [
    ('PENDING', 'در انتظار پرداخت'),
    ('PAID', 'پرداخت شده'),
    ('CANCELLED', 'لغو شده'),
]

class ExchangeRate(models.Model):
    """Store exchange rates for different currency pairs"""
    from_currency = models.CharField(max_length=10, default='USD')
    to_currency = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=20, decimal_places=8)
    provider = models.CharField(max_length=50)
    fetched_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['from_currency', 'to_currency', '-fetched_at']),
        ]
        unique_together = ['from_currency', 'to_currency', 'provider', 'fetched_at']
    
    def __str__(self):
        return f"{self.from_currency}/{self.to_currency}: {self.rate} ({self.provider})"

class Order(models.Model):
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=8, choices=PAYMENT_CHOICES, default='USDT')
    deposit_address = models.CharField(max_length=256, blank=True)
    status = models.CharField(max_length=16, choices=ORDER_STATUS, default='PENDING')
    created_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)  # ذخیره سبد یا فیلدهای اضافی
    
    # New fields for better order management
    tracking_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="کد پیگیری")
    note = models.TextField(blank=True, null=True, verbose_name="یادداشت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"

    def __str__(self):
        return f"Order {self.order_id} ({self.user.username})"
    
    @property
    def total(self):
        """Calculate total amount of the order"""
        return self.amount_usd
    
    @property
    def items_count(self):
        """Get the total number of items in this order"""
        return self.items.count()
    
    def get_status_display_persian(self):
        """Get Persian display for order status"""
        status_map = {
            'PENDING': 'در حال پردازش',
            'PROCESSING': 'در حال آماده‌سازی', 
            'SHIPPED': 'ارسال‌شده',
            'DELIVERED': 'تحویل‌شده',
            'CANCELLED': 'لغو شده',
        }
        return status_map.get(self.status, self.status)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.unit_price * self.quantity


# ---------------------------
# Load medicines.json safely
# ---------------------------
MEDICINES_FILE = Path(settings.BASE_DIR) / "medicines.json"

MEDICINES_DATA = {}
TRANSLATIONS = {}

MEDICINE_IMAGES = {}

if MEDICINES_FILE.exists():
    try:
        with open(MEDICINES_FILE, "r", encoding="utf-8") as f:
            DATA = json.load(f)

        # همه گروه‌ها
        all_group_keys = [
            "medicine_groups", "faroxy_groups", "tramadol_groups",
            "methadone_groups", "methylphenidate_groups", "phyto_groups",
            "seretide_groups", "modafinil_groups", "monjaro_groups",
            "insuline_groups", "soma_groups", "biobepa_groups",
            "warfarine_groups", "gardasil_groups", "rogam_groups",
            "Aminoven_groups", "Nexium_groups", "Exelon_groups",
            "testestron_groups", "zithromax_groups", "Liskantin_groups",
            "chimi_groups"
        ]

        for key in all_group_keys:
            if key in DATA:
                MEDICINES_DATA[key] = DATA[key]

        TRANSLATIONS = DATA.get("translations", {})
        MEDICINE_IMAGES = DATA.get("medicine_images", {})

        print("✅ Medicines.json loaded groups:", list(MEDICINES_DATA.keys()))
        print("✅ Loaded images:", len(MEDICINE_IMAGES))

    except Exception as e:
        print("❌ Error parsing medicines.json:", e)
else:
    print("⚠️ medicines.json not found at:", MEDICINES_FILE)


SUPPORT_STATUS_CHOICES = [
    ('PENDING', 'در حال بررسی'),
    ('IN_PROGRESS', 'در حال پیگیری'),
    ('RESOLVED', 'حل شده'),
    ('CLOSED', 'بسته شده'),
]

class SupportTicket(models.Model):
    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets', null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name='نام')
    contact = models.CharField(max_length=255, verbose_name='اطلاعات تماس')
    subject = models.CharField(max_length=255, verbose_name='موضوع')
    message = models.TextField(verbose_name='پیام')
    attachment = models.FileField(upload_to='support_attachments/', null=True, blank=True, verbose_name='ضمیمه')
    status = models.CharField(max_length=20, choices=SUPPORT_STATUS_CHOICES, default='PENDING', verbose_name='وضعیت')
    admin_response = models.TextField(blank=True, null=True, verbose_name='پاسخ ادمین')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ حل شدن')
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تیکت پشتیبانی'
        verbose_name_plural = 'تیکت‌های پشتیبانی'

    def __str__(self):
        return f"{self.subject} - {self.name}"

    @property
    def short_subject(self):
        return self.subject[:50] + '...' if len(self.subject) > 50 else self.subject

    @staticmethod
    def can_user_create_new_ticket(user_or_ip):
        """Check if user/IP can create a new ticket (24-hour limit)"""
        from django.utils import timezone
        from datetime import timedelta
        
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        
        if user_or_ip and hasattr(user_or_ip, 'is_authenticated') and user_or_ip.is_authenticated:
            # برای کاربران احراز هویت شده
            recent_tickets = SupportTicket.objects.filter(
                user=user_or_ip,
                created_at__gte=twenty_four_hours_ago
            ).exists()
        else:
            # برای کاربران مهمان بر اساس IP
            recent_tickets = SupportTicket.objects.filter(
                ip_address=user_or_ip,
                created_at__gte=twenty_four_hours_ago
            ).exists()
        
        return not recent_tickets

def _find_variant_record(cid: str) -> Optional[Dict[str, Any]]:
    """Find a variant by ID in the medicines data"""
    if not cid:
        return None
        
    # جستجو در تمام گروه‌ها
    for group_key, group_data in MEDICINES_DATA.items():
        if not isinstance(group_data, dict):
            continue
            
        # بررسی مستقیم در گروه
        if cid in group_data and isinstance(group_data[cid], dict):
            return group_data[cid]
            
        # بررسی در بخش variants گروه‌ها
        if 'variants' in group_data and isinstance(group_data['variants'], dict):
            variants = group_data['variants']
            if cid in variants:
                return variants[cid]
                
    return None