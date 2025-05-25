from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    # MongoDB settings
    MONGODB_URI: str = os.getenv('MONGODB_URI', default=None)
    MONGODB_DB: str = os.getenv('MONGODB_DB', default=None)
    
    # Google Cloud Storage settings
    GCS_BUCKET_NAME: str = os.getenv('GCS_BUCKET_NAME', default=None)
    GCS_CREDENTIALS_PATH: str = os.getenv('GCS_CREDENTIALS_PATH', default=None)
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv('GOOGLE_CLIENT_ID', default=None)
    GOOGLE_CLIENT_SECRET: str = os.getenv('GOOGLE_CLIENT_SECRET', default=None)
    GOOGLE_DISCOVERY_URL: str = "https://accounts.google.com/.well-known/openid-configuration"
    
    # Application settings
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key')
    DEBUG: bool = False
    HOST: str = "0.0.0.0" #"localhost"
    PORT: int = 5000
    
    # Model settings
    MODEL_PATH: str = "model/yolov11n-pose.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    
    # File upload settings
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: set = {'mp4', 'avi', 'mov'}
    
    # Inference service settings
    INFERENCE_HOST: str = "0.0.0.0"
    INFERENCE_PORT: int = 5001
    INFERENCE_URL: str = "http://localhost:5001"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 