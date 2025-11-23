# server/users/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework.exceptions import ValidationError
from core.models import TimestampedModel
from typing import TYPE_CHECKING

# helps IDEs understand django model managers and user model
if TYPE_CHECKING:
	from django.db.models.manager import Manager
	from django.contrib.auth.models import AbstractUser


class UserProfile(TimestampedModel):
	"""main user profile with basic info and relationships"""
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

	# basic profile info
	avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
	phone_number = models.CharField(max_length=20, blank=True)

	if TYPE_CHECKING:
		objects: Manager['UserProfile']

	def __str__(self):
		return f"{self.user.username}'s profile"

	@property
	def full_name(self):
		"""returns user's full name or username if names not set"""
		if self.user.first_name or self.user.last_name:
			return f"{self.user.first_name} {self.user.last_name}".strip()
		return self.user.username

	@property
	def initials(self):
		"""returns user initials for avatar display"""
		if self.user.first_name and self.user.last_name:
			return f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
		return self.user.username[:2].upper()

	def get_completion_percentage(self):
		"""calculate profile completion percentage"""
		completion_score = 0
		total_fields = 10

		# basic user info (3 points)
		if self.user.first_name: completion_score += 1
		if self.user.last_name: completion_score += 1
		if self.user.email: completion_score += 1

		# basic profile info (1 point)
		if self.phone_number: completion_score += 1

		# preferences (2 points)
		try:
			prefs = self.user.preferences
			if prefs.applying_for: completion_score += 1
			if prefs.fields_of_interest: completion_score += 1
		except:
			pass

		# academic info (4 points)
		try:
			academic = self.user.academic_info
			if academic.high_school_name: completion_score += 1
			if academic.gpa: completion_score += 1
			if academic.sat_score or academic.act_score: completion_score += 1
			if academic.graduation_year: completion_score += 1
		except:
			pass

		return round((completion_score / total_fields) * 100)


class AcademicInfo(TimestampedModel):
	"""stores user's academic information"""
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='academic_info', null=True, blank=True)

	# required fields
	high_school_name = models.CharField(max_length=200, null=True, blank=True)
	graduation_year = models.IntegerField(null=True, blank=True)
	gpa = models.FloatField(
		validators=[MinValueValidator(0.0), MaxValueValidator(4.0)],
		null=True,
		blank=True
	)
	gpa_scale = models.CharField(max_length=10, default='4.0')

	# optional standardized test scores
	sat_score = models.IntegerField(
		validators=[MinValueValidator(400), MaxValueValidator(1600)],
		null=True, blank=True
	)
	act_score = models.IntegerField(
		validators=[MinValueValidator(1), MaxValueValidator(36)],
		null=True, blank=True
	)
	toefl_score = models.IntegerField(
		validators=[MinValueValidator(0), MaxValueValidator(120)],
		null=True, blank=True
	)
	ielts_score = models.FloatField(
		validators=[MinValueValidator(0.0), MaxValueValidator(9.0)],
		null=True, blank=True
	)

	# optional class info
	class_rank = models.IntegerField(null=True, blank=True)
	class_size = models.IntegerField(null=True, blank=True)

	if TYPE_CHECKING:
		objects: Manager['AcademicInfo']

	def __str__(self):
		return f"{self.user.username}'s academic info"

	def clean(self):
		"""validate academic info fields"""
		if self.class_rank and self.class_size and self.class_rank > self.class_size:
			raise ValidationError('class rank cannot be greater than class size')


class Preferences(TimestampedModel):
	"""stores user's application preferences"""
	DEGREE_CHOICES = [
		('bachelor', "bachelor's degree"),
		('master', "master's degree"),
		('phd', 'phd'),
	]

	AID_CHOICES = [
		(0, 'none'),
		(1, 'partial'),
		(2, 'full'),
	]

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')

	# application preferences
	applying_for = models.CharField(max_length=20, choices=DEGREE_CHOICES, default='bachelor')
	fields_of_interest = models.JSONField(default=list, blank=True)  # stores list of interests
	preferred_ranking_min = models.IntegerField(default=0)
	preferred_ranking_max = models.IntegerField(default=500)
	need_financial_aid = models.IntegerField(choices=AID_CHOICES, default=0)

	if TYPE_CHECKING:
		objects: Manager['Preferences']

	def __str__(self):
		return f"{self.user.username}'s preferences"

	def clean(self):
		"""validate preferences"""
		if self.preferred_ranking_min > self.preferred_ranking_max:
			raise ValidationError('minimum ranking cannot be greater than maximum ranking')