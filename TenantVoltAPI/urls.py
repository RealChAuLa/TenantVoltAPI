"""
URL configuration for TenantVoltAPI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import path, re_path
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# Import views from the auth_views file we just created
from .auth_views import login_with_email_password, get_user_profile, update_user_profile

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Schema view for Swagger documentation
schema_view = get_schema_view(
   openapi.Info(
      title="TenantVolt API",
      default_version='v1',
      description="API documentation for TenantVolt application",
   ),
   public=True,
)
urlpatterns = [
    #root URL returns X-CSRFToken
    path('', lambda request: JsonResponse({'X-CSRFToken': request.META.get('CSRF_COOKIE')})),
    path('admin/', admin.site.urls),

    # Authentication endpoints
    path('api/auth/login/', login_with_email_password, name='login'),
    path('api/auth/profile/', get_user_profile, name='user_profile'),
    path('api/auth/profile/update/', update_user_profile, name='update_profile'),

    # Swagger URL
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]