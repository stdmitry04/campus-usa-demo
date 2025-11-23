# server/messaging/models.py
import json

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.contrib.auth.models import User
from core.models import TimestampedModel, UUIDModel
from django.utils.timezone import now
from typing import TYPE_CHECKING

from pydantic import ValidationError

# helps IDEs understand django model managers
if TYPE_CHECKING:
	from django.db.models.manager import Manager


class Conversation(UUIDModel, TimestampedModel):
	"""stores AI assistant conversation sessions"""
	user = models.ForeignKey(User, on_delete=models.CASCADE)

	title = models.CharField(max_length=200, blank=True)  # auto-generated from first message

	if TYPE_CHECKING:
		objects: Manager['Conversation']
		DoesNotExist: type[Exception]

	class Meta:
		ordering = ['-updated_at']

	def __str__(self):
		return f"conversation {self.title or str(self.id)[:8]} - {self.user.username}"


class Message(UUIDModel):
	"""individual messages within a conversation"""
	SENDER_CHOICES = [
		('user', 'user'),
		('assistant', 'ai assistant'),
	]

	conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')

	sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
	content = models.TextField(null=True)

	# metadata for AI responses
	response_time = models.FloatField(null=True, blank=True)  # time taken to generate response
	model_used = models.CharField(max_length=50, blank=True)  # which AI model was used
	created_at = models.DateTimeField(default=now, editable=False)
	metadata = models.JSONField(default=dict, blank=True)

	if TYPE_CHECKING:
		objects: Manager['Message']

	class Meta:
		ordering = ['created_at']

	def __str__(self):
		return f"{self.sender}: {self.content[:50]}..."


# class RAGChunk(models.Model):
# 	"""persistent storage for rag memory chunks"""
#
# 	CHUNK_TYPES = [
# 		('profile', 'Profile'),
# 		('document', 'Document'),
# 	]
#
# 	id = models.CharField(max_length=255, primary_key=True)
# 	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rag_chunks')
# 	content = models.TextField()
# 	chunk_type = models.CharField(max_length=20, choices=CHUNK_TYPES)
# 	source = models.CharField(max_length=100)
#
# 	# using JSONField directly - no property methods needed since django handles json conversion
# 	embedding = models.JSONField(default=list, blank=True, help_text='embedding vector as json array')
#
# 	metadata = models.JSONField(default=dict)
#
# 	created_at = models.DateTimeField(auto_now_add=True)
# 	updated_at = models.DateTimeField(auto_now=True)
#
# 	class Meta:
# 		db_table = 'rag_chunks'
# 		indexes = [
# 			models.Index(fields=['user', 'chunk_type']),
# 			models.Index(fields=['user', 'source']),
# 			models.Index(fields=['updated_at']),
# 		]
#
# 	def clean(self):
# 		"""validate that embedding is a list of numbers"""
# 		if self.embedding and not isinstance(self.embedding, list):
# 			raise ValidationError("embedding must be a list of numbers")
#
# 		if self.embedding and not all(isinstance(x, (int, float)) for x in self.embedding):
# 			raise ValidationError("all embedding values must be numbers")
#
# 	def __str__(self):
# 		return f"{self.chunk_type} chunk for {self.user.username}"