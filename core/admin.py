from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
import re
from .models import CustomUser, Order, OrderItem, Customer, SupportTicket, SiteSettings

# unregister اگر قبلاً ثبت شده
try:
    admin.site.unregister(CustomUser)
except admin.sites.NotRegistered:
    pass

class CustomUserAdminForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValidationError('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
        return phone

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    form = CustomUserAdminForm
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'address', 'language')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
        ('Logout History', {'fields': ('logout_history',)}),
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('phone',)
    list_display = ('phone', 'first_name', 'last_name', 'is_staff', 'created_at')
    search_fields = ('phone', 'first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'language')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2', 'first_name', 'last_name', 'email', 'address', 'language'),
        }),
    )
# ثبت مدل‌های دیگر بدون duplicate
try:
    admin.site.unregister(Order)
except admin.sites.NotRegistered:
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    readonly_fields = ('deposit_address',)

    def total_amount(self, obj):
        if hasattr(obj, 'amount_usd') and obj.amount_usd is not None:
            return f"${obj.amount_usd}"
        total = 0
        for it in obj.items.all():
            total += (it.unit_price or 0) * (it.quantity or 0)
        return f"${total:.2f}"
    total_amount.short_description = 'مبلغ کل'


try:
    admin.site.unregister(OrderItem)
except admin.sites.NotRegistered:
    pass

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit_price', 'quantity', 'order')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'first_name', 'last_name')

class SupportTicketAdminForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = '__all__'
        widgets = {
            'admin_response': forms.Textarea(attrs={'rows': 4, 'cols': 80}),
            'message': forms.Textarea(attrs={'rows': 6, 'cols': 80, 'readonly': True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields readonly for editing
        if self.instance.pk:
            readonly_fields = ['name', 'contact', 'subject', 'message', 'attachment', 'created_at', 'ip_address']
            for field_name in readonly_fields:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs['readonly'] = True
                    if field_name in ['name', 'contact', 'subject']:
                        self.fields[field_name].widget.attrs['style'] = 'background-color: #f8f9fa;'

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    form = SupportTicketAdminForm
    list_display = ('ticket_id_short', 'subject_short', 'name', 'status_colored', 'created_at', 'has_attachment')
    list_filter = ('status', 'created_at', 'resolved_at')
    search_fields = ('subject', 'name', 'contact', 'ticket_id')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at', 'ip_address')
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات تیکت', {
            'fields': ('ticket_id', 'user', 'status', 'created_at', 'updated_at', 'resolved_at')
        }),
        ('اطلاعات ارسال‌کننده', {
            'fields': ('name', 'contact', 'ip_address')
        }),
        ('محتوای درخواست', {
            'fields': ('subject', 'message', 'attachment')
        }),
        ('پاسخ ادمین', {
            'fields': ('admin_response',),
            'classes': ('wide',)
        }),
    )

    def ticket_id_short(self, obj):
        return str(obj.ticket_id)[:8] + '...'
    ticket_id_short.short_description = 'شناسه تیکت'

    def subject_short(self, obj):
        return obj.short_subject
    subject_short.short_description = 'موضوع'

    def status_colored(self, obj):
        colors = {
            'PENDING': '#ffc107',
            'IN_PROGRESS': '#17a2b8',
            'RESOLVED': '#28a745',
            'CLOSED': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'وضعیت'

    def has_attachment(self, obj):
        if obj.attachment:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: #ccc;">✗</span>')
    has_attachment.short_description = 'ضمیمه'

    def save_model(self, request, obj, form, change):
        # اگر وضعیت به حل شده تغییر کرد، زمان حل شدن را ثبت کن
        if change and obj.status in ['RESOLVED', 'CLOSED'] and not obj.resolved_at:
            obj.resolved_at = timezone.now()
        super().save_model(request, obj, form, change)

    actions = ['mark_as_resolved', 'mark_as_in_progress', 'mark_as_closed']

    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='RESOLVED', resolved_at=timezone.now())
        self.message_user(request, f'{updated} تیکت به حالت حل شده تغییر کرد.')
    mark_as_resolved.short_description = 'تغییر وضعیت به حل شده'

    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f'{updated} تیکت به حالت در حال پیگیری تغییر کرد.')
    mark_as_in_progress.short_description = 'تغییر وضعیت به در حال پیگیری'

    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='CLOSED', resolved_at=timezone.now())
        self.message_user(request, f'{updated} تیکت بسته شد.')
    mark_as_closed.short_description = 'بستن تیکت'


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """مدیریت تنظیمات سایت"""
    
    list_display = ('name', 'card_to_card_enabled', 'maintenance_mode', 'updated_at')
    list_filter = ('card_to_card_enabled', 'maintenance_mode')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات کلی', {
            'fields': ('name',)
        }),
        ('تنظیمات پرداخت', {
            'fields': ('card_to_card_enabled',),
            'description': 'تنظیمات مربوط به روش‌های پرداخت'
        }),
        ('تنظیمات سیستم', {
            'fields': ('maintenance_mode',),
            'description': 'تنظیمات کلی سیستم'
        }),
        ('اطلاعات زمانی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # فقط یک رکورد تنظیمات مجاز است
        if SiteSettings.objects.exists():
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        # حذف تنظیمات مجاز نیست
        return False
    
    def changelist_view(self, request, extra_context=None):
        # اگر تنظیمات وجود ندارد، یکی ایجاد کن
        if not SiteSettings.objects.exists():
            SiteSettings.get_settings()
        return super().changelist_view(request, extra_context)