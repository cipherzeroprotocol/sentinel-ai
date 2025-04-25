"""
Mixer Detector Module for identifying cryptocurrency mixing services
"""
import logging
import os
import sys
from datetime import datetime
import json
import pandas as pd
import numpy as np

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.collectors import helius_collector, range_collector, vybe_collector
from data.storage.address_db import get_address_data
from ai.models.pattern_detector import PatternDetector
from ai.models.relationship_mapper import RelationshipMapper
from ai.utils.ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)

class MixerDetector:
    """
    Mixer Detector module for identifying cryptocurrency mixing services
    """
    
    # Known mixer characteristics
    MIXER_CHARACTERISTICS = {
        "equal_input_output": "Equal or very similar input and output amounts",
        "fixed_denominations": "Transactions in fixed denominations (e.g., 1, 10, 100)",
        "time_delays": "Time delays between deposits and withdrawals",
        "multiple_hops": "Multiple intermediate addresses or hops",
        "high_privacy_coins": "Use of privacy-focused tokens",
        "transaction_batching": "Batching of multiple transactions",
        "similar_transaction_patterns": "Repeating patterns in transactions",
        "zero_knowledge_proofs": "Utilization of zero-knowledge proofs"
    }
    
    # Known mixers (from knowledge base)
    KNOWN_MIXERS = {
        "tor1xzb2Zyy1cUxXmyJfR8aNXuWnwHG8AwgaG7UGD4K": {
            "name": "Tornado Cash Solana",
            "type": "fixed_amount",
            "risk_level": "very_high",
            "amounts": [0.1, 1, 10, 100]  # Denominations in SOL
        },
        "1MixerZCaShtMCAdLozKTzVdLFf9WZqDehHHQdT1V5Pf": {
            "name": "SolMixer",
            "type": "variable_amount",
            "risk_level": "high"
        },
        "mixBkFZP3Z1hGWaXeYPxvyzh2Wuq2nIUQBNCZHLbwiU": {
            "name": "Cyclos Privacy Pool",
            "type": "fixed_amount",
            "risk_level": "high",
            "amounts": [1, 10, 100, 1000]  # Denominations in USDC
        }
    }
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.relationship_mapper = RelationshipMapper()
        self.ai_analyzer = AIAnalyzer()
    
    def analyze(self, address):
        """
        Analyze an address to determine if it's a mixer
        
        Args:
            address (str): Address to analyze
            
        Returns:
            dict: Analysis results
        """
        logger.info(f"Starting mixer analysis for address {address}")
        
        if not address:
            logger.error("No address provided for mixer analysis")
            return {"error": "No address provided for analysis"}
        
        # Check if this is a known mixer
        is_known_mixer = address in self.KNOWN_MIXERS
        
        # Collect data
        analysis_data = {}
        
        # Get address data
        address_data = self._collect_address_data(address)
        analysis_data['address_data'] = address_data
        
        # Collect transaction data
        transactions = self._collect_transactions(address, limit=500)  # Larger limit for mixers
        analysis_data['transactions'] = transactions
        
        # Detect patterns
        patterns = self._detect_patterns(transactions, address)
        analysis_data['patterns'] = patterns
        
        # Map relationships
        relationships = self._map_relationships(transactions, address)
        analysis_data['relationships'] = relationships
        
        # Analyze transaction patterns
        tx_pattern_analysis = self._analyze_transaction_patterns(transactions, address)
        analysis_data['tx_pattern_analysis'] = tx_pattern_analysis
        
        # Analyze user behavior
        user_analysis = self._analyze_user_behavior(transactions, relationships, address)
        analysis_data['user_analysis'] = user_analysis
        
        # Analyze volume
        volume_analysis = self._analyze_volume(transactions, address)
        analysis_data['volume_analysis'] = volume_analysis
        
        # Compare to known mixers
        comparison = self._compare_to_known_mixers(transactions, tx_pattern_analysis, volume_analysis)
        analysis_data['comparison'] = comparison
        
        # Calculate mixer confidence score
        characteristics, confidence_score = self._calculate_mixer_score(
            tx_pattern_analysis, 
            user_analysis, 
            volume_analysis, 
            comparison,
            is_known_mixer
        )
        
        # Run AI analysis
        ai_analysis = self.ai_analyzer.analyze(analysis_data, "mixer")
        
        # Combine results
        results = {
            "address": address,
            "is_known_mixer": is_known_mixer,
            "known_mixer_info": self.KNOWN_MIXERS.get(address, {}),
            "mixer_characteristics": characteristics,
            "confidence_score": confidence_score,
            "tx_pattern_analysis": tx_pattern_analysis,
            "user_analysis": user_analysis,
            "volume_analysis": volume_analysis,
            "comparison": comparison,
            "patterns": patterns,
            "ai_analysis": ai_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Completed mixer analysis for address {address}")
        
        return results
    
    def _collect_address_data(self, address):
        """
        Collect address data from various sources
        
        Args:
            address (str): Address to analyze
            
        Returns:
            dict: Combined address data
        """
        address_data = {}
        
        # Try to get address data from database first
        db_address_data = get_address_data(address)
        if db_address_data:
            address_data.update(db_address_data)
        
        # Get address data from Range API
        try:
            range_address_data = range_collector.get_address_info(address)
            if range_address_data:
                address_data.update(range_address_data)
        except Exception as e:
            logger.error(f"Error getting address data from Range: {str(e)}")
        
        # Get risk data from Range API
        try:
            risk_data = range_collector.get_address_risk_score(address)
            if risk_data:
                address_data['risk_score'] = risk_data.get('risk_score')
                address_data['risk_factors'] = risk_data.get('risk_factors', [])
        except Exception as e:
            logger.error(f"Error getting risk data from Range: {str(e)}")
        
        return address_data
    
    def _collect_transactions(self, address, limit=200):
        """
        Collect transactions for an address
        
        Args:
            address (str): Address to collect transactions for
            limit (int): Maximum number of transactions to collect
            
        Returns:
            list: Transactions
        """
        transactions = []
        
        # Get transactions from Helius API
        try:
            helius_tx_data = helius_collector.get_transaction_history(address, limit)
            
            # Get full transaction details
            for tx_info in helius_tx_data:
                if 'signature' in tx_info:
                    tx_details = helius_collector.get_transaction_details(tx_info['signature'])
                    if tx_details:
                        transactions.append(tx_details)
        except Exception as e:
            logger.error(f"Error getting transactions from Helius: {str(e)}")
        
        # Get transactions from Range API for broader coverage
        try:
            range_tx_data = range_collector.get_address_transactions(address, limit=limit)
            if range_tx_data and 'transactions' in range_tx_data:
                # Only add transactions that aren't already in the list
                existing_sigs = set(tx.get('signature') for tx in transactions if 'signature' in tx)
                for tx in range_tx_data['transactions']:
                    if 'signature' in tx and tx['signature'] not in existing_sigs:
                        transactions.append(tx)
                        existing_sigs.add(tx['signature'])
        except Exception as e:
            logger.error(f"Error getting transactions from Range: {str(e)}")
        
        return transactions
    
    def _detect_patterns(self, transactions, address=None):
        """
        Detect patterns in transaction data
        
        Args:
            transactions (list): List of transactions
            address (str, optional): Address to analyze
            
        Returns:
            dict: Detected patterns
        """
        if not transactions:
            return {}
        
        # Detect patterns
        patterns = self.pattern_detector.detect_patterns(transactions, address)
        
        return patterns
    
    def _map_relationships(self, transactions, address=None):
        """
        Map relationships in transaction data
        
        Args:
            transactions (list): List of transactions
            address (str, optional): Address to analyze
            
        Returns:
            dict: Mapped relationships
        """
        if not transactions:
            return {}
        
        # Map relationships
        relationships = self.relationship_mapper.map_relationships(transactions, [address] if address else None)
        
        return relationships
    
    def _analyze_transaction_patterns(self, transactions, address):
        """
        Analyze transaction patterns for mixer characteristics
        
        Args:
            transactions (list): List of transactions
            address (str): Address to analyze
            
        Returns:
            dict: Transaction pattern analysis
        """
        pattern_analysis = {
            "fixed_denominations": False,
            "denomination_clusters": [],
            "equal_values": False,
            "time_patterns": False,
            "multi_hop_patterns": False,
            "repeating_patterns": False,
            "batch_transactions": False,
            "denomination_confidence": 0.0,
            "transaction_scores": []
        }
        
        if not transactions:
            return pattern_analysis
        
        # Create dataframe for analysis
        try:
            df = self._create_transaction_dataframe(transactions, address)
            
            # Check for fixed denominations
            if len(df) >= 10:  # Need enough transactions for clustering
                amount_clusters = self._detect_amount_clusters(df)
                pattern_analysis["denomination_clusters"] = amount_clusters
                
                # Check if there are clear denomination clusters
                if amount_clusters and len(amount_clusters) >= 2:
                    total_txs = sum(cluster['count'] for cluster in amount_clusters)
                    clustered_txs = sum(cluster['count'] for cluster in amount_clusters 
                                      if cluster['std'] / max(0.0001, cluster['mean']) < 0.05)
                    
                    denomination_confidence = clustered_txs / total_txs if total_txs > 0 else 0
                    pattern_analysis["denomination_confidence"] = denomination_confidence
                    pattern_analysis["fixed_denominations"] = denomination_confidence > 0.5
            
            # Check for equal input/output values
            if 'input_amount' in df.columns and 'output_amount' in df.columns:
                equal_values_pct = self._check_equal_values(df)
                pattern_analysis["equal_values"] = equal_values_pct > 0.7
            
            # Check for time patterns
            time_pattern_score = self._detect_time_patterns(df)
            pattern_analysis["time_patterns"] = time_pattern_score > 0.6
            
            # Check for multi-hop patterns
            # This would require analyzing the transaction graph beyond the current function scope
            # Placeholder for now
            pattern_analysis["multi_hop_patterns"] = False
            
            # Check for repeating patterns
            repeating_score = self._detect_repeating_patterns(df)
            pattern_analysis["repeating_patterns"] = repeating_score > 0.6
            
            # Check for batch transactions
            batch_score = self._detect_batch_transactions(df)
            pattern_analysis["batch_transactions"] = batch_score > 0.6
            
            # Calculate transaction scores for each transaction
            pattern_analysis["transaction_scores"] = self._calculate_transaction_scores(df)
        
        except Exception as e:
            logger.error(f"Error analyzing transaction patterns: {str(e)}")
        
        return pattern_analysis
    
    def _create_transaction_dataframe(self, transactions, address):
        """
        Create a DataFrame from transaction data for analysis
        
        Args:
            transactions (list): List of transactions
            address (str): Address to analyze
            
        Returns:
            pandas.DataFrame: Transactions dataframe
        """
        # Extract key fields from transactions
        data = []
        
        for tx in transactions:
            # Extract base transaction info
            tx_data = {
                "signature": tx.get("signature", ""),
                "block_time": None,
                "success": True,
                "program_id": None,
                "instruction_name": None,
                "is_incoming": False,
                "is_outgoing": False,
                "counterparty": None,
                "amount": 0.0,
                "amount_usd": 0.0
            }
            
            # Extract timestamp
            if "blockTime" in tx:
                try:
                    tx_data["block_time"] = datetime.fromtimestamp(tx["blockTime"])
                except:
                    pass
            elif "block_time" in tx:
                if isinstance(tx["block_time"], str):
                    try:
                        tx_data["block_time"] = datetime.fromisoformat(tx["block_time"].replace("Z", "+00:00"))
                    except:
                        pass
                else:
                    tx_data["block_time"] = tx["block_time"]
            
            # Extract program ID
            if "program_id" in tx:
                tx_data["program_id"] = tx["program_id"]
            elif "program" in tx and isinstance(tx["program"], dict) and "id" in tx["program"]:
                tx_data["program_id"] = tx["program"]["id"]
            
            # Extract instruction name
            if "instruction_name" in tx:
                tx_data["instruction_name"] = tx["instruction_name"]
            
            # Extract sender/receiver
            sender = None
            receiver = None
            
            if "sender" in tx:
                if isinstance(tx["sender"], dict) and "wallet" in tx["sender"]:
                    sender = tx["sender"]["wallet"]
                else:
                    sender = tx["sender"]
            
            if "receiver" in tx:
                if isinstance(tx["receiver"], dict) and "wallet" in tx["receiver"]:
                    receiver = tx["receiver"]["wallet"]
                else:
                    receiver = tx["receiver"]
            
            # Determine direction and counterparty
            if sender == address:
                tx_data["is_outgoing"] = True
                tx_data["counterparty"] = receiver
            
            if receiver == address:
                tx_data["is_incoming"] = True
                tx_data["counterparty"] = sender
            
            # Extract amount
            if "amount" in tx:
                tx_data["amount"] = float(tx["amount"])
            
            if "amount_usd" in tx:
                tx_data["amount_usd"] = float(tx["amount_usd"])
            
            data.append(tx_data)
        
        # Create dataframe
        df = pd.DataFrame(data)
        
        # Add derived columns for analysis
        df["hour_of_day"] = df["block_time"].dt.hour if "block_time" in df and not df["block_time"].isna().all() else None
        df["day_of_week"] = df["block_time"].dt.dayofweek if "block_time" in df and not df["block_time"].isna().all() else None
        
        return df
    
    def _detect_amount_clusters(self, df):
        """
        Detect clusters of transaction amounts (fixed denominations)
        
        Args:
            df (pandas.DataFrame): Transaction dataframe
            
        Returns:
            list: Amount clusters
        """
        # Focus on amount in USD if available, otherwise use token amount
        amount_col = "amount_usd" if "amount_usd" in df and not df["amount_usd"].isna().all() else "amount"
        
        # Skip if no amount data
        if amount_col not in df or len(df) < 10:
            return []
        
        # Get amounts
        amounts = df[amount_col].dropna().values
        
        if len(amounts) < 10:
            return []
        
        try:
            # Use simple clustering based on amount ranges
            from sklearn.cluster import DBSCAN
            import numpy as np
            
            # Normalize amounts for clustering
            log_amounts = np.log1p(amounts.reshape(-1, 1))  # Log transform to handle different scales
            
            # Run DBSCAN clustering
            clustering = DBSCAN(eps=0.1, min_samples=3).fit(log_amounts)
            
            # Get cluster labels
            labels = clustering.labels_
            
            # Process clusters
            clusters = []
            for label in set(labels):
                if label == -1:  # Skip noise
                    continue
                
                # Get amounts in this cluster
                cluster_amounts = amounts[labels == label]
                
                # Calculate stats
                cluster = {
                    "mean": float(np.mean(cluster_amounts)),
                    "median": float(np.median(cluster_amounts)),
                    "min": float(np.min(cluster_amounts)),
                    "max": float(np.max(cluster_amounts)),
                    "std": float(np.std(cluster_amounts)),
                    "count": int(len(cluster_amounts)),
                    "percentage": float(len(cluster_amounts) / len(amounts))
                }
                
                clusters.append(cluster)
            
            # Sort by count (descending)
            clusters.sort(key=lambda x: x["count"], reverse=True)
            
            return clusters
        
        except Exception as e:
            logger.error(f"Error detecting amount clusters: {str(e)}")
            return []
    
    def _check_equal_values(self, df):
        """
        Check if input and output values are equal
        
        Args:
            df (pandas.DataFrame): Transaction dataframe
            
        Returns:
            float: Percentage of transactions with equal input/output values
        """
        # Skip if input/output amounts not available
        if "input_amount" not in df or "output_amount" not in df:
            return 0.0
        
        # Count transactions with equal or very similar input/output values
        mask = np.isclose(df["input_amount"], df["output_amount"], rtol=0.05)
        equal_count = mask.sum()
        
        # Calculate percentage
        equal_pct = equal_count / len(df) if len(df) > 0 else 0.0
        
        return equal_pct
    
    def _detect_time_patterns(self, df):
        """
        Detect patterns in transaction timing
        
        Args:
            df (pandas.DataFrame): Transaction dataframe
            
        Returns:
            float: Time pattern score
        """
        # Skip if no timestamp data
        if "block_time" not in df or df["block_time"].isna().all() or len(df) < 10:
            return 0.0
        
        try:
            # Check hour of day distribution
            hour_counts = df["hour_of_day"].value_counts().sort_index()
            
            # Check for skewed distribution
            from scipy import stats
            
            # Calculate entropy of hour distribution (lower entropy = more patterns)
            hour_probs = hour_counts / hour_counts.sum()
            hour_entropy = stats.entropy(hour_probs)
            max_entropy = np.log(24)  # Maximum entropy for 24 hours
            
            # Normalize entropy (0 = perfect pattern, 1 = uniform distribution)
            normalized_entropy = hour_entropy / max_entropy if max_entropy > 0 else 1.0
            
            # Convert to pattern score (1 - normalized_entropy)
            pattern_score = 1.0 - normalized_entropy
            
            return pattern_score
        
        except Exception as e:
            logger.error(f"Error detecting time patterns: {str(e)}")
            return 0.0
    
    def _detect_repeating_patterns(self, df):
        """
        Detect repeating patterns in transactions
        
        Args:
            df (pandas.DataFrame): Transaction dataframe
            
        Returns:
            float: Repeating pattern score
        """
        # Skip if not enough data
        if len(df) < 10:
            return 0.0
        
        try:
            # Check for repeating patterns based on amount and direction
            if "amount" in df and not df["amount"].isna().all():
                # Group by rounded amount and direction
                df["amount_rounded"] = df["amount"].round(2)
                
                # Create pattern key
                df["pattern_key"] = df.apply(
                    lambda row: f"{'in' if row['is_incoming'] else 'out'}_{row['amount_rounded']}",
                    axis=1
                )
                
                # Count patterns
                pattern_counts = df["pattern_key"].value_counts()
                
                # Calculate percentage of transactions following the top patterns
                top_pattern_count = pattern_counts.nlargest(3).sum()
                pattern_pct = top_pattern_count / len(df)
                
                return float(pattern_pct)
            
            return 0.0
        
        except Exception as e:
            logger.error(f"Error detecting repeating patterns: {str(e)}")
            return 0.0
    
    def _detect_batch_transactions(self, df):
        """
        Detect batch transaction patterns
        
        Args:
            df (pandas.DataFrame): Transaction dataframe
            
        Returns:
            float: Batch transaction score
        """
        # Skip if no timestamp data or not enough transactions
        if "block_time" not in df or df["block_time"].isna().all() or len(df) < 10:
            return 0.0
        
        try:
            # Sort by block time
            df_sorted = df.sort_values("block_time")
            
            # Calculate time differences between consecutive transactions
            df_sorted["time_diff"] = df_sorted["block_time"].diff().dt.total_seconds()
            
            # Identify batches (transactions happening within 10 seconds of each other)
            batch_threshold = 10  # seconds
            df_sorted["in_batch"] = df_sorted["time_diff"] <= batch_threshold
            
            # Count transactions in batches
            batch_count = df_sorted["in_batch"].sum()
            
            # Calculate percentage of transactions in batches
            batch_pct = batch_count / (len(df) - 1) if len(df) > 1 else 0.0
            
            return float(batch_pct)
        
        except Exception as e:
            logger.error(f"Error detecting batch transactions: {str(e)}")
            return 0.0
    
    def _calculate_transaction_scores(self, df):
        """
        Calculate mixer-characteristic scores for each transaction
        
        Args:
            df (pandas.DataFrame): Transaction dataframe
            
        Returns:
            list: Transaction scores
        """
        # Skip if dataframe is empty
        if len(df) == 0:
            return []
        
        try:
            # Get amount clusters for reference
            amount_col = "amount_usd" if "amount_usd" in df and not df["amount_usd"].isna().all() else "amount"
            
            transaction_scores = []
            
            # Analyze each transaction
            for _, row in df.iterrows():
                # Skip if no amount data
                if pd.isna(row[amount_col]):
                    continue
                
                tx_score = {
                    "signature": row["signature"],
                    "score": 0.0,
                    "factors": []
                }
                
                # Check for fixed denomination
                if "denomination_clusters" in globals():
                    for cluster in globals()["denomination_clusters"]:
                        if (row[amount_col] >= cluster["min"] and 
                            row[amount_col] <= cluster["max"]):
                            tx_score["score"] += 0.3
                            tx_score["factors"].append("fixed_denomination")
                            break
                
                # Check for round numbers
                if row[amount_col] == round(row[amount_col], 0):
                    tx_score["score"] += 0.2
                    tx_score["factors"].append("round_number")
                
                # Other factors could be added here
                
                transaction_scores.append(tx_score)
            
            return transaction_scores
        
        except Exception as e:
            logger.error(f"Error calculating transaction scores: {str(e)}")
            return []
    
    def _analyze_user_behavior(self, transactions, relationships, address):
        """
        Analyze user behavior patterns
        
        Args:
            transactions (list): List of transactions
            relationships (dict): Mapped relationships
            address (str): Address to analyze
            
        Returns:
            dict: User behavior analysis
        """
        user_analysis = {
            "unique_users": 0,
            "returning_users": 0,
            "one_time_users": 0,
            "user_distribution": {},
            "typical_user_behavior": {},
            "deposit_withdrawal_patterns": {},
            "anonymity_score": 0.0
        }
        
        if not transactions:
            return user_analysis
        
        try:
            # Extract direct relationships
            direct_relationships = relationships.get("direct", [])
            
            # Build user list
            users = {}
            
            for rel in direct_relationships:
                counterparty = None
                direction = rel.get("direction")
                
                if direction == "outgoing":
                    counterparty = rel.get("target")
                elif direction == "incoming":
                    counterparty = rel.get("source")
                
                if not counterparty or counterparty == address:
                    continue
                
                if counterparty not in users:
                    users[counterparty] = {
                        "address": counterparty,
                        "entity": rel.get("target_entity" if direction == "outgoing" else "source_entity"),
                        "labels": rel.get("target_labels" if direction == "outgoing" else "source_labels", []),
                        "deposits": 0,
                        "withdrawals": 0,
                        "deposit_volume": 0.0,
                        "withdrawal_volume": 0.0,
                        "first_interaction": rel.get("first_time"),
                        "last_interaction": rel.get("last_time"),
                        "transaction_count": rel.get("transaction_count", 0)
                    }
                
                # Update deposit/withdrawal counts
                if direction == "incoming":
                    users[counterparty]["deposits"] += rel.get("transaction_count", 0)
                    users[counterparty]["deposit_volume"] += rel.get("total_value_usd", 0)
                else:
                    users[counterparty]["withdrawals"] += rel.get("transaction_count", 0)
                    users[counterparty]["withdrawal_volume"] += rel.get("total_value_usd", 0)
            
            # Convert to list
            user_list = list(users.values())
            
            # Calculate user statistics
            user_analysis["unique_users"] = len(user_list)
            user_analysis["returning_users"] = sum(1 for user in user_list if user["transaction_count"] > 1)
            user_analysis["one_time_users"] = sum(1 for user in user_list if user["transaction_count"] == 1)
            
            # Calculate user distribution
            user_analysis["user_distribution"] = {
                "deposit_only": sum(1 for user in user_list if user["deposits"] > 0 and user["withdrawals"] == 0),
                "withdrawal_only": sum(1 for user in user_list if user["deposits"] == 0 and user["withdrawals"] > 0),
                "both": sum(1 for user in user_list if user["deposits"] > 0 and user["withdrawals"] > 0)
            }
            
            # Calculate typical user behavior
            if user_list:
                user_analysis["typical_user_behavior"] = {
                    "avg_transactions": sum(user["transaction_count"] for user in user_list) / len(user_list),
                    "avg_deposit_volume": sum(user["deposit_volume"] for user in user_list) / len(user_list),
                    "avg_withdrawal_volume": sum(user["withdrawal_volume"] for user in user_list) / len(user_list)
                }
            
            # Calculate deposit/withdrawal patterns
            deposit_users = [user for user in user_list if user["deposits"] > 0]
            withdrawal_users = [user for user in user_list if user["withdrawals"] > 0]
            
            if deposit_users and withdrawal_users:
                # Calculate ratio of deposit to withdrawal users
                deposit_withdrawal_ratio = len(deposit_users) / len(withdrawal_users) if withdrawal_users else float('inf')
                
                # Calculate average time between deposit and withdrawal
                time_between = None  # Would require detailed transaction analysis
                
                user_analysis["deposit_withdrawal_patterns"] = {
                    "deposit_withdrawal_ratio": deposit_withdrawal_ratio,
                    "time_between": time_between
                }
            
            # Calculate anonymity score
            anonymity_factors = []
            
            # Factor 1: Percentage of one-time users (higher = more anonymous)
            one_time_pct = user_analysis["one_time_users"] / user_analysis["unique_users"] if user_analysis["unique_users"] > 0 else 0
            anonymity_factors.append(one_time_pct)
            
            # Factor 2: Ratio of users with both deposits and withdrawals (lower = more anonymous)
            both_pct = user_analysis["user_distribution"]["both"] / user_analysis["unique_users"] if user_analysis["unique_users"] > 0 else 0
            anonymity_factors.append(1.0 - both_pct)
            
            # Calculate average anonymity score
            user_analysis["anonymity_score"] = sum(anonymity_factors) / len(anonymity_factors) if anonymity_factors else 0.0
        
        except Exception as e:
            logger.error(f"Error analyzing user behavior: {str(e)}")
        
        return user_analysis
    
    def _analyze_volume(self, transactions, address):
        """
        Analyze transaction volume
        
        Args:
            transactions (list): List of transactions
            address (str): Address to analyze
            
        Returns:
            dict: Volume analysis
        """
        volume_analysis = {
            "total_volume_usd": 0.0,
            "incoming_volume_usd": 0.0,
            "outgoing_volume_usd": 0.0,
            "daily_average_volume_usd": 0.0,
            "volume_distribution": {},
            "denomination_distribution": {},
            "temporal_patterns": {},
            "volume_growth": None
        }
        
        if not transactions:
            return volume_analysis
        
        try:
            # Create dataframe for analysis
            df = self._create_transaction_dataframe(transactions, address)
            
            # Calculate total volume
            if "amount_usd" in df and not df["amount_usd"].isna().all():
                volume_analysis["total_volume_usd"] = float(df["amount_usd"].sum())
                volume_analysis["incoming_volume_usd"] = float(df.loc[df["is_incoming"], "amount_usd"].sum())
                volume_analysis["outgoing_volume_usd"] = float(df.loc[df["is_outgoing"], "amount_usd"].sum())
            elif "amount" in df and not df["amount"].isna().all():
                volume_analysis["total_volume"] = float(df["amount"].sum())
                volume_analysis["incoming_volume"] = float(df.loc[df["is_incoming"], "amount"].sum())
                volume_analysis["outgoing_volume"] = float(df.loc[df["is_outgoing"], "amount"].sum())
            
            # Calculate daily average volume
            if "block_time" in df and not df["block_time"].isna().all():
                # Get date range
                min_date = df["block_time"].min()
                max_date = df["block_time"].max()
                
                if min_date and max_date:
                    days = (max_date - min_date).days + 1
                    
                    if days > 0:
                        daily_avg = volume_analysis["total_volume_usd"] / days
                        volume_analysis["daily_average_volume_usd"] = float(daily_avg)
                
                # Calculate volume distribution by day of week
                df["day_of_week"] = df["block_time"].dt.dayofweek
                
                if "amount_usd" in df and not df["amount_usd"].isna().all():
                    volume_by_day = df.groupby("day_of_week")["amount_usd"].sum()
                elif "amount" in df and not df["amount"].isna().all():
                    volume_by_day = df.groupby("day_of_week")["amount"].sum()
                else:
                    volume_by_day = None
                
                if volume_by_day is not None:
                    volume_analysis["volume_distribution"]["by_day_of_week"] = {
                        f"day_{day}": float(volume) for day, volume in volume_by_day.items()
                    }
                
                # Calculate temporal patterns
                df["hour"] = df["block_time"].dt.hour
                
                if "amount_usd" in df and not df["amount_usd"].isna().all():
                    volume_by_hour = df.groupby("hour")["amount_usd"].sum()
                elif "amount" in df and not df["amount"].isna().all():
                    volume_by_hour = df.groupby("hour")["amount"].sum()
                else:
                    volume_by_hour = None
                
                if volume_by_hour is not None:
                    volume_analysis["temporal_patterns"]["by_hour"] = {
                        f"hour_{hour}": float(volume) for hour, volume in volume_by_hour.items()
                    }
            
            # Calculate denomination distribution
            if "amount_usd" in df and not df["amount_usd"].isna().all():
                # Round to nearest integer for binning
                df["amount_rounded"] = df["amount_usd"].round()
                
                denom_counts = df["amount_rounded"].value_counts().sort_index()
                
                # Convert to dictionary (top 10 denominations)
                top_denoms = denom_counts.nlargest(10)
                
                volume_analysis["denomination_distribution"] = {
                    f"amount_{amount}": int(count) for amount, count in top_denoms.items()
                }
            
            # Calculate volume growth (monthly)
            if "block_time" in df and not df["block_time"].isna().all():
                df["month"] = df["block_time"].dt.to_period("M")
                
                if "amount_usd" in df and not df["amount_usd"].isna().all():
                    volume_by_month = df.groupby("month")["amount_usd"].sum()
                elif "amount" in df and not df["amount"].isna().all():
                    volume_by_month = df.groupby("month")["amount"].sum()
                else:
                    volume_by_month = None
                
                if volume_by_month is not None and len(volume_by_month) > 1:
                    # Convert to list for output
                    month_data = [
                        {"month": str(month), "volume": float(volume)}
                        for month, volume in volume_by_month.items()
                    ]
                    
                    # Sort by month
                    month_data.sort(key=lambda x: x["month"])
                    
                    volume_analysis["volume_growth"] = month_data
        
        except Exception as e:
            logger.error(f"Error analyzing volume: {str(e)}")
        
        return volume_analysis
    
    def _compare_to_known_mixers(self, transactions, tx_pattern_analysis, volume_analysis):
        """
        Compare address behavior to known mixers
        
        Args:
            transactions (list): List of transactions
            tx_pattern_analysis (dict): Transaction pattern analysis
            volume_analysis (dict): Volume analysis
            
        Returns:
            dict: Comparison to known mixers
        """
        comparison = {
            "similarity_scores": {},
            "most_similar": None,
            "distinctive_features": [],
            "mixer_likelihood": 0.0
        }
        
        # Define known mixer characteristics
        known_mixer_features = {
            "tornado_cash": {
                "fixed_denominations": True,
                "equal_values": True,
                "time_delays": True,
                "deposit_withdrawal_separation": True,
                "anonymity_focus": "very_high"
            },
            "cyclone": {
                "fixed_denominations": True,
                "equal_values": False,
                "time_delays": True,
                "deposit_withdrawal_separation": True,
                "anonymity_focus": "high"
            },
            "generic_mixer": {
                "fixed_denominations": True,
                "equal_values": True,
                "time_delays": True,
                "deposit_withdrawal_separation": True,
                "anonymity_focus": "high"
            }
        }
        
        try:
            # Calculate similarity scores
            similarity_scores = {}
            
            for mixer_name, features in known_mixer_features.items():
                score = 0.0
                matches = 0
                total = 0
                
                # Check fixed denominations
                if features["fixed_denominations"] == tx_pattern_analysis.get("fixed_denominations", False):
                    score += 1.0
                    matches += 1
                total += 1
                
                # Check equal values
                if features["equal_values"] == tx_pattern_analysis.get("equal_values", False):
                    score += 1.0
                    matches += 1
                total += 1
                
                # Check time patterns
                if features["time_delays"] == tx_pattern_analysis.get("time_patterns", False):
                    score += 1.0
                    matches += 1
                total += 1
                
                # Calculate similarity percentage
                similarity = score / total if total > 0 else 0.0
                similarity_scores[mixer_name] = similarity
            
            # Find most similar mixer
            if similarity_scores:
                most_similar = max(similarity_scores.items(), key=lambda x: x[1])
                comparison["most_similar"] = {
                    "name": most_similar[0],
                    "similarity": most_similar[1]
                }
            
            # Identify distinctive features
            distinctive_features = []
            
            if tx_pattern_analysis.get("fixed_denominations", False):
                distinctive_features.append("Uses fixed denominations like known mixers")
            
            if tx_pattern_analysis.get("equal_values", False):
                distinctive_features.append("Maintains equal input/output values like mixers")
            
            if tx_pattern_analysis.get("time_patterns", False):
                distinctive_features.append("Shows time delay patterns consistent with mixing")
            
            if tx_pattern_analysis.get("repeating_patterns", False):
                distinctive_features.append("Exhibits repeating transaction patterns typical of mixers")
            
            comparison["distinctive_features"] = distinctive_features
            
            # Calculate overall mixer likelihood
            feature_weights = {
                "fixed_denominations": 0.3,
                "equal_values": 0.2,
                "time_patterns": 0.15,
                "repeating_patterns": 0.15,
                "batch_transactions": 0.1,
                "similar_to_known": 0.1
            }
            
            likelihood_score = 0.0
            
            if tx_pattern_analysis.get("fixed_denominations", False):
                likelihood_score += feature_weights["fixed_denominations"]
            
            if tx_pattern_analysis.get("equal_values", False):
                likelihood_score += feature_weights["equal_values"]
            
            if tx_pattern_analysis.get("time_patterns", False):
                likelihood_score += feature_weights["time_patterns"]
            
            if tx_pattern_analysis.get("repeating_patterns", False):
                likelihood_score += feature_weights["repeating_patterns"]
            
            if tx_pattern_analysis.get("batch_transactions", False):
                likelihood_score += feature_weights["batch_transactions"]
            
            if comparison["most_similar"] and comparison["most_similar"]["similarity"] > 0.7:
                likelihood_score += feature_weights["similar_to_known"]
            
            comparison["mixer_likelihood"] = likelihood_score
            comparison["similarity_scores"] = similarity_scores
        
        except Exception as e:
            logger.error(f"Error comparing to known mixers: {str(e)}")
        
        return comparison
    
    def _calculate_mixer_score(self, tx_pattern_analysis, user_analysis, volume_analysis, comparison, is_known_mixer):
        """
        Calculate overall mixer confidence score
        
        Args:
            tx_pattern_analysis (dict): Transaction pattern analysis
            user_analysis (dict): User behavior analysis
            volume_analysis (dict): Volume analysis
            comparison (dict): Comparison to known mixers
            is_known_mixer (bool): Whether the address is a known mixer
            
        Returns:
            tuple: (characteristics, confidence_score)
        """
        # If it's a known mixer, return high confidence
        if is_known_mixer:
            characteristics = list(self.MIXER_CHARACTERISTICS.keys())
            return characteristics, 1.0
        
        # Initialize characteristics and scores
        characteristics = []
        feature_scores = {}
        
        # Check for equal input/output amounts
        if tx_pattern_analysis.get("equal_values", False):
            characteristics.append("equal_input_output")
            feature_scores["equal_input_output"] = 0.9
        
        # Check for fixed denominations
        if tx_pattern_analysis.get("fixed_denominations", False) and tx_pattern_analysis.get("denomination_confidence", 0.0) > 0.5:
            characteristics.append("fixed_denominations")
            feature_scores["fixed_denominations"] = tx_pattern_analysis.get("denomination_confidence", 0.0)
        
        # Check for time delays
        if tx_pattern_analysis.get("time_patterns", False):
            characteristics.append("time_delays")
            feature_scores["time_delays"] = 0.7
        
        # Check for multi-hop patterns
        if tx_pattern_analysis.get("multi_hop_patterns", False):
            characteristics.append("multiple_hops")
            feature_scores["multiple_hops"] = 0.8
        
        # Check for transaction batching
        if tx_pattern_analysis.get("batch_transactions", False):
            characteristics.append("transaction_batching")
            feature_scores["transaction_batching"] = 0.7
        
        # Check for similar transaction patterns
        if tx_pattern_analysis.get("repeating_patterns", False):
            characteristics.append("similar_transaction_patterns")
            feature_scores["similar_transaction_patterns"] = 0.8
        
        # Add anonymity factor
        anonymity_score = user_analysis.get("anonymity_score", 0.0)
        if anonymity_score > 0.7:
            characteristics.append("high_anonymity")
            feature_scores["high_anonymity"] = anonymity_score
        
        # Calculate weighted score
        feature_weights = {
            "equal_input_output": 0.20,
            "fixed_denominations": 0.25,
            "time_delays": 0.15,
            "multiple_hops": 0.15,
            "transaction_batching": 0.10,
            "similar_transaction_patterns": 0.10,
            "high_anonymity": 0.05
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for feature, score in feature_scores.items():
            if feature in feature_weights:
                weight = feature_weights[feature]
                weighted_score += score * weight
                total_weight += weight
        
        # Normalize score
        confidence_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Factor in comparison to known mixers
        mixer_likelihood = comparison.get("mixer_likelihood", 0.0)
        
        # Combine scores (70% features, 30% comparison)
        confidence_score = (confidence_score * 0.7) + (mixer_likelihood * 0.3)
        
        return characteristics, confidence_score

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    # Create analyzer
    detector = MixerDetector()
    
    # Test address (example, should be replaced with a real address)
    address = "tor1xzb2Zyy1cUxXmyJfR8aNXuWnwHG8AwgaG7UGD4K"
    
    # Run analysis
    result = detector.analyze(address)
    
    # Print result
    print(json.dumps(result, indent=2))