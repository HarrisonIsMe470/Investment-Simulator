"""
Game configuration handler
"""

import json
import os
from typing import Dict, Any


class ConfigManager:
    """Manages game configuration."""
    
    DEFAULT_CONFIG = {
        "game": {
            "difficulty": "normal",  # easy, normal, hard
            "game_speed": "normal",   # slow, normal, fast
            "starting_balance": 10000,
            "game_days": 365,
            "max_operations_per_day": 2
        },
        "ui": {
            "width": 1280,
            "height": 720,
            "fullscreen": False,
            "ui_scale": 1.0,
            "font_scale": 1.15
        },
        "features": {
            "enable_scams": True,
            "enable_ipo": True,
            "enable_crypto": True,
            "enable_options": True,
            "enable_forex": True,
            "enable_live_news": True
        },
        "audio": {
            "master_volume": 0.5,
            "music_volume": 0.3,
            "sound_enabled": False
        },
        "graphics": {
            "animations_enabled": True,
            "pixel_art_mode": True,
            "color_blind_mode": False
        }
    }
    
    def __init__(self, config_path: str = "config/game_config.json"):
        """Initialize configuration manager."""
        self.config_path = config_path
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        
        # Create default config
        self.save_config(self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation (e.g., 'game.difficulty')."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot notation."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.config.get(section, {})
