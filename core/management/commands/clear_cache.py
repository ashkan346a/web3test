from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Clear Redis cache keys for medicine data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear all cache keys',
        )
        parser.add_argument(
            '--medicines',
            action='store_true',
            help='Clear medicine-related cache keys only',
        )

    def handle(self, *args, **options):
        if options['all']:
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('✅ Successfully cleared all cache keys')
            )
        elif options['medicines']:
            medicine_keys = [
                "medicines:groups:all",
                "medicines:list:top200",
            ]
            for key in medicine_keys:
                cache.delete(key)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully cleared medicine cache keys: {medicine_keys}')
            )
        else:
            # Default: clear medicine keys
            from core.views import clear_medicine_cache
            clear_medicine_cache()
            self.stdout.write(
                self.style.SUCCESS('✅ Successfully cleared medicine cache keys (default)')
            )