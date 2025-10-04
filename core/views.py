from __future__ import annotations

from functools import lru_cache
import io
import json
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple



from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.urls import reverse
from django.core.cache import cache

from pharma_web.settings import BASE_DIR

# --- configuration
LANG_FALLBACKS = ["fa", "en", "tr", "ar"]
CART_SESSION_KEY = "cart"

from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
import json
from pathlib import Path

# --- views
from typing import Any, Dict, List
from django.shortcuts import render
from django.http import HttpRequest
from django.views.decorators.http import require_GET

from pathlib import Path
import json
from urllib import request
import uuid
import time
import threading
from decimal import Decimal
from io import BytesIO
import hashlib


try:
    import qrcode
except Exception:
    qrcode = None

try:
    import requests
except Exception:
    requests = None

try:
    from web3 import Web3, HTTPProvider as Web3HTTPProvider
except Exception:
    Web3 = None
    Web3HTTPProvider = None

try:
    from tronpy import Tron
    from tronpy.providers import HTTPProvider as TronHTTPProvider
except Exception:
    Tron = None
    TronHTTPProvider = None

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
import csv

from .models import CustomUser, Order, OrderItem, Cart, CartItem, Customer
from .forms import LoginForm, RegisterForm, ProfileUpdateForm

from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt


# اگر فرم AddressForm جداگانه وجود نداشت، از فرم پروفایل به عنوان fallback استفاده می‌کنیم
try:
    from .forms import AddressForm
except Exception:
    AddressForm = ProfileUpdateForm

from django.http import JsonResponse
from .utils.crypto import get_exchange_rates, convert_usd_to_crypto, check_payment

# api_live_rates is defined later with extended payload; keep that one only.

# --- Support Chat Agent Console
try:
    from chat.models import ChatRoom
except Exception:
    ChatRoom = None

@staff_member_required
def agent_console(request: HttpRequest):
    rooms = []
    if ChatRoom is not None:
        # آماده‌سازی اطلاعات کامل برای نمایش در پنل حرفه‌ای
        rooms_queryset = ChatRoom.objects.select_related('user').prefetch_related('messages').order_by('-updated_at')[:100]
        for room in rooms_queryset:
            last_message = room.messages.order_by('-created_at').first()
            
            # Use model methods for consistency
            room.last_message = last_message.content if last_message else ""
            room.unread_count = room.get_unread_count()
            room.display_name = room.get_display_name()
            rooms.append(room)
    
    return render(request, 'professional_chat_console.html', { 'rooms': rooms })

# نسخه قبلی برای سازگاری با کد موجود
@staff_member_required  
def agent_console_legacy(request: HttpRequest):
    rooms = []
    if ChatRoom is not None:
        rooms = ChatRoom.objects.order_by('-updated_at')[:100]
    return render(request, 'agent_console.html', { 'rooms': rooms })

# پنل چت حرفه‌ای با طراحی تلگرام
@staff_member_required
def telegram_chat_console(request: HttpRequest):
    return render(request, 'telegram_style_chat_console.html')

# API برای دریافت اتاق‌های چت  
def api_chat_rooms(request: HttpRequest):
    try:
        from chat.models import ChatRoom
        rooms = []
        rooms_queryset = ChatRoom.objects.order_by('-updated_at')[:50]
        
        for room in rooms_queryset:
            last_message = room.messages.order_by('-created_at').first()
            
            rooms.append({
                'id': room.id,
                'user_name': room.get_display_name(),
                'user_type': 'registered' if room.user else 'guest',
                'last_message': last_message.content if last_message else 'بدون پیام',
                'unread_count': room.get_unread_count(),
                'updated_at': last_message.created_at.strftime('%H:%M') if last_message else '',
                'online': True,  # فعلاً همه را آنلاین فرض می‌کنیم
                'guest_subject': getattr(room, 'guest_subject', None),
                'is_blocked': room.is_user_blocked()
            })
        
        return JsonResponse({'rooms': rooms})
    except Exception as e:
        import traceback
        print(f"API Error: {e}")
        print(traceback.format_exc())
        return JsonResponse({'rooms': [], 'error': str(e)})

# API برای دریافت پیام‌های یک اتاق  
def api_chat_messages(request: HttpRequest, room_id):
    try:
        from chat.models import ChatRoom, ChatMessage
        room = ChatRoom.objects.get(id=room_id)
        messages = room.messages.order_by('created_at')[:100]
        
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'message': msg.content,  # Frontend expects 'message' field
                'content': msg.content,  # Keep both for compatibility
                'sender': 'agent' if msg.role == 'agent' else 'user',
                'timestamp': msg.created_at.strftime('%H:%M'),
                'created_at': msg.created_at.isoformat()
            })
        
        return JsonResponse({
            'messages': message_list,
            'room': {
                'id': room.id,
                'user_name': room.get_display_name(),
                'user_type': 'registered' if room.user else 'guest',
                'is_blocked': room.is_user_blocked()
            }
        })
    except Exception as e:
        import traceback
        print(f"Messages API Error: {e}")
        print(traceback.format_exc())
        return JsonResponse({'messages': [], 'room': {}, 'error': str(e)})

# API برای پاک کردن پیام‌های یک اتاق
@staff_member_required
def api_clear_chat_messages(request: HttpRequest, room_id):
    """Clear all messages from a chat room"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from chat.models import ChatRoom, ChatMessage
        room = ChatRoom.objects.get(id=room_id)
        
        # Delete all messages in this room
        deleted_count = room.messages.count()
        room.messages.all().delete()
        
        # Notify connected clients to clear their UIs
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"chat.room.{room_id}",
                    {"type": "chat.clear"}
                )
        except Exception as notify_err:
            # Non-fatal: log but don't fail the request
            print(f"Warn: failed to broadcast clear event: {notify_err}")
        
        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} پیام حذف شد',
            'deleted_count': deleted_count
        })
    except Exception as e:
        import traceback
        print(f"Clear Messages API Error: {e}")
        print(traceback.format_exc())
        return JsonResponse({'error': f'خطا در حذف پیام‌ها: {str(e)}'}, status=500)

# API برای حذف کامل چت
@staff_member_required
def api_delete_chat(request: HttpRequest, room_id):
    """Delete entire chat room with all messages"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from chat.models import ChatRoom, ChatMessage
        room = ChatRoom.objects.get(id=room_id)
        
        # Count messages before deletion
        message_count = room.messages.count()
        
        # Store room info for notification
        room_info = {
            'id': room.id,
            'guest_name': room.guest_name or '',
            'user_phone': room.user.phone if room.user else '',
            'session_key': room.session_key or ''
        }
        
        # Notify connected clients that chat is being deleted
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                # Notify the specific room
                async_to_sync(channel_layer.group_send)(
                    f"chat.room.{room_id}",
                    {"type": "chat.deleted"}
                )
                
                # Notify agent feed about chat deletion
                async_to_sync(channel_layer.group_send)(
                    "agent.feed",
                    {
                        "type": "chat.deleted",
                        "room_id": room_id,
                        "room_info": room_info
                    }
                )
        except Exception as notify_err:
            print(f"Warn: failed to broadcast delete event: {notify_err}")
        
        # Delete the entire room (cascade delete will remove messages)
        room.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'چت با {message_count} پیام حذف شد',
            'deleted_messages': message_count,
            'room_id': room_id
        })
    except Exception as e:
        import traceback
        print(f"Delete Chat API Error: {e}")
        print(traceback.format_exc())
        return JsonResponse({'error': f'خطا در حذف چت: {str(e)}'}, status=500)

# API برای بلاک کردن کاربر
@staff_member_required
def api_block_user(request: HttpRequest, room_id):
    """Block a user from sending messages"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from chat.models import ChatRoom
        room = ChatRoom.objects.get(id=room_id)
        
        # Block the room itself
        room.is_blocked = True
        room.save()
        
        # Also block the user if they are registered
        if room.user:
            room.user.is_blocked = True
            room.user.save()
            user_type = "registered user"
            user_name = room.user.phone
        else:
            user_type = "guest"
            user_name = room.guest_name or f"Session {room.session_key[:8]}"
        
        return JsonResponse({
            'success': True,
            'message': f'کاربر {user_name} مسدود شد',
            'user_type': user_type,
            'user_name': user_name
        })
    except Exception as e:
        import traceback
        print(f"Block User API Error: {e}")
        print(traceback.format_exc())
        return JsonResponse({'error': f'خطا در مسدود کردن کاربر: {str(e)}'}, status=500)

# API برای آنبلاک کردن کاربر
@staff_member_required
def api_unblock_user(request: HttpRequest, room_id):
    """Unblock a user to allow sending messages again"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from chat.models import ChatRoom
        room = ChatRoom.objects.get(id=room_id)
        
        # Unblock the room itself
        room.is_blocked = False
        room.save()
        
        # Also unblock the user if they are registered
        if room.user:
            room.user.is_blocked = False
            room.user.save()
            user_type = "registered user"
            user_name = room.user.phone
        else:
            user_type = "guest"
            user_name = room.guest_name or f"Session {room.session_key[:8]}"
        
        return JsonResponse({
            'success': True,
            'message': f'کاربر {user_name} آزاد شد',
            'user_type': user_type,
            'user_name': user_name
        })
    except Exception as e:
        import traceback
        print(f"Unblock User API Error: {e}")
        print(traceback.format_exc())
        return JsonResponse({'error': f'خطا در آزاد کردن کاربر: {str(e)}'}, status=500)

# صفحه چت آنلاین برای کاربران
def online_chat(request: HttpRequest):
    """صفحه چت آنلاین برای کاربران"""
    return render(request, 'online_chat.html')

# helper: pick translation value for a field (e.g. 'name' or 'description')
def pick_by_lang(obj: dict, field: str, lang: str, fallbacks=None) -> str:
    if fallbacks is None:
        fallbacks = LANG_FALLBACKS
    # first try exact lang
    v = obj.get(f"{field}_{lang}")
    if v:
        return str(v)
    # then fallbacks in order (skip lang if duplicated)
    for ln in fallbacks:
        if ln == lang:
            continue
        vv = obj.get(f"{field}_{ln}")
        if vv:
            return str(vv)
    # fallback to generic field keys
    if obj.get(field):
        return str(obj.get(field))
    
    return str(obj.get(f"{field}") or obj.get("title") or "")


MEDICINES_DATA = {}
TRANSLATIONS = {}
MEDICINE_IMAGES = {}
MEDICINES_JSON = os.path.join(BASE_DIR, "medicines.json")

# 📦 بارگذاری داده‌ها از medicines.json
MEDICINES_FILE = Path(settings.BASE_DIR) / "medicines.json"
if MEDICINES_FILE.exists():
    with open(MEDICINES_FILE, "r", encoding="utf-8") as f:
        DATA = json.load(f)
else:
    DATA = {}

# 📷 تصاویر داروها
MEDICINE_IMAGES = DATA.get("medicine_images", {})

def get_all_groups():
    """Get all medicine groups with their variants"""
    groups = []
    
    for group_key in POSSIBLE_GROUP_KEYS:
        group_data = MEDICINES_DATA.get(group_key, {})
        
        for g_name, g_info in group_data.items():
            variants = []
            variant_key = group_key.replace("_groups", "s")  # Determine variant key
            
            # Get variants from the appropriate key
            variants_data = g_info.get(variant_key, {}) or g_info.get('variants', {})
            
            for vid, v in variants_data.items():
                if isinstance(v, dict):
                    # keep original multilingual dict available as 'raw'
                    vprice = float(v.get('price', 0)) if v.get('price') is not None else 0.0
                    vimage = MEDICINE_IMAGES.get(vid)
                    
                    variants.append({
                        "id": vid,
                        # note: do not pre-select a language here — keep multilingual raw dict
                        "raw": v,
                        "price": vprice,
                        "image": vimage,
                    })
            
            groups.append({
                "id": g_name.replace(" ", "_"),
                "raw": g_info,
                "name": g_info.get('name_fa') or g_info.get('name_en') or g_name,  # fallback name, not authoritative
                "variants": variants
            })
    
    return groups


def get_cached_medicine_groups():
    """Get medicine groups with Redis caching to reduce JSON processing overhead."""
    cache_key = "medicines:groups:all"
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        # Get all groups and convert to a cacheable format
        all_groups = get_all_groups()
        
        # Convert to serializable format (avoiding objects that can't be pickled)
        serializable_groups = []
        for group in all_groups:
            serializable_variants = []
            for variant in group['variants']:
                serializable_variants.append({
                    'id': variant['id'],
                    'raw': variant['raw'],
                    'price': float(variant['price']),
                    'image': variant['image'],
                })
            
            serializable_groups.append({
                'id': group['id'],
                'raw': group['raw'],
                'name': group['name'],
                'variants': serializable_variants
            })
        
        # Cache for 5 minutes (300 seconds)
        cache.set(cache_key, serializable_groups, 300)
        cached_data = serializable_groups
    
    return cached_data


def clear_medicine_cache():
    """Clear medicine-related cache keys."""
    cache_keys = [
        "medicines:groups:all",
        "medicines:list:top200",
    ]
    for key in cache_keys:
        cache.delete(key)
    print(f"✅ Cleared cache keys: {cache_keys}")


@lru_cache(maxsize=1)
def load_medicines():
    path = getattr(settings, "MEDICINES_JSON", os.path.join(settings.BASE_DIR, "medicines.json"))
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # بازگشت شیٔ اصلی (dict) برای دسترسی به گروه‌ها و آیتم‌ها
    return data


def load_medicines_json(path: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, str]]:
    if path is None:
        path = _json_path()

    if not os.path.exists(path):
        raise FileNotFoundError(f"medicines.json not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    groups_out: Dict[str, Dict[str, Any]] = {}
    images_out: Dict[str, str] = {}

    # handle top-level groups (e.g. "medicine_groups")
    for top_group_key, top_group_val in data.items():
        # detect images block
        if top_group_key.lower().endswith("images"):
            # merge images
            if isinstance(top_group_val, dict):
                images_out.update(top_group_val)
            continue

        # each top_group_val is a mapping of group names -> group data
        if isinstance(top_group_val, dict):
            for gkey, grow in top_group_val.items():
                # grow may contain 'variants' as a dict or list
                group_obj = dict(grow) if isinstance(grow, dict) else {}
                variants_raw = group_obj.get("variants", {})

                variants_list: List[Dict[str, Any]] = []
                # if variants is a mapping, convert to list preserving variant id
                if isinstance(variants_raw, dict):
                    for vid, vdata in variants_raw.items():
                        if not isinstance(vdata, dict):
                            continue
                        # keep all multilingual keys as-is; add explicit id
                        vcopy = dict(vdata)
                        vcopy["id"] = vid
                        variants_list.append(vcopy)
                elif isinstance(variants_raw, list):
                    # if list, ensure each has id
                    for vdata in variants_raw:
                        if isinstance(vdata, dict):
                            if "id" not in vdata:
                                vcopy = dict(vdata)
                                variants_list.append(vcopy)
                            else:
                                variants_list.append(dict(vdata))
                # overwrite 'variants' with list form for internal usage
                group_obj["variants"] = variants_list
                groups_out[gkey] = group_obj

    return groups_out, images_out


class BuyMedicineView(View):
    def get(self, request):
        lang = request.session.get('language', 'fa')
        groups = []
        for gkey, group in (MEDICINES_DATA.get("medicine_groups", {}) or {}).items():
            name = group.get(f'name_{lang}') or group.get('name_en') or gkey
            variants = []
            for vid, v in (group.get('variants') or {}).items():
                vname = v.get(f'name_{lang}') or v.get('name_en') or vid
                vdesc = v.get(f'description_{lang}') or v.get('description_en') or ''
                price = float(v.get('price', 0))
                variants.append({'id': vid, 'name': vname, 'description': vdesc, 'price': price})
            groups.append({'id': gkey, 'name': name, 'variants': variants})
        return render(request, 'buy_medicine.html', {'groups': groups})

    def post(self, request):
        cart = request.session.get('cart', [])
        variant_id = request.POST.get('variant_id')
        qty = int(request.POST.get('qty', 1) or 1)
        for group in (MEDICINES_DATA.get("medicine_groups", {}) or {}).values():
            for vid, v in (group.get('variants') or {}).items():
                if variant_id == vid:
                    cart.append({
                        'id': vid,
                        'name': v.get('name_fa') or v.get('name_en') or vid,
                        'price': float(v.get('price', 0)),
                        'qty': qty
                    })
                    request.session['cart'] = cart
                    messages.success(request, "به سبد خرید اضافه شد ✅")
                    break
        return redirect('buy_medicine')


POSSIBLE_GROUP_KEYS = [
    "medicine_groups",
    "faroxy_groups",
    "tramadol_groups",
    "methadone_groups",
    "methylphenidate_groups",
    "phyto_groups",
    "seretide_groups",
    "modafinil_groups",
    "monjaro_groups",
    "insuline_groups",
    "soma_groups",
    "biobepa_groups",
    "warfarine_groups",
    "gardasil_groups",
    "rogam_groups",
    "Aminoven_groups",
    "Nexium_groups",
    "Exelon_groups",
    "testestron_groups",
    "zithromax_groups",
    "Liskantin_groups",
    "chimi_groups",
]


# --- in-memory caches
_LOADED = False
_RAW_JSON: Dict[str, Any] = {}
_ITEMS: Dict[str, Dict[str, Any]] = {}
_GROUPS: Dict[str, Dict[str, Any]] = {}
_IMAGES: Dict[str, str] = {}





def _json_path() -> str:
    return os.path.join(settings.BASE_DIR, "medicines.json")



def _safe_float(v: Any) -> float:
    try:
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v)
        # keep digits and dot
        s = "".join(ch for ch in s if ch.isdigit() or ch == ".")
        return float(s) if s else 0.0
    except Exception:
        return 0.0


def _pick_name(d: Dict[str, Any]) -> str:
    for ln in LANG_FALLBACKS:
        v = d.get(f"name_{ln}")
        if v:
            return str(v)
    # fallback to any 'name' or empty
    return str(d.get("name") or "")


def _normalize_image_path(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    s = str(raw).strip()
    if s.startswith("http://") or s.startswith("https://"):
        # don't return absolute URLs (templates expect static path)
        return None
    # if already starts with images/ keep it
    if s.startswith("images/"):
        return s
    # strip leading slashes
    s = s.lstrip("/")
    # if it contains a subfolder like static/images/... try to reduce
    if s.startswith("static/"):
        s = s[len("static/"):]
    if s.startswith("images/"):
        return s
    # otherwise prefix images/
    return f"images/{s}"


def _normalize_medicine_groups(raw_groups):
    out = {}
    if not raw_groups:
        return out

    # if a list was provided, convert to dict using provided id or generated uuid
    if isinstance(raw_groups, list):
        g_iter = {str(g.get('id') or uuid.uuid4()): g for g in raw_groups}
    else:
        g_iter = dict(raw_groups)

    # metadata keys that are not variants
    meta_keys = {'id', 'name', 'name_en', 'name_fa', 'name_tr', 'name_ar', 'exp', 'description',
                 'description_en', 'description_fa', 'description_tr', 'description_ar', 'variants'}

    for gid, group in g_iter.items():
        if not isinstance(group, dict):
            continue
        grp = dict(group)  # shallow copy

        # collect variants
        variants = {}

        # 1) explicit 'variants' key takes precedence
        if 'variants' in grp and grp.get('variants'):
            v = grp.get('variants')
            if isinstance(v, list):
                for vv in v:
                    if not isinstance(vv, dict):
                        continue
                    vid = str(vv.get('id') or uuid.uuid4())
                    vv = vv.copy()
                    vv['id'] = vid
                    variants[vid] = vv
            elif isinstance(v, dict):
                for k, vv in v.items():
                    if not isinstance(vv, dict):
                        continue
                    vid = str(vv.get('id') or k)
                    vv = vv.copy()
                    vv['id'] = vid
                    variants[vid] = vv

        # 2) fallback: treat any child dict that isn't metadata as a variant
        for key, val in group.items():
            if key in meta_keys:
                continue
            if isinstance(val, dict):
                vid = str(val.get('id') or key or uuid.uuid4())
                vcopy = val.copy()
                vcopy['id'] = vid
                # fill name if missing using key
                if not vcopy.get('name') and isinstance(key, str):
                    vcopy['name'] = key
                variants[vid] = vcopy

        # ensure variants is a dict
        grp['variants'] = variants
        out[str(gid)] = grp

    return out


if MEDICINES_FILE.exists():
    try:
        with open(MEDICINES_FILE, "r", encoding="utf-8") as f:
            medicine_data = json.load(f)

        # store raw data
        MEDICINES_DATA.update(medicine_data or {})

        # load translations and images if present (support both 'images' and 'medicine_images')
        TRANSLATIONS.update(medicine_data.get('translations', {}) or {})
        MEDICINE_IMAGES.update(medicine_data.get('images', {}) or {})
        MEDICINE_IMAGES.update(medicine_data.get('medicine_images', {}) or {})

        # normalize medicine_groups into a dict of groups each with a 'variants' dict
        raw_mg = MEDICINES_DATA.get('medicine_groups', {})
        MEDICINES_DATA['medicine_groups'] = _normalize_medicine_groups(raw_mg)

    except Exception as e:
        print(f"Error loading medicine data: {e}")


def load_translations_from_json() -> None:
    global TRANSLATIONS
    try:
        # prefer configured path, otherwise fallback to _json_path()
        path = getattr(settings, "MEDICINES_JSON", None) or str(MEDICINES_FILE)
        if not path:
            path = _json_path()
        pf = Path(path)
        if not pf.exists():
            return
        with pf.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        t = data.get("translations") or {}
        if isinstance(t, dict):
            # merge shallowly
            for k, v in t.items():
                if isinstance(v, dict):
                    existing = TRANSLATIONS.get(k, {})
                    if isinstance(existing, dict):
                        existing.update(v)
                        TRANSLATIONS[k] = existing
                    else:
                        TRANSLATIONS[k] = dict(v)
                else:
                    TRANSLATIONS[k] = v
    except Exception:
        return


def _flatten_group_variants(group_key: str, group_raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    variants: List[Dict[str, Any]] = []
    # first, if subgroup explicitly contains a 'variants' list/dict
    if "variants" in group_raw:
        cand = group_raw["variants"]
        if isinstance(cand, dict):
            for vid, vraw in cand.items():
                if isinstance(vraw, dict):
                    vraw.setdefault("id", vid)
                    variants.append(vraw)
        elif isinstance(cand, list):
            for idx, vraw in enumerate(cand):
                if isinstance(vraw, dict):
                    vraw.setdefault("id", f"{group_key}_v{idx}")
                    variants.append(vraw)

    # second, consider sibling keys as variant entries
    meta_keys = {f"name_{ln}" for ln in LANG_FALLBACKS} | {"price", "description", "description_en", "description_fa", "description_tr", "description_ar", "exp", "variants", "name"}
    for k, v in list(group_raw.items()):
        if k in meta_keys:
            continue
        if isinstance(v, dict):
            # looks like a variant entry
            v.setdefault("id", k)
            variants.append(v)

    # normalize each variant and attach group_key
    norm: List[Dict[str, Any]] = []
    for v in variants:
        vid = str(v.get("id") or v.get("code") or f"{group_key}__{abs(hash(str(v)))%10**8}")
        v = dict(v)  # copy
        v["id"] = vid
        v["group_key"] = group_key
        
        # inherit exp from parent group if variant doesn't have it
        if not v.get("exp") and group_raw.get("exp"):
            v["exp"] = group_raw.get("exp")
            
        # try to find image by id in global _IMAGES (populated later)
        if not v.get("image"):
            img = _IMAGES.get(vid)
            if img:
                v["image"] = img
        # ensure price numeric
        v["price"] = _safe_float(v.get("price", 0))
        norm.append(v)
        
        _ITEMS[vid] = v

    return norm


def ensure_loaded():
    """بارگذاری درون‌حافظه (یکبار)."""
    global _GROUPS, _IMAGES
    if _GROUPS:
        return
    # load groups/images
    _GROUPS, _IMAGES = load_medicines_json()
    # ensure translations available too
    load_translations_from_json()

def _normalize_lang_code(lang: str) -> str:
    """نمونه: 'fa-IR' -> 'fa', 'en_US' -> 'en'"""
    if not lang:
        return "fa"
    lang = str(lang).strip().lower().replace("_", "-")
    if lang.startswith("en"):
        return "en"
    if lang.startswith("fa") or "farsi" in lang or "pers" in lang:
        return "fa"
    # return first two letters as fallback
    return lang[:2]


def pick_translation(obj: Dict[str, Any], base: str, lang: str) -> str:
    if not isinstance(obj, dict):
        return ""

    candidates = []
    candidates.append(f"{base}_{lang}")
    candidates.append(f"{base}_{lang.replace('-', '_')}")
    if lang == "fa":
        candidates.append(f"{base}_farsi")
        candidates.append(f"{base}_persian")
    # english fallback and generic
    candidates.append(f"{base}_en")
    candidates.append(base)

    # nested translations: translations: {'fa': {'description': '...'}}
    if "translations" in obj and isinstance(obj["translations"], dict):
        tr = obj["translations"]
        t = tr.get(lang) or tr.get(lang.replace("-", "_"))
        if isinstance(t, dict):
            val = t.get(base)
            if val:
                return str(val)

    for k in candidates:
        if k in obj and obj.get(k) not in (None, ""):
            val = obj.get(k)
            # if val is dict, skip here (handled below)
            if isinstance(val, str):
                return val
            if val is not None:
                # return json string of dict? but better to skip
                try:
                    return str(val)
                except Exception:
                    pass

    # if base is dict of languages: e.g. description: {"fa": "...", "en": "..."}
    top = obj.get(base)
    if isinstance(top, dict):
        for candidate_lang in (lang, lang.replace('-', '_'), "fa", "en"):
            if candidate_lang in top and top[candidate_lang]:
                return str(top[candidate_lang])

    return ""

# --- view helpers
def _filter_sort_paginate_variants(all_variants: List[Dict[str, Any]], request: HttpRequest) -> Tuple[List[Dict[str, Any]], Any]:
    q = (request.GET.get("q") or "").strip().lower()
    selected_group = request.GET.get("group")
    sort = request.GET.get("sort")

    # filter
    filtered = []
    for v in all_variants:
        if selected_group and v.get("group_key") != selected_group:
            continue
        if q:
            txt = " ".join([str(v.get("name", "")), str(v.get("description", "")), str(v.get("id", ""))]).lower()
            if q not in txt:
                continue
        filtered.append(v)

    # sort
    if sort == "price_asc":
        filtered.sort(key=lambda x: x.get("price", 0))
    elif sort == "price_desc":
        filtered.sort(key=lambda x: x.get("price", 0), reverse=True)
    else:
        # default alphabetical
        filtered.sort(key=lambda x: (x.get("name") or "").lower())

    # paginate
    paginator = Paginator(filtered, 24)
    page = paginator.get_page(request.GET.get("page"))
    return filtered, page




@cache_page(60 * 10)  # cache 10 minutes
@require_GET
def buy_medicine(request: HttpRequest):
    """Show grouped products with optional search/sort/pagination."""
    query = request.GET.get('q', '').strip()
    selected_group = request.GET.get('group')
    sort = request.GET.get('sort')
    
    # get all groups (raw with 'raw' variant dicts) - use cached version
    all_groups = get_cached_medicine_groups()
    
    # determine language early and normalize
    raw_lang = request.session.get("language", "") or request.GET.get("lang", "")
    lang = _normalize_lang_code(raw_lang)

    # Filter groups and build normalized variants with translated fields
    filtered_groups = []
    all_variants = []
    
    for group in all_groups:
        filtered_variants = []
        
        for variant in group['variants']:
            raw_variant = variant.get('raw') or {}
            vid = str(variant.get('id') or raw_variant.get('id') or "")
            # choose translations dynamically
            vname = pick_translation(raw_variant, "name", lang) or raw_variant.get("name") or variant.get("name") or vid
            vdesc = pick_translation(raw_variant, "description", lang) or raw_variant.get("description") or variant.get("description") or ""
            vprice = _safe_float(raw_variant.get('price', variant.get('price', 0)))
            vimage = variant.get('image') or MEDICINE_IMAGES.get(vid) or ""
            
            # Apply search filter
            if query:
                search_text = f"{vname} {vdesc} {vid}".lower()
                if query.lower() not in search_text:
                    continue
            
            # Apply group filter
            if selected_group and group['id'] != selected_group:
                continue
                
            # Get expiry date from raw_variant
            vexp = raw_variant.get('exp', '')
                
            norm_variant = {
                'id': vid,
                'name': vname,
                'description': vdesc,
                'price': vprice,
                'image': vimage,
                'group': group['id'],
                'exp': vexp,
            }
            filtered_variants.append(norm_variant)
            all_variants.append(norm_variant)
        
        # Only include groups that have variants after filtering
        if filtered_variants:
            gname = pick_translation(group.get('raw', {}), "name", lang) or group.get('name') or group.get('id')
            filtered_groups.append({
                'id': group['id'],
                'name': gname,
                'variants': filtered_variants
            })
    
    # Sort variants
    if sort == "price_asc":
        all_variants.sort(key=lambda x: x.get("price", 0))
    elif sort == "price_desc":
        all_variants.sort(key=lambda x: x.get("price", 0), reverse=True)
    else:
        # Default alphabetical
        all_variants.sort(key=lambda x: (x.get("name") or "").lower())
    
    # Paginate
    paginator = Paginator(all_variants, 24)
    page = paginator.get_page(request.GET.get("page"))
    
    context = {
        "groups": filtered_groups,
        "variants_page": page,
        "query": query,
        "selected_group": selected_group or "",
        "sort": sort or "",
        "lang": lang,
        "i18n": TRANSLATIONS.get(lang, {}),
    }
    return render(request, "buy_medicine.html", context)

# get_exchange_rates is imported from utils.crypto at top; removed local duplicate.



from django.conf import settings

WALLETS = settings.WALLETS


@login_required
def payment_page(request):
        WALLETS = settings.WALLETS



# تابع کمکی ترجمه/متن
def get_text(lang, key, **kwargs):
    translations = {
        'en': {
            'home': 'Home',
            'logout': 'Logout',
            'cart': 'Cart',
            'order_history': 'Order History',
            'guide': 'Guide',
            'support': 'Support',
            'profile': 'Profile',
            'change_language': 'Change Language',
            'logout_success': 'Logout successful',
            'logout_blocked': 'For spam prevention, logout is blocked for {minutes} minutes',
            'cart_empty': 'Your cart is empty',
            'item_summary': '{item_name} x {item_qty} - {item_price}',
            'remove': 'Remove',
            'total_amount': 'Total amount: {total}',
            'checkout': 'Checkout',
            'register_first': 'Please register first',
            'buying_guide': 'Detailed buying guide in English...',
            'support_text': 'Support text in English...',
            'payment_success': 'Payment successful',
        },
        'fa': {
            'home': 'خانه',
            'logout': 'خروج',
            'cart': 'سبد خرید',
            'order_history': 'تاریخچه سفارشات',
            'guide': 'راهنما',
            'support': 'پشتیبانی',
            'profile': 'پروفایل',
            'change_language': 'تغییر زبان',
            'logout_success': 'خروج موفق',
            'logout_blocked': 'برای جلوگیری از اسپم، تا {minutes} دقیقه امکان خروج ندارید',
            'cart_empty': 'سبد خرید خالی است',
            'item_summary': '{item_name} x {item_qty} - {item_price}',
            'remove': 'حذف',
            'total_amount': 'مجموع مبلغ: {total}',
            'checkout': 'پرداخت',
            'register_first': 'ابتدا ثبت‌نام کنید',
            'buying_guide': 'راهنمای خرید به فارسی...',
            'support_text': 'متن پشتیبانی به فارسی...',
            'payment_success': 'پرداخت موفق',
        }
    }
    # اگر ترجمه در فایل medicines.json موجود است، از آن استفاده کن
    t = TRANSLATIONS.get(lang, {})
    if key in t:
        return t[key].format(**kwargs)
    # fallback به جیسون بالا
    return translations.get(lang, translations['en']).get(key, key).format(**kwargs)


def generate_btc_address():
    try:
        from bitcoinlib.wallets import wallet_create_or_open
        w = wallet_create_or_open('pharma_wallet', network='bitcoin')
        return w.get_key().address
    except Exception:
        return "btc_" + uuid.uuid4().hex


def generate_eth_address():
    if Web3 and Web3HTTPProvider:
        try:
            w3 = Web3(Web3HTTPProvider('https://mainnet.infura.io/v3/YOUR_INFURA_KEY'))
            account = w3.eth.account.create()
            return account.address
        except Exception:
            pass
    # fallback ساختگی
    return "0x" + uuid.uuid4().hex[:40]


def generate_trx_address():
    if Tron and TronHTTPProvider:
        try:
            client = Tron(TronHTTPProvider('https://api.trongrid.io'))
            acc = client.generate_address()
            # tronpy generate returns dict with address info in some versions
            if isinstance(acc, dict):
                return acc.get("base58") or acc.get("address") or str(acc)
            return str(acc)
        except Exception:
            pass
    return "TRX" + uuid.uuid4().hex[:30]



# keep only the later, consolidated payment-check helpers below


# =========================
# کلاس‌ها و ویوها (ساختار حفظ شده)
# =========================

"""Legacy helper block removed (the canonical implementations are defined below)."""

class HomeView(View):
    def get(self, request):
        lang = request.session.get('language', 'fa')
        selected = request.GET.get('selected', get_text(lang, 'home'))
        if request.user.is_authenticated:
            if selected == get_text(lang, 'logout'):
                return self.logout(request)
            elif selected == get_text(lang, 'cart'):
                return CartView().get(request)
            elif selected == get_text(lang, 'order_history'):
                return OrderHistoryView().get(request)
            elif selected == get_text(lang, 'guide'):
                return GuideView().get(request)
            elif selected == get_text(lang, 'support'):
                return SupportView().get(request)
            elif selected == get_text(lang, 'profile'):
                return ProfileView().get(request)
            elif selected == get_text(lang, 'change_language'):
                return ChangeLanguageView().get(request)
        return render(request, 'home.html', {'lang': lang})

    def logout(self, request):
        lang = request.session.get('language', 'fa')
        phone = getattr(request.user, "phone", None)
        allowed, remaining = check_logout_spam(phone) if phone else (True, 0)
        if allowed:
            user = request.user
            # اطمینان از نوع داده logout_history
            hist = getattr(user, "logout_history", []) or []
            hist.append(time.time())
            user.logout_history = hist
            user.save()
            logout(request)
            # clear session and redirect to home
            try:
                request.session.flush()
            except Exception:
                # ignore session flush issues
                pass
            # tag the message so client-side can choose a longer toast timeout
            messages.success(request, get_text(lang, 'logout_success'), extra_tags='logout')
            return redirect('home')
        else:
            messages.error(request, get_text(lang, 'logout_blocked', minutes=remaining))
            return redirect('home')


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            # Use globals() to avoid NameError if admin constants or helper are not defined.
            admin_hash = globals().get('ADMIN_PASSWORD_HASH')
            admin_username = globals().get('ADMIN_USERNAME')
            hash_fn = globals().get('hash_password')
            if admin_hash and admin_username and hash_fn and phone == admin_username and hash_fn(password) == admin_hash:
                user, created = CustomUser.objects.get_or_create(username=admin_username, defaults={'is_superuser': True, 'is_staff': True})
                login(request, user)
                # keep session copy
                save_user_profile_to_session(user, request)
                return redirect('admin_panel')
            user = authenticate(username=phone, password=password)
            if user:
                login(request, user)
                request.session['language'] = getattr(user, "language", request.session.get('language', 'fa'))
                # save lightweight profile copy to session for easy access
                save_user_profile_to_session(user, request)
                return redirect('home')
        messages.error(request, _('Invalid credentials'))
        return render(request, 'login.html', {'form': form})


class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})

# Backwards-compatible function views expected by urls.py
def login_view(request):
    
    if request.method == 'POST':
        return LoginView().post(request)
    return LoginView().get(request)


def register_view(request):
    
    if request.method == 'POST':
        return RegisterView().post(request)
    return RegisterView().get(request)


def logout_view(request):
    return LogoutView().get(request)


class AdminPanelView(View):
    def get(self, request):
        if not request.user.is_superuser:
            return redirect('login')
        users = CustomUser.objects.all()
        orders = Order.objects.all()
        search_term = request.GET.get('search', '')
        if search_term:
            users = users.filter(phone__icontains=search_term) | users.filter(address__icontains=search_term)
            orders = orders.filter(user__phone__icontains=search_term)
        stats = {
            'total_users': users.count(),
            'total_orders': orders.count(),
        }
        return render(request, 'admin_panel.html', {'users': users, 'orders': orders, 'stats': stats})


@login_required
def admin_export_orders_csv(request):
    
    if not request.user.is_superuser:
        return redirect('login')

    orders = Order.objects.all().order_by('-created_at')
    # prepare CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['order_id', 'user_phone', 'amount_usd', 'currency', 'status', 'created_at'])
    for o in orders:
        writer.writerow([str(o.order_id), getattr(o.user, 'phone', ''), str(getattr(o, 'amount_usd', '0')), getattr(o, 'currency', ''), getattr(o, 'status', ''), getattr(o, 'created_at', '')])
    return response


def api_search(request):
    
    q = (request.GET.get('q') or '').strip().lower()
    out = []
    if q:
        for g in get_all_groups():
            for v in g.get('variants', []) or []:
                raw = v.get('raw') or {}
                name = pick_by_lang(raw, 'name', request.session.get('language', 'fa')) or v.get('name') or ''
                if q in str(name).lower() or q in str(v.get('id', '')).lower():
                    out.append({'id': v.get('id'), 'name': name, 'price': float(raw.get('price', v.get('price', 0) or 0))})
    return JsonResponse({'results': out})


class CartView(View):
    def _build_variant_lookup(self, lang: str) -> Dict[str, Dict[str, Any]]:
        
        lookup: Dict[str, Dict[str, Any]] = {}
        for g in get_all_groups():
            for v in g.get("variants", []) or []:
                raw = v.get("raw") or {}
                vid = str(v.get("id") or raw.get("id") or "")
                # prefer translation-aware name/description and safe numeric price
                name = pick_translation(raw, "name", lang) or raw.get("name") or v.get("name") or vid
                desc = pick_translation(raw, "description", lang) or raw.get("description") or v.get("description") or ""
                price = _safe_float(raw.get("price", v.get("price", 0)))
                lookup[vid] = {
                    "id": vid,
                    "raw": raw,
                    "name": name,
                    "description": desc,
                    "price": price,
                    "group": g.get("id"),
                }
        return lookup

    def get(self, request):
        lang = request.session.get("language", "fa")
        raw_cart = request.session.get("cart", {}) or {}
        variant_lookup = self._build_variant_lookup(lang)

        cart_items: List[Dict[str, Any]] = []
        if not raw_cart:
            return render(request, "cart.html", {"cart_items": [], "cart_total": 0.0, "message": get_text(lang, "cart_empty")})

        # helper to resolve product metadata using lookup as primary source
        def resolve_meta(cid: str, entry: Any) -> Dict[str, Any]:
            cid_str = str(cid)
            meta = {"id": cid_str, "name": cid_str, "price": 0.0, "quantity": 1}
            # prefer explicit entry values if present
            if isinstance(entry, dict):
                # quantity
                try:
                    meta["quantity"] = int(entry.get("qty", entry.get("quantity", 1)))
                except Exception:
                    meta["quantity"] = 1
                # if price present in session entry, try to use it, otherwise fallback to lookup
                if entry.get("price") is not None and entry.get("price") != "":
                    try:
                        meta["price"] = float(entry.get("price"))
                    except Exception:
                        meta["price"] = 0.0
                # name from session entry can be used as fallback
                if entry.get("name"):
                    meta["name"] = entry.get("name")
            else:
                # entry is simple (e.g. quantity number)
                try:
                    meta["quantity"] = int(entry)
                except Exception:
                    meta["quantity"] = 1

            # override with authoritative lookup if available or fill missing pieces
            lk = variant_lookup.get(cid_str)
            if lk:
                # prefer lookup price unless session explicitly provided a price (not empty)
                if not (isinstance(entry, dict) and entry.get("price") not in (None, "")):
                    meta["price"] = float(lk.get("price", 0.0))
                # prefer translated/normalized name from lookup if session doesn't provide a better one
                if not (isinstance(entry, dict) and entry.get("name")):
                    meta["name"] = lk.get("name") or meta["name"]
            return meta

        if isinstance(raw_cart, dict):
            for cid, entry in raw_cart.items():
                meta = resolve_meta(cid, entry)
                subtotal = meta["quantity"] * meta["price"]
                cart_items.append({
                    "id": str(meta["id"]),
                    "name": meta["name"],
                    "price": meta["price"],
                    "quantity": meta["quantity"],
                    "subtotal": subtotal,
                })
        elif isinstance(raw_cart, list):
            for it in raw_cart:
                cid = str(it.get("id") or it.get("product_id") or "")
                meta = resolve_meta(cid, it)
                subtotal = meta["quantity"] * meta["price"]
                cart_items.append({
                    "id": meta["id"],
                    "name": meta["name"],
                    "price": meta["price"],
                    "quantity": meta["quantity"],
                    "subtotal": subtotal,
                })

        cart_total = sum(item.get("subtotal", 0) for item in cart_items)
        if request.session.get("checkout_active", False):
            return PaymentView().get(request, total=cart_total)
        return render(request, "cart.html", {"cart_items": cart_items, "cart_total": cart_total})

    def post(self, request):
        lang = request.session.get("language", "fa")
        cart = request.session.get("cart", [])
        action = request.POST.get("action")
        if action == "remove":
            # support both dict (by id) and list (by index)
            remove_id = request.POST.get("id")
            if remove_id:
                # remove by id from dict or list
                if isinstance(cart, dict):
                    if str(remove_id) in cart:
                        cart.pop(str(remove_id), None)
                elif isinstance(cart, list):
                    cart = [it for it in cart if str(it.get("id")) != str(remove_id)]
            else:
                try:
                    i = int(request.POST.get("index"))
                    if isinstance(cart, list) and 0 <= i < len(cart):
                        del cart[i]
                except Exception:
                    pass
        elif action == "checkout":
            if not getattr(request.user, "address", None):
                messages.warning(request, get_text(lang, "register_first"))
                return redirect("profile")
            request.session["checkout_active"] = True
            return redirect("cart")
        # persist normalized cart back to session
        request.session["cart"] = cart
        request.session.modified = True
        return redirect("cart")


class PaymentView(View):
    def get(self, request, total=None):
        if total is None:
            try:
                total = float(request.GET.get('total', 0))
            except Exception:
                total = 0.0
        lang = request.session.get('language', 'fa')
        addresses = {
            'btc': generate_btc_address(),
            'eth': generate_eth_address(),
            'trx': generate_trx_address(),
        }
        qr_codes = {}
        for crypto, address in addresses.items():
            if qrcode:
                try:
                    qr = qrcode.make(address)
                    buf = BytesIO()
                    qr.save(buf, format='PNG')
                    qr_codes[crypto] = buf.getvalue()
                except Exception:
                    qr_codes[crypto] = None
            else:
                qr_codes[crypto] = None

        # شروع ترد بررسی پرداخت با انتقال داده‌های لازم
        cart = request.session.get('cart', [])
        threading.Thread(target=check_payment, args=(request.user, cart, total, addresses, lang), daemon=True).start()
        return render(request, 'payment.html', {'total': total, 'addresses': addresses, 'qr_codes': qr_codes, 'lang': lang})


# Backwards-compatible function-based endpoints expected by urls.py
@login_required
def process_payment(request):
    
    if request.method != "POST":
        return redirect('checkout')

    raw_cart = request.session.get('cart', []) or []
    # normalize to list of items
    cart_list = []
    if isinstance(raw_cart, dict):
        for cid, entry in raw_cart.items():
            cart_list.append({'id': str(cid), 'qty': int(entry.get('qty', entry.get('quantity', 1))), 'price': float(entry.get('price', 0) or 0)})
    elif isinstance(raw_cart, list):
        for it in raw_cart:
            cart_list.append({'id': str(it.get('id')), 'qty': int(it.get('qty', it.get('quantity', 1))), 'price': float(it.get('price', 0) or 0)})

    if not cart_list:
        messages.error(request, 'سبد خرید شما خالی است')
        return redirect('buy_medicine')

    total_amount = sum(it['qty'] * it['price'] for it in cart_list)

    currency = (request.POST.get('currency') or request.POST.get('currency_code') or 'USDT').upper()
    # choose deposit address generator
    if currency in ('BTC', 'BTC'):
        addr = generate_btc_address()
    elif currency in ('ETH', 'ETHEREUM'):
        addr = generate_eth_address()
    elif currency in ('TRX', 'TRON', 'USDT'):
        addr = generate_trx_address()
    else:
        addr = generate_trx_address()

    try:
        order = Order.objects.create(
            user=request.user,
            amount_usd=Decimal(total_amount),
            currency=currency,
            deposit_address=addr,
            status='PENDING',
            metadata={'cart': cart_list},
        )
    except Exception as e:
        messages.error(request, f'خطا هنگام ایجاد سفارش: {e}')
        return redirect('cart')

    # keep last order id in session for convenience
    request.session['last_order_id'] = str(order.order_id)
    request.session.modified = True
    return redirect('payment', order_id=order.order_id)


def payment(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    lang = request.session.get('language', 'fa')
    # simple context; templates may expect 'total' or 'order'
    context = {
        'order': order,
        'total': getattr(order, 'amount_usd', 0),
        'deposit_address': getattr(order, 'deposit_address', ''),
        'lang': lang,
    }
    return render(request, 'payment.html', context)


def order_success(request):
    lang = request.session.get('language', 'fa')
    return render(request, 'order_success.html', {'lang': lang})


@csrf_exempt
def api_check_payment(request):
    try:
        if request.method == 'POST':
            payload = json.loads(request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body) or {}
            oid = payload.get('order_id')
        else:
            oid = request.GET.get('order_id') or request.GET.get('id')
    except Exception:
        oid = None

    if not oid:
        return JsonResponse({'success': False, 'message': 'order_id required'})

    try:
        order = Order.objects.get(order_id=oid)
        return JsonResponse({'success': True, 'status': order.status})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'order not found'})


# توابع کمکی برای کنترل اسپم خروج
def check_logout_spam(phone):
    if not phone:
        return True, 0
    try:
        user = CustomUser.objects.get(phone=phone)
    except CustomUser.DoesNotExist:
        return True, 0
    hist = getattr(user, "logout_history", []) or []
    if hist:
        last_logout = max(hist)
        if time.time() - last_logout < 300:  # 5 دقیقه
            remaining = 5 - int((time.time() - last_logout) / 60)
            return False, max(1, remaining)
    return True, 0


class ProfileView(View):
    def get(self, request):
        lang = request.session.get('language', 'fa')
        
        # Always fetch fresh data from database
        request.user.refresh_from_db()
        
        # Create form with current user data
        form = AddressForm(instance=request.user)
        template_form = make_template_form(form, request.user)
        
        # Update session with latest user data
        save_user_profile_to_session(request.user, request)
        
        return render(request, 'profile.html', {
            'form': template_form,
            'user': request.user,
            'lang': lang,
            'user_profile': request.session.get('user_profile', {}),
            'wallet_balance': getattr(request.user, 'wallet_balance', '0.00')
        })

    def post(self, request):
        lang = request.session.get('language', 'fa')
        form = AddressForm(request.POST, instance=request.user)
        
        if form.is_valid():
            # Debug: print form data to see what's being submitted
            # print(f"Form data: {form.cleaned_data}")
            
            # Save the form normally - Django ModelForm will handle field updates properly
            user = form.save()
            
            # Debug: print user data after save
            # print(f"User after save: first_name={user.first_name}, last_name={user.last_name}, email={user.email}, address={user.address}")
            
            # Refresh user object to ensure we have the latest data
            user.refresh_from_db()
            
            # Update session with fresh data
            save_user_profile_to_session(user, request)
            
            messages.success(request, _('Profile updated successfully'))
            return redirect('profile')
        else:
            # Form has validation errors - show them to user
            messages.error(request, _('Please correct the errors below'))
            # Debug: print form errors
            # print(f"Form errors: {form.errors}")
        
        # Re-render with form errors
        template_form = make_template_form(form, request.user)
        return render(request, 'profile.html', {
            'form': template_form, 
            'user': request.user, 
            'lang': lang,
            'user_profile': request.session.get('user_profile', {}),
            'wallet_balance': getattr(request.user, 'wallet_balance', '0.00')
        })

# Add this function so urls.py can reference views.profile (keeps existing class-based logic)
@login_required
def profile(request):
    if request.method == 'POST':
        return ProfileView().post(request)
    return ProfileView().get(request)

class OrderHistoryView(View):
    def get(self, request):
        lang = request.session.get('language', 'fa')
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Redirect to login page
            from django.shortcuts import redirect
            return redirect(f"/login/?next={request.path}")
        
        # Get user's orders with their items
        orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
        
        # Calculate summary statistics
        shipped_count = orders.filter(status='SHIPPED').count()
        cancelled_count = orders.filter(status='CANCELLED').count()
        
        context = {
            'orders': orders,
            'lang': lang,
            'shipped_count': shipped_count,
            'cancelled_count': cancelled_count,
        }
        
        return render(request, 'order_history.html', context)


class OrderDetailView(View):
    def get(self, request, order_id):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect(f"/login/?next={request.path}")
        
        # Get the order or 404
        from django.shortcuts import get_object_or_404
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Get order items
        order_items = order.items.all()
        
        lang = request.session.get('language', 'fa')
        
        context = {
            'order': order,
            'order_items': order_items,
            'lang': lang,
        }
        
        return render(request, 'order_detail.html', context)


class GuideView(View):
    def get(self, request):
        lang = request.session.get('language', 'fa')
        text = get_text(lang, 'buying_guide')
        return render(request, 'guide.html', {'text': text})


class SupportView(View):
    def get(self, request):
        lang = request.session.get('language', 'fa')
        text = get_text(lang, 'support_text')
        
        # دریافت تیکت‌های کاربر (5 تای آخر)
        user_tickets = []
        if request.user.is_authenticated:
            from .models import SupportTicket
            user_tickets = SupportTicket.objects.filter(user=request.user)[:5]
        
        return render(request, 'support.html', {
            'text': text,
            'user_tickets': user_tickets
        })
    
    def post(self, request):
        from .models import SupportTicket
        from django.http import JsonResponse
        from django.core.files.storage import default_storage
        
        # بررسی محدودیت 24 ساعته
        user_or_ip = request.user if request.user.is_authenticated else self.get_client_ip(request)
        
        if not SupportTicket.can_user_create_new_ticket(user_or_ip):
            return JsonResponse({
                'error': True,
                'message': 'شما در 24 ساعت گذشته درخواست ثبت کرده‌اید. لطفاً منتظر پاسخ پشتیبانی باشید.'
            }, status=429)
        
        # اعتبارسنجی داده‌ها
        name = request.POST.get('name', '').strip()
        contact = request.POST.get('contact', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        attachment = request.FILES.get('attachment')
        
        # بررسی فیلدهای اجباری
        if not all([name, contact, subject, message]):
            return JsonResponse({
                'error': True,
                'message': 'لطفاً تمام فیلدهای اجباری را تکمیل کنید.'
            }, status=400)
        
        # بررسی اندازه فایل (5MB)
        if attachment and attachment.size > 5 * 1024 * 1024:
            return JsonResponse({
                'error': True,
                'message': 'حجم فایل نباید بیشتر از 5MB باشد.'
            }, status=400)
        
        # ایجاد تیکت
        try:
            ticket = SupportTicket.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                contact=contact,
                subject=subject,
                message=message,
                attachment=attachment,
                ip_address=self.get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'درخواست شما با موفقیت ثبت شد. تیم پشتیبانی در اسرع وقت پاسخ خواهد داد.',
                'ticket_id': str(ticket.ticket_id)[:8],
                'redirect_url': request.path  # برای رفرش صفحه
            })
            
        except Exception as e:
            return JsonResponse({
                'error': True,
                'message': 'خطا در ثبت درخواست. لطفاً دوباره تلاش کنید.'
            }, status=500)
    
    def get_client_ip(self, request):
        """دریافت IP کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ChangeLanguageView(View):
    def get(self, request):
        request.session.pop('language', None)
        return redirect('home')

    def post(self, request):
        lang = request.POST.get('lang')
        if lang in ['fa', 'en', 'tr', 'ar']:
            request.session['language'] = lang
            if request.user.is_authenticated:
                request.user.language = lang
                request.user.save()
        return redirect('home')


class LogoutView(View):
    def get(self, request):
        return HomeView().logout(request)
    
    def post(self, request):
        lang = request.session.get('language', 'fa')
        phone = getattr(request.user, "phone", None)
        allowed, remaining = check_logout_spam(phone) if phone else (True, 0)
        if allowed:
            user = request.user
            hist = getattr(user, "logout_history", []) or []
            hist.append(time.time())
            try:
                user.logout_history = hist
                user.save()
            except Exception:
                pass
            try:
                logout(request)
            except Exception:
                pass
            try:
                request.session.flush()
            except Exception:
                pass
            messages.success(request, get_text(lang, 'logout_success'), extra_tags='logout')
            return redirect('home')
        else:
            messages.error(request, get_text(lang, 'logout_blocked', minutes=remaining))
            return redirect('home')



def view_cart(request):
    return redirect('cart')


@require_POST
@login_required
def cart_add(request: HttpRequest, item_id: str):
    # Find the item in all groups
    item = None
    for group in get_all_groups():
        for variant in group['variants']:
            if variant['id'] == item_id:
                item = variant
                break
        if item:
            break
    
    if not item:
        return HttpResponseBadRequest("Invalid item")
    
    cart = request.session.get(CART_SESSION_KEY, {}) or {}
    try:
        qty = int(request.POST.get("qty") or request.POST.get('quantity') or 1)
    except Exception:
        qty = 1

    # if cart stored as list in session, convert it to dict form
    if isinstance(cart, list):
        new_cart = {}
        for it in cart:
            if isinstance(it, dict) and it.get('id'):
                new_cart[str(it.get('id'))] = it
        cart = new_cart

    entry = cart.get(item_id, {}) if isinstance(cart, dict) else {}
    # compute new quantity
    try:
        existing_qty = int(entry.get('qty', entry.get('quantity', 0)))
    except Exception:
        existing_qty = 0
    new_qty = existing_qty + qty

    # populate normalized dict entry
    entry = {
        'id': item_id,
        'qty': new_qty,
        'quantity': new_qty,
        'price': float(item.get('price') or 0),
        'name': item.get('name') or item.get('title') or '',
        'image': item.get('image'),
        'description': item.get('description'),
    }
    cart[item_id] = entry
    request.session[CART_SESSION_KEY] = cart
    messages.success(request, "محصول به سبد افزوده شد")
    return redirect("buy_medicine")


def cart(request: HttpRequest):
    if request.method == 'POST':
        return CartView().post(request)
    return CartView().get(request)


def medicine_detail(request: HttpRequest, item_id: str):
    ensure_loaded()
    found = None
    for g in get_all_groups():
        for v in g.get('variants', []) or []:
            vid = str(v.get('id') or (v.get('raw') or {}).get('id') or '')
            if vid == str(item_id):
                raw = v.get('raw') or {}
                name = pick_translation(raw, 'name', request.session.get('language', 'fa')) or raw.get('name') or v.get('name') or vid
                desc = pick_translation(raw, 'description', request.session.get('language', 'fa')) or raw.get('description') or v.get('description') or ''
                price = _safe_float(raw.get('price', v.get('price', 0)))
                image = v.get('image') or MEDICINE_IMAGES.get(vid) or ''
                found = {'id': vid, 'name': name, 'description': desc, 'price': price, 'image': image, 'group': g.get('id')}
                break
        if found:
            break
    if not found:
        return render(request, '404.html', status=404)
    return render(request, 'medicine_detail.html', {'item': found})


def cart_remove(request: HttpRequest, item_id: str):
    cart = request.session.get(CART_SESSION_KEY, {}) or {}
    modified = False
    if isinstance(cart, dict):
        if str(item_id) in cart:
            cart.pop(str(item_id), None)
            modified = True
    elif isinstance(cart, list):
        new = [it for it in cart if str(it.get('id')) != str(item_id)]
        if len(new) != len(cart):
            cart = new
            modified = True

    if modified:
        request.session[CART_SESSION_KEY] = cart
        request.session.modified = True
        messages.success(request, 'محصول از سبد حذف شد')
    else:
        messages.warning(request, 'محصولی برای حذف یافت نشد')
    return redirect('cart')


def cart_clear(request: HttpRequest):
    request.session[CART_SESSION_KEY] = {} if isinstance(request.session.get(CART_SESSION_KEY, {}), dict) else []
    request.session.modified = True
    messages.success(request, 'سبد خرید پاک شد')
    return redirect('cart')


def cart_update(request: HttpRequest, item_id: Optional[str] = None):
    if request.method != 'POST':
        return redirect('cart')

    cart = request.session.get(CART_SESSION_KEY, {}) or {}

    def set_qty_for_key(key, qty):
        nonlocal cart
        try:
            q = int(qty)
        except Exception:
            q = 1
        if isinstance(cart, dict):
            entry = cart.get(str(key), {})
            if isinstance(entry, dict):
                # set both legacy 'qty' and canonical 'quantity' for compatibility
                entry['qty'] = q
                entry['quantity'] = q
                cart[str(key)] = entry
            else:
                # if stored as plain number, convert to dict form
                cart[str(key)] = {'qty': q, 'quantity': q}
        elif isinstance(cart, list):
            for it in cart:
                if str(it.get('id')) == str(key):
                    it['qty'] = q
                    it['quantity'] = q

    if item_id:
        # accept either 'quantity' or 'qty' naming from forms
        qty = request.POST.get('quantity') or request.POST.get('qty') or request.POST.get(f'quantity_{item_id}') or request.POST.get(f'qty_{item_id}')
        if qty is not None:
            set_qty_for_key(item_id, qty)
    else:
        # scan for quantity_ keys
        for k, v in request.POST.items():
            if k.startswith('quantity_'):
                key = k.split('quantity_', 1)[1]
                set_qty_for_key(key, v)

    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True
    messages.success(request, 'مقدار سبد بروزرسانی شد')
    return redirect('cart')


@login_required
def checkout(request):
    # Ensure cart exists
    raw_cart = request.session.get(CART_SESSION_KEY, {}) or {}

    # Build quick lookup from loaded medicine groups (id -> meta)
    ensure_loaded()
    variant_lookup: Dict[str, Dict[str, Any]] = {}
    for g in get_all_groups():
        for v in g.get("variants", []) or []:
            raw = v.get("raw") or {}
            vid = str(v.get("id") or raw.get("id") or "")
            name = pick_translation(raw, "name", request.session.get("language", "fa")) or raw.get("name") or v.get("name") or vid
            price = _safe_float(raw.get("price", v.get("price", 0)))
            variant_lookup[vid] = {"id": vid, "name": name, "price": Decimal(str(price or 0))}

    # Normalize cart to list of items
    cart_items_in: List[Dict[str, Any]] = []
    if isinstance(raw_cart, dict):
        for cid, entry in raw_cart.items():
            try:
                qty = int(entry.get("qty", entry.get("quantity", 1)))
            except Exception:
                qty = 1
            price_provided = entry.get("price") if isinstance(entry, dict) else None
            cart_items_in.append({"id": str(cid), "qty": qty, "price": price_provided})
    elif isinstance(raw_cart, list):
        for entry in raw_cart:
            try:
                cid = str(entry.get("id") or "")
                qty = int(entry.get("qty", entry.get("quantity", 1)))
            except Exception:
                cid = str(entry.get("id", "")) or ""
                qty = 1
            price_provided = entry.get("price")
            cart_items_in.append({"id": cid, "qty": qty, "price": price_provided})
    else:
        cart_items_in = []

    if not cart_items_in:
        messages.error(request, 'سبد خرید شما خالی است')
        return redirect('buy_medicine')

    # Compute totals
    cart_items_out: List[Dict[str, Any]] = []
    total_amount_dec = Decimal("0")
    for it in cart_items_in:
        cid = str(it.get("id") or "")
        qty = int(it.get("qty") or 1)

        price_dec = None
        if it.get("price") not in (None, "", 0):
            try:
                price_dec = Decimal(str(it.get("price")))
            except Exception:
                price_dec = None

        if price_dec is None:
            lookup = variant_lookup.get(cid)
            if lookup and isinstance(lookup.get("price"), Decimal):
                price_dec = lookup["price"]
            else:
                price_dec = Decimal("0")

        line_total = (price_dec * Decimal(qty)).quantize(Decimal("0.01"))
        total_amount_dec += line_total

        name = cid
        lookup = variant_lookup.get(cid)
        if lookup:
            name = lookup.get("name") or name

        cart_items_out.append({
            "id": cid,
            "name": name,
            "quantity": qty,
            "price": float(price_dec.quantize(Decimal("0.01"))),
            "total": float(line_total),
        })

    total_amount = float(total_amount_dec.quantize(Decimal("0.01")))

    # --- use unified exchange system ---
    from .exchange import convert_fiat_to_cryptos
    
    # Get crypto conversions using the unified system
    crypto_conversions_raw = convert_fiat_to_cryptos(total_amount, 'usd')
    
    # Transform to match expected format for templates
    crypto_conversions = {}
    crypto_mapping = {
        'bitcoin': 'BTC',
        'ethereum': 'ETH', 
        'tron': 'TRX',
        'tether': 'USDT',
        'binancecoin': 'BNB',
        'the-open-network': 'TON',
        'solana': 'SOL',
        'dogecoin': 'DOGE'
    }
    
    for coin_id, short_name in crypto_mapping.items():
        if coin_id in crypto_conversions_raw:
            data = crypto_conversions_raw[coin_id]
            crypto_conversions[short_name] = {
                "amount": data.get('amount', 0),
                "price": data.get('price', 0),
                "currency": "USD",
            }

    # canonical wallets
    WALLETS = {
        'BTC': 'bc1q68p8twvd9ydfpeekuamkqwgu9wr2tzylnw3fsr',
        'ETH': '0x92c9901894dC0b0ee68865a6DC486CEF0DD73009',
        'TRX': 'TXyorCxyVGHXyeooHsUyf1edpj79WnrRQh',
        'USDT': 'TXyorCxyVGHXyeooHsUyf1edpj79WnrRQh',
        'BNB': '0xaF99374Dd015dA244cdA1F1Fc2183b423a17A10D',
        'TON': 'UQATaVtLxM93Sms6jNJwrMjQ_UOKTOvR2niXyS6ONIkx2HNc',
        'SOL': '9nt397D5ruuTaJVf1WcY6HoQtcthSHEHXek6UFxZUzhQ',
        'DOGE': 'DPbSdTVxAh2KpzDScG1qtJGwkfGAkBSG1A',
    }

    # --- IRR conversion ---
    from .exchange import convert_usd_to_irr
    irr_conversion = convert_usd_to_irr(total_amount_dec)
    
    # Card details for IRR payment
    irr_card_details = {
        "card_number": "5054-1610-0412-1429",
        "bank": "گردشگری",
        "account_holder": " امید احمدی "
    }

    try:
        import json as _json
        wallets_json = _json.dumps(WALLETS)
    except Exception:
        wallets_json = "{}"

    context = {
        "cart_items": cart_items_out,
        "total_amount": total_amount,
        "total_amount_dec": total_amount_dec,
        "crypto_conversions": crypto_conversions,   # ✅ معادل کریپتو
        "irr_conversion": irr_conversion,  # ✅ IRR conversion data
        "irr_card_details": irr_card_details,  # ✅ Card details
        "WALLETS": WALLETS,
        "WALLETS_json": wallets_json,
        "live_rates_url": "/api/live_rates/",
        "qr_base": "/static/images/qr/",
    }

    return render(request, "checkout.html", context)




from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_GET
# already imported at top; removed duplicate import

@require_GET
def api_live_rates(request):
    """Live crypto rates API using unified exchange system"""
    from .exchange import convert_fiat_to_cryptos

    # optional client-provided total to compute per-token amounts
    total_q = request.GET.get('total_usd') or request.GET.get('total')
    try:
        total_amount = float(total_q) if total_q not in (None, '') else 25.0  # Default amount
    except Exception:
        total_amount = 25.0

    # Get conversions using unified system
    conversions = convert_fiat_to_cryptos(total_amount, 'usd')
    
    # Transform to API format
    out = {}
    crypto_mapping = {
        'bitcoin': 'BTC',
        'ethereum': 'ETH', 
        'tron': 'TRX',
        'tether': 'USDT',
        'binancecoin': 'BNB',
        'the-open-network': 'TON',
        'solana': 'SOL',
        'dogecoin': 'DOGE'
    }
    
    for coin_id, short_name in crypto_mapping.items():
        if coin_id in conversions:
            data = conversions[coin_id]
            out[short_name] = {
                "USD": data.get('price', 0),
                "amount": data.get('amount', 0)
            }

    return JsonResponse({"rates": out})


"""Payment check helpers are provided by utils.crypto; duplicates removed here."""

@require_GET
def api_payment_irr(request):
    """API endpoint for IRR payment information"""
    from .exchange import convert_usd_to_irr
    
    # Get USD amount from query parameters
    total_usd = request.GET.get('total_usd', request.GET.get('total', 0))
    
    try:
        total_usd_decimal = Decimal(str(total_usd)) if total_usd else Decimal('0')
    except (ValueError, TypeError):
        return JsonResponse({
            'error': 'Invalid USD amount',
            'price_usd': 0,
            'price_irr': 0
        }, status=400)
    
    if total_usd_decimal <= 0:
        return JsonResponse({
            'error': 'USD amount must be greater than 0',
            'price_usd': 0,
            'price_irr': 0
        }, status=400)
    
    # Convert USD to IRR
    conversion = convert_usd_to_irr(total_usd_decimal)
    
    if not conversion:
        return JsonResponse({
            'error': 'Currency conversion failed',
            'price_usd': float(total_usd_decimal),
            'price_irr': 0
        }, status=500)
    
    # Card details for Iran
    card_details = {
        "card_number": "5054-1610-0412-1429",
        "bank": "Gardeshgari",
        "account_holder": "Omid Ahmadi"
    }
    
    response_data = {
        "price_usd": conversion['usd_amount'],
        "price_irr": conversion['irr_amount'],
        "provider": conversion['provider'],
        "fetched_at": conversion.get('fetched_at'),
        "card_number": card_details["card_number"],
        "bank": card_details["bank"],
        "account_holder": card_details["account_holder"],
        "exchange_rate": conversion['rate']
    }
    
    return JsonResponse(response_data)


# =========================
# کلاس‌ها و ویوها (ساختار حفظ شده)
# =========================

def save_user_profile_to_session(user, request):
    """Save user profile data to session for quick access"""
    try:
        # Ensure user data is fresh from database
        if hasattr(user, 'refresh_from_db'):
            user.refresh_from_db()
            
        profile = {
            'id': getattr(user, 'id', None),
            'username': getattr(user, 'username', None),
            'phone': getattr(user, 'phone', ''),
            'first_name': getattr(user, 'first_name', ''),
            'last_name': getattr(user, 'last_name', ''),
            'email': getattr(user, 'email', ''),
            'address': getattr(user, 'address', ''),
            'is_staff': getattr(user, 'is_staff', False),
            'language': getattr(user, 'language', request.session.get('language', 'fa')),
            'full_name': user.get_full_name() if hasattr(user, 'get_full_name') else '',
        }
        request.session['user_profile'] = profile
        request.session.modified = True
    except Exception as e:
        # Log the error in production, for now just pass
        pass

def make_template_form(real_form, user=None):
    class _Field:
        def __init__(self, v):
            self.value = v if v is not None else ""

    class _Wrapper:
        pass

    wrapper = _Wrapper()
    expected = ["first_name", "last_name", "email", "phone", "address", "language"]
    for name in expected:
        val = ""
        try:
            if getattr(real_form, 'data', None) and real_form.data.get(name) is not None:
                val = real_form.data.get(name)
            elif getattr(real_form, 'initial', None) and real_form.initial.get(name) is not None:
                val = real_form.initial.get(name)
            elif user is not None and hasattr(user, name):
                val = getattr(user, name) or ""
        except Exception:
            val = ""
        setattr(wrapper, name, _Field(val))

    return wrapper

 

class HomeView(View):
    def get(self, request):
        lang = request.session.get('language', 'fa')
        selected = request.GET.get('selected', get_text(lang, 'home'))
        if request.user.is_authenticated:
            if selected == get_text(lang, 'logout'):
                return self.logout(request)
            elif selected == get_text(lang, 'cart'):
                return CartView().get(request)
            elif selected == get_text(lang, 'order_history'):
                return OrderHistoryView().get(request)
            elif selected == get_text(lang, 'guide'):
                return GuideView().get(request)
            elif selected == get_text(lang, 'support'):
                return SupportView().get(request)
            elif selected == get_text(lang, 'profile'):
                return ProfileView().get(request)
            elif selected == get_text(lang, 'change_language'):
                return ChangeLanguageView().get(request)
        return render(request, 'home.html', {'lang': lang})

    def logout(self, request):
        lang = request.session.get('language', 'fa')
        phone = getattr(request.user, "phone", None)
        allowed, remaining = check_logout_spam(phone) if phone else (True, 0)
        if allowed:
            user = request.user
            # اطمینان از نوع داده logout_history
            hist = getattr(user, "logout_history", []) or []
            hist.append(time.time())
            user.logout_history = hist
            user.save()
            logout(request)
            request.session.flush()
            messages.success(request, get_text(lang, 'logout_success'))
            return redirect('login')
        else:
            messages.error(request, get_text(lang, 'logout_blocked', minutes=remaining))
            return redirect('home')


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            # Use globals() to avoid NameError if admin constants or helper are not defined.
            admin_hash = globals().get('ADMIN_PASSWORD_HASH')
            admin_username = globals().get('ADMIN_USERNAME')
            hash_fn = globals().get('hash_password')
            if admin_hash and admin_username and hash_fn and phone == admin_username and hash_fn(password) == admin_hash:
                user, created = CustomUser.objects.get_or_create(username=admin_username, defaults={'is_superuser': True, 'is_staff': True})
                login(request, user)
                # keep session copy
                save_user_profile_to_session(user, request)
                return redirect('admin_panel')
            user = authenticate(username=phone, password=password)
            if user:
                login(request, user)
                request.session['language'] = getattr(user, "language", request.session.get('language', 'fa'))
                # save lightweight profile copy to session for easy access
                save_user_profile_to_session(user, request)
                return redirect('home')
        messages.error(request, _('Invalid credentials'))
        return render(request, 'login.html', {'form': form})


class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                # ensure all fields are set on custom user
                if not getattr(user, 'phone', None):
                    user.phone = form.cleaned_data.get('phone')
                if not getattr(user, 'first_name', None):
                    user.first_name = form.cleaned_data.get('first_name', '')
                if not getattr(user, 'last_name', None):
                    user.last_name = form.cleaned_data.get('last_name', '')
                if not getattr(user, 'email', None):
                    user.email = form.cleaned_data.get('email', '')
                if not getattr(user, 'address', None):
                    user.address = form.cleaned_data.get('address', '')
                user.set_password(form.cleaned_data.get('password'))
                user.save()
                # authenticate using phone (USERNAME_FIELD) and login to ensure backend is set
                user_auth = authenticate(username=user.phone, password=form.cleaned_data.get('password'))
                try:
                    if user_auth:
                        login(request, user_auth)
                    else:
                        # fallback: attach backend attribute so login() can succeed
                        setattr(user, 'backend', 'django.contrib.auth.backends.ModelBackend')
                        login(request, user)
                except Exception:
                    # if login fails, continue without raising to avoid 500s; the template will show errors
                    pass
                request.session['language'] = getattr(user, "language", 'fa')
                # save lightweight profile copy to session for easy access
                save_user_profile_to_session(user, request)
                return redirect('home')
            except IntegrityError:
                # Handle the case where the phone number already exists (backup error handling)
                form.add_error('phone', 'شماره تلفن وارد شده قبلاً ثبت شده است.')
        return render(request, 'register.html', {'form': form})


class AdminPanelView(View):
    def get(self, request):
        if not request.user.is_superuser:
            return redirect('login')
        users = CustomUser.objects.all()
        orders = Order.objects.all()
        search_term = request.GET.get('search', '')
        if search_term:
            users = users.filter(phone__icontains=search_term) | users.filter(address__icontains=search_term)
            orders = orders.filter(user__phone__icontains=search_term)
        stats = {
            'total_users': users.count(),
            'total_orders': orders.count(),
        }
        return render(request, 'admin_panel.html', {'users': users, 'orders': orders, 'stats': stats})


    def _finalize_cart_update_response(request, cart):
        request.session[CART_SESSION_KEY] = cart
        request.session.modified = True
    
        response_items = []
        cart_total = 0.0
        if isinstance(cart, dict):
            for cid, entry in cart.items():
                try:
                    qty = int(entry.get('qty', entry.get('quantity', 1)))
                except Exception:
                    qty = 1
                try:
                    price = float(entry.get('price', 0) or 0)
                except Exception:
                    price = 0.0
                subtotal = round(qty * price, 2)
                response_items.append({'id': cid, 'quantity': qty, 'subtotal': subtotal})
                cart_total += subtotal
        else:
            for entry in cart:
                cid = str(entry.get('id'))
                try:
                    qty = int(entry.get('qty', entry.get('quantity', 1)))
                except Exception:
                    qty = 1
                try:
                    price = float(entry.get('price', 0) or 0)
                except Exception:
                    price = 0.0
                subtotal = round(qty * price, 2)
                response_items.append({'id': cid, 'quantity': qty, 'subtotal': subtotal})
                cart_total += subtotal
    
        return JsonResponse({'success': True, 'items': response_items, 'cart_total': round(cart_total, 2)})


@csrf_exempt
@require_http_methods(["POST"])
def api_cart_remove(request):
    try:
        payload = json.loads(request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body) or {}
    except Exception:
        payload = {}
    cid = str(payload.get('id') or '')
    if not cid:
        return JsonResponse({'success': False, 'message': 'Invalid id'})
    cart = request.session.get(CART_SESSION_KEY, {}) or {}
    modified = False
    if isinstance(cart, dict):
        if cid in cart:
            cart.pop(cid, None)
            modified = True
    else:
        new = [it for it in cart if str(it.get('id')) != cid]
        if len(new) != len(cart):
            cart = new
            modified = True
    if modified:
        request.session[CART_SESSION_KEY] = cart
        request.session.modified = True

    cart_total = 0.0
    if isinstance(cart, dict):
        for entry in cart.values():
            try:
                qty = int(entry.get('qty', entry.get('quantity', 1)))
            except Exception:
                qty = 1
            try:
                price = float(entry.get('price', 0) or 0)
            except Exception:
                price = 0.0
            cart_total += qty * price
    else:
        for entry in cart:
            try:
                qty = int(entry.get('qty', entry.get('quantity', 1)))
            except Exception:
                qty = 1
            try:
                price = float(entry.get('price', 0) or 0)
            except Exception:
                price = 0.0
            cart_total += qty * price

    return JsonResponse({'success': True, 'cart_total': round(cart_total, 2)})


@csrf_exempt
@require_http_methods(["POST"])
def api_cart_update(request):
    try:
        payload = json.loads(request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body) or {}
    except Exception:
        payload = {}
    items = payload.get('items') or []
    cart = request.session.get(CART_SESSION_KEY, {}) or {}

    # ensure dict-form cart
    if isinstance(cart, list):
        new_cart = {}
        for it in cart:
            if isinstance(it, dict) and it.get('id'):
                new_cart[str(it.get('id'))] = it
        cart = new_cart

    modified = False
    for it in items:
        cid = str(it.get('id') or '')
        if not cid:
            continue
        try:
            qty = max(1, int(it.get('quantity') or it.get('qty') or 1))
        except Exception:
            qty = 1
        price = None
        try:
            if it.get('price') is not None and it.get('price') != '':
                price = float(it.get('price'))
        except Exception:
            price = None

        entry = cart.get(cid, {}) if isinstance(cart, dict) else {}
        entry['id'] = cid
        entry['qty'] = qty
        entry['quantity'] = qty
        if price is not None:
            entry['price'] = price
        else:
            entry.setdefault('price', entry.get('price', 0))
        cart[cid] = entry
        modified = True

    if modified:
        request.session[CART_SESSION_KEY] = cart
        request.session.modified = True

    # compute response items and total
    response_items = []
    cart_total = 0.0
    if isinstance(cart, dict):
        for cid, entry in cart.items():
            try:
                qty = int(entry.get('qty', entry.get('quantity', 1)))
            except Exception:
                qty = 1
            try:
                price = float(entry.get('price', 0) or 0)
            except Exception:
                price = 0.0
            subtotal = round(qty * price, 2)
            response_items.append({'id': cid, 'quantity': qty, 'subtotal': subtotal})
            cart_total += subtotal
    else:
        for entry in cart:
            cid = str(entry.get('id'))
            try:
                qty = int(entry.get('qty', entry.get('quantity', 1)))
            except Exception:
                qty = 1
            try:
                price = float(entry.get('price', 0) or 0)
            except Exception:
                price = 0.0
            subtotal = round(qty * price, 2)
            response_items.append({'id': cid, 'quantity': qty, 'subtotal': subtotal})
            cart_total += subtotal

    return JsonResponse({'success': True, 'items': response_items, 'cart_total': round(cart_total, 2)})
