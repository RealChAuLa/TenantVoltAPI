import os
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Path to your Firebase Admin SDK JSON file
# Store this securely and don't commit to version control!
FIREBASE_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'firebase-admin-sdk.json')


def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    try:
        app = firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(FIREBASE_CONFIG_PATH)
        app = firebase_admin.initialize_app(cred)

    # Initialize and return Firestore client
    db = firestore.client()
    return app, db


# Initialize Firebase and Firestore when this module is imported
firebase_app, firestore_db = initialize_firebase()