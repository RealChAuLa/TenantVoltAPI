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

FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

# Get Firebase credentials from environment variable as JSON
def get_firebase_credentials():
    firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if not firebase_credentials_json:
        raise ValueError("FIREBASE_CREDENTIALS_JSON environment variable is not set")

    try:
        return json.loads(firebase_credentials_json)
    except json.JSONDecodeError:
        raise ValueError("Invalid FIREBASE_CREDENTIALS_JSON format")

# Global variables to store Firebase app and Firestore client
firebase_app = None
firestore_db = None


def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    global firebase_app, firestore_db

    if firebase_app:
        return firebase_app, firestore_db

    try:
        # Initialize the app with credential
        logger.info(f"Initializing Firebase with config from: FIREBASE_CREDENTIALS_JSON")
        cred = credentials.Certificate(get_firebase_credentials())
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
    Returns: (id_token, uid, error_message)
    """
    try:
        # Firebase Auth REST API endpoint
        sign_in_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

        # Payload for authentication
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        # Make the request to Firebase Auth API
        response = requests.post(sign_in_url, json=payload)

        # Check if request was successful
        if response.status_code == 200:
            auth_data = response.json()
            id_token = auth_data.get('idToken')
            uid = auth_data.get('localId')
            return id_token, uid, None
        else:
            # Authentication failed
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Authentication failed')
            logger.error(f"Authentication error: {error_message}")
            return None, None, error_message

    except Exception as e:
        logger.error(f"Exception during authentication: {str(e)}")
        return None, None, str(e)


def create_user_with_email_password(email, password):
    """
    Creates a new user with email and password using Firebase Authentication REST API
    Returns: (id_token, uid, error_message)
    """
    try:
        # Firebase Auth REST API endpoint for sign up
        sign_up_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"

        # Payload for authentication
        payload = {
            "email": email,
            "password": password
        }

        # Make the request to Firebase Auth API
        response = requests.post(sign_up_url, json=payload)

        # Check if request was successful
        if response.status_code == 200:
            auth_data = response.json()
            uid = auth_data.get('localId')
            return uid, None
        else:
            # User creation failed
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'User creation failed')
            logger.error(f"User creation error: {error_message}")
            return None, error_message

    except Exception as e:
        logger.error(f"Exception during user creation: {str(e)}")
        return None, str(e)