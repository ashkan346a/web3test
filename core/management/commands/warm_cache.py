from django.core.management.base import BaseCommand
from django.core.cache import cache
from core.views import get_cached_medicine_groups


class Command(BaseCommand):
    help = 'Warm up Redis cache with medicine data'

    def handle(self, *args, **options):
        self.stdout.write('🔥 Warming up cache...')
        
        # Warm up medicine groups cache
        try:
            groups = get_cached_medicine_groups()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Cached {len(groups)} medicine groups')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error warming medicine groups cache: {e}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Cache warming completed!')
        )