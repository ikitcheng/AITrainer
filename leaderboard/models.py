from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    workouts = db.relationship('Workout', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body_mass = db.Column(db.Float, nullable=False)  # User's body mass in kg
    exercise_mass = db.Column(db.Float, nullable=False)  # Mass being lifted in kg
    exercise_type = db.Column(db.String(50), nullable=False)
    rep_count = db.Column(db.Integer, nullable=False)
    avg_power = db.Column(db.Float, nullable=False)  # Average power in Watts
    max_power = db.Column(db.Float, nullable=False)  # Maximum power in Watts
    avg_power_per_kg = db.Column(db.Float, nullable=False)  # Average power per kg
    max_power_per_kg = db.Column(db.Float, nullable=False)  # Maximum power per kg
    video_path = db.Column(db.String(255))  # Path to stored video
    is_public = db.Column(db.Boolean, default=False)  # Whether to show on leaderboard
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Workout {self.id}>'