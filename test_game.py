#!/usr/bin/env python3
"""
Test script for Investment Simulator core logic
Tests game engine, market, and portfolio without UI
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.game import Game
from core.portfolio import Portfolio
from core.market import MarketSimulator
from core.email_system import EmailSystem


def test_portfolio():
    """Test portfolio management."""
    print("=" * 60)
    print("TESTING PORTFOLIO")
    print("=" * 60)
    
    portfolio = Portfolio(10000)
    print(f"Initial balance: ${portfolio.get_cash():.2f}")
    
    # Test buy
    success, msg = portfolio.buy("AAPL", "stock", 10, 150)
    print(f"Buy: {msg}")
    print(f"Cash after buy: ${portfolio.get_cash():.2f}")
    print(f"Total value: ${portfolio.get_total_value():.2f}")
    
    # Test another buy
    success, msg = portfolio.buy("BTC", "crypto", 0.5, 42000)
    print(f"Buy: {msg}")
    print(f"Total value: ${portfolio.get_total_value():.2f}")
    
    # Test partial sell
    success, msg = portfolio.sell("AAPL", 5, 155)
    print(f"Sell: {msg}")
    print(f"Total value: ${portfolio.get_total_value():.2f}")
    
    # Print summary
    summary = portfolio.get_portfolio_summary()
    print("\nPortfolio Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print()


def test_market():
    """Test market simulator."""
    print("=" * 60)
    print("TESTING MARKET SIMULATOR")
    print("=" * 60)
    
    market = MarketSimulator(seed=42)
    
    print("Initial prices:")
    for symbol in ["AAPL", "BTC", "US10Y", "SPY"]:
        print(f"  {symbol}: ${market.get_price(symbol):.2f}")
    
    # Simulate 10 days
    print("\nSimulating 10 days:")
    for day in range(1, 11):
        changes = market.update_prices(day)
        print(f"Day {day}: Market trend={market.market_trend:.3f}, VIX={market.vix_level:.1f}")
        print(f"  AAPL: ${changes['AAPL'][0]:.2f} ({changes['AAPL'][1]:+.2f}%)")
        print(f"  BTC: ${changes['BTC'][0]:.2f} ({changes['BTC'][1]:+.2f}%)")
        print(f"  US10Y: ${changes['US10Y'][0]:.2f} ({changes['US10Y'][1]:+.2f}%)")
    
    print()


def test_email_system():
    """Test email system."""
    print("=" * 60)
    print("TESTING EMAIL SYSTEM")
    print("=" * 60)
    
    email_system = EmailSystem()
    
    # Generate emails for different days
    for day in [1, 10, 30, 100, 200, 365]:
        emails = email_system.generate_daily_emails(day)
        print(f"Day {day}: Generated {len(emails)} emails")
        for email in emails:
            print(f"  [{email.email_type.value.upper()}] {email.subject}")
    
    print()


def test_game_engine():
    """Test game engine integration."""
    print("=" * 60)
    print("TESTING GAME ENGINE")
    print("=" * 60)
    
    game = Game()
    
    # Start new game
    player_id = game.start_new_game("TestPlayer")
    print(f"Started game with player_id={player_id}")
    
    summary = game.get_game_summary()
    print(f"Initial portfolio: ${summary['portfolio']['total_value']:.2f}")
    
    # Test trading
    print("\nTesting trades:")
    success, msg = game.buy_asset("AAPL", 10, game.market.get_price("AAPL"))
    print(f"Buy: {msg}")
    
    success, msg = game.buy_asset("BTC", 0.1, game.market.get_price("BTC"))
    print(f"Buy: {msg}")
    
    summary = game.get_game_summary()
    print(f"Portfolio value after buys: ${summary['portfolio']['total_value']:.2f}")
    print(f"Operations used: {summary['operations_today']}/{summary['max_operations_per_day']}")
    
    # Try to exceed operation limit
    success, msg = game.buy_asset("MSFT", 5, game.market.get_price("MSFT"))
    print(f"Buy (should fail): {msg}")
    
    # Advance day
    print("\nAdvancing to next day:")
    success, msg = game.advance_day()
    print(f"Day advance: {msg}")
    
    summary = game.get_game_summary()
    print(f"Current day: {summary['current_day']}")
    print(f"Operations today: {summary['operations_today']}")
    print(f"Unread emails: {summary['unread_emails']}")
    
    print()


if __name__ == "__main__":
    try:
        test_portfolio()
        test_market()
        test_email_system()
        test_game_engine()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
