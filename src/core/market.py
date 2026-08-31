"""
Market simulator for Investment Simulator
Generates market prices and economic events
"""

import random
import math
from datetime import datetime
from typing import Dict, List, Tuple
from enum import Enum


class AssetType(Enum):
    """Types of investment assets."""
    STOCK = "stock"
    CRYPTOCURRENCY = "crypto"
    BOND = "bond"
    FIXED_DEPOSIT = "fixed_deposit"
    SAVINGS = "savings"
    ETF = "etf"
    OPTIONS = "options"
    FOREX = "forex"


class MarketSimulator:
    """Simulates market prices and economic events."""
    
    def __init__(self, seed: int = None):
        """Initialize the market simulator."""
        if seed is not None:
            random.seed(seed)
        
        # Initialize asset prices
        self.prices: Dict[str, float] = {
            # Large Cap Stocks
            "AAPL": 150.0,
            "GOOGL": 140.0,
            "MSFT": 380.0,
            "AMZN": 170.0,
            "NVDA": 890.0,
            
            # Mid Cap Stocks
            "TSLA": 200.0,
            "META": 330.0,
            "NFLX": 445.0,
            "UBER": 72.0,
            "COIN": 98.0,
            
            # Cryptocurrencies
            "BTC": 42000.0,
            "ETH": 2200.0,
            "SOL": 100.0,
            "XRP": 2.50,
            "ADA": 0.60,
            
            # Bonds
            "US10Y": 100.0,
            "AUDIT": 98.0,
            "GOVT5Y": 99.5,
            
            # ETFs
            "SPY": 450.0,
            "QQQ": 380.0,
            "IWM": 195.0,
            "EEM": 41.0,
            
            # Forex (price pairs)
            "EURUSD": 1.09,
            "GBPUSD": 1.27,
            "JPYUSD": 0.0074,
        }
        
        # Price volatility factors (higher = more volatile)
        self.volatility: Dict[str, float] = {
            # Large Caps (low volatility)
            "AAPL": 0.02,
            "GOOGL": 0.02,
            "MSFT": 0.015,
            "AMZN": 0.018,
            "NVDA": 0.035,
            
            # Mid Caps (medium volatility)
            "TSLA": 0.04,
            "META": 0.03,
            "NFLX": 0.025,
            "UBER": 0.028,
            "COIN": 0.06,
            
            # Crypto (high volatility)
            "BTC": 0.05,
            "ETH": 0.06,
            "SOL": 0.08,
            "XRP": 0.07,
            "ADA": 0.08,
            
            # Bonds (low volatility)
            "US10Y": 0.01,
            "AUDIT": 0.01,
            "GOVT5Y": 0.009,
            
            # ETFs
            "SPY": 0.015,
            "QQQ": 0.02,
            "IWM": 0.025,
            "EEM": 0.035,
            
            # Forex
            "EURUSD": 0.01,
            "GBPUSD": 0.012,
            "JPYUSD": 0.015,
        }
        
        # Asset correlations (market trends)
        self.market_trend = 0.0  # -1.0 to 1.0 (bearish to bullish)
        self.interest_rate_trend = 0.02  # Starting from 2%
        self.vix_level = 15.0  # Market volatility index
        
        # Event tracking
        self.current_event = None
        self.event_day = 0
    
    def update_prices(self, game_day: int) -> Dict[str, Tuple[float, float]]:
        """
        Update all market prices and return changes.
        Returns: {symbol: (new_price, percent_change)}
        """
        changes = {}
        
        # Update market sentiment (random walk)
        self.market_trend += random.gauss(0, 0.02)
        self.market_trend = max(-1.0, min(1.0, self.market_trend))
        
        # Update VIX (market volatility index)
        vix_change = random.gauss(0, 2.0)
        self.vix_level = max(10.0, self.vix_level + vix_change)
        
        # Base volatility multiplier based on VIX
        vol_multiplier = self.vix_level / 15.0
        
        # Apply random market movement based on volatility
        for symbol in self.prices:
            volatility = self.volatility.get(symbol, 0.02)
            
            # Adjust for market trend and asset category
            trend_factor = self.market_trend * 0.002
            
            # Crypto has higher correlation with market trend
            if symbol in ["BTC", "ETH", "SOL", "XRP", "ADA", "COIN"]:
                trend_factor *= 1.5
            
            # Bonds move opposite to market
            if symbol in ["US10Y", "AUDIT", "GOVT5Y"]:
                trend_factor *= -0.5
            
            # Random walk with trend
            random_change = random.gauss(trend_factor, volatility * vol_multiplier)
            
            old_price = self.prices[symbol]
            self.prices[symbol] = old_price * (1 + random_change)
            
            # Prevent negative prices
            if self.prices[symbol] <= 0:
                self.prices[symbol] = old_price * 0.95
            
            # Cap unrealistic gains
            if self.prices[symbol] > old_price * 2:
                self.prices[symbol] = old_price * 1.05
            
            percent_change = (random_change * 100)
            changes[symbol] = (self.prices[symbol], percent_change)
        
        # Apply market events
        self._apply_market_events(game_day)
        
        return changes
    
    def _apply_market_events(self, game_day: int):
        """Apply random market events that affect prices."""
        # Market events occur with 10% probability per day
        if random.random() < 0.10:
            event_weights = [
                ("bull_market", 0.25),      # Tech stocks rise
                ("bear_market", 0.20),      # General market decline
                ("rate_hike", 0.15),        # Interest rate increase
                ("rate_cut", 0.10),         # Interest rate decrease
                ("crypto_rally", 0.15),     # Crypto surge
                ("earnings_surprise", 0.10),  # Unexpected earnings
                ("black_swan", 0.05),       # Major negative event
            ]
            
            event_type = random.choices(
                [event[0] for event in event_weights],
                weights=[event[1] for event in event_weights]
            )[0]
            
            if event_type == "bull_market":
                # Tech stocks and growth stocks rise
                for symbol in ["AAPL", "GOOGL", "MSFT", "NVDA", "META", "TSLA", "NFLX", "QQQ"]:
                    self.prices[symbol] *= random.uniform(1.01, 1.08)
                self.market_trend += 0.1
            
            elif event_type == "bear_market":
                # Most assets decline
                for symbol in self.prices:
                    if symbol not in ["US10Y", "AUDIT", "GOVT5Y"]:
                        self.prices[symbol] *= random.uniform(0.92, 0.98)
                self.market_trend -= 0.15
                self.vix_level += random.uniform(5, 15)
            
            elif event_type == "rate_hike":
                # Interest rate increase
                self.interest_rate_trend += 0.25
                # Bonds gain value
                for symbol in ["US10Y", "AUDIT", "GOVT5Y"]:
                    self.prices[symbol] *= 1.05
                # Growth stocks fall
                for symbol in ["TSLA", "NFLX", "COIN"]:
                    self.prices[symbol] *= 0.97
            
            elif event_type == "rate_cut":
                # Interest rate decrease
                self.interest_rate_trend -= 0.25
                # Bonds lose value
                for symbol in ["US10Y", "AUDIT", "GOVT5Y"]:
                    self.prices[symbol] *= 0.95
                # Growth stocks rise
                for symbol in ["TSLA", "NFLX", "COIN", "META"]:
                    self.prices[symbol] *= 1.05
            
            elif event_type == "crypto_rally":
                # Cryptocurrencies surge
                for symbol in ["BTC", "ETH", "SOL", "XRP", "ADA", "COIN"]:
                    self.prices[symbol] *= random.uniform(1.08, 1.20)
            
            elif event_type == "earnings_surprise":
                # Random company has good earnings
                lucky_stock = random.choice(["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"])
                self.prices[lucky_stock] *= random.uniform(1.03, 1.08)
            
            elif event_type == "black_swan":
                # Major negative market event
                self.vix_level += 20
                self.market_trend -= 0.2
                for symbol in ["BTC", "ETH", "TSLA", "COIN", "META"]:
                    self.prices[symbol] *= random.uniform(0.90, 0.95)
    
    def get_price(self, symbol: str) -> float:
        """Get current price of an asset."""
        return self.prices.get(symbol, 100.0)
    
    def get_asset_type(self, symbol: str) -> AssetType:
        """Determine asset type from symbol."""
        crypto_symbols = ["BTC", "ETH", "SOL"]
        bond_symbols = ["US10Y", "AUDIT"]
        etf_symbols = ["SPY", "QQQ"]
        forex_symbols = ["EURUSD", "GBPUSD"]
        
        if symbol in crypto_symbols:
            return AssetType.CRYPTOCURRENCY
        elif symbol in bond_symbols:
            return AssetType.BOND
        elif symbol in etf_symbols:
            return AssetType.ETF
        elif symbol in forex_symbols:
            return AssetType.FOREX
        else:
            return AssetType.STOCK
    
    def get_available_symbols(self) -> List[str]:
        """Get list of all available trading symbols."""
        return list(self.prices.keys())
