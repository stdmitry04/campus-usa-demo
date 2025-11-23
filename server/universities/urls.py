# server/universities/urls.py - FIXED VERSION (no conflicts)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# create router and register the main viewset
router = DefaultRouter()
router.register(r'', views.UniversityViewSet, basename='university')

urlpatterns = [
	# ONLY custom endpoints that don't conflict with ViewSet actions
	path('search/', views.UniversitySearchView.as_view(), name='university-search'),

	# remove the conflicting 'saved/' path - it's handled by ViewSet action
	# path('saved/', views.SavedUniversitiesView.as_view(), name='saved-universities'), # REMOVED

	# router handles all CRUD + custom actions like 'saved'
	path('', include(router.urls)),
]