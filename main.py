#!/usr/bin/env python3
"""
Investment Simulator - Main Entry Point
A one-year investment simulation game
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pygame
from core.game import Game
from ui.ui_manager import UIManager
from ui.screens import MenuScreen, TradingScreen, PortfolioScreen
from utils.config import ConfigManager


def main():
    """Initialize and run the game."""
    # Load configuration
    config = ConfigManager()
    
    # Initialize game engine
    game = Game()
    
    # Initialize UI
    ui_width = config.get("ui.width", 1280)
    ui_height = config.get("ui.height", 720)
    ui_manager = UIManager(ui_width, ui_height, "Investment Simulator")
    
    # Register screens
    menu_screen = MenuScreen(ui_width, ui_height, game)
    trading_screen = TradingScreen(ui_width, ui_height, game)
    portfolio_screen = PortfolioScreen(ui_width, ui_height, game)
    
    ui_manager.register_screen("menu", menu_screen)
    ui_manager.register_screen("trading", trading_screen)
    ui_manager.register_screen("portfolio", portfolio_screen)
    
    # Start with menu
    ui_manager.set_screen("menu")
    
    # Run game
    try:
        ui_manager.run()
    except KeyboardInterrupt:
        print("Game interrupted by user")
    finally:
        print("Investment Simulator closed")


if __name__ == "__main__":
    main()
