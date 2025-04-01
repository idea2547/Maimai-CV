"""
Coordinate mapping utility for converting webcam coordinates to screen coordinates.
"""

import numpy as np
from utils.config import WEBCAM_SETTINGS, WINDOW_WIDTH, WINDOW_HEIGHT
import cv2

class CoordinateMapper:
    def __init__(self):
        """Initialize the coordinate mapper."""
        self.calibration_points = []
        self.transformation_matrix = None
        
    def add_calibration_point(self, webcam_point, screen_point):
        """Add a calibration point pair."""
        self.calibration_points.append((webcam_point, screen_point))
        
    def calculate_transformation(self):
        """Calculate the transformation matrix from calibration points."""
        if len(self.calibration_points) < 4:
            return False
            
        # Convert points to numpy arrays
        src_points = np.float32([p[0] for p in self.calibration_points])
        dst_points = np.float32([p[1] for p in self.calibration_points])
        
        # Calculate perspective transformation matrix
        self.transformation_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        return True
        
    def map_coordinates(self, webcam_point):
        """Map webcam coordinates to screen coordinates."""
        if self.transformation_matrix is None:
            # If not calibrated, use simple scaling
            x = int(webcam_point[0] * WINDOW_WIDTH / WEBCAM_SETTINGS["WIDTH"])
            y = int(webcam_point[1] * WINDOW_HEIGHT / WEBCAM_SETTINGS["HEIGHT"])
            return (x, y)
            
        # Apply perspective transformation
        point = np.array([[webcam_point[0], webcam_point[1]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point.reshape(-1, 1, 2), self.transformation_matrix)
        return (int(transformed[0][0][0]), int(transformed[0][0][1]))
        
    def is_calibrated(self):
        """Check if the mapper is calibrated."""
        return self.transformation_matrix is not None 