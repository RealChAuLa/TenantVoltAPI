from django.http import JsonResponse
from firebase_admin import auth
from .firebase_config import firestore_db
import json
from datetime import datetime

def login_with_email_password(request):
    """
    Endpoint for Firebase Email/Password authentication.
    
    Expected request body:
    {
        "idToken": "firebase-id-token-after-client-login"
    }
    
    This endpoint verifies the token and returns user details from Firestore.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Get the ID token sent by the client (after they login with Firebase client SDK)
        id_token = data.get('idToken')
        
        if not id_token:
            return JsonResponse({
                'error': 'ID token is required',
                'message': 'Authentication must be done on client side with Firebase Auth SDK'
            }, status=400)
        
        # Verify the ID token
        try:
            # Verify and decode the token
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            
            # Get basic user details from Firebase Auth
            user = auth.get_user(uid)
            
            # Get additional user details from Firestore
            # User details are in "home_owners" collection with UID as document ID
            home_owner_ref = firestore_db.collection('home_owners').document(uid)
            home_owner_doc = home_owner_ref.get()
            
            # Default user data from Auth
            user_data = {
                'uid': user.uid,
                'email': user.email,
                'emailVerified': user.email_verified,
                'displayName': user.display_name,
                'lastLoginAt': decoded_token.get('auth_time'),
                'createdAt': user.user_metadata.creation_timestamp / 1000
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
                
                # Set Firestore data availability flag
                user_data['hasProfile'] = True
            else:
                # User exists in Auth but not in Firestore
                user_data['hasProfile'] = False
            
            # Return user data along with login timestamp
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'loginTime': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                'user': user_data
            })
            
        except auth.InvalidIdTokenError:
            return JsonResponse({'error': 'Invalid ID token'}, status=401)
        except auth.ExpiredIdTokenError:
            return JsonResponse({'error': 'Token expired'}, status=401)
        except auth.RevokedIdTokenError:
            return JsonResponse({'error': 'Token revoked'}, status=401)
        except auth.UserDisabledError:
            return JsonResponse({'error': 'User account is disabled'}, status=403)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

def get_user_profile(request):
    """
    Get the profile of an authenticated user from Firestore.
    Requires authentication with Bearer token.
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Authorization header required'}, status=401)
    
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
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=401)

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
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Authorization header required'}, status=401)
    
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
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)