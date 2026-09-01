"""
Market simulator for Investment Simulator
Generates market prices and economic events
"""

import random
import math
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Tuple
from enum import Enum
from .market_data_service import AlpacaQuoteService


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
        # A private generator keeps seeded games reproducible without changing
        # randomness used by the UI or other game systems.
        self.rng = random.Random(seed)
        self.quote_service = AlpacaQuoteService()
        
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

            # Sector diversification
            "JPM": 195.0,       # Banking
            "V": 275.0,         # Payments
            "JNJ": 160.0,       # Healthcare
            "PFE": 29.0,        # Pharmaceuticals
            "XOM": 116.0,       # Energy
            "NEE": 72.0,        # Utilities / renewables
            "WMT": 68.0,        # Consumer staples
            "DIS": 112.0,       # Media
            "BA": 185.0,        # Industrials
            "BHP": 58.0,        # Mining
            
            # Cryptocurrencies
            "BTC": 42000.0,
            "ETH": 2200.0,
            "SOL": 100.0,
            "XRP": 2.50,
            "ADA": 0.60,
            
            # Bonds
            "USA3M": 100.0,
            "AUS3M": 100.0,
            "GBR3M": 100.0,
            "JPN3M": 100.0,
            "DEU3M": 100.0,
            
            # ETFs
            "SPY": 450.0,
            "QQQ": 380.0,
            "IWM": 195.0,
            "EEM": 41.0,
            
            # Forex (price pairs)
            "EURUSD": 1.09,
            "GBPUSD": 1.27,
            "JPYUSD": 0.0074,
            "AUDUSD": 0.66,
            "USDCAD": 1.36,
            "USDCHF": 0.88,

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
            "JPM": 0.018,
            "V": 0.017,
            "JNJ": 0.012,
            "PFE": 0.022,
            "XOM": 0.022,
            "NEE": 0.018,
            "WMT": 0.012,
            "DIS": 0.024,
            "BA": 0.028,
            "BHP": 0.025,
            
            # Crypto (high volatility)
            "BTC": 0.05,
            "ETH": 0.06,
            "SOL": 0.08,
            "XRP": 0.07,
            "ADA": 0.08,
            
            # Bonds (low volatility)
            "USA3M": 0.004,
            "AUS3M": 0.004,
            "GBR3M": 0.004,
            "JPN3M": 0.003,
            "DEU3M": 0.0035,
            
            # ETFs
            "SPY": 0.015,
            "QQQ": 0.02,
            "IWM": 0.025,
            "EEM": 0.035,
            
            # Forex
            "EURUSD": 0.01,
            "GBPUSD": 0.012,
            "JPYUSD": 0.015,
            "AUDUSD": 0.012,
            "USDCAD": 0.010,
            "USDCHF": 0.009,
        }
        
        # Asset correlations (market trends)
        self.market_trend = 0.0  # -1.0 to 1.0 (bearish to bullish)
        self.interest_rate_trend = 0.02  # Starting from 2%
        self.vix_level = 15.0  # Market volatility index

        self.stock_symbols = [
            "AAPL", "GOOGL", "MSFT", "AMZN", "NVDA", "TSLA", "META",
            "NFLX", "UBER", "COIN", "JPM", "V", "JNJ", "PFE", "XOM",
            "NEE", "WMT", "DIS", "BA", "BHP",
        ]
        self.bond_symbols = ["USA3M", "AUS3M", "GBR3M", "JPN3M", "DEU3M"]
        self.bond_contracts = {
            symbol: {"maturity_days": 90, "term": "3 months"}
            for symbol in self.bond_symbols
        }
        self.current_day = 1
        self.option_contracts = {}
        for underlying in list(self.stock_symbols):
            self._add_option_chain(underlying, (30, 60, 90))
        self.pending_ipos = [
            {"symbol": "NOVA", "name": "Nova Robotics", "sector": "technology", "offer_price": 24.0, "announce_day": 5, "listing_day": 15},
            {"symbol": "CLRN", "name": "Clearwater Renewables", "sector": "energy", "offer_price": 18.0, "announce_day": 48, "listing_day": 60},
            {"symbol": "MEDX", "name": "Medaxis Health", "sector": "healthcare", "offer_price": 32.0, "announce_day": 105, "listing_day": 120},
        ]
        self.listed_ipos = set()
        
        # Event tracking
        self.current_event = None
        self.event_day = 0
        self.last_changes: Dict[str, float] = {symbol: 0.0 for symbol in self.prices}
        self.sectors = {
            "AAPL": "technology", "GOOGL": "technology", "MSFT": "technology",
            "AMZN": "consumer", "NVDA": "technology", "TSLA": "automotive",
            "META": "technology", "NFLX": "media", "UBER": "transport",
            "COIN": "finance", "JPM": "finance", "V": "finance",
            "JNJ": "healthcare", "PFE": "healthcare", "XOM": "energy",
            "NEE": "utilities", "WMT": "consumer", "DIS": "media",
            "BA": "industrials", "BHP": "materials",
        }
    
    def update_prices(self, game_day: int) -> Dict[str, Tuple[float, float]]:
        """
        Update all market prices and return changes.
        Returns: {symbol: (new_price, percent_change)}
        """
        changes = {}
        self.current_day = game_day
        opening_prices = dict(self.prices)
        self._list_due_ipos(game_day)
        self._roll_option_chains(game_day)
        
        # Update market sentiment (random walk)
        self.market_trend += self.rng.gauss(0, 0.02)
        self.market_trend = max(-1.0, min(1.0, self.market_trend))
        
        # Update VIX (market volatility index)
        vix_change = self.rng.gauss(0, 2.0)
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
            if self.get_asset_type(symbol) == AssetType.BOND:
                trend_factor *= -0.5
            
            # Random walk with trend
            if symbol in self.option_contracts:
                contract = self.option_contracts[symbol]
                underlying = contract["underlying"]
                spot = self.prices[underlying]
                days = max(0, contract["expiry_day"] - game_day)
                intrinsic = max(0.0, spot - contract["strike"]) if contract["kind"] == "CALL" else max(0.0, contract["strike"] - spot)
                time_value = spot * self.volatility[underlying] * math.sqrt(max(1, days) / 365) * 0.45
                target = max(0.05, intrinsic + time_value)
                random_change = (target / max(0.01, self.prices[symbol])) - 1
            else:
                random_change = self.rng.gauss(trend_factor, volatility * vol_multiplier)
            
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
        for symbol, old_change in list(changes.items()):
            previous_price = old_change[0] / (1 + old_change[1] / 100) if old_change[1] > -100 else old_change[0]
            percent = ((self.prices[symbol] / previous_price) - 1) * 100
            changes[symbol] = (self.prices[symbol], percent)
            self.last_changes[symbol] = percent
        
        return changes

    def _add_option_chain(self, underlying: str, expiries):
        """List three strikes and both rights for each requested expiry."""
        spot = self.prices[underlying]
        step = max(1.0, round(spot * 0.10, 2))
        strikes = (round(spot - step, 2), round(spot, 2), round(spot + step, 2))
        for expiry in expiries:
            for strike in strikes:
                for kind in ("CALL", "PUT"):
                    code = "C" if kind == "CALL" else "P"
                    symbol = f"{underlying}_{code}_{strike:g}_D{expiry}"
                    intrinsic = max(0.0, spot - strike) if kind == "CALL" else max(0.0, strike - spot)
                    premium = max(0.05, intrinsic + spot * self.volatility[underlying] * math.sqrt(max(1, expiry - self.current_day) / 365) * 0.45)
                    self.prices[symbol] = round(premium, 2)
                    self.volatility[symbol] = min(0.25, self.volatility[underlying] * 4)
                    self.option_contracts[symbol] = {
                        "underlying": underlying, "kind": kind, "strike": strike,
                        "expiry_day": expiry, "multiplier": 100,
                        "exercise_style": "American",
                    }

    def _roll_option_chains(self, game_day: int):
        for underlying in list(self.stock_symbols):
            expiries = sorted({c["expiry_day"] for c in self.option_contracts.values()
                               if c["underlying"] == underlying and c["expiry_day"] >= game_day})
            while len(expiries) < 3:
                next_expiry = (expiries[-1] if expiries else (game_day // 30) * 30) + 30
                self._add_option_chain(underlying, (next_expiry,))
                expiries.append(next_expiry)

    def _list_due_ipos(self, game_day: int):
        for ipo in self.pending_ipos:
            if ipo["listing_day"] == game_day and ipo["symbol"] not in self.listed_ipos:
                symbol = ipo["symbol"]
                self.prices[symbol] = ipo["offer_price"] * self.rng.uniform(0.85, 1.30)
                self.volatility[symbol] = 0.055
                self.stock_symbols.append(symbol)
                self.sectors[symbol] = ipo["sector"]
                self.last_changes[symbol] = 0.0
                self._add_option_chain(symbol, (game_day + 30, game_day + 60, game_day + 90))
                self.listed_ipos.add(symbol)

    def get_option_underlyings(self) -> List[str]:
        return list(self.stock_symbols)

    def get_option_chain(self, underlying: str, game_day: int = None) -> List[str]:
        day = self.current_day if game_day is None else game_day
        return sorted(
            (symbol for symbol, contract in self.option_contracts.items()
             if contract["underlying"] == underlying and contract["expiry_day"] >= day),
            key=lambda s: (self.option_contracts[s]["expiry_day"],
                           self.option_contracts[s]["strike"], self.option_contracts[s]["kind"]),
        )
    
    def _apply_market_events(self, game_day: int):
        """Apply random market events that affect prices."""
        # Market events occur with 10% probability per day
        self.current_event = None
        if self.rng.random() < 0.10:
            event_weights = [
                ("bull_market", 0.25),      # Tech stocks rise
                ("bear_market", 0.20),      # General market decline
                ("rate_hike", 0.15),        # Interest rate increase
                ("rate_cut", 0.10),         # Interest rate decrease
                ("crypto_rally", 0.15),     # Crypto surge
                ("earnings_surprise", 0.10),  # Unexpected earnings
                ("black_swan", 0.05),       # Major negative event
            ]
            
            event_type = self.rng.choices(
                [event[0] for event in event_weights],
                weights=[event[1] for event in event_weights]
            )[0]
            self.current_event = event_type
            self.event_day = game_day
            
            if event_type == "bull_market":
                # Tech stocks and growth stocks rise
                for symbol in ["AAPL", "GOOGL", "MSFT", "NVDA", "META", "TSLA", "NFLX", "QQQ"]:
                    self.prices[symbol] *= self.rng.uniform(1.01, 1.08)
                self.market_trend += 0.1
            
            elif event_type == "bear_market":
                # Most assets decline
                for symbol in self.prices:
                    if self.get_asset_type(symbol) != AssetType.BOND:
                        self.prices[symbol] *= self.rng.uniform(0.92, 0.98)
                self.market_trend -= 0.15
                self.vix_level += self.rng.uniform(5, 15)
            
            elif event_type == "rate_hike":
                # Interest rate increase
                self.interest_rate_trend += 0.0025
                # Bonds gain value
                for symbol in self.prices:
                    if self.get_asset_type(symbol) == AssetType.BOND:
                        self.prices[symbol] *= 1.05
                # Growth stocks fall
                for symbol in ["TSLA", "NFLX", "COIN"]:
                    self.prices[symbol] *= 0.97
            
            elif event_type == "rate_cut":
                # Interest rate decrease
                self.interest_rate_trend = max(0.0, self.interest_rate_trend - 0.0025)
                # Bonds lose value
                for symbol in self.prices:
                    if self.get_asset_type(symbol) == AssetType.BOND:
                        self.prices[symbol] *= 0.95
                # Growth stocks rise
                for symbol in ["TSLA", "NFLX", "COIN", "META"]:
                    self.prices[symbol] *= 1.05
            
            elif event_type == "crypto_rally":
                # Cryptocurrencies surge
                for symbol in ["BTC", "ETH", "SOL", "XRP", "ADA", "COIN"]:
                    self.prices[symbol] *= self.rng.uniform(1.08, 1.20)
            
            elif event_type == "earnings_surprise":
                # Random company has good earnings
                lucky_stock = self.rng.choice(["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"])
                self.prices[lucky_stock] *= self.rng.uniform(1.03, 1.08)
            
            elif event_type == "black_swan":
                # Major negative market event
                self.vix_level += 20
                self.market_trend -= 0.2
                for symbol in ["BTC", "ETH", "TSLA", "COIN", "META"]:
                    self.prices[symbol] *= self.rng.uniform(0.90, 0.95)
    
    def get_price(self, symbol: str) -> float:
        """Get current price of an asset."""
        if symbol not in self.prices:
            raise KeyError(f"Unknown asset symbol: {symbol}")
        return self.prices[symbol]
    
    def get_asset_type(self, symbol: str) -> AssetType:
        """Determine asset type from symbol."""
        crypto_symbols = ["BTC", "ETH", "SOL", "XRP", "ADA"]
        etf_symbols = ["SPY", "QQQ", "IWM", "EEM"]
        forex_symbols = ["EURUSD", "GBPUSD", "JPYUSD", "AUDUSD", "USDCAD", "USDCHF"]
        
        if symbol in crypto_symbols:
            return AssetType.CRYPTOCURRENCY
        elif symbol in self.bond_symbols:
            return AssetType.BOND
        elif symbol in etf_symbols:
            return AssetType.ETF
        elif symbol in forex_symbols:
            return AssetType.FOREX
        elif symbol in self.option_contracts:
            return AssetType.OPTIONS
        else:
            return AssetType.STOCK
    
    def get_available_symbols(self) -> List[str]:
        """Get list of all available trading symbols."""
        return list(self.prices.keys())

    def get_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Return display-ready market data with category and daily change."""
        snapshot = {
            symbol: {
                "price": price,
                "change_percent": self.last_changes.get(symbol, 0.0),
                "asset_type": self.get_asset_type(symbol).value,
            }
            for symbol, price in self.prices.items()
        }
        for symbol, contract in self.option_contracts.items():
            snapshot[symbol].update(contract)
        for symbol, contract in self.bond_contracts.items():
            snapshot[symbol].update(contract)
        return snapshot

    def get_order_book(self, symbol: str, levels: int = 8) -> Dict[str, Any]:
        """Return a stable simulated Level 2 book for a listed stock.

        The book is regenerated from symbol/day/price, so repeated UI redraws do
        not flicker while the next simulated day produces fresh liquidity.
        """
        if symbol not in self.prices:
            raise KeyError(f"Unknown asset symbol: {symbol}")
        if self.get_asset_type(symbol) != AssetType.STOCK:
            raise ValueError("Order book view is available for stocks only")
        levels = max(1, min(20, int(levels)))
        mid = self.prices[symbol]
        tick = 0.01 if mid >= 1 else 0.0001
        spread_pct = 0.0004 + self.volatility.get(symbol, 0.02) * 0.025
        half_spread = max(tick, mid * spread_pct / 2)
        best_bid = math.floor((mid - half_spread) / tick) * tick
        best_ask = math.ceil((mid + half_spread) / tick) * tick
        seed_text = f"{symbol}:{self.current_day}:{mid:.6f}"
        local_rng = random.Random(int(hashlib.sha256(seed_text.encode()).hexdigest()[:16], 16))
        base_size = max(20, int(900 / max(1.0, self.volatility.get(symbol, 0.02) * 100)))

        def side(start: float, direction: int):
            rows = []
            cumulative = 0
            for index in range(levels):
                step = tick * (1 + index + index // 3)
                price = round(start + direction * step * index, 4)
                quantity = local_rng.randint(base_size, base_size * 8) * (1 + index // 2)
                cumulative += quantity
                rows.append({"price": price, "quantity": quantity, "cumulative": cumulative})
            return rows

        real_quote = self.quote_service.latest_quote(symbol)
        if real_quote:
            best_bid, best_ask = real_quote["bid_price"], real_quote["ask_price"]
        bids = side(best_bid, -1)
        asks = side(best_ask, 1)
        if real_quote:
            bids[0]["price"], bids[0]["quantity"] = best_bid, real_quote["bid_size"]
            asks[0]["price"], asks[0]["quantity"] = best_ask, real_quote["ask_size"]
            for rows in (bids, asks):
                cumulative = 0
                for row in rows:
                    cumulative += row["quantity"]
                    row["cumulative"] = cumulative
        return {
            "symbol": symbol,
            "mid_price": (best_bid + best_ask) / 2 if real_quote else mid,
            "spread": best_ask - best_bid,
            "spread_percent": ((best_ask - best_bid) / mid) * 100,
            "bids": bids,
            "asks": asks,
            "day": self.current_day,
            "data_mode": "REAL NBBO + SIMULATED DEPTH" if real_quote else "SIMULATED DEPTH",
            "provider": "Alpaca " + real_quote["feed"] if real_quote else "Investment Simulator",
            "quote_timestamp": real_quote["timestamp"] if real_quote else "",
            "bid_exchange": real_quote["bid_exchange"] if real_quote else "",
            "ask_exchange": real_quote["ask_exchange"] if real_quote else "",
        }

    def apply_news_impact(self, headline: str) -> str:
        """Translate a real headline into a small, transparent market shock."""
        text = headline.lower()
        negative_words = ("fall", "drop", "cuts", "loss", "crisis", "war", "tariff", "inflation", "probe", "recall")
        positive_words = ("rise", "gain", "growth", "record", "deal", "boost", "surge", "profit", "approval")
        direction = -1 if any(word in text for word in negative_words) else 1 if any(word in text for word in positive_words) else 0
        groups = {
            "technology": ("ai", "chip", "technology", "software", "cyber", "apple", "google", "microsoft"),
            "finance": ("bank", "credit", "payments", "finance", "fed", "interest rate"),
            "energy": ("oil", "gas", "energy", "opec"),
            "healthcare": ("health", "drug", "vaccine", "pharma"),
            "consumer": ("retail", "consumer", "amazon", "walmart"),
            "industrials": ("airline", "aircraft", "manufacturing", "boeing"),
            "materials": ("mining", "iron", "copper", "commodity"),
            "crypto": ("bitcoin", "crypto", "ethereum"),
            "forex": ("dollar", "currency", "yen", "euro", "pound"),
        }
        matched = [group for group, words in groups.items() if any(word in text for word in words)]
        if not matched or direction == 0:
            return "No immediate modeled impact"
        targets = []
        for symbol in self.prices:
            asset_type = self.get_asset_type(symbol)
            sector = self.sectors.get(symbol)
            if sector in matched or ("crypto" in matched and asset_type == AssetType.CRYPTOCURRENCY) or ("forex" in matched and asset_type == AssetType.FOREX):
                targets.append(symbol)
        movement = direction * self.rng.uniform(0.003, 0.012)
        for symbol in targets:
            self.prices[symbol] *= 1 + movement
            self.last_changes[symbol] += movement * 100
        label = ", ".join(group.title() for group in matched)
        return f"{label}: {'+' if movement > 0 else ''}{movement * 100:.2f}% ({len(targets)} instruments)"
