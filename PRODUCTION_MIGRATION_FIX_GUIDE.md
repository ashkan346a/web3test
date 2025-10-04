# 🚨 راه حل فوری برای مشکل Migration در Production

## 🔍 علت مشکل:
Migration `core.0006` سعی می‌کند column `tracking_code` را به جدول `core_order` اضافه کند، اما این column احتمالاً در production database قبلاً وجود دارد.

## ⚡ راه حل فوری (در production server):

### 1️⃣ اول: بررسی وضعیت فعلی
```bash
# وارد Django shell شوید
python manage.py shell

# بررسی کنید که آیا فیلدها وجود دارند:
from django.db import connection
cursor = connection.cursor()

# بررسی فیلدهای موجود در جدول core_order
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'core_order'
    ORDER BY column_name;
""")

for row in cursor.fetchall():
    print(row[0])
```

### 2️⃣ اگر فیلدها موجود هستند (tracking_code, note, updated_at):
```bash
# Migration را به صورت fake اجرا کنید
python manage.py migrate core 0006 --fake
python manage.py migrate core 0007 --fake  # اگر وجود دارد
python manage.py migrate  # بقیه migration ها
```

### 3️⃣ اگر فیلدها موجود نیستند:
```bash
# ابتدا فیلدها را manual اضافه کنید
python manage.py shell

# در shell:
from django.db import connection
cursor = connection.cursor()

# اضافه کردن فیلدها
cursor.execute("ALTER TABLE core_order ADD COLUMN tracking_code VARCHAR(100) NULL;")
cursor.execute("ALTER TABLE core_order ADD COLUMN note TEXT NULL;")  
cursor.execute("ALTER TABLE core_order ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();")

# خروج از shell
exit()

# حالا migration را fake کنید
python manage.py migrate core --fake
```

### 4️⃣ راه حل خودکار (توصیه شده):

1. فایل `PRODUCTION_MIGRATION_0006.py` را به جای migration فعلی قرار دهید:
```bash
# پشتیبان گیری از migration فعلی  
cp core/migrations/0006_alter_order_options_order_note_order_tracking_code_and_more.py core/migrations/0006_backup.py

# جایگزینی با نسخه امن
cp PRODUCTION_MIGRATION_0006.py core/migrations/0006_alter_order_options_order_note_order_tracking_code_and_more.py
```

2. اجرای migration امن:
```bash
python manage.py migrate
```

## 🔧 حل کامل مشکل:

### برای جلوگیری از این مشکل در آینده:
1. همیشه قبل از migration در production، schema فعلی را بررسی کنید
2. از `--fake` برای migration هایی که manually اعمال شده‌اند استفاده کنید
3. برای تغییرات schema، از `RunPython` با بررسی وجود فیلد استفاده کنید

### دستور تست در local:
```bash  
# تست در local environment
python manage.py migrate --settings=local_settings
```

## ✅ تأیید حل مشکل:
پس از اجرای راه حل، این دستور باید بدون خطا اجرا شود:
```bash
python manage.py migrate
python manage.py check --deploy
```

## 📝 یادداشت مهم:
این مشکل فقط در production رخ می‌دهد زیرا احتمالاً فیلدها قبلاً به صورت manual اضافه شده‌اند. در local development environment مشکلی نیست.