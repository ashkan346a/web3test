import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'local_settings')
django.setup()

from core import views as core_views

print('🔍 تست دقیق بارگذاری آیتم‌ها:')
print('=' * 50)

# اول بیایید مستقیماً load_medicines_json را فراخوانی کنیم
groups, images = core_views.load_medicines_json()
print(f'✅ گروه‌های لود شده: {len(groups)}')
print(f'✅ تصاویر لود شده: {len(images)}')

# بیایید یک گروه را بررسی کنیم
if groups:
    first_group_name = list(groups.keys())[0]
    first_group = groups[first_group_name]
    print(f'\n📦 بررسی گروه اول: {first_group_name}')
    print(f'Structure: {list(first_group.keys())}')
    
    # بیایید variants را بررسی کنیم
    if 'variants' in first_group:
        variants = first_group['variants']
        print(f'✅ تعداد variants: {len(variants)}')
        if variants:
            first_variant_id = list(variants.keys())[0]
            first_variant = variants[first_variant_id]
            print(f'نمونه variant: {first_variant_id} = {first_variant}')

# حالا بیایید ensure_loaded را فراخوانی کنیم
print(f'\n🔄 فراخوانی ensure_loaded...')
core_views.ensure_loaded()

# بررسی global variables
groups_global = getattr(core_views, '_GROUPS', {})
items_global = getattr(core_views, '_ITEMS', {})

print(f'✅ _GROUPS: {len(groups_global)}')
print(f'✅ _ITEMS: {len(items_global)}')

if items_global:
    print('\nنمونه آیتم‌ها:')
    for i, (item_id, item_data) in enumerate(items_global.items()):
        if i >= 3:
            break
        print(f'  - {item_id}: {item_data.get("name", "نامشخص")}')
else:
    print('\n❌ هیچ آیتمی در _ITEMS وجود ندارد')
    # بیایید manual check کنیم
    print('\n🔍 بررسی دستی گروه‌ها برای یافتن variants:')
    for group_name, group_data in groups_global.items():
        variants = []
        if isinstance(group_data, dict):
            for key, value in group_data.items():
                if isinstance(value, dict) and 'variants' in value:
                    variants.extend(list(value['variants'].keys()))
        if variants:
            print(f'  {group_name}: {len(variants)} variants - {variants[:3]}...')