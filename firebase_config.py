import os
import json
import firebase_admin
from firebase_admin import credentials, db

# Load Firebase key from environment variable
firebase_key = json.loads(os.environ.get("FIREBASE_KEY"))

cred = credentials.Certificate(firebase_key)

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://real-time-app-f9712-default-rtdb.firebaseio.com/'
})