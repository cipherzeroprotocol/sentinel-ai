"""
Vybe API data collector
Collects data from Vybe API for token and account analysis
"""
import logging
import requests
import time
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.config import VYBE_API_URL, get_vybe_headers, DEFAULT_TRANSACTION_LIMIT, BATCH_SIZE
from data.storage.address_db import save_token_data, save_program_data

logger = logging.getLogger(__name__)

def get_token_balance(address):
    """
    Get token balances for an address from Vybe API
    
    Args:
        address (str): Solana address to query
    
    Returns:
        dict: Token balance data
    """
    url = f"{VYBE_API_URL}/account/token-balance/{address}"
    params = {
        "includeNoPriceBalance": "true"
    }
    
    try:
        response = requests.get(url, headers=get_vybe_headers(), params=params)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully retrieved token balances for {address}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting token balances for {address}: {str(e)}")
        return None

def get_token_balance_timeseries(address, days=30):
    """
    Get token balance time series data for an address from Vybe API
    
    Args:
        address (str): Solana address to query
        days (int): Number of days to retrieve data for
    
    Returns:
        dict: Token balance time series data
    """
    url = f"{VYBE_API_URL}/account/token-balance-ts/{address}"
    params = {
        "days": days
    }
    
    try:
        response = requests.get(url, headers=get_vybe_headers(), params=params)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully retrieved token balance time series for {address}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting token balance time series for {address}: {str(e)}")
        return None

def get_token_transfers(address=None, mint_address=None, limit=DEFAULT_TRANSACTION_LIMIT):
    """
    Get token transfers from Vybe API
    
    Args:
        address (str, optional): Address to query transfers for
        mint_address (str, optional): Token mint address to query transfers for
        limit (int): Maximum number of transfers to retrieve
    
    Returns:
        dict: Token transfers data
    """
    url = f"{VYBE_API_URL}/token/transfers"
    params = {
        "limit": min(BATCH_SIZE, limit)
    }
    
    if address:
        params["walletAddress"] = address
    
    if mint_address:
        params["mintAddress"] = mint_address
    
    transfers = []
    page = 1
    remaining = limit
    
    while remaining > 0:
        params["page"] = page
        
        try:
            response = requests.get(url, headers=get_vybe_headers(), params=params)
            response.raise_for_status()
            result = response.json()
            
            if "transfers" in result and result["transfers"]:
                batch = result["transfers"]
                transfers.extend(batch)
                
                if len(batch) < BATCH_SIZE:
                    # No more transfers
                    break
                
                page += 1
                remaining -= len(batch)
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.2)
            else:
                break
        
        except Exception as e:
            logger.error(f"Error getting token transfers: {str(e)}")
            break
    
    logger.info(f"Retrieved {len(transfers)} token transfers")
    return transfers

def get_token_details(mint_address):
    """
    Get token details from Vybe API
    
    Args:
        mint_address (str): Token mint address
    
    Returns:
        dict: Token details
    """
    url = f"{VYBE_API_URL}/token/{mint_address}"
    
    try:
        response = requests.get(url, headers=get_vybe_headers())
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully retrieved token details for {mint_address}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting token details for {mint_address}: {str(e)}")
        return None

def get_top_token_holders(mint_address, limit=100):
    """
    Get top token holders from Vybe API
    
    Args:
        mint_address (str): Token mint address
        limit (int): Maximum number of holders to retrieve
    
    Returns:
        dict: Top token holders data
    """
    url = f"{VYBE_API_URL}/token/{mint_address}/top-holders"
    params = {
        "limit": min(limit, 1000)  # API limit
    }
    
    try:
        response = requests.get(url, headers=get_vybe_headers(), params=params)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully retrieved top token holders for {mint_address}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting top token holders for {mint_address}: {str(e)}")
        return None

def get_program_details(program_id):
    """
    Get program details from Vybe API
    
    Args:
        program_id (str): Solana program ID
    
    Returns:
        dict: Program details
    """
    url = f"{VYBE_API_URL}/program/{program_id}"
    
    try:
        response = requests.get(url, headers=get_vybe_headers())
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully retrieved program details for {program_id}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting program details for {program_id}: {str(e)}")
        return None

def get_program_active_users(program_id, days=30, limit=100):
    """
    Get active users for a program from Vybe API
    
    Args:
        program_id (str): Solana program ID
        days (int): Number of days to retrieve data for
        limit (int): Maximum number of users to retrieve
    
    Returns:
        dict: Program active users data
    """
    url = f"{VYBE_API_URL}/program/{program_id}/active-users"
    params = {
        "days": days,
        "limit": min(limit, 1000)  # API limit
    }
    
    try:
        response = requests.get(url, headers=get_vybe_headers(), params=params)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully retrieved active users for program {program_id}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting active users for program {program_id}: {str(e)}")
        return None

def collect_data(address, limit=DEFAULT_TRANSACTION_LIMIT):
    """
    Collect all relevant data for an address from Vybe API
    
    Args:
        address (str): Address to collect data for
        limit (int): Maximum number of records to collect
    
    Returns:
        dict: Collected data
    """
    logger.info(f"Collecting Vybe API data for address {address}")
    
    # Get token balances
    token_balances = get_token_balance(address)
    
    # Get token balance time series
    token_balance_ts = get_token_balance_timeseries(address)
    
    # Get token transfers
    token_transfers = get_token_transfers(address=address, limit=limit)
    
    # Get token details for each token in the balance
    token_details = {}
    if token_balances and "balances" in token_balances:
        for token in token_balances["balances"][:10]:  # Limit to top 10 tokens to avoid too many API calls
            mint = token.get("mint")
            if mint:
                token_details[mint] = get_token_details(mint)
                
                # Save token data
                if token_details[mint]:
                    save_token_data(mint, token_details[mint])
    
    # Get program interactions (from token transfers)
    program_ids = set()
    for transfer in token_transfers:
        if "program" in transfer and "id" in transfer["program"]:
            program_ids.add(transfer["program"]["id"])
    
    # Get program details
    program_details = {}
    for program_id in list(program_ids)[:5]:  # Limit to top 5 programs to avoid too many API calls
        program_details[program_id] = get_program_details(program_id)
        
        # Save program data
        if program_details[program_id]:
            save_program_data(program_id, program_details[program_id])
    
    logger.info(f"Vybe API data collection complete for {address}")
    
    return {
        "address": address,
        "token_balances": token_balances,
        "token_balance_ts": token_balance_ts,
        "token_transfers": token_transfers,
        "token_details": token_details,
        "program_details": program_details,
        "collected_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # For testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect data from Vybe API")
    parser.add_argument("address", help="Address to collect data for")
    parser.add_argument("--limit", type=int, default=DEFAULT_TRANSACTION_LIMIT,
                        help="Maximum number of records to collect")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    collect_data(args.address, args.limit)