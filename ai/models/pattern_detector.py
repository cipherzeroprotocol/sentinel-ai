"""
Transaction pattern detector for identifying suspicious patterns
"""
import logging
import numpy as np
import pandas as pd
import networkx as nx
from datetime import datetime, timedelta
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)

class PatternDetector:
    """
    Transaction pattern detector for identifying suspicious patterns in blockchain data
    """

    # Define pattern types
    PATTERN_TYPES = {
        "layering": "Multiple transfers through intermediate addresses to obfuscate source/destination",
        "smurfing": "Breaking large amounts into smaller transactions to avoid detection",
        "round_trip": "Funds that return to the original address after passing through other addresses",
        "washing": "Trading with oneself to create artificial volume or price action",
        "dusting": "Sending tiny amounts to many addresses for tracking or phishing purposes",
        "address_poisoning": "Creating similar addresses to trick users into sending funds to wrong address",
        "pump_dump": "Artificially inflating token price before selling large amounts",
        "rug_pull": "Token creator withdrawing all liquidity from market",
        "mixer_use": "Using mixing services to obfuscate transaction trail",
        "high_velocity": "Unusually high transaction velocity for an address"
    }

    def __init__(self):
        pass

    def detect_patterns(self, transactions, address=None):
        """
        Detect patterns in transaction data

        Args:
            transactions (list): List of transactions
            address (str, optional): Address to analyze

        Returns:
            dict: Detected patterns with confidence scores
        """
        if not transactions:
            logger.warning("No transactions provided")
            return {}

        # Convert to dataframe for easier analysis
        df = self._prepare_transaction_dataframe(transactions)

        # Detect patterns
        patterns = {}

        # Detect layering patterns
        layering_score, layering_evidence = self._detect_layering(df, address)
        if layering_score > 0.5:
            patterns["layering"] = {
                "score": layering_score,
                "description": self.PATTERN_TYPES["layering"],
                "evidence": layering_evidence
            }

        # Detect smurfing patterns
        smurfing_score, smurfing_evidence = self._detect_smurfing(df, address)
        if smurfing_score > 0.5:
            patterns["smurfing"] = {
                "score": smurfing_score,
                "description": self.PATTERN_TYPES["smurfing"],
                "evidence": smurfing_evidence
            }

        # Detect round-trip patterns
        round_trip_score, round_trip_evidence = self._detect_round_trip(df, address)
        if round_trip_score > 0.5:
            patterns["round_trip"] = {
                "score": round_trip_score,
                "description": self.PATTERN_TYPES["round_trip"],
                "evidence": round_trip_evidence
            }

        # Detect washing patterns
        washing_score, washing_evidence = self._detect_washing(df, address)
        if washing_score > 0.5:
            patterns["washing"] = {
                "score": washing_score,
                "description": self.PATTERN_TYPES["washing"],
                "evidence": washing_evidence
            }

        # Detect dusting patterns
        dusting_score, dusting_evidence = self._detect_dusting(df, address)
        if dusting_score > 0.5:
            patterns["dusting"] = {
                "score": dusting_score,
                "description": self.PATTERN_TYPES["dusting"],
                "evidence": dusting_evidence
            }

        # Detect address poisoning patterns
        poisoning_score, poisoning_evidence = self._detect_address_poisoning(df, address)
        if poisoning_score > 0.5:
            patterns["address_poisoning"] = {
                "score": poisoning_score,
                "description": self.PATTERN_TYPES["address_poisoning"],
                "evidence": poisoning_evidence
            }

        # Detect mixer usage patterns
        mixer_score, mixer_evidence = self._detect_mixer_use(df, address)
        if mixer_score > 0.5:
            patterns["mixer_use"] = {
                "score": mixer_score,
                "description": self.PATTERN_TYPES["mixer_use"],
                "evidence": mixer_evidence
            }

        # Detect high velocity patterns
        velocity_score, velocity_evidence = self._detect_high_velocity(df, address)
        if velocity_score > 0.5:
            patterns["high_velocity"] = {
                "score": velocity_score,
                "description": self.PATTERN_TYPES["high_velocity"],
                "evidence": velocity_evidence
            }

        # For tokens, detect pump and dump or rug pull patterns
        if 'token_mint' in df.columns:
            # Group by token mint
            token_groups = df.groupby('token_mint')

            for token_mint, token_df in token_groups:
                # Detect pump and dump patterns
                pump_dump_score, pump_dump_evidence = self._detect_pump_dump(token_df)
                if pump_dump_score > 0.5:
                    patterns[f"pump_dump_{token_mint[:8]}"] = {
                        "score": pump_dump_score,
                        "description": self.PATTERN_TYPES["pump_dump"],
                        "token_mint": token_mint,
                        "evidence": pump_dump_evidence
                    }

                # Detect rug pull patterns
                rug_pull_score, rug_pull_evidence = self._detect_rug_pull(token_df)
                if rug_pull_score > 0.5:
                    patterns[f"rug_pull_{token_mint[:8]}"] = {
                        "score": rug_pull_score,
                        "description": self.PATTERN_TYPES["rug_pull"],
                        "token_mint": token_mint,
                        "evidence": rug_pull_evidence
                    }

        return patterns

    def _prepare_transaction_dataframe(self, transactions):
        """
        Prepare transaction data for analysis

        Args:
            transactions (list): List of transactions

        Returns:
            pandas.DataFrame: Prepared dataframe
        """
        # Convert to dataframe
        df = pd.DataFrame(transactions)

        # Extract datetime
        if 'block_time' in df.columns:
            df['datetime'] = pd.to_datetime(df['block_time'])
        elif 'blockTime' in df.columns:
            df['datetime'] = pd.to_datetime(df['blockTime'], unit='s')
        else:
            df['datetime'] = pd.to_datetime('now')

        # Sort by time
        df = df.sort_values('datetime')

        # Extract sender and receiver addresses
        if 'sender' not in df.columns and 'receiver' not in df.columns:
            # Try to extract from nested dictionaries
            try:
                df['sender_address'] = df.apply(lambda x: x.get('sender', {}).get('wallet')
                                             if isinstance(x.get('sender'), dict) else None, axis=1)
                df['receiver_address'] = df.apply(lambda x: x.get('receiver', {}).get('wallet')
                                               if isinstance(x.get('receiver'), dict) else None, axis=1)
            except:
                # If that fails, create empty columns
                df['sender_address'] = None
                df['receiver_address'] = None
        else:
            df['sender_address'] = df['sender']
            df['receiver_address'] = df['receiver']

        # Extract amounts
        if 'amount' not in df.columns and 'amount_usd' not in df.columns:
            # Try to extract from nested dictionaries
            try:
                df['amount'] = df.apply(lambda x: x.get('amount', 0), axis=1)
                df['amount_usd'] = df.apply(lambda x: x.get('amount_usd', 0), axis=1)
            except:
                # If that fails, create empty columns
                df['amount'] = 0
                df['amount_usd'] = 0

        return df

    def _detect_layering(self, df, address=None):
        """
        Detect layering patterns

        Args:
            df (pandas.DataFrame): Transaction dataframe
            address (str, optional): Address to analyze

        Returns:
            tuple: (confidence score, evidence)
        """
        # Check if we have enough data
        if len(df) < 3:
            return 0.0, {}

        try:
            # Create directed graph
            G = nx.DiGraph()

            # Add edges for each transaction
            for _, row in df.iterrows():
                if pd.notna(row['sender_address']) and pd.notna(row['receiver_address']):
                    G.add_edge(row['sender_address'], row['receiver_address'])

            # If address is provided, focus on paths from/to this address
            evidence = {}
            layering_score = 0.0

            if address:
                # Look for paths from address
                paths = []
                for node in G.nodes():
                    if node != address and node in G:
                        try:
                            # Find paths from address to node
                            for path in nx.all_simple_paths(G, address, node, cutoff=5):
                                if len(path) >= 3:  # At least one intermediate node
                                    paths.append(path)
                        except:
                            pass

                # Calculate layering score based on paths
                if paths:
                    # Longer paths and more intermediate nodes indicate higher likelihood of layering
                    avg_path_length = sum(len(path) for path in paths) / len(paths)
                    num_paths = len(paths)

                    # Normalize scores
                    path_length_score = min(1.0, (avg_path_length - 2) / 3)  # 2 is minimum for a transfer
                    path_count_score = min(1.0, num_paths / 5)  # 5 or more paths gets full score

                    # Combine scores
                    layering_score = (path_length_score * 0.7) + (path_count_score * 0.3)

                    # Prepare evidence
                    evidence = {
                        "paths": [
                            {
                                "path": "->".join(path),
                                "length": len(path)
                            }
                            for path in paths[:5]  # Limit to top 5 paths
                        ],
                        "avg_path_length": avg_path_length,
                        "path_count": num_paths
                    }
            else:
                # No specific address, look for general layering patterns
                # Find all paths with length >= 3
                all_paths = []
                for source in G.nodes():
                    for target in G.nodes():
                        if source != target and source in G and target in G:
                            try:
                                for path in nx.all_simple_paths(G, source, target, cutoff=5):
                                    if len(path) >= 3:  # At least one intermediate node
                                        all_paths.append(path)
                            except:
                                pass

                if all_paths:
                    # Calculate layering score
                    avg_path_length = sum(len(path) for path in all_paths) / len(all_paths)

                    # Normalize score
                    layering_score = min(1.0, (avg_path_length - 2) / 3)

                    # Prepare evidence
                    evidence = {
                        "paths": [
                            {
                                "path": "->".join(path),
                                "length": len(path)
                            }
                            for path in all_paths[:5]  # Limit to top 5 paths
                        ],
                        "avg_path_length": avg_path_length,
                        "path_count": len(all_paths)
                    }

            return layering_score, evidence

        except Exception as e:
            logger.error(f"Error detecting layering: {str(e)}")
            return 0.0, {}

    def _detect_smurfing(self, df, address=None):
        """
        Detect smurfing patterns (breaking large amounts into smaller transactions)

        Args:
            df (pandas.DataFrame): Transaction dataframe
            address (str, optional): Address to analyze

        Returns:
            tuple: (confidence score, evidence)
        """
        # Check if we have enough data
        if len(df) < 5:
            return 0.0, {}

        try:
            # Filter transactions if address is provided
            if address:
                # Look for outgoing transactions
                out_df = df[(df['sender_address'] == address)]

                if len(out_df) < 5:
                    return 0.0, {}

                # Group by receiver and time window
                out_df['time_window'] = out_df['datetime'].dt.floor('1H')
                grouped = out_df.groupby(['receiver_address', 'time_window'])

                # Look for multiple small transactions to the same address in a short time
                smurfing_groups = []

                for (receiver, time_window), group in grouped:
                    if len(group) >= 3:  # At least 3 transactions in the same hour
                        # Check if transaction amounts are similar
                        amounts = group['amount'].values
                        avg_amount = np.mean(amounts)
                        amount_std = np.std(amounts)

                        # Low standard deviation indicates similar amounts
                        if amount_std / avg_amount < 0.3:
                            smurfing_groups.append({
                                "receiver": receiver,
                                "time_window": time_window.strftime("%Y-%m-%d %H:%M"),
                                "transaction_count": len(group),
                                "total_amount": float(group['amount'].sum()),
                                "avg_amount": float(avg_amount),
                                "transaction_signatures": group['signature'].tolist()[:5]  # Limit to 5
                            })

                # Calculate smurfing score based on groups
                if smurfing_groups:
                    # More groups and more transactions per group indicate higher likelihood of smurfing
                    num_groups = len(smurfing_groups)
                    avg_tx_count = sum(g['transaction_count'] for g in smurfing_groups) / num_groups

                    # Normalize scores
                    group_score = min(1.0, num_groups / 3)  # 3 or more groups gets full score
                    tx_count_score = min(1.0, (avg_tx_count - 3) / 5)  # 8 or more transactions gets full score

                    # Combine scores
                    smurfing_score = (group_score * 0.5) + (tx_count_score * 0.5)

                    # Prepare evidence
                    evidence = {
                        "smurfing_groups": smurfing_groups,
                        "group_count": num_groups,
                        "avg_transaction_count": avg_tx_count
                    }

                    return smurfing_score, evidence
            else:
                # No specific address, look for general smurfing patterns
                # Group by sender, receiver, and time window
                df['time_window'] = df['datetime'].dt.floor('1H')
                grouped = df.groupby(['sender_address', 'receiver_address', 'time_window'])

                # Look for multiple small transactions between the same addresses in a short time
                smurfing_groups = []

                for (sender, receiver, time_window), group in grouped:
                    if len(group) >= 3:  # At least 3 transactions in the same hour
                        # Check if transaction amounts are similar
                        amounts = group['amount'].values
                        avg_amount = np.mean(amounts)
                        amount_std = np.std(amounts)

                        # Low standard deviation indicates similar amounts
                        if amount_std / avg_amount < 0.3:
                            smurfing_groups.append({
                                "sender": sender,
                                "receiver": receiver,
                                "time_window": time_window.strftime("%Y-%m-%d %H:%M"),
                                "transaction_count": len(group),
                                "total_amount": float(group['amount'].sum()),
                                "avg_amount": float(avg_amount),
                                "transaction_signatures": group['signature'].tolist()[:5]  # Limit to 5
                            })

                # Calculate smurfing score based on groups
                if smurfing_groups:
                    # More groups and more transactions per group indicate higher likelihood of smurfing
                    num_groups = len(smurfing_groups)
                    avg_tx_count = sum(g['transaction_count'] for g in smurfing_groups) / num_groups

                    # Normalize scores
                    group_score = min(1.0, num_groups / 3)  # 3 or more groups gets full score
                    tx_count_score = min(1.0, (avg_tx_count - 3) / 5)  # 8 or more transactions gets full score

                    # Combine scores
                    smurfing_score = (group_score * 0.5) + (tx_count_score * 0.5)

                    # Prepare evidence
                    evidence = {
                        "smurfing_groups": smurfing_groups,
                        "group_count": num_groups,
                        "avg_transaction_count": avg_tx_count
                    }

                    return smurfing_score, evidence

            return 0.0, {}

        except Exception as e:
            logger.error(f"Error detecting smurfing: {str(e)}")
            return 0.0, {}

    def _detect_round_trip(self, df, address=None):
        """
        Detect round-trip patterns (funds that return to the original address)

        Args:
            df (pandas.DataFrame): Transaction dataframe
            address (str, optional): Address to analyze

        Returns:
            tuple: (confidence score, evidence)
        """
        # Check if we have enough data
        if len(df) < 3:
            return 0.0, {}

        try:
            # Create directed graph
            G = nx.DiGraph()

            # Add edges for each transaction
            for _, row in df.iterrows():
                if pd.notna(row['sender_address']) and pd.notna(row['receiver_address']):
                    G.add_edge(row['sender_address'], row['receiver_address'])

            # If address is provided, focus on cycles involving this address
            evidence = {}
            round_trip_score = 0.0

            if address:
                # Look for cycles containing the address
                cycles = []

                try:
                    for cycle in nx.simple_cycles(G):
                        if address in cycle and len(cycle) >= 2:
                            cycles.append(cycle)
                except:
                    # Simple cycles can be expensive for large graphs
                    # Try a simpler approach
                    # Look for paths from address back to itself
                    for node in G.neighbors(address):
                        try:
                            for path in nx.all_simple_paths(G, node, address, cutoff=4):
                                if len(path) >= 2:
                                    cycles.append([address] + path)
                        except:
                            pass

                # Calculate round-trip score based on cycles
                if cycles:
                    # More cycles and shorter cycles indicate higher likelihood of round-tripping
                    num_cycles = len(cycles)
                    avg_cycle_length = sum(len(cycle) for cycle in cycles) / num_cycles

                    # Normalize scores
                    cycle_count_score = min(1.0, num_cycles / 3)  # 3 or more cycles gets full score
                    cycle_length_score = min(1.0, 5 / avg_cycle_length)  # Shorter cycles get higher scores

                    # Combine scores
                    round_trip_score = (cycle_count_score * 0.6) + (cycle_length_score * 0.4)

                    # Prepare evidence
                    evidence = {
                        "cycles": [
                            {
                                "path": "->".join(cycle + [cycle[0]]),
                                "length": len(cycle)
                            }
                            for cycle in cycles[:5]  # Limit to top 5 cycles
                        ],
                        "cycle_count": num_cycles,
                        "avg_cycle_length": avg_cycle_length
                    }
            else:
                # No specific address, look for general round-trip patterns
                # Find all cycles
                cycles = []

                try:
                    for cycle in nx.simple_cycles(G):
                        if len(cycle) >= 2:
                            cycles.append(cycle)
                except:
                    # If simple_cycles fails, try a different approach
                    # Look for paths from nodes back to themselves
                    for node in G.nodes():
                        for neighbor in G.neighbors(node):
                            try:
                                for path in nx.all_simple_paths(G, neighbor, node, cutoff=4):
                                    if len(path) >= 2:
                                        cycles.append([node] + path)
                            except:
                                pass

                # Calculate round-trip score based on cycles
                if cycles:
                    # More cycles and shorter cycles indicate higher likelihood of round-tripping
                    num_cycles = len(cycles)
                    avg_cycle_length = sum(len(cycle) for cycle in cycles) / num_cycles

                    # Normalize scores
                    cycle_count_score = min(1.0, num_cycles / 5)  # 5 or more cycles gets full score
                    cycle_length_score = min(1.0, 5 / avg_cycle_length)  # Shorter cycles get higher scores

                    # Combine scores
                    round_trip_score = (cycle_count_score * 0.6) + (cycle_length_score * 0.4)

                    # Prepare evidence
                    evidence = {
                        "cycles": [
                            {
                                "path": "->".join(cycle + [cycle[0]]),
                                "length": len(cycle)
                            }
                            for cycle in cycles[:5]  # Limit to top 5 cycles
                        ],
                        "cycle_count": num_cycles,
                        "avg_cycle_length": avg_cycle_length
                    }

            return round_trip_score, evidence

        except Exception as e:
            logger.error(f"Error detecting round-trip: {str(e)}")
            return 0.0, {}

    def _detect_washing(self, df, address=None):
        """
        Detect washing patterns (trading with oneself)

        Args:
            df (pandas.DataFrame): Transaction dataframe
            address (str, optional): Address to analyze

        Returns:
            tuple: (confidence score, evidence)
        """
        # Check if we have enough data
        if len(df) < 3:
            return 0.0, {}

        try:
            # Filter for transactions with 'swap' or 'trade' instructions
            trade_df = df[df['instruction_name'].str.contains('swap|trade', case=False, na=False)]

            if len(trade_df) < 3:
                return 0.0, {}

            # If address is provided, focus on trades involving this address
            if address:
                # Look for trades where the address is both sender and receiver
                washing_trades = []

                for _, row in trade_df.iterrows():
                    # Check direct self-trading
                    if row['sender_address'] == address and row['receiver_address'] == address:
                        washing_trades.append({
                            "signature": row['signature'],
                            "time": row['datetime'].strftime("%Y-%m-%d %H:%M:%S"),
                            "program_id": row.get('program_id', 'Unknown')
                        })

                    # Try to find indirect self-trading through intermediary addresses
                    # This requires additional analysis beyond the current transaction data

                # Calculate washing score based on trades
                if washing_trades:
                    # More self-trades indicate higher likelihood of washing
                    num_trades = len(washing_trades)

                    # Normalize score
                    washing_score = min(1.0, num_trades / 5)  # 5 or more trades gets full score

                    # Prepare evidence
                    evidence = {
                        "washing_trades": washing_trades,
                        "trade_count": num_trades
                    }

                    return washing_score, evidence
            else:
                # No specific address, look for general washing patterns
                # Group by sender and receiver
                grouped = trade_df.groupby(['sender_address', 'receiver_address'])

                # Look for addresses that trade with themselves
                washing_pairs = []

                for (sender, receiver), group in grouped:
                    if sender == receiver:
                        washing_pairs.append({
                            "address": sender,
                            "trade_count": len(group),
                            "first_trade": group['datetime'].min().strftime("%Y-%m-%d %H:%M:%S"),
                            "last_trade": group['datetime'].max().strftime("%Y-%m-%d %H:%M:%S"),
                            "example_signatures": group['signature'].tolist()[:3]  # Limit to 3
                        })

                # Calculate washing score based on pairs
                if washing_pairs:
                    # More pairs and more trades per pair indicate higher likelihood of washing
                    num_pairs = len(washing_pairs)
                    avg_trade_count = sum(p['trade_count'] for p in washing_pairs) / num_pairs

                    # Normalize scores
                    pair_score = min(1.0, num_pairs / 3)  # 3 or more pairs gets full score
                    trade_count_score = min(1.0, avg_trade_count / 5)  # 5 or more trades gets full score

                    # Combine scores
                    washing_score = (pair_score * 0.4) + (trade_count_score * 0.6)

                    # Prepare evidence
                    evidence = {
                        "washing_pairs": washing_pairs,
                        "pair_count": num_pairs,
                        "avg_trade_count": avg_trade_count
                    }

                    return washing_score, evidence

            return 0.0, {}

        except Exception as e:
            logger.error(f"Error detecting washing: {str(e)}")
            return 0.0, {}

    def _detect_dusting(self, df, address=None):
        """
        Detect dusting patterns (sending tiny amounts to many addresses)

        Args:
            df (pandas.DataFrame): Transaction dataframe
            address (str, optional): Address to analyze

        Returns:
            tuple: (confidence score, evidence)
        """
        # Check if we have enough data
        if len(df) < 5:
            return 0.0, {}

        try:
            # Identify tiny transactions
            # Use a threshold of 0.01 USD or equivalent
            if 'amount_usd' in df.columns and df['amount_usd'].notna().any():
                dust_df = df[df['amount_usd'] < 0.01]
            else:
                # If no USD values, assume dust is less than 0.000001 of the token
                dust_df = df[df['amount'] < 0.000001]

            # If address is provided, focus on dusting from/to this address
            if address:
                # Check if address is a duster (sending tiny amounts to many addresses)
                dust_out = dust_df[dust_df['sender_address'] == address]

                if len(dust_out) >= 5:
                    # Count unique recipients
                    unique_recipients = dust_out['receiver_address'].nunique()

                    if unique_recipients >= 5:
                        # More unique recipients indicates higher likelihood of dusting
                        dusting_score = min(1.0, unique_recipients / 20)  # 20 or more recipients gets full score

                        # Prepare evidence
                        evidence = {
                            "dusting_type": "sender",
                            "dust_count": len(dust_out),
                            "unique_recipients": unique_recipients,
                            "examples": dust_out.head(5)[['signature', 'datetime', 'receiver_address']].to_dict('records')
                        }

                        return dusting_score, evidence

                # Check if address is a dustee (receiving tiny amounts from many addresses)
                dust_in = dust_df[dust_df['receiver_address'] == address]

                if len(dust_in) >= 5:
                    # Count unique senders
                    unique_senders = dust_in['sender_address'].nunique()

                    if unique_senders >= 3:
                        # More unique senders indicates higher likelihood of being dusted
                        dusting_score = min(1.0, unique_senders / 10)  # 10 or more senders gets full score

                        # Prepare evidence
                        evidence = {
                            "dusting_type": "receiver",
                            "dust_count": len(dust_in),
                            "unique_senders": unique_senders,
                            "examples": dust_in.head(5)[['signature', 'datetime', 'sender_address']].to_dict('records')
                        }

                        return dusting_score, evidence
            else:
                # No specific address, look for general dusting patterns
                # Group by sender
                grouped = dust_df.groupby('sender_address')

                # Look for senders with many dust transactions to unique recipients
                dusters = []

                for sender, group in grouped:
                    if len(group) >= 5:
                        # Count unique recipients
                        unique_recipients = group['receiver_address'].nunique()

                        if unique_recipients >= 5:
                            dusters.append({
                                "address": sender,
                                "dust_count": len(group),
                                "unique_recipients": unique_recipients,
                                "example_signatures": group['signature'].tolist()[:3]  # Limit to 3
                            })

                # Calculate dusting score based on dusters
                if dusters:
                    # More dusters indicates higher likelihood of dusting activity
                    num_dusters = len(dusters)
                    avg_recipient_count = sum(d['unique_recipients'] for d in dusters) / num_dusters

                    # Normalize scores
                    duster_score = min(1.0, num_dusters / 3)  # 3 or more dusters gets full score
                    recipient_score = min(1.0, avg_recipient_count / 20)  # 20 or more recipients gets full score

                    # Combine scores
                    dusting_score = (duster_score * 0.4) + (recipient_score * 0.6)

                    # Prepare evidence
                    evidence = {
                        "dusters": dusters,
                        "duster_count": num_dusters,
                        "avg_recipient_count": avg_recipient_count
                    }

                    return dusting_score, evidence

            return 0.0, {}

        except Exception as e:
            logger.error(f"Error detecting dusting: {str(e)}")
            return 0.0, {}

    def _detect_address_poisoning(self, df, address=None):
        """
        Detect address poisoning patterns (creating similar addresses)

        Args:
            df (pandas.DataFrame): Transaction dataframe
            address (str, optional): Address to analyze

        Returns:
            tuple: (confidence score, evidence)
        """
        # Check if we have enough data
        if len(df) < 3:
            return 0.0, {}

        try:
            # Collect all unique addresses
            all_addresses = set()

            if 'sender_address' in df.columns:
                all_addresses.update(df['sender_address'].dropna().tolist())

            if 'receiver_address' in df.columns:
                all_addresses.update(df['receiver_address'].dropna().tolist())

            # Remove None and empty strings
            all_addresses = {a for a in all_addresses if a}

            # If address is provided, focus on addresses similar to this one
            if address:
                similar_addresses = []

                for addr in all_addresses:
                    if addr != address:
                        # Check for common prefix (first N characters)
                        prefix_length = max(len(address), len(addr)) // 4  # Use 25% of address length
                        if address[:prefix_length] == addr[:prefix_length]:
                            similarity = self._address_similarity(address, addr)
                            if similarity > 0.7:  # High similarity threshold
                                similar_addresses.append({
                                    "address": addr,
                                    "similarity": similarity,
                                    "common_prefix": address[:prefix_length]
                                })

                # Calculate poisoning score based on similar addresses
                if similar_addresses:
                    # More similar addresses and higher similarity indicate higher likelihood of poisoning
                    num_similar = len(similar_addresses)
                    avg_similarity = sum(a['similarity'] for a in similar_addresses) / num_similar

                    # Normalize scores
                    address_score = min(1.0, num_similar / 3)  # 3 or more similar addresses gets full score
                    similarity_score = min(1.0, (avg_similarity - 0.7) / 0.3)  # Scales from 0.7 to 1.0

                    # Combine scores
                    poisoning_score = (address_score * 0.7) + (similarity_score * 0.3)

                    # Prepare evidence
                    evidence = {
                        "similar_addresses": similar_addresses,
                        "similar_address_count": num_similar,
                        "avg_similarity": avg_similarity
                    }

                    return poisoning_score, evidence
            else:
                # No specific address, look for clusters of similar addresses
                address_clusters = []
                processed = set()

                # Find clusters of similar addresses
                for addr1 in all_addresses:
                    if addr1 in processed:
                        continue

                    cluster = []

                    for addr2 in all_addresses:
                        if addr1 != addr2 and addr2 not in processed:
                            # Check for common prefix (first N characters)
                            prefix_length = max(len(addr1), len(addr2)) // 4  # Use 25% of address length
                            if addr1[:prefix_length] == addr2[:prefix_length]:
                                similarity = self._address_similarity(addr1, addr2)
                                if similarity > 0.7:  # High similarity threshold
                                    cluster.append({
                                        "address": addr2,
                                        "similarity": similarity,
                                        "common_prefix": addr1[:prefix_length]
                                    })

                    if cluster:
                        address_clusters.append({
                            "base_address": addr1,
                            "similar_addresses": cluster,
                            "cluster_size": len(cluster) + 1  # Include the base address
                        })

                        # Mark all addresses in this cluster as processed
                        processed.add(addr1)
                        processed.update(a['address'] for a in cluster)

                # Calculate poisoning score based on clusters
                if address_clusters:
                    # More clusters and larger clusters indicate higher likelihood of poisoning
                    num_clusters = len(address_clusters)
                    avg_cluster_size = sum(c['cluster_size'] for c in address_clusters) / num_clusters

                    # Normalize scores
                    cluster_score = min(1.0, num_clusters / 3)  # 3 or more clusters gets full score
                    size_score = min(1.0, (avg_cluster_size - 2) / 3)  # Scales from 2 to 5

                    # Combine scores
                    poisoning_score = (cluster_score * 0.6) + (size_score * 0.4)

                    # Prepare evidence
                    evidence = {
                        "address_clusters": address_clusters,
                        "cluster_count": num_clusters,
                        "avg_cluster_size": avg_cluster_size
                    }

                    return poisoning_score, evidence

            return 0.0, {}

        except Exception as e:
            logger.error(f"Error detecting address poisoning: {str(e)}")
            return 0.0, {}

    def _address_similarity(self, addr1, addr2):
        """
        Calculate similarity between two addresses

        Args:
            addr1 (str): First address
            addr2 (str): Second address

        Returns:
            float: Similarity score (0.0 to 1.0)
        """
        if not addr1 or not addr2:
            return 0.0

        # Common prefix matching (e.g. first 4-8 chars)
        max_prefix = 0
        for i in range(min(len(addr1), len(addr2))):
            if addr1[i] == addr2[i]:
                max_prefix = i + 1
            else:
                break

        # Common suffix matching
        max_suffix = 0
        for i in range(min(len(addr1), len(addr2))):
            if addr1[-(i+1)] == addr2[-(i+1)]:
                max_suffix = i + 1
            else:
                break

        # Calculate similarity score (weighted more towards prefix similarity)
        prefix_weight = 0.8
        suffix_weight = 0.2

        # Normalize prefix length (first 8 chars are most important)
        prefix_similarity = max_prefix / min(8, min(len(addr1), len(addr2)))

        # Normalize suffix length (last 4 chars are most important)
        suffix_similarity = max_suffix / min(4, min(len(addr1), len(addr2)))

        return prefix_weight * prefix_similarity + suffix_weight * suffix_similarity

    def _detect_mixer_use(self, df, address=None):
        """
        Detect mixer usage patterns

        Args:
            df (pandas.DataFrame): Transaction dataframe
            address (str, optional): Address to analyze

        Returns:
            tuple: (confidence score, evidence)
        """
        # Known mixer program IDs and addresses (from the knowledge base)
        KNOWN_MIXERS = {
            "tor1xzb2Zyy1cUxXmyJfR8aNXuWnwHG8AwgaG7UGD4K": {
                "name": "Tornado Cash Solana",
                "risk_level": "very_high"
            },
            "1MixerZCaShtMCAdLozKTzVdLFf9WZqDehHHQdT1V5Pf": {
                "name": "SolMixer",
                "risk_level": "high"
            },
            "mixBkFZP3Z1hGWaXeYPxvyzh2Wuq2nIUQBNCZHLbwiU": {
                "name": "Cyclos Privacy Pool",
                "risk_level": "high"
            }
        }

        try:
            # Check for interactions with known mixers
            mixer_interactions = []

            for _, row in df.iterrows():
                # Check if sender or receiver is a mixer
                sender = row.get('sender_address')
                receiver = row.get('receiver_address')
                program_id = row.get('program_id')

                if sender in KNOWN_MIXERS:
                    mixer_interactions.append({
                        "mixer": KNOWN_MIXERS[sender]["name"],
                        "interaction_type": "withdrawal",
                        "risk_level": KNOWN_MIXERS[sender]["risk_level"],
                        "address": receiver,
                        "signature": row.get('signature'),
                        "time": row.get('datetime').strftime("%Y-%m-%d %H:%M:%S") if hasattr(row.get('datetime'), 'strftime') else str(row.get('datetime')),
                        "amount_usd": row.get('amount_usd', 0)
                    })

                if receiver in KNOWN_MIXERS:
                    mixer_interactions.append({
                        "mixer": KNOWN_MIXERS[receiver]["name"],
                        "interaction_type": "deposit",
                        "risk_level": KNOWN_MIXERS[receiver]["risk_level"],
                        "address": sender,
                        "signature": row.get('signature'),
                        "time": row.get('datetime').strftime("%Y-%m-%d %H:%M:%S") if hasattr(row.get('datetime'), 'strftime') else str(row.get('datetime')),
                        "amount_usd": row.get('amount_usd', 0)
                    })

                # Check if the program ID is a mixer
                if program_id in KNOWN_MIXERS:
                    mixer_interactions.append({
                        "mixer": KNOWN_MIXERS[program_id]["name"],
                        "interaction_type": "program_call",
                        "risk_level": KNOWN_MIXERS[program_id]["risk_level"],
                        "address": sender,
                        "signature": row.get('signature'),
                        "time": row.get('datetime').strftime("%Y-%m-%d %H:%M:%S") if hasattr(row.get('datetime'), 'strftime') else str(row.get('datetime')),
                        "amount_usd": row.get('amount_usd', 0)
                    })

            # If address is provided, filter interactions involving this address
            if address:
                mixer_interactions = [
                    interaction for interaction in mixer_interactions
                    if interaction.get('address') == address
                ]

            # Calculate mixer usage score based on interactions
            if mixer_interactions:
                # More interactions and deposits indicate higher likelihood of mixer usage
                num_interactions = len(mixer_interactions)
                num_deposits = sum(1 for interaction in mixer_interactions if interaction.get('interaction_type') == 'deposit')
                num_high_risk = sum(1 for interaction in mixer_interactions if interaction.get('risk_level') == 'very_high')

                # Normalize scores
                interaction_score = min(1.0, num_interactions / 5)  # 5 or more interactions gets full score
                deposit_score = min(1.0, num_deposits / 3)  # 3 or more deposits gets full score
                risk_score = min(1.0, num_high_risk / 2)  # 2 or more high risk interactions gets full score

                # Combine scores (deposits are more suspicious than withdrawals)
                mixer_score = (interaction_score * 0.3) + (deposit_score * 0.5) + (risk_score * 0.2)

                # Prepare evidence
                evidence = {
                    "mixer_interactions": mixer_interactions,
                    "interaction_count": num_interactions,
                    "deposit_count": num_deposits,
                    "high_risk_count": num_high_risk
                }

                return mixer_score, evidence

            return 0.0, {}

        except Exception as e:
            logger.error(f"Error detecting mixer usage: {str(e)}")
            return 0.0, {}

    def _detect_high_velocity(self, df, address=None):
        """
        Detect high transaction velocity patterns

        Args:
            df (pandas.DataFrame): Transaction dataframe
            address (str, optional): Address to analyze

        Returns:
            tuple: (confidence score, evidence)
        """
        # Check if we have enough data
        if len(df) < 5:
            return 0.0, {}

        try:
            # Filter transactions for the specified address if provided
            if address:
                address_df = df[(df['sender_address'] == address) | (df['receiver_address'] == address)]

                if len(address_df) < 5:
                    return 0.0, {}

                # Calculate transaction velocity
                address_df = address_df.sort_values('datetime')
                start_time = address_df['datetime'].min()
                end_time = address_df['datetime'].max()

                if start_time == end_time:
                    return 0.0, {}

                # Calculate time range in days
                time_range = (end_time - start_time).total_seconds() / 86400  # seconds to days

                # Calculate transactions per day
                tx_per_day = len(address_df) / time_range if time_range > 0 else 0

                # Check for bursts of activity
                address_df['time_diff'] = address_df['datetime'].diff().dt.total_seconds()
                bursts = address_df[address_df['time_diff'] < 60]  # Transactions less than a minute apart

                num_bursts = len(bursts)
                max_burst_size = 0

                if num_bursts > 0:
                    # Identify consecutive bursts
                    burst_groups = []
                    current_group = [bursts.iloc[0]]

                    for i in range(1, len(bursts)):
                        if bursts.iloc[i]['time_diff'] < 60:
                            current_group.append(bursts.iloc[i])
                        else:
                            if len(current_group) > 1:
                                burst_groups.append(current_group)
                            current_group = [bursts.iloc[i]]

                    if len(current_group) > 1:
                        burst_groups.append(current_group)

                    if burst_groups:
                        max_burst_size = max(len(group) for group in burst_groups)

                # Calculate velocity score
                # High transactions per day and large bursts indicate high velocity
                tx_per_day_score = min(1.0, tx_per_day / 50)  # 50 or more transactions per day gets full score
                burst_score = min(1.0, max_burst_size / 10)  # 10 or more transactions in a burst gets full score

                # Combine scores
                velocity_score = (tx_per_day_score * 0.7) + (burst_score * 0.3)

                # Prepare evidence
                evidence = {
                    "address": address,
                    "transaction_count": len(address_df),
                    "time_range_days": time_range,
                    "transactions_per_day": tx_per_day,
                    "burst_count": num_bursts,
                    "max_burst_size": max_burst_size
                }

                return velocity_score, evidence
            else:
                # No specific address, look for addresses with high velocity
                # Group by address
                sender_groups = df.groupby('sender_address')
                receiver_groups = df.groupby('receiver_address')

                # Calculate velocity for each address
                high_velocity_addresses = []

                for address, group in sender_groups:
                    if len(group) >= 5:
                        # Calculate time range
                        group = group.sort_values('datetime')
                        start_time = group['datetime'].min()
                        end_time = group['datetime'].max()

                        if start_time == end_time:
                            continue

                        # Calculate time range in days
                        time_range = (end_time - start_time).total_seconds() / 86400  # seconds to days

                        # Calculate transactions per day
                        tx_per_day = len(group) / time_range if time_range > 0 else 0

                        if tx_per_day >= 20:  # Threshold for high velocity
                            high_velocity_addresses.append({
                                "address": address,
                                "transaction_count": len(group),
                                "time_range_days": time_range,
                                "transactions_per_day": tx_per_day
                            })

                # Add receiver addresses not already in the list
                for address, group in receiver_groups:
                    if address not in [a['address'] for a in high_velocity_addresses] and len(group) >= 5:
                        # Calculate time range
                        group = group.sort_values('datetime')
                        start_time = group['datetime'].min()
                        end_time = group['datetime'].max()

                        if start_time == end_time:
                            continue

                        # Calculate time range in days
                        time_range = (end_time - start_time).total_seconds() / 86400  # seconds to days

                        # Calculate transactions per day
                        tx_per_day = len(group) / time_range if time_range > 0 else 0

                        if tx_per_day >= 20:  # Threshold for high velocity
                            high_velocity_addresses.append({
                                "address": address,
                                "transaction_count": len(group),
                                "time_range_days": time_range,
                                "transactions_per_day": tx_per_day
                            })

                # Calculate velocity score based on high velocity addresses
                if high_velocity_addresses:
                    # More high velocity addresses indicates higher overall velocity
                    num_addresses = len(high_velocity_addresses)
                    avg_tx_per_day = sum(a['transactions_per_day'] for a in high_velocity_addresses) / num_addresses

                    # Normalize scores
                    address_score = min(1.0, num_addresses / 5)  # 5 or more high velocity addresses gets full score
                    tx_per_day_score = min(1.0, avg_tx_per_day / 100)  # 100 or more transactions per day gets full score

                    # Combine scores
                    velocity_score = (address_score * 0.5) + (tx_per_day_score * 0.5)

                    # Prepare evidence
                    evidence = {
                        "high_velocity_addresses": high_velocity_addresses,
                        "address_count": num_addresses,
                        "avg_transactions_per_day": avg_tx_per_day
                    }

                    return velocity_score, evidence

            return 0.0, {}

        except Exception as e:
            logger.error(f"Error detecting high velocity: {str(e)}")
            return 0.0, {}

    def _detect_pump_dump(self, df):
        """
        Detect pump and dump patterns

        Args:
            df (pandas.DataFrame): Transaction dataframe for a specific token

        Returns:
            tuple: (confidence score, evidence)
        """
        # This requires price data which may not be available in the transaction dataframe
        # A placeholder implementation using token transfer patterns
        return 0.0, {}

    def _detect_rug_pull(self, df):
        """
        Detect rug pull patterns

        Args:
            df (pandas.DataFrame): Transaction dataframe for a specific token

        Returns:
            tuple: (confidence score, evidence)
        """
        # This requires liquidity pool data which may not be available in the transaction dataframe
        # A placeholder implementation using token transfer patterns
        return 0.0, {}

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)

    # Create pattern detector
    detector = PatternDetector()

    # Test with sample data
    sample_transactions = [
        {
            "signature": "sig1",
            "block_time": "2023-05-01T12:00:00",
            "sender": {"wallet": "wallet1"},
            "receiver": {"wallet": "wallet2"},
            "amount": 1000
        },
        {
            "signature": "sig2",
            "block_time": "2023-05-01T12:05:00",
            "sender": {"wallet": "wallet2"},
            "receiver": {"wallet": "wallet3"},
            "amount": 950
        },
        {
            "signature": "sig3",
            "block_time": "2023-05-01T12:10:00",
            "sender": {"wallet": "wallet3"},
            "receiver": {"wallet": "wallet4"},
            "amount": 900
        },
        {
            "signature": "sig4",
            "block_time": "2023-05-01T12:15:00",
            "sender": {"wallet": "wallet4"},
            "receiver": {"wallet": "wallet1"},
            "amount": 850
        }
    ]

    patterns = detector.detect_patterns(sample_transactions, "wallet1")
    print(f"Detected patterns: {patterns.keys()}")
    for pattern, details in patterns.items():
        print(f"Pattern: {pattern}, Score: {details['score']:.2f}")
        print(f"Description: {details['description']}")
        print(f"Evidence: {details['evidence']}")
