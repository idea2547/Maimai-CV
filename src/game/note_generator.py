"""
Note generator for converting motion detection to game notes.
"""

import math
import random
from utils.config import WEBCAM_SETTINGS

class NoteGenerator:
    def __init__(self):
        """Initialize the note generator."""
        self.last_note_time = 0
        self.note_cooldown = 500  # ms
        self.center_x = WEBCAM_SETTINGS["WIDTH"] // 2
        self.center_y = WEBCAM_SETTINGS["HEIGHT"] // 2
        
        # Map region names to angles
        self.region_angles = {
            'TOP': 90,
            'TOP_RIGHT': 45,
            'RIGHT': 0,
            'BOTTOM_RIGHT': 315,
            'BOTTOM': 270,
            'BOTTOM_LEFT': 225,
            'LEFT': 180,
            'TOP_LEFT': 135
        }

    def reset(self):
        """Reset the note generator state."""
        self.last_note_time = 0

    def motion_to_notes(self, motion_regions):
        """Convert motion regions to game notes."""
        if not motion_regions:
            return []

        notes = []
        for center, region_name in motion_regions:
            if isinstance(center, (tuple, list)) and len(center) == 2:
                x, y = center
                
                # Use the predefined angle for the region
                if region_name in self.region_angles:
                    angle = self.region_angles[region_name]
                else:
                    # Fallback to calculating angle if region not found
                    dx = x - self.center_x
                    dy = y - self.center_y
                    angle = math.degrees(math.atan2(dy, dx))
                    if angle < 0:
                        angle += 360
                
                # Determine note type based on motion characteristics
                note_type = "TAP"  # Default to tap notes for now
                notes.append((note_type, angle))

        return notes

    def generate_random_note(self):
        """Generate a random note for testing."""
        note_type = random.choice(["TAP", "SLIDE"])
        angle = random.randint(0, 359)
        return note_type, angle 