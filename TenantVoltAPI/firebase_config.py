import json
import os
import firebase_admin
import requests
from firebase_admin import credentials, auth, firestore
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the absolute path to your project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Path to your Firebase Admin SDK JSON file - adjust this to match your actual file name
FIREBASE_CONFIG_PATH = os.path.join(BASE_DIR, os.getenv("FIREBASE_ADMIN_SDK_NAME"))
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

# Global variables to store Firebase app and Firestore client
firebase_app = None
firestore_db = None


def initialize_firebase():
    global firebase_app, firestore_db

    if firebase_app:
        return firebase_app, firestore_db

    if not os.path.exists(FIREBASE_CONFIG_PATH):
        logger.error(f"Firebase config file not found at: {FIREBASE_CONFIG_PATH}")
        raise FileNotFoundError(f"Firebase config file not found at: {FIREBASE_CONFIG_PATH}")

    try:
        # Initialize the app with credential
        logger.info(f"Initializing Firebase with config from: {FIREBASE_CONFIG_PATH}")
        cred = credentials.Certificate(FIREBASE_CONFIG_PATH)
        firebase_app = firebase_admin.initialize_app(cred)

        # Initialize Firestore client
        firestore_db = firestore.client()
        logger.info("Firebase and Firestore initialized successfully")

        return firebase_app, firestore_db
    except Exception as e:
        logger.error(f"Error initializing Firebase: {str(e)}")
        raise


def sign_in_with_email_password(email, password):
    """
    Authenticates a user with email and password using Firebase Authentication REST API
    Returns: (user_data, id_token, refresh_token, error_message)
    """
    try:
        # Firebase Auth REST API endpoint
        sign_in_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

        # Payload for authentication
        payload = json.dumps({
            "email": email,
            "password": password,
            "returnSecureToken": True
        })

        # Headers
        headers = {
            "Content-Type": "application/json"
        }

        # Make the request to Firebase Auth API
        response = requests.post(sign_in_url, data=payload, headers=headers)

        # Check if request was successful
        if response.status_code == 200:
            auth_data = response.json()
            id_token = auth_data.get('idToken')
            refresh_token = auth_data.get('refreshToken')
            uid = auth_data.get('localId')

            # Get additional user data from Firebase Admin SDK
            try:
                # Initialize Firebase if not already initialized
                initialize_firebase()
                user = auth.get_user(uid)

                # Create user data dictionary
                user_data = {
                    'uid': user.uid,
                    'email': user.email,
                    'emailVerified': user.email_verified,
                    'displayName': user.display_name,
                }

                return user_data, id_token, refresh_token, None

            except Exception as e:
                logger.error(f"Error getting user data: {str(e)}")
                return None, id_token, refresh_token, f"Authentication succeeded but error getting user data: {str(e)}"
        else:
            # Authentication failed
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Authentication failed')
            logger.error(f"Authentication error: {error_message}")
            return None, None, None, error_message

    except Exception as e:
        logger.error(f"Exception during authentication: {str(e)}")
        return None, None, None, str(e)

# Don't initialize Firebase when this module is imported
# Instead, call initialize_firebase() explicitly when needed