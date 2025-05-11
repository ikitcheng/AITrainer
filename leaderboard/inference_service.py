from flask import Flask, request, jsonify
import os
import tempfile
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from src.workout_monitoring import process_video
from src.config import exercise_settings
from leaderboard.database.mongodb import Workout, User, db
from leaderboard.database.gcs_storage import GCSStorage
from leaderboard.config.settings import settings

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': settings.MONGODB_DB,
    'host': settings.MONGODB_URI
}

# Initialize database and GCS
db.init_app(app)
gcs = GCSStorage()

@app.route('/process_workout', methods=['POST'])
def process_workout():
    """
    Process a workout video that's stored in GCS.
    
    Expected JSON payload:
    {
        "workout_id": "workout_mongodb_id",
        "video_url": "gcs_url_of_uploaded_video",
        "body_mass": 70.5,
        "exercise_mass": 20.0,
        "exercise_type": "pullups"
    }
    
    Returns:
        JSON with workout metrics and URL to processed video
    """
    # Get data from request
    data = request.json
    print(data)

    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ['workout_id', 'video_url', 'body_mass', 'exercise_mass', 'exercise_type']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    temp_path = None
    try:
        # Create temporary file for downloaded video
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()  # Close the file handle but keep the file on disk
        
        # Debug: hard code temp path of video
        # temp_path = r"C:\Users\matth\AppData\Local\Temp\pullups_weighted.mp4"
        
        # Download video from GCS
        gcs.download_video(data['video_url'], temp_path)

        # Process video
        metrics = process_video(
            temp_path,
            body_mass=float(data['body_mass']),
            exercise_mass=float(data['exercise_mass']),
            exercise_type=data['exercise_type'],
            up_angle=exercise_settings[data['exercise_type']]['up_angle'],
            down_angle=exercise_settings[data['exercise_type']]['down_angle'],
            displacement=exercise_settings[data['exercise_type']]['displacement'],
            is_display=False
        )
        
        # Get processed video path
        processed_video_path = metrics['processed_video_path']
        print("processed_video_path: ", processed_video_path)
        
        if not settings.DEBUG:
            ## If only testing process_video, comment out the following lines which uses gcs and mongodb
            # Retrieve workout record for update
            workout = Workout.objects(id=data['workout_id']).first()
            if not workout:
                return jsonify({"error": "Workout not found"}), 404
            
            # Extract user_id from workout
            user_id = str(workout.user.id)
            
            # Upload processed video to GCS
            processed_video_url = gcs.upload_video(processed_video_path, user_id)
        
        # Clean up temporary files
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(processed_video_path):
            os.remove(processed_video_path)

        # Return success response with metrics
        return jsonify({
            "success": True,
            "workout_id": str(workout.id),
            "metrics": {
                "rep_count": metrics['rep_count'],
                "avg_power": metrics['avg_power'],
                "max_power": metrics['max_power'],
                "avg_power_per_kg": metrics['avg_power_per_kg'],
                "max_power_per_kg": metrics['max_power_per_kg'],
            },
            "processed_video_url": processed_video_url #processed_video_path for local
        })
        
    except Exception as e:
        print(f"Error processing workout: {str(e)}")
        # Clean up temporary file if it exists and there was an error
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_error:
                print(f"Error removing temporary file: {str(cleanup_error)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host=settings.INFERENCE_HOST, port=settings.INFERENCE_PORT, debug=False)