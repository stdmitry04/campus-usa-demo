# server/core/storage_service.py
# s3 storage configuration moved here for reuse across apps
import boto3
import os
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from storages.backends.s3boto3 import S3Boto3Storage
import uuid
from datetime import datetime


@deconstructible
class SecureS3Storage(S3Boto3Storage):
	"""custom s3 storage with enhanced security validation"""

	def __init__(self, *args, **kwargs):
		kwargs.setdefault('bucket_name', settings.AWS_STORAGE_BUCKET_NAME)
		kwargs.setdefault('region_name', settings.AWS_S3_REGION_NAME)
		kwargs.setdefault('file_overwrite', False)
		kwargs.setdefault('default_acl', 'private')  # important: keep files private
		super().__init__(*args, **kwargs)

	def _save(self, name, content):
		"""override save to add security validation"""
		# validate file before uploading to s3
		self._validate_file_security(content)

		# generate secure filename
		secure_name = self._generate_secure_filename(name)

		return super()._save(secure_name, content)

	def _validate_file_security(self, content):
		"""comprehensive file security validation"""
		from core.validators.document_validators import validate_file_size, validate_file_extension, validate_file_mimetype

		validate_file_size(content)
		if hasattr(content, 'name'):
			validate_file_extension(content)
		validate_file_mimetype(content)

	def _generate_secure_filename(self, original_name):
		"""generate secure filename with timestamp"""
		clean_name = self._sanitize_filename(original_name)
		name, ext = os.path.splitext(clean_name)

		# generate secure path: documents/year/month/uuid_filename.ext
		timestamp = datetime.now()
		secure_path = f"documents/{timestamp.year}/{timestamp.month:02d}/{uuid.uuid4().hex[:8]}_{name[:50]}{ext}"

		return secure_path

	def _sanitize_filename(self, filename):
		"""sanitize filename to prevent path traversal"""
		if not filename:
			return 'untitled'

		filename = os.path.basename(filename)
		dangerous_chars = ['..', '\\', '<', '>', ':', '"', '|', '?', '*', '/', '\x00']
		for char in dangerous_chars:
			filename = filename.replace(char, '_')

		if len(filename) > 255:
			name, ext = os.path.splitext(filename)
			filename = name[:255 - len(ext)] + ext

		return filename or 'untitled'


class S3PreSignedURLManager:
	"""manages pre-signed urls for s3 uploads and downloads"""

	def __init__(self):
		self.s3_client = boto3.client(
			's3',
			aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
			aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
			region_name=settings.AWS_S3_REGION_NAME
		)
		self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

	def generate_upload_url(self, file_key, content_type, file_size=None):
		"""generate pre-signed url for file upload"""
		try:
			# validate content type
			self._validate_content_type(content_type)

			# prepare conditions for upload
			conditions = [
				["content-length-range", 1, settings.MAX_UPLOAD_SIZE],
				{"Content-Type": content_type}
			]

			# generate pre-signed post
			response = self.s3_client.generate_presigned_post(
				Bucket=self.bucket_name,
				Key=file_key,
				Fields={"Content-Type": content_type},
				Conditions=conditions,
				ExpiresIn=3600  # 1 hour expiration
			)

			return response
		except ClientError as e:
			raise ValidationError(f'failed to generate upload url: {str(e)}')

	def generate_download_url(self, file_key, filename=None):
		"""generate pre-signed url for file download"""
		try:
			# check if file exists
			if not self._file_exists(file_key):
				raise ValidationError('file not found')

			# prepare response headers
			response_headers = {}
			if filename:
				safe_filename = self._sanitize_filename(filename)
				response_headers['ResponseContentDisposition'] = f'attachment; filename="{safe_filename}"'

			# generate pre-signed url
			url = self.s3_client.generate_presigned_url(
				'get_object',
				Params={
					'Bucket': self.bucket_name,
					'Key': file_key,
					**response_headers
				},
				ExpiresIn=3600  # 1 hour expiration
			)

			return url
		except ClientError as e:
			raise ValidationError(f'failed to generate download url: {str(e)}')

	def _validate_content_type(self, content_type):
		"""validate content type against allowed mimetypes"""
		allowed_mimetypes = getattr(settings, 'ALLOWED_DOCUMENT_MIMETYPES', ['application/pdf'])

		if content_type not in allowed_mimetypes:
			raise ValidationError(
				f'content type "{content_type}" is not allowed for security reasons'
			)

	def _file_exists(self, file_key):
		"""check if file exists in s3"""
		try:
			self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
			return True
		except ClientError:
			return False

	def _sanitize_filename(self, filename):
		"""sanitize filename for download headers"""
		if not filename:
			return 'download'

		dangerous_chars = ['"', "'", '\\', '\n', '\r', '\t']
		for char in dangerous_chars:
			filename = filename.replace(char, '_')

		return filename[:100]  # limit length for headers

	def delete_file(self, file_key):
		"""delete file from s3"""
		try:
			self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
			return True
		except ClientError as e:
			print(f"failed to delete file {file_key}: {str(e)}")
			return False

	def get_file_metadata(self, file_key):
		"""get file metadata from s3"""
		try:
			response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
			return {
				'size': response.get('ContentLength', 0),
				'last_modified': response.get('LastModified'),
				'content_type': response.get('ContentType'),
				'etag': response.get('ETag', '').strip('"')
			}
		except ClientError:
			return None