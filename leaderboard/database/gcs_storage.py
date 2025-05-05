from cloudpathlib import CloudPath
from typing import Optional
import uuid
import os
from ..config.settings import settings

class GCSStorage:
    def __init__(self):
        if not settings.GCS_BUCKET_NAME:
            raise ValueError("GCS_BUCKET_NAME is not set in settings")
        if not settings.GCS_CREDENTIALS_PATH:
            raise ValueError("GCS_CREDENTIALS_PATH is not set in settings")
        if not os.path.exists(settings.GCS_CREDENTIALS_PATH):
            raise FileNotFoundError(f"GCS credentials file not found at: {settings.GCS_CREDENTIALS_PATH}")
            
        self.bucket = CloudPath(f"gs://{settings.GCS_BUCKET_NAME}")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GCS_CREDENTIALS_PATH
        print(f"Initialized GCS storage with bucket: {self.bucket}")
    
    def upload_video(self, file_path: str, user_id: str) -> str:
        """
        Upload a video file to GCS.
        
        Args:
            file_path (str): Local path to the video file
            user_id (str): ID of the user uploading the video
            
        Returns:
            str: Public URL of the uploaded video
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Generate unique filename
        filename = f"{user_id}_{uuid.uuid4()}_{os.path.basename(file_path)}"
        destination_path = self.bucket / "videos" / filename
        
        print(f"Uploading file {file_path} to {destination_path}")
        with open(file_path, 'rb') as f:
            destination_path.write_bytes(f.read())
        
        return str(destination_path)
    
    def download_video(self, video_url: str, destination_path: str) -> None:
        """
        Download a video from GCS.
        
        Args:
            video_url (str): URL of the video in GCS
            destination_path (str): Local path to save the video
        
        Example:
        gcs = GCSStorage()
        gcs.download_video("gs://aitrainer_gcs_bucket/videos/680467d34e9356ba733c437f_b26cf968-9e0a-4b81-b97a-4552ec1b128e_680467d34e9356ba733c437f_20250423_235532_pullups_weighted.mp4", "./local_video.mp4")
        """
        if not video_url:
            raise ValueError("video_url cannot be None")
        if not destination_path:
            raise ValueError("destination_path cannot be None")
            
        print(f"Attempting to download from {video_url} to {destination_path}")
        
        try:
            source_path = CloudPath(video_url)
            print(f"Created CloudPath object: {source_path}")
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            print("Starting download...")
            source_path.download_to(destination_path)
            print("Download completed successfully")
            
            if not os.path.exists(destination_path):
                raise FileNotFoundError(f"File was not created at {destination_path}")
                
            file_size = os.path.getsize(destination_path)
            print(f"Downloaded file size: {file_size} bytes")
            
        except Exception as e:
            print(f"Error during download: {str(e)}")
            raise

    def delete_video(self, video_url: str) -> None:
        """
        Delete a video from GCS.
        
        Args:
            video_url (str): URL of the video in GCS
        """
        if not video_url:
            raise ValueError("video_url cannot be None")
            
        source_path = CloudPath(video_url)
        source_path.unlink() 