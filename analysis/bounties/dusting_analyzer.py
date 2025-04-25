"""
Address Poisoning (Dusting) Analyzer for detecting address poisoning attacks on Solana

This module identifies address poisoning/dusting attacks by:
1. Detecting small "dust" transactions to many addresses
2. Identifying lookalike addresses (address poisoning)
3. Analyzing transaction patterns consistent with dusting
4. Generating reports on detected dusting campaigns
"""

from asyncio.log import logger
import logging
import os
import sys
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
import difflib
from Levenshtein import distance
from sentinel.ai.utils.data_formatter import DataFormatter
from data.collectors import helius_collector, range_collector
from data.storage.address_db import AddressDatabase
from ai.models.pattern_detector import PatternDetector # Corrected import path and class name
from reports.generator import ReportGenerator
from ai.utils.ai_analyzer import AIAnalyzer # Import AIAnalyzer
from collections import Counter
import time

logger = logging.getLogger(__name__)

class DustingAnalyzer:
    """Analyzer for address poisoning and dusting attacks on Solana"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.db = AddressDatabase(db_path) if db_path else None
        self.ai_analyzer = AIAnalyzer() # Initialize AI Analyzer
        logger.info("DustingAnalyzer initialized.")
        
        # Dust thresholds (example, adjust based on token price feeds)
        self.dust_thresholds_usd = {
            "SOL": 0.001,
            "USDC": 0.01,
            "USDT": 0.01,
            "default": 0.1  # Default threshold in USD
        }
        
        # Address poisoning patterns
        self.poisoning_patterns = {
            "prefix_match": {
                "description": "Address with matching prefix (first 4-8 characters)",
                "weight": 0.7
            },
            "suffix_match": {
                "description": "Address with matching suffix (last 4-8 characters)",
                "weight": 0.5
            },
            "visual_similarity": {
                "description": "Address with high visual similarity",
                "weight": 0.6
            },
            "dust_amount": {
                "description": "Very small 'dust' transaction amount",
                "weight": 0.8
            },
            "multiple_recipients": {
                "description": "Same dust amount sent to multiple recipients",
                "weight": 0.7
            }
        }
        
        # Dusting campaign patterns
        self.campaign_patterns = {
            "high_frequency": {
                "description": "High frequency of dust transactions from a single source",
                "weight": 0.6
            },
            "broad_distribution": {
                "description": "Dust sent to a large number of unique recipients",
                "weight": 0.7
            },
            "coordinated_timing": {
                "description": "Dust transactions sent in coordinated bursts",
                "weight": 0.5
            },
            "consistent_amount": {
                "description": "Consistent dust amount used across the campaign",
                "weight": 0.8
            }
        }

    def is_dust_transaction(self, transaction):
        """
        Determines if a transaction qualifies as dust based on its value.
        
        Args:
            transaction (dict): Transaction data dictionary.
            
        Returns:
            bool: True if the transaction is considered dust, False otherwise.
        """
        amount_usd = transaction.get('amount_usd')
        token_symbol = transaction.get('token_symbol', 'default') # Assuming token symbol is available

        if amount_usd is None:
            # Fallback if USD amount is not available (less reliable)
            # amount = transaction.get('amount', 0)
            # threshold = self.dust_thresholds_token.get(token_symbol, self.dust_thresholds_token['default'])
            # return amount > 0 and amount <= threshold
            return False # Require USD amount for reliable dust detection

        threshold = self.dust_thresholds_usd.get(token_symbol, self.dust_thresholds_usd['default'])
        
        # Check if amount is positive but below the threshold
        return amount_usd > 0 and amount_usd <= threshold

    def calculate_address_similarity(self, addr1, addr2):
        """
        Calculates various similarity metrics between two Solana addresses.
        
        Args:
            addr1 (str): First Solana address.
            addr2 (str): Second Solana address.
            
        Returns:
            dict: Dictionary containing different similarity scores.
        """
        if not isinstance(addr1, str) or not isinstance(addr2, str):
            return {
                "prefix_similarity": 0, "prefix_length": 0,
                "suffix_similarity": 0, "suffix_length": 0,
                "levenshtein_similarity": 0, "difflib_similarity": 0,
                "visual_similarity": 0
            }
            
        min_len = min(len(addr1), len(addr2))
        
        # Prefix similarity (first 8 chars)
        prefix_length = 0
        for i in range(min(8, min_len)):
            if addr1[i] == addr2[i]:
                prefix_length += 1
            else:
                break
        
        prefix_similarity = prefix_length / min(8, min_len)
        
        # Suffix similarity (last 8 chars)
        suffix_length = 0
        for i in range(1, min(8, min_len) + 1):  # Check last 8 chars max
            if addr1[-i] == addr2[-i]:
                suffix_length += 1
            else:
                break
        
        suffix_similarity = suffix_length / min(8, min_len)
        
        # Calculate Levenshtein ratio
        lev_similarity = 1 - (distance(addr1, addr2) / max(len(addr1), len(addr2)))
        
        # Calculate difflib similarity
        difflib_similarity = difflib.SequenceMatcher(None, addr1, addr2).ratio()
        
        # Combine similarities with weights
        visual_similarity = (
            (prefix_similarity * 0.4) +
            (suffix_similarity * 0.3) +
            (lev_similarity * 0.15) +
            (difflib_similarity * 0.15)
        )
        
        return {
            "prefix_similarity": prefix_similarity,
            "prefix_length": prefix_length,
            "suffix_similarity": suffix_similarity,
            "suffix_length": suffix_length,
            "levenshtein_similarity": lev_similarity,
            "difflib_similarity": difflib_similarity,
            "visual_similarity": visual_similarity
        }

    def fetch_transactions(self, address, days=30, limit=1000):
        """Fetches transactions for an address within a given timeframe."""
        transactions = []
        logger.info(f"Fetching transactions for {address} (last {days} days, limit {limit})")
        try:
            if helius_collector:
                tx_history = helius_collector.get_transaction_history(address, limit=limit)
                signatures = [tx['signature'] for tx in tx_history if 'signature' in tx]
                logger.info(f"Fetched {len(signatures)} signatures from Helius for {address}.")

                fetched_count = 0
                for sig in signatures:
                    if fetched_count >= limit: break
                    try:
                        details = helius_collector.get_transaction_details(sig)
                        if details:
                            transactions.append(details)
                            fetched_count += 1
                    except Exception as detail_err:
                        logger.warning(f"Failed to fetch details for tx {sig}: {detail_err}")
                    time.sleep(0.05) # Basic rate limiting
                logger.info(f"Fetched details for {len(transactions)} transactions from Helius.")

            if not transactions and range_collector:
                logger.info(f"Falling back to Range for transactions for {address}")
                range_tx_data = range_collector.get_address_transactions(address, limit=limit)
                if range_tx_data and 'transactions' in range_tx_data:
                    transactions = range_tx_data['transactions']
                    logger.info(f"Fetched {len(transactions)} transactions from Range.")

        except Exception as e:
            logger.error(f"Error fetching transactions for {address}: {e}")

        # Filter transactions by date
        return self._filter_transactions_by_days(transactions, days)

    def fetch_dust_transactions(self, address=None, days=30):
        """
        Fetches transactions that qualify as dust for a specific address or globally.
        Note: Global dust fetching is currently limited.
        
        Args:
            address (str, optional): The target address. If None, attempts global fetch (limited).
            days (int): Number of days of history to consider.
            
        Returns:
            pandas.DataFrame: DataFrame containing dust transactions.
        """
        if address:
            # Fetch transactions for the specific address
            transactions = self.fetch_transactions(address, days=days, limit=2000) # Increase limit for dust
        else:
            # If looking for general dust patterns, use Range API for small value transactions
            # The function get_small_value_transactions is not defined in range_collector context.
            # Using get_address_transactions as a placeholder, needs refinement.
            # This part likely needs a different approach, e.g., querying a data source
            # that indexes transactions by value or using a broader transaction stream.
            self.logger.warning("Fetching general small value transactions is not fully implemented with current collectors.")
            # Placeholder: Fetch recent transactions and filter - this might be inefficient
            # transactions = range_collector.get_address_transactions(...) # Needs an address or different Range API endpoint
            transactions = [] # Set to empty for now
        
        # Keep only transactions that qualify as dust
        dust_transactions = [tx for tx in transactions if self.is_dust_transaction(tx)]
        self.logger.info(f"Found {len(dust_transactions)} dust transactions out of {len(transactions)} total transactions")
        
        return pd.DataFrame(dust_transactions)

    def detect_address_poisoning(self, address, transactions_df=None, days=30):
        """
        Detects potential address poisoning attempts targeting a specific address.
        
        Args:
            address (str): The target address to check for poisoning attempts.
            transactions_df (pd.DataFrame, optional): Pre-fetched transactions DataFrame. If None, fetches transactions.
            days (int): Number of days of history to consider.
            
        Returns:
            list: A list of dictionaries, each representing a potential poisoning attempt.
        """
        if transactions_df is None:
            transactions = self.fetch_transactions(address, days=days, limit=2000)
            if not transactions:
                logger.warning(f"No transactions found for {address} to analyze for poisoning.")
                return []
            transactions_df = pd.DataFrame(transactions)
            # Ensure necessary columns exist even if empty
            if 'sender' not in transactions_df.columns: transactions_df['sender'] = None
            if 'receiver' not in transactions_df.columns: transactions_df['receiver'] = None
            if 'amount_usd' not in transactions_df.columns: transactions_df['amount_usd'] = np.nan

        poisoning_attempts = []
        
        # 1. Identify legitimate counterparties (simplified: those the target sent funds TO)
        outgoing_txs = transactions_df[transactions_df['sender'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x) == address]
        legitimate_counterparties = set(outgoing_txs['receiver'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x).dropna())
        
        # 2. Identify incoming dust transactions
        incoming_dust_txs = transactions_df[
            (transactions_df['receiver'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x) == address) &
            (transactions_df.apply(self.is_dust_transaction, axis=1))
        ]
        
        if incoming_dust_txs.empty:
            logger.info(f"No incoming dust transactions found for {address}.")
            return []
            
        logger.info(f"Found {len(incoming_dust_txs)} incoming dust transactions for {address}.")

        # 3. Check similarity between dust senders and legitimate counterparties
        dust_senders = set(incoming_dust_txs['sender'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x).dropna())
        
        for sender in dust_senders:
            max_similarity = 0
            most_similar_counterparty = None
            similarity_details = {}

            for counterparty_address in legitimate_counterparties:
                if not counterparty_address: continue # Skip if counterparty address is None
                
                similarity = self.calculate_address_similarity(sender, counterparty_address)
                
                if similarity['visual_similarity'] > max_similarity:
                    max_similarity = similarity['visual_similarity']
                    most_similar_counterparty = counterparty_address
                    similarity_details = similarity

            # If there's a strong similarity, flag as potential poisoning
            if max_similarity > 0.7: # Similarity threshold
                # Get transactions from this sender
                sender_txs = incoming_dust_txs[
                    incoming_dust_txs['sender'].apply(
                        lambda x: x.get('wallet') if isinstance(x, dict) else x
                    ) == sender
                ]
                
                poisoning_attempts.append({
                    "target_address": address,
                    "legitimate_counterparty": most_similar_counterparty,
                    "poisoning_address": sender,
                    "similarity": similarity_details,
                    "transaction_count": len(sender_txs),
                    "total_dust_value_usd": sender_txs['amount_usd'].sum() if 'amount_usd' in sender_txs.columns else None,
                    "first_seen": sender_txs['block_time'].min() if 'block_time' in sender_txs.columns else None,
                    "last_seen": sender_txs['block_time'].max() if 'block_time' in sender_txs.columns else None,
                    "risk_score": self._calculate_poisoning_risk(similarity_details, len(sender_txs))
                })

        logger.info(f"Detected {len(poisoning_attempts)} potential address poisoning attempts against {address}.")
        return poisoning_attempts

    def _calculate_poisoning_risk(self, similarity, tx_count):
        """Calculates a risk score for a specific poisoning attempt."""
        score = 0
        # Base score on visual similarity
        score += similarity.get('visual_similarity', 0) * 60 # Max 60 points from visual similarity
        
        # Add points for prefix/suffix match length
        score += similarity.get('prefix_length', 0) * 2 # Max 16 points
        score += similarity.get('suffix_length', 0) * 1 # Max 8 points
        
        # Add points for multiple transactions from the same poisoner
        score += min(tx_count - 1, 5) * 3 # Max 15 points
        
        return min(score, 100) # Cap at 100

    def detect_dusting_campaign(self, transactions_df=None, min_recipients=10, days=30):
        """
        Detects potential dusting campaigns based on transaction patterns.
        Requires a broader set of transactions than just one address.
        
        Args:
            transactions_df (pd.DataFrame, optional): DataFrame of transactions to analyze. If None, fetches recent dust globally (limited).
            min_recipients (int): Minimum number of unique recipients for an address to be considered a campaign source.
            days (int): Number of days of history to consider.
            
        Returns:
            list: A list of dictionaries, each representing a potential dusting campaign source.
        """
        if transactions_df is None:
            # Fetch global dust transactions (currently limited)
            transactions_df = self.fetch_dust_transactions(address=None, days=days)

        if transactions_df.empty or 'sender' not in transactions_df.columns:
            logger.warning("No dust transactions provided or DataFrame is invalid for campaign detection.")
            return []

        # Ensure necessary columns exist
        if 'receiver' not in transactions_df.columns: transactions_df['receiver'] = None
        if 'amount_usd' not in transactions_df.columns: transactions_df['amount_usd'] = np.nan
        if 'block_time' not in transactions_df.columns: transactions_df['block_time'] = None

        # Filter for dust transactions if not already done
        dust_txs = transactions_df[transactions_df.apply(self.is_dust_transaction, axis=1)].copy() # Use .copy()

        if dust_txs.empty:
            logger.info("No dust transactions found in the provided data.")
            return []

        # Extract sender addresses
        dust_txs['sender_address'] = dust_txs['sender'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x)
        dust_txs.dropna(subset=['sender_address'], inplace=True)

        # Group by sender and analyze recipient count and frequency
        campaign_sources = []
        grouped = dust_txs.groupby('sender_address')

        for sender, group in grouped:
            unique_recipients = group['receiver'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x).nunique()
            transaction_count = len(group)
            
            if unique_recipients >= min_recipients:
                # Potential campaign source found
                avg_amount_usd = group['amount_usd'].mean()
                total_amount_usd = group['amount_usd'].sum()
                first_seen = group['block_time'].min()
                last_seen = group['block_time'].max()
                
                # Calculate frequency (transactions per day)
                duration_days = 1
                if pd.notna(first_seen) and pd.notna(last_seen) and first_seen != last_seen:
                    # Ensure first_seen and last_seen are timezone-aware or naive consistently
                    if isinstance(first_seen, pd.Timestamp) and isinstance(last_seen, pd.Timestamp):
                         if first_seen.tzinfo is None and last_seen.tzinfo is not None:
                              first_seen = first_seen.tz_localize(last_seen.tzinfo)
                         elif first_seen.tzinfo is not None and last_seen.tzinfo is None:
                              last_seen = last_seen.tz_localize(first_seen.tzinfo)
                         duration_seconds = (last_seen - first_seen).total_seconds()
                         duration_days = max(1, duration_seconds / 86400) # Avoid division by zero
                    else:
                         # Handle cases where timestamps might not be pandas Timestamps
                         try:
                              # Attempt conversion if possible, otherwise default duration
                              start_ts = pd.Timestamp(first_seen).timestamp()
                              end_ts = pd.Timestamp(last_seen).timestamp()
                              duration_seconds = end_ts - start_ts
                              duration_days = max(1, duration_seconds / 86400)
                         except Exception:
                              duration_days = 1 # Default if conversion fails

                frequency = transaction_count / duration_days if duration_days > 0 else transaction_count

                campaign_sources.append({
                    "source_address": sender,
                    "unique_recipients": unique_recipients,
                    "transaction_count": transaction_count,
                    "avg_amount_usd": avg_amount_usd,
                    "total_amount_usd": total_amount_usd,
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                    "frequency_per_day": frequency,
                    "risk_score": self._calculate_campaign_risk(unique_recipients, transaction_count, frequency)
                })

        logger.info(f"Detected {len(campaign_sources)} potential dusting campaign sources.")
        # Sort by risk score
        campaign_sources.sort(key=lambda x: x['risk_score'], reverse=True)
        return campaign_sources

    def _calculate_campaign_risk(self, recipients, tx_count, frequency):
        """Calculates a risk score for a potential dusting campaign."""
        score = 0
        # Score based on number of recipients
        score += min(recipients / 10, 50) # Max 50 points, 1 point per 10 recipients up to 500
        
        # Score based on transaction count
        score += min(tx_count / 20, 30) # Max 30 points, 1 point per 20 txs up to 600
        
        # Score based on frequency
        score += min(frequency / 5, 20) # Max 20 points, 1 point per 5 tx/day up to 100/day
        
        return min(score, 100) # Cap at 100

    def calculate_dusting_risk(self, address, poisoning_attempts=None, days=30):
        """
        Calculates an overall dusting/poisoning risk score for a given address.
        
        Args:
            address (str): The target address.
            poisoning_attempts (list, optional): Pre-calculated poisoning attempts. If None, calculates them.
            days (int): Number of days of history to consider.
            
        Returns:
            dict: Risk assessment containing score, level, and contributing factors.
        """
        if poisoning_attempts is None:
            poisoning_attempts = self.detect_address_poisoning(address, days=days)

        risk_score = 0
        risk_factors = []

        if not poisoning_attempts:
            risk_level = "low"
        else:
            # Aggregate risk from individual attempts
            max_poisoning_score = 0
            total_poisoning_txs = 0
            unique_poisoners = set()

            for attempt in poisoning_attempts:
                max_poisoning_score = max(max_poisoning_score, attempt.get('risk_score', 0))
                total_poisoning_txs += attempt.get('transaction_count', 0)
                unique_poisoners.add(attempt.get('poisoning_address'))

            # Base score on the highest risk attempt
            risk_score += max_poisoning_score * 0.6 # 60% weight

            # Add points for multiple distinct poisoners
            risk_score += min(len(unique_poisoners) - 1, 5) * 5 # Max 25 points

            # Add points for total volume of poisoning transactions
            risk_score += min(total_poisoning_txs / 5, 15) # Max 15 points

            risk_score = min(risk_score, 100) # Cap at 100

            if max_poisoning_score > 0:
                 risk_factors.append(f"Highest poisoning attempt score: {max_poisoning_score:.1f}")
            if len(unique_poisoners) > 1:
                 risk_factors.append(f"Targeted by {len(unique_poisoners)} unique poisoning addresses.")
            if total_poisoning_txs > 0:
                 risk_factors.append(f"Received {total_poisoning_txs} potential poisoning transactions.")

            # Determine risk level
            if risk_score >= 70:
                risk_level = "high"
            elif risk_score >= 40:
                risk_level = "medium"
            else:
                risk_level = "low"

        return {
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "factors": risk_factors,
            "poisoning_attempt_count": len(poisoning_attempts)
        }

    def _filter_transactions_by_days(self, transactions, days):
        """Filters transactions to include only those within the specified number of days."""
        if not transactions or days <= 0:
            return transactions

        cutoff_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
        filtered_txs = []

        for tx in transactions:
            tx_time = None
            # Extract timestamp from different possible formats
            if "blockTime" in tx and tx["blockTime"] is not None:
                tx_time = tx["blockTime"]
            elif "block_time" in tx and tx["block_time"] is not None:
                if isinstance(tx["block_time"], str):
                    try:
                        # Try to convert ISO format string to timestamp
                        tx_time = datetime.fromisoformat(tx["block_time"].replace("Z", "+00:00")).timestamp()
                    except ValueError:
                        logger.warning(f"Could not parse block_time string: {tx['block_time']}")
                elif isinstance(tx["block_time"], (int, float)):
                     tx_time = tx["block_time"]
                elif isinstance(tx["block_time"], datetime):
                     tx_time = tx["block_time"].timestamp()

            # Include transaction if it's within the time range or if we can't determine the time
            if tx_time is None or tx_time >= cutoff_timestamp:
                filtered_txs.append(tx)

        logger.info(f"Filtered transactions from {len(transactions)} to {len(filtered_txs)} based on {days} day limit.")
        return filtered_txs

    def identify_dust_transactions(self, transactions, address):
        """Placeholder: Identifies dust transactions from a list."""
        # Implement logic based on self.is_dust_transaction
        dust_txs = [tx for tx in transactions if self.is_dust_transaction(tx)]
        # Further filter based on direction if needed (e.g., only incoming dust)
        incoming_dust = [
            tx for tx in dust_txs
            if tx.get('receiver') == address or (isinstance(tx.get('receiver'), dict) and tx['receiver'].get('wallet') == address)
        ]
        self.logger.info(f"Identified {len(incoming_dust)} incoming dust transactions for {address}")
        return incoming_dust # Or return all dust_txs depending on requirement

    def summarize_transactions(self, transactions, address):
        """Placeholder: Summarizes transaction history."""
        # Implement logic to summarize transactions (e.g., count, volume, counterparties)
        if not transactions:
            return {"count": 0, "incoming_count": 0, "outgoing_count": 0}

        incoming_count = 0
        outgoing_count = 0
        for tx in transactions:
             sender = tx.get('sender')
             receiver = tx.get('receiver')
             if isinstance(sender, dict): sender = sender.get('wallet')
             if isinstance(receiver, dict): receiver = receiver.get('wallet')

             if sender == address: outgoing_count += 1
             if receiver == address: incoming_count += 1

        return {
            "count": len(transactions),
            "incoming_count": incoming_count,
            "outgoing_count": outgoing_count,
            # Add more summary stats as needed
        }

    def analyze_address(self, address, days=30):
        """
        Performs a comprehensive dusting and poisoning analysis for an address.
        
        Args:
            address (str): The target address.
            days (int): Number of days of history to consider.
            
        Returns:
            dict: Comprehensive analysis results including poisoning attempts,
                  campaign involvement (if source), and overall risk.
        """
        logger.info(f"Starting full dusting/poisoning analysis for {address} (last {days} days)")
        
        # Fetch transactions once
        transactions = self.fetch_transactions(address, days=days, limit=2000)
        if not transactions:
             logger.warning(f"No transactions found for {address} within {days} days.")
             return {
                 "address": address,
                 "analysis_period_days": days,
                 "poisoning_attempts": [],
                 "dusting_campaigns_source": [],
                 "risk_assessment": {"risk_score": 0, "risk_level": "low", "factors": ["No transaction data"]},
                 "ai_analysis": None,
                 "timestamp": datetime.now().isoformat()
             }
        transactions_df = pd.DataFrame(transactions)
        # Ensure necessary columns exist
        if 'sender' not in transactions_df.columns: transactions_df['sender'] = None
        if 'receiver' not in transactions_df.columns: transactions_df['receiver'] = None
        if 'amount_usd' not in transactions_df.columns: transactions_df['amount_usd'] = np.nan
        if 'block_time' not in transactions_df.columns: transactions_df['block_time'] = None


        # 1. Detect poisoning attempts targeting this address
        poisoning_attempts = self.detect_address_poisoning(address, transactions_df=transactions_df, days=days)
        
        # 2. Detect if this address is a source of a dusting campaign
        # We need outgoing dust transactions from this address
        outgoing_dust_txs = transactions_df[
            (transactions_df['sender'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x) == address) &
            (transactions_df.apply(self.is_dust_transaction, axis=1))
        ]
        
        dusting_campaigns_source = []
        if not outgoing_dust_txs.empty:
             # Use the campaign detection logic, but focused on this single sender
             unique_recipients = outgoing_dust_txs['receiver'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x).nunique()
             transaction_count = len(outgoing_dust_txs)
             min_recipients_for_campaign = 5 # Lower threshold when checking a specific address as source

             if unique_recipients >= min_recipients_for_campaign:
                  avg_amount_usd = outgoing_dust_txs['amount_usd'].mean()
                  total_amount_usd = outgoing_dust_txs['amount_usd'].sum()
                  first_seen = outgoing_dust_txs['block_time'].min()
                  last_seen = outgoing_dust_txs['block_time'].max()
                  duration_days = 1
                  if pd.notna(first_seen) and pd.notna(last_seen) and first_seen != last_seen:
                       # Consistent timezone handling
                       if isinstance(first_seen, pd.Timestamp) and isinstance(last_seen, pd.Timestamp):
                            if first_seen.tzinfo is None and last_seen.tzinfo is not None: first_seen = first_seen.tz_localize(last_seen.tzinfo)
                            elif first_seen.tzinfo is not None and last_seen.tzinfo is None: last_seen = last_seen.tz_localize(first_seen.tzinfo)
                            duration_seconds = (last_seen - first_seen).total_seconds()
                            duration_days = max(1, duration_seconds / 86400)
                       else:
                            try:
                                 start_ts = pd.Timestamp(first_seen).timestamp()
                                 end_ts = pd.Timestamp(last_seen).timestamp()
                                 duration_seconds = end_ts - start_ts
                                 duration_days = max(1, duration_seconds / 86400)
                            except Exception: duration_days = 1

                  frequency = transaction_count / duration_days if duration_days > 0 else transaction_count
                  campaign_risk = self._calculate_campaign_risk(unique_recipients, transaction_count, frequency)

                  dusting_campaigns_source.append({
                       "source_address": address,
                       "unique_recipients": unique_recipients,
                       "transaction_count": transaction_count,
                       "avg_amount_usd": avg_amount_usd,
                       "total_amount_usd": total_amount_usd,
                       "first_seen": first_seen,
                       "last_seen": last_seen,
                       "frequency_per_day": frequency,
                       "risk_score": campaign_risk
                  })
                  logger.info(f"Address {address} identified as a potential dusting campaign source.")


        # 3. Calculate overall risk assessment
        risk_assessment = self.calculate_dusting_risk(address, poisoning_attempts=poisoning_attempts, days=days)
        # Add campaign source risk if applicable
        if dusting_campaigns_source:
             campaign_risk = dusting_campaigns_source[0]['risk_score']
             risk_assessment['risk_score'] = max(risk_assessment['risk_score'], campaign_risk) # Take the higher risk
             risk_assessment['factors'].append(f"Identified as potential dusting campaign source (score: {campaign_risk:.1f})")
             # Recalculate risk level
             if risk_assessment['risk_score'] >= 70: risk_assessment['risk_level'] = "high"
             elif risk_assessment['risk_score'] >= 40: risk_assessment['risk_level'] = "medium"
             elif risk_assessment['risk_score'] > 0 : risk_assessment['risk_level'] = "low"
             else: risk_assessment['risk_level'] = "none"


        # 4. Prepare data for AI analysis
        analysis_data = {
            "target_address": address,
            "analysis_period_days": days,
            "poisoning_attempts": poisoning_attempts,
            "dusting_campaigns_source": dusting_campaigns_source,
            "risk_assessment": risk_assessment,
            "transaction_summary": self.summarize_transactions(transactions, address)
        }

        # 5. Run AI analysis
        ai_analysis = self.ai_analyzer.analyze(analysis_data, "dusting")

        # 6. Combine results
        results = {
            "address": address,
            "analysis_period_days": days,
            "poisoning_attempts": poisoning_attempts,
            "dusting_campaigns_source": dusting_campaigns_source,
            "risk_assessment": risk_assessment,
            "ai_analysis": ai_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Completed full dusting/poisoning analysis for {address}")
        return results

    def generate_dusting_report(self, analysis_result):
        """
        Generates a markdown report from the dusting analysis results.
        (Placeholder - actual implementation would use ReportGenerator)
        
        Args:
            analysis_result (dict): The result from analyze_address.
            
        Returns:
            str: Path to the generated report file or None on error.
        """
        logger.info(f"Generating dusting report for address {analysis_result.get('address')}")
        # In a real implementation, this would call ReportGenerator
        # report_generator = ReportGenerator()
        # report_path = report_generator.generate_report(
        #     target=analysis_result.get('address'),
        #     data=analysis_result,
        #     report_type='dusting'
        # )
        # return report_path
        print("[Placeholder] Dusting report generation called.")
        return None # Placeholder return

# Example usage (for testing)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ensure API keys are loaded (if needed by collectors/AI)
    # from dotenv import load_dotenv
    # load_dotenv()

    analyzer = DustingAnalyzer()
    
    test_address = "VinesRG7K3ubzKLbxXz197c1RHV3cACkvGr9Zca7BSw" # Example address
    
    # Test poisoning detection
    # poisoning = analyzer.detect_address_poisoning(test_address, days=90)
    # print("\n--- Poisoning Attempts ---")
    # print(json.dumps(poisoning, indent=2, default=str))
    
    # Test campaign detection (requires broader data source)
    # campaigns = analyzer.detect_dusting_campaign(days=7)
    # print("\n--- Dusting Campaigns ---")
    # print(json.dumps(campaigns, indent=2, default=str))
    
    # Test full analysis
    full_analysis = analyzer.analyze_address(test_address, days=90)
    print("\n--- Full Analysis ---")
    print(json.dumps(full_analysis, indent=2, default=str))
    
    # Test report generation (placeholder)
    analyzer.generate_dusting_report(full_analysis)