"""
Entity relationship mapper for detecting connections between blockchain entities
"""
import logging
import numpy as np
import pandas as pd
import networkx as nx
from datetime import datetime, timedelta
import os
import sys
from collections import defaultdict

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)

class RelationshipMapper:
    """
    Entity relationship mapper for detecting connections between blockchain entities
    """
    
    # Relationship types
    RELATIONSHIP_TYPES = {
        "direct": "Direct transaction between entities",
        "indirect": "Indirect connection through intermediary",
        "strong": "Strong connection with multiple transactions",
        "weak": "Weak connection with few transactions",
        "recent": "Recent connection",
        "old": "Historical connection",
        "recurring": "Recurring connection with regular transactions",
        "one_time": "One-time connection",
        "high_value": "High-value connection",
        "low_value": "Low-value connection",
        "suspicious": "Connection with suspicious patterns",
        "normal": "Normal connection with no suspicious patterns",
        "team": "Likely part of the same team or organization",
        "exchange": "Connection with an exchange",
        "mixer": "Connection with a mixing service",
        "similar": "Addresses with similar patterns or structure"
    }
    
    def __init__(self):
        pass
    
    def map_relationships(self, transactions, addresses=None, include_labels=True):
        """
        Map relationships between entities in transaction data
        
        Args:
            transactions (list): List of transactions
            addresses (list, optional): List of addresses to focus on
            include_labels (bool): Whether to include entity labels in the output
            
        Returns:
            dict: Mapped relationships
        """
        if not transactions:
            logger.warning("No transactions provided")
            return {}
        
        # Convert to dataframe for easier analysis
        df = self._prepare_transaction_dataframe(transactions)
        
        # Create graph
        G = self._create_transaction_graph(df)
        
        # Map relationships
        relationships = self._extract_relationships(G, df, addresses, include_labels)
        
        return relationships
    
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
        
        # Extract labels
        if 'sender_entity' not in df.columns:
            try:
                df['sender_entity'] = df.apply(lambda x: x.get('sender', {}).get('entity', {}).get('name') 
                                            if isinstance(x.get('sender'), dict) and isinstance(x.get('sender', {}).get('entity'), dict) 
                                            else None, axis=1)
            except:
                df['sender_entity'] = None
        
        if 'sender_labels' not in df.columns:
            try:
                df['sender_labels'] = df.apply(lambda x: x.get('sender', {}).get('labels') 
                                            if isinstance(x.get('sender'), dict) 
                                            else None, axis=1)
            except:
                df['sender_labels'] = None
        
        if 'receiver_entity' not in df.columns:
            try:
                df['receiver_entity'] = df.apply(lambda x: x.get('receiver', {}).get('entity', {}).get('name') 
                                              if isinstance(x.get('receiver'), dict) and isinstance(x.get('receiver', {}).get('entity'), dict) 
                                              else None, axis=1)
            except:
                df['receiver_entity'] = None
        
        if 'receiver_labels' not in df.columns:
            try:
                df['receiver_labels'] = df.apply(lambda x: x.get('receiver', {}).get('labels') 
                                              if isinstance(x.get('receiver'), dict) 
                                              else None, axis=1)
            except:
                df['receiver_labels'] = None
        
        return df
    
    def _create_transaction_graph(self, df):
        """
        Create a directed graph from transaction data
        
        Args:
            df (pandas.DataFrame): Transaction dataframe
            
        Returns:
            networkx.DiGraph: Transaction graph
        """
        # Create directed graph
        G = nx.DiGraph()
        
        # Add edges for each transaction
        for _, row in df.iterrows():
            sender = row.get('sender_address')
            receiver = row.get('receiver_address')
            
            if pd.notna(sender) and pd.notna(receiver):
                # Add nodes with attributes
                if sender not in G:
                    G.add_node(sender, type='address')
                
                if receiver not in G:
                    G.add_node(receiver, type='address')
                
                # Add or update edge
                if G.has_edge(sender, receiver):
                    # Update edge attributes
                    G[sender][receiver]['weight'] += 1
                    
                    # Update transaction list
                    G[sender][receiver]['transactions'].append({
                        'signature': row.get('signature'),
                        'datetime': row.get('datetime'),
                        'amount': row.get('amount'),
                        'amount_usd': row.get('amount_usd')
                    })
                    
                    # Update time range
                    tx_time = row.get('datetime')
                    if tx_time < G[sender][receiver]['first_time']:
                        G[sender][receiver]['first_time'] = tx_time
                    
                    if tx_time > G[sender][receiver]['last_time']:
                        G[sender][receiver]['last_time'] = tx_time
                    
                    # Update value
                    amount_usd = row.get('amount_usd', 0)
                    if amount_usd:
                        G[sender][receiver]['total_value_usd'] += amount_usd
                else:
                    # Add new edge
                    G.add_edge(sender, receiver, 
                               weight=1, 
                               transactions=[{
                                   'signature': row.get('signature'),
                                   'datetime': row.get('datetime'),
                                   'amount': row.get('amount'),
                                   'amount_usd': row.get('amount_usd')
                               }],
                               first_time=row.get('datetime'),
                               last_time=row.get('datetime'),
                               total_value_usd=row.get('amount_usd', 0))
        
        # Add node attributes from dataframe
        for _, row in df.iterrows():
            sender = row.get('sender_address')
            receiver = row.get('receiver_address')
            
            if pd.notna(sender) and sender in G:
                # Add entity and labels
                if pd.notna(row.get('sender_entity')):
                    G.nodes[sender]['entity'] = row.get('sender_entity')
                
                if pd.notna(row.get('sender_labels')):
                    labels = row.get('sender_labels')
                    if isinstance(labels, list):
                        G.nodes[sender]['labels'] = labels
                    else:
                        G.nodes[sender]['labels'] = [labels]
            
            if pd.notna(receiver) and receiver in G:
                # Add entity and labels
                if pd.notna(row.get('receiver_entity')):
                    G.nodes[receiver]['entity'] = row.get('receiver_entity')
                
                if pd.notna(row.get('receiver_labels')):
                    labels = row.get('receiver_labels')
                    if isinstance(labels, list):
                        G.nodes[receiver]['labels'] = labels
                    else:
                        G.nodes[receiver]['labels'] = [labels]
        
        return G
    
    def _extract_relationships(self, G, df, addresses=None, include_labels=True):
        """
        Extract relationships from transaction graph
        
        Args:
            G (networkx.DiGraph): Transaction graph
            df (pandas.DataFrame): Transaction dataframe
            addresses (list, optional): List of addresses to focus on
            include_labels (bool): Whether to include entity labels in the output
            
        Returns:
            dict: Extracted relationships
        """
        relationships = {}
        
        # Filter addresses if provided
        target_addresses = set(addresses) if addresses else set(G.nodes())
        
        # Extract direct relationships
        direct_relationships = self._extract_direct_relationships(G, target_addresses, include_labels)
        relationships['direct'] = direct_relationships
        
        # Extract indirect relationships (2 hops)
        indirect_relationships = self._extract_indirect_relationships(G, target_addresses, include_labels)
        relationships['indirect'] = indirect_relationships
        
        # Extract communities (address clusters)
        communities = self._detect_communities(G)
        relationships['communities'] = communities
        
        # Extract central addresses
        central_addresses = self._identify_central_addresses(G)
        relationships['central_addresses'] = central_addresses
        
        return relationships
    
    def _extract_direct_relationships(self, G, addresses, include_labels):
        """
        Extract direct relationships from transaction graph
        
        Args:
            G (networkx.DiGraph): Transaction graph
            addresses (set): Set of addresses to focus on
            include_labels (bool): Whether to include entity labels in the output
            
        Returns:
            list: Direct relationships
        """
        direct_relationships = []
        
        for address in addresses:
            if address not in G:
                continue
            
            # Get outgoing connections
            for _, target, data in G.out_edges(address, data=True):
                relationship = {
                    "source": address,
                    "target": target,
                    "direction": "outgoing",
                    "weight": data.get("weight", 0),
                    "transaction_count": data.get("weight", 0),
                    "total_value_usd": data.get("total_value_usd", 0),
                    "first_time": data.get("first_time").isoformat() if hasattr(data.get("first_time"), "isoformat") else str(data.get("first_time")),
                    "last_time": data.get("last_time").isoformat() if hasattr(data.get("last_time"), "isoformat") else str(data.get("last_time")),
                    "relationship_types": self._determine_relationship_types(data)
                }
                
                # Add target entity and labels if available
                if include_labels:
                    target_node = G.nodes[target]
                    relationship["target_entity"] = target_node.get("entity")
                    relationship["target_labels"] = target_node.get("labels", [])
                
                direct_relationships.append(relationship)
            
            # Get incoming connections
            for source, _, data in G.in_edges(address, data=True):
                relationship = {
                    "source": source,
                    "target": address,
                    "direction": "incoming",
                    "weight": data.get("weight", 0),
                    "transaction_count": data.get("weight", 0),
                    "total_value_usd": data.get("total_value_usd", 0),
                    "first_time": data.get("first_time").isoformat() if hasattr(data.get("first_time"), "isoformat") else str(data.get("first_time")),
                    "last_time": data.get("last_time").isoformat() if hasattr(data.get("last_time"), "isoformat") else str(data.get("last_time")),
                    "relationship_types": self._determine_relationship_types(data)
                }
                
                # Add source entity and labels if available
                if include_labels:
                    source_node = G.nodes[source]
                    relationship["source_entity"] = source_node.get("entity")
                    relationship["source_labels"] = source_node.get("labels", [])
                
                direct_relationships.append(relationship)
        
        return direct_relationships
    
    def _extract_indirect_relationships(self, G, addresses, include_labels):
        """
        Extract indirect relationships (2 hops) from transaction graph
        
        Args:
            G (networkx.DiGraph): Transaction graph
            addresses (set): Set of addresses to focus on
            include_labels (bool): Whether to include entity labels in the output
            
        Returns:
            list: Indirect relationships
        """
        indirect_relationships = []
        
        for address in addresses:
            if address not in G:
                continue
            
            # Get 2-hop outgoing connections
            for _, intermediate in G.out_edges(address):
                for _, target in G.out_edges(intermediate):
                    if target != address and target not in G.successors(address) and target not in G.predecessors(address):
                        relationship = {
                            "source": address,
                            "intermediate": intermediate,
                            "target": target,
                            "direction": "outgoing",
                            "path": f"{address} -> {intermediate} -> {target}"
                        }
                        
                        # Add entity and labels if available
                        if include_labels:
                            intermediate_node = G.nodes[intermediate]
                            target_node = G.nodes[target]
                            
                            relationship["intermediate_entity"] = intermediate_node.get("entity")
                            relationship["intermediate_labels"] = intermediate_node.get("labels", [])
                            relationship["target_entity"] = target_node.get("entity")
                            relationship["target_labels"] = target_node.get("labels", [])
                        
                        indirect_relationships.append(relationship)
            
            # Get 2-hop incoming connections
            for source, _ in G.in_edges(address):
                for source2, _ in G.in_edges(source):
                    if source2 != address and source2 not in G.successors(address) and source2 not in G.predecessors(address):
                        relationship = {
                            "source": source2,
                            "intermediate": source,
                            "target": address,
                            "direction": "incoming",
                            "path": f"{source2} -> {source} -> {address}"
                        }
                        
                        # Add entity and labels if available
                        if include_labels:
                            source_node = G.nodes[source2]
                            intermediate_node = G.nodes[source]
                            
                            relationship["source_entity"] = source_node.get("entity")
                            relationship["source_labels"] = source_node.get("labels", [])
                            relationship["intermediate_entity"] = intermediate_node.get("entity")
                            relationship["intermediate_labels"] = intermediate_node.get("labels", [])
                        
                        indirect_relationships.append(relationship)
        
        return indirect_relationships
    
    def _determine_relationship_types(self, edge_data):
        """
        Determine relationship types from edge data
        
        Args:
            edge_data (dict): Edge data
            
        Returns:
            list: Relationship types
        """
        relationship_types = []
        
        # Check transaction count
        transaction_count = edge_data.get("weight", 0)
        if transaction_count >= 5:
            relationship_types.append("strong")
        else:
            relationship_types.append("weak")
        
        # Check recency
        last_time = edge_data.get("last_time")
        if last_time and isinstance(last_time, datetime):
            now = datetime.now()
            if (now - last_time).days <= 7:
                relationship_types.append("recent")
            else:
                relationship_types.append("old")
        
        # Check regularity
        first_time = edge_data.get("first_time")
        if first_time and last_time and transaction_count > 1:
            if isinstance(first_time, datetime) and isinstance(last_time, datetime):
                time_range = (last_time - first_time).total_seconds()
                if time_range > 0:
                    avg_time_between_tx = time_range / (transaction_count - 1)
                    if avg_time_between_tx <= 86400:  # 1 day in seconds
                        relationship_types.append("recurring")
                    else:
                        relationship_types.append("occasional")
        elif transaction_count == 1:
            relationship_types.append("one_time")
        
        # Check value
        total_value_usd = edge_data.get("total_value_usd", 0)
        if total_value_usd >= 10000:
            relationship_types.append("high_value")
        else:
            relationship_types.append("low_value")
        
        return relationship_types
    
    def _detect_communities(self, G):
        """
        Detect communities (address clusters) in the transaction graph
        
        Args:
            G (networkx.DiGraph): Transaction graph
            
        Returns:
            list: Communities
        """
        # Convert directed graph to undirected for community detection
        undirected_G = G.to_undirected()
        
        # Detect communities using Louvain method
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(undirected_G)
            
            # Group addresses by community
            community_groups = defaultdict(list)
            for node, community_id in partition.items():
                community_groups[community_id].append(node)
            
            # Format communities
            communities = []
            for community_id, addresses in community_groups.items():
                if len(addresses) >= 2:  # Only include groups with at least 2 addresses
                    communities.append({
                        "id": community_id,
                        "addresses": addresses,
                        "size": len(addresses)
                    })
            
            # Sort by size (descending)
            communities.sort(key=lambda x: x["size"], reverse=True)
            
            return communities
        except ImportError:
            # Fall back to connected components
            logger.warning("python-louvain not installed, falling back to connected components")
            
            # Find connected components
            components = list(nx.connected_components(undirected_G))
            
            # Format communities
            communities = []
            for i, component in enumerate(components):
                if len(component) >= 2:  # Only include components with at least 2 addresses
                    communities.append({
                        "id": i,
                        "addresses": list(component),
                        "size": len(component)
                    })
            
            # Sort by size (descending)
            communities.sort(key=lambda x: x["size"], reverse=True)
            
            return communities
    
    def _identify_central_addresses(self, G):
        """
        Identify central addresses in the transaction graph
        
        Args:
            G (networkx.DiGraph): Transaction graph
            
        Returns:
            list: Central addresses
        """
        # Calculate degree centrality
        in_degree_centrality = nx.in_degree_centrality(G)
        out_degree_centrality = nx.out_degree_centrality(G)
        
        # Calculate eigenvector centrality
        try:
            eigenvector_centrality = nx.eigenvector_centrality(G)
        except:
            eigenvector_centrality = {}
        
        # Calculate betweenness centrality (can be slow for large graphs)
        try:
            betweenness_centrality = nx.betweenness_centrality(G, k=min(100, len(G)))
        except:
            betweenness_centrality = {}
        
        # Combine centrality measures
        central_addresses = []
        for node in G.nodes():
            if node in in_degree_centrality or node in out_degree_centrality:
                central_addresses.append({
                    "address": node,
                    "in_degree_centrality": in_degree_centrality.get(node, 0),
                    "out_degree_centrality": out_degree_centrality.get(node, 0),
                    "eigenvector_centrality": eigenvector_centrality.get(node, 0),
                    "betweenness_centrality": betweenness_centrality.get(node, 0),
                    "combined_centrality": (
                        in_degree_centrality.get(node, 0) +
                        out_degree_centrality.get(node, 0) +
                        eigenvector_centrality.get(node, 0) +
                        betweenness_centrality.get(node, 0)
                    ) / 4
                })
        
        # Sort by combined centrality (descending)
        central_addresses.sort(key=lambda x: x["combined_centrality"], reverse=True)
        
        # Return top 20 central addresses
        return central_addresses[:20]
    
    def analyze_entity(self, entity_data):
        """
        Analyze an entity based on its relationships
        
        Args:
            entity_data (dict): Entity data including relationships
            
        Returns:
            dict: Entity analysis
        """
        if not entity_data or "relationships" not in entity_data:
            logger.warning("No entity data or relationships provided")
            return {}
        
        # Extract direct relationships
        direct_relationships = entity_data.get("relationships", {}).get("direct", [])
        
        # Extract indirect relationships
        indirect_relationships = entity_data.get("relationships", {}).get("indirect", [])
        
        # Analyze transaction patterns
        transaction_patterns = self._analyze_transaction_patterns(direct_relationships)
        
        # Identify significant counterparties
        significant_counterparties = self._identify_significant_counterparties(direct_relationships)
        
        # Identify entity type
        entity_type, entity_type_confidence = self._identify_entity_type(
            direct_relationships, 
            indirect_relationships, 
            transaction_patterns
        )
        
        # Format results
        analysis = {
            "entity_type": entity_type,
            "entity_type_confidence": entity_type_confidence,
            "transaction_patterns": transaction_patterns,
            "significant_counterparties": significant_counterparties
        }
        
        return analysis
    
    def _analyze_transaction_patterns(self, relationships):
        """
        Analyze transaction patterns in relationships
        
        Args:
            relationships (list): List of relationships
            
        Returns:
            dict: Transaction patterns
        """
        if not relationships:
            return {}
        
        # Extract transaction counts
        tx_counts = [r.get("transaction_count", 0) for r in relationships]
        
        # Extract values
        values = [r.get("total_value_usd", 0) for r in relationships]
        
        # Extract relationship types
        rel_types = []
        for r in relationships:
            rel_types.extend(r.get("relationship_types", []))
        
        # Count relationship types
        type_counts = {}
        for rel_type in rel_types:
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        
        # Identify most common relationship types
        common_types = []
        for rel_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            common_types.append({
                "type": rel_type,
                "count": count,
                "description": self.RELATIONSHIP_TYPES.get(rel_type, "Unknown relationship type")
            })
        
        # Calculate statistics
        patterns = {
            "total_relationships": len(relationships),
            "total_transactions": sum(tx_counts),
            "total_value_usd": sum(values),
            "avg_transactions_per_relationship": np.mean(tx_counts) if tx_counts else 0,
            "avg_value_per_relationship": np.mean(values) if values else 0,
            "common_relationship_types": common_types
        }
        
        return patterns
    
    def _identify_significant_counterparties(self, relationships):
        """
        Identify significant counterparties in relationships
        
        Args:
            relationships (list): List of relationships
            
        Returns:
            list: Significant counterparties
        """
        if not relationships:
            return []
        
        # Group by counterparty
        counterparties = {}
        
        for r in relationships:
            target = r.get("target")
            source = r.get("source")
            direction = r.get("direction")
            
            if direction == "outgoing":
                counterparty = target
            elif direction == "incoming":
                counterparty = source
            else:
                continue
            
            if counterparty not in counterparties:
                counterparties[counterparty] = {
                    "address": counterparty,
                    "entity": r.get("target_entity" if direction == "outgoing" else "source_entity"),
                    "labels": r.get("target_labels" if direction == "outgoing" else "source_labels", []),
                    "incoming_count": 0,
                    "outgoing_count": 0,
                    "incoming_value_usd": 0,
                    "outgoing_value_usd": 0,
                    "first_time": r.get("first_time"),
                    "last_time": r.get("last_time"),
                    "relationship_types": r.get("relationship_types", [])
                }
            
            if direction == "outgoing":
                counterparties[counterparty]["outgoing_count"] += r.get("transaction_count", 0)
                counterparties[counterparty]["outgoing_value_usd"] += r.get("total_value_usd", 0)
            else:
                counterparties[counterparty]["incoming_count"] += r.get("transaction_count", 0)
                counterparties[counterparty]["incoming_value_usd"] += r.get("total_value_usd", 0)
        
        # Calculate total transaction count and value for each counterparty
        for cp in counterparties.values():
            cp["total_count"] = cp["incoming_count"] + cp["outgoing_count"]
            cp["total_value_usd"] = cp["incoming_value_usd"] + cp["outgoing_value_usd"]
        
        # Convert to list and sort by total value (descending)
        counterparty_list = list(counterparties.values())
        counterparty_list.sort(key=lambda x: x["total_value_usd"], reverse=True)
        
        return counterparty_list
    
    def _identify_entity_type(self, direct_relationships, indirect_relationships, transaction_patterns):
        """
        Identify entity type based on relationships and transaction patterns
        
        Args:
            direct_relationships (list): Direct relationships
            indirect_relationships (list): Indirect relationships
            transaction_patterns (dict): Transaction patterns
            
        Returns:
            tuple: (entity_type, confidence)
        """
        # Define entity type detection rules
        rules = [
            {
                "type": "exchange",
                "conditions": [
                    lambda dr, ir, tp: tp.get("total_relationships", 0) > 100,
                    lambda dr, ir, tp: tp.get("total_transactions", 0) > 1000,
                    lambda dr, ir, tp: any("exchange" in r.get("target_labels", []) or "exchange" in r.get("source_labels", []) for r in dr)
                ],
                "weight": 0.8
            },
            {
                "type": "mixer",
                "conditions": [
                    lambda dr, ir, tp: any("mixer" in r.get("relationship_types", []) for r in dr),
                    lambda dr, ir, tp: any("mixer" in r.get("target_labels", []) or "mixer" in r.get("source_labels", []) for r in dr),
                    lambda dr, ir, tp: tp.get("avg_transactions_per_relationship", 0) < 2
                ],
                "weight": 0.9
            },
            {
                "type": "whale",
                "conditions": [
                    lambda dr, ir, tp: tp.get("total_value_usd", 0) > 1000000,
                    lambda dr, ir, tp: tp.get("avg_value_per_relationship", 0) > 50000
                ],
                "weight": 0.7
            },
            {
                "type": "team",
                "conditions": [
                    lambda dr, ir, tp: any("team" in r.get("relationship_types", []) for r in dr),
                    lambda dr, ir, tp: tp.get("avg_transactions_per_relationship", 0) > 5,
                    lambda dr, ir, tp: any("recurring" in r.get("relationship_types", []) for r in dr)
                ],
                "weight": 0.6
            },
            {
                "type": "normal",
                "conditions": [
                    lambda dr, ir, tp: True  # Default type
                ],
                "weight": 0.5
            }
        ]
        
        # Evaluate rules
        type_scores = {}
        
        for rule in rules:
            entity_type = rule["type"]
            conditions = rule["conditions"]
            weight = rule["weight"]
            
            # Check how many conditions are met
            conditions_met = sum(1 for condition in conditions if condition(direct_relationships, indirect_relationships, transaction_patterns))
            conditions_total = len(conditions)
            
            # Calculate score
            if conditions_total > 0:
                score = (conditions_met / conditions_total) * weight
                type_scores[entity_type] = score
        
        # Get entity type with highest score
        if type_scores:
            entity_type = max(type_scores.items(), key=lambda x: x[1])[0]
            confidence = type_scores[entity_type]
        else:
            entity_type = "unknown"
            confidence = 0.0
        
        return entity_type, confidence

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    # Create relationship mapper
    mapper = RelationshipMapper()
    
    # Test with sample data
    sample_transactions = [
        {
            "signature": "sig1",
            "block_time": "2023-05-01T12:00:00",
            "sender": {"wallet": "wallet1", "entity": "Exchange A", "labels": ["exchange"]},
            "receiver": {"wallet": "wallet2"},
            "amount": 1000,
            "amount_usd": 1000
        },
        {
            "signature": "sig2",
            "block_time": "2023-05-01T12:05:00",
            "sender": {"wallet": "wallet2"},
            "receiver": {"wallet": "wallet3"},
            "amount": 950,
            "amount_usd": 950
        },
        {
            "signature": "sig3",
            "block_time": "2023-05-01T12:10:00",
            "sender": {"wallet": "wallet3"},
            "receiver": {"wallet": "wallet4"},
            "amount": 900,
            "amount_usd": 900
        },
        {
            "signature": "sig4",
            "block_time": "2023-05-01T12:15:00",
            "sender": {"wallet": "wallet4"},
            "receiver": {"wallet": "wallet1", "entity": "Exchange A", "labels": ["exchange"]},
            "amount": 850,
            "amount_usd": 850
        }
    ]
    
    relationships = mapper.map_relationships(sample_transactions, ["wallet1"])
    print(f"Mapped relationships: {relationships.keys()}")
    
    # Analyze entity
    entity_data = {
        "address": "wallet1",
        "relationships": relationships
    }
    
    analysis = mapper.analyze_entity(entity_data)
    print(f"Entity analysis: {analysis}")