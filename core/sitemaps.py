from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
import json
from pathlib import Path
from django.conf import settings

class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        # Use actual URL names defined in core/urls.py (no namespace prefix)
        return ['home', 'register_view', 'login', 'support', 'buy_medicine']

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return timezone.now()

class MedicineCategorySitemap(Sitemap):
    """Sitemap for medicine categories"""
    priority = 0.9
    changefreq = 'daily'
    protocol = 'https'

    def items(self):
        # Load medicines data
        medicines_file = Path(settings.BASE_DIR) / "medicines.json"
        categories = []
        
        if medicines_file.exists():
            try:
                with open(medicines_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Get all medicine group keys
                group_keys = [
                    "medicine_groups", "faroxy_groups", "tramadol_groups",
                    "methadone_groups", "methylphenidate_groups", "phyto_groups",
                    "seretide_groups", "modafinil_groups", "monjaro_groups",
                    "insuline_groups", "soma_groups", "biobepa_groups",
                    "warfarine_groups", "gardasil_groups", "rogam_groups",
                    "Aminoven_groups", "Nexium_groups", "Exelon_groups",
                    "testestron_groups", "zithromax_groups", "Liskantin_groups",
                    "chimi_groups"
                ]
                
                for group_key in group_keys:
                    if group_key in data:
                        group_name = group_key.replace('_groups', '')
                        categories.append(group_name)
                        
            except Exception as e:
                print(f"Error loading medicines for sitemap: {e}")
        
        return categories

    def location(self, item):
        # Map to existing listing route; currently '/buy-medicine/' supports filtering by group via querystring
        return f'/buy-medicine/?group={item}'

    def lastmod(self, item):
        return timezone.now()

class MedicineDetailSitemap(Sitemap):
    """Sitemap for individual medicine pages"""
    priority = 0.7
    changefreq = 'weekly'
    protocol = 'https'
    limit = 1000  # Limit number of URLs

    def items(self):
        medicines_file = Path(settings.BASE_DIR) / "medicines.json"
        medicines = []
        
        if medicines_file.exists():
            try:
                with open(medicines_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                group_keys = [
                    "medicine_groups", "faroxy_groups", "tramadol_groups",
                    "methadone_groups", "methylphenidate_groups", "phyto_groups",
                    "seretide_groups", "modafinil_groups", "monjaro_groups",
                    "insuline_groups", "soma_groups", "biobepa_groups",
                    "warfarine_groups", "gardasil_groups", "rogam_groups",
                    "Aminoven_groups", "Nexium_groups", "Exelon_groups",
                    "testestron_groups", "zithromax_groups", "Liskantin_groups",
                    "chimi_groups"
                ]
                
                for group_key in group_keys:
                    if group_key in data:
                        for medicine in data[group_key]:
                            medicine_data = {
                                'name': medicine.get('name', ''),
                                'group': group_key.replace('_groups', ''),
                                'id': medicine.get('id', medicine.get('name', '').replace(' ', '_'))
                            }
                            medicines.append(medicine_data)
                            
            except Exception as e:
                print(f"Error loading medicines for sitemap: {e}")
        
        return medicines[:self.limit]  # Limit results

    def location(self, item):
        # Detail route is defined as /item/<item_id>/
        return f'/item/{item["id"]}/'

    def lastmod(self, item):
        return timezone.now()