"""
Database manager for Investment Simulator
Handles SQLite database operations
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


class DatabaseManager:
    """Manages all database operations for the game."""
    
    def __init__(self, db_path: str = "data/game.db"):
        """Initialize the database manager."""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize the database with all required tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Players table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                initial_balance REAL DEFAULT 10000,
                current_balance REAL DEFAULT 10000,
                game_day INTEGER DEFAULT 1,
                operations_today INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Portfolio table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY,
                player_id INTEGER NOT NULL,
                asset_type TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                average_buy_price REAL NOT NULL,
                current_price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                player_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total_amount REAL NOT NULL,
                game_day INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        ''')
        
        # Market prices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_prices (
                id INTEGER PRIMARY KEY,
                asset_type TEXT NOT NULL,
                symbol TEXT NOT NULL,
                game_day INTEGER NOT NULL,
                price REAL NOT NULL,
                change_percent REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Email/News table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY,
                player_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                content TEXT NOT NULL,
                email_type TEXT NOT NULL,
                game_day INTEGER NOT NULL,
                read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_player(self, name: str, initial_balance: float = 10000) -> int:
        """Create a new player and return their ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO players (name, initial_balance, current_balance)
            VALUES (?, ?, ?)
        ''', (name, initial_balance, initial_balance))
        
        conn.commit()
        player_id = cursor.lastrowid
        conn.close()
        
        return player_id
    
    def get_player(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Get player data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM players WHERE id = ?', (player_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_player_balance(self, player_id: int, new_balance: float):
        """Update player's current balance."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE players 
            SET current_balance = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_balance, player_id))
        
        conn.commit()
        conn.close()
    
    def increment_game_day(self, player_id: int):
        """Move to the next game day and reset operations counter."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE players 
            SET game_day = game_day + 1, operations_today = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (player_id,))
        
        conn.commit()
        conn.close()
    
    def get_game_day(self, player_id: int) -> int:
        """Get current game day."""
        player = self.get_player(player_id)
        return player['game_day'] if player else 1
    
    def add_transaction(self, player_id: int, transaction_type: str, asset_type: str, 
                       symbol: str, quantity: float, price: float, game_day: int):
        """Record a transaction."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        total_amount = quantity * price
        
        cursor.execute('''
            INSERT INTO transactions 
            (player_id, transaction_type, asset_type, symbol, quantity, price, total_amount, game_day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (player_id, transaction_type, asset_type, symbol, quantity, price, total_amount, game_day))
        
        conn.commit()
        conn.close()
    
    def get_portfolio(self, player_id: int) -> List[Dict[str, Any]]:
        """Get player's portfolio."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM portfolio WHERE player_id = ?', (player_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def add_email(self, player_id: int, subject: str, content: str, email_type: str, game_day: int):
        """Add an email to player's inbox."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO emails (player_id, subject, content, email_type, game_day)
            VALUES (?, ?, ?, ?, ?)
        ''', (player_id, subject, content, email_type, game_day))
        
        conn.commit()
        conn.close()
    
    def get_unread_emails(self, player_id: int) -> List[Dict[str, Any]]:
        """Get unread emails."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM emails WHERE player_id = ? AND read = 0
            ORDER BY created_at DESC
        ''', (player_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
