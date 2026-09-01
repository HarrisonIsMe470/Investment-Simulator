"""
Portfolio management for Investment Simulator
Handles player assets and transactions
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Position:
    """Represents a position in the portfolio."""
    asset_type: str
    symbol: str
    quantity: float
    average_buy_price: float
    current_price: float
    opened_day: int = 1
    locked_until_day: int = 1
    expiry_day: int = 0
    strike: float = 0.0
    underlying: str = ""
    option_kind: str = ""
    multiplier: int = 1
    
    @property
    def total_value(self) -> float:
        """Total value of this position at current price."""
        return self.quantity * self.current_price * self.multiplier
    
    @property
    def cost_basis(self) -> float:
        """Total amount invested in this position."""
        return self.quantity * self.average_buy_price * self.multiplier
    
    @property
    def unrealized_gain(self) -> float:
        """Unrealized gain/loss in dollars."""
        return self.total_value - self.cost_basis
    
    @property
    def unrealized_gain_percent(self) -> float:
        """Unrealized gain/loss as percentage."""
        if self.cost_basis == 0:
            return 0
        return (self.unrealized_gain / self.cost_basis) * 100


class Portfolio:
    """Manages player's investment portfolio."""
    
    def __init__(self, cash_balance: float = 10000, initial_balance: float = 10000):
        """Initialize portfolio with starting cash."""
        self.cash = cash_balance
        self.initial_balance = initial_balance
        self.positions: Dict[str, Position] = {}
    
    def buy(self, symbol: str, asset_type: str, quantity: float, price: float,
            metadata: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Buy an asset.
        Returns: (success, message)
        """
        metadata = metadata or {}
        multiplier = int(metadata.get("multiplier", 1))
        cost = quantity * price * multiplier
        
        if cost > self.cash:
            return False, f"Insufficient cash. Need ${cost:.2f}, have ${self.cash:.2f}"
        
        if quantity <= 0:
            return False, "Quantity must be positive"
        
        # Update cash
        self.cash -= cost
        
        # Update or create position
        if symbol in self.positions:
            old_pos = self.positions[symbol]
            total_quantity = old_pos.quantity + quantity
            new_avg_price = (
                (old_pos.quantity * old_pos.average_buy_price) + (quantity * price)
            ) / total_quantity
            
            self.positions[symbol] = Position(
                asset_type=asset_type,
                symbol=symbol,
                quantity=total_quantity,
                average_buy_price=new_avg_price,
                current_price=price,
                opened_day=min(old_pos.opened_day, metadata.get("opened_day", old_pos.opened_day)),
                locked_until_day=max(old_pos.locked_until_day, metadata.get("locked_until_day", old_pos.locked_until_day)),
                expiry_day=metadata.get("expiry_day", old_pos.expiry_day),
                strike=metadata.get("strike", old_pos.strike),
                underlying=metadata.get("underlying", old_pos.underlying),
                option_kind=metadata.get("option_kind", old_pos.option_kind),
                multiplier=metadata.get("multiplier", old_pos.multiplier),
            )
        else:
            self.positions[symbol] = Position(
                asset_type=asset_type,
                symbol=symbol,
                quantity=quantity,
                average_buy_price=price,
                current_price=price,
                opened_day=metadata.get("opened_day", 1),
                locked_until_day=metadata.get("locked_until_day", 1),
                expiry_day=metadata.get("expiry_day", 0),
                strike=metadata.get("strike", 0.0),
                underlying=metadata.get("underlying", ""),
                option_kind=metadata.get("option_kind", ""),
                multiplier=multiplier,
            )
        
        return True, f"Bought {quantity} shares of {symbol} at ${price:.2f}"
    
    def sell(self, symbol: str, quantity: float, price: float) -> Tuple[bool, str]:
        """
        Sell an asset.
        Returns: (success, message)
        """
        if symbol not in self.positions:
            return False, f"No position in {symbol}"
        
        position = self.positions[symbol]
        
        if quantity > position.quantity:
            return False, f"Cannot sell {quantity} shares. Only have {position.quantity}"
        
        if quantity <= 0:
            return False, "Quantity must be positive"
        
        # Calculate proceeds
        proceeds = quantity * price * position.multiplier
        self.cash += proceeds
        
        # Update position
        if quantity == position.quantity:
            # Close position
            del self.positions[symbol]
        else:
            # Reduce position
            position.quantity -= quantity
            # Average buy price stays the same
        
        return True, f"Sold {quantity} shares of {symbol} at ${price:.2f}"

    def force_close(self, symbol: str, settlement_price: float) -> Optional[Position]:
        """Close a complete position without consuming a player operation."""
        position = self.positions.pop(symbol, None)
        if position:
            self.cash += position.quantity * max(0.0, settlement_price) * position.multiplier
        return position
    
    def update_prices(self, prices: Dict[str, float]):
        """Update current prices for all positions."""
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.current_price = prices[symbol]
    
    def get_total_value(self) -> float:
        """Get total portfolio value including cash."""
        holdings_value = sum(pos.total_value for pos in self.positions.values())
        return self.cash + holdings_value
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get a specific position."""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """Get all positions."""
        return list(self.positions.values())
    
    def get_cash(self) -> float:
        """Get cash balance."""
        return self.cash
    
    def set_cash(self, amount: float):
        """Set cash balance directly."""
        self.cash = amount
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary statistics."""
        total_value = self.get_total_value()
        holdings_value = total_value - self.cash
        
        total_cost_basis = sum(pos.cost_basis for pos in self.positions.values())
        total_gain = total_value - self.initial_balance
        
        return {
            "total_value": total_value,
            "cash": self.cash,
            "holdings_value": holdings_value,
            "total_cost_basis": total_cost_basis,
            "total_gain": total_gain,
            "total_gain_percent": (total_gain / self.initial_balance * 100) if self.initial_balance else 0,
            "position_count": len(self.positions)
        }
