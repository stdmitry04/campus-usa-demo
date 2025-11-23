# # server/documents/signals.py
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from django.contrib.auth.models import User
# from .models import Document
# from core.services.rag_service import rag_service
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# @receiver(post_save, sender=Document)
# def auto_embed_document(sender, instance, created, **kwargs):
#     """automatically embed document when it's completed"""
#     # only embed completed documents
#     if instance.status != 'completed':
#         return
#
#     # skip if document was just created (not updated to completed)
#     if created:
#         return
#
#     try:
#         logger.info(f"🔄 auto-embedding document {instance.id} for user {instance.user.id}")
#         result = rag_service.embed_document(instance.user, instance)
#
#         if result['success']:
#             logger.info(f"✅ auto-embedded document {instance.id} ({result['chunks_created']} chunks)")
#         else:
#             logger.warning(f"⚠️ auto-embedding failed for document {instance.id}: {result.get('error')}")
#
#     except Exception as e:
#         logger.error(f"❌ auto-embedding error for document {instance.id}: {e}")
#
#
# @receiver(post_delete, sender=Document)
# def cleanup_document_embeddings(sender, instance, **kwargs):
#     """clean up document embeddings when document is deleted"""
#     try:
#         user_id = str(instance.user.id)
#         document_id = str(instance.id)
#
#         # get user's chunks and remove document-specific ones
#         if user_id in rag_service.chunks:
#             original_count = len(rag_service.chunks[user_id])
#             rag_service.chunks[user_id] = [
#                 chunk for chunk in rag_service.chunks[user_id]
#                 if chunk.metadata.get('document_id') != document_id
#             ]
#             removed_count = original_count - len(rag_service.chunks[user_id])
#
#             if removed_count > 0:
#                 logger.info(f"🗑️ cleaned up {removed_count} chunks for deleted document {document_id}")
#
#     except Exception as e:
#         logger.error(f"❌ error cleaning up embeddings for document {instance.id}: {e}")