# server/essays/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.EssayViewSet, basename='essay')

urlpatterns = [
    # router endpoints - provides full CRUD at /api/essays/
    path('', include(router.urls)),
]