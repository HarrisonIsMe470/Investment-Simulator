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
        self.animation_progress = 1.0
    
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
        self.animation_progress = 0.0
    
    def hide(self):
        """Hide the dialog."""
        self.visible = False
    
    def is_visible(self) -> bool:
        """Check if dialog is visible."""
        return self.visible

    def update_animation(self, dt: float):
        """Advance a short eased fade/zoom shared by every dependent window."""
        self.animation_progress = min(1.0, self.animation_progress + dt * 6.5)

    def present_animated(self) -> pygame.Surface:
        if self.animation_progress >= 1.0:
            return self.surface
        eased = 1 - pow(1 - self.animation_progress, 3)
        scale = 0.90 + eased * 0.10
        scaled = pygame.transform.smoothscale(
            self.surface, (max(1, int(self.width * scale)), max(1, int(self.height * scale)))
        )
        scaled.set_alpha(max(1, int(255 * eased)))
        output = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        output.fill((3, 7, 14, int(210 * eased)))
        output.blit(scaled, scaled.get_rect(center=(self.width // 2, self.height // 2)))
        return output


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
                elif event.key == pygame.K_ESCAPE:
                    return False
                elif (event.unicode.isdigit() or (event.unicode == "." and "." not in self.text)) and len(self.text) < self.max_length:
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
        pygame.draw.rect(surface, Colors.SURFACE_ALT, self.rect, border_radius=5)
        pygame.draw.rect(surface, Colors.CYAN if self.active else Colors.BORDER, self.rect, 2, border_radius=5)
        
        # Draw text
        if self.text:
            text_surface = font.render(self.text, True, Colors.WHITE)
            surface.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        else:
            placeholder_surface = font.render(self.placeholder, True, Colors.MUTED)
            surface.blit(placeholder_surface, (self.rect.x + 5, self.rect.y + 5))
        
        # Draw cursor
        if self.active and self.cursor_visible:
            cursor_x = self.rect.x + 5 + font.size(self.text)[0]
            pygame.draw.line(surface, Colors.CYAN,
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
                 cash_available: float, on_buy: Callable, multiplier: int = 1):
        """Initialize buy dialog."""
        super().__init__(width, height, f"Buy {symbol}")
        self.symbol = symbol
        self.current_price = current_price
        self.cash_available = cash_available
        self.on_buy = on_buy
        self.multiplier = multiplier
        
        # Dialog dimensions
        self.dialog_width = 400
        self.dialog_height = 240
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
        self.cancel_btn.color = Colors.LIGHT_GRAY
        self.error_message = ""

    def show(self):
        super().show()
        self.quantity_input.active = True
        self.quantity_input.text = ""
        self.error_message = ""
    
    def handle_event(self, event: pygame.event.EventType) -> bool:
        """Handle events."""
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.hide()
            return True
        
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
            total_cost = quantity * self.current_price * self.multiplier
            
            if total_cost > self.cash_available:
                self.error_message = f"Insufficient cash. Need ${total_cost:.2f}"
                return False
            elif quantity <= 0:
                self.error_message = "Quantity must be positive"
                return False
            else:
                self.result = ("success", (self.symbol, quantity, self.current_price))
                self.on_buy(self.symbol, quantity, self.current_price)
            
            self.visible = False
            return True
        except ValueError:
            self.error_message = "Enter a valid quantity"
            return False
    
    def update(self, dt: float):
        """Update dialog."""
        self.update_animation(dt)
        self.quantity_input.update(dt)
    
    def draw(self) -> pygame.Surface:
        """Draw dialog."""
        if not self.visible:
            return self.surface
        
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.surface.fill((3, 7, 14, 210))
        
        font_small = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 17)
        font_medium = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 24, bold=True)
        
        # Draw dialog box
        pygame.draw.rect(self.surface, Colors.SURFACE,
                        pygame.Rect(self.dialog_x, self.dialog_y, 
                                   self.dialog_width, self.dialog_height))
        pygame.draw.rect(self.surface, Colors.CYAN,
                        pygame.Rect(self.dialog_x, self.dialog_y,
                                   self.dialog_width, self.dialog_height), 2, border_radius=8)
        
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
        if self.error_message:
            error = font_small.render(self.error_message, True, Colors.RED)
            self.surface.blit(error, (self.dialog_x + 20, self.dialog_y + 205))
        
        return self.present_animated()


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
        self.dialog_height = 240
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
        self.cancel_btn.color = Colors.LIGHT_GRAY
        self.error_message = ""

    def show(self):
        super().show()
        self.quantity_input.active = True
        self.quantity_input.text = ""
        self.error_message = ""
    
    def handle_event(self, event: pygame.event.EventType) -> bool:
        """Handle events."""
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.hide()
            return True
        
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
                self.error_message = f"Can only sell {self.quantity_owned:g} units"
                return False
            elif quantity <= 0:
                self.error_message = "Quantity must be positive"
                return False
            else:
                self.result = ("success", (self.symbol, quantity, self.current_price))
                self.on_sell(self.symbol, quantity, self.current_price)
            
            self.visible = False
            return True
        except ValueError:
            self.error_message = "Enter a valid quantity"
            return False
    
    def update(self, dt: float):
        """Update dialog."""
        self.update_animation(dt)
        self.quantity_input.update(dt)
    
    def draw(self) -> pygame.Surface:
        """Draw dialog."""
        if not self.visible:
            return self.surface
        
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.surface.fill((3, 7, 14, 210))
        
        font_small = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 17)
        font_medium = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 24, bold=True)
        
        # Draw dialog box
        pygame.draw.rect(self.surface, Colors.SURFACE,
                        pygame.Rect(self.dialog_x, self.dialog_y,
                                   self.dialog_width, self.dialog_height))
        pygame.draw.rect(self.surface, Colors.RED,
                        pygame.Rect(self.dialog_x, self.dialog_y,
                                   self.dialog_width, self.dialog_height), 2, border_radius=8)
        
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
        if self.error_message:
            error = font_small.render(self.error_message, True, Colors.RED)
            self.surface.blit(error, (self.dialog_x + 20, self.dialog_y + 205))
        
        return self.present_animated()


class NewsDetailDialog(Dialog):
    """Readable modal showing the complete stored details for a news item."""

    def __init__(self, width: int, height: int, email, on_accept=None, on_decline=None):
        super().__init__(width, height, "News details")
        self.email = email
        self.on_accept = on_accept
        self.on_decline = on_decline
        self.action_message = ""
        self.dialog_width = min(760, width - 80)
        self.dialog_height = min(520, height - 80)
        self.dialog_x = (width - self.dialog_width) // 2
        self.dialog_y = (height - self.dialog_height) // 2
        self.close_btn = Button(self.dialog_x + self.dialog_width - 128,
                                self.dialog_y + self.dialog_height - 58,
                                100, 36, "CLOSE")
        self.close_btn.color = Colors.LIGHT_GRAY
        self.accept_btn = Button(self.dialog_x + 28, self.dialog_y + self.dialog_height - 58,
                                 130, 36, "ACCEPT OFFER")
        self.decline_btn = Button(self.dialog_x + 168, self.dialog_y + self.dialog_height - 58,
                                  100, 36, "DECLINE")
        self.decline_btn.color = Colors.RED

    def handle_event(self, event: pygame.event.EventType) -> bool:
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.hide()
            return True
        if self.close_btn.handle_event(event):
            self.hide()
            return True
        if self.email.interactive and not self.email.accepted and not self.email.resolved:
            if self.accept_btn.handle_event(event) and self.on_accept:
                _, self.action_message = self.on_accept(self.email)
            elif self.decline_btn.handle_event(event) and self.on_decline:
                _, self.action_message = self.on_decline(self.email)
        return False

    def update(self, dt: float):
        self.update_animation(dt)

    @staticmethod
    def _wrap(text: str, font: pygame.font.Font, width: int):
        lines, current = [], ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def draw(self) -> pygame.Surface:
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.surface.fill((3, 7, 14, 220))
        box = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)
        pygame.draw.rect(self.surface, Colors.SURFACE, box, border_radius=9)
        pygame.draw.rect(self.surface, Colors.BORDER, box, 2, border_radius=9)
        title_font = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 24, bold=True)
        body_font = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 17)
        meta_font = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 13)
        x, y = self.dialog_x + 28, self.dialog_y + 24
        tag = meta_font.render(f"{self.email.email_type.value.upper()}  •  DAY {self.email.game_day}", True, Colors.CYAN)
        self.surface.blit(tag, (x, y))
        y += 34
        for line in self._wrap(self.email.subject, title_font, self.dialog_width - 56)[:3]:
            self.surface.blit(title_font.render(line, True, Colors.WHITE), (x, y))
            y += 31
        y += 10
        source = f"Source: {self.email.source}"
        if self.email.published:
            source += f"  •  {self.email.published}"
        self.surface.blit(meta_font.render(source, True, Colors.MUTED), (x, y))
        y += 34
        for line in self._wrap(self.email.content, body_font, self.dialog_width - 56)[:9]:
            self.surface.blit(body_font.render(line, True, Colors.WHITE), (x, y))
            y += 25
        y += 12
        impact = self.email.market_impact or "Information only"
        self.surface.blit(meta_font.render(f"SIMULATED MARKET IMPACT  {impact}", True, Colors.YELLOW), (x, y))
        if self.email.interactive and not self.email.accepted and not self.email.resolved:
            offer_text = f"UNKNOWN OUTCOME  •  COMMITMENT ${self.email.stake:,.2f}  •  RESOLVES DAY {self.email.resolve_day}"
            self.surface.blit(meta_font.render(offer_text, True, Colors.MAGENTA), (x, y + 28))
            self.accept_btn.draw(self.surface, meta_font)
            self.decline_btn.draw(self.surface, meta_font)
        elif self.email.interactive:
            state = "ACCEPTED — OUTCOME PENDING" if self.email.accepted and not self.email.resolved else "OFFER CLOSED"
            self.surface.blit(meta_font.render(state, True, Colors.MAGENTA), (x, y + 28))
        if self.action_message:
            self.surface.blit(meta_font.render(self.action_message[:80], True, Colors.GREEN), (x, y + 54))
        self.close_btn.draw(self.surface, meta_font)
        return self.present_animated()


class OrderBookDialog(Dialog):
    """Level 2 depth view for a single stock."""

    def __init__(self, width: int, height: int, book):
        super().__init__(width, height, f"{book['symbol']} order book")
        self.book = book
        self.dialog_width = min(720, width - 80)
        self.dialog_height = min(590, height - 60)
        self.dialog_x = (width - self.dialog_width) // 2
        self.dialog_y = (height - self.dialog_height) // 2
        self.close_btn = Button(self.dialog_x + self.dialog_width - 118,
                                self.dialog_y + self.dialog_height - 52,
                                90, 34, "CLOSE")
        self.close_btn.color = Colors.LIGHT_GRAY

    def handle_event(self, event: pygame.event.EventType) -> bool:
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.hide()
            return True
        if self.close_btn.handle_event(event):
            self.hide()
            return True
        return False

    def update(self, dt: float):
        self.update_animation(dt)

    def draw(self) -> pygame.Surface:
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.surface.fill((3, 7, 14, 224))
        box = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)
        pygame.draw.rect(self.surface, Colors.SURFACE, box, border_radius=9)
        pygame.draw.rect(self.surface, Colors.BORDER, box, 2, border_radius=9)
        title_font = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 25, bold=True)
        body_font = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 14)
        small_font = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 11, bold=True)
        x, y = self.dialog_x + 28, self.dialog_y + 22
        self.surface.blit(title_font.render(f"{self.book['symbol']}  ORDER BOOK", True, Colors.WHITE), (x, y))
        meta = f"DAY {self.book['day']:03d}   MID ${self.book['mid_price']:,.2f}   SPREAD ${self.book['spread']:.4f} ({self.book['spread_percent']:.3f}%)"
        self.surface.blit(body_font.render(meta, True, Colors.MUTED), (x, y + 38))
        mode = f"{self.book['data_mode']}  •  {self.book['provider']}"
        self.surface.blit(small_font.render(mode, True, Colors.YELLOW), (x, y + 61))
        header_y = y + 90
        for label, offset in (("BID SIZE", 0), ("BID", 142), ("ASK", 352), ("ASK SIZE", 520)):
            self.surface.blit(small_font.render(label, True, Colors.MUTED), (x + offset, header_y))
        max_depth = max(self.book['bids'][-1]['cumulative'], self.book['asks'][-1]['cumulative'])
        row_y = header_y + 30
        for bid, ask in zip(self.book['bids'], self.book['asks']):
            bid_width = int(270 * bid['cumulative'] / max_depth)
            ask_width = int(270 * ask['cumulative'] / max_depth)
            pygame.draw.rect(self.surface, (18, 65, 58), (x + 270 - bid_width, row_y - 5, bid_width, 29), border_radius=3)
            pygame.draw.rect(self.surface, (72, 31, 45), (x + 330, row_y - 5, ask_width, 29), border_radius=3)
            self.surface.blit(body_font.render(f"{bid['quantity']:,}", True, Colors.WHITE), (x, row_y))
            self.surface.blit(body_font.render(f"${bid['price']:,.2f}", True, Colors.GREEN), (x + 142, row_y))
            self.surface.blit(body_font.render(f"${ask['price']:,.2f}", True, Colors.RED), (x + 352, row_y))
            self.surface.blit(body_font.render(f"{ask['quantity']:,}", True, Colors.WHITE), (x + 520, row_y))
            row_y += 39
        note = "Simulated depth • Double-click any STOCK row to refresh this view"
        self.surface.blit(small_font.render(note, True, Colors.MUTED),
                          (x, self.dialog_y + self.dialog_height - 42))
        self.close_btn.draw(self.surface, small_font)
        return self.present_animated()
