# Investment Simulator

Investment Simulator is a one-year portfolio management game built with Python
and Pygame. The player starts with $10,000, may perform at most two operations
per simulated day, and tries to finish day 365 with the highest possible net
assets.

The market is a game simulation rather than a brokerage or trading platform.
Prices react to seeded random movement, volatility, economic events, and news.

## Current Features

### Markets and products

- 20 initial stocks across technology, finance, healthcare, energy, consumer,
  media, industrial, utility, transport, automotive, and materials sectors
- BTC, ETH, SOL, XRP, and ADA cryptocurrency
- USA, Australia, UK, Japan, and Germany three-month sovereign bonds
- SPY, QQQ, IWM, and EEM ETFs
- EUR/USD, GBP/USD, JPY/USD, AUD/USD, USD/CAD, and USD/CHF forex pairs
- Calls and puts for every listed stock
- No cash-category investment products; uninvested money remains portfolio cash

### Options

The Options category first displays a submenu of underlying stocks. Selecting a
stock opens its option chain.

- Calls and puts at three strikes around the underlying price
- Rolling 30-, 60-, and 90-day expiration dates
- American-style contract metadata
- 100 underlying shares per contract
- Premium, portfolio value, sale proceeds, and expiration settlement all use
  the contract multiplier
- Automatic settlement at expiration
- Automatic forced close after an 80% loss

This is a simplified educational model. It does not implement option writing,
margin accounts, early exercise, assignment, spreads, or a full pricing model.

### Bonds

All sovereign bonds have a three-month term. A purchased bond cannot be sold
until its 90-day holding lock has elapsed.

### IPO calendar

Scheduled IPO announcements identify the company, expected offer price, listing
day, and number of days remaining. The stock is unavailable before that date
and is added to the stock market on its listing day. Its option chain is created
after listing.

### News and private offers

- Live headlines are fetched in the background from BBC Business, BBC
  Technology, and the US Federal Reserve RSS feeds
- Simulated headlines are used when live feeds are unavailable
- News headlines can apply modeled impacts to matching market sectors
- Selecting a news row opens a dependent detail window
- Private offers may be accepted or declined
- An accepted offer does not reveal whether it is legitimate or a scam until
  its resolution day
- Accepting an offer commits cash and consumes one of the day's two operations

Set `features.enable_live_news` to `false` in
`config/game_config.json` for fully offline play.

### Stock order books

Double-click a stock row to open its eight-level bid/ask order book.

By default, the complete book is simulated. If Alpaca credentials are present,
the best bid, best ask, and their displayed sizes are anchored to Alpaca's
latest IEX quote; deeper levels remain simulated. The window labels the result
as either `SIMULATED DEPTH` or `REAL NBBO + SIMULATED DEPTH`.

```bash
export ALPACA_API_KEY_ID="your-key-id"
export ALPACA_API_SECRET_KEY="your-secret-key"
python3 main.py
```

### Interface and persistence

- Metro-inspired financial dashboard at a default resolution of 1280 x 720
- Readable system fonts with configurable scaling
- Animated popup windows, selection pulses, status indicators, market flashes,
  and terminal-style background motion
- Category filters for stocks, options, crypto, bonds, ETFs, and forex
- Editable keyboard quantity fields in buy and sell dialogs
- Automatic persistence after state-changing actions
- Manual `SAVE GAME` control and `CONTINUE` from the main menu
- SQLite storage for players, positions, transactions, emails, and game state

Saved state includes cash, holdings, contract metadata, current day, operations
used, market prices, market conditions, listed IPOs, and interactive-offer state.

## Game Rules

1. Start with $10,000.
2. Perform no more than two trades or accepted offers per day.
3. Advance through 365 simulated days.
4. Evaluate news, risk, liquidity, and time to expiration.
5. Maximize total net assets: cash plus the current value of all positions.

## Installation

Python 3 and pip are required.

```bash
python3 -m pip install -r requirements.txt
```

## Running

Run commands from the project root:

```bash
python3 main.py
```

The optional terminal version can be started with:

```bash
python3 cli_game.py
```

## Configuration

Runtime settings are stored in `config/game_config.json`.

```json
{
  "game": {
    "starting_balance": 10000,
    "game_days": 365,
    "max_operations_per_day": 2
  },
  "ui": {
    "width": 1280,
    "height": 720,
    "font_scale": 1.15
  },
  "features": {
    "enable_live_news": true
  }
}
```

## Project Structure

```text
|-- main.py                        # Pygame entry point
|-- cli_game.py                    # Optional terminal interface
|-- config/
|   `-- game_config.json           # Runtime configuration
|-- data/
|   `-- game.db                    # SQLite save database
|-- src/
|   |-- core/
|   |   |-- game.py                # Game loop and rules
|   |   |-- market.py              # Products, prices, events, IPOs, options
|   |   |-- portfolio.py           # Cash, positions, valuation, trading
|   |   |-- database.py            # SQLite persistence
|   |   |-- email_system.py        # News, offers, and reports
|   |   |-- news_service.py        # RSS news reader
|   |   `-- market_data_service.py # Optional Alpaca quote adapter
|   |-- ui/
|   |   |-- screens.py             # Menu, trading, portfolio screens
|   |   |-- dialogs.py             # Trade, news, and order-book windows
|   |   `-- ui_manager.py          # Pygame UI primitives and loop
|   |-- models/
|   `-- utils/
|       `-- config.py              # JSON configuration helper
|-- requirements.txt
`-- test_game.py                   # Core and UI regression tests
```

## Testing

With `pytest` installed:

```bash
SDL_VIDEODRIVER=dummy python3 -m pytest -q
```

The dummy video driver allows Pygame UI tests to run without opening a window.

## Technology

- Python
- Pygame
- SQLite
- JSON configuration
- Python standard-library random simulation, RSS, and HTTP clients
- Git version control

## Disclaimer

This project is an educational simulation. Its prices, option values, order-book
depth, news impacts, opportunities, and scams are simplified game mechanics and
must not be treated as investment advice or executable market data.
