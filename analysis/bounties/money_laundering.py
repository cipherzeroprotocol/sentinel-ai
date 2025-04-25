"""
Money Laundering Analysis Module for detecting suspicious transaction patterns
"""
import logging
import os
import sys
from datetime import datetime
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.collectors import helius_collector, range_collector, vybe_collector
from data.storage.address_db import get_address_data
from ai.models.pattern_detector import PatternDetector
from ai.models.relationship_mapper import RelationshipMapper
from ai.utils.ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)

class MoneyLaunderingAnalyzer:
    """
    Money Laundering Analysis module for detecting suspicious transaction patterns
    """
    
    # Known high-risk pattern types for money laundering
    HIGH_RISK_PATTERNS = [
        "layering",
        "smurfing",
        "round_trip",
        "mixer_use",
        "high_velocity"
    ]
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.relationship_mapper = RelationshipMapper()
        self.ai_analyzer = AIAnalyzer()
    
    def analyze(self, address):
        """
        Analyze an address for money laundering patterns
        
        Args:
            address (str): Address to analyze
            
        Returns:
            dict: Analysis results
        """
        logger.info(f"Starting money laundering analysis for address {address}")
        
        if not address:
            logger.error("No address provided for money laundering analysis")
            return {"error": "No address provided for analysis"}
        
        # Collect data
        analysis_data = {}
        
        # Get address data
        address_data = self._collect_address_data(address)
        analysis_data['address_data'] = address_data
        
        # Collect transaction data
        transactions = self._collect_transactions(address)
        analysis_data['transactions'] = transactions
        
        # Detect patterns
        patterns = self._detect_patterns(transactions, address)
        analysis_data['patterns'] = patterns
        
        # Map relationships
        relationships = self._map_relationships(transactions, address)
        analysis_data['relationships'] = relationships
        
        # Analyze flow patterns
        flow_patterns = self._analyze_flow_patterns(transactions, patterns, address)
        analysis_data['flow_patterns'] = flow_patterns
        
        # Identify high-risk counterparties
        counterparties = self._identify_counterparties(transactions, relationships, address)
        analysis_data['counterparties'] = counterparties
        
        # Detect cross-chain transfers
        cross_chain = self._detect_cross_chain_transfers(transactions, address)
        analysis_data['cross_chain_transfers'] = cross_chain
        
        # Run AI analysis
        ai_analysis = self.ai_analyzer.analyze(analysis_data, "laundering")
        
        # Calculate risk score
        risk_score, risk_factors = self._calculate_risk_score(patterns, counterparties, cross_chain)
        
        # Combine results
        results = {
            "address": address,
            "address_data": address_data,
            "flow_patterns": flow_patterns,
            "counterparties": counterparties,
            "cross_chain_transfers": cross_chain,
            "patterns": patterns,
            "relationships": relationships,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "ai_analysis": ai_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Completed money laundering analysis for address {address}")
        
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
    
    def _analyze_flow_patterns(self, transactions, patterns, address):
        """
        Analyze flow patterns for money laundering
        
        Args:
            transactions (list): List of transactions
            patterns (dict): Detected patterns
            address (str): Address to analyze
            
        Returns:
            list: Flow patterns
        """
        flow_patterns = []
        
        # Check for layering patterns
        if "layering" in patterns:
            layering_pattern = patterns["layering"]
            flow_patterns.append({
                "type": "layering",
                "description": "Multiple transfers through intermediate addresses to obfuscate source/destination",
                "score": layering_pattern["score"],
                "evidence": layering_pattern["evidence"]
            })
        
        # Check for smurfing patterns
        if "smurfing" in patterns:
            smurfing_pattern = patterns["smurfing"]
            flow_patterns.append({
                "type": "smurfing",
                "description": "Breaking large amounts into smaller transactions to avoid detection",
                "score": smurfing_pattern["score"],
                "evidence": smurfing_pattern["evidence"]
            })
        
        # Check for round-trip patterns
        if "round_trip" in patterns:
            round_trip_pattern = patterns["round_trip"]
            flow_patterns.append({
                "type": "round_trip",
                "description": "Funds that return to the original address after passing through other addresses",
                "score": round_trip_pattern["score"],
                "evidence": round_trip_pattern["evidence"]
            })
        
        # Check for mixer usage
        if "mixer_use" in patterns:
            mixer_pattern = patterns["mixer_use"]
            flow_patterns.append({
                "type": "mixer_use",
                "description": "Using mixing services to obfuscate transaction trail",
                "score": mixer_pattern["score"],
                "evidence": mixer_pattern["evidence"]
            })
        
        # Check for high velocity
        if "high_velocity" in patterns:
            velocity_pattern = patterns["high_velocity"]
            flow_patterns.append({
                "type": "high_velocity",
                "description": "Unusually high transaction velocity for an address",
                "score": velocity_pattern["score"],
                "evidence": velocity_pattern["evidence"]
            })
        
        # Sort by score (descending)
        flow_patterns.sort(key=lambda x: x["score"], reverse=True)
        
        return flow_patterns
    
    def _identify_counterparties(self, transactions, relationships, address):
        """
        Identify high-risk counterparties
        
        Args:
            transactions (list): List of transactions
            relationships (dict): Mapped relationships
            address (str): Address to analyze
            
        Returns:
            list: High-risk counterparties
        """
        # Known mixer and high-risk program IDs (from knowledge base)
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
        
        counterparties = []
        
        # Extract direct relationships
        direct_relationships = relationships.get('direct', [])
        
        # Group by counterparty
        counterparty_map = {}
        
        for rel in direct_relationships:
            counterparty = None
            direction = rel.get('direction')
            
            if direction == 'outgoing':
                counterparty = rel.get('target')
            elif direction == 'incoming':
                counterparty = rel.get('source')
            
            if not counterparty or counterparty == address:
                continue
            
            if counterparty not in counterparty_map:
                counterparty_map[counterparty] = {
                    "address": counterparty,
                    "entity": rel.get('target_entity' if direction == 'outgoing' else 'source_entity'),
                    "labels": rel.get('target_labels' if direction == 'outgoing' else 'source_labels', []),
                    "incoming_count": 0,
                    "outgoing_count": 0,
                    "incoming_value_usd": 0,
                    "outgoing_value_usd": 0,
                    "first_time": rel.get('first_time'),
                    "last_time": rel.get('last_time'),
                    "relationship_types": rel.get('relationship_types', []),
                    "is_mixer": counterparty in KNOWN_MIXERS
                }
            
            if direction == 'outgoing':
                counterparty_map[counterparty]['outgoing_count'] += rel.get('transaction_count', 0)
                counterparty_map[counterparty]['outgoing_value_usd'] += rel.get('total_value_usd', 0)
            else:
                counterparty_map[counterparty]['incoming_count'] += rel.get('transaction_count', 0)
                counterparty_map[counterparty]['incoming_value_usd'] += rel.get('total_value_usd', 0)
        
        # Convert to list and calculate risk score
        for cp in counterparty_map.values():
            cp['total_count'] = cp['incoming_count'] + cp['outgoing_count']
            cp['total_value_usd'] = cp['incoming_value_usd'] + cp['outgoing_value_usd']
            
            # Calculate risk score
            risk_score = 0
            
            # Mixer = very high risk
            if cp['is_mixer']:
                risk_score += 90
            
            # Check labels for high risk indicators
            high_risk_labels = ['mixer', 'high_risk', 'suspicious', 'scam', 'fraud', 'sanctioned']
            cp['high_risk_labels'] = [label for label in cp.get('labels', []) if label.lower() in high_risk_labels]
            
            if cp['high_risk_labels']:
                risk_score += 70
            
            # Check relationship types
            high_risk_rel_types = ['suspicious', 'mixer', 'high_value']
            cp['high_risk_relationships'] = [rel for rel in cp.get('relationship_types', []) if rel.lower() in high_risk_rel_types]
            
            if cp['high_risk_relationships']:
                risk_score += 50
            
            # High value transfers
            if cp['total_value_usd'] > 100000:
                risk_score += 30
            elif cp['total_value_usd'] > 10000:
                risk_score += 15
            
            # Normalize risk score
            cp['risk_score'] = min(100, risk_score)
            
            # Add to counterparties list if risk score is significant
            if cp['risk_score'] >= 30 or cp['is_mixer'] or cp['high_risk_labels']:
                counterparties.append(cp)
        
        # Sort by risk score (descending)
        counterparties.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return counterparties
    
    def _detect_cross_chain_transfers(self, transactions, address):
        """
        Detect cross-chain transfers
        
        Args:
            transactions (list): List of transactions
            address (str): Address to analyze
            
        Returns:
            list: Cross-chain transfers
        """
        # Known bridge program IDs (from knowledge base)
        BRIDGE_PROGRAMS = {
            "wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb": {
                "name": "Wormhole",
                "chains": ["ethereum", "bsc", "avalanche", "polygon", "arbitrum"]
            },
            "3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5": {
                "name": "Wormhole Portal",
                "chains": ["ethereum", "bsc", "avalanche", "polygon", "arbitrum"]
            },
            "worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth": {
                "name": "Wormhole Token Bridge",
                "chains": ["ethereum", "bsc", "avalanche", "polygon", "arbitrum"]
            }
        }
        
        cross_chain_transfers = []
        
        # Look for bridge transactions
        for tx in transactions:
            program_id = None
            
            # Extract program ID
            if 'program_id' in tx:
                program_id = tx['program_id']
            elif 'program' in tx and isinstance(tx['program'], dict) and 'id' in tx['program']:
                program_id = tx['program']['id']
            
            if not program_id or program_id not in BRIDGE_PROGRAMS:
                continue
            
            # Found a bridge transaction
            bridge_info = BRIDGE_PROGRAMS[program_id]
            
            # Extract relevant data
            sender = None
            receiver = None
            
            if 'sender' in tx:
                if isinstance(tx['sender'], dict) and 'wallet' in tx['sender']:
                    sender = tx['sender']['wallet']
                else:
                    sender = tx['sender']
            
            if 'receiver' in tx:
                if isinstance(tx['receiver'], dict) and 'wallet' in tx['receiver']:
                    receiver = tx['receiver']['wallet']
                else:
                    receiver = tx['receiver']
            
            # Determine direction
            is_outgoing = sender == address
            is_incoming = receiver == address
            
            if not is_outgoing and not is_incoming:
                continue
            
            # Extract amount
            amount = tx.get('amount', 0)
            amount_usd = tx.get('amount_usd', 0)
            
            # Extract destination chain (simplified, would need deeper parsing in real implementation)
            destination_chain = bridge_info['chains'][0] if bridge_info['chains'] else 'unknown'
            
            # Create transfer record
            transfer = {
                "bridge_name": bridge_info['name'],
                "program_id": program_id,
                "transaction_hash": tx.get('signature'),
                "source_chain": "solana",
                "destination_chain": destination_chain,
                "direction": "outgoing" if is_outgoing else "incoming",
                "amount": amount,
                "volume_usd": amount_usd,
                "timestamp": tx.get('block_time'),
                "sender": sender,
                "receiver": receiver
            }
            
            cross_chain_transfers.append(transfer)
        
        return cross_chain_transfers
    
    def _calculate_risk_score(self, patterns, counterparties, cross_chain):
        """
        Calculate money laundering risk score
        
        Args:
            patterns (dict): Detected patterns
            counterparties (list): High-risk counterparties
            cross_chain (list): Cross-chain transfers
            
        Returns:
            tuple: (risk_score, risk_factors)
        """
        risk_score = 0
        risk_factors = []
        
        # Check for high-risk patterns
        for pattern_type in self.HIGH_RISK_PATTERNS:
            if pattern_type in patterns:
                pattern = patterns[pattern_type]
                pattern_score = pattern['score'] * 100  # Convert to 0-100 scale
                
                if pattern_score >= 70:
                    risk_score += pattern_score * 0.2  # 20% weight per high-risk pattern
                    risk_factors.append(f"High {pattern_type} pattern detected")
        
        # Check for high-risk counterparties
        high_risk_cps = [cp for cp in counterparties if cp.get('risk_score', 0) >= 70]
        if high_risk_cps:
            risk_score += min(50, len(high_risk_cps) * 10)  # Up to 50 points
            risk_factors.append(f"Transactions with {len(high_risk_cps)} high-risk counterparties")
        
        # Check for mixer interactions
        mixer_cps = [cp for cp in counterparties if cp.get('is_mixer', False)]
        if mixer_cps:
            risk_score += min(80, len(mixer_cps) * 40)  # Up to 80 points
            risk_factors.append(f"Transactions with {len(mixer_cps)} mixing services")
        
        # Check for cross-chain transfers
        if cross_chain:
            risk_score += min(40, len(cross_chain) * 10)  # Up to 40 points
            risk_factors.append(f"{len(cross_chain)} cross-chain transfers detected")
        
        # Cap risk score at 100
        risk_score = min(100, risk_score)
        
        return risk_score, risk_factors

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    # Create analyzer
    analyzer = MoneyLaunderingAnalyzer()
    
    # Test address (example, should be replaced with a real address)
    address = "VinesRG7K3ubzKLbxXz197c1RHV3cACkvGr9Zca7BSw"
    
    # Run analysis
    result = analyzer.analyze(address)
    
    # Print result
    print(json.dumps(result, indent=2))