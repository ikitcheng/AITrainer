# AI Trainer

AI Trainer helps you track exercises, count reps, and calculate your power output using computer vision.

## Features

- Real-time pose detection using YOLO11 pose estimation model
- Exercise rep counting
- Power output calculation using physics-based metrics:
  - Power = mass × gravity × displacement / time
  - Real-time display of power output in Watts
  - Average power output across multiple repetitions
- Support for different exercises (currently implemented):
  - Pull-ups
  - Push-ups (experimental)
- Performance metrics display:
  - Rep count
  - Mass (kg)
  - Vertical displacement (m)
  - Time per rep (ms)
  - Power output (W)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AITrainer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download the YOLO pose estimation model:
```bash
# The model will be downloaded automatically on first run
# or you can manually place yolo11n-pose.pt in the model/ directory
```

## Usage

1. Configure user parameters in `src/workout_monitoring.py`:
```python
USER_MASS = 60.0  # Mass of the person in kg
DISPLACEMENT = 0.6  # Vertical distance in meters for a full rep
```

2. Run the workout monitor:
```bash
python src/workout_monitoring.py
```

3. Point the camera at the person exercising or use a video file:
```python
# For video file:
cap = cv2.VideoCapture("path/to/your/video.mp4")

# For webcam:
cap = cv2.VideoCapture(0)
```

## How It Works

1. **Pose Detection**: 
   - Uses YOLO11 pose estimation to detect 17 key body points
   - Tracks specific keypoints for exercise form (e.g., shoulders, elbows, wrists for pull-ups)

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

## Contributing

Contributions are welcome! Some areas for improvement:

- Additional exercise types
- Improved form detection
- Rep quality assessment
- Energy expenditure calculation
- User interface for parameter adjustment
- Support for multiple simultaneous users

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Ultralytics YOLO for the pose estimation model
- OpenCV for image processing capabilities 