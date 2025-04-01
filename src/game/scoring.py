"""
Scoring system for the MaiMai game.
"""

import pygame
from utils.config import COLORS, TIMING_WINDOWS

class ScoreManager:
    def __init__(self):
        """Initialize the score manager."""
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.perfects = 0
        self.greats = 0
        self.goods = 0
        self.misses = 0
        
        # Initialize font
        self.font = pygame.font.Font(None, 36)
        
    def add_hit(self, timing):
        """Add a hit with the given timing."""
        if timing <= TIMING_WINDOWS["PERFECT"]:
            self.score += 100
            self.perfects += 1
            self.combo += 1
        elif timing <= TIMING_WINDOWS["GREAT"]:
            self.score += 80
            self.greats += 1
            self.combo += 1
        elif timing <= TIMING_WINDOWS["GOOD"]:
            self.score += 50
            self.goods += 1
            self.combo += 1
        else:
            self.misses += 1
            self.combo = 0
            
        # Update max combo
        self.max_combo = max(self.max_combo, self.combo)
        
    def add_miss(self):
        """Add a miss."""
        self.misses += 1
        self.combo = 0
        
    def draw(self, screen):
        """Draw the score information on screen."""
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, COLORS["WHITE"])
        screen.blit(score_text, (10, 10))
        
        # Combo
        combo_text = self.font.render(f"Combo: {self.combo}", True, COLORS["WHITE"])
        screen.blit(combo_text, (10, 50))
        
        # Max Combo
        max_combo_text = self.font.render(f"Max Combo: {self.max_combo}", True, COLORS["WHITE"])
        screen.blit(max_combo_text, (10, 90))
        
        # Statistics
        stats_text = self.font.render(
            f"Perfect: {self.perfects} Great: {self.greats} Good: {self.goods} Miss: {self.misses}",
            True, COLORS["WHITE"]
        )
        screen.blit(stats_text, (10, 130))
        
    def get_accuracy(self):
        """Calculate the accuracy percentage."""
        total_notes = self.perfects + self.greats + self.goods + self.misses
        if total_notes == 0:
            return 0
        return (self.perfects + self.greats + self.goods) / total_notes * 100 