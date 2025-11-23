# server/documents/base_views.py
from celery import chain
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from .models import Document
from .serializers import DocumentSerializer
from .validators import (
	validate_document_title,
	generate_secure_s3_key,
	validate_content_type_for_s3
)
from core.services import rag_service
from core.services.storage_service import S3PreSignedURLManager
from core.utils.document_utils import get_content_type_from_extension
import logging

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
	"""document upload and management with s3 support"""
	queryset = Document.objects.none()
	serializer_class = DocumentSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return Document.objects.filter(user=self.request.user)

	@action(detail=False, methods=['post'])
	def request_upload_url(self, request):
		"""get pre-signed url for file upload"""
		try:
			# get request data
			title = request.data.get('title', '').strip()
			document_type = request.data.get('document_type', '')
			original_filename = request.data.get('filename', '')
			file_size = request.data.get('file_size', 0)

			# validate required fields
			if not title:
				return Response({
					'error': 'validation failed',
					'details': {'title': ['title is required']}
				}, status=status.HTTP_400_BAD_REQUEST)

			if not document_type:
				return Response({
					'error': 'validation failed',
					'details': {'document_type': ['document type is required']}
				}, status=status.HTTP_400_BAD_REQUEST)

			if not original_filename:
				return Response({
					'error': 'validation failed',
					'details': {'filename': ['filename is required']}
				}, status=status.HTTP_400_BAD_REQUEST)

			# validate file size
			max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 25 * 1024 * 1024)
			if file_size > max_size:
				return Response({
					'error': 'validation failed',
					'details': {
						'file_size': [f'file size exceeds maximum allowed size ({max_size / 1024 / 1024:.1f}MB)']}
				}, status=status.HTTP_400_BAD_REQUEST)

			# validate and sanitize title
			try:
				clean_title = validate_document_title(title)
			except ValidationError as e:
				return Response({
					'error': 'validation failed',
					'details': {'title': [str(e)]}
				}, status=status.HTTP_400_BAD_REQUEST)

			# validate file extension
			try:
				from core.validators.document_validators import validate_file_extension
				# create a mock file object for validation
				class MockFile:
					def __init__(self, name):
						self.name = name

				validate_file_extension(MockFile(original_filename))
			except ValidationError as e:
				return Response({
					'error': 'validation failed',
					'details': {'filename': [str(e)]}
				}, status=status.HTTP_400_BAD_REQUEST)

			# determine content type
			content_type = get_content_type_from_extension(original_filename)

			# validate content type
			try:
				validate_content_type_for_s3(content_type)
			except ValidationError as e:
				return Response({
					'error': 'validation failed',
					'details': {'content_type': [str(e)]}
				}, status=status.HTTP_400_BAD_REQUEST)

			# generate secure s3 key
			s3_key = generate_secure_s3_key(original_filename, request.user.id)

			# create document record (pending status)
			document = Document.objects.create(
				user=request.user,
				title=clean_title,
				document_type=document_type,
				s3_key=s3_key,
				original_filename=original_filename,
				content_type=content_type,
				file_size=file_size,
				status='pending'
			)

			# generate pre-signed upload url
			s3_manager = S3PreSignedURLManager()
			upload_data = s3_manager.generate_upload_url(s3_key, content_type, file_size)

			logger.info(f"generated upload url for user {request.user.id}, document {document.id}")

			return Response({
				'document_id': str(document.id),
				'upload_url': upload_data['url'],
				'upload_fields': upload_data['fields'],
				's3_key': s3_key,
				'expires_in': 3600  # 1 hour
			}, status=status.HTTP_201_CREATED)

		except ValidationError as e:
			logger.error(f"validation error in upload url request: {e}")
			return Response({
				'error': 'validation failed',
				'details': {'general': [str(e)]}
			}, status=status.HTTP_400_BAD_REQUEST)

		except Exception as e:
			logger.error(f"unexpected error in upload url request: {e}")
			return Response({
				'error': 'failed to generate upload url',
				'details': 'an unexpected error occurred'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=True, methods=['post'])
	def confirm_upload(self, request, pk=None):
		"""confirm that file was uploaded to s3"""
		try:
			document = self.get_object()

			if document.status != 'pending':
				return Response({
					'error': 'document is not in pending status'
				}, status=status.HTTP_400_BAD_REQUEST)

			# verify file exists in s3
			s3_manager = S3PreSignedURLManager()
			metadata = s3_manager.get_file_metadata(document.s3_key)

			if not metadata:
				return Response({
					'error': 'file not found in storage'
				}, status=status.HTTP_404_NOT_FOUND)

			# update document with actual file size and status
			document.file_size = metadata.get('size', document.file_size)
			document.status = 'processing'
			document.processed_at = timezone.now()
			document.save()

			logger.info(f"confirmed upload for document {document.id}")

			# In DocumentViewSet.confirm_upload()
			try:
				from core.tasks.ocr_tasks import process_document_ocr_task
				from core.tasks.validation_tasks import validate_document_task
				from core.tasks.embedding_tasks import embed_document_task

				# Schedule OCR first, then embedding
				# ocr_result = process_document_ocr_task.delay(request.user.id, document.id)
				# logger.info(f"🔄 scheduled OCR task: task_id={ocr_result.id}")

				# validation_result = validate_document_task.apply_async(
				# 	args=[request.user.id, document.id],
				# 	countdown=60
				# )
				#
				# # Schedule embedding after OCR (with delay)
				# embed_result = embed_document_task.apply_async(
				# 	args=[request.user.id, document.id],
				# 	countdown=120  # wait 30 seconds for OCR to complete
				# )
				# logger.info(f"🔄 scheduled embedding task: task_id={embed_result.id}")

				chain(
					process_document_ocr_task.si(request.user.id, document.id),
					validate_document_task.si(request.user.id, document.id),
					embed_document_task.si(request.user.id, document.id)
				).delay()

			except Exception as e:
				logger.error(f"⚠️ failed to schedule document processing pipeline: {e}")
				# still return success since the upload itself worked
				document.status = 'error'
				document.save()

			serializer = self.get_serializer(document)
			return Response(serializer.data, status=status.HTTP_200_OK)

			# try:
			# 	from core.tasks import ocr_tasks    # <- only import what you need for now
			# 	print("📣 OCR task is about to be triggered!")
			#
			# 	# schedule just the OCR task
			# 	ocr_tasks.process_document_ocr_task.apply_async(
			# 		kwargs={
			# 			"user_id": self.request.user.id,
			# 			"document_id": document.id,
			# 		}
			# 	)
			#
			# except Exception as e:
			# 	logger.error(f"Failed to import or schedule OCR task: {e}")
			#
			# 	# return updated document data
			# 	serializer = self.get_serializer(document)
			# 	return Response(serializer.data)

		except Exception as e:
			logger.error(f"error confirming upload: {e}")
			return Response({
				'error': 'failed to confirm upload',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	def create(self, request, *args, **kwargs):
		"""legacy direct upload support (fallback)"""
		try:
			print('DOCKERDOCKERDOCKERDOCKERDOCKER USING LEGACY🏗🏗🏗🏗🏗🏗🏗🏗')
			logger.info(f"direct upload attempt for user: {request.user.username}")

			# validate data completely before creating anything
			serializer = self.get_serializer(data=request.data)
			serializer.is_valid(raise_exception=True)

			# save with completed status for direct uploads
			document = serializer.save(
				user=request.user,
				status='completed',
				processed_at=timezone.now()
			)

			# if file was uploaded directly, set metadata
			if document.file:
				document.original_filename = document.file.name
				document.file_size = document.file.size
				document.content_type = getattr(document.file, 'content_type',
				                                get_content_type_from_extension(document.file.name))
				document.save()

			logger.info(f"direct upload completed: {document.title}")

			response_data = DocumentSerializer(document).data
			return Response(response_data, status=status.HTTP_201_CREATED)

		except ValidationError as e:
			logger.error(f"django validation error: {e}")
			return Response({
				'error': 'file validation failed',
				'details': {'file': [str(e)]}
			}, status=status.HTTP_400_BAD_REQUEST)

		except serializers.ValidationError as e:
			logger.error(f"serializer validation error: {e.detail}")
			return Response({
				'error': 'validation failed',
				'details': e.detail
			}, status=status.HTTP_400_BAD_REQUEST)

		except Exception as e:
			logger.error(f"unexpected error during direct upload: {e}")
			return Response({
				'error': 'upload failed',
				'details': 'an unexpected error occurred'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=True, methods=['get'])
	def download(self, request, pk=None):
		"""download document with s3 pre-signed url"""
		try:
			document = self.get_object()

			if document.user != request.user:
				return Response(
					{'error': 'access denied'},
					status=status.HTTP_403_FORBIDDEN
				)

			# get download url
			download_url = document.get_download_url()

			if not download_url:
				return Response({
					'error': 'no file attached'
				}, status=status.HTTP_404_NOT_FOUND)

			logger.info(f"generated download url for document {document.id}")

			return Response({
				'download_url': download_url,
				'filename': document.original_filename or document.title,
				'file_size': document.file_size_display,
				'content_type': document.content_type,
				'storage_location': 's3' if document.is_stored_in_s3 else 'local',
				'expires_in': 3600  # 1 hour for s3 urls
			})

		except ValidationError as e:
			logger.error(f"validation error in download: {e}")
			return Response({
				'error': 'failed to generate download url',
				'details': str(e)
			}, status=status.HTTP_400_BAD_REQUEST)

		except Exception as e:
			logger.error(f"error generating download url: {e}")
			return Response({
				'error': 'failed to generate download url'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	def destroy(self, request, *args, **kwargs):
		"""delete document and cleanup storage"""
		try:
			document = self.get_object()
			document_id = document.id

			# delete from storage first
			storage_deleted = document.delete_from_storage()

			if not storage_deleted:
				logger.warning(f"failed to delete file from storage for document {document_id}")

			# delete database record
			document.delete()

			logger.info(f"deleted document {document_id}")

			return Response(status=status.HTTP_204_NO_CONTENT)

		except Exception as e:
			logger.error(f"error deleting document: {e}")
			return Response({
				'error': 'failed to delete document',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=False, methods=['get'])
	def storage_stats(self, request):
		"""get user's storage statistics"""
		try:
			user_documents = self.get_queryset()

			total_documents = user_documents.count()
			total_size = sum(doc.file_size for doc in user_documents if doc.file_size)
			s3_documents = user_documents.filter(s3_key__isnull=False).count()
			local_documents = user_documents.filter(file__isnull=False, s3_key__isnull=True).count()

			return Response({
				'total_documents': total_documents,
				'total_size_bytes': total_size,
				'total_size_display': self._format_file_size(total_size),
				's3_documents': s3_documents,
				'local_documents': local_documents,
				'storage_breakdown': {
					's3_percentage': round((s3_documents / total_documents * 100) if total_documents > 0 else 0, 1),
					'local_percentage': round((local_documents / total_documents * 100) if total_documents > 0 else 0,
					                          1)
				}
			})

		except Exception as e:
			logger.error(f"error getting storage stats: {e}")
			return Response({
				'error': 'failed to get storage statistics'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	def _format_file_size(self, size_bytes):
		"""format file size in human readable format"""
		if not size_bytes:
			return "0 B"

		for unit in ['B', 'KB', 'MB', 'GB']:
			if size_bytes < 1024.0:
				return f"{size_bytes:.1f} {unit}"
			size_bytes /= 1024.0
		return f"{size_bytes:.1f} TB"


	@action(detail=False, methods=['get'])
	def embedding_stats(self, request):
		"""get embedding stats for current user"""
		try:
			stats = rag_service.get_user_stats(request.user)

			# get recent chunks
			from messaging.models import RAGChunk
			recent_chunks = RAGChunk.objects.filter(
				user=request.user
			).order_by('-created_at')[:5]

			chunk_details = []
			for chunk in recent_chunks:
				chunk_details.append({
					'id': chunk.id,
					'type': chunk.chunk_type,
					'source': chunk.source,
					'content_preview': chunk.content[:100] + '...' if len(chunk.content) > 100 else chunk.content,
					'metadata': chunk.metadata,
					'created_at': chunk.created_at
				})

			return Response({
				'stats': stats,
				'recent_chunks': chunk_details,
				'has_embeddings': stats['total_chunks'] > 0
			})

		except Exception as e:
			return Response({
				'error': str(e)
			}, status=500)

	@action(detail=False, methods=['get'])
	def embedding_status(self, request):
		"""get embedding status for all user documents"""
		from core.models import RAGChunk

		user_chunks = RAGChunk.objects.filter(user=request.user)
		statuses = {}

		for chunk in user_chunks:
			doc_id = chunk.metadata.get('document_id')
			if doc_id:
				if doc_id not in statuses:
					statuses[doc_id] = {
						'status': 'success',
						'chunks': 0,
						'embeddedAt': chunk.updated_at
					}
				statuses[doc_id]['chunks'] += 1

		return Response(statuses)

















