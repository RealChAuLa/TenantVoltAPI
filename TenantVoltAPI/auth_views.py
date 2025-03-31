from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, UTC
import logging
from .firebase_config import initialize_firebase, sign_in_with_email_password, create_user_with_email_password

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@csrf_exempt
def login(request):
    """
    Endpoint for Firebase Email/Password authentication.

    Expected request body:
    {
        "email": "user@example.com",
        "password": "userPassword123"
    }

    Returns:
    {
        "success": true,
        "token": "firebase-auth-token",
        "uid": "user-uid"
    }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Read request body
        body_data = request.body
        data = json.loads(body_data.decode('utf-8'))

        # Get email and password
        email = data.get('email')
        password = data.get('password')

        # Validate inputs
        if not email or not password:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)

        # Authenticate with Firebase
        token, uid, error = sign_in_with_email_password(email, password)

        if error:
            return JsonResponse({
                'success': False,
                'error': error
            }, status=401)

        # Return token and uid
        return JsonResponse({
            'success': True,
            'token': token,
            'uid': uid
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def signup(request):
    """
    Endpoint for user registration with Firebase.

    Expected request body:
    {
      "first_name": "John",
      "last_name": "Doe",
      "mobile_number": "+1234567890",
      "email": "john.doe@example.com",
      "password" : "Johndoe123",
      "address": "123 Main St, City, Country",
      "tenants": [
        {
          "name": "Alice Smith",
          "email": "alice.smith@example.com",
          "product_id": "1112",
          "address": "456 Elm St, City, Country"
        },
        ...
      ]
    }

    Returns:
    {
        "success": true,
        "token": "firebase-auth-token",
        "uid": "user-uid"
    }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Initialize Firebase
        _, firestore_db = initialize_firebase()

        # Read request body
        body_data = request.body
        data = json.loads(body_data.decode('utf-8'))

        # Get required fields
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        mobile_number = data.get('mobile_number')
        address = data.get('address')
        tenants = data.get('tenants', [])

        # Validate inputs
        if not all([email, password, first_name, last_name, mobile_number, address, tenants]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)

        # Create user in Firebase Authentication
        uid , error = create_user_with_email_password(email, password)

        if error:
            return JsonResponse({
                'success': False,
                'error': error
            }, status=400)

        # Store user data in Firestore
        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'mobile_number': mobile_number,
            'email': email,
            'address': address,
            'order_date_time': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            'order_status': "pending"
        }

        # Add tenants if available
        if tenants and isinstance(tenants, list):
            user_data['tenants'] = tenants

        # Save to Firestore
        house_owners_ref = firestore_db.collection('house_owners').document(uid)
        house_owners_ref.set(user_data)

        # Return token and uid
        return JsonResponse({
            'success': True
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)