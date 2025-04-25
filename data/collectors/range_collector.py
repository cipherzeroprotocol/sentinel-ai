"""
Range API data collector
Collects data from Range API for security analysis
"""
import logging
import requests
import time
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.config import RANGE_API_URL, get_range_headers, DEFAULT_TRANSACTION_LIMIT, BATCH_SIZE
from data.storage.address_db import save_risk_data, save_counterparties

logger = logging.getLogger(__name__)

def get_address_info(address, network="solana"):
    """
    Get address information from Range API
    
    Args:
        address (str): Address to query
        network (str): Blockchain network (default: solana)
    
    Returns:
        dict: Address information
    """
    url = f"{RANGE_API_URL}/address"
    params = {
        "network": network,
        "address": address
    }
    
    try:
        response = requests.get(url, headers=get_range_headers(), params=params)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully retrieved address info for {address}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting address info for {address}: {str(e)}")
        return None

def get_address_risk_score(address, network="solana"):
    """
    Get risk score for an address from Range API
    
    Args:
        address (str): Address to query
        network (str): Blockchain network (default: solana)
    
    Returns:
        dict: Risk score data
    """
    url = f"{RANGE_API_URL}/risk/address"
    params = {
        "address": address,
        "network": network
    }
    
    try:
        response = requests.get(url, headers=get_range_headers(), params=params)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully retrieved risk score for {address}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting risk score for {address}: {str(e)}")
        return None

def get_address_counterparties(address, network="solana", limit=DEFAULT_TRANSACTION_LIMIT):
    """
    Get counterparties for an address from Range API
    
    Args:
        address (str): Address to query
        network (str): Blockchain network (default: solana)
        limit (int): Maximum number of counterparties to retrieve
    
    Returns:
        dict: Counterparties data
    """
    url = f"{RANGE_API_URL}/address/counterparties"
    params = {
        "address": address,
        "network": network,
        "limit": min(limit, 100),  # API limit
        "include_labels": "true"
    }
    
    try:
        response = requests.get(url, headers=get_range_headers(), params=params)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully retrieved {len(result.get('counterparties', []))} counterparties for {address}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting counterparties for {address}: {str(e)}")
        return None

def get_address_transactions(address, network="solana", limit=DEFAULT_TRANSACTION_LIMIT):
    """
    Get transactions for an address from Range API
    
    Args:
        address (str): Address to query
        network (str): Blockchain network (default: solana)
        limit (int): Maximum number of transactions to retrieve
    
    Returns:
        list: Transactions data
    """
    url = f"{RANGE_API_URL}/address/transactions"
    params = {
        "address": address,
        "network": network,
        "limit": min(BATCH_SIZE, limit),
        "include_metadata": "true"
    }
    
    transactions = []
    offset = 0
    remaining = limit
    
    while remaining > 0:
        params["offset"] = offset
        
        try:
            response = requests.get(url, headers=get_range_headers(), params=params)
            response.raise_for_status()
            result = response.json()
            
            if "transactions" in result and result["transactions"]:
                batch = result["transactions"]
                transactions.extend(batch)
                
                if len(batch) < BATCH_SIZE:
                    # No more transactions
                    break
                
                offset += len(batch)
                remaining -= len(batch)
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.2)
            else:
                break
        
        except Exception as e:
            logger.error(f"Error getting transactions for {address}: {str(e)}")
            break
    
    logger.info(f"Retrieved {len(transactions)} transactions from Range API for {address}")
    return transactions

def get_transaction_risk_score(tx_hash, network="solana"):
    """
    Get risk score for a transaction from Range API
    
    Args:
        tx_hash (str): Transaction hash
        network (str): Blockchain network (default: solana)
    
    Returns:
        dict: Risk score data
    """
    url = f"{RANGE_API_URL}/risk/transaction"
    params = {
        "hash": tx_hash,
        "network": network
    }
    
    try:
        response = requests.get(url, headers=get_range_headers(), params=params)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully retrieved risk score for transaction {tx_hash}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting risk score for transaction {tx_hash}: {str(e)}")
        return None

def collect_data(address, limit=DEFAULT_TRANSACTION_LIMIT, network="solana"):
    """
    Collect all relevant data for an address from Range API
    
    Args:
        address (str): Address to collect data for
        limit (int): Maximum number of transactions to collect
        network (str): Blockchain network (default: solana)
    
    Returns:
        dict: Collected data
    """
    logger.info(f"Collecting Range API data for address {address}")
    
    # Get address info
    address_info = get_address_info(address, network)
    
    # Get risk score
    risk_score = get_address_risk_score(address, network)
    
    # Get counterparties
    counterparties = get_address_counterparties(address, network, limit)
    
    # Get transactions (optional - can be expensive for API quota)
    # transactions = get_address_transactions(address, network, limit)
    
    # Save data to database
    save_risk_data(address, risk_score)
    if counterparties and "counterparties" in counterparties:
        save_counterparties(address, counterparties["counterparties"])
    
    logger.info(f"Range API data collection complete for {address}")
    
    return {
        "address": address,
        "address_info": address_info,
        "risk_score": risk_score,
        "counterparties": counterparties,
        # "transactions": transactions,  # Commented out to save API quota
        "collected_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # For testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect data from Range API")
    parser.add_argument("address", help="Address to collect data for")
    parser.add_argument("--limit", type=int, default=DEFAULT_TRANSACTION_LIMIT,
                        help="Maximum number of transactions to collect")
    parser.add_argument("--network", default="solana", help="Blockchain network")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    collect_data(args.address, args.limit, args.network)