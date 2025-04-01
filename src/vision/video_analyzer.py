"""
Video analyzer for detecting maimai machine buttons.
"""

import cv2
import numpy as np
import json
import os
from utils.config import WEBCAM_SETTINGS
import math

class VideoAnalyzer:
    def __init__(self):
        """Initialize the video analyzer."""
        # Screen detection parameters
        self.min_radius = int(min(WEBCAM_SETTINGS["WIDTH"], WEBCAM_SETTINGS["HEIGHT"]) * 0.3)
        self.max_radius = int(min(WEBCAM_SETTINGS["WIDTH"], WEBCAM_SETTINGS["HEIGHT"]) * 0.45)
        
        # Visualization parameters
        self.circle_thickness = 1  # Reduced from default (usually 2 or 3)
        self.line_thickness = 1    # Reduced from default
        self.dot_radius = 3        # Reduced from default (usually 5 or more)
        
        # Button detection parameters
        self.button_min_area = 100
        self.button_max_area = 1000
        self.button_color_lower = np.array([20, 100, 100])  # Yellow-ish color in HSV
        self.button_color_upper = np.array([40, 255, 255])
        
        # Store detected button positions
        self.button_positions = {}  # Changed from list to dictionary
        
        # Screen parameters
        self.screen_center = None
        self.screen_radius = None
        
        # Manual mapping parameters
        self.mapping_mode = False
        self.manual_buttons = {
            'TOP': None,
            'TOP_RIGHT': None,
            'RIGHT': None,
            'BOTTOM_RIGHT': None,
            'BOTTOM': None,
            'BOTTOM_LEFT': None,
            'LEFT': None,
            'TOP_LEFT': None
        }
        self.current_mapping_button = None
        self.mapping_file = "button_mapping.json"
        self.load_button_mapping()

    def start_mapping_mode(self):
        """Start manual button mapping mode."""
        self.mapping_mode = True
        self.current_mapping_button = list(self.manual_buttons.keys())[0]
        print(f"Starting mapping mode. Click to set position for {self.current_mapping_button}")

    def stop_mapping_mode(self):
        """Stop manual button mapping mode and save mappings."""
        self.mapping_mode = False
        self.current_mapping_button = None
        self.save_button_mapping()
        print("Mapping mode stopped and positions saved.")

    def handle_mapping_click(self, x, y):
        """Handle mouse click for manual button mapping."""
        if not self.mapping_mode or self.current_mapping_button is None:
            return False

        # Store the clicked position for current button
        self.manual_buttons[self.current_mapping_button] = (x, y)
        
        # Move to next button
        button_keys = list(self.manual_buttons.keys())
        current_index = button_keys.index(self.current_mapping_button)
        
        if current_index < len(button_keys) - 1:
            self.current_mapping_button = button_keys[current_index + 1]
            print(f"Set position for {button_keys[current_index]}. Now click position for {self.current_mapping_button}")
        else:
            print("All buttons mapped. Stopping mapping mode.")
            self.stop_mapping_mode()
        
        return True

    def save_button_mapping(self):
        """Save button mapping to file."""
        mapping_data = {
            'buttons': {k: {'x': v[0], 'y': v[1]} if v else None 
                       for k, v in self.manual_buttons.items()},
            'screen': {
                'center': {'x': self.screen_center[0], 'y': self.screen_center[1]} if self.screen_center else None,
                'radius': self.screen_radius
            } if self.screen_center and self.screen_radius else None
        }
        
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(mapping_data, f, indent=4)
            print(f"Button mapping saved to {self.mapping_file}")
        except Exception as e:
            print(f"Error saving button mapping: {e}")

    def load_button_mapping(self):
        """Load button mapping from file."""
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r') as f:
                    mapping_data = json.load(f)
                
                # Load button positions
                for button, pos in mapping_data['buttons'].items():
                    if pos:
                        self.manual_buttons[button] = (pos['x'], pos['y'])
                
                # Load screen parameters
                if mapping_data['screen']:
                    self.screen_center = (mapping_data['screen']['center']['x'],
                                        mapping_data['screen']['center']['y'])
                    self.screen_radius = mapping_data['screen']['radius']
                
                print(f"Button mapping loaded from {self.mapping_file}")
                return True
        except Exception as e:
            print(f"Error loading button mapping: {e}")
        return False

    def detect_screen(self, frame):
        """Detect the maimai screen circle."""
        if frame is None:
            return False
            
        # Try manual mapping first
        if all(v is not None for v in self.manual_buttons.values()):
            # If we have manual mapping, calculate screen parameters from button positions
            x_coords = [x for x, y in self.manual_buttons.values()]
            y_coords = [y for x, y in self.manual_buttons.values()]
            center_x = sum(x_coords) / len(x_coords)
            center_y = sum(y_coords) / len(y_coords)
            self.screen_center = (int(center_x), int(center_y))
            
            # Calculate radius as average distance from center to buttons
            distances = [np.sqrt((x - center_x)**2 + (y - center_y)**2) 
                        for x, y in self.manual_buttons.values()]
            self.screen_radius = int(sum(distances) / len(distances))
            return True
            
        # Original automatic detection if no manual mapping
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Sort contours by area in descending order
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            
            # Try each contour until we find a good circular one
            for contour in contours:
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                
                # Check if contour is circular enough and within size limits
                if (circularity > 0.7 and 
                    self.min_radius < np.sqrt(area/np.pi) < self.max_radius):
                    (x, y), radius = cv2.minEnclosingCircle(contour)
                    self.screen_center = (int(x), int(y))
                    self.screen_radius = int(radius)
                    return True
        return False

    def detect_buttons(self, frame):
        """Detect buttons around the edge of the screen."""
        if not self.screen_center or not self.screen_radius:
            return
            
        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply multiple thresholding methods
        # Method 1: Simple threshold
        _, thresh1 = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Method 2: Adaptive threshold
        thresh2 = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Combine both thresholded images
        thresh = cv2.bitwise_or(thresh1, thresh2)
        
        # Apply morphological operations to clean up noise
        kernel = np.ones((3,3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours in the thresholded image
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Clear previous button positions
        self.button_positions.clear()
        
        # Filter contours by area and distance from screen center
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if self.button_min_area < area < self.button_max_area:
                # Get contour center
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # Calculate distance from screen center
                    dx = cx - self.screen_center[0]
                    dy = cy - self.screen_center[1]
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    # If button is near the edge of the screen
                    if 0.7 * self.screen_radius < distance < 0.9 * self.screen_radius:
                        # Calculate angle from center
                        angle = math.degrees(math.atan2(dy, dx)) % 360
                        
                        # Store button position with angle-based name
                        button_name = f"BUTTON_{i}"
                        self.button_positions[button_name] = (cx, cy)

    def analyze_frame(self, frame):
        """Analyze a single frame to detect screen and buttons."""
        if frame is None:
            return None, None
            
        # Try to detect screen first
        if not self.detect_screen(frame):
            # If screen detection fails, try to use manual mapping
            if not all(v is not None for v in self.manual_buttons.values()):
                return frame, None
        
        # If we have screen parameters, detect buttons
        if self.screen_center and self.screen_radius:
            self.detect_buttons(frame)
        
        # Create output frame for visualization
        output_frame = frame.copy()
        
        # Draw screen circle if detected
        if self.screen_center and self.screen_radius:
            cv2.circle(output_frame, self.screen_center, self.screen_radius, (0, 255, 0), 2)
            # Draw center point
            cv2.circle(output_frame, self.screen_center, 5, (0, 255, 0), -1)
        
        # Draw mapped button positions
        for button_name, pos in self.button_positions.items():
            cv2.circle(output_frame, pos, 10, (0, 255, 255), -1)
            cv2.putText(output_frame, button_name, (pos[0] + 15, pos[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            # Draw line from center to button
            if self.screen_center:
                cv2.line(output_frame, self.screen_center, pos, (0, 255, 255), 1)
        
        # Return results
        results = {
            'screen_center': self.screen_center,
            'screen_radius': self.screen_radius,
            'button_positions': self.button_positions
        }
        
        return output_frame, results 