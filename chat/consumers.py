import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import ChatRoom, ChatMessage

logger = logging.getLogger(__name__)


def _room_group(room_id: int) -> str:
    return f"chat.room.{room_id}"

AGENT_GROUP = "chat.agents"


class UserChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room = await self._get_or_create_room()
        self.room_group_name = _room_group(self.room.id)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        # send history (last 30 msgs)
        history = await self._get_history()
        await self.send_json({"type": "history", "messages": history, "room_id": self.room.id})

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg = (content or {}).get("message", "").strip()
        name = (content or {}).get("name", "").strip()
        contact = (content or {}).get("contact", "").strip()
        subject = (content or {}).get("subject", "").strip()
        
        # Handle guest info update
        if name or contact:
            await self._update_guest_info(name, contact, subject)
        
        # Handle typing indicators
        typing_type = (content or {}).get("type")
        if typing_type == "typing":
            status = (content or {}).get("status", "stop")
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "typing_start" if status == "start" else "typing_stop"}
            )
            return
        
        if not msg:
            return
            
        saved = await self._create_message(role="user", content=msg)
        
        # Check if message creation was blocked
        if saved is None:
            await self.send_json({
                "type": "error", 
                "message": "شما توسط پشتیبان مسدود شده‌اید و نمی‌توانید پیام ارسال کنید."
            })
            return
            
        logger.info(f"User message sent: {saved.id} in room {self.room.id}")
        
        # fan out to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": self._serialize_message(saved)}
        )
        
        # notify agents feed
        sender_id = saved.sender.id if saved.sender else None
        await self.channel_layer.group_send(
            AGENT_GROUP,
            {"type": "agent.notify", "room_id": self.room.id, "message": self._serialize_message(saved), "sender_id": sender_id}
        )
        logger.info(f"Sent agent notify for room {self.room.id} to AGENT_GROUP with sender_id {sender_id}")

    async def typing_start(self, event):
        await self.send_json({"type": "typing", "user": "agent", "status": "start"})

    async def typing_stop(self, event):
        await self.send_json({"type": "typing", "user": "agent", "status": "stop"})

    async def chat_message(self, event):
        await self.send_json({"type": "message", "message": event["message"]})

    async def chat_clear(self, event):
        # Instruct client to clear messages UI
        await self.send_json({"type": "clear"})

    async def chat_deleted(self, event):
        # Instruct client that chat has been deleted
        await self.send_json({"type": "chat_deleted", "message": "چت توسط پشتیبانی حذف شد"})

    @database_sync_to_async
    def _get_or_create_room(self):
        user = self.scope.get("user")
        session = self.scope.get("session")
        session_key = getattr(session, 'session_key', None) or ''
        if session and not session.session_key:
            session.save()  # ensure key
            session_key = session.session_key
        if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
            room, _ = ChatRoom.objects.get_or_create(user=user, defaults={"session_key": session_key})
        else:
            room, _ = ChatRoom.objects.get_or_create(user=None, session_key=session_key)
        return room

    @database_sync_to_async
    def _get_history(self):
        msgs = self.room.messages.select_related("sender").order_by("-created_at")[:30]
        return [self._serialize_message(m) for m in reversed(list(msgs))]

    @database_sync_to_async
    def _create_message(self, role: str, content: str):
        # Check if user is blocked before allowing message creation
        if role == "user":
            if self.room.is_user_blocked():
                # Return None or raise an exception to indicate blocked status
                return None
        
        sender = self.scope.get("user") if role == "agent" else None
        msg = ChatMessage.objects.create(
            room=self.room, role=role, sender=sender, content=content, created_at=timezone.now()
        )
        # bump room activity timestamp
        ChatRoom.objects.filter(id=self.room.id).update(updated_at=timezone.now())
        return msg

    @database_sync_to_async
    def _update_guest_info(self, name, contact, subject=None):
        updated = False
        if name and (not self.room.guest_name or len(name.strip()) > len(self.room.guest_name.split(' - ')[0] if ' - ' in self.room.guest_name else self.room.guest_name)):
            base_name = name.strip()[:120]
            if subject:
                self.room.guest_name = f"{base_name} - {subject.strip()[:80]}"[:120]
                self.room.guest_subject = subject.strip()[:200]
            else:
                self.room.guest_name = base_name
            updated = True
        if contact and (not self.room.guest_contact or len(contact.strip()) > len(self.room.guest_contact)):
            self.room.guest_contact = contact.strip()[:255]
            updated = True
        if subject and not self.room.guest_subject:
            self.room.guest_subject = subject.strip()[:200]
            # Update guest_name to include subject if it doesn't already
            if self.room.guest_name and ' - ' not in self.room.guest_name:
                base_name = self.room.guest_name.split(' - ')[0]
                self.room.guest_name = f"{base_name} - {subject.strip()[:80]}"[:120]
            updated = True
            
        if updated:
            update_fields = ["guest_name", "guest_contact", "updated_at"]
            if subject:
                update_fields.append("guest_subject")
            self.room.save(update_fields=update_fields)

    def _serialize_message(self, m: ChatMessage):
        return {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
            "sender": getattr(m.sender, 'phone', None),
        }


class AgentChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated or not user.is_staff:
            await self.close()
            return
        # normalize room id
        rid = self.scope['url_route']['kwargs'].get('room_id')
        try:
            self.room_id = int(rid)
        except Exception:
            await self.close()
            return
        self.room_group_name = _room_group(self.room_id)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        # send recent history to the agent for context
        history = await self._get_history(self.room_id)
        await self.send_json({"type": "history", "messages": history, "room_id": self.room_id})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg = (content or {}).get('message', '').strip()
        
        # Handle typing indicators
        typing_type = (content or {}).get("type")
        if typing_type == "typing":
            status = (content or {}).get("status", "stop")
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "typing_start" if status == "start" else "typing_stop"}
            )
            return
            
        if not msg:
            return
            
        saved = await self._create_agent_message(self.room_id, msg)
        logger.info(f"Agent message sent: {saved.id} in room {self.room_id}")
        
        # Mark user messages as read when agent responds
        await self._mark_messages_read(self.room_id)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": self._serialize_message(saved)}
        )
        # notify other agents (exclude self)
        await self.channel_layer.group_send(
            AGENT_GROUP,
            {"type": "agent.notify", "room_id": self.room_id, "message": self._serialize_message(saved), "sender_id": self.scope['user'].id}
        )

    async def typing_start(self, event):
        await self.send_json({"type": "typing", "user": "user", "status": "start"})

    async def typing_stop(self, event):
        await self.send_json({"type": "typing", "user": "user", "status": "stop"})

    async def chat_message(self, event):
        await self.send_json({"type": "message", "message": event["message"]})

    async def chat_clear(self, event):
        await self.send_json({"type": "clear"})

    async def chat_deleted(self, event):
        # Instruct agent that chat has been deleted
        await self.send_json({"type": "chat_deleted", "message": "چت حذف شد"})

    @database_sync_to_async
    def _create_agent_message(self, room_id: int, content: str):
        room = ChatRoom.objects.get(id=room_id)
        sender = self.scope.get('user')
        msg = ChatMessage.objects.create(
            room=room, role='agent', sender=sender, content=content, created_at=timezone.now()
        )
        ChatRoom.objects.filter(id=room_id).update(updated_at=timezone.now())
        return msg

    @database_sync_to_async
    def _mark_messages_read(self, room_id: int):
        """Mark all user messages in this room as read"""
        ChatMessage.objects.filter(room_id=room_id, role='user', is_read=False).update(is_read=True)

    @database_sync_to_async
    def _get_history(self, room_id: int):
        qs = ChatMessage.objects.filter(room_id=room_id).select_related("sender").order_by("-created_at")[:50]
        return [self._serialize_message(m) for m in reversed(list(qs))]

    def _serialize_message(self, m: ChatMessage):
        return {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
            "sender": getattr(m.sender, 'phone', None),
        }


class AgentFeedConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated or not user.is_staff:
            await self.close()
            return
        await self.channel_layer.group_add(AGENT_GROUP, self.channel_name)
        await self.accept()
        # send recent rooms snapshot
        rooms = await self._recent_rooms()
        await self.send_json({"type": "rooms", "rooms": rooms})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(AGENT_GROUP, self.channel_name)

    async def agent_notify(self, event):
        # forward notification to client only if not from self
        sender_id = event.get("sender_id")
        current_user_id = self.scope['user'].id if self.scope.get('user') else None
        logger.info(f"AgentFeedConsumer received notify: room_id={event.get('room_id')}, sender_id={sender_id}, current_user_id={current_user_id}")
        if sender_id != current_user_id:
            await self.send_json({"type": "notify", "room_id": event.get("room_id"), "message": event.get("message")})
            logger.info(f"Sent notify to agent feed client")

    @database_sync_to_async
    def _recent_rooms(self):
        out = []
        for r in ChatRoom.objects.select_related('user').prefetch_related('messages').order_by('-updated_at')[:50]:
            last = r.messages.order_by('-created_at').first()
            unread_count = r.messages.filter(is_read=False, role='user').count()
            
            # Use the model's get_display_name method
            title = r.get_display_name()
            
            out.append({
                "id": r.id,
                "title": title,
                "last": last.content if last else "",
                "last_at": (last.created_at.isoformat() if last else r.updated_at.isoformat()),
                "count": r.messages.count(),
                "unread": unread_count > 0,
                "unread_count": unread_count,
                "is_authenticated": r.user is not None,
                "contact": r.guest_contact if r.guest_contact else (r.user.phone if r.user else ""),
            })
        return out

    async def chat_deleted(self, event):
        """Handle chat deletion notification"""
        # Send updated rooms list after deletion
        rooms = await self._recent_rooms()
        await self.send_json({
            "type": "chat_deleted", 
            "room_id": event.get("room_id"),
            "room_info": event.get("room_info", {}),
            "rooms": rooms  # Updated rooms list without deleted chat
        })
