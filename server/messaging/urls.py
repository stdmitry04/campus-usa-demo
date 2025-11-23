# server/messaging/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from messaging.views.base_views import *
from messaging.views.embedding_views import (
	EmbeddingView, BatchEmbeddingView, RAGProfileView,
	RAGDocumentView, RAGRetrievalView, RAGContextualPromptView, RAGStatsView
)

# set up the router for CRUD operations on conversations
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
	# messaging-specific endpoints
	path('send-message/', SendMessageView.as_view(), name='send-message'),
	path('stats/', ConversationStatsView.as_view(), name='conversation-stats'),

	# embedding endpoints - core rag functionality
	path('embed/', EmbeddingView.as_view(), name='embed'),
	path('embed/batch/', BatchEmbeddingView.as_view(), name='batch-embed'),

	# rag management endpoints
	path('rag/profile/', RAGProfileView.as_view(), name='rag-profile'),
	path('rag/document/', RAGDocumentView.as_view(), name='rag-document'),
	path('rag/retrieve/', RAGRetrievalView.as_view(), name='rag-retrieve'),
	path('rag/prompt/', RAGContextualPromptView.as_view(), name='rag-prompt'),
	path('rag/stats/', RAGStatsView.as_view(), name='rag-stats'),

	# conversation endpoints
	# GET /api/messaging/conversations/ - list user's conversations
	# POST /api/messaging/conversations/ - create new conversation
	# GET /api/messaging/conversations/{id}/ - get specific conversation with messages
	# PUT/PATCH /api/messaging/conversations/{id}/ - update conversation
	# DELETE /api/messaging/conversations/{id}/ - delete conversation
	path('', include(router.urls)),
]