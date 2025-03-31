import os
import cv2
from pathlib import Path
from ai_gym import AIGym

def main(path_to_video:str):
    cap = cv2.VideoCapture(path_to_video)
    assert cap.isOpened(), "Error reading video file"
    w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
    os.makedirs('./output', exist_ok=True)
    video_writer = cv2.VideoWriter("./output/workouts.avi", cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    gym = AIGym(
        show=True,
        kpts=[5, 7, 9],  # Left shoulder, left elbow, left wrist
        lw=2,
        up_angle=120,
        down_angle=145,
        pose_type="pullups",
        model=f"{str(root)}/model/yolo11n-pose.pt",
        user_mass=USER_MASS,
        displacement=DISPLACEMENT,  # rep displacement estimate
        fps=fps  # Pass video FPS for accurate timing
    )

    while cap.isOpened():
        success, im0 = cap.read()
        if not success:
            print("Video frame is empty or video processing has been successfully completed.")
            break

        # Process frame with AIGym to detect pose and calculate power
        im0 = gym.monitor(im0)

        video_writer.write(im0)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    video_writer.release()

if __name__ == "__main__":
    # Constants and parameters that can be adjusted
    USER_MASS = 63.0  # Mass of the person in kg (can be adjusted)
    USER_HEIGHT = 1.75  # Height of the person in meters (can be adjusted)
    DISPLACEMENT = 0.6  # Estimated vertical distance in meters for a full pull-up (https://www.janereactionfitness.com/blog/physics-of-fitness-fridays-the-pull-up)
    root = Path(__file__).parent.parent
    PATH_TO_VIDEO = root / "data/pullups.mp4"
    main(PATH_TO_VIDEO)