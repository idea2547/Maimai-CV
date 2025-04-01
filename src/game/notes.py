"""
Note management for the MaiMai Trainer.
"""

import pygame
import math
from utils.config import (
    COLORS, 
    CIRCLE_RADIUS, 
    NOTE_SPEED, 
    NOTE_SIZE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT
)
import time

class Note:
    def __init__(self, note_type, angle, radius):
        """Initialize a note."""
        self.type = note_type  # "TAP" or "SLIDE"
        self.angle = angle
        self.radius = radius
        self.creation_time = time.time() * 1000
        self.active = True
        self.hit = False
        self.color = COLORS["YELLOW"] if note_type == "TAP" else COLORS["BLUE"]
        
    def update(self):
        """Update note position."""
        if self.active:
            self.radius -= NOTE_SPEED
            if self.radius < 0:  # Miss threshold
                self.active = False
                
    def draw(self, screen, center):
        """Draw the note."""
        if not self.active:
            return
            
        # Calculate position
        x = center[0] + math.cos(math.radians(self.angle)) * self.radius
        y = center[1] + math.sin(math.radians(self.angle)) * self.radius
        
        if self.type == "TAP":
            # Draw circular note
            pygame.draw.circle(screen, self.color, (int(x), int(y)), NOTE_SIZE)
        else:  # SLIDE
            # Draw arrow-shaped note
            direction = math.radians(self.angle)
            points = [
                (x + math.cos(direction) * NOTE_SIZE,
                 y + math.sin(direction) * NOTE_SIZE),
                (x + math.cos(direction + 2.6) * NOTE_SIZE,
                 y + math.sin(direction + 2.6) * NOTE_SIZE),
                (x + math.cos(direction - 2.6) * NOTE_SIZE,
                 y + math.sin(direction - 2.6) * NOTE_SIZE)
            ]
            pygame.draw.polygon(screen, self.color, points)

class NoteManager:
    def __init__(self):
        """Initialize the note manager."""
        self.notes = []
        self.last_spawn_time = time.time() * 1000
        self.spawn_interval = 2000  # 2 seconds between notes
        self.note_speed = 1  # Reduced speed (was 2)
        self.note_size = 20
        
    def add_note(self, note_type, angle):
        """Add a new note at the specified angle."""
        current_time = time.time() * 1000
        
        # Create note at the edge of the play area
        radius = CIRCLE_RADIUS * 1.5  # Reduced starting distance (was 2)
        self.notes.append(Note(note_type, angle, radius))
        
    def update(self):
        """Update all notes."""
        # Update existing notes
        for note in self.notes[:]:  # Create a copy of the list to modify while iterating
            note.update()  # Use Note's update method
            # Remove notes that have moved too far inside
            if note.radius < 0:
                self.notes.remove(note)
    
    def check_hits(self, gestures, positions):
        """Check for note hits."""
        hits = []
        for note in self.notes[:]:  # Create a copy to modify while iterating
            for gesture, pos in zip(gestures, positions):
                # Calculate angle of the hit position
                dx = pos[0] - WINDOW_WIDTH//4  # Center x
                dy = pos[1] - WINDOW_HEIGHT//2  # Center y
                hit_angle = math.degrees(math.atan2(dy, dx))
                if hit_angle < 0:
                    hit_angle += 360
                
                # Check if the hit is within the acceptable range
                angle_diff = abs(hit_angle - note.angle)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                
                # More forgiving hit window for hand movements
                # Increased angle tolerance and wider radius range
                if angle_diff < 60 and CIRCLE_RADIUS * 0.6 < note.radius < CIRCLE_RADIUS * 1.4:
                    hits.append(note)
                    self.notes.remove(note)
                    break
        
        return hits
    
    def draw(self, screen):
        """Draw all notes."""
        center = (WINDOW_WIDTH//4, WINDOW_HEIGHT//2)
        for note in self.notes:
            # Calculate note position
            angle_rad = math.radians(note.angle)
            x = center[0] + int(math.cos(angle_rad) * note.radius)
            y = center[1] + int(math.sin(angle_rad) * note.radius)
            
            # Draw note
            if note.type == "TAP":
                pygame.draw.circle(screen, COLORS["YELLOW"], (x, y), self.note_size)
            elif note.type == "SLIDE":
                pygame.draw.circle(screen, COLORS["BLUE"], (x, y), self.note_size)
            
            # Draw direction indicator
            end_x = x + int(math.cos(angle_rad) * 10)
            end_y = y + int(math.sin(angle_rad) * 10)
            pygame.draw.line(screen, COLORS["WHITE"], (x, y), (end_x, end_y), 2) 