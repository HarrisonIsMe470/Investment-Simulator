"""
Data models for Investment Simulator
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class OrderType(Enum):
    """Types of orders."""
    BUY = "buy"
    SELL = "sell"


class AssetCategory(Enum):
    """Asset categories."""
    STOCK = "stock"
    CRYPTO = "crypto"
    BOND = "bond"
    DEPOSIT = "deposit"
    SAVINGS = "savings"
    ETF = "etf"
    OPTIONS = "options"
    FOREX = "forex"


@dataclass
class Asset:
    """Represents an investment asset."""
    symbol: str
    name: str
    category: AssetCategory
    current_price: float
    change_percent: float = 0.0
    volume: float = 0.0
    
    def __repr__(self):
        return f"Asset({self.symbol}, ${self.current_price:.2f})"


@dataclass
class Order:
    """Represents a buy/sell order."""
    order_type: OrderType
    asset_symbol: str
    quantity: float
    price: float
    timestamp: datetime
    
    @property
    def total_value(self) -> float:
        """Total order value."""
        return self.quantity * self.price


@dataclass
class Transaction:
    """Represents a completed transaction."""
    order_id: int
    order_type: OrderType
    asset_symbol: str
    quantity: float
    price: float
    total_value: float
    commission: float = 0.0
    game_day: int = 1
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PlayerStats:
    """Player statistics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    largest_gain: float = 0.0
    largest_loss: float = 0.0
    win_rate: float = 0.0
    
    def update_trade(self, gain: float):
        """Update stats with a completed trade."""
        self.total_trades += 1
        if gain > 0:
            self.winning_trades += 1
            self.largest_gain = max(self.largest_gain, gain)
        else:
            self.losing_trades += 1
            self.largest_loss = min(self.largest_loss, gain)
        
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
