# server/documents/models.py
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import TimestampedModel, UUIDModel
from core.services.storage_service import S3PreSignedURLManager
from core.validators.document_validators import validate_document_file, sanitize_title
from core.utils.document_utils import get_content_type_from_extension
from typing import TYPE_CHECKING

from s3transfer import logger

# helps IDEs understand django model managers
if TYPE_CHECKING:
	from django.db.models.manager import Manager


class Document(UUIDModel, TimestampedModel):
	"""handles document uploads with s3 storage"""
	DOCUMENT_TYPES = [
		('transcript', 'high school transcript'),
		('sat_score', 'sat score report'),
		('act_score', 'act score report'),
		('toefl_score', 'toefl score report'),
		('ielts_score', 'ielts score report'),
		('recommendation', 'letter of recommendation'),
		('personal_statement', 'personal statement'),
		('bank_statement', 'bank statement'),
		('i20', 'i-20 form'),
		('passport', 'passport copy'),
		('visa', 'visa document'),
		('other', 'other'),
	]

	STATUS_CHOICES = [
		('pending', 'Pending'),
		('processing', 'Processing'),
		('successful', 'Successful'),
		('validation_failed', 'Validation Failed'),  # Add this
		('error', 'Error'),
	]

	# ocr status choices
	OCR_STATUS_CHOICES = [
		('pending', 'pending'),
		('processing', 'processing'),
		('completed', 'completed'),
		('failed', 'failed'),
	]


	uploaded_at = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	title = models.CharField(max_length=200)
	document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)

	# s3 storage fields
	s3_key = models.CharField(max_length=500, blank=True, null=True)
	original_filename = models.CharField(max_length=255, default="unknown_file.pdf")
	content_type = models.CharField(max_length=100, blank=True)
	file_size = models.PositiveIntegerField(default=0)

	# keep legacy file field for backward compatibility
	file = models.FileField(
		upload_to='documents/',
		validators=[validate_document_file],
		blank=True,
		null=True
	)

	# existing processing status and extracted data
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	extracted_data = models.JSONField(default=dict, blank=True)
	processed_at = models.DateTimeField(null=True, blank=True)

	# ocr fields
	ocr_status = models.CharField(
		max_length=20,
		choices=OCR_STATUS_CHOICES,
		default='pending',
		null=True,
		blank=True,
		help_text='Status of OCR text extraction'
	)

	extracted_text = models.TextField(
		null=True,
		blank=True,
		help_text='Text extracted from document via OCR'
	)

	ocr_metadata = models.JSONField(
		default=dict,
		blank=True,
		help_text='Metadata from OCR processing (page count, method, etc.)'
	)

	ocr_error = models.TextField(
		null=True,
		blank=True,
		help_text='Error message if OCR processing failed'
	)

	# validation fields
	validation_passed = models.BooleanField(null=True, blank=True)
	validation_confidence = models.FloatField(null=True, blank=True)
	validation_notes = models.TextField(blank=True)
	validation_completed_at = models.DateTimeField(null=True, blank=True)

	if TYPE_CHECKING:
		objects: Manager['Document']

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.title} - {self.user.username}"

	@property
	def file_size_display(self):
		"""returns file size in human-readable format"""
		if not self.file_size:
			return "unknown size"

		size = self.file_size
		for unit in ['B', 'KB', 'MB', 'GB']:
			if size < 1024.0:
				return f"{size:.1f} {unit}"
			size /= 1024.0
		return f"{size:.1f} TB"

	@property
	def is_stored_in_s3(self):
		"""check if document is stored in s3"""
		return bool(self.s3_key)

	@property
	def storage_location(self):
		"""get storage location description"""
		if self.is_stored_in_s3:
			return f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/{self.s3_key}"
		elif self.file:
			return f"local: {self.file.name}"
		else:
			return "no file attached"

	def get_download_url(self, expire_time=None):
		"""get download url (s3 pre-signed or local)"""
		if self.is_stored_in_s3:
			s3_manager = S3PreSignedURLManager()
			return s3_manager.generate_download_url(self.s3_key, self.original_filename)
		elif self.file:
			return self.file.url
		else:
			return None

	def delete_from_storage(self):
		"""delete file from storage (s3 or local)"""
		if self.is_stored_in_s3:
			s3_manager = S3PreSignedURLManager()
			return s3_manager.delete_file(self.s3_key)
		elif self.file:
			try:
				self.file.delete(save=False)
				return True
			except Exception as e:
				print(f"failed to delete local file: {e}")
				return False
		return True

	def get_file_metadata(self):
		"""get file metadata from storage"""
		if self.is_stored_in_s3:
			s3_manager = S3PreSignedURLManager()
			return s3_manager.get_file_metadata(self.s3_key)
		elif self.file:
			try:
				return {
					'size': self.file.size,
					'content_type': getattr(self.file, 'content_type', None),
					'url': self.file.url
				}
			except Exception:
				return None
		return None

	def clean(self):
		"""validate document fields"""
		super().clean()

		# ensure we have either s3_key or file
		if not self.s3_key and not self.file:
			raise ValidationError('document must have either s3_key or file')

		# validate title
		if self.title:
			self.title = sanitize_title(self.title)

	def save(self, *args, **kwargs):
		"""override save to run validation and set metadata"""
		self.full_clean()

		# set file size if not already set
		if not self.file_size:
			if self.file and hasattr(self.file, 'size'):
				self.file_size = self.file.size

		# set content type if not already set
		if not self.content_type and self.original_filename:
			self.content_type = get_content_type_from_extension(self.original_filename)

		super().save(*args, **kwargs)

	def delete(self, *args, **kwargs):
		"""override delete to clean up storage"""
		from core.services.embedding_service import get_embedding_service

		# delete embeddings
		embedding_service = get_embedding_service()
		if embedding_service:
			try:
				success = embedding_service.delete_document_embeddings(
					user_id=self.user_id,
					document_id=str(self.id)
				)
				if success:
					logger.info(f"cleaned up embeddings for document {self.id}")
				else:
					logger.warning(f"failed to clean up embeddings for document {self.id}")
			except Exception as e:
				logger.error(f"error cleaning up embeddings for document {self.id}: {e}")

		# delete file from storage first
		self.delete_from_storage()
		super().delete(*args, **kwargs)