"""
Transaction Analyzer - Shared component for Sentinel AI platform

This module provides shared functionality for analyzing Solana transactions, including:
1. Transaction flow visualization and pattern detection
2. Risk assessment and anomaly detection
3. Token flow tracking across multiple transactions
4. Cross-chain transaction tracing
"""

import logging
import os
import sys
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
import networkx as nx
from collections import defaultdict

# Add the project root to the Python path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) # Removed, assuming proper package structure

import data.collectors.helius_collector as helius_collector
import data.collectors.range_collector as range_collector
from data.storage.address_db import AddressDatabase


class TransactionAnalyzer:
    """Shared component for analyzing Solana transactions"""
    
    def __init__(self, db_path=None):
        """
        Initialize the TransactionAnalyzer
        
        Args:
            db_path (str, optional): Path to the SQLite database. Defaults to None.
        """
        self.logger = logging.getLogger(__name__)
        self.db = AddressDatabase(db_path)
        
        # Define known programs for categorizing transactions
        self.known_programs = {
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "Token Program",
            "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb": "Token-2022 Program",
            "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB": "Jupiter Aggregator",
            "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Raydium Swap",
            "wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb": "Wormhole",
            "marea3UiXK2AkPyQLZ56npJT6D7vnxQgJ7SDMQkFC9Z": "Meteora",
            "orcanEwBWRvkf8XTp1iYk8KgEnEw6IxJ9w6sc9Jcx6N": "Orca Swap"
        }
        
        # Bridge programs for cross-chain analysis
        self.bridge_programs = {
            "wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb": "Wormhole",
            "3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5": "Wormhole: Portal",
            "worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth": "Wormhole: Token Bridge",
            "3CEbPFMdBeWpX1z9QgKDdmBbTdJ7gYLjE2GQJ5uoVP7P": "Allbridge",
            "6Cust4zaiNJJDkJZZbdS4wHfNXdgGu8EGRmAT9FW3cZb": "Portal Bridge"
        }
        
        # Common tokens for easier identification
        self.common_tokens = {
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
                "symbol": "USDC",
                "name": "USD Coin"
            },
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {
                "symbol": "USDT", 
                "name": "Tether USD"
            },
            "So11111111111111111111111111111111111111112": {
                "symbol": "SOL",
                "name": "Wrapped SOL"
            }
        }
    
    def get_program_name(self, program_id):
        """
        Get the name of a program based on its ID
        
        Args:
            program_id (str): Program ID
            
        Returns:
            str: Program name if known, otherwise program ID
        """
        return self.known_programs.get(program_id, program_id)
    
    def is_bridge_program(self, program_id):
        """
        Check if a program is a bridge program
        
        Args:
            program_id (str): Program ID
            
        Returns:
            bool: True if it's a bridge program, False otherwise
        """
        return program_id in self.bridge_programs
    
    def get_token_info(self, mint_address):
        """
        Get token information based on mint address
        
        Args:
            mint_address (str): Token mint address
            
        Returns:
            dict: Token information if known, None otherwise
        """
        # Check if it's in our common tokens list
        if mint_address in self.common_tokens:
            return self.common_tokens[mint_address]
        
        # Otherwise, try to fetch from Vybe API
        try:
            token_info = self.vybe_collector.get_token_info(mint_address)
            if (token_info):
                return {
                    "symbol": token_info.get("symbol"),
                    "name": token_info.get("name")
                }
        except Exception as e:
            self.logger.warning(f"Failed to fetch token info for {mint_address}: {e}")
        
        return {"symbol": "Unknown", "name": "Unknown Token"}
    
    def fetch_transactions(self, address=None, signatures=None, days=30):
        """Fetches transactions by address or signatures."""
        transactions = []
        if signatures:
            # Fetch by signature
            for sig in signatures:
                try:
                    tx_details = helius_collector.get_transaction_details(sig)
                    if tx_details:
                        transactions.append(tx_details)
                except Exception as e:
                    logger.error(f"Error fetching transaction details for {sig}: {e}")
        elif address:
            # Fetch by address
            try:
                # Corrected method call: Use get_transaction_history
                address_txs = helius_collector.get_transaction_history(address) # Removed days=days if not supported

                # Apply filtering if needed (similar to DustingAnalyzer._filter_transactions_by_days)
                if days > 0:
                     address_txs = self._filter_transactions_by_days(address_txs, days) # Add this helper method if needed

                # Optionally fetch full details if history only returns signatures/basic info
                # This depends on what get_transaction_history returns
                # If it returns full details, the following loop might be redundant
                detailed_txs = []
                for tx_info in address_txs:
                    sig = tx_info.get('signature')
                    if sig:
                         # Avoid re-fetching if details are already present
                         if 'transaction' in tx_info and 'message' in tx_info['transaction']:
                              detailed_txs.append(tx_info)
                         else:
                              try:
                                   tx_details = helius_collector.get_transaction_details(sig)
                                   if tx_details:
                                        detailed_txs.append(tx_details)
                              except Exception as e:
                                   logger.error(f"Error fetching transaction details for {sig} in analyzer: {e}")
                    else: # If no signature, maybe it's already detailed?
                         detailed_txs.append(tx_info)
                transactions = detailed_txs

            except Exception as e:
                logger.error(f"Error fetching transactions for {address} in TransactionAnalyzer: {e}")

        # Convert to DataFrame for easier analysis
        if transactions:
            return pd.DataFrame(transactions)
        else:
            return pd.DataFrame()

    # Add this helper method if needed for filtering by days
    def _filter_transactions_by_days(self, transactions, days):
        """Filters transactions to include only those within the specified number of days."""
        if not transactions or days <= 0:
            return transactions

        cutoff_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
        filtered_txs = []

        for tx in transactions:
            tx_time = None
            # Extract timestamp (similar logic as in DustingAnalyzer)
            if "blockTime" in tx and tx["blockTime"] is not None:
                tx_time = tx["blockTime"]
            elif "block_time" in tx and tx["block_time"] is not None:
                 # Handle string, datetime, or timestamp formats
                 if isinstance(tx["block_time"], str):
                     try: tx_time = datetime.fromisoformat(tx["block_time"].replace("Z", "+00:00")).timestamp()
                     except ValueError: pass
                 elif isinstance(tx["block_time"], (datetime, pd.Timestamp)): tx_time = tx["block_time"].timestamp()
                 elif isinstance(tx["block_time"], (int, float)): tx_time = tx["block_time"]

            if tx_time is None or tx_time >= cutoff_timestamp:
                filtered_txs.append(tx)

        return filtered_txs

    def build_transaction_graph(self, transactions_df, include_tokens=True):
        """
        Build a graph representation of transaction flows
        
        Args:
            transactions_df (pd.DataFrame): DataFrame of transactions
            include_tokens (bool, optional): Whether to include token nodes. Defaults to True.
            
        Returns:
            nx.DiGraph: Directed graph of transaction flows
        """
        self.logger.info("Building transaction graph")
        
        G = nx.DiGraph()
        
        if transactions_df.empty:
            return G
        
        # Process each transaction
        for _, tx in transactions_df.iterrows():
            # Add sender and receiver if available
            if 'sender' in tx and 'receiver' in tx:
                sender = tx['sender'].get('wallet') if isinstance(tx['sender'], dict) else tx['sender']
                receiver = tx['receiver'].get('wallet') if isinstance(tx['receiver'], dict) else tx['receiver']
                
                if sender and receiver:
                    # Add nodes if they don't exist
                    if not G.has_node(sender):
                        G.add_node(sender, type='address')
                    
                    if not G.has_node(receiver):
                        G.add_node(receiver, type='address')
                    
                    # Add edge or update existing edge
                    if not G.has_edge(sender, receiver):
                        G.add_edge(sender, receiver, transactions=[], weight=0)
                    
                    edge_data = G.get_edge_data(sender, receiver)
                    edge_data['transactions'].append({
                        'signature': tx.get('signature'),
                        'block_time': tx.get('block_time'),
                        'amount': tx.get('amount'),
                        'amount_usd': tx.get('amount_usd')
                    })
                    
                    # Update edge weight based on transaction count
                    edge_data['weight'] = len(edge_data['transactions'])
            
            # Add token information if available and requested
            if include_tokens and 'mint' in tx:
                mint = tx['mint']
                
                if mint:
                    # Add token node if it doesn't exist
                    if not G.has_node(mint):
                        token_info = self.get_token_info(mint)
                        G.add_node(mint, type='token', symbol=token_info.get('symbol'), name=token_info.get('name'))
                    
                    # Connect sender and receiver to token
                    if 'sender' in tx and 'receiver' in tx:
                        sender = tx['sender'].get('wallet') if isinstance(tx['sender'], dict) else tx['sender']
                        receiver = tx['receiver'].get('wallet') if isinstance(tx['receiver'], dict) else tx['receiver']
                        
                        if sender and mint:
                            if not G.has_edge(sender, mint):
                                G.add_edge(sender, mint, transactions=[], relation='sends')
                            
                            edge_data = G.get_edge_data(sender, mint)
                            if 'signature' in tx:
                                edge_data['transactions'].append(tx['signature'])
                        
                        if mint and receiver:
                            if not G.has_edge(mint, receiver):
                                G.add_edge(mint, receiver, transactions=[], relation='received_by')
                            
                            edge_data = G.get_edge_data(mint, receiver)
                            if 'signature' in tx:
                                edge_data['transactions'].append(tx['signature'])
        
        # Add program information if available
        if 'program' in transactions_df.columns:
            for _, tx in transactions_df.iterrows():
                if isinstance(tx['program'], dict) and 'id' in tx['program']:
                    program_id = tx['program']['id']
                    program_name = self.get_program_name(program_id)
                    
                    # Add program node
                    if not G.has_node(program_id):
                        G.add_node(program_id, type='program', name=program_name)
                    
                    # Connect sender to program
                    if 'sender' in tx:
                        sender = tx['sender'].get('wallet') if isinstance(tx['sender'], dict) else tx['sender']
                        
                        if sender:
                            if not G.has_edge(sender, program_id):
                                G.add_edge(sender, program_id, transactions=[], relation='calls')
                            
                            edge_data = G.get_edge_data(sender, program_id)
                            if 'signature' in tx:
                                edge_data['transactions'].append(tx['signature'])
        
        return G
    
    def identify_transaction_patterns(self, transactions_df):
        """
        Identify common transaction patterns
        
        Args:
            transactions_df (pd.DataFrame): DataFrame of transactions
            
        Returns:
            dict: Dictionary of identified patterns
        """
        self.logger.info("Identifying transaction patterns")
        
        patterns = {}
        
        if transactions_df.empty:
            return patterns
        
        # Check for swaps
        if 'program' in transactions_df.columns:
            # Look for DEX programs
            dex_programs = ["JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB", "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc", "orcanEwBWRvkf8XTp1iYk8KgEnEw6IxJ9w6sc9Jcx6N"]
            
            dex_txs = transactions_df[
                transactions_df['program'].apply(
                    lambda x: x.get('id') in dex_programs if isinstance(x, dict) and 'id' in x else False
                )
            ]
            
            if not dex_txs.empty:
                patterns['swaps'] = {
                    'count': len(dex_txs),
                    'percentage': len(dex_txs) / len(transactions_df) * 100,
                    'programs': dex_txs['program'].apply(
                        lambda x: x.get('id') if isinstance(x, dict) and 'id' in x else None
                    ).value_counts().to_dict()
                }
        
        # Check for bridge transactions
        bridge_txs = transactions_df[
            transactions_df['program'].apply(
                lambda x: self.is_bridge_program(x.get('id')) if isinstance(x, dict) and 'id' in x else False
            )
        ]
        
        if not bridge_txs.empty:
            patterns['bridges'] = {
                'count': len(bridge_txs),
                'percentage': len(bridge_txs) / len(transactions_df) * 100,
                'programs': bridge_txs['program'].apply(
                    lambda x: x.get('id') if isinstance(x, dict) and 'id' in x else None
                ).value_counts().to_dict()
            }
        
        # Check for circular flows (potential wash trading or money laundering)
        if 'sender' in transactions_df.columns and 'receiver' in transactions_df.columns:
            # Extract sender and receiver addresses
            transactions_df['sender_address'] = transactions_df['sender'].apply(
                lambda x: x.get('wallet') if isinstance(x, dict) else x
            )
            
            transactions_df['receiver_address'] = transactions_df['receiver'].apply(
                lambda x: x.get('wallet') if isinstance(x, dict) else x
            )
            
            # Build a graph of sender->receiver
            flow_graph = nx.DiGraph()
            
            for _, row in transactions_df.iterrows():
                sender = row['sender_address']
                receiver = row['receiver_address']
                
                if sender and receiver:
                    if not flow_graph.has_edge(sender, receiver):
                        flow_graph.add_edge(sender, receiver, weight=0)
                    
                    # Increment weight
                    flow_graph[sender][receiver]['weight'] += 1
            
            # Find cycles in the graph
            try:
                cycles = list(nx.simple_cycles(flow_graph))
                if cycles:
                    patterns['circular_flows'] = {
                        'count': len(cycles),
                        'cycles': [cycle for cycle in cycles if len(cycle) <= 5]  # Limit to small cycles for readability
                    }
            except:
                self.logger.warning("Error finding cycles in transaction graph")
        
        # Check for high-frequency trading
        if 'block_time' in transactions_df.columns and 'sender' in transactions_df.columns:
            # Group by sender
            transactions_df['sender_address'] = transactions_df['sender'].apply(
                lambda x: x.get('wallet') if isinstance(x, dict) else x
            )
            
            # Sort by time
            sorted_df = transactions_df.sort_values('block_time')
            
            high_frequency_senders = {}
            
            for sender in sorted_df['sender_address'].unique():
                sender_txs = sorted_df[sorted_df['sender_address'] == sender]
                
                # Calculate time differences between consecutive transactions
                if len(sender_txs) >= 5:  # Only consider senders with at least 5 transactions
                    sender_txs = sender_txs.sort_values('block_time')
                    time_diffs = []
                    
                    for i in range(1, len(sender_txs)):
                        prev_time = sender_txs.iloc[i-1]['block_time']
                        curr_time = sender_txs.iloc[i]['block_time']
                        time_diffs.append(curr_time - prev_time)
                    
                    # Calculate average time between transactions
                    if time_diffs:
                        avg_time_diff = sum(time_diffs) / len(time_diffs)
                        
                        # If average time is less than 1 minute (60 seconds), consider high frequency
                        if avg_time_diff < 60:
                            high_frequency_senders[sender] = {
                                'transaction_count': len(sender_txs),
                                'avg_time_between_txs': avg_time_diff,
                                'shortest_time_between_txs': min(time_diffs) if time_diffs else None
                            }
            
            if high_frequency_senders:
                patterns['high_frequency_trading'] = {
                    'count': len(high_frequency_senders),
                    'senders': high_frequency_senders
                }
        
        # Check for token concentration (many tokens going to the same address)
        if 'receiver' in transactions_df.columns:
            transactions_df['receiver_address'] = transactions_df['receiver'].apply(
                lambda x: x.get('wallet') if isinstance(x, dict) else x
            )
            
            receiver_counts = transactions_df['receiver_address'].value_counts()
            high_concentration_receivers = receiver_counts[receiver_counts > 10].to_dict()
            
            if high_concentration_receivers:
                patterns['token_concentration'] = {
                    'count': len(high_concentration_receivers),
                    'receivers': {addr: count for addr, count in high_concentration_receivers.items()}
                }
        
        return patterns
    
    def trace_token_flow(self, start_transaction, max_depth=3):
        """
        Trace the flow of tokens starting from a specific transaction
        
        Args:
            start_transaction (str): Signature of the starting transaction
            max_depth (int, optional): Maximum depth to trace. Defaults to 3.
            
        Returns:
            dict: Token flow data
        """
        self.logger.info(f"Tracing token flow from transaction {start_transaction}")
        
        # Get the start transaction
        start_tx = helius_collector.get_transaction(start_transaction)
        if not start_tx:
            return {"error": "Start transaction not found"}
        
        # Initialize flow tracking
        flow = {
            "start_transaction": start_transaction,
            "token": start_tx.get("mint"),
            "token_info": self.get_token_info(start_tx.get("mint")) if start_tx.get("mint") else None,
            "amount": start_tx.get("amount"),
            "amount_usd": start_tx.get("amount_usd"),
            "flow_steps": []
        }
        
        # Track addresses that have received tokens
        to_explore = [(
            start_tx.get("receiver", {}).get("wallet") if isinstance(start_tx.get("receiver"), dict) else start_tx.get("receiver"),
            start_tx.get("mint"),
            start_tx.get("amount"),
            0  # Depth
        )]
        
        explored = set()
        
        # Explore token flows up to max_depth
        while to_explore and len(flow["flow_steps"]) < 100:  # Limit to 100 steps for performance
            current_address, token, amount, depth = to_explore.pop(0)
            
            if depth >= max_depth or (current_address, token) in explored:
                continue
            
            explored.add((current_address, token))
            
            # Get outgoing transactions for this address with this token
            outgoing_txs = helius_collector.get_token_transfers(
                sender_address=current_address, 
                mint_address=token, 
                limit=10  # Limit to recent transactions for performance
            )
            
            if not outgoing_txs:
                continue
            
            # Add each outgoing transaction to the flow
            for tx in outgoing_txs:
                receiver = tx.get("receiver", {}).get("wallet") if isinstance(tx.get("receiver"), dict) else tx.get("receiver")
                
                if not receiver:
                    continue
                
                # Add this step to the flow
                flow["flow_steps"].append({
                    "from": current_address,
                    "to": receiver,
                    "transaction": tx.get("signature"),
                    "block_time": tx.get("block_time"),
                    "amount": tx.get("amount"),
                    "amount_usd": tx.get("amount_usd"),
                    "depth": depth
                })
                
                # Add the next address to explore
                to_explore.append((receiver, token, tx.get("amount"), depth + 1))
        
        return flow
    
    def detect_cross_chain_transfers(self, transactions_df):
        """
        Detect cross-chain transfers in transactions
        
        Args:
            transactions_df (pd.DataFrame): DataFrame of transactions
            
        Returns:
            list: List of detected cross-chain transfers
        """
        self.logger.info("Detecting cross-chain transfers")
        
        cross_chain_transfers = []
        
        if transactions_df.empty:
            return cross_chain_transfers
        
        # Look for bridge program interactions
        bridge_txs = transactions_df[
            transactions_df['program'].apply(
                lambda x: self.is_bridge_program(x.get('id')) if isinstance(x, dict) and 'id' in x else False
            )
        ]
        
        # For each bridge transaction, get cross-chain details
        for _, tx in bridge_txs.iterrows():
            signature = tx.get("signature")
            if not signature:
                continue
            
            # Use Range API to get cross-chain information
            cross_chain_data = range_collector.get_cross_chain_transaction(signature)
            
            if cross_chain_data:
                cross_chain_transfers.append({
                    "solana_transaction": signature,
                    "bridge_program": tx["program"].get("id") if isinstance(tx["program"], dict) else None,
                    "bridge_name": self.bridge_programs.get(
                        tx["program"].get("id") if isinstance(tx["program"], dict) else None
                    ),
                    "source_chain": "solana",
                    "destination_chain": cross_chain_data.get("destination_chain"),
                    "destination_address": cross_chain_data.get("destination_address"),
                    "token": tx.get("mint"),
                    "token_info": self.get_token_info(tx.get("mint")),
                    "amount": tx.get("amount"),
                    "amount_usd": tx.get("amount_usd"),
                    "block_time": tx.get("block_time")
                })
        
        return cross_chain_transfers
    
    def calculate_transaction_risk(self, transactions_df):
        """
        Calculate risk scores for transactions
        
        Args:
            transactions_df (pd.DataFrame): DataFrame of transactions
            
        Returns:
            dict: Risk assessment data
        """
        self.logger.info("Calculating transaction risk scores")
        
        risk_data = {
            "overall_risk_score": 0,
            "high_risk_transactions": [],
            "risk_factors": defaultdict(int)
        }
        
        if transactions_df.empty:
            return risk_data
        
        # Get risk scores from Range API for each transaction
        total_risk_score = 0
        high_risk_txs = []
        
        for _, tx in transactions_df.iterrows():
            signature = tx.get("signature")
            if not signature:
                continue
            
            # Check if risk_score is already in the DataFrame
            risk_score = tx.get("risk_score")
            risk_factors = tx.get("risk_factors")
            
            if risk_score is None:
                # Fetch risk data from Range API
                risk_data_tx = range_collector.get_transaction_risk(signature)
                if risk_data_tx:
                    risk_score = risk_data_tx.get("risk_score", 0)
                    risk_factors = risk_data_tx.get("risk_factors", [])
            
            # Process risk factors
            if isinstance(risk_factors, str):
                try:
                    risk_factors = json.loads(risk_factors.replace("'", "\""))
                except:
                    risk_factors = []
            
            # Add to total risk score
            if risk_score is not None:
                total_risk_score += risk_score
                
                # Add high risk transactions
                if risk_score >= 70:
                    high_risk_txs.append({
                        "signature": signature,
                        "risk_score": risk_score,
                        "block_time": tx.get("block_time"),
                        "amount": tx.get("amount"),
                        "amount_usd": tx.get("amount_usd"),
                        "risk_factors": risk_factors
                    })
                
                # Count risk factors
                for factor in risk_factors:
                    if isinstance(factor, dict):
                        factor_name = factor.get("name")
                        if factor_name:
                            risk_data["risk_factors"][factor_name] += 1
                    elif isinstance(factor, str):
                        risk_data["risk_factors"][factor] += 1
        
        # Calculate overall risk score
        if len(transactions_df) > 0:
            risk_data["overall_risk_score"] = total_risk_score / len(transactions_df)
        
        # Add high risk transactions
        risk_data["high_risk_transactions"] = sorted(high_risk_txs, key=lambda x: x.get("risk_score", 0), reverse=True)
        
        # Convert risk factors from defaultdict to regular dict
        risk_data["risk_factors"] = dict(risk_data["risk_factors"])
        
        return risk_data
    
    def get_transaction_stats(self, transactions_df):
        """
        Get statistical summaries for transactions
        
        Args:
            transactions_df (pd.DataFrame): DataFrame of transactions
            
        Returns:
            dict: Transaction statistics
        """
        self.logger.info("Calculating transaction statistics")
        
        stats = {}
        
        if transactions_df.empty:
            return stats
        
        # Basic counts
        stats["total_transactions"] = len(transactions_df)
        
        # Time range
        if "block_time" in transactions_df.columns:
            stats["first_transaction_time"] = transactions_df["block_time"].min()
            stats["last_transaction_time"] = transactions_df["block_time"].max()
            
            # Calculate transactions per day
            if stats["first_transaction_time"] and stats["last_transaction_time"]:
                time_range_days = (stats["last_transaction_time"] - stats["first_transaction_time"]) / (60 * 60 * 24)
                if time_range_days > 0:
                    stats["transactions_per_day"] = stats["total_transactions"] / time_range_days
        
        # Amount statistics
        if "amount_usd" in transactions_df.columns:
            amounts = transactions_df["amount_usd"].dropna()
            if not amounts.empty:
                stats["total_volume_usd"] = amounts.sum()
                stats["average_amount_usd"] = amounts.mean()
                stats["min_amount_usd"] = amounts.min()
                stats["max_amount_usd"] = amounts.max()
                stats["median_amount_usd"] = amounts.median()
        
        # Token statistics
        if "mint" in transactions_df.columns:
            token_counts = transactions_df["mint"].value_counts()
            stats["token_counts"] = token_counts.to_dict()
            stats["unique_tokens"] = len(token_counts)
            
            # Get token names
            stats["tokens"] = {}
            for token, count in token_counts.items():
                if token:
                    token_info = self.get_token_info(token)
                    stats["tokens"][token] = {
                        "symbol": token_info.get("symbol"),
                        "name": token_info.get("name"),
                        "count": count
                    }
        
        # Program statistics
        if "program" in transactions_df.columns:
            program_counts = transactions_df["program"].apply(
                lambda x: x.get("id") if isinstance(x, dict) and "id" in x else None
            ).value_counts(dropna=True)
            
            stats["program_counts"] = {}
            for program_id, count in program_counts.items():
                if program_id:
                    program_name = self.get_program_name(program_id)
                    stats["program_counts"][program_id] = {
                        "name": program_name,
                        "count": count
                    }
            
            stats["unique_programs"] = len(program_counts)
        
        # Counterparty statistics
        if "sender" in transactions_df.columns and "receiver" in transactions_df.columns:
            # Extract addresses
            transactions_df["sender_address"] = transactions_df["sender"].apply(
                lambda x: x.get("wallet") if isinstance(x, dict) else x
            )
            
            transactions_df["receiver_address"] = transactions_df["receiver"].apply(
                lambda x: x.get("wallet") if isinstance(x, dict) else x
            )
            
            # Count unique counterparties
            stats["unique_senders"] = transactions_df["sender_address"].nunique()
            stats["unique_receivers"] = transactions_df["receiver_address"].nunique()
            
            # Most common counterparties
            stats["top_senders"] = transactions_df["sender_address"].value_counts().head(10).to_dict()
            stats["top_receivers"] = transactions_df["receiver_address"].value_counts().head(10).to_dict()
        
        return stats
    
    def analyze_transactions(self, address=None, signatures=None, days=30):
        """Analyzes transactions for suspicious patterns."""
        self.logger.info(f"Analyzing transactions for {'address ' + address if address else 'signatures'}")
        
        # Fetch transactions
        transactions_df = self.fetch_transactions(address, signatures, days=days)
        
        if transactions_df.empty:
            return {
                "error": "No transactions found for analysis",
                "address": address,
                "signatures": signatures,
                "days": days
            }
        
        # Build transaction graph
        graph = self.build_transaction_graph(transactions_df)
        
        # Identify transaction patterns
        patterns = self.identify_transaction_patterns(transactions_df)
        
        # Detect cross-chain transfers
        cross_chain_transfers = self.detect_cross_chain_transfers(transactions_df)
        
        # Calculate risk scores
        risk_data = self.calculate_transaction_risk(transactions_df)
        
        # Calculate statistics
        stats = self.get_transaction_stats(transactions_df)
        
        # Compile analysis results
        results = {
            "address": address,
            "signatures": signatures,
            "analysis_timeframe": f"{days} days" if days else None,
            "transaction_count": len(transactions_df),
            "patterns": patterns,
            "cross_chain_transfers": cross_chain_transfers,
            "risk_assessment": risk_data,
            "statistics": stats,
            "graph_data": {
                "nodes": len(graph.nodes()),
                "edges": len(graph.edges())
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate an overall suspicion score based on patterns and risk assessment
        suspicion_score = 0.0
        suspicion_factors = []
        
        # Factor 1: Overall risk score
        if risk_data["overall_risk_score"] > 0:
            risk_contribution = risk_data["overall_risk_score"] / 100 * 0.4  # 40% weight to risk score
            suspicion_score += risk_contribution
            suspicion_factors.append({
                "factor": "transaction_risk",
                "score": risk_data["overall_risk_score"],
                "weight": 0.4,
                "description": f"Overall transaction risk score: {risk_data['overall_risk_score']:.1f}/100"
            })
        
        # Factor 2: Cross-chain transfers
        if cross_chain_transfers:
            cross_chain_factor = min(1.0, len(cross_chain_transfers) / 10) * 0.2  # 20% weight, max at 10 transfers
            suspicion_score += cross_chain_factor
            suspicion_factors.append({
                "factor": "cross_chain_activity",
                "count": len(cross_chain_transfers),
                "weight": 0.2,
                "description": f"Found {len(cross_chain_transfers)} cross-chain transfers"
            })
        
        # Factor 3: Circular flows
        if "circular_flows" in patterns:
            circular_factor = min(1.0, patterns["circular_flows"]["count"] / 5) * 0.2  # 20% weight, max at 5 cycles
            suspicion_score += circular_factor
            suspicion_factors.append({
                "factor": "circular_flows",
                "count": patterns["circular_flows"]["count"],
                "weight": 0.2,
                "description": f"Found {patterns['circular_flows']['count']} circular transaction flows"
            })
        
        # Factor 4: High frequency trading
        if "high_frequency_trading" in patterns:
            hft_factor = min(1.0, patterns["high_frequency_trading"]["count"] / 5) * 0.1  # 10% weight
            suspicion_score += hft_factor
            suspicion_factors.append({
                "factor": "high_frequency_trading",
                "count": patterns["high_frequency_trading"]["count"],
                "weight": 0.1,
                "description": f"Found {patterns['high_frequency_trading']['count']} high-frequency traders"
            })
        
        # Factor 5: Bridge usage
        if "bridges" in patterns:
            bridge_factor = min(1.0, patterns["bridges"]["percentage"] / 50) * 0.1  # 10% weight
            suspicion_score += bridge_factor
            suspicion_factors.append({
                "factor": "bridge_usage",
                "percentage": patterns["bridges"]["percentage"],
                "weight": 0.1,
                "description": f"{patterns['bridges']['percentage']:.1f}% of transactions use bridge programs"
            })
        
        # Add suspicion score to results
        results["suspicion_score"] = suspicion_score * 100  # Convert to 0-100 scale
        results["suspicion_factors"] = suspicion_factors
        
        return results

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = TransactionAnalyzer()
    
    # Example: Analyze transactions for an address
    if len(sys.argv) > 1:
        address = sys.argv[1]
        print(f"Analyzing transactions for address: {address}")
        results = analyzer.analyze_transactions(address=address, days=30)
        print(json.dumps(results, indent=2))
    else:
        # Example transaction analysis
        print("No address provided. Please provide an address to analyze.")