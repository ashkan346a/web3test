#!/usr/bin/env python3
"""
Production Migration Fixer
این script مشکل migration های duplicate column را در production حل می‌کند
"""

import os
import sys
import django

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharma_web.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def check_column_exists(table_name, column_name):
    """بررسی وجود column در جدول"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, [table_name, column_name])
        return cursor.fetchone() is not None

def fix_migration_state():
    """تصحیح وضعیت migration ها"""
    
    print("🔍 بررسی وضعیت جدول core_order...")
    
    # بررسی فیلدهای مورد نظر
    fields_to_check = ['tracking_code', 'note', 'updated_at']
    existing_fields = []
    
    for field in fields_to_check:
        if check_column_exists('core_order', field):
            existing_fields.append(field)
            print(f"✅ فیلد {field} موجود است")
        else:
            print(f"❌ فیلد {field} موجود نیست")
    
    if len(existing_fields) == len(fields_to_check):
        print("✅ تمام فیلدها موجود هستند!")
        
        # اگر تمام فیلدها موجود هستند، migration را fake بزن
        print("🔧 اجرای fake migration...")
        try:
            execute_from_command_line([
                'manage.py', 'migrate', 'core', '0006', '--fake'
            ])
            print("✅ Migration 0006 به صورت fake اجرا شد")
            
            execute_from_command_line([
                'manage.py', 'migrate', 'core', '0007', '--fake'  
            ])
            print("✅ Migration 0007 به صورت fake اجرا شد")
            
        except Exception as e:
            print(f"❌ خطا در fake migration: {e}")
            
    else:
        print("⚠️ برخی فیلدها موجود نیستند. migration عادی اجرا خواهد شد.")
        
        # اضافه کردن فیلدهای موجود نبوده
        with connection.cursor() as cursor:
            for field in fields_to_check:
                if field not in existing_fields:
                    print(f"📝 اضافه کردن فیلد {field}...")
                    
                    if field == 'tracking_code':
                        cursor.execute("ALTER TABLE core_order ADD COLUMN tracking_code VARCHAR(100) NULL;")
                    elif field == 'note':
                        cursor.execute("ALTER TABLE core_order ADD COLUMN note TEXT NULL;")
                    elif field == 'updated_at':
                        cursor.execute("ALTER TABLE core_order ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();")
                    
                    print(f"✅ فیلد {field} اضافه شد")
        
        # حالا migration را fake بزن
        print("🔧 اجرای fake migration پس از اضافه کردن فیلدها...")
        try:
            execute_from_command_line([
                'manage.py', 'migrate', 'core', '--fake'
            ])
            print("✅ تمام migration ها به صورت fake اجرا شدند")
            
        except Exception as e:
            print(f"❌ خطا در fake migration: {e}")

if __name__ == '__main__':
    try:
        fix_migration_state()
        print("\n🎉 مشکل migration برطرف شد!")
        
    except Exception as e:
        print(f"\n❌ خطای کلی: {e}")
        import traceback
        traceback.print_exc()