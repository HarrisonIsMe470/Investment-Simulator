"""
Main game engine for Investment Simulator
Orchestrates game logic and state management
"""

from typing import Tuple, List, Optional, Dict
from enum import Enum
import json
import os

from .database import DatabaseManager
from .market import MarketSimulator
from .portfolio import Portfolio
from .email_system import EmailSystem, Email, EmailType


class GameState(Enum):
    """Game states."""
    MENU = "menu"
    PLAYING = "playing"
    PORTFOLIO = "portfolio"
    MARKET = "market"
    EMAILS = "emails"
    END_GAME = "end_game"


class Game:
    """Main game engine."""
    
    # Game constants
    STARTING_BALANCE = 10000
    GAME_DAYS = 365
    MAX_OPERATIONS_PER_DAY = 2
    
    def __init__(self):
        """Initialize the game."""
        self.db = DatabaseManager()
        self.market = MarketSimulator()
        self.email_system = EmailSystem()
        self.portfolio: Optional[Portfolio] = None
        
        self.player_id: Optional[int] = None
        self.current_day = 1
        self.state = GameState.MENU
        self.operations_today = 0
        
        # Load or create config
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load game configuration."""
        config_path = "config/game_config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default config
        config = {
            "game_speed": "normal",
            "difficulty": "normal",
            "enable_scams": True,
            "sound_enabled": False,
            "ui_scale": 1.0
        }
        
        os.makedirs("config", exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config
    
    def start_new_game(self, player_name: str) -> int:
        """Start a new game and return player ID."""
        self.player_id = self.db.create_player(player_name, self.STARTING_BALANCE)
        self.portfolio = Portfolio(self.STARTING_BALANCE)
        self.current_day = 1
        self.operations_today = 0
        self.state = GameState.PLAYING
        
        return self.player_id
    
    def load_game(self, player_id: int) -> bool:
        """Load an existing game."""
        player = self.db.get_player(player_id)
        if not player:
            return False
        
        self.player_id = player_id
        self.current_day = player['game_day']
        self.operations_today = player['operations_today']
        self.portfolio = Portfolio(player['current_balance'])
        self.state = GameState.PLAYING
        
        return True
    
    def advance_day(self) -> Tuple[bool, str]:
        """
        Advance to the next game day.
        Returns: (success, message)
        """
        if self.current_day >= self.GAME_DAYS:
            return False, "Game has ended"
        
        # Update market prices
        market_changes = self.market.update_prices(self.current_day)
        
        # Update portfolio prices
        prices = {symbol: self.market.get_price(symbol) 
                 for symbol in self.market.get_available_symbols()}
        self.portfolio.update_prices(prices)
        
        # Generate emails for the day
        daily_emails = self.email_system.generate_daily_emails(self.current_day)
        for email in daily_emails:
            self.email_system.add_email(email)
        
        # Advance day
        self.current_day += 1
        self.operations_today = 0
        
        # Save to database
        self.db.increment_game_day(self.player_id)
        self.db.update_player_balance(self.player_id, self.portfolio.get_total_value())
        
        # Check if game ended
        if self.current_day > self.GAME_DAYS:
            self.state = GameState.END_GAME
            return True, f"Game ended! Final balance: ${self.portfolio.get_total_value():.2f}"
        
        return True, f"Advanced to day {self.current_day}"
    
    def can_trade(self) -> Tuple[bool, str]:
        """Check if player can perform a trade today."""
        if self.operations_today >= self.MAX_OPERATIONS_PER_DAY:
            return False, f"Maximum {self.MAX_OPERATIONS_PER_DAY} operations per day reached"
        
        if self.current_day > self.GAME_DAYS:
            return False, "Game has ended"
        
        return True, "Can trade"
    
    def buy_asset(self, symbol: str, quantity: float, price: float) -> Tuple[bool, str]:
        """
        Buy an asset.
        Returns: (success, message)
        """
        can_trade, msg = self.can_trade()
        if not can_trade:
            return False, msg
        
        asset_type = self.market.get_asset_type(symbol).value
        success, msg = self.portfolio.buy(symbol, asset_type, quantity, price)
        
        if success:
            self.operations_today += 1
            self.db.add_transaction(
                self.player_id, "BUY", asset_type, symbol, quantity, price, self.current_day
            )
            self.db.update_player_balance(self.player_id, self.portfolio.get_total_value())
        
        return success, msg
    
    def sell_asset(self, symbol: str, quantity: float, price: float) -> Tuple[bool, str]:
        """
        Sell an asset.
        Returns: (success, message)
        """
        can_trade, msg = self.can_trade()
        if not can_trade:
            return False, msg
        
        asset_type = self.market.get_asset_type(symbol).value
        success, msg = self.portfolio.sell(symbol, quantity, price)
        
        if success:
            self.operations_today += 1
            self.db.add_transaction(
                self.player_id, "SELL", asset_type, symbol, quantity, price, self.current_day
            )
            self.db.update_player_balance(self.player_id, self.portfolio.get_total_value())
        
        return success, msg
    
    def get_market_data(self) -> Dict:
        """Get current market data."""
        prices = {}
        for symbol in self.market.get_available_symbols():
            prices[symbol] = self.market.get_price(symbol)
        
        return prices
    
    def get_game_summary(self) -> Dict:
        """Get current game summary."""
        portfolio_summary = self.portfolio.get_portfolio_summary()
        
        return {
            "current_day": self.current_day,
            "days_remaining": max(0, self.GAME_DAYS - self.current_day),
            "operations_today": self.operations_today,
            "max_operations_per_day": self.MAX_OPERATIONS_PER_DAY,
            "portfolio": portfolio_summary,
            "unread_emails": len(self.email_system.get_unread())
        }
    
    def get_portfolio_value(self) -> float:
        """Get current portfolio value."""
        return self.portfolio.get_total_value()
    
    def run(self):
        """Run the game (placeholder for future UI integration)."""
        # This will be implemented with the Pygame UI
        print("Investment Simulator - Game Engine Ready")
        print("Waiting for UI initialization...")
