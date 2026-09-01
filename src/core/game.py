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
from .portfolio import Portfolio, Position
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
    
    def __init__(self, db_path: str = "data/game.db", seed: int = None):
        """Initialize the game."""
        self.db = DatabaseManager(db_path)
        self.seed = seed
        self.market = MarketSimulator(seed)
        self.email_system = EmailSystem()
        self.portfolio: Optional[Portfolio] = None
        
        self.player_id: Optional[int] = None
        self.current_day = 1
        self.state = GameState.MENU
        self.operations_today = 0
        self.last_risk_events: List[str] = []
        
        # Load or create config
        self.config = self._load_config()
        game_config = self.config.get("game", self.config)
        self.STARTING_BALANCE = float(game_config.get("starting_balance", 10000))
        self.GAME_DAYS = int(game_config.get("game_days", 365))
        self.MAX_OPERATIONS_PER_DAY = int(game_config.get("max_operations_per_day", 2))
    
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
        self.market = MarketSimulator(self.seed)
        self.email_system = EmailSystem()
        self.player_id = self.db.create_player(player_name, self.STARTING_BALANCE)
        self.portfolio = Portfolio(self.STARTING_BALANCE)
        self.current_day = 1
        self.operations_today = 0
        self.state = GameState.PLAYING
        self.last_risk_events = []
        if self.config.get("features", {}).get("enable_live_news", True):
            self.email_system.live_news.refresh_async()
        
        return self.player_id
    
    def load_game(self, player_id: int) -> bool:
        """Load an existing game."""
        player = self.db.get_player(player_id)
        if not player:
            return False
        
        self.player_id = player_id
        self.current_day = player['game_day']
        self.operations_today = player['operations_today']
        # current_balance stores total net assets, not spendable cash. Restore
        # positions first and derive cash so a loaded game cannot duplicate money.
        rows = self.db.get_portfolio(player_id)
        # Removed products from older saves are liquidated at their last stored
        # value instead of silently reappearing in the current market.
        rows = [row for row in rows if row['symbol'] in self.market.prices]
        holdings_value = sum(
            row['quantity'] * row['current_price'] * (row.get('multiplier') or 1)
            for row in rows
        )
        self.portfolio = Portfolio(
            max(0.0, player['current_balance'] - holdings_value),
            player['initial_balance'],
        )
        for row in rows:
            self.portfolio.positions[row['symbol']] = Position(
                row['asset_type'], row['symbol'], row['quantity'],
                row['average_buy_price'], row['current_price'],
                row.get('opened_day') or 1, row.get('locked_until_day') or 1,
                row.get('expiry_day') or 0, row.get('strike') or 0.0,
                row.get('underlying') or "", row.get('option_kind') or "",
                row.get('multiplier') or 1
            )
            if row['symbol'] in self.market.prices:
                self.market.prices[row['symbol']] = row['current_price']
        for row in reversed(self.db.get_unread_emails(player_id)):
            try:
                email_type = EmailType(row['email_type'])
            except ValueError:
                email_type = EmailType.NEWS
            self.email_system.add_email(Email(
                row['subject'], row['content'], email_type, row['game_day'], False,
                row.get('source') or "Investment Simulator", row.get('url') or "",
                row.get('published') or "", row.get('market_impact') or ""
            ))
        self.state = (GameState.END_GAME if self.db.get_game_result(player_id)
                      else GameState.PLAYING)
        raw_state = self.db.get_game_state(player_id)
        if raw_state:
            try:
                saved = json.loads(raw_state)
                for ipo_symbol in saved.get("listed_ipos", []):
                    ipo = next((item for item in self.market.pending_ipos
                                if item["symbol"] == ipo_symbol), None)
                    if ipo:
                        self.market._list_due_ipos(ipo["listing_day"])
                saved_prices = saved.get("market_prices", {})
                saved_changes = saved.get("last_changes", {})
                self.market.prices.update({
                    symbol: price for symbol, price in saved_prices.items()
                    if symbol in self.market.prices
                })
                self.market.last_changes.update({
                    symbol: change for symbol, change in saved_changes.items()
                    if symbol in self.market.last_changes
                })
                self.market.market_trend = saved.get("market_trend", self.market.market_trend)
                self.market.interest_rate_trend = saved.get("interest_rate", self.market.interest_rate_trend)
                self.market.vix_level = saved.get("vix", self.market.vix_level)
                self.market.current_day = self.current_day
                self.market._roll_option_chains(self.current_day)
                self.portfolio.update_prices(self.market.prices)
                if saved.get("emails"):
                    self.email_system.emails = []
                    for item in saved["emails"]:
                        item = dict(item)
                        try:
                            item["email_type"] = EmailType(item["email_type"])
                            self.email_system.add_email(Email(**item))
                        except (TypeError, ValueError):
                            continue
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
        
        return True

    def load_latest_game(self) -> Tuple[bool, str]:
        player = self.db.get_latest_player()
        if not player:
            return False, "No saved game found"
        if self.load_game(player['id']):
            return True, f"Loaded {player['name']} — day {self.current_day}"
        return False, "Could not load saved game"

    def save_game(self) -> Tuple[bool, str]:
        if self.player_id is None or self.portfolio is None:
            return False, "Start a game before saving"
        self._persist_state()
        return True, f"Game saved on day {self.current_day}"
    
    def advance_day(self) -> Tuple[bool, str]:
        """
        Advance to the next game day.
        Returns: (success, message)
        """
        if self.current_day >= self.GAME_DAYS:
            self.state = GameState.END_GAME
            self._record_game_result()
            self._persist_state()
            return True, f"Game ended! Final balance: ${self.portfolio.get_total_value():.2f}"
        
        # Update market prices
        market_changes = self.market.update_prices(self.current_day)
        
        # Update portfolio prices
        prices = {symbol: self.market.get_price(symbol) 
                 for symbol in self.market.get_available_symbols()}
        self.portfolio.update_prices(prices)
        
        # Generate emails for the day
        daily_emails = self.email_system.generate_daily_emails(self.current_day)
        for ipo in self.market.pending_ipos:
            if ipo["announce_day"] == self.current_day:
                days = ipo["listing_day"] - self.current_day
                daily_emails.insert(0, Email(
                    subject=f"IPO ANNOUNCEMENT: {ipo['name']} ({ipo['symbol']})",
                    content=(f"Expected offer price ${ipo['offer_price']:.2f}. "
                             f"Public trading begins in {days} days on day {ipo['listing_day']}. "
                             "The stock will become tradable only on its listing day."),
                    email_type=EmailType.IPO, game_day=self.current_day,
                    source="IPO Calendar",
                ))
        if self.market.current_event:
            daily_emails.insert(0, Email(
                subject=f"MARKET ALERT: {self.market.current_event.replace('_', ' ').title()}",
                content="A live market event has moved prices. Review affected assets before trading.",
                email_type=EmailType.NEWS,
                game_day=self.current_day,
            ))
        for email in daily_emails:
            if email.email_type == EmailType.NEWS:
                email.market_impact = self.market.apply_news_impact(email.subject)
            self.email_system.add_email(email)
            self.db.add_email(self.player_id, email.subject, email.content,
                              email.email_type.value, email.game_day, email.source,
                              email.url, email.published, email.market_impact)
        # News shocks occur after the baseline daily move and must immediately
        # flow through to net assets.
        self.portfolio.update_prices(self.market.prices)
        self.last_risk_events = self._process_option_risk()
        self._resolve_offers()
        
        # Advance day
        self.current_day += 1
        self.operations_today = 0
        
        # Save to database
        self._persist_state()
        
        # Check if game ended
        message = f"Advanced to day {self.current_day}"
        if self.last_risk_events:
            message += f" — {len(self.last_risk_events)} option position(s) closed"
        return True, message

    def _record_game_result(self):
        """Store the current run once when it reaches the terminal state."""
        if self.player_id is None or self.portfolio is None:
            return
        player = self.db.get_player(self.player_id)
        self.db.record_game_result(
            self.player_id,
            player["name"] if player else "Player",
            self.portfolio.initial_balance,
            self.portfolio.get_total_value(),
            self.current_day,
        )

    def get_rankings(self, limit: int = 100) -> List[Dict]:
        return self.db.get_game_results(limit)

    def get_current_rank(self) -> Optional[int]:
        if self.player_id is None:
            return None
        for rank, result in enumerate(self.db.get_game_results(100000), 1):
            if result["player_id"] == self.player_id:
                return rank
        return None
    
    def can_trade(self) -> Tuple[bool, str]:
        """Check if player can perform a trade today."""
        if self.state == GameState.END_GAME:
            return False, "Game has ended"
        if self.operations_today >= self.MAX_OPERATIONS_PER_DAY:
            return False, f"Maximum {self.MAX_OPERATIONS_PER_DAY} operations per day reached"
        
        if self.current_day > self.GAME_DAYS:
            return False, "Game has ended"
        
        return True, "Can trade"
    
    def buy_asset(self, symbol: str, quantity: float, price: float = None) -> Tuple[bool, str]:
        """
        Buy an asset.
        Returns: (success, message)
        """
        can_trade, msg = self.can_trade()
        if not can_trade:
            return False, msg
        
        if symbol not in self.market.get_available_symbols():
            return False, f"Unknown asset: {symbol}"
        price = self.market.get_price(symbol)  # Market is the authoritative quote.
        asset_type = self.market.get_asset_type(symbol).value
        metadata = {"opened_day": self.current_day}
        if asset_type == "bond":
            metadata["locked_until_day"] = self.current_day + 90
        elif asset_type == "options":
            contract = self.market.option_contracts[symbol]
            metadata.update({
                "expiry_day": contract["expiry_day"], "strike": contract["strike"],
                "underlying": contract["underlying"], "option_kind": contract["kind"],
                "multiplier": contract.get("multiplier", 100),
            })
        success, msg = self.portfolio.buy(symbol, asset_type, quantity, price, metadata)
        
        if success:
            self.operations_today += 1
            self.db.add_transaction(
                self.player_id, "BUY", asset_type, symbol, quantity, price, self.current_day
            )
            self._persist_state()
        
        return success, msg

    def accept_offer(self, email: Email) -> Tuple[bool, str]:
        if not email.interactive or email.accepted:
            return False, "This offer is no longer available"
        can_trade, message = self.can_trade()
        if not can_trade:
            return False, message
        if self.portfolio.get_cash() < email.stake:
            return False, f"Offer requires ${email.stake:.2f} cash"
        self.portfolio.cash -= email.stake
        self.operations_today += 1
        email.accepted = True
        self._persist_state()
        return True, f"Offer accepted for ${email.stake:.2f}; outcome on day {email.resolve_day}"

    def decline_offer(self, email: Email) -> Tuple[bool, str]:
        if not email.interactive or email.accepted:
            return False, "This offer is no longer available"
        email.resolved = True
        self._persist_state()
        return True, "Offer declined"

    def _resolve_offers(self):
        for email in self.email_system.get_all():
            if email.interactive and email.accepted and not email.resolved and self.current_day >= email.resolve_day:
                payout = email.stake * email.payout_multiplier
                self.portfolio.cash += payout
                email.resolved = True
                result = "was a scam; the investment was lost" if email.offer_kind == "scam" else f"returned ${payout:.2f}"
                report = Email(
                    subject=f"OFFER RESULT: {email.subject}",
                    content=f"Your ${email.stake:.2f} commitment {result}.",
                    email_type=EmailType.REPORT, game_day=self.current_day,
                )
                self.email_system.add_email(report)
    
    def sell_asset(self, symbol: str, quantity: float, price: float = None) -> Tuple[bool, str]:
        """
        Sell an asset.
        Returns: (success, message)
        """
        can_trade, msg = self.can_trade()
        if not can_trade:
            return False, msg
        
        if symbol not in self.market.get_available_symbols():
            return False, f"Unknown asset: {symbol}"
        price = self.market.get_price(symbol)
        asset_type = self.market.get_asset_type(symbol).value
        position = self.portfolio.get_position(symbol)
        if position and asset_type == "bond" and self.current_day < position.locked_until_day:
            remaining = position.locked_until_day - self.current_day
            return False, f"Bond is locked for {remaining} more day(s)"
        success, msg = self.portfolio.sell(symbol, quantity, price)
        
        if success:
            self.operations_today += 1
            self.db.add_transaction(
                self.player_id, "SELL", asset_type, symbol, quantity, price, self.current_day
            )
            self._persist_state()
        
        return success, msg

    def _process_option_risk(self) -> List[str]:
        """Force-close options at an 80% loss or settle them at expiry."""
        events = []
        option_positions = [p for p in self.portfolio.get_all_positions() if p.asset_type == "options"]
        for position in option_positions:
            reason = ""
            settlement = position.current_price
            if position.expiry_day and self.current_day >= position.expiry_day:
                underlying_price = self.market.get_price(position.underlying)
                if position.option_kind == "CALL":
                    settlement = max(0.0, underlying_price - position.strike)
                else:
                    settlement = max(0.0, position.strike - underlying_price)
                reason = "expired and settled"
            elif position.current_price <= position.average_buy_price * 0.20:
                reason = "liquidated after an 80% loss"
            if reason:
                closed = self.portfolio.force_close(position.symbol, settlement)
                if closed:
                    self.db.add_transaction(
                        self.player_id, "FORCED_CLOSE", "options", position.symbol,
                        position.quantity, settlement, self.current_day
                    )
                    message = f"{position.symbol} {reason} at ${settlement:.2f}"
                    events.append(message)
                    email = Email(
                        subject=f"RISK ALERT: {position.symbol}", content=message,
                        email_type=EmailType.REPORT, game_day=self.current_day,
                        market_impact="Automatic option risk management",
                    )
                    self.email_system.add_email(email)
                    self.db.add_email(self.player_id, email.subject, email.content,
                                      email.email_type.value, email.game_day,
                                      email.source, email.url, email.published,
                                      email.market_impact)
        return events

    def _persist_state(self):
        """Keep SQLite in sync after every successful state-changing action."""
        if self.player_id is None or self.portfolio is None:
            return
        self.db.update_player_progress(
            self.player_id, self.portfolio.get_total_value(),
            self.current_day, self.operations_today
        )
        self.db.replace_portfolio(self.player_id, self.portfolio.get_all_positions())
        self.db.save_game_state(self.player_id, json.dumps({
            "version": 1,
            "market_prices": self.market.prices,
            "last_changes": self.market.last_changes,
            "market_trend": self.market.market_trend,
            "interest_rate": self.market.interest_rate_trend,
            "vix": self.market.vix_level,
            "listed_ipos": list(self.market.listed_ipos),
            "emails": [
                {
                    "subject": e.subject, "content": e.content,
                    "email_type": e.email_type.value, "game_day": e.game_day,
                    "read": e.read, "source": e.source, "url": e.url,
                    "published": e.published, "market_impact": e.market_impact,
                    "interactive": e.interactive, "offer_kind": e.offer_kind,
                    "stake": e.stake, "accepted": e.accepted,
                    "resolved": e.resolved, "resolve_day": e.resolve_day,
                    "payout_multiplier": e.payout_multiplier,
                } for e in self.email_system.get_all()
            ],
        }))
    
    def get_market_data(self) -> Dict:
        """Get current market data."""
        prices = {}
        for symbol in self.market.get_available_symbols():
            prices[symbol] = self.market.get_price(symbol)
        
        return prices
    
    def get_game_summary(self) -> Dict:
        """Get current game summary."""
        if self.portfolio is None:
            portfolio_summary = {
                "total_value": float(self.STARTING_BALANCE),
                "cash": float(self.STARTING_BALANCE),
                "holdings_value": 0.0,
                "total_cost_basis": 0.0,
                "total_gain": 0.0,
                "total_gain_percent": 0.0,
                "position_count": 0,
            }
        else:
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
        if self.portfolio is None:
            return float(self.STARTING_BALANCE)
        return self.portfolio.get_total_value()
    
    def run(self):
        """Run the game (placeholder for future UI integration)."""
        # This will be implemented with the Pygame UI
        print("Investment Simulator - Game Engine Ready")
        print("Waiting for UI initialization...")
