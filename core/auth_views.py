from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .views import get_text
from django.views.decorators.http import require_POST
from . import views as core_views

import uuid


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # prefer phone as username in this project
            if not getattr(user, 'phone', None):
                user.phone = form.cleaned_data.get('phone')
            # set password from form (templates post password1)
            pw = form.cleaned_data.get('password') or form.cleaned_data.get('password1')
            user.set_password(pw)
            user.save()
            # authenticate and login by phone (CustomUser.USERNAME_FIELD)
            user_auth = authenticate(request, username=getattr(user, 'phone', None), password=pw)
            try:
                if user_auth:
                    auth_login(request, user_auth)
                else:
                    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            except Exception:
                pass
            messages.success(request, 'حساب با موفقیت ساخته شد')
            return redirect('profile')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


@login_required
def logout_view(request):
    lang = request.session.get('language', 'fa')
    if request.method == 'POST':
        try:
            auth_logout(request)
        except Exception:
            pass
        messages.success(request, get_text(lang, 'logout_success'))
        return redirect('login_view')
    return render(request, 'logout_confirm.html', {'lang': lang})


@require_POST
def cart_add(request, item_id: str):
    """Public wrapper to add an item to session cart (works for anonymous users)."""
    try:
        core_views.ensure_loaded()
    except Exception:
        pass
    # try direct lookup
    item = None
    try:
        item = getattr(core_views, '_ITEMS', {}).get(item_id)
    except Exception:
        item = None
    if not item:
        # fallback search
        groups = getattr(core_views, '_GROUPS', {}) or {}
        for g in groups.values():
            for v in g.get('variants', []) or []:
                if str(v.get('id')) == str(item_id):
                    item = v
                    break
            if item:
                break
    if not item:
        messages.error(request, 'محصول یافت نشد')
        return redirect('buy_medicine')

    # accept either 'qty' (legacy) or 'quantity' from forms
    qty = int(request.POST.get('qty') or request.POST.get('quantity') or 1)
    cart = request.session.get('cart', {}) or {}
    if isinstance(cart, list):
        new = {}
        for it in cart:
            new[it.get('id')] = it
        cart = new
    entry = cart.get(item_id, {})
    entry['id'] = item_id
    new_qty = int(entry.get('qty', entry.get('quantity', 0))) + qty
    entry['qty'] = new_qty
    entry['quantity'] = new_qty
    # robust price extraction: try common keys and nested 'raw' dicts
    try:
        safe_float = getattr(core_views, '_safe_float', None)
        if safe_float is None:
            # fallback simple conversion
            entry_price = float(item.get('price') or item.get('price_usd') or item.get('amount') or item.get('value') or 0)
        else:
            cand = item.get('price') if 'price' in item else (item.get('price_usd') or item.get('amount') or item.get('value'))
            if cand is None and isinstance(item.get('raw'), dict):
                raw = item.get('raw')
                cand = raw.get('price') or raw.get('price_usd') or raw.get('amount') or raw.get('value')
            entry_price = float(safe_float(cand))
    except Exception:
        entry_price = 0.0
    entry['price'] = entry_price
    entry['name'] = item.get('name') or item.get('title') or ''
    entry['image'] = item.get('image')
    entry['description'] = item.get('description')
    cart[item_id] = entry
    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, 'محصول به سبد افزوده شد')
    return redirect('cart')


# Password reset views: use Django built-in class-based views so urls can reference them
from django.contrib.auth import views as django_auth_views
from django.urls import reverse_lazy

password_reset = django_auth_views.PasswordResetView.as_view(
    template_name='password_reset.html',
    email_template_name='password_reset_email.html',
    subject_template_name='password_reset_subject.txt',
    success_url=reverse_lazy('password_reset_done'),
)

password_reset_done = django_auth_views.PasswordResetDoneView.as_view(
    template_name='password_reset_done.html'
)

password_reset_confirm = django_auth_views.PasswordResetConfirmView.as_view(
    template_name='password_reset_confirm.html',
    success_url=reverse_lazy('password_reset_complete'),
)

password_reset_complete = django_auth_views.PasswordResetCompleteView.as_view(
    template_name='password_reset_complete.html'
)
