from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Warm up Redis cache with medicine data'

    def handle(self, *args, **options):
        self.stdout.write('🔥 Warming up cache...')
        
        try:
            from core.views import get_cached_medicine_groups, clear_medicine_cache
            
            # Clear existing cache first
            clear_medicine_cache()
            self.stdout.write('🧹 Cleared existing cache')
            
            # Load and cache medicine groups
            groups = get_cached_medicine_groups()
            self.stdout.write(f'✅ Cached {len(groups)} medicine groups')
            
            # Test cache retrieval
            cached_groups = get_cached_medicine_groups()
            if len(cached_groups) == len(groups):
                self.stdout.write(
                    self.style.SUCCESS('✅ Cache warming completed successfully!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Cache warming verification failed')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during cache warming: {e}')
            )