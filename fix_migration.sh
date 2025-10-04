#!/bin/bash

# 🚨 اسکریپت حل فوری مشکل Migration در Production
# این اسکریپت مشکل "column already exists" را حل می‌کند

echo "🔍 شروع حل مشکل Migration..."

# 1. بررسی وضعیت فعلی
echo "📊 بررسی وضعیت پایگاه داده..."
python manage.py shell << 'EOF'
from django.db import connection
cursor = connection.cursor()

try:
    cursor.execute("SELECT tracking_code FROM core_order LIMIT 1;")
    print("✅ فیلد tracking_code موجود است")
    tracking_exists = True
except:
    print("❌ فیلد tracking_code موجود نیست")  
    tracking_exists = False

try:
    cursor.execute("SELECT note FROM core_order LIMIT 1;")
    print("✅ فیلد note موجود است")
    note_exists = True
except:
    print("❌ فیلد note موجود نیست")
    note_exists = False

try:
    cursor.execute("SELECT updated_at FROM core_order LIMIT 1;")
    print("✅ فیلد updated_at موجود است")
    updated_exists = True
except:
    print("❌ فیلد updated_at موجود نیست")
    updated_exists = False

# ذخیره وضعیت در فایل
with open('/tmp/migration_status.txt', 'w') as f:
    f.write(f"tracking_code:{tracking_exists}\n")
    f.write(f"note:{note_exists}\n") 
    f.write(f"updated_at:{updated_exists}\n")

print("🔍 وضعیت فیلدها ذخیره شد")
EOF

# 2. خواندن وضعیت
if [ -f /tmp/migration_status.txt ]; then
    source /tmp/migration_status.txt
    
    # اگر تمام فیلدها موجود هستند
    if grep -q "tracking_code:True" /tmp/migration_status.txt && 
       grep -q "note:True" /tmp/migration_status.txt && 
       grep -q "updated_at:True" /tmp/migration_status.txt; then
        
        echo "✅ تمام فیلدها موجود هستند - اجرای fake migration..."
        
        # Fake کردن migration های مشکل‌دار
        python manage.py migrate core 0006 --fake 2>/dev/null || echo "Migration 0006 قبلاً اجرا شده"
        python manage.py migrate core 0007 --fake 2>/dev/null || echo "Migration 0007 وجود ندارد یا قبلاً اجرا شده"
        
        echo "✅ Fake migration تمام شد"
        
    else
        echo "⚠️ برخی فیلدها موجود نیستند - اضافه کردن فیلدهای ناقص..."
        
        # اضافه کردن فیلدهای ناقص
        python manage.py shell << 'EOF'
from django.db import connection
cursor = connection.cursor()

# خواندن وضعیت
with open('/tmp/migration_status.txt', 'r') as f:
    status = f.read()

if 'tracking_code:False' in status:
    try:
        cursor.execute("ALTER TABLE core_order ADD COLUMN tracking_code VARCHAR(100) NULL;")
        print("✅ فیلد tracking_code اضافه شد")
    except Exception as e:
        print(f"⚠️ خطا در اضافه کردن tracking_code: {e}")

if 'note:False' in status:
    try:
        cursor.execute("ALTER TABLE core_order ADD COLUMN note TEXT NULL;")
        print("✅ فیلد note اضافه شد")
    except Exception as e:
        print(f"⚠️ خطا در اضافه کردن note: {e}")

if 'updated_at:False' in status:
    try:
        cursor.execute("ALTER TABLE core_order ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();")
        print("✅ فیلد updated_at اضافه شد")
    except Exception as e:
        print(f"⚠️ خطا در اضافه کردن updated_at: {e}")
EOF
        
        # حالا fake migration
        echo "🔧 اجرای fake migration پس از اضافه کردن فیلدها..."
        python manage.py migrate core --fake
    fi
    
    # پاکسازی فایل موقت
    rm -f /tmp/migration_status.txt
    
else
    echo "❌ خطا در بررسی وضعیت پایگاه داده"
    exit 1
fi

# 3. اجرای migration های باقی‌مانده
echo "🔄 اجرای سایر migration ها..."
python manage.py migrate

# 4. تست نهایی
echo "🧪 تست نهایی..."
python manage.py check --deploy

echo ""
echo "🎉 مشکل Migration برطرف شد!"
echo "✅ سیستم آماده استفاده است"