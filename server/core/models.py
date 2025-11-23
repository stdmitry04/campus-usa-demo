# server/core/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

from pydantic import ValidationError


class TimestampedModel(models.Model):
	"""base model with timestamps for common functionality"""
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class UUIDModel(models.Model):
	"""base model with uuid primary key"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	class Meta:
		abstract = True



class RAGChunk(models.Model):
	"""persistent storage for rag memory chunks"""

	CHUNK_TYPES = [
		('profile', 'Profile'),
		('document', 'Document'),
	]

	id = models.CharField(max_length=255, primary_key=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rag_chunks')
	content = models.TextField()
	chunk_type = models.CharField(max_length=20, choices=CHUNK_TYPES)
	source = models.CharField(max_length=100)

	# using JSONField directly - no property methods needed since django handles json conversion
	embedding = models.JSONField(default=list, blank=True, help_text='embedding vector as json array')

	metadata = models.JSONField(default=dict)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		managed = True
		db_table = 'rag_chunks'
		indexes = [
			models.Index(fields=['user', 'chunk_type']),
			models.Index(fields=['user', 'source']),
			models.Index(fields=['updated_at']),
		]

	def clean(self):
		"""validate that embedding is a list of numbers"""
		if self.embedding and not isinstance(self.embedding, list):
			raise ValidationError("embedding must be a list of numbers")

		if self.embedding and not all(isinstance(x, (int, float)) for x in self.embedding):
			raise ValidationError("all embedding values must be numbers")

	def __str__(self):
		return f"{self.chunk_type} chunk for {self.user.username}"