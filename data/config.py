"""
Configuration settings for Sentinel AI
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
dotenv_path = Path(__file__).parent.parent / '.env'
if (dotenv_path.exists()):
    load_dotenv(dotenv_path)
    logging.info(f"Loaded environment variables from {dotenv_path}")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
REPORTS_DIR = PROJECT_ROOT / 'generated_reports'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Database configuration
DB_PATH = os.environ.get('DB_PATH', str(DATA_DIR / 'sentinel_data.db'))

# API configuration
API_HOST = os.environ.get('API_HOST', '0.0.0.0')
API_PORT = int(os.environ.get('API_PORT', 5000))
API_DEBUG = os.environ.get('API_DEBUG', 'False').lower() == 'true'

# CORS configuration
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')

# OpenAI API key
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
if not OPENAI_API_KEY:
    logging.warning("OPENAI_API_KEY not set in environment variables")

# Logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Report generation
DEFAULT_REPORT_TEMPLATE = os.environ.get('DEFAULT_REPORT_TEMPLATE', 'standard')

# API Keys
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
RANGE_API_KEY = os.getenv("RANGE_API_KEY")
VYBE_API_KEY = os.getenv("VYBE_API_KEY")
RUGCHECK_API_KEY = os.getenv("RUGCHECK_API_KEY")

# API Endpoints
HELIUS_API_URL = "https://mainnet.helius-rpc.com/?api-key=" + HELIUS_API_KEY if HELIUS_API_KEY else ""
RANGE_API_URL = "https://api.range.org/v1"
VYBE_API_URL = "https://mainnet.vybenetwork.com/v1"
RUGCHECK_API_URL = "https://api.rugcheck.xyz/v1"

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sentinel.db")

# Model paths
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ai", "models")

# Default parameters
DEFAULT_TRANSACTION_LIMIT = 100
BATCH_SIZE = 20

def get_helius_headers():
    return {
        "Content-Type": "application/json"
    }

def get_range_headers():
    return {
        "X-API-KEY": RANGE_API_KEY,
        "Content-Type": "application/json"
    }

def get_vybe_headers():
    return {
        "X-API-KEY": VYBE_API_KEY,
        "Content-Type": "application/json"
    }

def get_rugcheck_headers():
    return {
        "Authorization": f"Bearer {RUGCHECK_API_KEY}",
        "Content-Type": "application/json"
    }