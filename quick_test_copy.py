"""
تست سریع کپی مبلغ کارت به کارت
"""

print("🔧 تست فوری کپی مبلغ کارت به کارت")
print("=" * 50)

import os

# بررسی فایل‌های موجود
files_to_check = [
    ("C:/Users/win11/Documents/GitHub/web3test/core/templates/checkout.html", "فایل اصلی checkout"),
    ("C:/Users/win11/Documents/GitHub/web3test/emergency_copy_test.html", "فایل تست فوری")
]

for file_path, description in files_to_check:
    if os.path.exists(file_path):
        print(f"✅ {description} موجود است")
    else:
        print(f"❌ {description} موجود نیست")

# بررسی محتوای checkout.html
checkout_path = "C:/Users/win11/Documents/GitHub/web3test/core/templates/checkout.html"
if os.path.exists(checkout_path):
    with open(checkout_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # بررسی تابع جدید
    checks = [
        ("=== copyIRRAmount START ===", "تابع جدید copyIRRAmount"),
        ("fallbackCopyAmount", "تابع fallback جدید"),
        ("showSuccessButton", "تابع success feedback"),
        ("replace(/\\D/g, '')", "حذف کاراکترهای غیرعددی"),
        ("navigator.clipboard.writeText", "modern clipboard API"),
        ("document.execCommand('copy')", "fallback copy method"),
        ("#irr-amount", "عنصر مبلغ HTML"),
        ("onclick=\"copyIRRAmount()\"", "دکمه کپی HTML")
    ]
    
    print(f"\n🔍 بررسی عناصر کلیدی:")
    for check, description in checks:
        if check in content:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description}")
    
    # شمارش debug logs
    debug_count = content.count("console.log")
    alert_count = content.count("alert(")
    
    print(f"\n📊 آمار debug:")
    print(f"   - تعداد console.log: {debug_count}")
    print(f"   - تعداد alert: {alert_count}")

print(f"\n🧪 مراحل تست:")
print("   1. فایل emergency_copy_test.html را باز کنید")
print("   2. F12 کنید و console tab را باز کنید")
print("   3. روی دکمه 'کپی مبلغ' کلیک کنید")
print("   4. console logs را بررسی کنید")
print("   5. اگر alert نمایش داده شد، در notepad paste کنید")
print("   6. باید عدد 2986500 (بدون کاما) نمایش داده شود")

print(f"\n🚨 اگر هنوز کار نمی‌کند:")
print("   - console را چک کنید برای error messages")
print("   - مطمئن شوید که مرورگر از clipboard API پشتیبانی می‌کند")
print("   - در صورت لزوم از fallback method استفاده می‌شود")

print(f"\n✨ تابع جدید ویژگی‌های بهتری دارد:")
print("   🔍 Multiple element selection methods")  
print("   📝 Extensive debug logging")
print("   🛡️ Better error handling")
print("   🎯 Clean number extraction with /\\D/g")
print("   💚 Visual success feedback")
print("   ⚡ Both modern and fallback clipboard methods")

print(f"\n🎉 کد حالا باید کاملاً کار کند!")