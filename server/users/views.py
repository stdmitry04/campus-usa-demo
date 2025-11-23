# server/users/base_views.py - UPDATED FOR CHUNKED EMBEDDINGS
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserProfile, AcademicInfo, Preferences
from .serializers import (
	UserSerializer, UserProfileSerializer, AcademicInfoSerializer, PreferencesSerializer,
	UserUpdateSerializer, ProfileUpdateSerializer
)
import logging

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
	"""user registration endpoint"""
	queryset = User.objects.all()
	serializer_class = UserSerializer
	permission_classes = [AllowAny]

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()

		# create related objects automatically
		UserProfile.objects.create(user=user)
		Preferences.objects.create(user=user)

		# generate tokens for immediate login
		refresh = RefreshToken.for_user(user)

		# trigger initial complete profile embedding with new chunked system
		try:
			from core.tasks.embedding_tasks import embed_user_profile_task
			# use apply_async for better control in production
			result = embed_user_profile_task.apply_async(
				args=[user.id],
				countdown=2  # delay 2 seconds to ensure db commit
			)
			logger.info(f"scheduled complete chunked profile embedding for new user {user.id}: task_id={result.id}")
		except Exception as e:
			logger.error(f"failed to schedule initial profile embedding: {e}")

		return Response({
			'user': UserSerializer(user).data,
			'refresh': str(refresh),
			'access': str(refresh.access_token),
			'message': 'account created successfully!'
		}, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
	"""logout by blacklisting the refresh token"""
	permission_classes = [IsAuthenticated]

	def post(self, request):
		try:
			refresh_token = request.data["refresh"]
			token = RefreshToken(refresh_token)
			token.blacklist()
			return Response({'message': 'logged out successfully'})
		except Exception as e:
			return Response({'error': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
	"""get and update user profile with nested data"""
	serializer_class = UserProfileSerializer
	permission_classes = [IsAuthenticated]

	def get_object(self):
		# get or create profile for the current user
		profile, created = UserProfile.objects.get_or_create(user=self.request.user)

		# ensure preferences exist for this user
		preferences, pref_created = Preferences.objects.get_or_create(
			user=self.request.user,
			defaults={
				'applying_for': 'bachelor',
				'fields_of_interest': [],
				'preferred_ranking_min': 0,
				'preferred_ranking_max': 500,
				'need_financial_aid': 0,
			}
		)

		if created:
			print(f"created new profile for user: {self.request.user.username}")
		if pref_created:
			print(f"created new preferences for user: {self.request.user.username}")

		return profile

	def update(self, request, *args, **kwargs):
		"""handle profile updates with nested user data and trigger targeted chunk re-embedding"""
		try:
			profile = self.get_object()

			# extract different types of updates
			user_fields = {}
			profile_fields = {}

			for key, value in request.data.items():
				if key in ['first_name', 'last_name', 'email']:
					user_fields[key] = value
				elif key in ['avatar', 'phone_number']:
					profile_fields[key] = value

			# track if any meaningful changes were made
			profile_updated = False

			# update user fields if any
			if user_fields:
				print(f"updating user fields: {user_fields}")
				user_serializer = UserUpdateSerializer(request.user, data=user_fields, partial=True)
				if user_serializer.is_valid():
					user_serializer.save()
					print(f"user updated")
					profile_updated = True
				else:
					print(f"user validation failed: {user_serializer.errors}")
					return Response({
						'error': 'user validation failed',
						'details': user_serializer.errors
					}, status=status.HTTP_400_BAD_REQUEST)

			# update profile fields if any
			if profile_fields:
				print(f"updating profile fields: {profile_fields}")
				profile_serializer = ProfileUpdateSerializer(profile, data=profile_fields, partial=True)
				if profile_serializer.is_valid():
					profile_serializer.save()
					print(f"profile updated")
					profile_updated = True
				else:
					print(f"profile validation failed: {profile_serializer.errors}")
					return Response({
						'error': 'profile validation failed',
						'details': profile_serializer.errors
					}, status=status.HTTP_400_BAD_REQUEST)

			# trigger targeted re-embedding for basic info changes - NEW CHUNKED APPROACH
			if profile_updated:
				try:
					from core.tasks.embedding_tasks import update_basic_info_chunks_task

					# update only basic personal info and summary chunks
					result = update_basic_info_chunks_task.delay(request.user.id)
					logger.info(f"scheduled basic info chunk update: task_id={result.id}")

				except Exception as e:
					logger.error(f"failed to schedule basic info chunk update: {e}")

			# return updated profile data
			updated_profile = self.get_object()
			serializer = self.get_serializer(updated_profile)
			return Response(serializer.data)

		except Exception as e:
			print(f"profile update failed: {e}")
			return Response({
				'error': 'profile update failed',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcademicInfoView(generics.RetrieveUpdateDestroyAPIView):
	"""manage academic information"""
	serializer_class = AcademicInfoSerializer
	permission_classes = [IsAuthenticated]

	def get_object(self):
		# get or create academic info for current user
		academic_info, created = AcademicInfo.objects.get_or_create(user=self.request.user)
		return academic_info

	def update(self, request, *args, **kwargs):
		"""handle academic info updates with validation and trigger academic-specific chunk re-embedding"""
		try:
			academic_info = self.get_object()

			print(f"updating academic info: {request.data}")

			serializer = self.get_serializer(academic_info, data=request.data, partial=True)
			if serializer.is_valid():
				serializer.save()
				print(f"academic info updated")

				# trigger academic-specific chunk re-embedding - NEW CHUNKED APPROACH
				print(f"attempting to schedule academic chunk re-embedding for user {request.user.id}")
				try:
					from core.tasks.embedding_tasks import update_academic_chunks_task

					# update academic chunks: high_school, test_scores, profile_summary,
					# score_narrative, academic_standing, university_match
					result = update_academic_chunks_task.delay(request.user.id)
					logger.info(f"scheduled academic chunk update: task_id={result.id}")

				except Exception as e:
					logger.error(f"failed to schedule academic chunk update: {e}")

				return Response(serializer.data)
			else:
				print(f"academic validation failed: {serializer.errors}")
				return Response({
					'error': 'academic validation failed',
					'details': serializer.errors
				}, status=status.HTTP_400_BAD_REQUEST)

		except Exception as e:
			print(f"academic update failed: {e}")
			return Response({
				'error': 'academic update failed',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PreferencesView(generics.RetrieveUpdateAPIView):
	"""manage application preferences"""
	serializer_class = PreferencesSerializer
	permission_classes = [IsAuthenticated]

	def get_object(self):
		# get or create preferences for current user
		preferences, created = Preferences.objects.get_or_create(user=self.request.user)
		return preferences

	def update(self, request, *args, **kwargs):
		"""handle preferences updates and trigger preference-specific chunk re-embedding"""
		try:
			preferences = self.get_object()

			print(f"updating preferences: {request.data}")

			serializer = self.get_serializer(preferences, data=request.data, partial=True)
			if serializer.is_valid():
				serializer.save()
				print(f"preferences updated")

				# trigger preference-specific chunk re-embedding - NEW CHUNKED APPROACH
				print(f"attempting to schedule preferences chunk re-embedding for user {request.user.id}")
				try:
					from core.tasks.embedding_tasks import update_preferences_chunks_task

					# update preference chunks: application_prefs, profile_summary, university_match
					result = update_preferences_chunks_task.delay(request.user.id)
					logger.info(f"scheduled preferences chunk update: task_id={result.id}")

				except Exception as e:
					logger.error(f"failed to schedule preferences chunk update: {e}")

				return Response(serializer.data)
			else:
				print(f"preferences validation failed: {serializer.errors}")
				return Response({
					'error': 'preferences validation failed',
					'details': serializer.errors
				}, status=status.HTTP_400_BAD_REQUEST)

		except Exception as e:
			print(f"preferences update failed: {e}")
			return Response({
				'error': 'preferences update failed',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserStatsView(APIView):
	"""get user's application statistics with enhanced profile completion"""
	permission_classes = [IsAuthenticated]

	def get(self, request):
		try:
			user = request.user
			profile, created = UserProfile.objects.get_or_create(user=user)

			# import here to avoid circular imports
			from documents.models import Document
			from essays.models import Essay
			from messaging.models import Conversation

			# get embedding stats with chunk breakdown - UPDATED FOR CHUNKS
			from core.services.embedding_service import get_embedding_service
			embedding_service = get_embedding_service()

			if embedding_service:
				user_data = embedding_service.get_user_data(user.id)

				# analyze chunk breakdown
				chunk_breakdown = {}
				for chunk in user_data.get('profile_chunks', []):
					chunk_type = chunk.get('chunk_type', 'unknown')
					chunk_breakdown[chunk_type] = chunk_breakdown.get(chunk_type, 0) + 1

				embedding_stats = {
					'total_profile_chunks': len(user_data.get('profile_chunks', [])),
					'total_document_chunks': len(user_data.get('documents', [])),
					'profile_chunk_breakdown': chunk_breakdown,
				}
			else:
				embedding_stats = {
					'total_profile_chunks': 0,
					'total_document_chunks': 0,
					'profile_chunk_breakdown': {},
					'error': 'embedding service unavailable'
				}

			stats = {
				'documents_uploaded': Document.objects.filter(user=user).count(),
				'essays_written': Essay.objects.filter(user=user).count(),
				'chat_conversations': Conversation.objects.filter(user=user).count(),
				'profile_completion': profile.get_completion_percentage(),
				'embedding_stats': embedding_stats
			}

			return Response(stats)
		except Exception as e:
			print(f"failed to get user stats: {e}")
			return Response({
				'error': 'failed to get user stats',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileChunkStatusView(APIView):
	"""check embedding status for user profile chunks - NEW"""
	permission_classes = [IsAuthenticated]

	def get(self, request):
		try:
			user = request.user

			# import here to avoid circular imports
			from core.tasks.embedding_tasks import inspect_user_chunks
			from core.services.embedding_service import ProfileChunker

			# get detailed chunk information
			chunks_info = inspect_user_chunks(user.id)

			if 'error' in chunks_info:
				return Response({
					'error': chunks_info['error']
				}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

			# calculate completion status
			available_types = set(ProfileChunker.CHUNK_TYPES.keys())
			existing_types = set(chunks_info.get('chunk_details', {}).keys())
			missing_types = available_types - existing_types

			completion_percentage = round((len(existing_types) / len(available_types)) * 100)

			return Response({
				'chunk_status': {
					'total_chunk_types_available': len(available_types),
					'chunk_types_embedded': len(existing_types),
					'completion_percentage': completion_percentage,
					'existing_chunks': list(existing_types),
					'missing_chunks': list(missing_types),
					'chunk_details': chunks_info.get('chunk_details', {}),
					'total_documents': chunks_info.get('total_documents', 0)
				}
			})

		except Exception as e:
			print(f"failed to get chunk status: {e}")
			return Response({
				'error': 'failed to get chunk status',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TriggerChunkUpdateView(APIView):
	"""manually trigger specific chunk updates - NEW"""
	permission_classes = [IsAuthenticated]

	def post(self, request):
		try:
			chunk_types = request.data.get('chunk_types', [])

			if not chunk_types:
				return Response({
					'error': 'chunk_types required',
					'available_types': list(ProfileChunker.CHUNK_TYPES.keys())
				}, status=status.HTTP_400_BAD_REQUEST)

			# validate chunk types
			from core.services.embedding_service import ProfileChunker
			valid_types = set(ProfileChunker.CHUNK_TYPES.keys())
			invalid_types = set(chunk_types) - valid_types

			if invalid_types:
				return Response({
					'error': f'invalid chunk types: {list(invalid_types)}',
					'available_types': list(valid_types)
				}, status=status.HTTP_400_BAD_REQUEST)

			# trigger chunk update
			from core.tasks.embedding_tasks import update_profile_chunks_task
			result = update_profile_chunks_task.delay(request.user.id, chunk_types)

			logger.info(f"manually triggered chunk update for user {request.user.id}: {chunk_types}, task_id={result.id}")

			return Response({
				'message': f'chunk update triggered for types: {chunk_types}',
				'task_id': str(result.id),
				'chunk_types': chunk_types
			})

		except Exception as e:
			logger.error(f"failed to trigger chunk update: {e}")
			return Response({
				'error': 'failed to trigger chunk update',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TriggerFullEmbeddingView(APIView):
	"""manually trigger full profile re-embedding (for debugging/admin) - UPDATED"""
	permission_classes = [IsAuthenticated]

	def post(self, request):
		try:
			from core.tasks.embedding_tasks import embed_user_profile_task

			result = embed_user_profile_task.delay(request.user.id)
			logger.info(f"manually triggered full chunked profile embedding for user {request.user.id}: task_id={result.id}")

			return Response({
				'message': 'full chunked profile embedding triggered',
				'task_id': str(result.id)
			})

		except Exception as e:
			logger.error(f"failed to trigger full profile embedding: {e}")
			return Response({
				'error': 'failed to trigger embedding',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchProfileChunksView(APIView):
	"""search user's profile chunks - NEW"""
	permission_classes = [IsAuthenticated]

	def post(self, request):
		try:
			query_text = request.data.get('query', '')
			chunk_types = request.data.get('chunk_types', None)  # optional filter
			limit = min(int(request.data.get('limit', 5)), 10)  # max 10

			if not query_text:
				return Response({
					'error': 'query text required'
				}, status=status.HTTP_400_BAD_REQUEST)

			from core.services.embedding_service import get_embedding_service
			embedding_service = get_embedding_service()

			if not embedding_service:
				return Response({
					'error': 'embedding service not available'
				}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

			# search profile chunks
			results = embedding_service.search_user_profile_chunks(
				user_id=request.user.id,
				query_text=query_text,
				chunk_types=chunk_types,
				limit=limit
			)

			return Response({
				'query': query_text,
				'chunk_types_filter': chunk_types,
				'results_count': len(results),
				'results': results
			})

		except Exception as e:
			logger.error(f"failed to search profile chunks: {e}")
			return Response({
				'error': 'failed to search profile chunks',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileChunkTypesView(APIView):
	"""get available chunk types and their descriptions - NEW"""
	permission_classes = [IsAuthenticated]

	def get(self, request):
		try:
			from core.services.embedding_service import ProfileChunker

			chunk_types_info = []
			for chunk_type, description in ProfileChunker.CHUNK_TYPES.items():
				chunk_types_info.append({
					'type': chunk_type,
					'description': description,
					'category': 'profile'
				})

			return Response({
				'chunk_types': chunk_types_info,
				'total_types': len(chunk_types_info)
			})

		except Exception as e:
			return Response({
				'error': 'failed to get chunk types',
				'details': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)