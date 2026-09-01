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
                opened_day INTEGER DEFAULT 1,
                locked_until_day INTEGER DEFAULT 1,
                expiry_day INTEGER DEFAULT 0,
                strike REAL DEFAULT 0,
                underlying TEXT DEFAULT '',
                option_kind TEXT DEFAULT '',
                multiplier INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        ''')
        portfolio_columns = {row[1] for row in cursor.execute('PRAGMA table_info(portfolio)')}
        for column, definition in {
            "opened_day": "INTEGER DEFAULT 1", "locked_until_day": "INTEGER DEFAULT 1",
            "expiry_day": "INTEGER DEFAULT 0", "strike": "REAL DEFAULT 0",
            "underlying": "TEXT DEFAULT ''", "option_kind": "TEXT DEFAULT ''",
            "multiplier": "INTEGER DEFAULT 1",
        }.items():
            if column not in portfolio_columns:
                cursor.execute(f"ALTER TABLE portfolio ADD COLUMN {column} {definition}")
        
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
                source TEXT DEFAULT 'Investment Simulator',
                url TEXT DEFAULT '',
                published TEXT DEFAULT '',
                market_impact TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_states (
                player_id INTEGER PRIMARY KEY,
                state_json TEXT NOT NULL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_results (
                id INTEGER PRIMARY KEY,
                player_id INTEGER NOT NULL UNIQUE,
                player_name TEXT NOT NULL,
                initial_balance REAL NOT NULL,
                final_balance REAL NOT NULL,
                return_percent REAL NOT NULL,
                completed_day INTEGER NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        ''')
        # Non-destructive migration for databases created by earlier builds.
        email_columns = {row[1] for row in cursor.execute('PRAGMA table_info(emails)')}
        for column, definition in {
            "source": "TEXT DEFAULT 'Investment Simulator'",
            "url": "TEXT DEFAULT ''",
            "published": "TEXT DEFAULT ''",
            "market_impact": "TEXT DEFAULT ''",
        }.items():
            if column not in email_columns:
                cursor.execute(f"ALTER TABLE emails ADD COLUMN {column} {definition}")
        
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

    def get_latest_player(self) -> Optional[Dict[str, Any]]:
        """Return the most recently updated player save."""
        with self.get_connection() as conn:
            row = conn.execute('SELECT * FROM players ORDER BY updated_at DESC, id DESC LIMIT 1').fetchone()
        return dict(row) if row else None

    def save_game_state(self, player_id: int, state_json: str):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO game_states (player_id, state_json, saved_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(player_id) DO UPDATE SET
                    state_json = excluded.state_json, saved_at = CURRENT_TIMESTAMP
            ''', (player_id, state_json))

    def get_game_state(self, player_id: int) -> Optional[str]:
        with self.get_connection() as conn:
            row = conn.execute('SELECT state_json FROM game_states WHERE player_id = ?',
                               (player_id,)).fetchone()
        return row['state_json'] if row else None

    def record_game_result(self, player_id: int, player_name: str,
                           initial_balance: float, final_balance: float,
                           completed_day: int):
        """Record one immutable leaderboard result for a completed run."""
        return_percent = ((final_balance / initial_balance) - 1) * 100 if initial_balance else 0.0
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR IGNORE INTO game_results
                (player_id, player_name, initial_balance, final_balance,
                 return_percent, completed_day)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (player_id, player_name, initial_balance, final_balance,
                  return_percent, completed_day))

    def get_game_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return completed runs ranked by final assets, then completion time."""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM game_results
                ORDER BY final_balance DESC, completed_at ASC, id ASC
                LIMIT ?
            ''', (limit,)).fetchall()
        return [dict(row) for row in rows]

    def get_game_result(self, player_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM game_results WHERE player_id = ?', (player_id,)
            ).fetchone()
        return dict(row) if row else None
    
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

    def update_player_progress(self, player_id: int, balance: float, game_day: int,
                               operations_today: int):
        """Persist the player's complete lightweight game progress."""
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE players SET current_balance = ?, game_day = ?,
                operations_today = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (balance, game_day, operations_today, player_id))

    def replace_portfolio(self, player_id: int, positions):
        """Atomically replace persisted positions with the in-memory portfolio."""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM portfolio WHERE player_id = ?', (player_id,))
            conn.executemany('''
                INSERT INTO portfolio
                (player_id, asset_type, symbol, quantity, average_buy_price, current_price,
                 opened_day, locked_until_day, expiry_day, strike, underlying, option_kind, multiplier)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                (player_id, p.asset_type, p.symbol, p.quantity,
                 p.average_buy_price, p.current_price, p.opened_day, p.locked_until_day,
                 p.expiry_day, p.strike, p.underlying, p.option_kind, p.multiplier) for p in positions
            ])
    
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
    
    def add_email(self, player_id: int, subject: str, content: str, email_type: str,
                  game_day: int, source: str = "Investment Simulator", url: str = "",
                  published: str = "", market_impact: str = ""):
        """Add an email to player's inbox."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO emails
            (player_id, subject, content, email_type, game_day, source, url, published, market_impact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (player_id, subject, content, email_type, game_day, source, url,
              published, market_impact))
        
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
