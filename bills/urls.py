from django.urls import path
from bills import views

urlpatterns = [
    path('send-notification/', views.send_bill_notification, name='send_bill_notification'),
]