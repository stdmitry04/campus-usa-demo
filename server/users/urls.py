# server/users/urls.py
from django.urls import path, include

urlpatterns = [
	path('', include('users.auth_urls')),
	path('', include('users.profile_urls')),
]