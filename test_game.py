#!/usr/bin/env python3
"""
Test script for Investment Simulator core logic
Tests game engine, market, and portfolio without UI
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pygame
import tempfile

from core.game import Game
from core.portfolio import Portfolio
from core.market import MarketSimulator
from core.email_system import EmailSystem, Email, EmailType
from core.news_service import LiveNewsService
from ui.ui_manager import Button
from ui.dialogs import BuyDialog, InputField


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
    for symbol in ["AAPL", "BTC", "USA3M", "SPY"]:
        print(f"  {symbol}: ${market.get_price(symbol):.2f}")
    
    # Simulate 10 days
    print("\nSimulating 10 days:")
    for day in range(1, 11):
        changes = market.update_prices(day)
        print(f"Day {day}: Market trend={market.market_trend:.3f}, VIX={market.vix_level:.1f}")
        print(f"  AAPL: ${changes['AAPL'][0]:.2f} ({changes['AAPL'][1]:+.2f}%)")
        print(f"  BTC: ${changes['BTC'][0]:.2f} ({changes['BTC'][1]:+.2f}%)")
        print(f"  USA3M: ${changes['USA3M'][0]:.2f} ({changes['USA3M'][1]:+.2f}%)")
    
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
    
    temporary_directory = tempfile.TemporaryDirectory()
    game = Game(db_path=os.path.join(temporary_directory.name, "game.db"), seed=42)
    
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
    temporary_directory.cleanup()


def test_button_click_without_hover():
    """Button clicks should trigger when the mouse is directly over the button."""
    pygame.init()
    button = Button(10, 10, 80, 40, "BUY")
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(40, 30))
    assert button.handle_event(event) is True
    pygame.quit()


def test_game_summary_before_new_game():
    """Game summary should still work before the player creates a new game."""
    game = Game()
    summary = game.get_game_summary()
    assert summary["current_day"] == 1
    assert summary["portfolio"]["total_value"] >= 0
    assert summary["portfolio"]["cash"] >= 0


def test_market_rejects_unknown_symbol():
    market = MarketSimulator(seed=1)
    try:
        market.get_price("NOT_REAL")
        assert False, "unknown symbols must not receive a made-up price"
    except KeyError:
        pass


def test_game_uses_market_quote_and_persists_holdings():
    with tempfile.TemporaryDirectory() as directory:
        db_path = os.path.join(directory, "game.db")
        game = Game(db_path=db_path, seed=7)
        player_id = game.start_new_game("Persistence Test")

        success, _ = game.buy_asset("AAPL", 2, price=0.01)
        assert success
        assert game.portfolio.get_cash() == 10000 - (2 * 150)
        assert game.operations_today == 1

        restored = Game(db_path=db_path, seed=7)
        assert restored.load_game(player_id)
        position = restored.portfolio.get_position("AAPL")
        assert position is not None and position.quantity == 2
        assert restored.operations_today == 1
        assert restored.portfolio.get_total_value() == game.portfolio.get_total_value()


def test_all_requested_product_categories_exist():
    market = MarketSimulator(seed=2)
    categories = {market.get_asset_type(symbol) for symbol in market.get_available_symbols()}
    expected = {
        "stock", "crypto", "bond", "etf", "options", "forex"
    }
    assert expected == {category.value for category in categories}


def test_quantity_field_accepts_numeric_keyboard_input():
    pygame.init()
    field = InputField(0, 0, 200, 40)
    field.active = True
    for character, key in [("1", pygame.K_1), ("2", pygame.K_2), (".", pygame.K_PERIOD), ("5", pygame.K_5)]:
        field.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=character))
    assert field.get_value() == "12.5"
    field.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, unicode="a"))
    assert field.get_value() == "12.5"
    pygame.quit()


def test_trade_dialog_autofocuses_and_stays_open_on_invalid_input():
    pygame.init()
    dialog = BuyDialog(1280, 720, "AAPL", 150, 10000, lambda *args: None)
    dialog.show()
    assert dialog.quantity_input.active
    dialog.quantity_input.set_value("not-a-number")
    assert dialog._try_buy() is False
    assert dialog.is_visible()
    assert dialog.error_message
    pygame.quit()


def test_expanded_market_has_sectors_debt_and_fx():
    market = MarketSimulator(seed=9)
    assert {"JPM", "JNJ", "XOM", "WMT", "BA", "BHP"}.issubset(market.prices)
    assert {"USA3M", "AUS3M", "GBR3M", "JPN3M", "DEU3M"}.issubset(market.prices)
    assert {"AUDUSD", "USDCAD", "USDCHF"}.issubset(market.prices)
    assert market.get_asset_type("AUS3M").value == "bond"
    assert market.get_asset_type("AUDUSD").value == "forex"


def test_news_headline_influences_matching_sector():
    market = MarketSimulator(seed=3)
    before = market.get_price("XOM")
    impact = market.apply_news_impact("Oil prices surge after major production deal")
    assert market.get_price("XOM") > before
    assert "Energy" in impact


def test_live_news_html_is_cleaned_for_display():
    assert LiveNewsService._clean("<p>Stocks &amp; bonds <b>rise</b></p>") == "Stocks & bonds rise"


def test_stock_order_book_has_valid_price_priority_and_depth():
    market = MarketSimulator(seed=12)
    book = market.get_order_book("AAPL", levels=8)
    assert len(book["bids"]) == len(book["asks"]) == 8
    assert all(a["price"] > b["price"] for a, b in zip(book["asks"], book["bids"]))
    assert all(book["bids"][i]["price"] > book["bids"][i + 1]["price"] for i in range(7))
    assert all(book["asks"][i]["price"] < book["asks"][i + 1]["price"] for i in range(7))
    assert all(level["quantity"] > 0 for level in book["bids"] + book["asks"])
    assert market.get_order_book("AAPL") == book


def test_order_book_rejects_non_stock_products():
    market = MarketSimulator(seed=12)
    try:
        market.get_order_book("BTC")
        assert False, "crypto should not expose the stock order book"
    except ValueError:
        pass


def test_real_nbbo_anchors_simulated_order_book_depth():
    market = MarketSimulator(seed=12)
    market.quote_service.latest_quote = lambda symbol: {
        "bid_price": 149.98, "ask_price": 150.02,
        "bid_size": 1200, "ask_size": 900,
        "bid_exchange": "V", "ask_exchange": "Q",
        "timestamp": "2026-01-01T00:00:00Z", "feed": "IEX",
    }
    book = market.get_order_book("AAPL")
    assert book["bids"][0]["price"] == 149.98
    assert book["asks"][0]["price"] == 150.02
    assert book["bids"][0]["quantity"] == 1200
    assert book["data_mode"] == "REAL NBBO + SIMULATED DEPTH"


def test_complete_market_state_survives_save_and_continue():
    with tempfile.TemporaryDirectory() as directory:
        db_path = os.path.join(directory, "save.db")
        game = Game(db_path=db_path, seed=21)
        game.config.setdefault("features", {})["enable_live_news"] = False
        game.start_new_game("Save Test")
        game.buy_asset("AAPL", 3)
        game.market.prices["GOOGL"] = 321.45
        game.market.last_changes["GOOGL"] = 7.25
        assert game.save_game()[0]

        restored = Game(db_path=db_path, seed=99)
        restored.config.setdefault("features", {})["enable_live_news"] = False
        success, _ = restored.load_latest_game()
        assert success
        assert restored.market.get_price("GOOGL") == 321.45
        assert restored.market.last_changes["GOOGL"] == 7.25
        assert restored.portfolio.get_position("AAPL").quantity == 3
        assert restored.operations_today == 1


def test_every_stock_has_call_and_put_options():
    market = MarketSimulator(seed=31)
    assert len(market.stock_symbols) == 20
    assert len(market.option_contracts) == len(market.stock_symbols) * 18
    for stock in market.stock_symbols:
        chain = market.get_option_chain(stock)
        contracts = [market.option_contracts[symbol] for symbol in chain]
        assert len(chain) == 18
        assert {contract["kind"] for contract in contracts} == {"CALL", "PUT"}
        assert {contract["expiry_day"] for contract in contracts} == {30, 60, 90}
        assert len({contract["strike"] for contract in contracts}) == 3
        assert all(contract["multiplier"] == 100 for contract in contracts)


def test_screen_uses_manual_double_click_and_single_click_news():
    pygame.init()
    from ui.screens import TradingScreen
    with tempfile.TemporaryDirectory() as directory:
        game = Game(db_path=os.path.join(directory, "ui.db"), seed=8)
        game.config.setdefault("features", {})["enable_live_news"] = False
        game.start_new_game("Interaction Test")
        screen = TradingScreen(1280, 720, game)

        first = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(100, 225), button=1, timestamp=1000)
        second = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(100, 225), button=1, timestamp=1300)
        screen.handle_event(first)
        assert screen.order_book_dialog is None
        screen.handle_event(second)
        assert screen.order_book_dialog and screen.order_book_dialog.is_visible()
        screen.order_book_dialog.hide()

        email = Email("Detailed market news", "Complete article summary", EmailType.NEWS, 1)
        game.email_system.add_email(email)
        screen.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, pos=(960, 180), button=1, timestamp=2000
        ))
        assert screen.news_dialog and screen.news_dialog.is_visible()
    pygame.quit()


def test_market_category_filter_selects_only_requested_type():
    pygame.init()
    from ui.screens import TradingScreen
    with tempfile.TemporaryDirectory() as directory:
        game = Game(db_path=os.path.join(directory, "filter.db"), seed=8)
        game.config.setdefault("features", {})["enable_live_news"] = False
        game.start_new_game("Filter Test")
        screen = TradingScreen(1280, 720, game)
        # OPTION is the third category tab.
        screen.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, pos=(34 + 2 * 58 + 20, 158), button=1
        ))
        assert screen.active_category == "options"
        assert screen._filtered_symbols()
        assert all(game.market.get_asset_type(s).value == "stock" for s in screen._filtered_symbols())
        # The first level is a stock submenu; clicking a row opens its contracts.
        screen.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, pos=(100, 225), button=1, timestamp=1800
        ))
        assert screen.option_underlying == "AAPL"
        assert all(game.market.get_asset_type(s).value == "options"
                   for s in screen._filtered_symbols())
    pygame.quit()


def test_cash_products_removed_and_all_bonds_are_three_months():
    market = MarketSimulator(seed=40)
    assert "SAVINGS" not in market.prices
    assert "FIXED90" not in market.prices
    assert market.bond_contracts
    assert all(contract["maturity_days"] == 90 for contract in market.bond_contracts.values())
    assert all(contract["term"] == "3 months" for contract in market.bond_contracts.values())


def test_dependent_windows_animate_on_open():
    pygame.init()
    from ui.dialogs import NewsDetailDialog
    email = Email("Animated news", "Details", EmailType.NEWS, 1, url="https://example.com")
    dialog = NewsDetailDialog(1280, 720, email)
    dialog.show()
    assert dialog.animation_progress == 0.0
    dialog.update(0.05)
    assert 0.0 < dialog.animation_progress < 1.0
    assert dialog.draw().get_size() == (1280, 720)
    pygame.quit()


def test_bond_cannot_be_sold_during_ninety_day_lock():
    with tempfile.TemporaryDirectory() as directory:
        game = Game(db_path=os.path.join(directory, "bond.db"), seed=4)
        game.config.setdefault("features", {})["enable_live_news"] = False
        game.start_new_game("Bond Test")
        assert game.buy_asset("USA3M", 10)[0]
        position = game.portfolio.get_position("USA3M")
        assert position.locked_until_day == 91
        success, message = game.sell_asset("USA3M", 1)
        assert not success and "90 more day" in message
        game.current_day = 91
        assert game.sell_asset("USA3M", 1)[0]


def test_option_liquidation_force_closes_at_eighty_percent_loss():
    with tempfile.TemporaryDirectory() as directory:
        game = Game(db_path=os.path.join(directory, "risk.db"), seed=4)
        game.config.setdefault("features", {})["enable_live_news"] = False
        game.start_new_game("Risk Test")
        symbol = game.market.get_option_chain("AAPL")[0]
        assert game.buy_asset(symbol, 1)[0]
        position = game.portfolio.get_position(symbol)
        position.current_price = position.average_buy_price * 0.19
        game.market.prices[symbol] = position.current_price
        events = game._process_option_risk()
        assert events and "80% loss" in events[0]
        assert game.portfolio.get_position(symbol) is None


def test_option_expiry_settles_and_removes_position():
    with tempfile.TemporaryDirectory() as directory:
        game = Game(db_path=os.path.join(directory, "expiry.db"), seed=4)
        game.config.setdefault("features", {})["enable_live_news"] = False
        game.start_new_game("Expiry Test")
        symbol = game.market.get_option_chain("AAPL")[0]
        assert game.buy_asset(symbol, 1)[0]
        game.current_day = game.market.option_contracts[symbol]["expiry_day"]
        events = game._process_option_risk()
        assert events and "expired and settled" in events[0]
        assert game.portfolio.get_position(symbol) is None


def test_option_contract_multiplier_is_charged_and_valued():
    with tempfile.TemporaryDirectory() as directory:
        game = Game(db_path=os.path.join(directory, "multiplier.db"), seed=17)
        game.config.setdefault("features", {})["enable_live_news"] = False
        game.start_new_game("Multiplier Test")
        symbol = game.market.get_option_chain("AAPL")[0]
        premium = game.market.get_price(symbol)
        cash_before = game.portfolio.get_cash()
        assert game.buy_asset(symbol, 1)[0]
        assert abs(game.portfolio.get_cash() - (cash_before - premium * 100)) < 0.01
        assert abs(game.portfolio.get_position(symbol).total_value - premium * 100) < 0.01


def test_interactive_scam_is_hidden_until_resolved():
    with tempfile.TemporaryDirectory() as directory:
        game = Game(db_path=os.path.join(directory, "offer.db"), seed=23)
        game.config.setdefault("features", {})["enable_live_news"] = False
        game.start_new_game("Offer Test")
        offer = Email("Exclusive allocation", "Commit funds for a private result.",
                      EmailType.OFFER, 1, interactive=True, offer_kind="scam",
                      stake=500, resolve_day=4, payout_multiplier=0)
        game.email_system.add_email(offer)
        assert game.accept_offer(offer)[0]
        assert game.portfolio.get_cash() == 9500
        assert not offer.resolved
        game.current_day = 4
        game._resolve_offers()
        assert offer.resolved and game.portfolio.get_cash() == 9500
        assert any("was a scam" in email.content for email in game.email_system.get_all())


def test_ipo_lists_only_on_announced_listing_day():
    market = MarketSimulator(seed=9)
    assert "NOVA" not in market.prices
    market.update_prices(14)
    assert "NOVA" not in market.prices
    market.update_prices(15)
    assert "NOVA" in market.prices
    assert "NOVA" in market.stock_symbols
    assert len(market.get_option_chain("NOVA", 15)) == 18


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
