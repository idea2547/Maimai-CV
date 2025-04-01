"""
Configuration settings for the MaiMai Trainer application.
"""

import pygame

# Window settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600
WINDOW_TITLE = "MaiMai Trainer"

# Game settings
FPS = 60
CIRCLE_RADIUS = 300
NOTE_SPEED = 7.5
NOTE_SIZE = 30

# Development mode settings
DEV_MODE = {
    "ENABLED": False,  # Toggle for dev mode
    "VIDEO_PATH": "assets/video_example/maivideo_01.mp4",  # Path to test video
    "USE_KEYBOARD": True  # Allow keyboard input for testing
}

# Keyboard mappings for testing
KEY_MAPPINGS = {
    pygame.K_1: 225,  # Bottom left
    pygame.K_2: 270,  # Bottom
    pygame.K_3: 315,  # Bottom right
    pygame.K_4: 180,  # Left
    pygame.K_5: 0,    # Center (not used)
    pygame.K_6: 0,    # Right
    pygame.K_7: 135,  # Top left
    pygame.K_8: 90,   # Top
    pygame.K_9: 45    # Top right
}

# Note settings
NOTE_SETTINGS = {
    "MIN_MOTION_AREA": 200,  # Minimum area to trigger note generation
    "COOLDOWN": 10,         # Frames between note generation
    "ANGLE_TOLERANCE": 45,  # Degrees of tolerance for hit detection
    "SLIDE_THRESHOLD": 30   # Minimum distance for slide detection
}

# Timing windows (in milliseconds)
TIMING_WINDOWS = {
    "PERFECT": 50,
    "GREAT": 100,
    "GOOD": 150,
    "BAD": 200
}

# Colors
COLORS = {
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "YELLOW": (255, 255, 0),
    "PURPLE": (255, 0, 255),
    "CYAN": (0, 255, 255),
    "GRAY": (128, 128, 128)  # Added gray color
}

# MediaPipe settings
MEDIAPIPE_SETTINGS = {
    "MAX_NUM_HANDS": 2,
    "MIN_DETECTION_CONFIDENCE": 0.7,
    "MIN_TRACKING_CONFIDENCE": 0.5
}

# Webcam settings
WEBCAM_SETTINGS = {
    "DEVICE_ID": 0,
    "WIDTH": 640,
    "HEIGHT": 480,
    "FPS": 30
} 