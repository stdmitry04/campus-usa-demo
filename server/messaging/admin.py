# server/messaging/admin.py
from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
	list_display = ['title', 'user', 'created_at', 'updated_at']
	search_fields = ['title', 'user__username']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ['conversation', 'sender', 'content_preview', 'created_at']
	list_filter = ['sender']
	search_fields = ['content']

	def content_preview(self, obj):
		return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

	content_preview.short_description = "content"