#!/usr/bin/env python3
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'local_settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth import get_user_model
from core.models import Order, OrderItem
from decimal import Decimal

User = get_user_model()

def create_test_data():
    # Create test user
    user, created = User.objects.get_or_create(
        phone='09123456789',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password('password123')
        user.save()
        print(f"Created user: {user.phone}")
    else:
        print(f"User already exists: {user.phone}")
    
    # Create test orders
    for i in range(3):
        order, created = Order.objects.get_or_create(
            user=user,
            amount_usd=Decimal(f'{100 + i * 50}.00'),
            defaults={
                'currency': 'USDT',
                'status': ['PENDING', 'PROCESSING', 'DELIVERED'][i],
                'tracking_code': f'TR{1000 + i}' if i > 0 else None,
                'note': f'Test order note {i+1}' if i == 1 else None,
            }
        )
        
        if created:
            # Add order items
            OrderItem.objects.create(
                order=order,
                name=f'Test Medicine {i+1}',
                unit_price=Decimal(f'{50 + i * 25}.00'),
                quantity=i + 1
            )
            
            OrderItem.objects.create(
                order=order,
                name=f'Test Supplement {i+1}',
                unit_price=Decimal(f'{25 + i * 15}.00'),
                quantity=1
            )
            
            print(f"Created order {order.id} with {order.items_count} items")
        else:
            print(f"Order already exists: {order.id}")

if __name__ == '__main__':
    create_test_data()
    print("Test data creation completed!")