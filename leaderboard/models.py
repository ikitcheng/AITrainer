from datetime import datetime
from flask_mongoengine import MongoEngine
from flask_login import UserMixin

db = MongoEngine()

class User(UserMixin, db.Document):
    username = db.StringField(max_length=80, unique=True, required=True)
    email = db.StringField(max_length=120, unique=True, required=True)
    password_hash = db.StringField(max_length=256)
    is_admin = db.BooleanField(default=False)
    created_at = db.DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'users'}

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username}>'

class Workout(db.Document):
    user = db.ReferenceField(document_type=User, required=True)
    body_mass = db.FloatField(required=True)  # User's body mass in kg
    exercise_mass = db.FloatField(required=True)  # Mass being lifted in kg
    exercise_type = db.StringField(max_length=50, required=True)
    rep_count = db.IntField(required=True)
    avg_power = db.FloatField(required=True)  # Average power in Watts
    max_power = db.FloatField(required=True)  # Maximum power in Watts
    avg_power_per_kg = db.FloatField(required=True)  # Average power per kg
    max_power_per_kg = db.FloatField(required=True)  # Maximum power per kg
    video_path = db.StringField(max_length=255)  # Path to stored video
    is_public = db.BooleanField(default=False)  # Whether to show on leaderboard
    created_at = db.DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'workouts'}

    def __repr__(self):
        return f'<Workout {self.id}>'