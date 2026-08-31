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
    
    @property
    def total_value(self) -> float:
        """Total value of this position at current price."""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Total amount invested in this position."""
        return self.quantity * self.average_buy_price
    
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
    
    def __init__(self, cash_balance: float = 10000):
        """Initialize portfolio with starting cash."""
        self.cash = cash_balance
        self.positions: Dict[str, Position] = {}
    
    def buy(self, symbol: str, asset_type: str, quantity: float, price: float) -> Tuple[bool, str]:
        """
        Buy an asset.
        Returns: (success, message)
        """
        cost = quantity * price
        
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
                current_price=price
            )
        else:
            self.positions[symbol] = Position(
                asset_type=asset_type,
                symbol=symbol,
                quantity=quantity,
                average_buy_price=price,
                current_price=price
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
        proceeds = quantity * price
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
        total_gain = total_value - 10000  # Assuming started with $10k
        
        return {
            "total_value": total_value,
            "cash": self.cash,
            "holdings_value": holdings_value,
            "total_cost_basis": total_cost_basis,
            "total_gain": total_gain,
            "total_gain_percent": (total_gain / 10000 * 100) if total_gain else 0,
            "position_count": len(self.positions)
        }
