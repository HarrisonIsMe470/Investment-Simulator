"""
Pygame UI system for Investment Simulator
Manages the graphical interface
"""

import pygame
from typing import Optional, Tuple
from enum import Enum
from abc import ABC, abstractmethod


class Screen(ABC):
    """Base class for game screens."""
    
    def __init__(self, width: int, height: int):
        """Initialize screen."""
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))
    
    @abstractmethod
    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """
        Handle user input.
        Returns: next screen name or None
        """
        pass
    
    @abstractmethod
    def update(self, dt: float):
        """Update screen state."""
        pass
    
    @abstractmethod
    def draw(self) -> pygame.Surface:
        """Draw screen and return surface."""
        pass


class Colors:
    """Retro color palette."""
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    DARK_GRAY = (64, 64, 64)
    LIGHT_GRAY = (192, 192, 192)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    YELLOW = (255, 255, 0)
    DARK_GREEN = (0, 128, 0)


class UIManager:
    """Manages UI rendering and events."""
    
    def __init__(self, width: int = 1280, height: int = 720, title: str = "Investment Simulator"):
        """Initialize UI manager."""
        pygame.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 60
        
        # Font setup (retro style)
        pygame.font.init()
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_large = pygame.font.Font(None, 48)
        
        self.screens: dict = {}
        self.current_screen: Optional[Screen] = None
        self.current_screen_name: Optional[str] = None
    
    def register_screen(self, name: str, screen: Screen):
        """Register a new screen."""
        self.screens[name] = screen
    
    def set_screen(self, screen_name: str) -> bool:
        """Set the active screen."""
        if screen_name in self.screens:
            self.current_screen = self.screens[screen_name]
            self.current_screen_name = screen_name
            return True
        return False
    
    def run(self):
        """Main game loop."""
        while self.running and self.current_screen:
            dt = self.clock.tick(self.fps) / 1000.0
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                else:
                    # Pass event to current screen
                    next_screen = self.current_screen.handle_event(event)
                    if next_screen:
                        self.set_screen(next_screen)
            
            # Update
            self.current_screen.update(dt)
            
            # Draw
            surface = self.current_screen.draw()
            self.screen.blit(surface, (0, 0))
            
            pygame.display.flip()
        
        pygame.quit()
    
    def quit(self):
        """Quit the game."""
        self.running = False


class Button:
    """Retro-style button."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 color: Tuple = Colors.LIGHT_GRAY, text_color: Tuple = Colors.BLACK):
        """Initialize button."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hovered = False
    
    def handle_event(self, event: pygame.event.EventType) -> bool:
        """
        Handle events.
        Returns: True if clicked
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered:
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        """Draw button on surface."""
        # Draw button
        color = Colors.WHITE if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, Colors.BLACK, self.rect, 2)
        
        # Draw text
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class Panel:
    """Retro-style panel for displaying information."""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 bg_color: Tuple = Colors.DARK_GRAY, border_color: Tuple = Colors.WHITE):
        """Initialize panel."""
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = bg_color
        self.border_color = border_color
        self.content: list = []
    
    def draw(self, surface: pygame.Surface):
        """Draw panel on surface."""
        # Draw background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        
        # Draw border
        pygame.draw.rect(surface, self.border_color, self.rect, 3)
    
    def add_text(self, text: str, font: pygame.font.Font, color: Tuple = Colors.WHITE, 
                 y_offset: int = 10):
        """Add text to panel content."""
        self.content.append((text, font, color, y_offset))
    
    def draw_content(self, surface: pygame.Surface):
        """Draw panel content."""
        current_y = self.rect.y + 10
        
        for text, font, color, y_offset in self.content:
            text_surface = font.render(text, True, color)
            surface.blit(text_surface, (self.rect.x + 10, current_y))
            current_y += y_offset
