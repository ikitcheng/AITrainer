# keypoints_in_box.py
import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from src.ai_gym import AIGym

# Load model once at module level for efficiency
root = Path(__file__).parent.parent
MODEL_PATH = str(root / "model/yolo11n-pose.pt")
gym = AIGym(model=MODEL_PATH)

def keypoints_in_box(image: np.ndarray, box: tuple, threshold: float = 0.9, confidence:float = 0.6, is_display:bool = False) -> bool:
    """
    Checks if the detected person's keypoints are inside the given box.
    Args:
        image: np.ndarray, input image (BGR)
        box: (x1, y1, x2, y2) in pixel coordinates
        threshold: float, fraction of keypoints that must be inside the box
        confiden
        is_display: bool, Display output image or not (default: False).
    Returns:
        bool: True if enough keypoints are inside the box
    """
    # Run pose detection
    tracks = gym.model.track(source=image, persist=True, classes=gym.CFG["classes"])[0]
    if tracks.boxes.id is None or len(tracks.keypoints.data) == 0:
        return False
    # Use the first detected person
    kpts = tracks.keypoints.data[0]  # shape: (17, 3)
    x1, y1, x2, y2 = box
    inside = 0
    total = 0
    for kp in kpts:
        # xy positions, v confidence
        x, y, v = kp.tolist()
        # print(x,y,v)
        if v > 0.6:  # Only count visible keypoints
            total += 1
            if x1 <= x <= x2 and y1 <= y <= y2:
                inside += 1
    print(f"Total keypoints: {total}")
    print(f"Keypoints inside box: {inside}")

    if total == 0:
        return False
    
    if is_display:
        # Draw keypoints and box on the image
        for kp in kpts:
            x, y, v = kp.tolist()
            if v > 0:
                cv2.circle(image, (int(x), int(y)), 5, (0, 255, 0), -1)
        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.imshow("Keypoints and Box", image)
        cv2.waitKey(0)
    return (inside / total) >= threshold

if __name__ == "__main__":
    # Example usage
    img = cv2.imread("data/test.jpg")
    # Example box (x1, y1, x2, y2)
    box = (100, 100, 900, 600)
    result = keypoints_in_box(img, box, threshold=0.8, is_display=True)
    print("Person in box:", result)