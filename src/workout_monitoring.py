import os
import cv2
from pathlib import Path
import sys
# Add parent directory to path to import workout_monitoring
sys.path.append(str(Path(__file__).parent.parent))
from src.ai_gym import AIGym

def process_video(video_path: str, body_mass: float, exercise_mass: float, exercise_type: str = "pullups",
                   up_angle: float = 120, down_angle: float = 150, displacement: float = 0.6, is_display:bool=False) -> dict:
    """
    Process a workout video and return metrics.
    
    Args:
        video_path: Path to the video file
        body_mass: User's mass in kg
        exercise_mass: Mass being lifted in exercise (in kg)
        exercise_type: Type of exercise (default: "pullups")
        up_angle: The angle (in degrees) at which the rep is in the 'up' phase.
        down_angle: The angle (in degrees) at which the rep is in the 'down' phase.
        displacement: Vertical displacement in meters (default: 0.6)
        is_display: Display output image or not (default: False).
    
    Returns:
        dict: Dictionary containing workout metrics:
            - rep_count: Number of repetitions
            - avg_power: Average power output in Watts
            - max_power: Maximum power output in Watts
    """
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), "Error reading video file"
    w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
    print("Original resolution:", w, h)
    max_resolution = (640, 480)
    if h > w:
        max_resolution = (480, 640)
        
    scale = min(max_resolution[0] / w, max_resolution[1] / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    print("New resolution:", new_w, new_h)

    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(video_path), 'processed')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create output video writer
    output_path = os.path.join(output_dir, f"processed_{os.path.basename(video_path)}")
    video_writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (new_w, new_h))

    # Initialize AIGym
    root = Path(__file__).parent.parent
    gym = AIGym(
        show=True,
        kpts=[5, 7, 9],  # Left shoulder, left elbow, left wrist
        lw=2,
        up_angle=up_angle,
        down_angle=down_angle,
        pose_type=exercise_type,
        model=f"{str(root)}/model/yolo11n-pose.pt",
        exercise_mass=exercise_mass,
        displacement=displacement,
        fps=fps
    )

    rep_count = 0
    avg_power = 0
    max_power = 0

    while cap.isOpened():
        success, im0 = cap.read()
        if not success:
            break
        
        # resize video to 480p
        im0 = cv2.resize(im0, (new_w, new_h))

        # Process frame with AIGym to detect pose and calculate power
        im0 = gym.monitor(im0, is_display)
        video_writer.write(im0)

        # Update metrics if available        
        if hasattr(gym, 'count') and len(gym.count) > 0:
            rep_count = gym.count[0]
        
        if hasattr(gym, 'avg_power') and len(gym.avg_power) > 0:
            avg_power = gym.avg_power[0]
        
        if hasattr(gym, 'max_power') and len(gym.max_power) > 0:
            max_power = gym.max_power[0]

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    video_writer.release()
    cap.release()

    return {
        'rep_count': rep_count,
        'avg_power': avg_power,
        'max_power': max_power,
        'avg_power_per_kg': avg_power / body_mass if body_mass > 0 else 0,
        'max_power_per_kg': max_power / body_mass if body_mass > 0 else 0,
        'processed_video_path': output_path
    }

if __name__ == "__main__":
    # Example usage
    root = Path(__file__).parent.parent
    video_path = str(root / "data/pullups.mp4")
    body_mass = 63.0  # kg
    exercise_mass = 63.0 # kg
    metrics = process_video(video_path, body_mass=body_mass, exercise_mass=exercise_mass, exercise_type='pullups', is_display=False)
    print(f"Processed video metrics:")
    print(f"Reps: {metrics['rep_count']}")
    print(f"Average Power: {metrics['avg_power']:.1f} W")
    print(f"Maximum Power: {metrics['max_power']:.1f} W")
    print(f"Average Power per kg: {metrics['avg_power_per_kg']:.1f} W/kg")
    print(f"Maximum Power per kg: {metrics['max_power_per_kg']:.1f} W/kg")