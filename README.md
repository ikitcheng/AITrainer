# AI Trainer

AI Trainer helps you track exercises, count reps, and calculate your power output using computer vision.

## How it works?
1. **Pose Estimation**: 
   - Uses YOLO11 pose estimation to detect 17 key body points
   - Tracks specific keypoints for exercise form (e.g., shoulders, elbows, 
   wrists for pull-ups)
2. **Rep Counting**:
   - Monitors angle changes between key body points
   - Detects transitions between "up" and "down" positions
   - Counts completed repetitions based on full range of motion
3. **Power Calculation**:
   - Measures time duration of each rep using frame count and FPS
   - Uses physics formula: P = m × g × h / t
   - Where:
     - m = user mass (kg)
     - g = gravitational acceleration (9.81 m/s²)
     - h = vertical displacement (m)
     - t = time taken (s)

## Architecture

1. **Frontend Service** (`leaderboard/app.py`): Handles user authentication, file uploads to Google Cloud Storage, and dashboard display.
2. **Inference Service** (`inference_service.py`): Processes workout videos, extracts metrics, and uploads processed videos back to Google Cloud Storage.

The flow of data is as follows:
1. User uploads workout video through the frontend
2. Frontend uploads the video to Google Cloud Storage (GCS)
3. Frontend creates a workout record in MongoDB with "pending" status
4. Frontend sends processing request to the inference service
5. Inference service downloads the video from GCS, processes it, and uploads the processed video back to GCS
6. Inference service updates the workout record in MongoDB with the metrics and "complete" status
7. Frontend displays the processed results in the dashboard

## Setup

### Prerequisites

- Python 3.8+
- MongoDB
- Google Cloud Storage account with a configured bucket
- Google OAuth credentials (for authentication)

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# MongoDB settings
MONGODB_URI=mongodb://localhost:27017/ai_trainer
MONGODB_DB=ai_trainer

# Google Cloud Storage settings
GCS_BUCKET_NAME=your-bucket-name
GCS_CREDENTIALS_PATH=/path/to/your/gcs-credentials.json

# Google OAuth settings
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Flask settings
SECRET_KEY=your-secret-key
HOST=0.0.0.0
PORT=5000

# Inference service settings
INFERENCE_HOST=0.0.0.0
INFERENCE_PORT=5001
INFERENCE_URL=http://localhost:5001
```

### Installation

1. Clone the repository
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
3. Set up the environment variables as described above

### Running the Services

1. Start the frontend service:
   ```
   python leaderboard/app.py
   ```

2. Start the inference service:
   ```
   python inference_service.py
   ```

## Development

### Project Structure

```
.
├── leaderboard/
│   ├── app.py                  # Frontend service
│   ├── templates/              # HTML templates
│   ├── static/                 # Static files
│   ├── auth/                   # Authentication modules
│   │   └── google_auth.py      # Google authentication
│   ├── config/                 # Configuration
│   │   └── settings.py         # Settings class
│   └── database/               # Database models
│       ├── mongodb.py          # MongoDB models
│       └── gcs_storage.py      # GCS operations
├── src/
│   └── workout_monitoring.py   # Video processing logic
├── model/                      # ML models
├── inference_service.py        # Inference service
└── requirements.txt            # Python dependencies
```

## Adding New Features

### Adding a New Exercise Type

1. Update the allowed exercise types in `leaderboard/templates/upload.html`
2. Add support for the new exercise in `src/workout_monitoring.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Ultralytics YOLO for the pose estimation model
- OpenCV for image processing capabilities 