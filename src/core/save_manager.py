"""
Save/Load system for Investment Simulator
Handles game persistence
"""

import pickle
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


class SaveGame:
    """Represents a saved game."""
    
    def __init__(self, player_id: int, player_name: str, current_day: int,
                 total_value: float, portfolio_data: Dict[str, Any]):
        """Initialize save game."""
        self.player_id = player_id
        self.player_name = player_name
        self.current_day = current_day
        self.total_value = total_value
        self.portfolio_data = portfolio_data
        self.timestamp = datetime.now()
    
    @property
    def filename(self) -> str:
        """Get save file name."""
        return f"save_{self.player_id}.sav"
    
    @property
    def display_name(self) -> str:
        """Get display name for save."""
        return f"{self.player_name} - Day {self.current_day} (${self.total_value:.0f})"


class SaveManager:
    """Manages game saving and loading."""
    
    SAVE_DIR = "data/saves"
    
    def __init__(self):
        """Initialize save manager."""
        os.makedirs(self.SAVE_DIR, exist_ok=True)
    
    def save_game(self, game) -> bool:
        """
        Save the current game state.
        Returns: True if successful
        """
        try:
            # Prepare save data
            save_data = {
                "player_id": game.player_id,
                "player_name": "Player",  # Get from database if needed
                "current_day": game.current_day,
                "total_value": game.portfolio.get_total_value(),
                "portfolio": {
                    "cash": game.portfolio.get_cash(),
                    "positions": [
                        {
                            "symbol": pos.symbol,
                            "asset_type": pos.asset_type,
                            "quantity": pos.quantity,
                            "average_buy_price": pos.average_buy_price,
                            "current_price": pos.current_price
                        }
                        for pos in game.portfolio.get_all_positions()
                    ]
                },
                "market_prices": {
                    symbol: game.market.get_price(symbol)
                    for symbol in game.market.get_available_symbols()
                },
                "timestamp": datetime.now()
            }
            
            # Create save object
            save_game = SaveGame(
                game.player_id,
                "Player",
                game.current_day,
                game.portfolio.get_total_value(),
                save_data["portfolio"]
            )
            
            # Save to file
            filepath = os.path.join(self.SAVE_DIR, save_game.filename)
            with open(filepath, 'wb') as f:
                pickle.dump(save_data, f)
            
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def load_game(self, player_id: int) -> Optional[Dict[str, Any]]:
        """
        Load a saved game.
        Returns: Game data dict or None
        """
        try:
            filepath = os.path.join(self.SAVE_DIR, f"save_{player_id}.sav")
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
            
            return save_data
        except Exception as e:
            print(f"Error loading game: {e}")
            return None
    
    def get_saves(self) -> List[SaveGame]:
        """Get list of all saved games."""
        saves = []
        
        try:
            for filename in os.listdir(self.SAVE_DIR):
                if filename.endswith('.sav'):
                    filepath = os.path.join(self.SAVE_DIR, filename)
                    with open(filepath, 'rb') as f:
                        save_data = pickle.load(f)
                    
                    save = SaveGame(
                        save_data["player_id"],
                        save_data["player_name"],
                        save_data["current_day"],
                        save_data["total_value"],
                        save_data["portfolio"]
                    )
                    saves.append(save)
        except Exception as e:
            print(f"Error listing saves: {e}")
        
        return sorted(saves, key=lambda s: s.timestamp, reverse=True)
    
    def delete_save(self, player_id: int) -> bool:
        """Delete a saved game."""
        try:
            filepath = os.path.join(self.SAVE_DIR, f"save_{player_id}.sav")
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            print(f"Error deleting save: {e}")
        
        return False
    
    def autosave_game(self, game) -> bool:
        """Autosave the game periodically."""
        return self.save_game(game)
