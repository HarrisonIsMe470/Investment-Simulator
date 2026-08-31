#!/usr/bin/env python3
"""
CLI (Command-line) version of Investment Simulator
Useful for testing and playing without GUI
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.game import Game
from core.save_manager import SaveManager


class CLIGame:
    """CLI interface for Investment Simulator."""
    
    def __init__(self):
        """Initialize CLI game."""
        self.game = Game()
        self.save_manager = SaveManager()
        self.running = True
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def print_header(self, text: str):
        """Print a formatted header."""
        print("\n" + "=" * 60)
        print(text.center(60))
        print("=" * 60)
    
    def print_summary(self):
        """Print game summary."""
        summary = self.game.get_game_summary()
        portfolio = summary['portfolio']
        
        print(f"\n📊 DAY {summary['current_day']}/{365}")
        print(f"💰 Balance: ${portfolio['total_value']:.2f}")
        print(f"💵 Cash: ${portfolio['cash']:.2f}")
        print(f"📈 Holdings: ${portfolio['holdings_value']:.2f}")
        print(f"📊 Gain: ${portfolio['total_gain']:.2f} ({portfolio['total_gain_percent']:.2f}%)")
        print(f"⚡ Operations: {summary['operations_today']}/{summary['max_operations_per_day']}")
        print(f"📧 Unread Emails: {summary['unread_emails']}")
    
    def show_portfolio(self):
        """Show detailed portfolio."""
        self.clear_screen()
        self.print_header("PORTFOLIO")
        
        positions = self.game.portfolio.get_all_positions()
        
        if not positions:
            print("No positions held.")
        else:
            print(f"\n{'Symbol':<10} {'Qty':<10} {'Price':<12} {'Value':<12} {'Gain %':<10}")
            print("-" * 60)
            
            for pos in positions:
                print(f"{pos.symbol:<10} {pos.quantity:<10.2f} ${pos.current_price:<11.2f} "
                      f"${pos.total_value:<11.2f} {pos.unrealized_gain_percent:>9.2f}%")
        
        print(f"\nCash: ${self.game.portfolio.get_cash():.2f}")
        print(f"Total Value: ${self.game.portfolio.get_total_value():.2f}")
    
    def show_market(self):
        """Show market data."""
        self.clear_screen()
        self.print_header("MARKET DATA")
        
        market_data = self.game.get_market_data()
        symbols = sorted(market_data.keys())
        
        print(f"\n{'Symbol':<12} {'Price':<12} {'Volume':<12}")
        print("-" * 40)
        
        for symbol in symbols:
            price = market_data[symbol]
            print(f"{symbol:<12} ${price:<11.2f}")
    
    def show_emails(self):
        """Show unread emails."""
        self.clear_screen()
        self.print_header("EMAILS")
        
        emails = self.game.email_system.get_unread()
        
        if not emails:
            print("No unread emails.")
            return
        
        for i, email in enumerate(emails, 1):
            print(f"\n[{i}] [{email.email_type.value.upper()}] {email.subject}")
            print(f"    {email.content[:80]}...")
    
    def buy_asset(self):
        """Buy an asset."""
        can_trade, msg = self.game.can_trade()
        if not can_trade:
            print(f"❌ {msg}")
            return
        
        market_data = self.game.get_market_data()
        symbols = sorted(market_data.keys())
        
        print("\nAvailable symbols:")
        for i, symbol in enumerate(symbols, 1):
            print(f"  {i}. {symbol}: ${market_data[symbol]:.2f}")
        
        try:
            choice = int(input("\nEnter symbol number (0 to cancel): "))
            if choice == 0:
                return
            
            symbol = symbols[choice - 1]
            price = market_data[symbol]
            
            quantity = float(input(f"Enter quantity to buy: "))
            
            success, msg = self.game.buy_asset(symbol, quantity, price)
            print(f"{'✓' if success else '❌'} {msg}")
        
        except (ValueError, IndexError):
            print("Invalid input.")
    
    def sell_asset(self):
        """Sell an asset."""
        can_trade, msg = self.game.can_trade()
        if not can_trade:
            print(f"❌ {msg}")
            return
        
        positions = self.game.portfolio.get_all_positions()
        
        if not positions:
            print("No positions to sell.")
            return
        
        print("\nYour positions:")
        for i, pos in enumerate(positions, 1):
            print(f"  {i}. {pos.symbol}: {pos.quantity} shares @ ${pos.current_price:.2f}")
        
        try:
            choice = int(input("\nEnter position number (0 to cancel): "))
            if choice == 0:
                return
            
            position = positions[choice - 1]
            quantity = float(input(f"Enter quantity to sell (max {position.quantity}): "))
            
            success, msg = self.game.sell_asset(position.symbol, quantity, position.current_price)
            print(f"{'✓' if success else '❌'} {msg}")
        
        except (ValueError, IndexError):
            print("Invalid input.")
    
    def next_day(self):
        """Advance to next day."""
        if self.game.current_day >= 365:
            print("Game has ended!")
            return
        
        success, msg = self.game.advance_day()
        if success:
            print(f"✓ {msg}")
            
            # Show new emails
            emails = self.game.email_system.get_unread()
            if emails:
                print(f"\n📧 Received {len(emails)} new emails!")
        else:
            print(f"❌ {msg}")
    
    def show_menu(self):
        """Show main menu."""
        self.clear_screen()
        self.print_header("INVESTMENT SIMULATOR")
        self.print_summary()
        
        print("\n" + "=" * 60)
        print("1. Buy Asset")
        print("2. Sell Asset")
        print("3. View Portfolio")
        print("4. View Market")
        print("5. Check Emails")
        print("6. Next Day")
        print("7. Save Game")
        print("8. Exit")
        print("=" * 60)
    
    def run(self):
        """Run the CLI game."""
        # Start new game
        self.game.start_new_game("CLIPlayer")
        
        while self.running and self.game.current_day <= 365:
            self.show_menu()
            
            try:
                choice = input("\nEnter your choice (1-8): ").strip()
                
                if choice == "1":
                    self.buy_asset()
                elif choice == "2":
                    self.sell_asset()
                elif choice == "3":
                    self.show_portfolio()
                elif choice == "4":
                    self.show_market()
                elif choice == "5":
                    self.show_emails()
                elif choice == "6":
                    self.next_day()
                elif choice == "7":
                    if self.save_manager.save_game(self.game):
                        print("✓ Game saved!")
                    else:
                        print("❌ Failed to save game.")
                elif choice == "8":
                    print("Thanks for playing!")
                    self.running = False
                else:
                    print("Invalid choice.")
                
                if choice in ["1", "2", "3", "4", "5"]:
                    input("\nPress Enter to continue...")
            
            except KeyboardInterrupt:
                print("\n\nGame interrupted.")
                self.running = False
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")
        
        # Game ended
        if self.game.current_day > 365:
            self.clear_screen()
            self.print_header("GAME COMPLETE")
            
            summary = self.game.get_game_summary()
            portfolio = summary['portfolio']
            
            print(f"\n🏆 Final Portfolio Value: ${portfolio['total_value']:.2f}")
            print(f"💰 Total Gain: ${portfolio['total_gain']:.2f} ({portfolio['total_gain_percent']:.2f}%)")
            print(f"\nThanks for playing Investment Simulator!")


if __name__ == "__main__":
    cli = CLIGame()
    cli.run()
