# server/universities/base_views.py
from rest_framework import viewsets, generics, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import University, SavedUniversity
from .serializers import UniversitySerializer, SavedUniversitySerializer
import logging

logger = logging.getLogger(__name__)

class UniversityViewSet(viewsets.ReadOnlyModelViewSet):
	"""university browsing and search"""
	queryset = University.objects.all()
	serializer_class = UniversitySerializer
	permission_classes = [IsAuthenticated]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ['location', 'has_financial_aid']
	search_fields = ['name', 'city', 'state']
	ordering_fields = ['name', 'rank', 'acceptance_rate', 'annual_tuition']
	ordering = ['rank', 'name']

	def get_serializer_context(self):
		"""pass request to serializer for is_saved field"""
		context = super().get_serializer_context()
		context['request'] = self.request
		return context

	@action(detail=True, methods=['post'])
	def toggle_save(self, request, pk=None):
		"""toggle save on a university"""
		try:
			university = self.get_object()
			saved_university, created = SavedUniversity.objects.get_or_create(
				user=request.user,
				university=university
			)

			if created:
				message = f'saved {university.name} to your profile'
				saved = True
				logger.info(f"user {request.user.id} saved university {university.id}")
			else:
				saved_university.delete()
				message = f'removed {university.name} from saved universities'
				saved = False
				logger.info(f"user {request.user.id} unsaved university {university.id}")

			return Response({
				'message': message,
				'saved': saved
			}, status=status.HTTP_200_OK)

		except Exception as e:
			logger.error(f"error toggling save for university {pk}: {e}")
			return Response({
				'error': 'failed to toggle save status',
				'detail': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=False, methods=['get'], url_path='saved')
	def saved(self, request):
		"""get user's saved universities - FIXED IMPLEMENTATION"""
		try:
			logger.info(f"fetching saved universities for user {request.user.id}")

			# get saved university relationships for this user
			saved_relations = SavedUniversity.objects.filter(user=request.user).select_related('university')

			logger.info(f"found {saved_relations.count()} saved universities for user {request.user.id}")

			# transform to expected format - return list directly (not paginated)
			saved_universities = []
			for relation in saved_relations:
				university = relation.university
				saved_universities.append({
					'id': university.id,
					'name': university.name,
					'location': university.location,
					'rank': university.rank,
					'admissionChance': f"{int(university.admission_chance)}%",
					'acceptanceRate': f"{int(university.acceptance_rate)}%",
					'avgSAT': university.avg_sat_score,
					'avgGPA': university.avg_gpa,
					'annualTuition': f"${university.annual_tuition:,}/yr",
					'hasFinancialAid': university.has_financial_aid,
					'websiteUrl': university.website_url,
					'logo': university.logo.url if university.logo else None,
				})

			logger.info(f"returning {len(saved_universities)} transformed universities")
			return Response(saved_universities, status=status.HTTP_200_OK)

		except Exception as e:
			logger.error(f"error fetching saved universities for user {request.user.id}: {e}")
			return Response({
				'error': 'failed to fetch saved universities',
				'detail': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@action(detail=False, methods=['get'])
	def saved_ids(self, request):
		"""get just the IDs of saved universities"""
		try:
			saved_ids = list(SavedUniversity.objects.filter(user=request.user).values_list('university_id', flat=True))
			logger.info(f"returning {len(saved_ids)} saved university IDs for user {request.user.id}")
			return Response({'saved_university_ids': saved_ids}, status=status.HTTP_200_OK)
		except Exception as e:
			logger.error(f"error getting saved IDs for user {request.user.id}: {e}")
			return Response({'saved_university_ids': []}, status=status.HTTP_200_OK)


class UniversitySearchView(generics.ListAPIView):
	"""advanced university search with custom filters"""
	serializer_class = UniversitySerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		queryset = University.objects.all()

		# basic search filters
		search = self.request.query_params.get('search', None)
		if search:
			queryset = queryset.filter(name__icontains=search)

		# financial aid filter
		has_aid = self.request.query_params.get('has_aid', None)
		if has_aid == 'true':
			queryset = queryset.filter(has_financial_aid=True)

		# ranking filter
		max_rank = self.request.query_params.get('max_rank', None)
		if max_rank:
			try:
				queryset = queryset.filter(rank__lte=int(max_rank))
			except ValueError:
				pass

		return queryset.order_by('rank')

	def get_serializer_context(self):
		"""pass request to serializer for is_saved field"""
		context = super().get_serializer_context()
		context['request'] = self.request
		return context