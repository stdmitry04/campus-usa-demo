# server/users/profile_urls.py
from django.urls import path
from .views import *

urlpatterns = [
    # profile management endpoints - these become /api/profile/, /api/academic-info/ etc
    path('profile/', ProfileView.as_view(), name='profile'),
    path('academic-info/', AcademicInfoView.as_view(), name='academic-info'),
    path('preferences/', PreferencesView.as_view(), name='preferences'),
    path('user-stats/', UserStatsView.as_view(), name='user-stats'),

    # stats and monitoring
    path('stats/', UserStatsView.as_view(), name='user-stats'),

    # chunked embedding management endpoints
    path('chunks/status/', ProfileChunkStatusView.as_view(), name='chunk-status'),
    path('chunks/types/', ProfileChunkTypesView.as_view(), name='chunk-types'),
    path('chunks/update/', TriggerChunkUpdateView.as_view(), name='trigger-chunk-update'),
    path('chunks/search/', SearchProfileChunksView.as_view(), name='search-chunks'),

    # full embedding management (admin/debug)
    path('embedding/trigger/', TriggerFullEmbeddingView.as_view(), name='trigger-full-embedding'),
]