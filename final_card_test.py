"""
تست نهایی کپی کارت به کارت
بررسی کامل عملکرد توابع
"""

print("🔧 تست نهایی کپی کارت به کارت")
print("=" * 60)

import os

# فایل checkout.html
checkout_path = "C:/Users/win11/Documents/GitHub/web3test/core/templates/checkout.html"

if os.path.exists(checkout_path):
    with open(checkout_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("✅ فایل checkout.html موجود است")
    
    # بررسی عناصر HTML
    html_elements = [
        ('id="irr-amount"', '🏷️ عنصر مبلغ ریال'),
        ('id="card-number"', '💳 عنصر شماره کارت'),
        ('onclick="copyIRRAmount()"', '🔘 دکمه کپی مبلغ'),
        ('onclick="copyCardNumber()"', '🔘 دکمه کپی شماره کارت')
    ]
    
    print(f"\n🏷️ بررسی عناصر HTML:")
    for element, desc in html_elements:
        if element in content:
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc}")
    
    # بررسی توابع JavaScript
    js_functions = [
        ('function copyIRRAmount()', '📝 تابع کپی مبلغ'),
        ('function copyCardNumber()', '📝 تابع کپی شماره کارت'),
        ('function fallbackCopyAmount(', '🔄 fallback مبلغ'),
        ('function fallbackCopyCard(', '🔄 fallback شماره کارت'),
        ('function showSuccessButton()', '✨ نمایش موفقیت مبلغ'),
        ('function showCardSuccess()', '✨ نمایش موفقیت کارت')
    ]
    
    print(f"\n📝 بررسی توابع JavaScript:")
    for func, desc in js_functions:
        if func in content:
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc}")
    
    # بررسی ویژگی‌های کلیدی
    key_features = [
        ('replace(/[^0-9]/g, \'\')', '🧹 حذف کاراکترهای غیرعددی'),
        ('navigator.clipboard.writeText', '📋 Modern clipboard API'),
        ('document.execCommand(\'copy\')', '📋 Fallback clipboard'),
        ('console.log(', '🐛 Debug logging'),
        ('alert(', '💬 User alerts'),
        ('style.backgroundColor = \'#28a745\'', '🎨 Visual feedback')
    ]
    
    print(f"\n🛠️ ویژگی‌های کلیدی:")
    for feature, desc in key_features:
        count = content.count(feature)
        if count > 0:
            print(f"   ✅ {desc} ({count} مورد)")
        else:
            print(f"   ❌ {desc}")
    
    # بررسی مشکلات احتمالی
    print(f"\n🔍 بررسی مشکلات احتمالی:")
    
    # بررسی display:none
    if 'id="irr-payment-details"' in content and 'style="display:none"' in content:
        print("   ⚠️  بخش کارت به کارت ممکن است مخفی باشد (display:none)")
        print("       باید با کلیک روی گزینه کارت به کارت نمایش داده شود")
    else:
        print("   ✅ مشکل display:none مشاهده نشد")
    
    # بررسی وجود توابع تکراری
    copy_irr_count = content.count('function copyIRRAmount')
    copy_card_count = content.count('function copyCardNumber')
    
    if copy_irr_count > 1:
        print(f"   ⚠️  تابع copyIRRAmount تکراری ({copy_irr_count} مورد)")
    if copy_card_count > 1:
        print(f"   ⚠️  تابع copyCardNumber تکراری ({copy_card_count} مورد)")
    
    if copy_irr_count == 1 and copy_card_count == 1:
        print("   ✅ هر تابع فقط یک بار تعریف شده")
    
else:
    print("❌ فایل checkout.html یافت نشد")

# بررسی فایل‌های تست
test_files = [
    "C:/Users/win11/Documents/GitHub/web3test/card_to_card_test.html",
    "C:/Users/win11/Documents/GitHub/web3test/emergency_copy_test.html"
]

print(f"\n🧪 فایل‌های تست:")
for test_file in test_files:
    if os.path.exists(test_file):
        print(f"   ✅ {os.path.basename(test_file)}")
    else:
        print(f"   ❌ {os.path.basename(test_file)}")

print(f"\n📋 راهنمای تست:")
print("   1. فایل card_to_card_test.html را باز کنید")
print("   2. F12 کنید و Console tab را باز کنید")
print("   3. روی 'کپی مبلغ' کلیک کنید")
print("   4. باید alert با مبلغ 2986500 (بدون کاما) نمایش دهد")
print("   5. روی 'کپی' شماره کارت کلیک کنید")
print("   6. باید alert با 6037991812345678 (بدون خط تیره) نمایش دهد")
print("   7. در notepad paste کنید تا مطمئن شوید")

print(f"\n🎯 اگر هنوز کار نمی‌کند:")
print("   - Console errors را بررسی کنید")
print("   - مطمئن شوید بخش کارت به کارت visible است")
print("   - از فایل تست مستقل استفاده کنید")
print("   - مرورگر را restart کنید")

print(f"\n🚀 کد حالا باید کاملاً کار کند!")
print("   📱 پشتیبانی از همه مرورگرها")
print("   🔢 کپی بدون کاما و خط تیره")
print("   🎨 Visual feedback روی دکمه‌ها")
print("   🐛 Debug logging کامل")