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
from datetime import datetime
import json
import pandas as pd
import numpy as np
import difflib
from Levenshtein import distance
from sentinel.ai.utils.data_formatter import DataFormatter
from data.collectors import helius_collector
from data.collectors.helius_collector import get_transaction_history, get_transaction_details
# Import the module itself, not a class
import data.collectors.range_collector as range_collector
from data.storage.address_db import AddressDatabase
from ai.models.pattern_detector import PatternDetector # Corrected import path and class name
from reports.generator import ReportGenerator

# Add the project root to the Python path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) # Removed, assuming proper package structure


class DustingAnalyzer:
    """Analyzer for address poisoning and dusting attacks on Solana"""
    
    def __init__(self, db_path=None):
        """
        Initialize the DustingAnalyzer
        
        Args:
            db_path (str, optional): Path to the SQLite database. Defaults to None.
        """
        self.logger = logging.getLogger(__name__)
        # self.helius_collector = helius_collector() # Assuming helius_collector is used via functions
        # self.range_collector = RangeCollector() # Removed instantiation
        self.db = AddressDatabase(db_path)
        self.pattern_detector = PatternDetector() # Use the correct class name
        self.data_formatter = DataFormatter()
        self.report_generator = ReportGenerator()
        
        # Define dust transaction thresholds based on knowledge base
        self.dust_thresholds = {
            "SOL": 0.001,  # 0.001 SOL
            "USDC": 0.1,   # $0.10
            "USDT": 0.1,   # $0.10
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
    
    def is_dust_transaction(self, transaction):
        """
        Check if a transaction is a dust transaction
        
        Args:
            transaction (dict): Transaction data
            
        Returns:
            bool: True if dust transaction, False otherwise
        """
        # Get token symbol and amount
        token_symbol = transaction.get('symbol', 'default').upper()
        
        # Get amount in USD if available, otherwise use token amount
        amount_usd = transaction.get('amount_usd')
        if amount_usd is not None:
            threshold = self.dust_thresholds.get('default')
            return amount_usd <= threshold
        
        # Fall back to token amount
        amount = transaction.get('amount', 0)
        threshold = self.dust_thresholds.get(token_symbol, self.dust_thresholds['default'])
        
        return amount <= threshold
    
    def calculate_address_similarity(self, addr1, addr2):
        """
        Calculate similarity between two addresses
        
        Args:
            addr1 (str): First address
            addr2 (str): Second address
            
        Returns:
            dict: Similarity metrics
        """
        # Normalize addresses
        addr1 = addr1.strip().lower()
        addr2 = addr2.strip().lower()
        
        # Get length of the shorter address
        min_len = min(len(addr1), len(addr2))
        
        # Check prefix similarity
        prefix_length = 0
        for i in range(min(8, min_len)):  # Check first 8 chars max
            if addr1[i] == addr2[i]:
                prefix_length += 1
            else:
                break
        
        prefix_similarity = prefix_length / min(8, min_len)
        
        # Check suffix similarity
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
    
    def fetch_dust_transactions(self, address=None, days=30):
        """
        Fetch potential dust transactions
        
        Args:
            address (str, optional): Address to analyze. If None, analyze general dust patterns.
            days (int, optional): Number of days to look back. Defaults to 30.
            
        Returns:
            pd.DataFrame: DataFrame of dust transactions
        """
        self.logger.info(f"Fetching dust transactions for the last {days} days")
        
        # Get transactions
        transactions = []
        if address:
            # If analyzing a specific address
            # Assuming helius_collector functions are used directly
            tx_history = helius_collector.get_transaction_history(address) # Need to handle days parameter if supported
            for tx_info in tx_history:
                 if 'signature' in tx_info:
                    tx_details = helius_collector.get_transaction_details(tx_info['signature'])
                    if tx_details:
                        transactions.append(tx_details)
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
        Detect address poisoning targeting a specific address
        
        Args:
            address (str): Address to check for poisoning attacks
            transactions_df (pd.DataFrame, optional): Pre-loaded transactions. Defaults to None.
            days (int, optional): Number of days to look back. Defaults to 30.
            
        Returns:
            list: List of detected poisoning attempts
        """
        self.logger.info(f"Detecting address poisoning for {address}")
        
        # If transactions are not provided, fetch them
        if transactions_df is None:
            transactions_df = self.fetch_dust_transactions(address, days)

        if transactions_df.empty:
             self.logger.warning(f"No dust transactions found for {address} to analyze for poisoning.")
             return []
        
        # Get the address's frequent counterparties
        # Use the imported module function directly
        counterparties_data = range_collector.get_address_counterparties(address)
        counterparties = counterparties_data.get('counterparties', []) if counterparties_data else []
        
        poisoning_attempts = []
        
        # Check each counterparty for look-alike addresses in transactions
        for counterparty in counterparties:
            counterparty_address = counterparty.get('address')
            if not counterparty_address:
                continue
            
            # Get all sender addresses from the dust transactions
            sender_addresses = transactions_df['sender'].apply(
                lambda x: x.get('wallet') if isinstance(x, dict) else x
            ).dropna().unique()
            
            # Check each sender for similarity to the counterparty
            for sender in sender_addresses:
                # Skip if they're the same address
                if sender == counterparty_address:
                    continue
                
                # Calculate similarity
                similarity = self.calculate_address_similarity(sender, counterparty_address)
                
                # If there's a strong similarity, flag as potential poisoning
                if similarity['visual_similarity'] > 0.7:
                    # Get transactions from this sender
                    sender_txs = transactions_df[
                        transactions_df['sender'].apply(
                            lambda x: x.get('wallet') if isinstance(x, dict) else x
                        ) == sender
                    ]
                    
                    poisoning_attempts.append({
                        "target_address": address,
                        "legitimate_counterparty": counterparty_address,
                        "poisoning_address": sender,
                        "similarity": similarity,
                        "transaction_count": len(sender_txs),
                        "total_dust_value_usd": sender_txs['amount_usd'].sum() if 'amount_usd' in sender_txs.columns else None,
                        "first_seen": sender_txs['block_time'].min() if 'block_time' in sender_txs.columns else None,
                        "last_seen": sender_txs['block_time'].max() if 'block_time' in sender_txs.columns else None,
                        "confidence": similarity['visual_similarity']
                    })
        
        # Sort by confidence, highest first
        poisoning_attempts.sort(key=lambda x: x['confidence'], reverse=True)
        
        return poisoning_attempts
    
    def detect_dusting_campaign(self, transactions_df=None, min_recipients=10, days=30):
        """
        Detect coordinated dusting campaigns
        
        Args:
            transactions_df (pd.DataFrame, optional): Pre-loaded transactions. Defaults to None.
            min_recipients (int, optional): Minimum number of recipients to consider a campaign. Defaults to 10.
            days (int, optional): Number of days to look back. Defaults to 30.
            
        Returns:
            list: List of detected dusting campaigns
        """
        self.logger.info(f"Detecting dusting campaigns (min_recipients={min_recipients})")
        
        # If transactions are not provided, fetch them
        if transactions_df is None:
            transactions_df = self.fetch_dust_transactions(days=days)
        
        if transactions_df.empty:
            return []
        
        # Group by sender address
        if 'sender' in transactions_df.columns:
            # Extract sender wallet addresses if they're in dictionary format
            if isinstance(transactions_df.iloc[0].get('sender'), dict):
                sender_addresses = transactions_df['sender'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else None)
                transactions_df['sender_address'] = sender_addresses
            else:
                transactions_df['sender_address'] = transactions_df['sender']
        else:
            self.logger.warning("No sender column found in transactions DataFrame")
            return []
        
        # Group transactions by sender
        sender_groups = transactions_df.groupby('sender_address')
        
        dusting_campaigns = []
        
        for sender, group in sender_groups:
            if len(group) < min_recipients:
                continue
            
            # Check if the amounts are similar (typical for dusting campaigns)
            amount_counts = group['amount'].value_counts()
            most_common_amount = amount_counts.index[0] if not amount_counts.empty else None
            most_common_count = amount_counts.iloc[0] if not amount_counts.empty else 0
            
            # If a significant portion of transactions have the same amount, likely a campaign
            if most_common_count >= min_recipients:
                # Get unique recipients
                if 'receiver' in group.columns:
                    if isinstance(group.iloc[0].get('receiver'), dict):
                        recipients = group['receiver'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else None).unique()
                    else:
                        recipients = group['receiver'].unique()
                else:
                    recipients = []
                
                dusting_campaigns.append({
                    "sender_address": sender,
                    "recipient_count": len(recipients),
                    "transaction_count": len(group),
                    "common_amount": most_common_amount,
                    "common_amount_count": most_common_count,
                    "first_seen": group['block_time'].min() if 'block_time' in group.columns else None,
                    "last_seen": group['block_time'].max() if 'block_time' in group.columns else None,
                    "total_dust_value_usd": group['amount_usd'].sum() if 'amount_usd' in group.columns else None,
                    "recipients_sample": list(recipients)[:10] if recipients is not None else [],
                    "confidence": min(0.9, most_common_count / len(group) * 0.9 + 0.1)
                })
        
        # Sort by recipient count, highest first
        dusting_campaigns.sort(key=lambda x: x['recipient_count'], reverse=True)
        
        return dusting_campaigns
    
    def calculate_dusting_risk(self, address, poisoning_attempts=None, days=30):
        """
        Calculate the risk score for an address being targeted by dusting/poisoning
        
        Args:
            address (str): Address to analyze
            poisoning_attempts (list, optional): Pre-detected poisoning attempts. Defaults to None.
            days (int, optional): Number of days to look back. Defaults to 30.
            
        Returns:
            dict: Risk assessment
        """
        self.logger.info(f"Calculating dusting risk for {address}")
        
        # If poisoning attempts are not provided, detect them
        if poisoning_attempts is None:
            poisoning_attempts = self.detect_address_poisoning(address, days=days)
        
        # Get dust transactions
        dust_txs = self.fetch_dust_transactions(address, days=days)

        incoming_dust_count = 0
        if not dust_txs.empty and 'receiver' in dust_txs.columns:
            # Count incoming dust transactions
            incoming_dust = dust_txs[
                dust_txs['receiver'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x) == address
            ]
            incoming_dust_count = len(incoming_dust)
        else:
            incoming_dust = pd.DataFrame() # Ensure incoming_dust is a DataFrame

        # Calculate risk score
        risk_score = 0.0
        risk_factors = []
        
        # Risk from poisoning attempts
        if poisoning_attempts:
            # Higher risk with more poisoning attempts
            poisoning_risk = min(0.8, len(poisoning_attempts) * 0.2)
            risk_score += poisoning_risk
            
            risk_factors.append({
                "factor": "address_poisoning",
                "description": f"Detected {len(poisoning_attempts)} address poisoning attempts",
                "severity": "high" if poisoning_risk >= 0.5 else "medium",
                "weight": 0.4
            })
            
            # Add details of the highest confidence poisoning attempt
            if poisoning_attempts:
                top_attempt = poisoning_attempts[0]
                risk_factors.append({
                    "factor": "most_similar_address",
                    "description": f"Most similar poisoning address: {top_attempt['poisoning_address']}",
                    "similarity": top_attempt['similarity']['visual_similarity'],
                    "weight": 0.2
                })
        
        # Risk from incoming dust
        if incoming_dust_count > 0:
            # Calculate risk based on number of dust transactions
            dust_risk = min(0.7, incoming_dust_count * 0.05)
            risk_score += dust_risk
            
            risk_factors.append({
                "factor": "incoming_dust",
                "description": f"Received {incoming_dust_count} dust transactions",
                "severity": "high" if dust_risk >= 0.4 else ("medium" if dust_risk >= 0.2 else "low"),
                "weight": 0.3
            })
            
            # Check unique senders
            if not incoming_dust.empty and 'sender' in incoming_dust.columns:
                unique_senders = incoming_dust['sender'].apply(
                    lambda x: x.get('wallet') if isinstance(x, dict) else x
                ).nunique()
                
                if unique_senders >= 3:
                    risk_factors.append({
                        "factor": "multiple_dust_senders",
                        "description": f"Dust received from {unique_senders} different addresses",
                        "severity": "medium",
                        "weight": 0.1
                    })
        
        # Check if any dust was followed by large outgoing transactions
        # This is a common pattern where victims fall for the poisoning
        if not incoming_dust.empty and 'block_time' in incoming_dust.columns:
            # Get all transactions for this address
            # Assuming helius_collector functions are used directly
            all_tx_history = helius_collector.get_transaction_history(address) # Need to handle days parameter
            all_transactions = []
            for tx_info in all_tx_history:
                 if 'signature' in tx_info:
                    tx_details = helius_collector.get_transaction_details(tx_info['signature'])
                    if tx_details:
                        all_transactions.append(tx_details)

            # Convert to DataFrame
            all_txs_df = pd.DataFrame(all_transactions)
            
            if not all_txs_df.empty and 'block_time' in all_txs_df.columns and 'sender' in all_txs_df.columns:
                # Convert blockTime to datetime if necessary
                if not pd.api.types.is_datetime64_any_dtype(all_txs_df['block_time']):
                     all_txs_df['block_time'] = pd.to_datetime(all_txs_df['block_time'], unit='s')

                # Get outgoing transactions
                outgoing_txs = all_txs_df[
                    all_txs_df['sender'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x) == address
                ]
                
                # Check if any large outgoing tx happened after receiving dust
                # Ensure dust_times are datetime objects
                if not pd.api.types.is_datetime64_any_dtype(incoming_dust['block_time']):
                     incoming_dust['block_time'] = pd.to_datetime(incoming_dust['block_time'], unit='s')
                dust_times = incoming_dust['block_time'].tolist()
                
                suspicious_txs = []
                for _, tx in outgoing_txs.iterrows():
                    # Ensure tx block_time is datetime
                    tx_time = tx['block_time']
                    if not isinstance(tx_time, datetime):
                         tx_time = pd.to_datetime(tx_time, unit='s')

                    # Check if this tx happened after receiving dust
                    if any(tx_time > dust_time for dust_time in dust_times):
                        # Check if it's a large transaction
                        amount_usd = tx.get('amount_usd', 0)
                        if amount_usd > 100:  # Significant value
                            suspicious_txs.append(tx)
                
                if suspicious_txs:
                    risk_score += 0.4  # Very suspicious pattern
                    risk_factors.append({
                        "factor": "post_dust_outflow",
                        "description": f"Sent {len(suspicious_txs)} large transactions after receiving dust",
                        "severity": "very_high",
                        "examples": [tx.get('signature') for tx in suspicious_txs[:3]],
                        "weight": 0.4
                    })
        
        # Normalize risk score
        risk_score = min(1.0, risk_score)
        
        # Determine risk level
        risk_level = "low"
        if risk_score >= 0.8:
            risk_level = "very_high"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "medium"
        
        return {
            "address": address,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "poisoning_attempts": len(poisoning_attempts),
            "dust_transactions": incoming_dust_count,
            "analysis_timeframe": f"{days} days",
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_address(self, address, days=30):
        """
        Perform a comprehensive dusting analysis for an address
        
        Args:
            address (str): Address to analyze
            days (int, optional): Number of days to look back. Defaults to 30.
            
        Returns:
            dict: Analysis results
        """
        self.logger.info(f"Performing dusting analysis for {address}")
        
        # Detect address poisoning attempts
        poisoning_attempts = self.detect_address_poisoning(address, days=days)
        
        # Calculate risk score
        risk_assessment = self.calculate_dusting_risk(address, poisoning_attempts, days=days)
        
        # Get transactions to and from this address
        # Assuming helius_collector functions are used directly
        tx_history = helius_collector.get_transaction_history(address) # Need to handle days parameter
        transactions = []
        for tx_info in tx_history:
             if 'signature' in tx_info:
                tx_details = helius_collector.get_transaction_details(tx_info['signature'])
                if tx_details:
                    transactions.append(tx_details)
        transactions_df = pd.DataFrame(transactions)
        
        # Identify potential dusting campaigns targeting this address
        dusting_campaigns = []
        if not transactions_df.empty and 'receiver' in transactions_df.columns and 'sender' in transactions_df.columns:
            # Filter for incoming dust transactions
            incoming_dust = transactions_df[
                (transactions_df['receiver'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x) == address) &
                transactions_df.apply(lambda x: self.is_dust_transaction(x), axis=1)
            ]
            
            # Group by sender to identify campaigns
            if not incoming_dust.empty:
                sender_counts = incoming_dust['sender'].apply(
                    lambda x: x.get('wallet') if isinstance(x, dict) else x
                ).value_counts()
                
                # Identify senders with multiple dust transactions
                for sender, count in sender_counts.items():
                    if count >= 3:  # Multiple dust txs from same sender
                        sender_txs = incoming_dust[
                            incoming_dust['sender'].apply(lambda x: x.get('wallet') if isinstance(x, dict) else x) == sender
                        ]
                        
                        # Check if other addresses were also targeted
                        campaign = self.detect_dusting_campaign(
                            self.fetch_dust_transactions(sender, days=days)
                        )
                        
                        campaign_info = next((c for c in campaign if c['sender_address'] == sender), None)
                        
                        dusting_campaigns.append({
                            "sender_address": sender,
                            "dust_transaction_count": count,
                            "first_seen": sender_txs['block_time'].min() if 'block_time' in sender_txs.columns else None,
                            "last_seen": sender_txs['block_time'].max() if 'block_time' in sender_txs.columns else None,
                            "total_dust_value_usd": sender_txs['amount_usd'].sum() if 'amount_usd' in sender_txs.columns else None,
                            "part_of_larger_campaign": campaign_info is not None,
                            "campaign_size": campaign_info['recipient_count'] if campaign_info else None
                        })
        
        # Compile analysis results
        result = {
            "address": address,
            "risk_assessment": risk_assessment,
            "poisoning_attempts": poisoning_attempts,
            "dusting_campaigns": dusting_campaigns,
            "analysis_timeframe": f"{days} days",
            "timestamp": datetime.now().isoformat()
        }
        
        # Save results to database
        self.db.save_dusting_analysis(result)
        
        return result
    
    def generate_dusting_report(self, address=None, analysis_result=None):
        """
        Generate a dusting report using the ReportGenerator instance.

        Args:
            address (str, optional): The address analyzed (used for filename/context if needed).
                                     Defaults to None.
            analysis_result (dict, optional): The result from analyze_address. Defaults to None.

        Returns:
            str: Path to the generated report, or None if generation failed.
        """
        if not analysis_result:
            logger.error("Cannot generate dusting report without analysis results.")
            return None

        # Ensure the analysis_result contains the address if not provided separately
        if not address and 'address' in analysis_result:
            address = analysis_result['address']

        logger.info(f"Generating dusting report for address: {address or 'Unknown'}")
        try:
            # Call the method on the instance, passing the analysis data
            report_path = self.report_generator.generate_dusting_report(analysis_result)
            return report_path
        except Exception as e:
            logger.error(f"Error generating dusting report: {e}", exc_info=True)
            return None
    
    def scan_for_dusting_campaigns(self, min_recipients=20, days=30):
        """
        Scan the blockchain for active dusting campaigns
        
        Args:
            min_recipients (int, optional): Minimum number of recipients to consider a campaign. Defaults to 20.
            days (int, optional): Number of days to look back. Defaults to 30.
            
        Returns:
            list: List of detected dusting campaigns
        """
        self.logger.info(f"Scanning for dusting campaigns (min_recipients={min_recipients}, days={days})")
        
        # Fetch dust transactions
        dust_txs = self.fetch_dust_transactions(days=days)
        
        # Detect dusting campaigns
        campaigns = self.detect_dusting_campaign(dust_txs, min_recipients=min_recipients, days=days)
        
        return campaigns

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = DustingAnalyzer()
    
    # Example: Analyze a specific address
    if len(sys.argv) > 1:
        address = sys.argv[1]
        print(f"Analyzing address: {address}")
        result = analyzer.analyze_address(address)
        print(json.dumps(result, indent=2))
        
        # Generate report
        report_path = analyzer.generate_dusting_report(analysis_result=result)
        print(f"Report generated: {report_path}")
    else:
        # Scan for dusting campaigns
        print("Scanning for dusting campaigns...")
        campaigns = analyzer.scan_for_dusting_campaigns(min_recipients=10, days=30)
        print(f"Found {len(campaigns)} dusting campaigns")
        for campaign in campaigns:
            print(f"- Sender: {campaign['sender_address']}, Recipients: {campaign['recipient_count']}, Confidence: {campaign['confidence']:.2f}")