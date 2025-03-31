from firebase_admin import auth
from django.http import JsonResponse
from functools import wraps
import json

def verify_firebase_token(id_token):
    """Verify the Firebase ID token"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        return None

def login_required(view_func):
    """Decorator for views that require Firebase authentication"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authorization header required'}, status=401)
        
        token = auth_header.split('Bearer ')[1]
        user_data = verify_firebase_token(token)
        
        if user_data is None:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        # Add the user data to the request
        request.firebase_user = user_data
        return view_func(request, *args, **kwargs)
    
    return wrapped_view