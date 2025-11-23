# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
	"""simple api root endpoint"""
	return JsonResponse({
		'message': 'college application platform api',
		'endpoints': {
			'auth': '/api/auth/',
			'universities': '/api/universities/',
			'documents': '/api/documents/',
			'essays': '/api/essays/',
			'messaging': '/api/messaging/',
			'profile': '/api/profile/',
			'admin': '/admin/'
		}
	})

urlpatterns = [
	path('admin/', admin.site.urls),
	path('', api_root),  # add root endpoint

	# authentication endpoints
	path('api/auth/', include('users.auth_urls')),  # separate auth urls

	# user profile endpoints (direct, not under auth)
	path('api/', include('users.profile_urls')),   # this gives /api/profile/, /api/academic-info/ etc

	# other api endpoints
	path('api/universities/', include('universities.urls')),
	path('api/documents/', include('documents.urls')),
	path('api/essays/', include('essays.urls')),
	path('api/messaging/', include('messaging.urls')),
]