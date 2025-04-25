"""
Rugpull Detector Module for identifying potential token rugpulls
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

class RugpullDetector:
    """
    Rugpull Detector module for identifying potential token rugpulls
    """
    
    # Key risk factors for rugpulls
    RUGPULL_RISK_FACTORS = [
        "mint_authority_enabled",
        "freeze_authority_enabled",
        "no_liquidity_lock",
        "short_liquidity_lock",
        "high_team_token_concentration",
        "anonymous_team",
        "suspicious_creator_history",
        "copycat_token",
        "misleading_token_name",
        "honeypot_code"
    ]
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.relationship_mapper = RelationshipMapper()
        self.ai_analyzer = AIAnalyzer()
    
    def analyze(self, token_mint):
        """
        Analyze a token for rugpull risk
        
        Args:
            token_mint (str): Token mint address
            
        Returns:
            dict: Analysis results
        """
        logger.info(f"Starting rugpull analysis for token {token_mint}")
        
        if not token_mint:
            logger.error("No token_mint provided for rugpull analysis")
            return {"error": "No token_mint provided for analysis"}
        
        # Collect data
        analysis_data = {}
        
        # Get token data
        token_data = self._collect_token_data(token_mint)
        analysis_data['token_data'] = token_data
        
        # Get creator data
        creator_address = token_data.get('creator')
        if creator_address:
            creator_data = self._collect_address_data(creator_address)
            analysis_data['creator_data'] = creator_data
            
            # Get creator transactions
            creator_transactions = self._collect_transactions(creator_address)
            analysis_data['creator_transactions'] = creator_transactions
            
            # Detect patterns in creator transactions
            creator_patterns = self._detect_patterns(creator_transactions, creator_address)
            analysis_data['creator_patterns'] = creator_patterns
            
            # Map creator relationships
            creator_relationships = self._map_relationships(creator_transactions, creator_address)
            analysis_data['creator_relationships'] = creator_relationships
            
            # Get creator's other tokens
            creator_tokens = self._get_creator_tokens(creator_address)
            analysis_data['creator_tokens'] = creator_tokens
        
        # Analyze liquidity
        liquidity_data = self._analyze_liquidity(token_data)
        analysis_data['liquidity_data'] = liquidity_data
        
        # Get token price history
        price_history = self._get_price_history(token_mint)
        analysis_data['price_history'] = price_history
        
        # Analyze token holders
        holder_analysis = self._analyze_holders(token_data)
        analysis_data['holder_analysis'] = holder_analysis
        
        # Analyze RugCheck data
        rugcheck_analysis = self._analyze_rugcheck_data(token_data)
        analysis_data['rugcheck_analysis'] = rugcheck_analysis
        
        # Calculate risk factors
        risk_factors, risk_score = self._calculate_rugpull_risk(analysis_data)
        
        # Run AI analysis
        ai_analysis = self.ai_analyzer.analyze(analysis_data, "rugpull")
        
        # Combine results
        results = {
            "token_mint": token_mint,
            "token_data": token_data,
            "creator_data": creator_data if 'creator_data' in analysis_data else {},
            "liquidity_data": liquidity_data,
            "holder_analysis": holder_analysis,
            "price_history": price_history,
            "rugcheck_analysis": rugcheck_analysis,
            "risk_factors": risk_factors,
            "risk_score": risk_score,
            "ai_analysis": ai_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Completed rugpull analysis for token {token_mint}")
        
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
                # Add key data from report
                token_data['creator'] = rugcheck_report.get('creator')
                token_data['mint_authority'] = rugcheck_report.get('mintAuthority')
                token_data['freeze_authority'] = rugcheck_report.get('freezeAuthority')
                token_data['token_program'] = rugcheck_report.get('tokenProgram')
                
                # Add top holders
                token_data['top_holders'] = rugcheck_report.get('topHolders', [])
                
                # Add markets data
                token_data['markets'] = rugcheck_report.get('markets', [])
                
                # Add liquidity data
                token_data['total_market_liquidity'] = rugcheck_report.get('totalMarketLiquidity')
                
                # Add creation date
                token_data['creation_date'] = rugcheck_report.get('detectedAt')
                
                # Add locker data
                token_data['lockers'] = rugcheck_report.get('lockers', {})
                token_data['locker_owners'] = rugcheck_report.get('lockerOwners', {})
                
                # Add creator's previous tokens
                token_data['creator_tokens'] = rugcheck_report.get('creatorTokens', [])
                
                # Add file metadata
                token_data['file_meta'] = rugcheck_report.get('fileMeta', {})
                
                # Add insider networks
                token_data['insider_networks'] = rugcheck_report.get('insiderNetworks', [])
                
                # Add known accounts
                token_data['known_accounts'] = rugcheck_report.get('knownAccounts', {})
        except Exception as e:
            logger.error(f"Error getting detailed token report from RugCheck: {str(e)}")
        
        # Get token holders from Vybe API
        try:
            top_holders = vybe_collector.get_top_token_holders(token_mint)
            if top_holders:
                token_data['vybe_top_holders'] = top_holders
        except Exception as e:
            logger.error(f"Error getting top token holders from Vybe: {str(e)}")
        
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
    
    def _get_creator_tokens(self, creator_address):
        """
        Get other tokens created by the same creator
        
        Args:
            creator_address (str): Creator address
            
        Returns:
            list: Other tokens by the same creator
        """
        creator_tokens = []
        
        # Try to get from database
        # This is a placeholder - in a real implementation, you would query the database
        
        return creator_tokens
    
    def _analyze_liquidity(self, token_data):
        """
        Analyze token liquidity
        
        Args:
            token_data (dict): Token data
            
        Returns:
            dict: Liquidity analysis
        """
        liquidity_data = {
            "current_liquidity_usd": 0,
            "locked_liquidity_usd": 0,
            "locked_percentage": 0,
            "lock_expiry": None,
            "liquidity_concentration": 0,
            "markets": []
        }
        
        # Extract markets data
        markets = token_data.get('markets', [])
        
        # Calculate total liquidity
        total_liquidity = token_data.get('total_market_liquidity', 0)
        liquidity_data['current_liquidity_usd'] = total_liquidity
        
        # Extract locker data
        lockers = token_data.get('lockers', {})
        locked_liquidity = 0
        latest_expiry = None
        
        for locker_id, locker_data in lockers.items():
            locked_usd = locker_data.get('usdcLocked', 0)
            locked_liquidity += locked_usd
            
            # Track latest expiry
            unlock_date = locker_data.get('unlockDate')
            if unlock_date:
                try:
                    unlock_timestamp = int(unlock_date)
                    if latest_expiry is None or unlock_timestamp > latest_expiry:
                        latest_expiry = unlock_timestamp
                except:
                    pass
        
        liquidity_data['locked_liquidity_usd'] = locked_liquidity
        
        # Calculate locked percentage
        if total_liquidity > 0:
            locked_percentage = (locked_liquidity / total_liquidity) * 100
            liquidity_data['locked_percentage'] = locked_percentage
        
        # Set lock expiry
        if latest_expiry:
            try:
                # Convert to readable date
                expiry_date = datetime.fromtimestamp(latest_expiry).isoformat()
                liquidity_data['lock_expiry'] = expiry_date
            except:
                liquidity_data['lock_expiry'] = str(latest_expiry)
        
        # Analyze markets
        simplified_markets = []
        for market in markets:
            lp_data = market.get('lp', {})
            
            simplified_market = {
                "market_type": market.get('marketType'),
                "liquidity_usd": lp_data.get('baseUSD', 0) + lp_data.get('quoteUSD', 0),
                "locked_percentage": lp_data.get('lpLockedPct', 0),
                "locked_usd": lp_data.get('lpLockedUSD', 0)
            }
            
            simplified_markets.append(simplified_market)
        
        liquidity_data['markets'] = simplified_markets
        
        return liquidity_data
    
    def _get_price_history(self, token_mint):
        """
        Get token price history
        
        Args:
            token_mint (str): Token mint address
            
        Returns:
            list: Price history
        """
        price_history = []
        
        # Try to get price history from Vybe API
        try:
            # Sample resolution: 1h, 1d, 1w
            resolution = "1d"
            
            # Calculate timestamps (last 30 days)
            now = datetime.now()
            end_time = int(now.timestamp())
            start_time = int((now.timestamp() - (30 * 24 * 60 * 60)))  # 30 days ago
            
            ohlc_data = vybe_collector.get_token_ohlc(token_mint, resolution, start_time, end_time)
            
            if ohlc_data:
                price_history = ohlc_data
        except Exception as e:
            logger.error(f"Error getting price history: {str(e)}")
        
        return price_history
    
    def _analyze_holders(self, token_data):
        """
        Analyze token holders
        
        Args:
            token_data (dict): Token data
            
        Returns:
            dict: Holder analysis
        """
        holder_analysis = {
            "total_holders": 0,
            "top_10_concentration": 0,
            "creator_concentration": 0,
            "team_concentration": 0,
            "top_holders": []
        }
        
        # Get top holders
        top_holders = token_data.get('top_holders', [])
        
        if not top_holders:
            return holder_analysis
        
        # Set total holders
        holder_analysis['total_holders'] = token_data.get('totalHolders', len(top_holders))
        
        # Calculate top 10 concentration
        top_10 = top_holders[:10] if len(top_holders) >= 10 else top_holders
        top_10_pct = sum(holder.get('pct', 0) for holder in top_10)
        holder_analysis['top_10_concentration'] = top_10_pct
        
        # Identify creator and team wallets
        creator_address = token_data.get('creator')
        creator_pct = 0
        team_pct = 0
        
        for holder in top_holders:
            address = holder.get('address')
            if address == creator_address:
                creator_pct += holder.get('pct', 0)
            
            # Check if insider
            if holder.get('insider', False):
                team_pct += holder.get('pct', 0)
        
        holder_analysis['creator_concentration'] = creator_pct
        holder_analysis['team_concentration'] = team_pct
        
        # Add simplified top holder data
        simplified_holders = []
        for holder in top_holders[:20]:  # Limit to top 20
            simplified_holder = {
                "address": holder.get('address'),
                "percentage": holder.get('pct', 0),
                "amount": holder.get('uiAmount', 0),
                "is_insider": holder.get('insider', False)
            }
            simplified_holders.append(simplified_holder)
        
        holder_analysis['top_holders'] = simplified_holders
        
        return holder_analysis
    
    def _analyze_rugcheck_data(self, token_data):
        """
        Analyze RugCheck data
        
        Args:
            token_data (dict): Token data
            
        Returns:
            dict: RugCheck analysis
        """
        rugcheck_analysis = {
            "risk_score": 0,
            "risk_factors": [],
            "insider_detection": False,
            "rugged": False
        }
        
        # Extract risk score
        risk_score = token_data.get('risk_score')
        if risk_score is not None:
            rugcheck_analysis['risk_score'] = risk_score
        
        # Extract risk factors
        risk_factors = token_data.get('risk_factors', [])
        simplified_factors = []
        
        for factor in risk_factors:
            if isinstance(factor, dict):
                simplified_factor = {
                    "name": factor.get('name', ''),
                    "description": factor.get('description', ''),
                    "level": factor.get('level', ''),
                    "score": factor.get('score', 0)
                }
                simplified_factors.append(simplified_factor)
            else:
                simplified_factors.append({"description": str(factor)})
        
        rugcheck_analysis['risk_factors'] = simplified_factors
        
        # Check for insider detection
        insider_networks = token_data.get('insider_networks', [])
        rugcheck_analysis['insider_detection'] = len(insider_networks) > 0
        
        # Check if already rugged
        rugged = token_data.get('rugged', False)
        rugcheck_analysis['rugged'] = rugged
        
        return rugcheck_analysis
    
    def _calculate_rugpull_risk(self, analysis_data):
        """
        Calculate rugpull risk factors and score
        
        Args:
            analysis_data (dict): Analysis data
            
        Returns:
            tuple: (risk_factors, risk_score)
        """
        risk_factors = []
        risk_score = 0
        
        # 1. Check mint authority
        token_data = analysis_data.get('token_data', {})
        if token_data.get('mint_authority'):
            risk_factors.append("Mint authority is still active, allowing unlimited token minting")
            risk_score += 20
        
        # 2. Check freeze authority
        if token_data.get('freeze_authority'):
            risk_factors.append("Freeze authority is active, allowing creator to freeze token accounts")
            risk_score += 15
        
        # 3. Check liquidity lock
        liquidity_data = analysis_data.get('liquidity_data', {})
        locked_percentage = liquidity_data.get('locked_percentage', 0)
        
        if locked_percentage < 10:
            risk_factors.append("Less than 10% of liquidity is locked")
            risk_score += 30
        elif locked_percentage < 50:
            risk_factors.append("Less than 50% of liquidity is locked")
            risk_score += 20
        elif locked_percentage < 80:
            risk_factors.append("Less than 80% of liquidity is locked")
            risk_score += 10
        
        # 4. Check lock expiry
        lock_expiry = liquidity_data.get('lock_expiry')
        if lock_expiry:
            try:
                expiry_date = datetime.fromisoformat(lock_expiry)
                now = datetime.now()
                
                # Check if expiry is less than 30 days away
                days_until_expiry = (expiry_date - now).days
                
                if days_until_expiry < 0:
                    risk_factors.append("Liquidity lock has already expired")
                    risk_score += 30
                elif days_until_expiry < 7:
                    risk_factors.append(f"Liquidity lock expires in {days_until_expiry} days")
                    risk_score += 25
                elif days_until_expiry < 30:
                    risk_factors.append(f"Liquidity lock expires in {days_until_expiry} days")
                    risk_score += 15
                elif days_until_expiry < 90:
                    risk_factors.append(f"Liquidity lock expires in {days_until_expiry} days")
                    risk_score += 5
            except:
                pass
        else:
            risk_factors.append("No liquidity lock found")
            risk_score += 25
        
        # 5. Check holder concentration
        holder_analysis = analysis_data.get('holder_analysis', {})
        top_10_concentration = holder_analysis.get('top_10_concentration', 0)
        team_concentration = holder_analysis.get('team_concentration', 0)
        
        if team_concentration > 50:
            risk_factors.append(f"Team controls {team_concentration:.1f}% of token supply")
            risk_score += 25
        elif team_concentration > 30:
            risk_factors.append(f"Team controls {team_concentration:.1f}% of token supply")
            risk_score += 15
        
        if top_10_concentration > 80:
            risk_factors.append(f"Top 10 holders control {top_10_concentration:.1f}% of token supply")
            risk_score += 20
        elif top_10_concentration > 60:
            risk_factors.append(f"Top 10 holders control {top_10_concentration:.1f}% of token supply")
            risk_score += 10
        
        # 6. Check insider detection
        rugcheck_analysis = analysis_data.get('rugcheck_analysis', {})
        if rugcheck_analysis.get('insider_detection', False):
            risk_factors.append("Insider networks detected by RugCheck")
            risk_score += 20
        
        # 7. Check existing RugCheck risk factors
        for factor in rugcheck_analysis.get('risk_factors', []):
            if isinstance(factor, dict):
                factor_name = factor.get('name', '')
                factor_level = factor.get('level', '')
                factor_score = factor.get('score', 0)
                
                # Only include high-risk factors we haven't already covered
                if factor_level in ['high', 'very_high'] and factor_score >= 50:
                    risk_factors.append(f"RugCheck risk: {factor_name}")
                    risk_score += 5  # Add a smaller score since we're already factoring in RugCheck's overall score
        
        # 8. Check if already rugged
        if rugcheck_analysis.get('rugged', False):
            risk_factors.append("Token has already been rugged according to RugCheck")
            risk_score = 100  # Automatic maximum score
        
        # 9. Factor in RugCheck's risk score
        rugcheck_risk_score = rugcheck_analysis.get('risk_score', 0)
        if rugcheck_risk_score > 0:
            # Weight RugCheck's score at 30% of our overall score
            risk_score = (risk_score * 0.7) + (rugcheck_risk_score * 0.3)
        
        # Cap risk score at 100
        risk_score = min(100, risk_score)
        
        return risk_factors, risk_score

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    # Create analyzer
    detector = RugpullDetector()
    
    # Test token mint (example, should be replaced with a real token)
    token_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    # Run analysis
    result = detector.analyze(token_mint)
    
    # Print result
    print(json.dumps(result, indent=2))