from django.db import models
from django.conf import settings
from django.utils import timezone


class ChatRoom(models.Model):
    """Represents a chat session between a visitor (anonymous or user) and staff."""
    # If a user is authenticated we bind the room; otherwise, we only keep a session key and optional name/contact
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='chat_rooms'
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    guest_name = models.CharField(max_length=120, blank=True)
    guest_contact = models.CharField(max_length=255, blank=True)
    guest_subject = models.CharField(max_length=200, blank=True)  # New field for subject
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False, help_text="مسدود شده توسط پشتیبان")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        who = self.user.phone if self.user_id else (self.guest_name or self.session_key[:8])
        return f"ChatRoom({who})"

    def get_display_name(self):
        """Get formatted display name for admin panel"""
        if self.user:
            return f"{self.user.phone} (عضو)"
        elif self.guest_name:
            if self.guest_subject:
                return f"{self.guest_name} - {self.guest_subject}"
            return self.guest_name
        return f"مهمان ({self.session_key[:8]})"

    def get_unread_count(self):
        """Get count of unread messages from users"""
        return self.messages.filter(is_read=False, role='user').count()

    def is_user_blocked(self):
        """Check if the user or chat room is blocked"""
        if self.is_blocked:
            return True
        if self.user and hasattr(self.user, 'is_blocked'):
            return self.user.is_blocked
        return False


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    # role: 'user' (visitor) | 'agent' (staff)
    role = models.CharField(max_length=16, choices=(('user', 'user'), ('agent', 'agent')))
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:30]}"
