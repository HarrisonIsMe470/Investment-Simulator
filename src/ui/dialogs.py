"""
Dialog system for Investment Simulator
Handles user input dialogs and interactions
"""

import pygame
from typing import Optional, Tuple, Callable
from abc import ABC, abstractmethod

from .ui_manager import Colors, Button, Panel


class Dialog(ABC):
    """Base class for dialogs."""
    
    def __init__(self, width: int, height: int, title: str):
        """Initialize dialog."""
        self.width = width
        self.height = height
        self.title = title
        self.surface = pygame.Surface((width, height))
        self.visible = False
        self.result: Optional[any] = None
    
    @abstractmethod
    def handle_event(self, event: pygame.event.EventType) -> bool:
        """
        Handle user input.
        Returns: True if dialog is closed
        """
        pass
    
    @abstractmethod
    def update(self, dt: float):
        """Update dialog state."""
        pass
    
    @abstractmethod
    def draw(self) -> pygame.Surface:
        """Draw dialog and return surface."""
        pass
    
    def show(self):
        """Show the dialog."""
        self.visible = True
    
    def hide(self):
        """Hide the dialog."""
        self.visible = False
    
    def is_visible(self) -> bool:
        """Check if dialog is visible."""
        return self.visible


class InputField:
    """Text input field."""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 placeholder: str = "", max_length: int = 20):
        """Initialize input field."""
        self.rect = pygame.Rect(x, y, width, height)
        self.placeholder = placeholder
        self.max_length = max_length
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_time = 0
    
    def handle_event(self, event: pygame.event.EventType):
        """Handle input events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == pygame.K_RETURN:
                    return True
                elif len(self.text) < self.max_length:
                    self.text += event.unicode
        
        return False
    
    def update(self, dt: float):
        """Update cursor blink."""
        self.cursor_time += dt
        if self.cursor_time > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_time = 0
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        """Draw input field."""
        # Draw background
        pygame.draw.rect(surface, Colors.WHITE if self.active else Colors.LIGHT_GRAY, self.rect)
        pygame.draw.rect(surface, Colors.BLACK, self.rect, 2)
        
        # Draw text
        if self.text:
            text_surface = font.render(self.text, True, Colors.BLACK)
            surface.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        else:
            placeholder_surface = font.render(self.placeholder, True, Colors.DARK_GRAY)
            surface.blit(placeholder_surface, (self.rect.x + 5, self.rect.y + 5))
        
        # Draw cursor
        if self.active and self.cursor_visible:
            cursor_x = self.rect.x + 5 + font.size(self.text)[0]
            pygame.draw.line(surface, Colors.BLACK, 
                           (cursor_x, self.rect.y + 5),
                           (cursor_x, self.rect.y + self.rect.height - 5), 2)
    
    def get_value(self):
        """Get input value."""
        return self.text
    
    def set_value(self, value: str):
        """Set input value."""
        self.text = str(value)[:self.max_length]


class BuyDialog(Dialog):
    """Dialog for buying assets."""
    
    def __init__(self, width: int, height: int, symbol: str, current_price: float, 
                 cash_available: float, on_buy: Callable):
        """Initialize buy dialog."""
        super().__init__(width, height, f"Buy {symbol}")
        self.symbol = symbol
        self.current_price = current_price
        self.cash_available = cash_available
        self.on_buy = on_buy
        
        # Dialog dimensions
        self.dialog_width = 400
        self.dialog_height = 300
        self.dialog_x = (width - self.dialog_width) // 2
        self.dialog_y = (height - self.dialog_height) // 2
        
        # Input fields
        self.quantity_input = InputField(
            self.dialog_x + 20, self.dialog_y + 80, 360, 40,
            placeholder="Enter quantity", max_length=10
        )
        
        # Buttons
        self.buy_btn = Button(self.dialog_x + 20, self.dialog_y + 140, 170, 40, "BUY")
        self.cancel_btn = Button(self.dialog_x + 210, self.dialog_y + 140, 170, 40, "CANCEL")
    
    def handle_event(self, event: pygame.event.EventType) -> bool:
        """Handle events."""
        if not self.visible:
            return False
        
        if self.quantity_input.handle_event(event):
            # User pressed enter
            return self._try_buy()
        
        if self.buy_btn.handle_event(event):
            return self._try_buy()
        elif self.cancel_btn.handle_event(event):
            self.visible = False
            return False
        
        return False
    
    def _try_buy(self) -> bool:
        """Try to execute buy order."""
        try:
            quantity = float(self.quantity_input.get_value())
            total_cost = quantity * self.current_price
            
            if total_cost > self.cash_available:
                self.result = ("error", f"Insufficient cash. Need ${total_cost:.2f}")
            elif quantity <= 0:
                self.result = ("error", "Quantity must be positive")
            else:
                self.result = ("success", (self.symbol, quantity, self.current_price))
                self.on_buy(self.symbol, quantity, self.current_price)
            
            self.visible = False
            return True
        except ValueError:
            self.result = ("error", "Invalid quantity")
            self.visible = False
            return True
    
    def update(self, dt: float):
        """Update dialog."""
        self.quantity_input.update(dt)
    
    def draw(self) -> pygame.Surface:
        """Draw dialog."""
        if not self.visible:
            return self.surface
        
        self.surface.fill((200, 200, 200, 128))
        
        font_small = pygame.font.Font(None, 24)
        font_medium = pygame.font.Font(None, 32)
        
        # Draw dialog box
        pygame.draw.rect(self.surface, Colors.DARK_GRAY, 
                        pygame.Rect(self.dialog_x, self.dialog_y, 
                                   self.dialog_width, self.dialog_height))
        pygame.draw.rect(self.surface, Colors.WHITE,
                        pygame.Rect(self.dialog_x, self.dialog_y,
                                   self.dialog_width, self.dialog_height), 3)
        
        # Title
        title = font_medium.render(self.title, True, Colors.CYAN)
        self.surface.blit(title, (self.dialog_x + 20, self.dialog_y + 10))
        
        # Info
        info_text = f"Price: ${self.current_price:.2f} | Cash: ${self.cash_available:.2f}"
        info_surface = font_small.render(info_text, True, Colors.GREEN)
        self.surface.blit(info_surface, (self.dialog_x + 20, self.dialog_y + 50))
        
        # Input field
        self.quantity_input.draw(self.surface, font_small)
        
        # Buttons
        self.buy_btn.draw(self.surface, font_small)
        self.cancel_btn.draw(self.surface, font_small)
        
        return self.surface


class SellDialog(Dialog):
    """Dialog for selling assets."""
    
    def __init__(self, width: int, height: int, symbol: str, current_price: float,
                 quantity_owned: float, on_sell: Callable):
        """Initialize sell dialog."""
        super().__init__(width, height, f"Sell {symbol}")
        self.symbol = symbol
        self.current_price = current_price
        self.quantity_owned = quantity_owned
        self.on_sell = on_sell
        
        # Dialog dimensions
        self.dialog_width = 400
        self.dialog_height = 300
        self.dialog_x = (width - self.dialog_width) // 2
        self.dialog_y = (height - self.dialog_height) // 2
        
        # Input field
        self.quantity_input = InputField(
            self.dialog_x + 20, self.dialog_y + 80, 360, 40,
            placeholder="Enter quantity", max_length=10
        )
        
        # Buttons
        self.sell_btn = Button(self.dialog_x + 20, self.dialog_y + 140, 170, 40, "SELL")
        self.cancel_btn = Button(self.dialog_x + 210, self.dialog_y + 140, 170, 40, "CANCEL")
    
    def handle_event(self, event: pygame.event.EventType) -> bool:
        """Handle events."""
        if not self.visible:
            return False
        
        if self.quantity_input.handle_event(event):
            return self._try_sell()
        
        if self.sell_btn.handle_event(event):
            return self._try_sell()
        elif self.cancel_btn.handle_event(event):
            self.visible = False
            return False
        
        return False
    
    def _try_sell(self) -> bool:
        """Try to execute sell order."""
        try:
            quantity = float(self.quantity_input.get_value())
            
            if quantity > self.quantity_owned:
                self.result = ("error", f"Can only sell {self.quantity_owned} shares")
            elif quantity <= 0:
                self.result = ("error", "Quantity must be positive")
            else:
                self.result = ("success", (self.symbol, quantity, self.current_price))
                self.on_sell(self.symbol, quantity, self.current_price)
            
            self.visible = False
            return True
        except ValueError:
            self.result = ("error", "Invalid quantity")
            self.visible = False
            return True
    
    def update(self, dt: float):
        """Update dialog."""
        self.quantity_input.update(dt)
    
    def draw(self) -> pygame.Surface:
        """Draw dialog."""
        if not self.visible:
            return self.surface
        
        self.surface.fill((200, 200, 200, 128))
        
        font_small = pygame.font.Font(None, 24)
        font_medium = pygame.font.Font(None, 32)
        
        # Draw dialog box
        pygame.draw.rect(self.surface, Colors.DARK_GRAY,
                        pygame.Rect(self.dialog_x, self.dialog_y,
                                   self.dialog_width, self.dialog_height))
        pygame.draw.rect(self.surface, Colors.WHITE,
                        pygame.Rect(self.dialog_x, self.dialog_y,
                                   self.dialog_width, self.dialog_height), 3)
        
        # Title
        title = font_medium.render(self.title, True, Colors.CYAN)
        self.surface.blit(title, (self.dialog_x + 20, self.dialog_y + 10))
        
        # Info
        info_text = f"Price: ${self.current_price:.2f} | Own: {self.quantity_owned}"
        info_surface = font_small.render(info_text, True, Colors.GREEN)
        self.surface.blit(info_surface, (self.dialog_x + 20, self.dialog_y + 50))
        
        # Input field
        self.quantity_input.draw(self.surface, font_small)
        
        # Buttons
        self.sell_btn.draw(self.surface, font_small)
        self.cancel_btn.draw(self.surface, font_small)
        
        return self.surface
