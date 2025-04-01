"""
Development mode handler for testing without webcam.
"""

import cv2
import pygame
import numpy as np
import os
import time
import math
from utils.config import DEV_MODE, KEY_MAPPINGS, WEBCAM_SETTINGS, FPS
from vision.video_analyzer import VideoAnalyzer
from game.note_generator import NoteGenerator

class DevModeHandler:
    def __init__(self):
        """Initialize the development mode handler."""
        self.video = None
        self.video_path = DEV_MODE.get("VIDEO_PATH", "assets/video_example/maivideo_01.mp4")
        self.frame_count = 0
        self.generated_notes = []
        self.last_button_states = {}  # Track previous button states
        self.note_cooldown = {}  # Cooldown timer for each button
        self.cooldown_time = 500  # Milliseconds
        self.last_time = time.time() * 1000
        self.video_analyzer = VideoAnalyzer()
        self.note_generator = NoteGenerator()
        self.analysis_results = None
        self.current_gesture = None
        self.current_position = None
        self.cached_surface = None
        self.center = (WEBCAM_SETTINGS["WIDTH"]//2, WEBCAM_SETTINGS["HEIGHT"]//2)
        
        # Frame timing control
        self.last_frame_time = time.time()
        self.frame_interval = 1.0 / 30  # Target 30 FPS for gameplay
        self.cached_frame = None
        
        # Hand motion detection
        self.prev_frame = None
        self.motion_threshold = 30
        self.min_motion_area = 100
        self.max_motion_area = 1000
        
        # Video playback control
        self.video_speed = 1.0
        
        # Initialize video if dev mode is enabled
        if DEV_MODE["ENABLED"] and self.video_path and os.path.exists(self.video_path):
            self.video = cv2.VideoCapture(self.video_path)
            if not self.video.isOpened():
                print(f"Error: Could not open video file: {self.video_path}")

    def set_video_speed(self, speed):
        """Set the playback speed of the video."""
        self.video_speed = speed
        # Adjust frame interval based on speed
        self.frame_interval = (1.0 / 30) / speed  # Adjust 30 FPS base interval

    def get_frame(self):
        """Get the next frame from the video source."""
        if not self.video or not self.video.isOpened():
            return None

        current_time = time.time()
        if current_time - self.last_frame_time < self.frame_interval:
            return self.cached_frame

        ret, frame = self.video.read()
        if not ret:
            # Reset video to beginning when it ends
            self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video.read()
            if not ret:
                return None

        self.last_frame_time = current_time
        self.cached_frame = frame
        return frame

    def get_analysis_results(self):
        """Get the latest analysis results."""
        return self.analysis_results

    def get_generated_notes(self):
        """Get and clear the list of generated notes."""
        notes = self.generated_notes.copy()
        self.generated_notes.clear()
        return notes

    def detect_hand_motion(self, frame):
        """Detect hand motion in the frame."""
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return []

        # Convert current frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate absolute difference between frames
        diff = cv2.absdiff(self.prev_frame, gray)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(diff, self.motion_threshold, 255, cv2.THRESH_BINARY)
        
        # Apply morphological operations to reduce noise
        kernel = np.ones((5,5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours of motion regions
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and process motion regions
        motion_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_motion_area < area < self.max_motion_area:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # Calculate angle from center
                    angle = math.degrees(math.atan2(cy - self.center[1], 
                                                  cx - self.center[0])) % 360
                    
                    motion_regions.append(("TAP", angle))
        
        # Update previous frame
        self.prev_frame = gray
        
        return motion_regions

    def handle_keyboard_input(self, events):
        """Handle keyboard and mouse input for gesture simulation."""
        current_time = time.time() * 1000
        
        # Get current frame and detect motion
        frame = self.get_frame()
        if frame is not None:
            # Detect hand motion
            motion_hits = self.detect_hand_motion(frame)
            for hit_type, angle in motion_hits:
                # Check cooldown for this angle region
                angle_key = f"motion_{int(angle/45)*45}"  # Group angles into 45-degree sectors
                if (angle_key not in self.note_cooldown or 
                    current_time - self.note_cooldown.get(angle_key, 0) > self.cooldown_time):
                    
                    # Generate a note
                    self.generated_notes.append((hit_type, angle))
                    # Update cooldown
                    self.note_cooldown[angle_key] = current_time
            
            # Process frame with video analyzer for visualization
            analyzed_frame, results = self.video_analyzer.analyze_frame(frame)
        
        # Handle keyboard input for manual testing
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_MAPPINGS:
                    angle = KEY_MAPPINGS[event.key]
                    return "TAP", (
                        self.center[0] + int(np.cos(np.radians(angle)) * CIRCLE_RADIUS),
                        self.center[1] + int(np.sin(np.radians(angle)) * CIRCLE_RADIUS)
                    )
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    return "TAP", event.pos
        
        return None, None

    def toggle_dev_mode(self):
        """Toggle development mode on/off."""
        if not DEV_MODE["ENABLED"]:
            # Try to open the video file when enabling dev mode
            if self.video_path and os.path.exists(self.video_path):
                if self.video is None or not self.video.isOpened():
                    self.video = cv2.VideoCapture(self.video_path)
                    if not self.video.isOpened():
                        print(f"Error: Could not open video file: {self.video_path}")
                        return False
                    
                    # Set video properties for controlled playback
                    self.video.set(cv2.CAP_PROP_FPS, 30)  # Force 30 FPS
            else:
                print("Error: No video file specified for dev mode")
                return False
        else:
            # Release video resources when disabling dev mode
            if self.video:
                self.video.release()
                self.video = None
                self.cached_frame = None
        
        DEV_MODE["ENABLED"] = not DEV_MODE["ENABLED"]
        return True

    def release(self):
        """Release resources."""
        if self.video:
            self.video.release()
        self.video = None
        self.cached_surface = None
        self.frame_count = 0
        self.note_generator.reset() 