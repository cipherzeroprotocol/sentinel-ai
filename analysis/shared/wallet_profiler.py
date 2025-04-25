"""
Wallet Profiler - Shared component for Sentinel AI platform

This module provides shared functionality for profiling and classifying Solana wallets:
1. Wallet behavioral analysis and classification
2. Entity identification and relationship mapping
3. Risk scoring and anomaly detection
4. Historical activity profiling
"""

import logging
import os
import sys
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
from collections import defaultdict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from analysis.shared.transaction_analyzer import TransactionAnalyzer
import data.collectors.helius_collector as helius_collector
import data.collectors.range_collector as range_collector
import data.collectors.vybe_collector as vybe_collector
from data.storage.address_db import AddressDatabase

# Add the project root to the Python path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) # Removed, assuming proper package structure


class WalletProfiler:
    """Shared component for profiling and classifying Solana wallets"""
    
    def __init__(self, db_path=None):
        """
        Initialize the WalletProfiler
        
        Args:
            db_path (str, optional): Path to the SQLite database. Defaults to None.
        """
        self.logger = logging.getLogger(__name__)
        self.db = AddressDatabase(db_path)
        self.transaction_analyzer = TransactionAnalyzer(db_path)
        
        # Wallet classification categories
        self.wallet_categories = {
            "exchange": {
                "description": "Centralized exchange wallet",
                "features": ["high_volume", "balanced_in_out", "many_counterparties"]
            },
            "whale": {
                "description": "Large holder wallet",
                "features": ["high_balance", "large_transactions", "low_transaction_frequency"]
            },
            "trader": {
                "description": "Active trader wallet",
                "features": ["high_frequency", "dex_interaction", "token_diversity"]
            },
            "bot": {
                "description": "Automated trading bot",
                "features": ["very_high_frequency", "pattern_consistency", "small_transactions"]
            },
            "mixer": {
                "description": "Cryptocurrency mixing service",
                "features": ["balanced_in_out", "consistent_amounts", "high_privacy"]
            },
            "miner": {
                "description": "Mining/Validator wallet",
                "features": ["regular_income", "staking_rewards", "validator_interaction"]
            },
            "dapp": {
                "description": "Decentralized application",
                "features": ["program_interaction", "contract_calls", "service_patterns"]
            },
            "contract": {
                "description": "Smart contract",
                "features": ["is_program", "no_outgoing", "internal_transactions"]
            },
            "project_treasury": {
                "description": "Project treasury or multisig",
                "features": ["controlled_outflow", "large_balance", "multisig_patterns"]
            },
            "nft_trader": {
                "description": "NFT trader/collector",
                "features": ["nft_interactions", "marketplace_usage", "collection_holdings"]
            },
            "laundering": {
                "description": "Potential money laundering wallet",
                "features": ["layering_behavior", "mixer_interaction", "bridge_hopping"]
            },
            "scammer": {
                "description": "Potential scam operator",
                "features": ["phishing_patterns", "rugpull_connections", "victim_inflows"]
            }
        }
    
    def extract_wallet_features(self, address, transactions_df=None, days=90):
        """
        Extract behavioral features from wallet transaction history
        
        Args:
            address (str): Wallet address to analyze
            transactions_df (pd.DataFrame, optional): Pre-loaded transactions. Defaults to None.
            days (int, optional): Number of days to look back. Defaults to 90.
            
        Returns:
            dict: Extracted features
        """
        self.logger.info(f"Extracting wallet features for {address}")
        
        # If transactions are not provided, fetch them
        if transactions_df is None:
            # Get transactions for this address
            transactions = helius_collector.get_account_transactions(address, days=days)
            transactions_df = pd.DataFrame(transactions)
        
        features = {
            "address": address,
            "extraction_time": datetime.now().isoformat()
        }
        
        if transactions_df.empty:
            self.logger.warning(f"No transactions found for {address}")
            return features
        
        # Filter and prepare the data
        if 'sender' in transactions_df.columns and 'receiver' in transactions_df.columns:
            # Extract sender and receiver addresses
            transactions_df['sender_address'] = transactions_df['sender'].apply(
                lambda x: x.get('wallet') if isinstance(x, dict) else x
            )
            
            transactions_df['receiver_address'] = transactions_df['receiver'].apply(
                lambda x: x.get('wallet') if isinstance(x, dict) else x
            )
            
            # Filter for transactions involving this address
            sent_txs = transactions_df[transactions_df['sender_address'] == address]
            received_txs = transactions_df[transactions_df['receiver_address'] == address]
        else:
            sent_txs = pd.DataFrame()
            received_txs = pd.DataFrame()
        
        # Activity timeframe
        if not sent_txs.empty and 'block_time' in sent_txs.columns:
            features['first_sent_time'] = sent_txs['block_time'].min()
            features['last_sent_time'] = sent_txs['block_time'].max()
        
        if not received_txs.empty and 'block_time' in received_txs.columns:
            features['first_received_time'] = received_txs['block_time'].min()
            features['last_received_time'] = received_txs['block_time'].max()
        
        # Combine all transaction times to get the overall activity period
        all_times = []
        if not sent_txs.empty and 'block_time' in sent_txs.columns:
            all_times.extend(sent_txs['block_time'].tolist())
        
        if not received_txs.empty and 'block_time' in received_txs.columns:
            all_times.extend(received_txs['block_time'].tolist())
        
        if all_times:
            features['first_activity'] = min(all_times)
            features['last_activity'] = max(all_times)
            features['activity_days'] = (features['last_activity'] - features['first_activity']) / (60 * 60 * 24)
        else:
            features['activity_days'] = 0
        
        # Transaction counts
        features['sent_tx_count'] = len(sent_txs)
        features['received_tx_count'] = len(received_txs)
        features['total_tx_count'] = features['sent_tx_count'] + features['received_tx_count']
        
        # Transaction volumes
        if not sent_txs.empty and 'amount_usd' in sent_txs.columns:
            features['sent_volume_usd'] = sent_txs['amount_usd'].sum()
            features['avg_sent_amount_usd'] = sent_txs['amount_usd'].mean() if features['sent_tx_count'] > 0 else 0
            features['max_sent_amount_usd'] = sent_txs['amount_usd'].max() if features['sent_tx_count'] > 0 else 0
        else:
            features['sent_volume_usd'] = 0
            features['avg_sent_amount_usd'] = 0
            features['max_sent_amount_usd'] = 0
        
        if not received_txs.empty and 'amount_usd' in received_txs.columns:
            features['received_volume_usd'] = received_txs['amount_usd'].sum()
            features['avg_received_amount_usd'] = received_txs['amount_usd'].mean() if features['received_tx_count'] > 0 else 0
            features['max_received_amount_usd'] = received_txs['amount_usd'].max() if features['received_tx_count'] > 0 else 0
        else:
            features['received_volume_usd'] = 0
            features['avg_received_amount_usd'] = 0
            features['max_received_amount_usd'] = 0
        
        features['total_volume_usd'] = features['sent_volume_usd'] + features['received_volume_usd']
        
        # Calculate balance ratios
        if features['total_tx_count'] > 0:
            features['in_out_tx_ratio'] = features['received_tx_count'] / max(1, features['sent_tx_count'])
            features['in_out_volume_ratio'] = features['received_volume_usd'] / max(1, features['sent_volume_usd'])
        else:
            features['in_out_tx_ratio'] = 0
            features['in_out_volume_ratio'] = 0
        
        # Unique counterparties
        if not sent_txs.empty and 'receiver_address' in sent_txs.columns:
            features['unique_receivers'] = sent_txs['receiver_address'].nunique()
        else:
            features['unique_receivers'] = 0
        
        if not received_txs.empty and 'sender_address' in received_txs.columns:
            features['unique_senders'] = received_txs['sender_address'].nunique()
        else:
            features['unique_senders'] = 0
        
        features['unique_counterparties'] = features['unique_receivers'] + features['unique_senders']
        
        # Transaction velocity
        if features['activity_days'] > 0:
            features['tx_per_day'] = features['total_tx_count'] / features['activity_days']
            features['volume_per_day_usd'] = features['total_volume_usd'] / features['activity_days']
        else:
            features['tx_per_day'] = 0
            features['volume_per_day_usd'] = 0
        
        # Token diversity
        token_set = set()
        
        if 'mint' in transactions_df.columns:
            for token in transactions_df['mint'].dropna().unique():
                if token:
                    token_set.add(token)
        
        features['token_diversity'] = len(token_set)
        
        # Program interaction
        program_set = set()
        
        if 'program' in transactions_df.columns:
            for program in transactions_df['program'].dropna():
                if isinstance(program, dict) and 'id' in program:
                    program_id = program['id']
                    if program_id:
                        program_set.add(program_id)
        
        features['program_diversity'] = len(program_set)
        
        # Get current token balances
        try:
            token_balances = vybe_collector.get_token_balances(address)
            if token_balances:
                features['token_balance_count'] = len(token_balances)
                
                total_balance_usd = 0
                for balance in token_balances:
                    if isinstance(balance, dict) and 'balance_usd' in balance:
                        total_balance_usd += balance['balance_usd']
                
                features['total_balance_usd'] = total_balance_usd
        except Exception as e:
            self.logger.warning(f"Error fetching token balances: {e}")
            features['token_balance_count'] = 0
            features['total_balance_usd'] = 0
        
        # Calculate transaction timing features
        if not transactions_df.empty and 'block_time' in transactions_df.columns:
            # Sort by time
            sorted_txs = transactions_df.sort_values('block_time')
            
            # Calculate time differences between consecutive transactions
            if len(sorted_txs) > 1:
                time_diffs = []
                for i in range(1, len(sorted_txs)):
                    prev_time = sorted_txs.iloc[i-1]['block_time']
                    curr_time = sorted_txs.iloc[i]['block_time']
                    time_diffs.append(curr_time - prev_time)
                
                if time_diffs:
                    features['avg_time_between_txs'] = sum(time_diffs) / len(time_diffs)
                    features['min_time_between_txs'] = min(time_diffs)
                    features['max_time_between_txs'] = max(time_diffs)
                    
                    # Calculate standard deviation of time differences
                    if len(time_diffs) > 1:
                        features['time_between_txs_std'] = np.std(time_diffs)
                    else:
                        features['time_between_txs_std'] = 0
                    
                    # Check for regular patterns (potential automated activity)
                    if len(time_diffs) >= 5:
                        # Calculate coefficient of variation (lower values indicate more regular patterns)
                        cv = features['time_between_txs_std'] / features['avg_time_between_txs'] if features['avg_time_between_txs'] > 0 else float('inf')
                        features['timing_regularity'] = 1 / (1 + cv) if cv != float('inf') else 0
                    else:
                        features['timing_regularity'] = 0
        
        # Calculate transaction amount consistency
        if not transactions_df.empty and 'amount' in transactions_df.columns:
            amounts = transactions_df['amount'].dropna()
            if not amounts.empty and len(amounts) > 1:
                features['amount_mean'] = amounts.mean()
                features['amount_std'] = amounts.std()
                
                # Coefficient of variation for amounts
                cv_amount = features['amount_std'] / features['amount_mean'] if features['amount_mean'] > 0 else float('inf')
                features['amount_consistency'] = 1 / (1 + cv_amount) if cv_amount != float('inf') else 0
                
                # Check for round numbers (common in bot trading or specific services)
                round_amounts = 0
                for amount in amounts:
                    # Check if amount is a round number (no decimal places or simple fractions)
                    if amount == int(amount) or amount * 10 == int(amount * 10) or amount * 100 == int(amount * 100):
                        round_amounts += 1
                
                features['round_amount_ratio'] = round_amounts / len(amounts)
        
        # Calculate high-risk interactions
        # Get risk scores from Range API
        address_risk = range_collector.get_address_risk(address)
        if address_risk:
            features['risk_score'] = address_risk.get('risk_score', 0)
            features['risk_factors'] = address_risk.get('risk_factors', [])
        else:
            features['risk_score'] = 0
            features['risk_factors'] = []
        
        # Check for mixer interactions
        if not transactions_df.empty and 'program' in transactions_df.columns:
            # Known mixer program IDs based on the knowledge base
            mixer_program_ids = [
                "tor1xzb2Zyy1cUxXmyJfR8aNXuWnwHG8AwgaG7UGD4K",
                "mixerEfg3yXGYZJbhG43RJ2KdMUXbf6s9YGBXnJE9Qj2T",
                "1MixerZCaShtMCAdLozKTzVdLFf9WZqDehHHQdT1V5Pf",
                "mixBkFZP3Z1hGWaXeYPxvyzh2Wuq2nIUQBNCZHLbwiU"
            ]
            
            mixer_interactions = 0
            for _, tx in transactions_df.iterrows():
                program = tx.get('program')
                if isinstance(program, dict) and 'id' in program:
                    program_id = program['id']
                    if program_id in mixer_program_ids:
                        mixer_interactions += 1
            
            features['mixer_interactions'] = mixer_interactions
        else:
            features['mixer_interactions'] = 0
        
        # Check for bridge interactions (cross-chain activity)
        if not transactions_df.empty and 'program' in transactions_df.columns:
            # Known bridge program IDs based on the knowledge base
            bridge_program_ids = [
                "wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb",
                "3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5",
                "worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth",
                "3CEbPFMdBeWpX1z9QgKDdmBbTdJ7gYLjE2GQJ5uoVP7P",
                "6Cust4zaiNJJDkJZZbdS4wHfNXdgGu8EGRmAT9FW3cZb"
            ]
            
            bridge_interactions = 0
            for _, tx in transactions_df.iterrows():
                program = tx.get('program')
                if isinstance(program, dict) and 'id' in program:
                    program_id = program['id']
                    if program_id in bridge_program_ids:
                        bridge_interactions += 1
            
            features['bridge_interactions'] = bridge_interactions
        else:
            features['bridge_interactions'] = 0
        
        # Check for DEX interactions (trading activity)
        if not transactions_df.empty and 'program' in transactions_df.columns:
            # Known DEX program IDs based on the knowledge base
            dex_program_ids = [
                "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",  # Jupiter
                "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",   # Raydium
                "orcanEwBWRvkf8XTp1iYk8KgEnEw6IxJ9w6sc9Jcx6N",   # Orca
                "marea3UiXK2AkPyQLZ56npJT6D7vnxQgJ7SDMQkFC9Z"    # Meteora
            ]
            
            dex_interactions = 0
            for _, tx in transactions_df.iterrows():
                program = tx.get('program')
                if isinstance(program, dict) and 'id' in program:
                    program_id = program['id']
                    if program_id in dex_program_ids:
                        dex_interactions += 1
            
            features['dex_interactions'] = dex_interactions
        else:
            features['dex_interactions'] = 0
        
        return features
    
    def classify_wallet(self, features):
        """
        Classify wallet based on extracted features
        
        Args:
            features (dict): Wallet features
            
        Returns:
            dict: Classification results
        """
        self.logger.info(f"Classifying wallet {features.get('address')}")
        
        # Define classification rules based on extracted features
        classifications = []
        
        # Exchange wallet classification
        exchange_score = 0
        if features.get('total_tx_count', 0) > 1000:
            exchange_score += 0.3
        if 0.8 <= features.get('in_out_tx_ratio', 0) <= 1.2:  # Balanced in/out ratio
            exchange_score += 0.3
        if features.get('unique_counterparties', 0) > 500:
            exchange_score += 0.4
        
        if exchange_score >= 0.7:
            classifications.append({
                "type": "exchange",
                "confidence": exchange_score,
                "description": self.wallet_categories["exchange"]["description"]
            })
        
        # Whale wallet classification
        whale_score = 0
        if features.get('total_balance_usd', 0) > 1000000:  # $1M+ balance
            whale_score += 0.5
        if features.get('max_sent_amount_usd', 0) > 100000:  # $100k+ transactions
            whale_score += 0.3
        if features.get('tx_per_day', 0) < 5:  # Low transaction frequency
            whale_score += 0.2
        
        if whale_score >= 0.6:
            classifications.append({
                "type": "whale",
                "confidence": whale_score,
                "description": self.wallet_categories["whale"]["description"]
            })
        
        # Trader wallet classification
        trader_score = 0
        if features.get('tx_per_day', 0) > 10:  # High transaction frequency
            trader_score += 0.3
        if features.get('dex_interactions', 0) > 50:  # DEX interactions
            trader_score += 0.4
        if features.get('token_diversity', 0) > 10:  # Diverse token holdings
            trader_score += 0.3
        
        if trader_score >= 0.6:
            classifications.append({
                "type": "trader",
                "confidence": trader_score,
                "description": self.wallet_categories["trader"]["description"]
            })
        
        # Bot wallet classification
        bot_score = 0
        if features.get('tx_per_day', 0) > 50:  # Very high transaction frequency
            bot_score += 0.3
        if features.get('timing_regularity', 0) > 0.7:  # Consistent timing
            bot_score += 0.4
        if features.get('amount_consistency', 0) > 0.7:  # Consistent amounts
            bot_score += 0.3
        
        if bot_score >= 0.7:
            classifications.append({
                "type": "bot",
                "confidence": bot_score,
                "description": self.wallet_categories["bot"]["description"]
            })
        
        # Mixer classification
        mixer_score = 0
        if 0.95 <= features.get('in_out_volume_ratio', 0) <= 1.05:  # Almost perfectly balanced
            mixer_score += 0.4
        if features.get('round_amount_ratio', 0) > 0.8:  # Consistent round amounts
            mixer_score += 0.3
        if features.get('mixer_interactions', 0) > 0:  # Known mixer interactions
            mixer_score += 0.5
        
        if mixer_score >= 0.7:
            classifications.append({
                "type": "mixer",
                "confidence": mixer_score,
                "description": self.wallet_categories["mixer"]["description"]
            })
        
        # Project treasury classification
        treasury_score = 0
        if features.get('total_balance_usd', 0) > 500000:  # Large balance
            treasury_score += 0.3
        if features.get('in_out_tx_ratio', 0) > 2:  # More incoming than outgoing
            treasury_score += 0.3
        if features.get('unique_receivers', 0) < 10 and features.get('sent_tx_count', 0) > 10:  # Controlled outflow
            treasury_score += 0.4
        
        if treasury_score >= 0.6:
            classifications.append({
                "type": "project_treasury",
                "confidence": treasury_score,
                "description": self.wallet_categories["project_treasury"]["description"]
            })
        
        # Money laundering wallet classification
        laundering_score = 0
        if features.get('mixer_interactions', 0) > 0:  # Mixer usage
            laundering_score += 0.4
        if features.get('bridge_interactions', 0) > 3:  # Multiple bridge usage
            laundering_score += 0.3
        if features.get('risk_score', 0) > 70:  # High risk score
            laundering_score += 0.4
        
        if laundering_score >= 0.6:
            classifications.append({
                "type": "laundering",
                "confidence": laundering_score,
                "description": self.wallet_categories["laundering"]["description"]
            })
        
        # Sort classifications by confidence
        classifications.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Determine primary classification (highest confidence)
        primary_classification = classifications[0]["type"] if classifications else "unknown"
        primary_confidence = classifications[0]["confidence"] if classifications else 0
        
        return {
            "address": features.get("address"),
            "primary_type": primary_classification,
            "primary_confidence": primary_confidence,
            "classifications": classifications,
            "total_classifications": len(classifications),
            "classification_time": datetime.now().isoformat()
        }
    
    def detect_anomalies(self, address, transactions_df=None, days=90):
        """
        Detect anomalous transactions for a wallet
        
        Args:
            address (str): Wallet address to analyze
            transactions_df (pd.DataFrame, optional): Pre-loaded transactions. Defaults to None.
            days (int, optional): Number of days to look back. Defaults to 90.
            
        Returns:
            dict: Detected anomalies
        """
        self.logger.info(f"Detecting anomalies for wallet {address}")
        
        # If transactions are not provided, fetch them
        if transactions_df is None:
            # Get transactions for this address
            transactions = helius_collector.get_account_transactions(address, days=days)
            transactions_df = pd.DataFrame(transactions)
        
        if transactions_df.empty:
            return {
                "address": address,
                "anomalies_detected": False,
                "reason": "No transactions available for analysis"
            }
        
        # Filter to get transactions with amounts
        if 'amount_usd' in transactions_df.columns:
            # Remove rows with missing amount
            amount_df = transactions_df.dropna(subset=['amount_usd'])
            
            if len(amount_df) >= 10:  # Need at least 10 transactions for meaningful anomaly detection
                # Prepare features for anomaly detection
                features = amount_df[['amount_usd']].copy()
                
                # Add time-based features if available
                if 'block_time' in amount_df.columns:
                    # Sort by time
                    amount_df = amount_df.sort_values('block_time')
                    
                    # Add time difference between transactions
                    amount_df['time_diff'] = amount_df['block_time'].diff()
                    features['time_diff'] = amount_df['time_diff'].fillna(0)
                
                # Normalize features
                scaler = StandardScaler()
                features_scaled = scaler.fit_transform(features)
                
                # Apply Isolation Forest for anomaly detection
                model = IsolationForest(contamination=0.05)  # Assume 5% anomalies
                amount_df['anomaly'] = model.fit_predict(features_scaled)
                
                # Identify anomalous transactions (marked as -1 by the model)
                anomalies = amount_df[amount_df['anomaly'] == -1]
                
                if not anomalies.empty:
                    # Prepare anomaly information
                    anomaly_info = []
                    for _, anomaly in anomalies.iterrows():
                        info = {
                            "signature": anomaly.get("signature"),
                            "block_time": anomaly.get("block_time"),
                            "amount_usd": anomaly.get("amount_usd"),
                            "sender": anomaly['sender'].get('wallet') if isinstance(anomaly.get('sender'), dict) else anomaly.get('sender'),
                            "receiver": anomaly['receiver'].get('wallet') if isinstance(anomaly.get('receiver'), dict) else anomaly.get('receiver')
                        }
                        
                        # Determine anomaly reason
                        if 'amount_usd' in features.columns:
                            avg_amount = features['amount_usd'].mean()
                            std_amount = features['amount_usd'].std()
                            
                            if anomaly['amount_usd'] > avg_amount + 3 * std_amount:
                                info["reason"] = "unusually_large_amount"
                                info["details"] = f"Amount ${anomaly['amount_usd']:.2f} is {(anomaly['amount_usd'] - avg_amount) / std_amount:.1f} standard deviations above average"
                            elif 'time_diff' in features.columns and anomaly['time_diff'] > features['time_diff'].mean() + 3 * features['time_diff'].std():
                                info["reason"] = "unusual_timing"
                                info["details"] = f"Time since previous transaction ({anomaly['time_diff']:.0f} seconds) is unusually long"
                            else:
                                info["reason"] = "complex_pattern"
                                info["details"] = "Transaction exhibits unusual pattern across multiple features"
                        
                        anomaly_info.append(info)
                    
                    return {
                        "address": address,
                        "anomalies_detected": True,
                        "anomaly_count": len(anomalies),
                        "anomaly_ratio": len(anomalies) / len(amount_df),
                        "anomalies": anomaly_info,
                        "detection_time": datetime.now().isoformat()
                    }
        
        # No anomalies detected
        return {
            "address": address,
            "anomalies_detected": False,
            "reason": "No significant anomalies detected"
        }
    
    def get_entity_relationships(self, address, max_depth=2, days=90):
        """
        Map entity relationships and community connections
        
        Args:
            address (str): Wallet address to analyze
            max_depth (int, optional): Maximum relationship depth. Defaults to 2.
            days (int, optional): Number of days to look back. Defaults to 90.
            
        Returns:
            dict: Entity relationship data
        """
        self.logger.info(f"Mapping entity relationships for {address} (depth={max_depth})")
        
        # Get initial info from Range API
        address_info = range_collector.get_address_info(address)
        
        # Initialize relationships data
        relationships = {
            "address": address,
            "entity": address_info.get("entity") if address_info else None,
            "labels": address_info.get("labels") if address_info else [],
            "direct_relationships": [],
            "community_clusters": [],
            "mapping_depth": max_depth,
            "mapping_time": datetime.now().isoformat()
        }
        
        # Get counterparties (direct relationships)
        counterparties = range_collector.get_address_counterparties(address, days=days)
        
        # Process direct relationships
        for counterparty in counterparties:
            cp_address = counterparty.get("address")
            if not cp_address:
                continue
            
            # Get additional info for this counterparty
            cp_info = range_collector.get_address_info(cp_address)
            
            relationships["direct_relationships"].append({
                "address": cp_address,
                "entity": cp_info.get("entity") if cp_info else None,
                "labels": cp_info.get("labels") if cp_info else [],
                "interaction_count": counterparty.get("interaction_count", 0),
                "first_interaction": counterparty.get("first_interaction"),
                "last_interaction": counterparty.get("last_interaction"),
                "sent_volume_usd": counterparty.get("sent_volume_usd", 0),
                "received_volume_usd": counterparty.get("received_volume_usd", 0),
                "relationship_type": counterparty.get("relationship_type")
            })
        
        # Stop here if we only want direct relationships
        if max_depth <= 1:
            return relationships
        
        # Build extended relationship network for deeper analysis
        network_addresses = set([address])
        for relationship in relationships["direct_relationships"]:
            network_addresses.add(relationship["address"])
        
        # Analyze interactions between direct relationships to find clusters
        if len(network_addresses) > 1:
            # Get transactions between these addresses
            network_transactions = []
            
            # Batch processing to avoid too many API calls
            batch_size = 10
            address_list = list(network_addresses)
            
            for i in range(0, len(address_list), batch_size):
                batch = address_list[i:i+batch_size]
                
                for addr in batch:
                    # Get transactions for this address
                    addr_txs = helius_collector.get_account_transactions(addr, days=days)
                    
                    # Filter for transactions between network addresses
                    for tx in addr_txs:
                        sender = tx.get('sender', {}).get('wallet') if isinstance(tx.get('sender'), dict) else tx.get('sender')
                        receiver = tx.get('receiver', {}).get('wallet') if isinstance(tx.get('receiver'), dict) else tx.get('receiver')
                        
                        if sender in network_addresses and receiver in network_addresses:
                            network_transactions.append(tx)
            
            # Convert to DataFrame
            network_df = pd.DataFrame(network_transactions)
            
            # Use transaction analyzer to build a graph
            if not network_df.empty:
                network_graph = self.transaction_analyzer.build_transaction_graph(network_df)
                
                # Find communities/clusters in the graph
                try:
                    from networkx.algorithms import community
                    
                    # Find communities using Louvain method
                    communities = community.louvain_communities(network_graph.to_undirected())
                    
                    # Convert communities to list format
                    for i, comm in enumerate(communities):
                        community_addresses = list(comm)
                        
                        # Get info for addresses in this community
                        community_info = []
                        for comm_addr in community_addresses:
                            addr_info = range_collector.get_address_info(comm_addr)
                            comm_features = self.extract_wallet_features(comm_addr, days=days)
                            
                            community_info.append({
                                "address": comm_addr,
                                "entity": addr_info.get("entity") if addr_info else None,
                                "labels": addr_info.get("labels") if addr_info else [],
                                "transaction_count": comm_features.get("total_tx_count", 0),
                                "volume_usd": comm_features.get("total_volume_usd", 0)
                            })
                        
                        # Add community to results
                        relationships["community_clusters"].append({
                            "cluster_id": i,
                            "addresses": community_info,
                            "address_count": len(community_addresses),
                            "includes_primary": address in community_addresses
                        })
                except Exception as e:
                    self.logger.warning(f"Error finding communities: {e}")
        
        return relationships
    
    def calculate_risk_score(self, features, classification=None, anomalies=None):
        """
        Calculate comprehensive risk score for a wallet
        
        Args:
            features (dict): Wallet features
            classification (dict, optional): Wallet classification results. Defaults to None.
            anomalies (dict, optional): Detected anomalies. Defaults to None.
            
        Returns:
            dict: Risk assessment data
        """
        self.logger.info(f"Calculating risk score for {features.get('address')}")
        
        # Initialize risk assessment
        risk_assessment = {
            "address": features.get("address"),
            "risk_score": 0,
            "risk_level": "unknown",
            "risk_factors": [],
            "assessment_time": datetime.now().isoformat()
        }
        
        # Calculate risk based on features
        risk_score = 0
        risk_factors = []
        
        # Factor 1: Existing risk score from Range API
        if features.get("risk_score"):
            # Range API risk score (0-100)
            api_risk_score = features.get("risk_score")
            api_risk_weight = 0.4  # 40% weight to API risk score
            risk_score += api_risk_score * api_risk_weight
            
            risk_factors.append({
                "factor": "external_risk_assessment",
                "description": f"External risk assessment score: {api_risk_score}/100",
                "score": api_risk_score,
                "weight": api_risk_weight
            })
        
        # Factor 2: Mixer interactions
        if features.get("mixer_interactions", 0) > 0:
            mixer_risk = min(100, features.get("mixer_interactions", 0) * 20)  # 20 points per mixer interaction, max 100
            mixer_weight = 0.25  # 25% weight
            risk_score += mixer_risk * mixer_weight
            
            risk_factors.append({
                "factor": "mixer_usage",
                "description": f"Detected {features.get('mixer_interactions')} interactions with mixing services",
                "score": mixer_risk,
                "weight": mixer_weight
            })
        
        # Factor 3: Bridge usage (cross-chain activity)
        if features.get("bridge_interactions", 0) > 0:
            bridge_risk = min(80, features.get("bridge_interactions", 0) * 15)  # 15 points per bridge, max 80
            bridge_weight = 0.15  # 15% weight
            risk_score += bridge_risk * bridge_weight
            
            risk_factors.append({
                "factor": "cross_chain_activity",
                "description": f"Detected {features.get('bridge_interactions')} cross-chain bridge transactions",
                "score": bridge_risk,
                "weight": bridge_weight
            })
        
        # Factor 4: Classification-based risk
        if classification and "primary_type" in classification:
            # Risk scores by wallet type
            type_risk_scores = {
                "exchange": 30,  # Legitimate but can be used for cashing out
                "whale": 20,     # Large holders typically not high risk
                "trader": 30,    # Normal trading activity
                "bot": 40,       # Automated trading can be suspicious
                "mixer": 90,     # Very high risk
                "miner": 20,     # Mining/validator typically legitimate
                "dapp": 30,      # dApps are typically legitimate
                "contract": 20,  # Contracts typically legitimate
                "project_treasury": 20,  # Treasury typically legitimate
                "nft_trader": 30,       # NFT activity can sometimes be suspicious
                "laundering": 95,       # Extremely high risk
                "scammer": 95,          # Extremely high risk
                "unknown": 50           # Unknown classification is medium risk
            }
            
            wallet_type = classification.get("primary_type")
            type_risk = type_risk_scores.get(wallet_type, 50)
            type_confidence = classification.get("primary_confidence", 0.5)
            type_weight = 0.2  # 20% weight
            
            # Adjust risk by confidence
            adjusted_type_risk = type_risk * type_confidence
            risk_score += adjusted_type_risk * type_weight
            
            risk_factors.append({
                "factor": "wallet_classification",
                "description": f"Wallet classified as '{wallet_type}' (confidence: {type_confidence:.2f})",
                "score": adjusted_type_risk,
                "weight": type_weight
            })
        
        # Factor 5: Anomalous activity
        if anomalies and anomalies.get("anomalies_detected"):
            anomaly_count = anomalies.get("anomaly_count", 0)
            anomaly_risk = min(90, anomaly_count * 10)  # 10 points per anomaly, max 90
            anomaly_weight = 0.15  # 15% weight
            risk_score += anomaly_risk * anomaly_weight
            
            risk_factors.append({
                "factor": "anomalous_activity",
                "description": f"Detected {anomaly_count} anomalous transactions",
                "score": anomaly_risk,
                "weight": anomaly_weight
            })
        
        # Factor 6: Transaction velocity
        tx_per_day = features.get("tx_per_day", 0)
        if tx_per_day > 20:  # High velocity can be suspicious
            velocity_risk = min(70, 30 + (tx_per_day - 20) * 0.5)  # 30 base + 0.5 per tx above 20, max 70
            velocity_weight = 0.1  # 10% weight
            risk_score += velocity_risk * velocity_weight
            
            risk_factors.append({
                "factor": "high_transaction_velocity",
                "description": f"Unusually high transaction rate: {tx_per_day:.1f} transactions per day",
                "score": velocity_risk,
                "weight": velocity_weight
            })
        
        # Normalize final risk score to 0-100
        risk_assessment["risk_score"] = min(100, max(0, risk_score))
        
        # Determine risk level
        if risk_assessment["risk_score"] >= 80:
            risk_assessment["risk_level"] = "very_high"
        elif risk_assessment["risk_score"] >= 60:
            risk_assessment["risk_level"] = "high"
        elif risk_assessment["risk_score"] >= 40:
            risk_assessment["risk_level"] = "medium"
        elif risk_assessment["risk_score"] >= 20:
            risk_assessment["risk_level"] = "low"
        else:
            risk_assessment["risk_level"] = "very_low"
        
        # Add risk factors
        risk_assessment["risk_factors"] = risk_factors
        
        return risk_assessment
    
    def profile_wallet(self, address, days=90):
        """
        Generate comprehensive wallet profile
        
        Args:
            address (str): Wallet address to profile
            days (int, optional): Number of days to look back. Defaults to 90.
            
        Returns:
            dict: Comprehensive wallet profile
        """
        self.logger.info(f"Generating comprehensive profile for wallet {address}")
        
        # Get transactions for this wallet
        transactions = helius_collector.get_account_transactions(address, days=days)
        transactions_df = pd.DataFrame(transactions)
        
        # Extract wallet features
        features = self.extract_wallet_features(address, transactions_df, days=days)
        
        # Classify wallet
        classification = self.classify_wallet(features)
        
        # Detect anomalies
        anomalies = self.detect_anomalies(address, transactions_df, days=days)
        
        # Get entity relationships
        relationships = self.get_entity_relationships(address, max_depth=2, days=days)
        
        # Calculate risk score
        risk_assessment = self.calculate_risk_score(features, classification, anomalies)
        
        # Analyze transactions
        transaction_analysis = self.transaction_analyzer.analyze_transactions(address, days=days)
        
        # Compile comprehensive profile
        profile = {
            "address": address,
            "profile_generated": datetime.now().isoformat(),
            "analysis_timeframe": f"{days} days",
            "features": features,
            "classification": classification,
            "risk_assessment": risk_assessment,
            "anomalies": anomalies,
            "relationships": relationships,
            "transaction_analysis": transaction_analysis
        }
        
        # Store profile in database
        self.db.save_wallet_profile(profile)
        
        return profile

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    profiler = WalletProfiler()
    
    # Example: Profile a wallet
    if len(sys.argv) > 1:
        address = sys.argv[1]
        print(f"Profiling wallet: {address}")
        profile = profiler.profile_wallet(address)
        print(json.dumps(profile, indent=2))
    else:
        print("Please provide a wallet address to profile.")