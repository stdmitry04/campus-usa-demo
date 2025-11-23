# server/documents/serializers.py
from rest_framework import serializers
from .models import Document
from .validators import validate_document_file, validate_document_title


class DocumentSerializer(serializers.ModelSerializer):
	"""document upload and management"""
	# uploaded_at = serializers.DateTimeField(source='created_at', read_only=True)
	file_size_display = serializers.ReadOnlyField()

	class Meta:
		model = Document
		fields = [
			'id',
			'title',
			'document_type',
			'uploaded_at',
			'processed_at',
			'validation_passed',
			'validation_confidence',
			'validation_notes',
			'validation_completed_at',
			'ocr_status',
			'ocr_metadata',
			'ocr_error',
			'extracted_text',
			'file',
			'file_size',
			'content_type',
			's3_key',
			'original_filename',
			'status',
			'file_size_display'
		]
		read_only_fields = [
			'id',
			'uploaded_at',
			'uploaded_at',
			'processed_at',
			'validation_passed',
			'validation_confidence',
			'validation_notes',
			'validation_completed_at',
			'ocr_status',
			'ocr_metadata',
			'ocr_error',
			'extracted_text',
			'file_size',
			'content_type',
			's3_key',
			'original_filename',
			'status',
			'file_size_display'
		]

	def validate_file(self, value):
		"""validate uploaded file before saving"""
		if not value:
			raise serializers.ValidationError("file is required")

		# run the file validators
		try:
			validate_document_file(value)
		except Exception as e:
			raise serializers.ValidationError(str(e))

		return value

	def validate_title(self, value):
		"""validate and sanitize document title for security"""
		try:
			sanitized_title = validate_document_title(value)
			return sanitized_title
		except Exception as e:
			raise serializers.ValidationError(str(e))