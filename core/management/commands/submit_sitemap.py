from django.core.management.base import BaseCommand
from django.contrib.sitemaps import ping_google
from django.conf import settings
import requests

class Command(BaseCommand):
    help = 'Submit sitemap to search engines'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ping-google',
            action='store_true',
            help='Ping Google about sitemap update',
        )
        parser.add_argument(
            '--submit-bing',
            action='store_true',
            help='Submit sitemap to Bing',
        )

    def handle(self, *args, **options):
        sitemap_url = f"{settings.SITE_URL}/sitemap.xml"
        
        if options['ping_google']:
            try:
                ping_google()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully pinged Google for {sitemap_url}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to ping Google: {e}')
                )

        if options['submit_bing']:
            # Bing Webmaster API endpoint
            bing_url = "https://www.bing.com/ping"
            params = {'sitemap': sitemap_url}
            
            try:
                response = requests.get(bing_url, params=params)
                if response.status_code == 200:
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully submitted to Bing: {sitemap_url}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Bing response: {response.status_code}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to submit to Bing: {e}')
                )

        # Always show sitemap URL
        self.stdout.write(f'Sitemap URL: {sitemap_url}')