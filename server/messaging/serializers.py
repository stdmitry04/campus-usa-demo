# server/messaging/serializers.py
from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
	"""individual chat messages"""

	class Meta:
		model = Message
		fields = [
			'id', 'sender', 'content', 'response_time',
			'model_used', 'created_at'
		]
		read_only_fields = ['response_time', 'model_used']


class ConversationSerializer(serializers.ModelSerializer):
	"""chat conversations with nested messages"""
	messages = MessageSerializer(many=True, read_only=True)
	message_count = serializers.SerializerMethodField()

	class Meta:
		model = Conversation
		fields = [
			'id', 'title', 'message_count', 'messages',
			'created_at', 'updated_at'
		]

	def get_message_count(self, obj):
		"""returns the number of messages in this conversation"""
		return obj.messages.count()


class ConversationListSerializer(serializers.ModelSerializer):
	"""simplified conversation list without all messages"""
	message_count = serializers.SerializerMethodField()
	last_message = serializers.SerializerMethodField()

	class Meta:
		model = Conversation
		fields = [
			'id', 'title', 'message_count', 'last_message',
			'created_at', 'updated_at'
		]

	def get_message_count(self, obj):
		return obj.messages.count()

	def get_last_message(self, obj):
		"""get the most recent message preview"""
		last_msg = obj.messages.last()
		if last_msg:
			return {
				'content': last_msg.content[:100],  # first 100 chars
				'sender': last_msg.sender,
				'created_at': last_msg.created_at
			}
		return None