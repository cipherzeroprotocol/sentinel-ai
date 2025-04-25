"""
ICO Analysis Module for detecting suspicious ICO patterns
"""
import logging
import os
import sys
from datetime import datetime
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.collectors import helius_collector, range_collector, vybe_collector, rugcheck_collector
from data.storage.address_db import get_address_data, get_token_data
from ai.models.pattern_detector import PatternDetector
from ai.models.relationship_mapper import RelationshipMapper
from sentinel.ai.utils.ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)

class ICOAnalyzer:
    """
    ICO Analysis module for detecting suspicious ICO patterns
    """
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.relationship_mapper = RelationshipMapper()
        self.ai_analyzer = AIAnalyzer()
    
    def analyze(self, address=None, token_mint=None):
        """
        Analyze an ICO/token launch
        
        Args:
            address (str, optional): Creator address
            token_mint (str, optional): Token mint address
            
        Returns:
            dict: Analysis results
        """
        logger.info(f"Starting ICO analysis for address={address}, token_mint={token_mint}")
        
        # If token_mint is provided, try to get the creator from token data
        if token_mint and not address:
            token_data = self._collect_token_data(token_mint)
            if token_data and 'creator' in token_data:
                address = token_data['creator']
                logger.info(f"Found creator address {address} for token {token_mint}")
        
        if not address and not token_mint:
            logger.error("No address or token_mint provided for ICO analysis")
            return {"error": "No address or token_mint provided for analysis"}
        
        # Collect data
        analysis_data = {}
        
        if token_mint:
            token_data = self._collect_token_data(token_mint)
            analysis_data['token_data'] = token_data
        
        if address:
            creator_data = self._collect_address_data(address)
            analysis_data['creator_data'] = creator_data
            
            # Collect transaction data
            transactions = self._collect_transactions(address)
            analysis_data['transactions'] = transactions
            
            # Detect patterns
            patterns = self._detect_patterns(transactions, address)
            analysis_data['patterns'] = patterns
            
            # Map relationships
            relationships = self._map_relationships(transactions, address)
            analysis_data['relationships'] = relationships
        
        # Collect funding data
        funding_flow = self._analyze_funding_flow(analysis_data)
        analysis_data['funding_flow'] = funding_flow
        
        # Run AI analysis
        ai_analysis = self.ai_analyzer.analyze(analysis_data, "ico")
        
        # Combine results
        results = {
            "address": address,
            "token_mint": token_mint,
            "token_data": analysis_data.get('token_data', {}),
            "creator_data": analysis_data.get('creator_data', {}),
            "funding_flow": funding_flow,
            "patterns": patterns if 'patterns' in locals() else {},
            "relationships": relationships if 'relationships' in locals() else {},
            "ai_analysis": ai_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Completed ICO analysis for address={address}, token_mint={token_mint}")
        
        return results
    
    def _collect_token_data(self, token_mint):
        """
        Collect token data from various sources
        
        Args:
            token_mint (str): Token mint address
            
        Returns:
            dict: Combined token data
        """
        token_data = {}
        
        # Try to get token data from database first
        db_token_data = get_token_data(token_mint)
        if db_token_data:
            token_data.update(db_token_data)
        
        # Get token data from Vybe API
        try:
            vybe_token_data = vybe_collector.get_token_details(token_mint)
            if vybe_token_data:
                token_data.update(vybe_token_data)
        except Exception as e:
            logger.error(f"Error getting token data from Vybe: {str(e)}")
        
        # Get token risk data from RugCheck API
        try:
            rugcheck_data = rugcheck_collector.get_token_report_summary(token_mint)
            if rugcheck_data:
                # Add risk data
                token_data['risk_score'] = rugcheck_data.get('score_normalised')
                token_data['risk_factors'] = rugcheck_data.get('risks', [])
                token_data['token_type'] = rugcheck_data.get('tokenType')
        except Exception as e:
            logger.error(f"Error getting token risk data from RugCheck: {str(e)}")
        
        # Get detailed token report if available
        try:
            rugcheck_report = rugcheck_collector.get_token_report(token_mint)
            if rugcheck_report:
                # Add top holders
                token_data['top_holders'] = rugcheck_report.get('topHolders', [])
                
                # Add markets data
                token_data['markets'] = rugcheck_report.get('markets', [])
                
                # Add liquidity data
                token_data['total_market_liquidity'] = rugcheck_report.get('totalMarketLiquidity')
                
                # Add creation date
                token_data['creation_date'] = rugcheck_report.get('detectedAt')
        except Exception as e:
            logger.error(f"Error getting detailed token report from RugCheck: {str(e)}")
        
        return token_data
    
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
    
    def _collect_transactions(self, address, limit=100):
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
    
    def _analyze_funding_flow(self, analysis_data):
        """
        Analyze funding flow for an ICO
        
        Args:
            analysis_data (dict): Analysis data
            
        Returns:
            dict: Funding flow analysis
        """
        funding_flow = {
            "total_raised": 0,
            "investor_count": 0,
            "investors": [],
            "fund_destinations": []
        }
        
        # Get token mint
        token_mint = None
        if 'token_data' in analysis_data and 'mint' in analysis_data['token_data']:
            token_mint = analysis_data['token_data']['mint']
        
        # Get creator address
        creator_address = None
        if 'creator_data' in analysis_data and 'address' in analysis_data['creator_data']:
            creator_address = analysis_data['creator_data']['address']
        
        if not token_mint or not creator_address:
            return funding_flow
        
        # Get token transfers
        try:
            token_transfers = vybe_collector.get_token_transfers(mint_address=token_mint)
            
            if token_transfers:
                # Find initial token distribution
                initial_transfers = []
                for transfer in token_transfers:
                    if transfer.get('sender_address') == creator_address:
                        initial_transfers.append(transfer)
                
                # Extract investor data
                investors = {}
                for transfer in initial_transfers:
                    receiver = transfer.get('receiver_address')
                    if receiver and receiver != creator_address:
                        if receiver not in investors:
                            investors[receiver] = {
                                "address": receiver,
                                "amount": 0,
                                "amount_usd": 0,
                                "transaction_count": 0
                            }
                        
                        investors[receiver]["amount"] += transfer.get('amount', 0)
                        investors[receiver]["amount_usd"] += transfer.get('amount_usd', 0)
                        investors[receiver]["transaction_count"] += 1
                
                # Sort investors by amount
                investor_list = list(investors.values())
                investor_list.sort(key=lambda x: x['amount_usd'], reverse=True)
                
                # Update funding flow
                funding_flow["investors"] = investor_list
                funding_flow["investor_count"] = len(investor_list)
                funding_flow["total_raised"] = sum(inv['amount_usd'] for inv in investor_list)
                
                # Find fund destinations (where creator sent funds)
                creator_outgoing = []
                for tx in analysis_data.get('transactions', []):
                    if 'sender' in tx and tx['sender'].get('wallet') == creator_address:
                        creator_outgoing.append(tx)
                
                # Extract destination data
                destinations = {}
                for tx in creator_outgoing:
                    receiver = tx.get('receiver', {}).get('wallet')
                    if receiver and receiver != creator_address:
                        if receiver not in destinations:
                            destinations[receiver] = {
                                "address": receiver,
                                "amount": 0,
                                "amount_usd": 0,
                                "transaction_count": 0
                            }
                        
                        destinations[receiver]["amount"] += tx.get('amount', 0)
                        destinations[receiver]["amount_usd"] += tx.get('amount_usd', 0)
                        destinations[receiver]["transaction_count"] += 1
                
                # Sort destinations by amount
                destination_list = list(destinations.values())
                destination_list.sort(key=lambda x: x['amount_usd'], reverse=True)
                
                # Update funding flow
                funding_flow["fund_destinations"] = destination_list
        
        except Exception as e:
            logger.error(f"Error analyzing funding flow: {str(e)}")
        
        return funding_flow

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    # Create analyzer
    analyzer = ICOAnalyzer()
    
    # Test token mint (example, should be replaced with a real token)
    token_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    # Run analysis
    result = analyzer.analyze(token_mint=token_mint)
    
    # Print result
    print(json.dumps(result, indent=2))