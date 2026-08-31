# Investment Simulator - Technical Documentation

## Architecture Overview

Investment Simulator is built with a modular architecture separating game logic, data management, and user interface.

```
┌─────────────────────────────────────────────┐
│           UI Layer (Pygame/CLI)             │
│  Screens, Dialogs, Input Handling           │
├─────────────────────────────────────────────┤
│          Game Engine (core/game.py)         │
│  Game State, Turn Logic, Trade Processing   │
├─────────────────────────────────────────────┤
│  Game Systems (Market, Portfolio, Email)    │
│  Business Logic & Simulation                │
├─────────────────────────────────────────────┤
│       Data Layer (SQLite Database)          │
│  Persistence & Transaction History          │
└─────────────────────────────────────────────┘
```

## Module Structure

### `src/core/` - Core Game Engine

#### `game.py` - Main Game Engine
- **Class: Game**
  - Central orchestrator for game logic
  - Manages game state and transitions
  - Handles all player actions (buy, sell, advance day)

```python
game = Game()
game.start_new_game("PlayerName")
game.buy_asset("AAPL", 10, 150.0)  # Buy 10 shares
game.advance_day()  # Move to next day
```

#### `market.py` - Market Simulator
- **Class: MarketSimulator**
  - Simulates realistic market prices
  - Generates market events and trends
  - Manages volatility and asset correlations

```python
market = MarketSimulator()
market.update_prices(day)  # Update all prices for a day
market.get_price("AAPL")   # Get current price
```

#### `portfolio.py` - Portfolio Management
- **Class: Portfolio**
  - Tracks positions and cash balance
  - Calculates portfolio value and gains/losses
  - Manages buy/sell transactions

```python
portfolio = Portfolio(10000)
portfolio.buy("AAPL", "stock", 10, 150)
portfolio.sell("AAPL", 5, 155)
portfolio.get_total_value()
```

#### `database.py` - Database Management
- **Class: DatabaseManager**
  - SQLite database for game persistence
  - Tables: players, portfolio, transactions, market_prices, emails

```python
db = DatabaseManager()
player_id = db.create_player("PlayerName")
db.add_transaction(player_id, "BUY", "stock", "AAPL", 10, 150, day)
```

#### `email_system.py` - Email & Notifications
- **Class: EmailSystem**
  - Generates daily game emails
  - News, advertisements, scams, IPOs, and reports
  - Email management (read/unread)

```python
email_system = EmailSystem()
emails = email_system.generate_daily_emails(day)
```

#### `save_manager.py` - Save/Load System
- **Class: SaveManager**
  - Saves game state to disk (pickle format)
  - Loads previous games
  - Manages multiple save files

```python
save_manager = SaveManager()
save_manager.save_game(game)
save_manager.load_game(player_id)
```

### `src/ui/` - User Interface

#### `ui_manager.py` - UI Framework
- **Class: UIManager**
  - Pygame display and input handling
  - Screen management system
  - Retro-style components (Button, Panel)

#### `screens.py` - Game Screens
- **MenuScreen** - Main menu
- **TradingScreen** - Primary trading interface
- **PortfolioScreen** - Detailed portfolio view

#### `dialogs.py` - Interactive Dialogs
- **BuyDialog** - Purchase asset dialog
- **SellDialog** - Sell asset dialog
- Text input handling and validation

### `src/models/` - Data Models

#### `data_models.py` - Data Structures
- **Asset** - Asset information (price, change, volume)
- **Order** - Buy/sell order
- **Transaction** - Completed trade record
- **PlayerStats** - Player performance statistics

### `src/utils/` - Utilities

#### `config.py` - Configuration Management
- **ConfigManager** - Load/save game settings
- Supports dot notation for nested config values

```python
config = ConfigManager()
config.get("game.difficulty")
config.set("ui.scale", 1.5)
```

## Game Loop

```
Day 1:
├─ Load game state
├─ Generate daily emails
├─ Player performs trades (max 2)
│  └─ Each trade updates portfolio
└─ Advance to next day
   └─ Update prices
   └─ Increment day counter
   └─ Reset operations counter

Repeat until day 365
```

## Data Models

### Portfolio Structure
```python
{
    "cash": 8500.00,
    "positions": [
        {
            "symbol": "AAPL",
            "quantity": 10,
            "average_buy_price": 150.00,
            "current_price": 155.00,
            "total_value": 1550.00
        }
    ]
}
```

### Market Data
```python
{
    "AAPL": 155.00,
    "GOOGL": 140.50,
    "BTC": 42000.00,
    ...
}
```

## Configuration

Game configuration stored in `config/game_config.json`:

```json
{
  "game": {
    "difficulty": "normal",
    "game_speed": "normal",
    "starting_balance": 10000,
    "game_days": 365,
    "max_operations_per_day": 2
  },
  "ui": {
    "width": 1280,
    "height": 720,
    "fullscreen": false,
    "ui_scale": 1.0
  },
  "features": {
    "enable_scams": true,
    "enable_ipo": true,
    "enable_crypto": true
  }
}
```

## Database Schema

### players table
```sql
CREATE TABLE players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    initial_balance REAL,
    current_balance REAL,
    game_day INTEGER,
    operations_today INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### portfolio table
```sql
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY,
    player_id INTEGER,
    asset_type TEXT,
    symbol TEXT,
    quantity REAL,
    average_buy_price REAL,
    current_price REAL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### transactions table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    player_id INTEGER,
    transaction_type TEXT,  -- BUY or SELL
    asset_type TEXT,
    symbol TEXT,
    quantity REAL,
    price REAL,
    total_amount REAL,
    game_day INTEGER,
    timestamp TIMESTAMP
)
```

## Performance Optimization

- Market price updates use efficient random walk algorithms
- Portfolio calculations cache position values
- Database queries use indexed columns
- UI rendering only updates changed elements

## Extension Points

### Adding New Asset Classes
1. Add symbol to `MarketSimulator.prices`
2. Update volatility in `MarketSimulator.volatility`
3. Define asset type in `get_asset_type()`

### Adding New Game Events
Edit `EmailSystem.generate_daily_emails()` to include new email types or add new market events in `MarketSimulator._apply_market_events()`

### Custom Screens
Extend `Screen` base class and register with `UIManager`

## Testing

Run core logic tests:
```bash
python3 test_game.py
```

Test coverage:
- Portfolio management
- Market simulation
- Email generation
- Game engine integration

## Troubleshooting

### ImportError when running main.py
- Ensure pygame is installed: `pip install -r requirements.txt`
- Check Python version: Requires Python 3.7+

### Database errors
- Delete `data/game.db` to reset database
- Check file permissions in `data/` directory

### Performance issues
- Reduce UI scale in config
- Disable animations if CPU usage high
- Use CLI version instead of GUI

## Future Enhancements

- [ ] Multiplayer leaderboard
- [ ] Achievement system
- [ ] More sophisticated option contracts
- [ ] Tax simulation
- [ ] Margin trading/leverage
- [ ] Short selling capability
- [ ] Realistic options pricing (Black-Scholes)
- [ ] Machine learning price prediction
- [ ] Mobile version
- [ ] Sound effects and music

## License

This project is created for educational purposes as part of USYD COMP9001.
