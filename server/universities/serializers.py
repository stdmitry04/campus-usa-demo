# server/universities/serializers.py
from rest_framework import serializers
from .models import University, SavedUniversity


class UniversitySerializer(serializers.ModelSerializer):
	"""university information with calculated fields"""
	acceptance_rate_display = serializers.ReadOnlyField()
	admission_chance_display = serializers.ReadOnlyField()
	tuition_display = serializers.ReadOnlyField()
	is_saved = serializers.SerializerMethodField()

	class Meta:
		model = University
		fields = [
			'id', 'name', 'location', 'city', 'state',
			'rank',
			'admission_chance', 'admission_chance_display',
			'acceptance_rate', 'acceptance_rate_display',
			'avg_sat_score', 'avg_gpa', 'annual_tuition', 'tuition_display',
			'has_financial_aid', 'website_url', 'logo',
			'is_saved', 'created_at', 'updated_at'
		]

	def get_is_saved(self, obj):
		"""check if university is saved by current user"""
		request = self.context.get('request')
		if request and request.user.is_authenticated:
			return SavedUniversity.objects.filter(user=request.user, university=obj).exists()
		return False


class SavedUniversitySerializer(serializers.ModelSerializer):
	"""saved university with university details"""
	university = UniversitySerializer(read_only=True)

	class Meta:
		model = SavedUniversity
		fields = ['id', 'university', 'created_at']