import firebase_admin
from firebase_admin import credentials, firestore
from decouple import config  # Add this

# Read Firebase key path from .env
firebase_key_path = config("FIREBASE_KEY_PATH")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_key_path)
firebase_admin.initialize_app(cred)

# Initialize Firestore database
db = firestore.client()

