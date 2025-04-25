"""
Database operations for token-related data.
"""
import sqlite3
import json
import logging
from datetime import datetime
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.config import DATABASE_URL # Or use a direct path if simpler

logger = logging.getLogger(__name__)

# Determine the database file path from DATABASE_URL or use a default
db_path = DATABASE_URL.replace("sqlite:///", "") if DATABASE_URL.startswith("sqlite:///") else "sentinel_data.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def initialize_token_db():
    """Initializes the necessary tables for token data if they don't exist."""
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        # Create table for RugCheck analysis results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_rugcheck_analysis (
                mint_address TEXT PRIMARY KEY,
                analysis_data TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        # Add other token-related tables here if needed (e.g., token_details, program_details)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_details (
                mint_address TEXT PRIMARY KEY,
                symbol TEXT,
                name TEXT,
                decimals INTEGER,
                total_supply REAL,
                details_json TEXT,
                last_updated TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS program_details (
                program_id TEXT PRIMARY KEY,
                name TEXT,
                details_json TEXT,
                last_updated TEXT NOT NULL
            )
        """)
        conn.commit()
        logger.info("Token database tables initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error initializing token database tables: {e}")
    finally:
        conn.close()

def save_token_rugcheck_data(mint_address, analysis_data):
    """
    Saves or updates RugCheck analysis data for a token in the database.

    Args:
        mint_address (str): The Solana token mint address.
        analysis_data (dict): The analysis data received from RugCheck API.
    """
    conn = get_db_connection()
    if conn is None:
        logger.error(f"Cannot save RugCheck data for {mint_address}: No database connection.")
        return

    try:
        cursor = conn.cursor()
        analysis_json = json.dumps(analysis_data)
        timestamp = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO token_rugcheck_analysis (mint_address, analysis_data, last_updated)
            VALUES (?, ?, ?)
            ON CONFLICT(mint_address) DO UPDATE SET
                analysis_data = excluded.analysis_data,
                last_updated = excluded.last_updated
        """, (mint_address, analysis_json, timestamp))

        conn.commit()
        logger.debug(f"Successfully saved/updated RugCheck data for {mint_address}")
    except sqlite3.Error as e:
        logger.error(f"Database error saving RugCheck data for {mint_address}: {e}")
    except json.JSONDecodeError as e:
         logger.error(f"JSON encoding error saving RugCheck data for {mint_address}: {e}")
    finally:
        conn.close()

def get_token_rugcheck_data(mint_address):
    """
    Retrieves RugCheck analysis data for a token from the database.

    Args:
        mint_address (str): The Solana token mint address.

    Returns:
        dict: The stored analysis data, or None if not found or error occurs.
    """
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT analysis_data, last_updated FROM token_rugcheck_analysis WHERE mint_address = ?", (mint_address,))
        row = cursor.fetchone()

        if row:
            analysis_data = json.loads(row["analysis_data"])
            return {
                "analysis_data": analysis_data,
                "last_updated": row["last_updated"]
            }
        else:
            return None
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving RugCheck data for {mint_address}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error retrieving RugCheck data for {mint_address}: {e}")
        return None
    finally:
        conn.close()

# --- Placeholder functions for Vybe collector dependencies ---

def save_token_data(mint_address, token_data):
    """Placeholder for saving general token data."""
    # Implement saving logic similar to save_token_rugcheck_data
    logger.warning(f"Placeholder: save_token_data called for {mint_address}")
    # Example structure:
    # conn = get_db_connection()
    # ... execute INSERT/UPDATE on token_details table ...
    # conn.close()
    pass

def save_program_data(program_id, program_data):
    """Placeholder for saving program data."""
    # Implement saving logic similar to save_token_rugcheck_data
    logger.warning(f"Placeholder: save_program_data called for {program_id}")
    # Example structure:
    # conn = get_db_connection()
    # ... execute INSERT/UPDATE on program_details table ...
    # conn.close()
    pass

# --- Initialization ---
# Ensure tables are created when the module is imported or used.
initialize_token_db()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Testing token_db operations...")

    # Example usage
    test_mint = "TESTMINTADDRESS12345"
    test_data = {"score": 85, "liquidity": "good", "holders": 1000}

    print(f"Saving data for {test_mint}...")
    save_token_rugcheck_data(test_mint, test_data)

    print(f"Retrieving data for {test_mint}...")
    retrieved = get_token_rugcheck_data(test_mint)

    if retrieved:
        print("Retrieved data:")
        print(json.dumps(retrieved, indent=2))
    else:
        print("Failed to retrieve data.")
