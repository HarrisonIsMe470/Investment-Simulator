"""
Game screens for Investment Simulator
Implements different UI screens for various game states
"""

import pygame
from typing import Optional

from ..core.game import Game, GameState
from .ui_manager import Screen, Colors, Button, Panel


class MenuScreen(Screen):
    """Main menu screen."""
    
    def __init__(self, width: int, height: int, game: Game):
        """Initialize menu screen."""
        super().__init__(width, height)
        self.game = game
        
        # Create buttons
        button_y = height // 2
        self.new_game_btn = Button(width // 2 - 100, button_y, 200, 50, "New Game")
        self.load_game_btn = Button(width // 2 - 100, button_y + 70, 200, 50, "Load Game")
        self.quit_btn = Button(width // 2 - 100, button_y + 140, 200, 50, "Quit")
        
        self.buttons = [self.new_game_btn, self.load_game_btn, self.quit_btn]
    
    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """Handle events."""
        for button in self.buttons:
            if button.handle_event(event):
                if button == self.new_game_btn:
                    # Start new game
                    self.game.start_new_game("Player")
                    return "trading"
                elif button == self.load_game_btn:
                    # Load game (placeholder)
                    return "trading"
                elif button == self.quit_btn:
                    return None
        
        return None
    
    def update(self, dt: float):
        """Update screen."""
        pass
    
    def draw(self) -> pygame.Surface:
        """Draw screen."""
        self.surface.fill(Colors.BLACK)
        
        # Draw title
        font_large = pygame.font.Font(None, 64)
        title = font_large.render("INVESTMENT SIMULATOR", True, Colors.CYAN)
        title_rect = title.get_rect(center=(self.width // 2, 100))
        self.surface.blit(title, title_rect)
        
        # Draw subtitle
        font_small = pygame.font.Font(None, 24)
        subtitle = font_small.render("Retro Trading Experience", True, Colors.GREEN)
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 150))
        self.surface.blit(subtitle, subtitle_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.surface, font_small)
        
        return self.surface


class TradingScreen(Screen):
    """Main trading screen."""
    
    def __init__(self, width: int, height: int, game: Game):
        """Initialize trading screen."""
        super().__init__(width, height)
        self.game = game
        
        # Panels
        self.info_panel = Panel(10, 10, 400, 150)
        self.market_panel = Panel(10, 170, 400, 500)
        self.portfolio_panel = Panel(420, 10, 400, 300)
        self.trading_panel = Panel(420, 320, 400, 350)
        self.email_panel = Panel(830, 10, 440, 660)
        
        # Buttons
        self.buy_btn = Button(430, 330, 80, 40, "BUY")
        self.sell_btn = Button(520, 330, 80, 40, "SELL")
        self.next_day_btn = Button(610, 330, 100, 40, "NEXT DAY")
        self.portfolio_btn = Button(720, 330, 100, 40, "PORTFOLIO")
    
    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """Handle events."""
        if self.buy_btn.handle_event(event):
            # Show buy dialog
            pass
        elif self.sell_btn.handle_event(event):
            # Show sell dialog
            pass
        elif self.next_day_btn.handle_event(event):
            self.game.advance_day()
        elif self.portfolio_btn.handle_event(event):
            return "portfolio"
        
        return None
    
    def update(self, dt: float):
        """Update screen."""
        pass
    
    def draw(self) -> pygame.Surface:
        """Draw screen."""
        self.surface.fill(Colors.BLACK)
        font_small = pygame.font.Font(None, 24)
        font_medium = pygame.font.Font(None, 32)
        
        # Draw info panel
        self.info_panel.draw(self.surface)
        summary = self.game.get_game_summary()
        info_text = [
            f"Day: {summary['current_day']}/{365}",
            f"Ops: {summary['operations_today']}/{summary['max_operations_per_day']}",
            f"Balance: ${summary['portfolio']['total_value']:.2f}",
        ]
        y_pos = 20
        for text in info_text:
            text_surface = font_small.render(text, True, Colors.GREEN)
            self.surface.blit(text_surface, (20, y_pos))
            y_pos += 30
        
        # Draw market panel
        self.market_panel.draw(self.surface)
        market_data = self.game.get_market_data()
        y_pos = 180
        for symbol, price in list(market_data.items())[:15]:
            market_text = f"{symbol}: ${price:.2f}"
            text_surface = font_small.render(market_text, True, Colors.WHITE)
            self.surface.blit(text_surface, (20, y_pos))
            y_pos += 25
        
        # Draw portfolio panel
        self.portfolio_panel.draw(self.surface)
        positions = self.game.portfolio.get_all_positions()
        y_pos = 20
        portfolio_title = font_medium.render("PORTFOLIO", True, Colors.CYAN)
        self.surface.blit(portfolio_title, (430, y_pos))
        y_pos += 40
        
        for pos in positions[:5]:
            pos_text = f"{pos.symbol}: {pos.quantity} @ ${pos.current_price:.2f}"
            text_surface = font_small.render(pos_text, True, Colors.GREEN)
            self.surface.blit(text_surface, (430, y_pos))
            y_pos += 25
        
        # Draw buttons
        for button in [self.buy_btn, self.sell_btn, self.next_day_btn, self.portfolio_btn]:
            button.draw(self.surface, font_small)
        
        # Draw email panel
        self.email_panel.draw(self.surface)
        emails = self.game.email_system.get_unread()
        email_title = font_medium.render(f"EMAILS ({len(emails)})", True, Colors.YELLOW)
        self.surface.blit(email_title, (840, 20))
        
        y_pos = 70
        for email in emails[:8]:
            email_text = f"- {email.subject[:30]}"
            text_surface = font_small.render(email_text, True, Colors.MAGENTA)
            self.surface.blit(text_surface, (840, y_pos))
            y_pos += 25
        
        return self.surface


class PortfolioScreen(Screen):
    """Detailed portfolio screen."""
    
    def __init__(self, width: int, height: int, game: Game):
        """Initialize portfolio screen."""
        super().__init__(width, height)
        self.game = game
        
        # Back button
        self.back_btn = Button(10, 10, 100, 40, "BACK")
    
    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """Handle events."""
        if self.back_btn.handle_event(event):
            return "trading"
        
        return None
    
    def update(self, dt: float):
        """Update screen."""
        pass
    
    def draw(self) -> pygame.Surface:
        """Draw screen."""
        self.surface.fill(Colors.BLACK)
        font_small = pygame.font.Font(None, 24)
        font_medium = pygame.font.Font(None, 32)
        font_large = pygame.font.Font(None, 48)
        
        # Title
        title = font_large.render("PORTFOLIO", True, Colors.CYAN)
        self.surface.blit(title, (self.width // 2 - 100, 20))
        
        # Summary
        summary = self.game.get_game_summary()
        portfolio = summary['portfolio']
        
        summary_text = [
            f"Total Value: ${portfolio['total_value']:.2f}",
            f"Cash: ${portfolio['cash']:.2f}",
            f"Holdings Value: ${portfolio['holdings_value']:.2f}",
            f"Total Gain: ${portfolio['total_gain']:.2f} ({portfolio['total_gain_percent']:.2f}%)",
        ]
        
        y_pos = 100
        for text in summary_text:
            text_surface = font_medium.render(text, True, Colors.GREEN)
            self.surface.blit(text_surface, (20, y_pos))
            y_pos += 50
        
        # Positions
        y_pos = 350
        positions_title = font_medium.render("POSITIONS", True, Colors.YELLOW)
        self.surface.blit(positions_title, (20, y_pos))
        y_pos += 50
        
        for pos in self.game.portfolio.get_all_positions():
            pos_info = f"{pos.symbol}: {pos.quantity} @ ${pos.current_price:.2f} (Value: ${pos.total_value:.2f}, Gain: {pos.unrealized_gain_percent:.2f}%)"
            text_surface = font_small.render(pos_info, True, Colors.WHITE)
            self.surface.blit(text_surface, (20, y_pos))
            y_pos += 30
        
        # Back button
        self.back_btn.draw(self.surface, font_small)
        
        return self.surface
