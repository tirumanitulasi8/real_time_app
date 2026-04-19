import firebase_admin
from firebase_admin import credentials, db
import os
import json

firebase_key = os.environ.get("FIREBASE_KEY")

if firebase_key:
    cred = credentials.Certificate(json.loads(firebase_key))
else:
    cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://real-time-app-f9712-default-rtdb.firebaseio.com/'
})

db = db.reference()