"""
Main entry point for the MaiMai Trainer application.
"""

import pygame
import sys
import time
import cv2
import numpy as np
import math
import random
import mediapipe as mp
from utils.config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    FPS,
    CIRCLE_RADIUS,
    COLORS,
    DEV_MODE,
    WEBCAM_SETTINGS
)
from vision.hand_tracker import HandTracker
from game.notes import NoteManager, Note
from game.scoring import ScoreManager
from utils.dev_mode import DevModeHandler
from vision.video_analyzer import VideoAnalyzer

class MaiMaiTrainer:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        
        # MediaPipe drawing utils and hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Set up the display
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        
        # Set up the clock for controlling frame rate
        self.clock = pygame.time.Clock()
        
        # Initialize components
        self.hand_tracker = HandTracker()
        self.note_manager = NoteManager()
        self.score_manager = ScoreManager()
        self.dev_mode = DevModeHandler()
        self.video_analyzer = VideoAnalyzer()
        
        # Frame processing optimization
        self.last_processed_time = time.time() * 1000
        self.process_interval = 1000 / 60  # Increased to 60 FPS
        self.skip_frames = 2  # Process every 3rd frame for hit detection
        self.frame_counter = 0
        
        # Hit detection optimization
        self.last_hit_time = 0
        self.hit_cooldown = 50  # Minimum time between hits in milliseconds
        self.hit_distance_threshold = 40  # Increased distance threshold for better detection
        self.min_movement_threshold = 10  # Minimum movement required to trigger hit
        self.last_finger_positions = {}  # Store last positions of fingers for motion detection
        self.hit_buffer = {}  # Buffer to track potential hits
        
        # Performance tracking
        self.frame_times = []
        self.max_frame_history = 30
        self.last_fps_update = time.time()
        self.current_fps = 0
        
        # Game state
        self.running = True
        self.start_time = time.time() * 1000  # Convert to milliseconds
        self.calibrating = not DEV_MODE["ENABLED"]  # Skip calibration in dev mode
        self.calibration_points = []
        
        # Hit effect tracking
        self.hit_effects = []  # List of (position, time, type) tuples
        self.hit_effect_duration = 500  # Duration in milliseconds
        
        # Center of the play area
        self.center = (WINDOW_WIDTH//4, WINDOW_HEIGHT//2)  # Left side of window
        
        # Calibration points (corners of the play area)
        self.calibration_targets = [
            (self.center[0] - CIRCLE_RADIUS, self.center[1] - CIRCLE_RADIUS),  # Top-left
            (self.center[0] + CIRCLE_RADIUS, self.center[1] - CIRCLE_RADIUS),  # Top-right
            (self.center[0] + CIRCLE_RADIUS, self.center[1] + CIRCLE_RADIUS),  # Bottom-right
            (self.center[0] - CIRCLE_RADIUS, self.center[1] + CIRCLE_RADIUS)   # Bottom-left
        ]
        
        # UI elements
        self.font = pygame.font.Font(None, 36)
        self.dev_mode_button = pygame.Rect(WINDOW_WIDTH - 150, 10, 140, 40)
        self.mapping_button = pygame.Rect(WINDOW_WIDTH - 150, 60, 140, 40)
        
        # Video display surface
        self.video_surface = pygame.Surface((WEBCAM_SETTINGS["WIDTH"], WEBCAM_SETTINGS["HEIGHT"]))
        self.video_rect = pygame.Rect(
            0,  # Changed from WINDOW_WIDTH - WEBCAM_SETTINGS["WIDTH"] to 0
            (WINDOW_HEIGHT - WEBCAM_SETTINGS["HEIGHT"]) // 2,
            WEBCAM_SETTINGS["WIDTH"],
            WEBCAM_SETTINGS["HEIGHT"]
        )
        
        # Hit visualization
        self.hit_dots = []  # List of (position, time, color) tuples
        self.dot_duration = 500  # Duration in milliseconds
        self.dot_size = 15
        self.last_dot_time = 0  # Track last dot creation time
        self.dot_cooldown = 100  # Minimum time between dots in milliseconds
        
        # Hit statistics tracking
        self.hit_stats = {
            "TOP": 0,
            "TOP_RIGHT": 0,
            "RIGHT": 0,
            "BOTTOM_RIGHT": 0,
            "BOTTOM": 0,
            "BOTTOM_LEFT": 0,
            "LEFT": 0,
            "TOP_LEFT": 0
        }
        self.stats_font = pygame.font.Font(None, 24)
        
        # Video speed control
        self.video_speed = 1.0  # Normal speed
        self.min_speed = 0.25   # Quarter speed
        self.max_speed = 2.0    # Double speed
        self.speed_step = 0.25  # Speed adjustment increment
        
        # Button mapping drag state
        self.is_dragging = False
        self.temp_button_pos = None

    def add_hit_effect(self, position, hit_type="PERFECT"):
        """Add a hit effect at the specified position."""
        current_time = time.time() * 1000
        self.hit_effects.append((position, current_time, hit_type))

    def update_hit_effects(self):
        """Update hit effects and remove expired ones."""
        current_time = time.time() * 1000
        self.hit_effects = [(pos, start_time, hit_type) for pos, start_time, hit_type in self.hit_effects
                          if current_time - start_time < self.hit_effect_duration]

    def draw_hit_effects(self):
        """Draw hit effects on the screen."""
        current_time = time.time() * 1000
        for pos, start_time, hit_type in self.hit_effects:
            # Calculate effect progress (0.0 to 1.0)
            progress = (current_time - start_time) / self.hit_effect_duration
            
            # Scale effect size based on progress
            size = int(40 * (1 - progress))  # Start at 40 pixels and shrink
            
            # Calculate alpha based on progress (fade out)
            alpha = int(255 * (1 - progress))
            
            # Choose color based on hit type
            color = COLORS["GREEN"] if hit_type == "PERFECT" else \
                   COLORS["YELLOW"] if hit_type == "GREAT" else \
                   COLORS["BLUE"] if hit_type == "GOOD" else \
                   COLORS["RED"]
            
            # Create surface for the hit effect
            effect_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(effect_surface, (*color, alpha), (size, size), size)
            
            # Draw the effect centered on the hit position
            self.screen.blit(effect_surface, 
                           (pos[0] - size, pos[1] - size))
            
            # Draw hit text
            if progress < 0.3:  # Only show text briefly
                text = self.font.render(hit_type, True, color)
                text_rect = text.get_rect(center=(pos[0], pos[1] - 40))
                self.screen.blit(text, text_rect)

    def get_hit_section(self, angle):
        """Convert angle to hit section name."""
        # Normalize angle to 0-360 and adjust to match maimai layout
        # In maimai, 0 degrees is at the top (TOP button) and angles increase clockwise
        
        # First rotate the angle so 0 is at the top (subtract 90 degrees)
        adjusted_angle = (angle - 90) % 360
        
        # Define section boundaries for maimai layout (clockwise from top)
        sections = [
            ("TOP", 337.5, 22.5),          # 0 degrees
            ("TOP_RIGHT", 22.5, 67.5),     # 45 degrees
            ("RIGHT", 67.5, 112.5),        # 90 degrees
            ("BOTTOM_RIGHT", 112.5, 157.5), # 135 degrees
            ("BOTTOM", 157.5, 202.5),      # 180 degrees
            ("BOTTOM_LEFT", 202.5, 247.5), # 225 degrees
            ("LEFT", 247.5, 292.5),        # 270 degrees
            ("TOP_LEFT", 292.5, 337.5)     # 315 degrees
        ]
        
        # Find matching section
        for section_name, start_angle, end_angle in sections:
            if start_angle <= adjusted_angle or adjusted_angle < end_angle:
                if section_name == "TOP" and (adjusted_angle >= 337.5 or adjusted_angle < 22.5):
                    return section_name
            elif start_angle <= adjusted_angle < end_angle:
                return section_name
        
        return "TOP"  # Default to TOP if no match (shouldn't happen)

    def add_hit_dot(self, angle):
        """Add a hit dot at the specified angle on the play circle."""
        current_time = time.time() * 1000
        
        # Check cooldown
        if current_time - self.last_dot_time < self.dot_cooldown:
            return
            
        # Calculate position on the play circle
        angle_rad = math.radians(angle)
        x = self.center[0] + int(math.cos(angle_rad) * CIRCLE_RADIUS)
        y = self.center[1] + int(math.sin(angle_rad) * CIRCLE_RADIUS)
        
        # Determine which section was hit
        section = self.get_hit_section(angle)
        
        # Update hit stats
        if section in self.hit_stats:
            self.hit_stats[section] = self.hit_stats[section] + 1
        
        # Use a fixed bright color
        color = (0, 255, 255)  # Cyan color
        self.hit_dots.append(((x, y), current_time, color))
        self.last_dot_time = current_time

    def update_hit_dots(self):
        """Update hit dots and remove expired ones."""
        current_time = time.time() * 1000
        self.hit_dots = [(pos, start_time, color) for pos, start_time, color in self.hit_dots
                        if current_time - start_time < self.dot_duration]

    def draw_hit_dots(self):
        """Draw all active hit dots."""
        current_time = time.time() * 1000
        for pos, start_time, color in self.hit_dots:
            # Calculate fade based on time
            progress = (current_time - start_time) / self.dot_duration
            if progress >= 1.0:  # Skip expired dots
                continue
                
            # Draw directly on screen with solid color
            pygame.draw.circle(
                self.screen,
                (0, 255, 255),  # Cyan color
                pos,  # Position
                self.dot_size  # Radius
            )

    def draw_hit_stats(self):
        """Draw hit statistics around the play circle."""
        # Define positions for each section's stats (relative to center)
        stat_positions = {
            "TOP": (0, -CIRCLE_RADIUS - 20),
            "TOP_RIGHT": (CIRCLE_RADIUS//1.5, -CIRCLE_RADIUS//1.5 - 20),
            "RIGHT": (CIRCLE_RADIUS + 20, 0),
            "BOTTOM_RIGHT": (CIRCLE_RADIUS//1.5, CIRCLE_RADIUS//1.5 + 20),
            "BOTTOM": (0, CIRCLE_RADIUS + 20),
            "BOTTOM_LEFT": (-CIRCLE_RADIUS//1.5, CIRCLE_RADIUS//1.5 + 20),
            "LEFT": (-CIRCLE_RADIUS - 20, 0),
            "TOP_LEFT": (-CIRCLE_RADIUS//1.5, -CIRCLE_RADIUS//1.5 - 20)
        }
        
        for section, hits in self.hit_stats.items():
            # Calculate absolute position
            rel_x, rel_y = stat_positions[section]
            pos = (self.center[0] + rel_x, self.center[1] + rel_y)
            
            # Render hit count
            text = self.stats_font.render(str(hits), True, (0, 255, 255))
            text_rect = text.get_rect(center=pos)
            self.screen.blit(text, text_rect)

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_d:  # Toggle dev mode
                    self.dev_mode.toggle_dev_mode()
                    self.calibrating = not DEV_MODE["ENABLED"]
                elif event.key == pygame.K_m:  # Toggle mapping mode
                    if not self.video_analyzer.mapping_mode:
                        self.video_analyzer.start_mapping_mode()
                    else:
                        self.video_analyzer.stop_mapping_mode()
                        self.is_dragging = False
                        self.temp_button_pos = None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if dev mode button was clicked
                if self.dev_mode_button.collidepoint(event.pos):
                    self.dev_mode.toggle_dev_mode()
                    self.calibrating = not DEV_MODE["ENABLED"]
                # Check if mapping button was clicked
                elif self.mapping_button.collidepoint(event.pos):
                    if not self.video_analyzer.mapping_mode:
                        self.video_analyzer.start_mapping_mode()
                    else:
                        self.video_analyzer.stop_mapping_mode()
                        self.is_dragging = False
                        self.temp_button_pos = None
                # Handle mapping mode clicks
                elif self.video_analyzer.mapping_mode and event.button == 1:  # Left click
                    # Get click position relative to video area
                    mouse_x, mouse_y = event.pos
                    
                    # Check if click is in video area
                    if (self.video_rect.left <= mouse_x <= self.video_rect.right and 
                        self.video_rect.top <= mouse_y <= self.video_rect.bottom):
                        
                        # Start dragging
                        self.is_dragging = True
                        
                        # Convert window coordinates to video frame coordinates
                        video_x = mouse_x - self.video_rect.left
                        video_y = mouse_y - self.video_rect.top
                        
                        # Scale coordinates to match original video resolution
                        scale_x = WEBCAM_SETTINGS["WIDTH"] / self.video_rect.width
                        scale_y = WEBCAM_SETTINGS["HEIGHT"] / self.video_rect.height
                        
                        mapped_x = int(video_x * scale_x)
                        mapped_y = int(video_y * scale_y)
                        
                        # Store temporary position
                        self.temp_button_pos = (mapped_x, mapped_y)
                        
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.is_dragging:  # Left click release
                    self.is_dragging = False
                    if self.temp_button_pos is not None:
                        # Finalize button position
                        self.video_analyzer.handle_mapping_click(*self.temp_button_pos)
                        self.temp_button_pos = None
                        
            elif event.type == pygame.MOUSEMOTION:
                if self.is_dragging and self.video_analyzer.mapping_mode:
                    # Get current mouse position
                    mouse_x, mouse_y = event.pos
                    
                    # Check if mouse is in video area
                    if (self.video_rect.left <= mouse_x <= self.video_rect.right and 
                        self.video_rect.top <= mouse_y <= self.video_rect.bottom):
                        
                        # Convert window coordinates to video frame coordinates
                        video_x = mouse_x - self.video_rect.left
                        video_y = mouse_y - self.video_rect.top
                        
                        # Scale coordinates to match original video resolution
                        scale_x = WEBCAM_SETTINGS["WIDTH"] / self.video_rect.width
                        scale_y = WEBCAM_SETTINGS["HEIGHT"] / self.video_rect.height
                        
                        mapped_x = int(video_x * scale_x)
                        mapped_y = int(video_y * scale_y)
                        
                        # Update temporary position
                        self.temp_button_pos = (mapped_x, mapped_y)

    def handle_calibration(self):
        """Handle calibration point recording."""
        frame = self.hand_tracker.get_frame()
        if frame is not None:
            results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if results and results.multi_hand_landmarks:
                # Use the first detected hand's index finger tip
                hand_landmarks = results.multi_hand_landmarks[0]
                tip_landmark = hand_landmarks.landmark[8]  # Index finger tip
                x = int(tip_landmark.x * frame.shape[1])
                y = int(tip_landmark.y * frame.shape[0])
                self.calibration_points.append((x, y))
                if len(self.calibration_points) >= 4:
                    self.calibrating = False

    def check_button_hit(self, finger_x, finger_y, finger_id):
        """Check if a finger has moved through a mapped button position."""
        current_time = time.time() * 1000
        
        # Check hit cooldown
        if current_time - self.last_hit_time < self.hit_cooldown:
            return False
            
        # Get last position for this finger
        last_pos = self.last_finger_positions.get(finger_id)
        if last_pos is None:
            self.last_finger_positions[finger_id] = (finger_x, finger_y)
            return False
            
        # Calculate movement vector
        dx = finger_x - last_pos[0]
        dy = finger_y - last_pos[1]
        movement = math.sqrt(dx*dx + dy*dy)
        
        # Update last position
        self.last_finger_positions[finger_id] = (finger_x, finger_y)
        
        # Get screen center and radius
        screen_center = self.video_analyzer.screen_center
        screen_radius = self.video_analyzer.screen_radius
        
        if not screen_center or not screen_radius:
            return False
            
        # Calculate distance from screen center
        center_dx = finger_x - screen_center[0]
        center_dy = finger_y - screen_center[1]
        distance_from_center = math.sqrt(center_dx*center_dx + center_dy*center_dy)
        
        # Check if finger is in the hit zone (70-90% of screen radius)
        if 0.7 * screen_radius < distance_from_center < 0.9 * screen_radius:
            # Calculate angle from center
            angle = math.degrees(math.atan2(center_dy, center_dx)) % 360
            
            # Check if we have enough movement
            if movement > self.min_movement_threshold:
                # Add hit dot and update counter
                self.add_hit_dot(angle)
                self.last_hit_time = current_time
                
                # Update hit statistics
                section = self.get_hit_section(angle)
                if section in self.hit_stats:
                    self.hit_stats[section] += 1
                
                print(f"Hit detected at angle {angle:.1f}, Section {section}, Movement: {movement:.1f}")
                return True
        
        return False

    def update(self):
        """Update game state."""
        if self.calibrating:
            return
            
        # Update hit dots
        self.update_hit_dots()
        
        if DEV_MODE["ENABLED"]:
            current_time = time.time() * 1000
            
            # Skip frames for performance
            self.frame_counter += 1
            if self.frame_counter % self.skip_frames != 0:
                return
                
            # Get frame from video source
            frame = self.dev_mode.get_frame()
            if frame is not None:
                # Process frame with video analyzer
                analyzed_frame, results = self.video_analyzer.analyze_frame(frame)
                
                if results and results['screen_center'] and results['screen_radius']:
                    # Convert frame to RGB for MediaPipe
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    hand_results = self.hands.process(rgb_frame)
                    
                    if hand_results and hand_results.multi_hand_landmarks:
                        for hand_landmarks in hand_results.multi_hand_landmarks:
                            # Get index finger tip and thumb tip positions
                            for finger_id in [4, 8]:  # Thumb and index finger
                                landmark = hand_landmarks.landmark[finger_id]
                                finger_x = int(landmark.x * frame.shape[1])
                                finger_y = int(landmark.y * frame.shape[0])
                                
                                # Check for button hits
                                self.check_button_hit(finger_x, finger_y, finger_id)
                
                # Update last processed time
                self.last_processed_time = current_time
                
                # Update FPS counter
                self.frame_times.append(current_time)
                if len(self.frame_times) > self.max_frame_history:
                    self.frame_times.pop(0)
                
                # Calculate FPS every second
                if current_time - self.last_fps_update > 1000:
                    if len(self.frame_times) > 1:
                        avg_frame_time = (self.frame_times[-1] - self.frame_times[0]) / len(self.frame_times)
                        self.current_fps = 1000 / avg_frame_time
                    self.last_fps_update = current_time
                    self.frame_times.clear()

    def region_to_angle(self, region_name):
        """Convert region name to angle in degrees."""
        region_angles = {
            "TOP": 270,
            "TOP_RIGHT": 315,
            "RIGHT": 0,
            "BOTTOM_RIGHT": 45,
            "BOTTOM": 90,
            "BOTTOM_LEFT": 135,
            "LEFT": 180,
            "TOP_LEFT": 225
        }
        return region_angles.get(region_name)

    def draw(self):
        """Draw the game state."""
        # Clear the screen
        self.screen.fill(COLORS["BLACK"])
        
        # Draw video/webcam feed
        frame_surface = None
        if DEV_MODE["ENABLED"]:
            frame = self.dev_mode.get_frame()
            if frame is not None:
                # Process frame with video analyzer
                analyzed_frame, results = self.video_analyzer.analyze_frame(frame)
                
                # If we're dragging in mapping mode, draw temporary button position
                if self.is_dragging and self.temp_button_pos is not None:
                    # Draw a yellow circle at the temporary position
                    cv2.circle(analyzed_frame, self.temp_button_pos, 10, (0, 255, 255), -1)
                    # Draw a text label
                    cv2.putText(analyzed_frame, 
                              f"Setting: {self.video_analyzer.current_mapping_button}",
                              (self.temp_button_pos[0] + 15, self.temp_button_pos[1]),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                
                # Draw hand landmarks if detected
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                hand_results = self.hands.process(rgb_frame)
                if hand_results and hand_results.multi_hand_landmarks:
                    for hand_landmarks in hand_results.multi_hand_landmarks:
                        # Draw hand connections
                        self.mp_drawing.draw_landmarks(
                            analyzed_frame,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2),
                            self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                        )
                        
                        # Draw larger circles at finger tips
                        for tip_id in [4, 8]:  # Thumb and index finger
                            landmark = hand_landmarks.landmark[tip_id]
                            x = int(landmark.x * frame.shape[1])
                            y = int(landmark.y * frame.shape[0])
                            cv2.circle(analyzed_frame, (x, y), 8, (0, 255, 255), -1)
                
                # Convert frame to Pygame surface
                analyzed_frame = cv2.cvtColor(analyzed_frame, cv2.COLOR_BGR2RGB)
                frame_surface = pygame.surfarray.make_surface(analyzed_frame.swapaxes(0, 1))
        else:
            frame = self.hand_tracker.get_frame()
            if frame is not None:
                # Convert frame to RGB for MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                hand_results = self.hands.process(rgb_frame)
                
                # Process frame with video analyzer
                analyzed_frame, results = self.video_analyzer.analyze_frame(frame)
                
                # If we're dragging in mapping mode, draw temporary button position
                if self.is_dragging and self.temp_button_pos is not None:
                    # Draw a yellow circle at the temporary position
                    cv2.circle(analyzed_frame, self.temp_button_pos, 10, (0, 255, 255), -1)
                    # Draw a text label
                    cv2.putText(analyzed_frame, 
                              f"Setting: {self.video_analyzer.current_mapping_button}",
                              (self.temp_button_pos[0] + 15, self.temp_button_pos[1]),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                
                # Draw hand landmarks if detected
                if hand_results and hand_results.multi_hand_landmarks:
                    for hand_landmarks in hand_results.multi_hand_landmarks:
                        # Draw hand connections
                        self.mp_drawing.draw_landmarks(
                            analyzed_frame,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2),
                            self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                        )
                
                # Convert frame to Pygame surface
                analyzed_frame = cv2.cvtColor(analyzed_frame, cv2.COLOR_BGR2RGB)
                frame_surface = pygame.surfarray.make_surface(analyzed_frame.swapaxes(0, 1))
            
        if frame_surface is not None:
            # Scale the frame to fit the video area while maintaining aspect ratio
            scaled_surface = pygame.transform.smoothscale(frame_surface, 
                                                        (self.video_rect.width, 
                                                         self.video_rect.height))
            self.screen.blit(scaled_surface, self.video_rect)
        
        if self.calibrating and not DEV_MODE["ENABLED"]:
            # Draw calibration instructions and targets
            instruction_text = self.font.render(
                "Press SPACE to calibrate at each corner of the play area",
                True, COLORS["WHITE"]
            )
            self.screen.blit(instruction_text, (10, 10))
            
            # Draw calibration targets
            for i, target in enumerate(self.calibration_targets):
                pygame.draw.circle(self.screen, COLORS["RED"], target, 10)
                if i < len(self.calibration_points):
                    pygame.draw.circle(self.screen, COLORS["GREEN"], 
                                    (int(self.calibration_points[i][0]), 
                                     int(self.calibration_points[i][1])), 5)
        else:
            # Draw the play area (circle)
            pygame.draw.circle(self.screen, COLORS["WHITE"], self.center, CIRCLE_RADIUS, 2)
            
            # Draw hit dots
            self.draw_hit_dots()
            
            # Draw hit statistics
            self.draw_hit_stats()
        
        # Draw dev mode button
        pygame.draw.rect(self.screen, COLORS["GRAY"], self.dev_mode_button)
        button_text = self.font.render(
            "Dev Mode: " + ("ON" if DEV_MODE["ENABLED"] else "OFF"),
            True, COLORS["WHITE"]
        )
        self.screen.blit(button_text, (self.dev_mode_button.x + 5, self.dev_mode_button.y + 5))
        
        # Draw mapping mode button
        pygame.draw.rect(self.screen, COLORS["GRAY"], self.mapping_button)
        mapping_text = self.font.render(
            "Map Buttons" if not self.video_analyzer.mapping_mode else f"Mapping: {self.video_analyzer.current_mapping_button}",
            True, COLORS["WHITE"]
        )
        self.screen.blit(mapping_text, (self.mapping_button.x + 5, self.mapping_button.y + 5))
        
        # Draw speed indicator and FPS in dev mode
        if DEV_MODE["ENABLED"]:
            speed_text = self.font.render(
                f"Speed: {self.video_speed:.2f}x | FPS: {self.current_fps:.1f}", 
                True, 
                COLORS["WHITE"]
            )
            self.screen.blit(speed_text, (10, WINDOW_HEIGHT - 40))
            
            # Draw speed control instructions
            controls_text = self.font.render(
                "↑/↓: Adjust Speed | R: Reset Speed", 
                True, 
                COLORS["WHITE"]
            )
            self.screen.blit(controls_text, (10, WINDOW_HEIGHT - 80))
        
        # Update the display
        pygame.display.flip()

    def run(self):
        """Main game loop."""
        last_frame_time = time.time()
        frame_interval = 1.0 / FPS
        
        while self.running:
            current_time = time.time()
            delta_time = current_time - last_frame_time
            
            # Handle events
            self.handle_events()
            
            # Update game state
            self.update()
            
            # Draw frame
            self.draw()
            
            # Control frame rate
            if delta_time < frame_interval:
                pygame.time.wait(int((frame_interval - delta_time) * 1000))
            
            last_frame_time = current_time
            
        # Clean up
        self.hand_tracker.release()
        self.dev_mode.release()
        pygame.quit()

def main():
    """Entry point of the application."""
    trainer = MaiMaiTrainer()
    trainer.run()
    sys.exit()

if __name__ == "__main__":
    main()