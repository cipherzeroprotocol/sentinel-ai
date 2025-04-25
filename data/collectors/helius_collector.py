"""
Helius API data collector
Collects transaction data from Helius API
"""
import json
import logging
import requests
import time
from datetime import datetime
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.config import HELIUS_API_URL, get_helius_headers, DEFAULT_TRANSACTION_LIMIT, BATCH_SIZE
from data.storage.address_db import save_transactions, save_address_data

logger = logging.getLogger(__name__)

def get_account_info(address):
    """
    Get account information from Helius API
    
    Args:
        address (str): Solana address to query
    
    Returns:
        dict: Account information
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [
            address,
            {
                "encoding": "jsonParsed"
            }
        ]
    }
    
    try:
        response = requests.post(HELIUS_API_URL, headers=get_helius_headers(), json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "result" in result and result["result"] is not None:
            logger.info(f"Successfully retrieved account info for {address}")
            return result["result"]
        else:
            logger.warning(f"No account info found for {address}")
            return None
    
    except Exception as e:
        logger.error(f"Error getting account info for {address}: {str(e)}")
        return None

def get_token_balances(address):
    """
    Get token balances for a Solana address using Helius API
    
    Args:
        address (str): Solana address to query
    
    Returns:
        list: List of token balances
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            address,
            {
                "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
            },
            {
                "encoding": "jsonParsed"
            }
        ]
    }
    
    try:
        response = requests.post(HELIUS_API_URL, headers=get_helius_headers(), json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "result" in result and "value" in result["result"]:
            token_accounts = result["result"]["value"]
            logger.info(f"Found {len(token_accounts)} token accounts for {address}")
            return token_accounts
        else:
            logger.warning(f"No token accounts found for {address}")
            return []
    
    except Exception as e:
        logger.error(f"Error getting token balances for {address}: {str(e)}")
        return []

def get_transaction_history(address, limit=DEFAULT_TRANSACTION_LIMIT):
    """
    Get transaction history for a Solana address using Helius API
    
    Args:
        address (str): Solana address to query
        limit (int): Maximum number of transactions to retrieve
    
    Returns:
        list: List of transactions
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [
            address,
            {
                "limit": min(BATCH_SIZE, limit)
            }
        ]
    }
    
    transactions = []
    before = None
    remaining = limit
    
    while remaining > 0:
        if before:
            payload["params"][1]["before"] = before
        
        try:
            response = requests.post(HELIUS_API_URL, headers=get_helius_headers(), json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "result" in result and result["result"]:
                batch = result["result"]
                transactions.extend(batch)
                
                if len(batch) < BATCH_SIZE:
                    # No more transactions
                    break
                
                # Get the signature of the last transaction for pagination
                before = batch[-1]["signature"]
                remaining -= len(batch)
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.2)
            else:
                break
        
        except Exception as e:
            logger.error(f"Error getting transaction history for {address}: {str(e)}")
            break
    
    logger.info(f"Retrieved {len(transactions)} transactions for {address}")
    return transactions

def get_transaction_details(signature):
    """
    Get detailed transaction data for a signature using Helius API
    
    Args:
        signature (str): Transaction signature
    
    Returns:
        dict: Transaction details
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            signature,
            {
                "encoding": "jsonParsed",
                "maxSupportedTransactionVersion": 0
            }
        ]
    }
    
    try:
        response = requests.post(HELIUS_API_URL, headers=get_helius_headers(), json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "result" in result and result["result"]:
            return result["result"]
        else:
            logger.warning(f"No transaction details found for signature {signature}")
            return None
    
    except Exception as e:
        logger.error(f"Error getting transaction details for {signature}: {str(e)}")
        return None

def collect_data(address, limit=DEFAULT_TRANSACTION_LIMIT):
    """
    Collect all relevant data for an address
    
    Args:
        address (str): Solana address to collect data for
        limit (int): Maximum number of transactions to collect
    
    Returns:
        dict: Collected data
    """
    logger.info(f"Collecting data for address {address}")
    
    # Get account info
    account_info = get_account_info(address)
    
    # Get token balances
    token_balances = get_token_balances(address)
    
    # Get transaction history
    transaction_signatures = get_transaction_history(address, limit)
    
    # Get transaction details
    transactions = []
    for sig_data in transaction_signatures:
        signature = sig_data["signature"]
        tx_details = get_transaction_details(signature)
        if tx_details:
            transactions.append(tx_details)
    
    # Save data to database
    address_data = {
        "address": address,
        "account_info": account_info,
        "token_balances": token_balances,
        "collected_at": datetime.now().isoformat()
    }
    
    save_address_data(address, address_data)
    save_transactions(address, transactions)
    
    logger.info(f"Data collection complete for {address}")
    
    return {
        "address": address,
        "account_info": account_info,
        "token_balances": token_balances,
        "transactions": transactions
    }

if __name__ == "__main__":
    # For testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect data from Helius API")
    parser.add_argument("address", help="Solana address to collect data for")
    parser.add_argument("--limit", type=int, default=DEFAULT_TRANSACTION_LIMIT, 
                        help="Maximum number of transactions to collect")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    collect_data(args.address, args.limit)