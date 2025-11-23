# server/messaging/base_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

import time
# from core.services import ai_service
from messaging.models import Conversation, Message
from messaging.serializers import ConversationSerializer, ConversationListSerializer
from core.services.ai_service import get_ai_service
from core.services.rag_service import rag_service
import logging

logger = logging.getLogger(__name__)
ai_service = get_ai_service()

class ConversationViewSet(viewsets.ModelViewSet):
	"""ai assistant conversations - handles CRUD operations"""
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		# only return conversations belonging to the current user
		return Conversation.objects.filter(user=self.request.user).prefetch_related('messages')

	def get_serializer_class(self):
		# use different serializers for list vs detail views
		if self.action == 'list':
			return ConversationListSerializer
		return ConversationSerializer

	def perform_create(self, serializer):
		# automatically set the user when creating a conversation
		serializer.save(user=self.request.user)

	def perform_destroy(self, instance):
		# make sure user can only delete their own conversations
		if instance.user != self.request.user:
			logger.warning(f"user {self.request.user.id} tried to delete conversation {instance.id} belonging to {instance.user.id}")
			return Response({'error': 'permission denied'}, status=status.HTTP_403_FORBIDDEN)

		logger.info(f"deleting conversation {instance.id} for user {self.request.user.id}")
		instance.delete()


class SendMessageView(APIView):
	"""send message with automatic rag context retrieval"""
	permission_classes = [IsAuthenticated]

	def post(self, request):
		"""send message with built-in rag context"""
		try:
			message_content = request.data.get('message', '').strip()
			conversation_id = request.data.get('conversation_id')
			use_rag = request.data.get('use_rag', True)  # allow disabling rag if needed

			if not message_content:
				return Response({
					'error': 'message is required'
				}, status=status.HTTP_400_BAD_REQUEST)

			# get or create conversation
			if conversation_id:
				try:
					conversation = Conversation.objects.get(id=conversation_id, user=request.user)
				except Conversation.DoesNotExist:
					return Response({
						'error': 'conversation not found'
					}, status=status.HTTP_404_NOT_FOUND)
			else:
				conversation = Conversation.objects.create(
					user=request.user,
					title=message_content[:50] + '...' if len(message_content) > 50 else message_content
				)

			# get conversation history
			recent_messages = Message.objects.filter(
				conversation=conversation
			).order_by('-created_at')[:10]  # last 10 messages

			conversation_history = []
			for msg in reversed(recent_messages):  # reverse to get chronological order
				conversation_history.append({
					'sender': msg.sender,
					'content': msg.content,
					'created_at': msg.created_at
				})

			# generate ai response with automatic rag context
			logger.info(f"🤖 generating response for user {request.user.id} with auto-rag")

			ai_response = ai_service.generate_response(
				user_message=message_content,
				conversation_history=conversation_history,
				user=request.user,
				use_rag=use_rag
			)

			if not ai_response['success']:
				return Response({
					'error': 'failed to generate response',
					'details': ai_response.get('error', 'unknown error')
				}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

			# save user message
			user_message = Message.objects.create(
				conversation=conversation,
				sender='user',
				content=message_content,
				metadata={
					'timestamp': time.time(),
					'message_length': len(message_content)
				}
			)

			# save ai response
			ai_message = Message.objects.create(
				conversation=conversation,
				sender='assistant',
				content=ai_response['content'],
				metadata={
					'ai_stats': {
						'model_used': ai_response['model_used'],
						'response_time': ai_response['response_time'],
						'rag_used': ai_response['rag_used'],
						'rag_stats': ai_response.get('rag_stats', {}),
						'usage': ai_response.get('usage', {})
					},
					'timestamp': time.time()
				}
			)

			# update conversation
			conversation.message_count = Message.objects.filter(conversation=conversation).count()
			conversation.save()

			logger.info(f"✅ message sent and response generated for user {request.user.id}")

			return Response({
				'conversation_id': conversation.id,
				'user_message': {
					'id': user_message.id,
					'content': user_message.content,
					'sender': user_message.sender,
					'created_at': user_message.created_at,
					'metadata': user_message.metadata
				},
				'ai_message': {
					'id': ai_message.id,
					'content': ai_message.content,
					'sender': ai_message.sender,
					'created_at': ai_message.created_at,
					'metadata': ai_message.metadata
				},
				'conversation': {
					'id': conversation.id,
					'title': conversation.title,
					'message_count': conversation.message_count
				},
				# include rag context info for debugging/ui
				'rag_info': {
					'rag_used': ai_response['rag_used'],
					'rag_stats': ai_response.get('rag_stats', {}),
					'contexts_used': ai_response.get('rag_stats', {}).get('contexts_used', 0),
					'has_context': ai_response.get('rag_stats', {}).get('has_context', False)
				}
			})

		except Exception as e:
			logger.error(f"error in send message: {e}")
			return Response({
				'error': 'failed to send message'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversationStatsView(APIView):
	"""get conversation statistics for the user with rag integration"""
	permission_classes = [IsAuthenticated]

	def get(self, request):
		user_conversations = Conversation.objects.filter(user=request.user)
		total_conversations = user_conversations.count()
		total_messages = Message.objects.filter(conversation__user=request.user).count()

		# get recent activity (last 7 days)
		from datetime import datetime, timedelta
		week_ago = datetime.now() - timedelta(days=7)
		recent_conversations = user_conversations.filter(created_at__gte=week_ago).count()

		# get rag stats
		try:
			rag_stats = rag_service.get_user_stats(request.user)
		except Exception as e:
			logger.warning(f"failed to get rag stats for user {request.user.id}: {e}")
			rag_stats = {
				'total_chunks': 0,
				'profile_chunks': 0,
				'document_chunks': 0,
				'unique_documents': 0
			}

		return Response({
			'total_conversations': total_conversations,
			'total_messages': total_messages,
			'recent_conversations': recent_conversations,
			'avg_messages_per_conversation': round(total_messages / max(total_conversations, 1), 1),
			'rag_stats': rag_stats,
			'rag_enabled': rag_stats['total_chunks'] > 0
		})


class StartConversationView(APIView):
	"""start new conversation with optional rag context check"""
	permission_classes = [IsAuthenticated]

	def post(self, request):
		"""start new conversation with context readiness check"""
		try:
			initial_message = request.data.get('message', '').strip()
			metadata = request.data.get('metadata', {})

			# create new conversation
			conversation = Conversation.objects.create(
				user=request.user,
				title=initial_message[:50] + ('...' if len(initial_message) > 50 else '') if initial_message else 'new conversation'
			)

			response_data = {
				'conversation_id': str(conversation.id),
				'title': conversation.title,
				'created_at': conversation.created_at.isoformat()
			}

			# if initial message provided, process it
			if initial_message:
				# delegate to send message view
				message_view = SendMessageView()
				message_view.ai_service = ai_service

				# create fake request for delegation
				class FakeRequest:
					def __init__(self, user, data):
						self.user = user
						self.data = data

				fake_request = FakeRequest(request.user, {
					'conversation_id': str(conversation.id),
					'message': initial_message,
					'metadata': metadata
				})

				message_response = message_view.post(fake_request)
				if message_response.status_code == 200:
					response_data.update(message_response.data)

			# add rag readiness info
			try:
				rag_stats = rag_service.get_user_stats(request.user)
				response_data['rag_ready'] = rag_stats['total_chunks'] > 0
				response_data['rag_stats'] = rag_stats
			except Exception as e:
				logger.warning(f"failed to get rag readiness for user {request.user.id}: {e}")
				response_data['rag_ready'] = False

			return Response(response_data)

		except Exception as e:
			logger.error(f"error starting conversation: {e}")
			return Response({
				'error': 'failed to start conversation'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)