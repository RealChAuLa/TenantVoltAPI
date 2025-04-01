from django.urls import path
from orders import views

# Define URL patterns for orders
urlpatterns = [
    path('pending/', views.get_pending_orders, name='get_pending_orders'),
    path('update-status/', views.update_order_status, name='update_order_status'),
]