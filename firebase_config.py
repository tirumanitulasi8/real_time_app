import firebase_admin
from firebase_admin import credentials, db
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

cred = credentials.Certificate(os.path.join(BASE_DIR, "serviceAccountKey.json"))

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://real-time-app-f9712-default-rtdb.firebaseio.com/'
})

db = db.reference()