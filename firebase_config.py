import firebase_admin
from firebase_admin import credentials, firestore

firebaseConfig = {
  "apiKey": "AIzaSyAPwplgr5ap8QRlF1h-k8lUCgGNyUb5Pxk",  # Add your new API key if needed
  "authDomain": "bd-fitness-challenge-2026.firebaseapp.com",
  "projectId": "bd-fitness-challenge-2026",
  "storageBucket": "bd-fitness-challenge-2026.firebasestorage.app",
  "messagingSenderId": "447583093963",  # Add your new sender ID if needed
  "appId": "1:447583093963:web:c4d49a03db329f4090474e",  # Add your new app ID if needed
  "measurementId": "G-8MM6TDDVXX",  # Add your new measurement ID if needed
  "databaseURL": ""
}

#firebase = pyrebase.initialize_app(firebaseConfig)


import os, json
from firebase_admin import credentials, firestore, initialize_app, storage, auth


# Read Firebase credentials from environment variable (for deployment) or local JSON file
if os.getenv("FIREBASE_CREDENTIALS"):
  firebase_key = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
else:
  with open("bd-fitness-challenge-2026.json", "r") as f:
    firebase_key = json.load(f)

cred = credentials.Certificate(firebase_key)
firebase = initialize_app(cred, {
    "storageBucket": "bd-fitness-challenge-2026.firebasestorage.app"
})

db = firestore.client()
bucket = storage.bucket()
# Firebase Auth is automatically initialized with the app
