# server/documents/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.DocumentViewSet, basename='document')

urlpatterns = [
    # router endpoints - provides full CRUD at /api/documents/
    path('', include(router.urls)),
]