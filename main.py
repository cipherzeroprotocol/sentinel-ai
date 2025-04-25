#!/usr/bin/env python3
"""
Sentinel AI: Solana Security Analysis Platform

Main entry point for Sentinel AI platform. This script provides a command-line
interface to run various security analyses on Solana blockchain data.

Usage:
    python main.py --help
    python main.py ico --token <token_address> [--days <days>]
    python main.py rugpull --token <token_address>
    python main.py money-laundering --address <wallet_address> [--days <days>]
    python main.py mixer --address <wallet_address> [--days <days>]
    python main.py dusting --address <wallet_address> [--days <days>]
    python main.py wallet --address <wallet_address> [--days <days>]
    python main.py transaction --address <wallet_address> [--days <days>]
    python main.py batch --type <analysis_type> [--limit <limit>]
    python main.py web [--host <host>] [--port <port>]
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Add the parent directory (containing the sentinel package) to the Python path
# This allows absolute imports from the 'sentinel' package to work correctly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set up environment variables from a .env file if available
try:
    from dotenv import load_dotenv
    env_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
except ImportError:
    print("python-dotenv not installed. Skipping .env loading.")

# Now try the imports
try:
    # Use absolute imports from the 'sentinel' package
    from sentinel.analysis.bounties.dusting_analyzer import DustingAnalyzer
    from sentinel.analysis.bounties.ico_analysis import ICOAnalyzer
    from sentinel.analysis.bounties.mixer_detector import MixerDetector
    from sentinel.analysis.bounties.rugpull_detector import RugpullDetector
    from sentinel.analysis.shared.transaction_analyzer import TransactionAnalyzer
    from sentinel.analysis.shared.wallet_profiler import WalletProfiler
    from sentinel.data.storage.address_db import AddressDatabase  
    from sentinel.analysis.bounties.money_laundering import MoneyLaunderingAnalyzer
except ImportError as e:
    print(f"Error importing Sentinel modules: {e}")
    print("This might be due to import paths. Try running from the project root.")
    print(f"Current Python path: {sys.path}")
    sys.exit(1)

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f"sentinel_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize database
db_path = os.environ.get('DB_PATH', os.path.join(PROJECT_ROOT, 'sentinel', 'sentinel_data.db')) # Make db_path relative to project root
db = AddressDatabase(db_path) # Use correct class name

# Initialize analyzers (globally, initialized when needed)
ico_analyzer = None
laundering_detector = None
rugpull_detector = None
mixer_detector = None
dusting_analyzer = None
transaction_analyzer = None
wallet_profiler = None

def init_analyzers():
    """Initialize all analysis modules"""
    global ico_analyzer, laundering_detector, rugpull_detector, mixer_detector, dusting_analyzer, transaction_analyzer, wallet_profiler

    # Avoid re-initialization
    if all([ico_analyzer, laundering_detector, rugpull_detector, mixer_detector, dusting_analyzer, transaction_analyzer, wallet_profiler]):
        return

    logger.info("Initializing analysis modules...")

    # Initialize AI analyzer first (all other analyzers depend on it)
    ai_analyzer = None
    try:
        from sentinel.ai.utils.ai_analyzer import AIAnalyzer
        ai_analyzer = AIAnalyzer()
        logger.info("AI Analyzer initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize AI Analyzer: {e}. Some analyses may be limited.")

    # Correctly initialize each analyzer based on its requirements
    ico_analyzer = ICOAnalyzer()  # No parameters
    laundering_detector = MoneyLaunderingAnalyzer()  # No parameters
    rugpull_detector = RugpullDetector()  # No parameters - doesn't accept DB_PATH
    mixer_detector = MixerDetector()  # No parameters
    dusting_analyzer = DustingAnalyzer(db_path)  # Pass db_path, AIAnalyzer is internal
    transaction_analyzer = TransactionAnalyzer(db_path)  # Pass db_path if required
    wallet_profiler = WalletProfiler(db_path)  # Pass db_path if required

def analyze_ico(args):
    """Run ICO analysis"""
    if not ico_analyzer:
        init_analyzers()
    
    logger.info(f"Running ICO analysis for token {args.token}")
    
    try:
        # Perform analysis - Assuming analyze method exists
        result = ico_analyzer.analyze(args.token) # Changed method signature
        
        # Generate report - Assuming generate_ico_report method exists
        # report_path = ico_analyzer.generate_ico_report(analysis_result=result)
        report_path = None # Placeholder if report generation is elsewhere or not implemented
        
        logger.info(f"ICO analysis completed for {args.token}")
        if report_path:
            logger.info(f"Report generated: {report_path}")
        
        # Output summary to console
        token_data = result.get('token_data', {})
        creator_data = result.get('creator_data', {})
        funding_flow = result.get('funding_flow', {})
        patterns = result.get('patterns', {})
        
        print(f"\n=== ICO Analysis for {token_data.get('symbol', 'Unknown Token')} ===")
        print(f"Token: {token_data.get('symbol', 'Unknown')} ({token_data.get('name', 'Unknown')})")
        print(f"Mint Address: {result.get('token_mint')}")
        # Assuming risk score/level might come from AI analysis or needs calculation
        # print(f"Risk Score: {result.get('risk_score')}/100")
        # print(f"Risk Level: {result.get('risk_level')}")
        print(f"Detected Patterns: {len(patterns.get('detected_patterns', [])) if patterns else 0}")
        # print(f"Team Holdings: {result.get('team_analysis', {}).get('total_team_holdings_pct', 0):.1f}%") # Needs team analysis logic
        print(f"Total Raised (Estimated): ${funding_flow.get('total_raised', 0):,.2f}")
        print(f"Investor Count: {funding_flow.get('investor_count', 0)}")
        if report_path:
            print(f"Report Path: {report_path}")
        
        # Return the results
        return result, report_path
    
    except Exception as e:
        logger.error(f"Error in ICO analysis: {e}")
        print(f"Error: {e}")
        return None, None

def analyze_rugpull(args):
    """Run rugpull detection"""
    if not rugpull_detector:
        init_analyzers()
    
    logger.info(f"Running rugpull detection for token {args.token}")
    
    try:
        # Perform analysis
        result = rugpull_detector.analyze(args.token) # Changed method name based on rugpull_detector.py context
        
        # Generate report - Assuming generate_rugpull_report method exists
        # report_path = rugpull_detector.generate_rugpull_report(detection_result=result)
        report_path = None # Placeholder
        
        logger.info(f"Rugpull detection completed for {args.token}")
        if report_path:
            logger.info(f"Report generated: {report_path}")
        
        # Output summary to console
        token_data = result.get('token_data', {})
        holder_analysis = result.get('holder_analysis', {})
        rugcheck_analysis = result.get('rugcheck_analysis', {})

        print(f"\n=== Rugpull Analysis for {token_data.get('symbol', 'Unknown Token')} ===")
        print(f"Token: {token_data.get('symbol', 'Unknown')} ({token_data.get('name', 'Unknown')})")
        print(f"Mint Address: {result.get('token_mint')}")
        # print(f"Is Rugpull: {'Yes' if result.get('is_rugpull') else 'No'}") # Needs final determination logic
        print(f"Calculated Risk Score: {result.get('risk_score', 0):.1f}/100")
        # Determine risk level based on score
        risk_score = result.get('risk_score', 0)
        risk_level = "low"
        if risk_score >= 80: risk_level = "very_high"
        elif risk_score >= 60: risk_level = "high"
        elif risk_score >= 30: risk_level = "medium"
        print(f"Risk Level: {risk_level}")
        print(f"Risk Factors: {len(result.get('risk_factors', []))}")
        print(f"Top 10 Holder Concentration: {holder_analysis.get('top_10_concentration', 0):.1f}%")
        print(f"Liquidity Locked: {result.get('liquidity_data', {}).get('locked_percentage', 0):.1f}%")
        print(f"Rugcheck Score: {rugcheck_analysis.get('risk_score', 0)}")
        if report_path:
            print(f"Report Path: {report_path}")
        
        # Return the results
        return result, report_path
    
    except Exception as e:
        logger.error(f"Error in rugpull detection: {e}")
        print(f"Error: {e}")
        return None, None

def analyze_money_laundering(args):
    """Run money laundering detection"""
    if not laundering_detector:
        init_analyzers()
    
    logger.info(f"Running money laundering detection for address {args.address}")
    
    try:
        # Perform analysis - Pass 'days' argument now
        result = laundering_detector.analyze(args.address, days=args.days) # Pass days
        
        # Generate report - Assuming generate_ml_report method exists
        # report_path = laundering_detector.generate_ml_report(detection_result=result)
        report_path = None # Placeholder
        
        logger.info(f"Money laundering detection completed for {args.address}")
        if report_path:
            logger.info(f"Report generated: {report_path}")
        
        # Output summary to console
        print(f"\n=== Money Laundering Analysis for {args.address} ===")
        print(f"Address: {args.address}")
        # print(f"Is Money Laundering: {'Yes' if result.get('is_money_laundering') else 'No'}") # Needs final determination
        print(f"Risk Score: {result.get('risk_score', 0):.1f}/100")
        # Determine risk level based on score
        risk_score = result.get('risk_score', 0)
        risk_level = "low"
        if risk_score >= 70: risk_level = "high"
        elif risk_score >= 40: risk_level = "medium"
        print(f"Risk Level: {risk_level}") # Updated risk level calculation
        print(f"Detected Patterns: {len(result.get('flow_patterns', []))}") # Use flow_patterns
        print(f"Mixer Interaction: {'Yes' if any(cp.get('is_mixer') for cp in result.get('counterparties', [])) else 'No'}") # Check counterparties
        # print(f"Wallet Type: {result.get('wallet_classification', 'unknown')}") # Needs wallet classification logic
        # print(f"Laundering Routes: {len(result.get('money_laundering_routes', []))}") # Needs route detection logic
        if report_path:
            print(f"Report Path: {report_path}")
        
        # Return the results
        return result, report_path
    
    except Exception as e:
        logger.error(f"Error in money laundering detection: {e}")
        print(f"Error: {e}")
        return None, None

def analyze_mixer(args):
    """Run mixer detection"""
    if not mixer_detector:
        init_analyzers()
    
    logger.info(f"Running mixer detection for address {args.address}")
    
    try:
        # Perform analysis
        result = mixer_detector.analyze(args.address, days=args.days) # Added days argument
        
        # Generate report - Assuming generate_mixer_report method exists
        # report_path = mixer_detector.generate_mixer_report(analysis_result=result)
        report_path = None # Placeholder
        
        logger.info(f"Mixer detection completed for {args.address}")
        if report_path:
            logger.info(f"Report generated: {report_path}")
        
        # Output summary to console
        print(f"\n=== Mixer Analysis for {args.address} ===")
        print(f"Address: {args.address}")
        print(f"Is Known Mixer: {'Yes' if result.get('is_known_mixer') else 'No'}")
        print(f"Confidence Score: {result.get('confidence_score', 0):.2f}")
        print(f"Detected Characteristics: {len(result.get('mixer_characteristics', []))}")
        print(f"Transaction Count (Analyzed): {len(result.get('transactions', []))}")
        print(f"Unique Users (Estimated): {result.get('user_analysis', {}).get('unique_users', 0)}")
        if report_path:
            print(f"Report Path: {report_path}")
        
        # Return the results
        return result, report_path
    
    except Exception as e:
        logger.error(f"Error in mixer detection: {e}")
        print(f"Error: {e}")
        return None, None

def analyze_dusting(args):
    """Run dusting analysis"""
    if not dusting_analyzer:
        init_analyzers()
    
    logger.info(f"Running dusting analysis for address {args.address}")
    
    try:
        # Perform analysis
        result = dusting_analyzer.analyze_address(args.address, days=args.days)
        
        # Generate report
        report_path = dusting_analyzer.generate_dusting_report(analysis_result=result)
        
        logger.info(f"Dusting analysis completed for {args.address}")
        logger.info(f"Report generated: {report_path}")
        
        # Output summary to console
        print(f"\n=== Address Poisoning Analysis for {args.address} ===")
        print(f"Address: {args.address}")
        print(f"Risk Level: {result.get('risk_assessment', {}).get('risk_level', 'unknown')}")
        print(f"Risk Score: {result.get('risk_assessment', {}).get('risk_score', 0)}/100")
        print(f"Poisoning Attempts: {len(result.get('poisoning_attempts', []))}")
        print(f"Dusting Campaigns: {len(result.get('dusting_campaigns', []))}")
        print(f"Report Path: {report_path}")
        
        # Return the results
        return result, report_path
    
    except Exception as e:
        logger.error(f"Error in dusting analysis: {e}")
        print(f"Error: {e}")
        return None, None

def analyze_wallet(args):
    """Run wallet profiling"""
    if not wallet_profiler:
        init_analyzers()
    
    logger.info(f"Running wallet profiling for address {args.address}")
    
    try:
        # Perform analysis
        result = wallet_profiler.profile_wallet(args.address, days=args.days)
        
        logger.info(f"Wallet profiling completed for {args.address}")
        
        # Output summary to console
        print(f"\n=== Wallet Profile for {args.address} ===")
        print(f"Address: {args.address}")
        print(f"Wallet Type: {result.get('classification', {}).get('primary_type', 'unknown')}")
        print(f"Risk Score: {result.get('risk_assessment', {}).get('risk_score', 0)}/100")
        print(f"Risk Level: {result.get('risk_assessment', {}).get('risk_level', 'unknown')}")
        print(f"Transaction Count: {result.get('features', {}).get('total_tx_count', 0)}")
        print(f"Total Volume: ${result.get('features', {}).get('total_volume_usd', 0):,.2f}")
        
        # Return the results
        return result, None
    
    except Exception as e:
        logger.error(f"Error in wallet profiling: {e}")
        print(f"Error: {e}")
        return None, None

def analyze_transaction(args):
    """Run transaction analysis"""
    if not transaction_analyzer:
        init_analyzers()
    
    logger.info(f"Running transaction analysis for address {args.address}")
    
    try:
        # Perform analysis
        result = transaction_analyzer.analyze_transactions(address=args.address, days=args.days)
        
        logger.info(f"Transaction analysis completed for {args.address}")
        
        # Output summary to console
        print(f"\n=== Transaction Analysis for {args.address} ===")
        print(f"Address: {args.address}")
        print(f"Transaction Count: {result.get('transaction_count', 0)}")
        print(f"Suspicion Score: {result.get('suspicion_score', 0)}/100")
        print(f"Patterns Detected: {len(result.get('patterns', {}))}")
        print(f"Cross-Chain Transfers: {len(result.get('cross_chain_transfers', []))}")
        print(f"Risk Score: {result.get('risk_assessment', {}).get('overall_risk_score', 0)}/100")
        
        # Return the results
        return result, None
    
    except Exception as e:
        logger.error(f"Error in transaction analysis: {e}")
        print(f"Error: {e}")
        return None, None

def run_batch_analysis(args):
    """Run batch analysis"""
    if not ico_analyzer or not rugpull_detector or not laundering_detector or not mixer_detector: # Added mixer_detector check
        init_analyzers()
    
    try:
        results = []
        
        analysis_type = args.type.lower()
        limit = args.limit
        
        if analysis_type == "ico":
            print(f"Running batch ICO analysis (limit: {limit})...")
            # Assuming batch_analyze_recent_launches exists
            # batch_results = ico_analyzer.batch_analyze_recent_launches(days=30, max_tokens=limit)
            print("Batch ICO analysis not fully implemented yet.")
            batch_results = []
            results = batch_results
        
        elif analysis_type == "rugpull":
            print(f"Running batch rugpull detection (limit: {limit})...")
            # Assuming batch_analyze_recent_tokens exists
            # batch_results = rugpull_detector.batch_analyze_recent_tokens(days=30, max_tokens=limit)
            print("Batch rugpull analysis not fully implemented yet.")
            batch_results = []
            results = batch_results
        
        elif analysis_type == "money-laundering" or analysis_type == "laundering":
            print(f"Running batch money laundering detection (limit: {limit})...")
            # Assuming batch_analyze_high_risk_addresses exists
            # batch_results = laundering_detector.batch_analyze_high_risk_addresses(max_addresses=limit)
            print("Batch money laundering analysis not fully implemented yet.")
            batch_results = []
            results = batch_results
        
        elif analysis_type == "mixer":
            print(f"Running batch mixer detection (limit: {limit})...")
            # Scan for potential mixers - Assuming scan_for_mixers exists
            # potential_mixers = mixer_detector.scan_for_mixers(min_transaction_count=500, days=30)
            print("Batch mixer scanning not fully implemented yet.")
            potential_mixers = []
            # Analyze top candidates
            for i, mixer in enumerate(potential_mixers[:limit]):
                address = mixer.get("address")
                if address:
                    print(f"Analyzing potential mixer {i+1}/{min(limit, len(potential_mixers))}: {address}")
                    result = mixer_detector.analyze(address)
                    # report_path = mixer_detector.generate_mixer_report(analysis_result=result) # Report generation placeholder
                    results.append(result)
        
        else:
            print(f"Invalid analysis type: {analysis_type}")
            print("Available types: ico, rugpull, money-laundering, mixer")
            return None
        
        # Print batch results summary
        print(f"\n=== Batch {analysis_type.upper()} Analysis Results ===")
        print(f"Analyzed {len(results)} entities\n")
        
        for i, result in enumerate(results):
            if analysis_type == "ico":
                print(f"{i+1}. {result.get('symbol', 'Unknown')}: Risk {result.get('risk_score', 0):.1f}/100, Level: {result.get('risk_level', 'unknown')}")
            
            elif analysis_type == "rugpull":
                print(f"{i+1}. {result.get('symbol', 'Unknown')}: {'Rugpull' if result.get('is_rugpull') else 'Not Rugpull'}, Score: {result.get('rugpull_score', 0):.1f}/100")
            
            elif analysis_type == "money-laundering" or analysis_type == "laundering":
                print(f"{i+1}. {result.get('address', 'Unknown')}: {'Money Laundering' if result.get('is_money_laundering') else 'Not Money Laundering'}, Score: {result.get('risk_score', 0):.1f}/100")
            
            elif analysis_type == "mixer":
                print(f"{i+1}. {result.get('address', 'Unknown')}: {'Known Mixer' if result.get('is_known_mixer') else 'Potential Mixer'}, Score: {result.get('confidence_score', 0):.2f}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        print(f"Error: {e}")
        return None

def run_web_server(args):
    """Run the web interface"""
    try:
        # Ensure analyzers are ready if web server uses them directly
        init_analyzers()
        # NOTE: This import happens conditionally, ensure sentinel/web/app.py exists
        from sentinel.web.app import app # Corrected import path
        
        # Let app.py handle its own analyzer initialization
        # Remove any analyzer passing to app that might conflict

        host = args.host
        port = args.port

        print(f"Starting Sentinel AI web interface on http://{host}:{port}")
        print("Press Ctrl+C to stop the server")

        app.run(debug=True, host=host, port=port)

    except ImportError as e:
        logger.error(f"Import error starting web server: {e}")
        print(f"Import Error: {e}")
        print("Please ensure all dependencies are installed and the project structure is correct.")
        return False
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        print(f"Error: {e}")
        print("Make sure you have Flask installed: pip install Flask flask-cors")
        return False

    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Sentinel AI: Solana Security Analysis Platform')
    subparsers = parser.add_subparsers(dest='command', help='Analysis command')
    
    # ICO analysis
    ico_parser = subparsers.add_parser('ico', help='Analyze ICO token')
    ico_parser.add_argument('--token', required=True, help='Token mint address')
    ico_parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    
    # Rugpull detection
    rugpull_parser = subparsers.add_parser('rugpull', help='Detect rugpull')
    rugpull_parser.add_argument('--token', required=True, help='Token mint address')
    
    # Money laundering detection
    ml_parser = subparsers.add_parser('money-laundering', help='Detect money laundering')
    ml_parser.add_argument('--address', required=True, help='Wallet address')
    ml_parser.add_argument('--days', type=int, default=90, help='Number of days to analyze')
    
    # Mixer detection
    mixer_parser = subparsers.add_parser('mixer', help='Detect mixer')
    mixer_parser.add_argument('--address', required=True, help='Wallet address')
    mixer_parser.add_argument('--days', type=int, default=30, help='Number of days to analyze') # Added days argument
    
    # Dusting analysis
    dusting_parser = subparsers.add_parser('dusting', help='Analyze dusting attacks')
    dusting_parser.add_argument('--address', required=True, help='Wallet address')
    dusting_parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    
    # Wallet profiling
    wallet_parser = subparsers.add_parser('wallet', help='Profile wallet')
    wallet_parser.add_argument('--address', required=True, help='Wallet address')
    wallet_parser.add_argument('--days', type=int, default=90, help='Number of days to analyze')
    
    # Transaction analysis
    tx_parser = subparsers.add_parser('transaction', help='Analyze transactions')
    tx_parser.add_argument('--address', required=True, help='Wallet address')
    tx_parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    
    # Batch analysis
    batch_parser = subparsers.add_parser('batch', help='Run batch analysis')
    batch_parser.add_argument('--type', required=True, choices=['ico', 'rugpull', 'money-laundering', 'mixer'], help='Analysis type')
    batch_parser.add_argument('--limit', type=int, default=10, help='Maximum number of entities to analyze')
    
    # Web interface
    web_parser = subparsers.add_parser('web', help='Run web interface')
    web_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    web_parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command provided, show help
    if not args.command:
        parser.print_help()
        return
    
    # Initialize analyzers only when needed
    if args.command in ['ico', 'rugpull', 'money-laundering', 'mixer', 'dusting', 'wallet', 'transaction', 'batch']:
        init_analyzers()
    
    # Run appropriate command
    if args.command == 'ico':
        analyze_ico(args)
    elif args.command == 'rugpull':
        analyze_rugpull(args)
    elif args.command == 'money-laundering':
        analyze_money_laundering(args)
    elif args.command == 'mixer':
        analyze_mixer(args)
    elif args.command == 'dusting':
        analyze_dusting(args)
    elif args.command == 'wallet':
        analyze_wallet(args)
    elif args.command == 'transaction':
        analyze_transaction(args)
    elif args.command == 'batch':
        run_batch_analysis(args)
    elif args.command == 'web':
        run_web_server(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()