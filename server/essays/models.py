# server/essays/models.py
from django.db import models
from django.contrib.auth.models import User
from universities.models import University
from core.models import TimestampedModel, UUIDModel
from typing import TYPE_CHECKING

# helps IDEs understand django model managers
if TYPE_CHECKING:
	from django.db.models.manager import Manager


class Essay(UUIDModel, TimestampedModel):
	"""stores user essays and personal statements"""
	ESSAY_TYPES = [
		('personal_statement', 'personal statement'),
		('supplemental', 'supplemental essay'),
		('scholarship', 'scholarship essay'),
		('other', 'other'),
	]

	user = models.ForeignKey(User, on_delete=models.CASCADE)

	title = models.CharField(max_length=200)
	essay_type = models.CharField(max_length=20, choices=ESSAY_TYPES, default='personal_statement')
	content = models.TextField()
	prompt = models.TextField(blank=True, help_text="the essay prompt or question")

	# essay metadata
	word_count = models.IntegerField(default=0)
	target_universities = models.ManyToManyField(University, blank=True)

	# ai assistance tracking
	ai_generated = models.BooleanField(default=False)
	ai_feedback = models.JSONField(default=dict, blank=True)

	if TYPE_CHECKING:
		objects: Manager['Essay']

	class Meta:
		ordering = ['-updated_at']

	def __str__(self):
		return f"{self.title} - {self.user.username}"

	def save(self, *args, **kwargs):
		"""automatically calculate word count when saving"""
		if self.content:
			self.word_count = len(self.content.split())
		super().save(*args, **kwargs)