from django.contrib import admin
from django.urls import path
from .auth_views import login, signup

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication endpoints
    path('api/auth/login/', login, name='login'),
    path('api/auth/signup/', signup, name='signup'),
]