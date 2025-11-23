# server/messaging/embedding_views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from core.services.embedding_service import embedding_service
from core.services.rag_service import rag_service
import logging

logger = logging.getLogger(__name__)


class EmbeddingView(APIView):
    """generate embeddings for text - used by frontend rag system"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """generate embedding for provided text"""
        try:
            text = request.data.get('text', '').strip()

            if not text:
                return Response({
                    'error': 'text is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # validate text length
            if len(text) > 50000:  # 50k char limit
                return Response({
                    'error': 'text too long (max 50,000 characters)'
                }, status=status.HTTP_400_BAD_REQUEST)

            # generate embedding
            result = embedding_service.generate_embedding(text)

            return Response({
                'embedding': result['embedding'],
                'model': result['model'],
                'dimensions': result['dimensions'],
                'cached': result.get('cached', False),
                'processing_time': result.get('processing_time', 0),
                'usage': result.get('usage', {})
            })

        except ValidationError as e:
            logger.error(f"validation error in embedding: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"unexpected error in embedding: {e}")
            return Response({
                'error': 'failed to generate embedding'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BatchEmbeddingView(APIView):
    """generate embeddings for multiple texts"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """generate embeddings for multiple texts"""
        try:
            texts = request.data.get('texts', [])

            if not texts or not isinstance(texts, list):
                return Response({
                    'error': 'texts array is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            if len(texts) > 100:
                return Response({
                    'error': 'too many texts (max 100)'
                }, status=status.HTTP_400_BAD_REQUEST)

            # validate each text
            for i, text in enumerate(texts):
                if not isinstance(text, str):
                    return Response({
                        'error': f'text at index {i} must be a string'
                    }, status=status.HTTP_400_BAD_REQUEST)

                if len(text) > 10000:
                    return Response({
                        'error': f'text at index {i} too long (max 10,000 characters for batch)'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # generate embeddings
            results = embedding_service.generate_batch_embeddings(texts)

            return Response({
                'embeddings': results,
                'count': len(results)
            })

        except Exception as e:
            logger.error(f"error in batch embedding: {e}")
            return Response({
                'error': 'failed to generate batch embeddings'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RAGProfileView(APIView):
    """manage rag profile embedding"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """embed user profile"""
        try:
            result = rag_service.embed_user_profile(request.user)

            if result['success']:
                return Response({
                    'message': 'profile embedded successfully',
                    'processing_time': result['processing_time'],
                    'content_length': result['content_length'],
                    'model': result['model'],
                    'cached': result['cached']
                })
            else:
                return Response({
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"error embedding profile for user {request.user.id}: {e}")
            return Response({
                'error': 'failed to embed profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """get profile embedding status"""
        try:
            stats = rag_service.get_user_stats(request.user)
            has_profile = stats['profile_chunks'] > 0

            return Response({
                'has_profile_embedding': has_profile,
                'stats': stats
            })

        except Exception as e:
            logger.error(f"error getting profile status for user {request.user.id}: {e}")
            return Response({
                'error': 'failed to get profile status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RAGDocumentView(APIView):
    """manage rag document embedding"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """embed a document"""
        try:
            document_id = request.data.get('document_id')

            if not document_id:
                return Response({
                    'error': 'document_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # get document
            from documents.models import Document
            try:
                document = Document.objects.get(id=document_id, user=request.user)
            except Document.DoesNotExist:
                return Response({
                    'error': 'document not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # embed document
            result = rag_service.embed_document(request.user, document)

            if result['success']:
                return Response({
                    'message': f'document embedded successfully',
                    'chunks_created': result['chunks_created'],
                    'processing_time': result['processing_time'],
                    'document_type': result['document_type']
                })
            else:
                return Response({
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"error embedding document: {e}")
            return Response({
                'error': 'failed to embed document'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RAGRetrievalView(APIView):
    """retrieve relevant context for queries"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """retrieve context for a query"""
        try:
            query = request.data.get('query', '').strip()
            top_k = request.data.get('top_k', 5)

            if not query:
                return Response({
                    'error': 'query is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # validate top_k
            if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
                top_k = 5

            # retrieve context
            result = rag_service.retrieve_context(request.user, query, top_k)

            return Response({
                'contexts': result['contexts'],
                'has_context': result['has_context'],
                'processing_time': result['processing_time'],
                'query_embedding_cached': result.get('query_embedding_cached', False)
            })

        except Exception as e:
            logger.error(f"error retrieving context: {e}")
            return Response({
                'error': 'failed to retrieve context'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RAGContextualPromptView(APIView):
    """build contextualized prompts for ai"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """build contextual prompt for query"""
        try:
            query = request.data.get('query', '').strip()
            max_context_length = request.data.get('max_context_length', 3000)

            if not query:
                return Response({
                    'error': 'query is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # validate max_context_length
            if not isinstance(max_context_length, int) or max_context_length < 500:
                max_context_length = 3000

            # build prompt
            result = rag_service.build_contextual_prompt(
                request.user, query, max_context_length
            )

            return Response({
                'system_prompt': result['system_prompt'],
                'user_prompt': result['user_prompt'],
                'contexts_used': result['contexts_used'],
                'has_context': result['has_context'],
                'context_length': result.get('context_length', 0),
                'processing_time': result['processing_time']
            })

        except Exception as e:
            logger.error(f"error building contextual prompt: {e}")
            return Response({
                'error': 'failed to build contextual prompt'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RAGStatsView(APIView):
    """get rag system statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """get user's rag statistics"""
        try:
            user_stats = rag_service.get_user_stats(request.user)
            embedding_stats = embedding_service.get_stats()

            return Response({
                'user_stats': user_stats,
                'embedding_stats': embedding_stats,
                'system_ready': user_stats['total_chunks'] > 0
            })

        except Exception as e:
            logger.error(f"error getting rag stats: {e}")
            return Response({
                'error': 'failed to get rag statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """clear all rag data for user"""
        try:
            cleared = rag_service.clear_user_data(request.user)

            return Response({
                'message': 'rag data cleared successfully' if cleared else 'no data to clear',
                'cleared': cleared
            })

        except Exception as e:
            logger.error(f"error clearing rag data: {e}")
            return Response({
                'error': 'failed to clear rag data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)