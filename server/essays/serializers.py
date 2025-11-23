# server/essays/serializers.py
from rest_framework import serializers
from .models import Essay


class EssaySerializer(serializers.ModelSerializer):
	"""essay creation and editing"""

	class Meta:
		model = Essay
		fields = [
			'id', 'title', 'essay_type', 'content', 'prompt',
			'word_count', 'target_universities', 'ai_generated',
			'ai_feedback', 'created_at', 'updated_at'
		]
		read_only_fields = ['word_count', 'ai_feedback']