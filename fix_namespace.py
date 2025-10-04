import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'local_settings')
django.setup()

# Replace all core: namespace references in templates
import re

# Template files to update
template_files = [
    'core/templates/order_history.html',
    'core/templates/order_detail.html'
]

for template_file in template_files:
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace core: namespace with direct URL names
        content = re.sub(r"{% url 'core:([^']+)'", r"{% url '\1'", content)
        
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'✅ Updated {template_file}')
    except Exception as e:
        print(f'❌ Error updating {template_file}: {e}')

print('🎯 All templates updated!')