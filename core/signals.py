from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Customer

User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_customer_profile(sender, instance, created, **kwargs):
    """Keep a simple Customer row in sync with the user for secondary profile fields.
    This avoids losing profile info and provides a place to extend later.
    """
    try:
        # get_or_create by user FK
        customer, _ = Customer.objects.get_or_create(user=instance, defaults={
            'phone': getattr(instance, 'phone', '') or '',
            'first_name': getattr(instance, 'first_name', '') or '',
            'last_name': getattr(instance, 'last_name', '') or '',
            'address': getattr(instance, 'address', '') or '',
        })
        # mirror updates whenever user is saved
        changed = False
        for attr, field in (
            ('phone', 'phone'),
            ('first_name', 'first_name'),
            ('last_name', 'last_name'),
            ('address', 'address'),
        ):
            v = getattr(instance, attr, '') or ''
            if getattr(customer, field, '') != v:
                setattr(customer, field, v)
                changed = True
        if changed:
            customer.save(update_fields=['phone', 'first_name', 'last_name', 'address', 'updated_at'])
    except Exception:
        # never break user save due to secondary profile syncing
        pass
