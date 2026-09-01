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
    """Muted neon palette for a modern retro terminal."""
    BLACK = (7, 11, 20)
    SURFACE = (14, 21, 35)
    SURFACE_ALT = (20, 30, 48)
    BORDER = (42, 58, 82)
    WHITE = (226, 235, 247)
    MUTED = (126, 145, 170)
    DARK_GRAY = SURFACE
    LIGHT_GRAY = (56, 72, 96)
    GREEN = (61, 220, 151)
    RED = (255, 99, 118)
    CYAN = (67, 199, 255)
    MAGENTA = (190, 126, 255)
    YELLOW = (255, 198, 92)
    DARK_GREEN = (21, 103, 77)
    METRO_BLUE = (0, 120, 215)
    METRO_ORANGE = (243, 119, 53)


class UIManager:
    """Manages UI rendering and events."""

    FONT_CANDIDATES = [
        "Helvetica Neue",
        "Arial",
        "DejaVu Sans",
        "Verdana",
        "Liberation Sans",
        "sans-serif",
    ]

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

        # Font setup (clean, readable system fonts)
        pygame.font.init()
        self.font_small = self.get_font(24)
        self.font_medium = self.get_font(32)
        self.font_large = self.get_font(48)

        self.screens: dict = {}
        self.current_screen: Optional[Screen] = None
        self.current_screen_name: Optional[str] = None

    def get_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        """Return a readable system font with a sensible fallback chain."""
        for family in self.FONT_CANDIDATES:
            if pygame.font.match_font(family):
                return pygame.font.SysFont(family, size, bold=bold)
        return pygame.font.Font(None, size)
    
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
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # Let visible dialogs consume Escape; otherwise quit.
                    has_modal = any(
                        getattr(getattr(self.current_screen, name, None), "is_visible", lambda: False)()
                        for name in ("buy_dialog", "sell_dialog", "news_dialog", "order_book_dialog")
                    )
                    if has_modal:
                        self.current_screen.handle_event(event)
                    else:
                        self.running = False
                else:
                    # Keyboard input must reach active input fields.
                    next_screen = self.current_screen.handle_event(event)
                    if next_screen:
                        if next_screen == "quit":
                            self.running = False
                        else:
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
                 color: Tuple = Colors.CYAN, text_color: Tuple = Colors.BLACK):
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
            if hasattr(event, "pos") and self.rect.collidepoint(event.pos):
                self.hovered = True
                return True

        return False
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        """Draw button on surface."""
        # Draw button
        color = tuple(min(255, channel + 24) for channel in self.color) if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, Colors.BORDER, self.rect, 1)
        pygame.draw.rect(surface, Colors.WHITE if self.hovered else Colors.METRO_BLUE,
                         (self.rect.x, self.rect.y, 4, self.rect.height))
        
        # Draw text
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class Panel:
    """Retro-style panel for displaying information."""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 bg_color: Tuple = Colors.SURFACE, border_color: Tuple = Colors.BORDER):
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
        pygame.draw.rect(surface, self.border_color, self.rect, 1)
        pygame.draw.rect(surface, Colors.METRO_BLUE,
                         (self.rect.x, self.rect.y, self.rect.width, 3))
    
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
