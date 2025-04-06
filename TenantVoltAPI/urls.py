from django.http import HttpResponse, JsonResponse
from django.urls import path, include

urlpatterns = [
    path('health/', lambda request: JsonResponse({'status': 'ok'})),

    # Authentication endpoints
    path('api/auth/', include('authentication.urls')),

    # Order endpoints
    path('api/orders/', include('orders.urls')),

    # Bills endpoints
    path('api/bills/', include('bills.urls')),
]