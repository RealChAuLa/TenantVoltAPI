from django.http import HttpResponse, JsonResponse
from django.urls import path, include

urlpatterns = [
    path('health/', lambda request: JsonResponse({'status': 'ok'})),

    # Authentication endpoints
    path('api/auth/', include('authentication.urls')),
]