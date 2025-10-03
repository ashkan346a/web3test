from django.contrib import admin
from .models import ChatRoom, ChatMessage


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "guest_name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("session_key", "guest_name", "guest_contact", "user__phone")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "role", "sender", "short", "created_at", "is_read")
    list_filter = ("role", "is_read", "created_at")
    search_fields = ("content",)

    def short(self, obj):
        return (obj.content or "")[:50]
