"""
Hand tracking system using MediaPipe for maimai machine tracking.
"""

import cv2
import mediapipe as mp
import numpy as np
from utils.config import MEDIAPIPE_SETTINGS, WEBCAM_SETTINGS
from utils.coordinate_mapper import CoordinateMapper

class HandTracker:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=2,  # Track both hands for slides
            min_detection_confidence=MEDIAPIPE_SETTINGS["MIN_DETECTION_CONFIDENCE"],
            min_tracking_confidence=MEDIAPIPE_SETTINGS["MIN_TRACKING_CONFIDENCE"]
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_SETTINGS["WIDTH"])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_SETTINGS["HEIGHT"])
        self.cap.set(cv2.CAP_PROP_FPS, WEBCAM_SETTINGS["FPS"])
        
        # Initialize coordinate mapper
        self.coordinate_mapper = CoordinateMapper()
        
        # Track finger positions for gesture detection
        self.prev_positions = {}  # Track multiple fingers
        self.gesture_history = []  # Store recent gestures
        self.slide_threshold = 30  # Minimum pixels for slide detection
        self.tap_threshold = 0.1   # Z-axis threshold for tap detection
        
        # Machine border detection
        self.border_detector = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16)
        self.machine_circle = None

    def detect_machine_border(self, frame):
        """Detect the maimai machine's circular border."""
        # Apply background subtraction
        fg_mask = self.border_detector.apply(frame)
        
        # Apply threshold
        _, thresh = cv2.threshold(fg_mask, 244, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest circular contour
        max_circle = None
        max_radius = 0
        
        for contour in contours:
            # Check if contour is roughly circular
            perimeter = cv2.arcLength(contour, True)
            area = cv2.contourArea(contour)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            if circularity > 0.8:  # Threshold for circularity
                (x, y), radius = cv2.minEnclosingCircle(contour)
                if radius > max_radius:
                    max_radius = radius
                    max_circle = ((int(x), int(y)), int(radius))
        
        if max_circle is not None:
            self.machine_circle = max_circle
        
        return self.machine_circle

    def get_frame(self):
        """Get a frame from the webcam."""
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None

    def detect_gesture(self, finger_pos, finger_id):
        """Detect tap or slide gestures."""
        if finger_id not in self.prev_positions:
            self.prev_positions[finger_id] = finger_pos
            return None
            
        prev_pos = self.prev_positions[finger_id]
        
        # Calculate movement
        dx = finger_pos[0] - prev_pos[0]
        dy = finger_pos[1] - prev_pos[1]
        dz = finger_pos[2] - prev_pos[2]
        
        # Update previous position
        self.prev_positions[finger_id] = finger_pos
        
        # Detect gestures
        movement = np.sqrt(dx*dx + dy*dy)
        if movement > self.slide_threshold:
            # Calculate angle for slide direction
            angle = np.degrees(np.arctan2(dy, dx))
            return ("SLIDE", angle)
        elif abs(dz) > self.tap_threshold:
            return ("TAP", None)
            
        return None

    def get_finger_positions(self, results):
        """Get positions of all tracked fingers."""
        if not results or not results.multi_hand_landmarks:
            return {}
            
        finger_positions = {}
        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # Track index finger and thumb for each hand
            for finger_idx in [4, 8]:  # 4 = thumb tip, 8 = index finger tip
                finger = hand_landmarks.landmark[finger_idx]
                
                # Convert normalized coordinates to screen coordinates
                x = int(finger.x * WEBCAM_SETTINGS["WIDTH"])
                y = int(finger.y * WEBCAM_SETTINGS["HEIGHT"])
                z = finger.z
                
                finger_id = f"hand{hand_idx}_finger{finger_idx}"
                finger_positions[finger_id] = (x, y, z)
                
        return finger_positions

    def release(self):
        """Release the webcam."""
        self.cap.release()
        cv2.destroyAllWindows() 