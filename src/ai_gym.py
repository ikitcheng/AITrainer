# Ultralytics YOLO 🚀, AGPL-3.0 license

from ultralytics.solutions.solutions import BaseSolution
from ultralytics.utils.plotting import Annotator
import numpy as np
import cv2


class AIGym(BaseSolution):
    """
    A class to manage gym steps of people in a real-time video stream based on their poses.

    This class extends BaseSolution to monitor workouts using YOLO pose estimation models. It tracks and counts
    repetitions of exercises based on predefined angle thresholds for up and down positions.

    Attributes:
        count (List[int]): Repetition counts for each detected person.
        angle (List[float]): Current angle of the tracked body part for each person.
        stage (List[str]): Current exercise stage ('up', 'down', or '-') for each person.
        initial_stage (str | None): Initial stage of the exercise.
        up_angle (float): Angle threshold for considering the 'up' position of an exercise.
        down_angle (float): Angle threshold for considering the 'down' position of an exercise.
        kpts (List[int]): Indices of keypoints used for angle calculation.
        lw (int): Line width for drawing annotations.
        annotator (Annotator): Object for drawing annotations on the image.
        start_frames (List[int]): Frame number when movement starts.
        start_positions (List[float]): Starting Y position.
        power_outputs (List[float]): Power output for each rep.
        rep_durations (List[List[float]]): List of rep durations.
        exercise_mass (float): User mass in kg.
        displacement (float): Rep displacement in meters.
        fps (float): Video FPS.
        frame_count (int): Current frame number.

    Methods:
        calculate_power: Calculates power output based on exercise mass, distance, and time.
        monitor: Processes a frame to detect poses, calculate angles, and count repetitions.

    Examples:
        >>> gym = AIGym(model="yolov8n-pose.pt")
        >>> image = cv2.imread("gym_scene.jpg")
        >>> processed_image = gym.monitor(image)
        >>> cv2.imshow("Processed Image", processed_image)
        >>> cv2.waitKey(0)
    """

    def __init__(self, **kwargs):
        """Initializes AIGym for workout monitoring using pose estimation and predefined angles."""
        # Check if the model name ends with '-pose'
        if "model" in kwargs and "-pose" not in kwargs["model"]:
            kwargs["model"] = "yolo11n-pose.pt"
        elif "model" not in kwargs:
            kwargs["model"] = "yolo11n-pose.pt"

        super().__init__(**kwargs)
        self.count = []  
        self.angle = [] 
        self.stage = [] 
        
        # Add power calculation attributes
        self.start_frames = []  # Frame number when movement starts
        self.start_positions = []  # Starting Y position
        self.power_outputs = []  # Power output for each rep
        self.avg_power = []  # Average power output
        self.max_power = []  # Maximum power output
        self.rep_durations = []  # List of rep durations
        self.exercise_mass = kwargs.get('exercise_mass', 70.0)  # Exercise mass in kg
        self.displacement = kwargs.get('displacement', 0.6)  # Rep displacement in meters
        self.fps = kwargs.get('fps', 30.0)  # Video FPS
        self.frame_count = 0  # Current frame number

        # Extract details from CFG single time for usage later
        self.initial_stage = None
        self.up_angle = float(self.CFG["up_angle"])  # Pose up predefined angle to consider up pose
        self.down_angle = float(self.CFG["down_angle"])  # Pose down predefined angle to consider down pose
        self.kpts = self.CFG["kpts"]  # User selected kpts of workouts
        self.lw = self.CFG["line_width"]  # Store line_width for usage
        if "pose_type" in kwargs:
            self.pose_type = kwargs["pose_type"]

    def calculate_power(self, vertical_distance: float, time_taken: float):
        """Calculate power output based on exercise mass, distance, and time."""
        if time_taken <= 0:
            return 0
        g = 9.81  # m/s²
        work = self.exercise_mass * g * vertical_distance
        power = work / time_taken
        return power

    def track_pullups(self, ind:int, kpts:list):
        # Get shoulder position (kpts[0] should be shoulder joint)
        shoulder_y = float(kpts[0][1])

        if self.angle[ind] > self.down_angle and self.stage[ind] != "down":
            # Starting position detected
            self.start_frames[ind] = self.frame_count
            self.start_positions[ind] = shoulder_y
            self.stage[ind] = "down"
        elif self.angle[ind] < self.up_angle:
            if self.stage[ind] == "down":
                # Completed rep
                if self.start_frames[ind] > 0:
                    # Calculate duration in seconds using frame count
                    frames_elapsed = self.frame_count - self.start_frames[ind]
                    duration = frames_elapsed / self.fps
                    
                    # Calculate and store power
                    power = self.calculate_power(self.displacement, duration)
                    if ind < len(self.power_outputs):
                        self.power_outputs[ind].append(power)
                    
                    # Store duration
                    if ind < len(self.rep_durations):
                        self.rep_durations[ind].append(duration)
                
                self.count[ind] += 1
            self.stage[ind] = "up"

    def track_dips(self, ind:int, kpts:list):
        pass

    def track_pushups(self, ind:int, kpts:list):
        if self.angle[ind] < self.down_angle:
            if self.stage[ind] == "up":
                self.count[ind] += 1
            self.stage[ind] = "down"
        elif self.angle[ind] > self.up_angle:
            self.stage[ind] = "up"

    def track_squats(self, ind:int, kpts:list):
        pass

    def track_situps(self, ind:int, kpts:list):
        pass

    def monitor(self, im0, is_display:bool=False):
        """
        Monitors workouts using Ultralytics YOLO Pose Model.

        This function processes an input image to track and analyze human poses for workout monitoring. It uses
        the YOLO Pose model to detect keypoints, estimate angles, and count repetitions based on predefined
        angle thresholds.

        Args:
            im0 (ndarray): Input image for processing.
            is_dispaly (bool): Display the output

        Returns:
            (ndarray): Processed image with annotations for workout monitoring.

        Examples:
            >>> gym = AIGym()
            >>> image = cv2.imread("workout.jpg")
            >>> processed_image = gym.monitor(image)
        """
        # Increment frame counter
        self.frame_count += 1
        
        # Extract tracks
        tracks = self.model.track(source=im0, persist=True, classes=self.CFG["classes"])[0]

        if tracks.boxes.id is not None:
            # Extract and check keypoints
            print("Number of tracks:", len(tracks), "Number of rep counters:", len(self.count))
            if len(tracks) > len(self.count): # 1st frame len(self.count) is 0
                new_human = len(tracks) - len(self.count)
                self.angle += [0] * new_human
                self.count += [0] * new_human
                self.stage += ["-"] * new_human
                self.start_frames += [0] * new_human
                self.start_positions += [0] * new_human
                self.rep_durations += [[]] * new_human
                self.power_outputs += [[]] * new_human
                self.avg_power += [0] * new_human
                self.max_power += [0] * new_human

            # Initialize annotator
            self.annotator = Annotator(im0, line_width=self.lw)

            # Enumerate over 17 keypoints, each with (x,y,visible) values
            for ind, k in enumerate(reversed(tracks.keypoints.data)): # (nPerson, 17, 3)
                # Get keypoints and estimate the angle
                kpts = [k[int(self.kpts[i])].cpu() for i in range(len(self.kpts))]
                self.angle[ind] = self.annotator.estimate_pose_angle(*kpts)
                
                # Track movement for power calculation
                if self.pose_type == 'pullups':
                    self.track_pullups(ind, kpts)

                elif self.pose_type == 'pushups':
                    self.track_pushups(ind, kpts)

                # Draw keypoints and skeleton
                draw_kpts = self.kpts # [5,7,9,11,12,13,14,15,16]
                im0 = self.annotator.draw_specific_points(k, draw_kpts, radius=self.lw)

                # Display comprehensive information
                if ind < len(self.power_outputs) and len(self.power_outputs[ind]) > 0:
                    # Calculate average and max power if we have multiple reps
                    self.avg_power[ind] = 0
                    self.max_power[ind] = 0
                    if ind < len(self.rep_durations) and len(self.rep_durations[ind]) > 0:
                        self.avg_power[ind] = np.mean(self.power_outputs[ind])
                        self.max_power[ind] = np.max(self.power_outputs[ind])
                    
                    # Get image dimensions for positioning
                    img_h, img_w = im0.shape[:2]
                    
                    # Format text for display
                    info_text = [
                        f"Reps: {self.count[ind]}", # Reps
                        f"m: {self.exercise_mass:.0f} kg",  # Mass in kg
                        f"dh: {self.displacement:.2f} m",  # Distance
                        f"t: {self.rep_durations[ind][-1]:.2f} s" if self.rep_durations[ind] else "",  # Time in seconds
                        f"Rep Power: {self.power_outputs[ind][-1]:.0f} W",  # Result
                        f"Max Power: {self.max_power[ind]:.0f} W" if self.max_power[ind] > 0 else "",  # Max power in W
                        f"Avg Power: {self.avg_power[ind]:.0f} W" if self.avg_power[ind] > 0 else "", # Average power in W
                    ]
                    
                    # Position text at bottom left with smaller font
                    font_scale = 0.7  # Smaller font size
                    font_thickness = 1  # Thinner text
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    padding = 10  # Padding from image edges
                    
                    # Calculate starting y position from bottom
                    y_offset = img_h - (len(info_text) * 25 + padding)  # 25 pixels between lines
                    x_offset = padding
                    
                    for text in info_text:
                        if text:  # Only display non-empty text
                            cv2.putText(im0, text, (x_offset, y_offset), 
                                      font, font_scale, (0, 255, 0), font_thickness)
                            y_offset += 25  # Smaller line spacing

                # Display angle, count, and stage text
                # self.annotator.plot_angle_and_count_and_stage(
                #     angle_text=self.angle[ind],  # angle text for display
                #     count_text=self.count[ind],  # count text for workouts
                #     stage_text=self.stage[ind],  # stage position text
                #     center_kpt=k[int(self.kpts[1])],  # center keypoint for display
                # )

        if is_display:
            self.display_output(im0)  # Display output image, if environment support display
        return im0  # return an image
