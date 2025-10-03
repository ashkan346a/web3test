from django.core.management.base import BaseCommand
from core.models import SiteSettings

class Command(BaseCommand):
    help = 'ایجاد تنظیمات پیش‌فرض سایت'
    
    def handle(self, *args, **options):
        try:
            settings = SiteSettings.get_settings()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ تنظیمات سایت ایجاد/به‌روزرسانی شد: '
                    f'کارت به کارت={settings.card_to_card_enabled}, '
                    f'حالت نگهداری={settings.maintenance_mode}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ خطا در ایجاد تنظیمات: {e}')
            )