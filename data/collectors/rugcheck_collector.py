"""
RugCheck API data collector
Collects token analysis data from RugCheck.xyz API
"""
import requests
import logging
import os
import sys
from datetime import datetime
import json # Added missing import

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.config import RUGCHECK_API_URL, get_rugcheck_headers # Assuming these are defined in config
from data.storage.token_db import save_token_rugcheck_data # Assuming a function to save data


logger = logging.getLogger(__name__)

def get_token_analysis(mint_address):
    """
    Get token analysis data from RugCheck API.

    Args:
        mint_address (str): The Solana token mint address.

    Returns:
        dict: Token analysis data from RugCheck, or None if an error occurs.
    """
    if not RUGCHECK_API_URL:
        logger.error("RUGCHECK_API_URL is not configured.")
        return None

    # Construct the API endpoint URL (adjust if the actual endpoint differs)
    url = f"{RUGCHECK_API_URL.rstrip('/')}/v1/tokens/{mint_address}" # Example endpoint structure
    headers = get_rugcheck_headers() # Get headers, potentially including API key

    try:
        logger.info(f"Fetching RugCheck analysis for token: {mint_address}")
        response = requests.get(url, headers=headers, timeout=30) # Added timeout
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        analysis_data = response.json()
        logger.info(f"Successfully retrieved RugCheck analysis for {mint_address}")
        return analysis_data

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching RugCheck data for {mint_address}: {http_err} - Status Code: {response.status_code}")
        # Log response body for debugging if needed, be careful with sensitive data
        # logger.debug(f"Response body: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred while fetching RugCheck data for {mint_address}: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred while fetching RugCheck data for {mint_address}: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"An error occurred during RugCheck API request for {mint_address}: {req_err}")
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response from RugCheck API for {mint_address}")
    except Exception as e:
        logger.error(f"An unexpected error occurred fetching RugCheck data for {mint_address}: {e}")

    return None

def collect_data(mint_address):
    """
    Collect RugCheck analysis data for a specific token mint address.

    Args:
        mint_address (str): The Solana token mint address.

    Returns:
        dict: A dictionary containing the collected RugCheck data and metadata, or None.
    """
    logger.info(f"Starting RugCheck data collection for token: {mint_address}")

    analysis_data = get_token_analysis(mint_address)

    if analysis_data:
        # Optionally save the raw data to a database
        try:
            save_token_rugcheck_data(mint_address, analysis_data) # Save the collected data
            logger.info(f"Successfully saved RugCheck data for {mint_address} to database.")
        except Exception as e:
            logger.error(f"Failed to save RugCheck data for {mint_address} to database: {e}")

        logger.info(f"RugCheck data collection complete for {mint_address}")
        return {
            "mint_address": mint_address,
            "rugcheck_analysis": analysis_data,
            "collected_at": datetime.now().isoformat()
        }
    else:
        logger.warning(f"RugCheck data collection failed for {mint_address}")
        return None

# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Replace with a valid Solana token mint address for testing
    # test_mint_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263" # Example: BONK
    test_mint_address = "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm" # Example: WIF

    if len(sys.argv) > 1:
         test_mint_address = sys.argv[1] # Allow passing mint address via command line

    print(f"Collecting RugCheck data for: {test_mint_address}")
    collected_data = collect_data(test_mint_address)

    if collected_data:
        print("\nCollected Data:")
        # Pretty print the JSON data
        import json
        print(json.dumps(collected_data, indent=2))
    else:
        print("\nFailed to collect data.")

