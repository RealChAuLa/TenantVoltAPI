from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from firebase_admin import auth, firestore
import json
from datetime import datetime
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .firebase_config import initialize_firebase

# Configure logging
logger = logging.getLogger(__name__)

from django.http import JsonResponse
from firebase_admin import auth, firestore
import json
from datetime import datetime
import logging
from .firebase_config import initialize_firebase, sign_in_with_email_password

# Configure logging
logger = logging.getLogger(__name__)




# Define the request body schema
login_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email', 'password'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email address'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
    }
)

# Define the response body schema
login_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Operation success status'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message'),
        'loginTime': openapi.Schema(type=openapi.TYPE_STRING, description='Login timestamp (YYYY-MM-DD HH:MM:SS)'),
        'idToken': openapi.Schema(type=openapi.TYPE_STRING, description='JWT authentication token'),
        'refreshToken': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token for obtaining new ID tokens'),
        'user': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'uid': openapi.Schema(type=openapi.TYPE_STRING, description='User ID'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email address'),
                'emailVerified': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Email verification status'),
                'displayName': openapi.Schema(type=openapi.TYPE_STRING, description='User display name', nullable=True),
                'hasProfile': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether user has completed profile'),
            }
        ),
    }
)

@swagger_auto_schema(
    method='post',
    request_body=login_request_schema,
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Login successful",
            schema=login_response_schema
        ),
        status.HTTP_401_UNAUTHORIZED: "Invalid credentials",
        status.HTTP_400_BAD_REQUEST: "Bad request data"
    },
    manual_parameters=[
        openapi.Parameter(
            name='X-CSRFToken',
            in_=openapi.IN_HEADER,
            type=openapi.TYPE_STRING,
            required=True,
            description='CSRF Token (obtained from csrftoken cookie)'
        )
    ],
    operation_description="Login with email and password to receive authentication tokens"
)
@api_view(['POST'])
@csrf_protect
@permission_classes([AllowAny])
def login_with_email_password(request):
    """
    Endpoint for Firebase Email/Password authentication.

    Expected request body:
    {
        "email": "user@example.com",
        "password": "userPassword123"
    }

    This endpoint validates credentials with Firebase and returns user details.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Initialize Firebase
        _, firestore_db = initialize_firebase()

        # Parse request body
        data = json.loads(request.body)

        # Get email and password from request
        email = data.get('email')
        password = data.get('password')

        # Validate required fields
        if not email or not password:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields',
                'message': 'Email and password are required'
            }, status=400)

        # Authenticate with Firebase
        user_data, id_token, refresh_token, error_message = sign_in_with_email_password(email, password)

        if error_message:
            # Authentication failed
            return JsonResponse({
                'success': False,
                'error': 'Authentication failed',
                'message': error_message
            }, status=401)

        # Authentication succeeded, get Firestore data
        uid = user_data['uid']

        # Get additional user details from Firestore
        # User details are in "home_owners" collection with UID as document ID
        home_owner_ref = firestore_db.collection('home_owners').document(uid)
        home_owner_doc = home_owner_ref.get()

        # Add user details from Firestore if available
        if home_owner_doc.exists:
            home_owner_data = home_owner_doc.to_dict()
            user_data.update({
                'name': home_owner_data.get('name', ''),
                'district': home_owner_data.get('district', ''),
                'address': home_owner_data.get('address', ''),
                'telephone': home_owner_data.get('telephone', '')
            })
            user_data['hasProfile'] = True
        else:
            # User exists in Auth but not in Firestore
            user_data['hasProfile'] = False

        # Return tokens and user data
        return JsonResponse({
            'success': True,
            'message': 'Login successful',
            'loginTime': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            'idToken': id_token,  # Frontend should store this for authenticated requests
            'refreshToken': refresh_token,  # Frontend can use this to refresh the ID token
            'user': user_data
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON',
            'message': 'Request body is not valid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }, status=500)


def get_user_profile(request):
    """
    Get the profile of an authenticated user from Firestore.
    Requires authentication with Bearer token.
    """
    # Initialize Firebase
    _, firestore_db = initialize_firebase()

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')

    if not auth_header.startswith('Bearer '):
        return JsonResponse({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authorization header with Bearer token required'
        }, status=401)

    token = auth_header.split('Bearer ')[1]

    try:
        # Verify and decode the token
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']

        # Get basic user details from Firebase Auth
        user = auth.get_user(uid)

        # Get user details from Firestore
        home_owner_ref = firestore_db.collection('home_owners').document(uid)
        home_owner_doc = home_owner_ref.get()

        # Default user data from Auth
        user_data = {
            'uid': user.uid,
            'email': user.email,
            'emailVerified': user.email_verified,
            'displayName': user.display_name
        }

        # Add user details from Firestore if available
        if home_owner_doc.exists:
            home_owner_data = home_owner_doc.to_dict()
            user_data.update({
                'name': home_owner_data.get('name', ''),
                'district': home_owner_data.get('district', ''),
                'address': home_owner_data.get('address', ''),
                'telephone': home_owner_data.get('telephone', '')
            })
            user_data['hasProfile'] = True
        else:
            user_data['hasProfile'] = False

        return JsonResponse({
            'success': True,
            'user': user_data
        })

    except auth.InvalidIdTokenError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid token',
            'message': 'The provided authentication token is invalid'
        }, status=401)
    except auth.ExpiredIdTokenError:
        return JsonResponse({
            'success': False,
            'error': 'Token expired',
            'message': 'The provided authentication token has expired'
        }, status=401)
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }, status=500)


def update_user_profile(request):
    """
    Update the user profile in Firestore.
    Requires authentication with Bearer token.

    Expected request body:
    {
        "name": "John Doe",
        "district": "Central",
        "address": "123 Main St",
        "telephone": "1234567890"
    }
    """
    # Initialize Firebase
    _, firestore_db = initialize_firebase()

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed',
            'message': 'Only POST requests are allowed for this endpoint'
        }, status=405)

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')

    if not auth_header.startswith('Bearer '):
        return JsonResponse({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authorization header with Bearer token required'
        }, status=401)

    token = auth_header.split('Bearer ')[1]

    try:
        # Parse request body
        data = json.loads(request.body)

        # Verify and decode the token
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']

        # Prepare profile data
        profile_data = {
            'name': data.get('name', ''),
            'district': data.get('district', ''),
            'address': data.get('address', ''),
            'telephone': data.get('telephone', ''),
            'updated_at': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Update or create user profile in Firestore
        home_owner_ref = firestore_db.collection('home_owners').document(uid)
        home_owner_ref.set(profile_data, merge=True)

        # Return updated profile
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully',
            'profile': profile_data
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON',
            'message': 'Request body is not valid JSON'
        }, status=400)
    except auth.InvalidIdTokenError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid token',
            'message': 'The provided authentication token is invalid'
        }, status=401)
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }, status=500)