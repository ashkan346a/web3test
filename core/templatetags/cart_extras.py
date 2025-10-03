from django import template

register = template.Library()

CART_SESSION_ID = 'cart'

@register.simple_tag(takes_context=True)
def cart_count(context):
    request = context['request']
    cart = request.session.get(CART_SESSION_ID, {})
    total = 0
    for item in (cart.values() if isinstance(cart, dict) else cart):
        total += int(item.get('quantity', item.get('qty', 0)) or 0)
    return total

@register.simple_tag(takes_context=True)
def cart_total(context):
    request = context['request']
    cart = request.session.get(CART_SESSION_ID, {})
    total = 0
    for item in (cart.values() if isinstance(cart, dict) else cart):
        qty = int(item.get('quantity', item.get('qty', 0)) or 0)
        price = float(item.get('price', 0) or 0)
        total += price * qty
    return total