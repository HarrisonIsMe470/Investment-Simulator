# Investment Simulator

A one-year investment simulation game where players manage $10,000 across various financial instruments including stocks, cryptocurrency, bonds, and more.

## Features

- **Investment Products**: Stocks, Cryptocurrency, Government Bonds, Fixed Deposits, High-Interest Savings, ETFs, Options, Forex Trading
- **Dynamic Market**: Real-time market fluctuations based on economic events
- **Email System**: Financial news, advertisements, and investment reports
- **Limited Actions**: Maximum 2 operations per day
- **Retro UI**: Pixel-art style financial interface

## Technical Stack

- **GUI**: Pygame
- **Database**: SQLite
- **Configuration**: JSON
- **Version Control**: Git

## Installation

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python main.py
```

## Project Structure

```
├── src/
│   ├── core/           # Game engine and logic
│   ├── ui/             # GUI components
│   ├── models/         # Data models
│   └── utils/          # Utility functions
├── assets/
│   ├── sprites/        # Game graphics
│   ├── sounds/         # Audio files
│   └── fonts/          # Game fonts
├── config/             # Configuration files
└── data/               # Database and save files
```

## Game Rules

1. Start with $10,000
2. Maximum 2 operations per day
3. Simulate 365 days (1 year)
4. Objective: Maximize total net assets
5. Navigate risks and opportunities through market volatility and events

## Authors

USYD COMP9001 Final Project
