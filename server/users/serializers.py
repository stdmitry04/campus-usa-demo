# server/users/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, AcademicInfo, Preferences
from typing import TYPE_CHECKING

# help IDE understand User model attributes
if TYPE_CHECKING:
	from django.contrib.auth.models import AbstractUser


class UserSerializer(serializers.ModelSerializer):
	"""serializer for user registration and profile display"""
	password = serializers.CharField(write_only=True)
	password_confirm = serializers.CharField(write_only=True)

	class Meta:
		model = User
		fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']

	def validate(self, data):
		"""check that passwords match"""
		if data.get('password') != data.get('password_confirm'):
			raise serializers.ValidationError("passwords don't match")
		return data

	def create(self, validated_data):
		"""create user with hashed password"""
		validated_data.pop('password_confirm')
		user = User.objects.create_user(**validated_data)
		return user


class AcademicInfoSerializer(serializers.ModelSerializer):
	"""handles academic information like GPA, test scores"""

	class Meta:
		model = AcademicInfo
		fields = [
			'high_school_name', 'graduation_year', 'gpa', 'gpa_scale',
			'sat_score', 'act_score', 'toefl_score', 'ielts_score',
			'class_rank', 'class_size', 'created_at', 'updated_at'
		]
		read_only_fields = ['created_at', 'updated_at']

	def validate(self, data):
		"""validate academic info fields"""
		# validate gpa range
		gpa = data.get('gpa')
		if gpa and (gpa < 0 or gpa > 4):
			raise serializers.ValidationError({'gpa': 'gpa must be between 0 and 4'})

		# validate test scores
		sat_score = data.get('sat_score')
		if sat_score and (sat_score < 400 or sat_score > 1600):
			raise serializers.ValidationError({'sat_score': 'sat score must be between 400 and 1600'})

		act_score = data.get('act_score')
		if act_score and (act_score < 1 or act_score > 36):
			raise serializers.ValidationError({'act_score': 'act score must be between 1 and 36'})

		# validate class rank vs class size
		class_rank = data.get('class_rank')
		class_size = data.get('class_size')
		if class_rank and class_size and class_rank > class_size:
			raise serializers.ValidationError({'class_rank': 'class rank cannot be greater than class size'})

		return data


class PreferencesSerializer(serializers.ModelSerializer):
	"""handles application preferences"""

	class Meta:
		model = Preferences
		fields = [
			'applying_for', 'fields_of_interest', 'preferred_ranking_min',
			'preferred_ranking_max', 'need_financial_aid', 'created_at', 'updated_at'
		]
		read_only_fields = ['created_at', 'updated_at']

	def validate(self, data):
		"""validate preferences"""
		# validate ranking range
		min_rank = data.get('preferred_ranking_min')
		max_rank = data.get('preferred_ranking_max')
		if min_rank is not None and max_rank is not None and min_rank > max_rank:
			raise serializers.ValidationError({
				'preferred_ranking_min': 'minimum ranking cannot be greater than maximum ranking'
			})

		# validate fields of interest
		fields = data.get('fields_of_interest', [])
		if not fields or len(fields) == 0:
			raise serializers.ValidationError({
				'fields_of_interest': 'at least one field of interest is required'
			})

		return data


class UserProfileSerializer(serializers.ModelSerializer):
	"""main profile serializer with nested user, academic, and preferences"""
	user = UserSerializer(read_only=True)
	academic_info = AcademicInfoSerializer(source='user.academic_info', read_only=True)
	preferences = serializers.SerializerMethodField()
	full_name = serializers.ReadOnlyField()
	initials = serializers.ReadOnlyField()

	class Meta:
		model = UserProfile
		fields = [
			'user', 'avatar', 'phone_number', 'preferences', 'academic_info',
			'full_name', 'initials', 'created_at', 'updated_at'
		]
		read_only_fields = ['created_at', 'updated_at']

	def get_preferences(self, obj):
		"""get user preferences, creating default if none exist"""
		try:
			preferences = obj.user.preferences
			return PreferencesSerializer(preferences).data
		except Preferences.DoesNotExist:
			# create default preferences if they don't exist
			preferences = Preferences.objects.create(
				user=obj.user,
				applying_for='bachelor',
				fields_of_interest=[],
				preferred_ranking_min=0,
				preferred_ranking_max=500,
				need_financial_aid=0,
			)
			return PreferencesSerializer(preferences).data


class UserUpdateSerializer(serializers.ModelSerializer):
	"""serializer for updating user basic info"""

	class Meta:
		model = User
		fields = ['first_name', 'last_name', 'email']

	def validate_email(self, value):
		"""ensure email is unique"""
		if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
			raise serializers.ValidationError("this email is already in use")
		return value


class ProfileUpdateSerializer(serializers.ModelSerializer):
	"""serializer for updating basic profile info"""

	class Meta:
		model = UserProfile
		fields = ['avatar', 'phone_number']


class ProfileStatsSerializer(serializers.Serializer):
	"""serializer for profile statistics"""
	documents_uploaded = serializers.IntegerField()
	essays_written = serializers.IntegerField()
	chat_conversations = serializers.IntegerField()
	profile_completion = serializers.IntegerField()

	class Meta:
		fields = [
			'documents_uploaded', 'essays_written',
			'chat_conversations', 'profile_completion'
		]