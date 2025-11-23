# server/universities/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import TimestampedModel
from typing import TYPE_CHECKING

# helps IDEs understand django model managers
if TYPE_CHECKING:
	from django.db.models.manager import Manager


class University(TimestampedModel):
	"""stores university information for the college search feature"""
	name = models.CharField(max_length=200)
	location = models.CharField(max_length=100)  # could be "US", "Canada", etc.
	rank = models.IntegerField()
	city = models.CharField(max_length=100, blank=True)
	state = models.CharField(max_length=50, blank=True)

	admission_chance = models.FloatField(
		validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
		help_text="admission chance as percentage"
	)

	# admission statistics
	acceptance_rate = models.FloatField(
		validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
		help_text="acceptance rate as percentage"
	)
	avg_sat_score = models.IntegerField(
		validators=[MinValueValidator(400), MaxValueValidator(1600)],
		null=True, blank=True
	)
	avg_gpa = models.FloatField(
		validators=[MinValueValidator(0.0), MaxValueValidator(4.0)],
		null=True, blank=True
	)

	# financial info
	annual_tuition = models.IntegerField(help_text="annual tuition in USD")
	has_financial_aid = models.BooleanField(default=True)

	# additional info
	website_url = models.URLField(blank=True)
	logo = models.ImageField(upload_to='university_logos/', blank=True, null=True)
	ranking = models.IntegerField(null=True, blank=True)

	if TYPE_CHECKING:
		objects: Manager['University']

	class Meta:
		verbose_name_plural = "universities"
		ordering = ['ranking', 'name']

	def __str__(self):
		return self.name

	@property
	def acceptance_rate_display(self):
		"""returns acceptance rate as a formatted string like '4%'"""
		return f"{int(self.acceptance_rate)}%"

	@property
	def admission_chance_display(self):
		"""returns admission chance as a formatted string like '4%'"""
		return f"{int(self.admission_chance)}%"

	@property
	def tuition_display(self):
		"""formats tuition as currency"""
		return f"${self.annual_tuition:,}/yr"


class SavedUniversity(TimestampedModel):
	"""tracks which universities users have saved"""
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_universities')
	university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='saved_by_users')

	class Meta:
		unique_together = ['user', 'university']
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.user.username} saved {self.university.name}"