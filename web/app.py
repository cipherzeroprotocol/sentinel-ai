import os
import sys
import json
import logging
from datetime import datetime
import mimetypes # Import mimetypes

from flask import Flask, request, jsonify, send_from_directory, abort # Added abort
from flask_cors import CORS

# Add the parent directory of the web module to Python path
# This allows absolute imports from the 'sentinel' package
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Use absolute imports from the sentinel package
try:
    from sentinel.analysis.bounties.dusting_analyzer import DustingAnalyzer
    from sentinel.analysis.bounties.ico_analysis import ICOAnalyzer
    from sentinel.analysis.bounties.mixer_detector import MixerDetector
    from sentinel.analysis.bounties.rugpull_detector import RugpullDetector
    from sentinel.analysis.shared.transaction_analyzer import TransactionAnalyzer
    from sentinel.analysis.shared.wallet_profiler import WalletProfiler
    from sentinel.data.storage.report_store import ReportStore # Keep if used for metadata
    from sentinel.data.storage.address_db import AddressDatabase
    from sentinel.reports.generator import ReportGenerator, REPORTS_DIR as GENERATED_REPORTS_DIR
    from sentinel.analysis.bounties.money_laundering import MoneyLaunderingAnalyzer
    # Import AI Analyzer
    from sentinel.ai.utils.ai_analyzer import AIAnalyzer
    from sentinel.data.config import (
        CORS_ORIGINS, API_HOST, API_PORT, API_DEBUG, 
        DB_PATH, REPORTS_DIR as GENERATED_REPORTS_DIR
    )
except ImportError as e:
    print(f"Error importing Sentinel modules: {e}. Ensure PYTHONPATH is set correctly or run from the project root.")
    print(f"Current Python path: {sys.path}")
    sys.exit(1)


# Initialize Flask app
app = Flask(__name__)

# Configure CORS with settings from config
CORS(app, resources={
    r"/api/*": {"origins": CORS_ORIGINS, "supports_credentials": True},
    r"/generated_reports/*": {"origins": CORS_ORIGINS}
})

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Component Initializations ---
# Define DB path (consider making this configurable)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'sentinel_data.db')
logger.info(f"Using database at: {DB_PATH}")

# Ensure database directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Initialize Database and Report Store/Generator
try:
    address_db = AddressDatabase(DB_PATH)
    report_store = ReportStore(DB_PATH) # Keep if storing metadata
    report_generator = ReportGenerator() # Class instance
    # Ensure the report output directory exists
    if not os.path.exists(GENERATED_REPORTS_DIR):
        os.makedirs(GENERATED_REPORTS_DIR)
        logger.info(f"Created reports output directory: {GENERATED_REPORTS_DIR}")
    else:
        logger.info(f"Reports output directory: {GENERATED_REPORTS_DIR}")

    # Initialize AI Analyzer first
    ai_analyzer = None
    try:
        ai_analyzer = AIAnalyzer()
        logger.info("AI Analyzer initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize AI Analyzer: {e}. Some analyses may be limited.")

    # Initialize analyzers with appropriate arguments based on their actual implementation
    # Only pass parameters that each class accepts
    ico_analyzer = ICOAnalyzer()  # No parameters
    money_laundering_detector = MoneyLaunderingAnalyzer()  # No parameters 
    rugpull_detector = RugpullDetector()  # No parameters - doesn't accept DB_PATH
    mixer_detector = MixerDetector()  # No parameters
    dusting_analyzer = DustingAnalyzer(DB_PATH)  # Pass DB_PATH if required
    transaction_analyzer = TransactionAnalyzer(DB_PATH)  # Pass DB_PATH if required
    wallet_profiler = WalletProfiler(DB_PATH)  # Pass DB_PATH if required

    ANALYZERS_READY = True
    logger.info("All analysis modules initialized successfully.")

except Exception as e:
    logger.exception(f"FATAL: Failed to initialize core components: {e}")
    ANALYZERS_READY = False
    # Optionally exit or prevent app from starting fully
    # sys.exit(1)


# --- API Endpoints ---

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint to analyze an address or token"""
    if not ANALYZERS_READY:
         logger.error("Analysis request received but analyzers are not ready.")
         return jsonify({'success': False, 'error': 'Server initialization failed. Analyzers not available.'}), 503

    data = request.json
    address = data.get('address')
    token = data.get('token')
    analysis_type = data.get('type', 'all') # Default to 'all' if not specified
    days = int(data.get('days', 30))

    if not address and not token:
        return jsonify({'success': False, 'error': 'Address or Token is required'}), 400

    # Determine primary target and type for reporting
    target = address if address else token
    target_type = 'address' if address else 'token'
    logger.info(f"Received analysis request: type={analysis_type}, target={target}, target_type={target_type}, days={days}")

    try:
        results = {}
        analysis_performed_count = 0 # Count how many analyses ran

        # --- Run analyses based on type ---
        # Use 'report_type' variable consistent with generator function names
        if analysis_type == 'ico' or analysis_type == 'all':
            report_type = 'ico'
            if token and ico_analyzer:
                logger.info(f"Running ICO analysis for token: {token}")
                # Fix: Use the correct analyze method with token_mint keyword argument
                results[report_type] = ico_analyzer.analyze(token_mint=token) # Corrected method call
                analysis_performed_count += 1
            elif analysis_type == report_type and not token:
                 logger.warning(f"ICO analysis requested but no token provided.")

        if analysis_type == 'money_laundering' or analysis_type == 'all':
            report_type = 'money_laundering'
            if address and money_laundering_detector:
                logger.info(f"Running Money Laundering analysis for address: {address}, days: {days}")
                # Fix: Use the correct analyze method, which only takes address
                results[report_type] = money_laundering_detector.analyze(address) # Corrected method call (removed days)
                analysis_performed_count += 1
            elif analysis_type == report_type and not address:
                 logger.warning(f"Money Laundering analysis requested but no address provided.")

        if analysis_type == 'rugpull' or analysis_type == 'all':
            report_type = 'rugpull'
            if token and rugpull_detector:
                logger.info(f"Running Rugpull analysis for token: {token}")
                # Fix: Ensure we're using the correct method name
                results[report_type] = rugpull_detector.analyze(token)
                analysis_performed_count += 1
            elif analysis_type == report_type and not token:
                 logger.warning(f"Rugpull analysis requested but no token provided.")

        if analysis_type == 'mixer' or analysis_type == 'all':
            report_type = 'mixer'
            if address and mixer_detector:
                logger.info(f"Running Mixer analysis for address: {address}, days: {days}")
                # Fix: Use the correct method name for mixer_detector
                results[report_type] = mixer_detector.analyze(address, days=days)
                analysis_performed_count += 1
            elif analysis_type == report_type and not address:
                 logger.warning(f"Mixer analysis requested but no address provided.")

        if analysis_type == 'dusting' or analysis_type == 'all':
            report_type = 'dusting'
            if address and dusting_analyzer:
                logger.info(f"Running Dusting analysis for address: {address}, days: {days}")
                results[report_type] = dusting_analyzer.analyze_address(address, days=days)
                analysis_performed_count += 1
            elif analysis_type == report_type and not address:
                 logger.warning(f"Dusting analysis requested but no address provided.")

        if analysis_type == 'wallet' or analysis_type == 'all':
             report_type = 'wallet' # Define report type if generating wallet report
             if address and wallet_profiler:
                 logger.info(f"Running Wallet analysis for address: {address}, days: {days}")
                 results[report_type] = wallet_profiler.profile_wallet(address, days=days)
                 analysis_performed_count += 1
             elif analysis_type == report_type and not address:
                 logger.warning(f"Wallet analysis requested but no address provided.")

        if analysis_type == 'transaction' or analysis_type == 'all':
             report_type = 'transaction' # Define report type if generating tx report
             if address and transaction_analyzer:
                 logger.info(f"Running Transaction analysis for address: {address}, days: {days}")
                 # Assuming analyze_transactions returns data suitable for results dict
                 results[report_type] = transaction_analyzer.analyze_transactions(address=address, days=days)
                 analysis_performed_count += 1
             elif analysis_type == report_type and not address:
                 logger.warning(f"Transaction analysis requested but no address provided.")

        # --- Generate Report ---
        report_path = None
        # Generate report only if a specific type was requested (not 'all') and analysis ran
        if analysis_type != 'all' and analysis_performed_count > 0:
            try:
                logger.info(f"Generating {analysis_type} report for target: {target}")
                # Pass the specific result block for the requested analysis type
                report_data_for_type = results.get(analysis_type)
                if report_data_for_type:
                     # Call the class method, passing target and the relevant data block
                     report_path = report_generator.generate_report(target, report_data_for_type, analysis_type)
                     if report_path:
                         logger.info(f"Report generated: {report_path} for target: {target}")
                         # Optionally store metadata if needed
                         # report_store.save_report(os.path.basename(report_path).replace('.md',''), target, analysis_type, report_path)
                     else:
                         logger.error(f"Report generation function returned None for {analysis_type} report for {target}.")
                else:
                     logger.warning(f"No result data found for analysis type '{analysis_type}' to generate report.")
            except Exception as report_e:
                logger.exception(f"Failed to generate report for {target} (type: {analysis_type}): {report_e}")
                # Don't let report generation failure stop the API response if analysis succeeded

        if analysis_performed_count == 0:
             # If 'all' was requested but nothing matched address/token, or specific type failed prerequisite
             error_message = f"No suitable analysis could be performed for the requested type ('{analysis_type}') with the provided target ('{target}'). Check address/token validity and analysis type requirements."
             logger.warning(error_message)
             return jsonify({'success': False, 'error': error_message}), 400

        logger.info(f"Analysis complete for target: {target}. Performed {analysis_performed_count} analyses. Results keys: {list(results.keys())}")
        response_data = {
            'success': True,
            'target': target,
            'target_type': target_type,
            'analysis_type': analysis_type, # Return the requested type ('all' or specific)
            'results': results,
        }
        if report_path:
            # Return the relative path suitable for frontend linking
            response_data['report_path'] = os.path.relpath(report_path, GENERATED_REPORTS_DIR)
        return jsonify(response_data)
    except Exception as e:
        logger.exception(f"Unhandled error during analysis for {target}: {str(e)}")
        return jsonify({'success': False, 'error': f'An unexpected server error occurred: {str(e)}'}), 500

@app.route('/api/reports/<report_id>')
def get_report_metadata(report_id): # Renamed function
    """API endpoint to get report metadata by ID (if ReportStore is used)"""
    # This endpoint might be less relevant if reports are just files.
    # If ReportStore saves metadata, this can retrieve it.
    if not ANALYZERS_READY: # Check if components are ready
         return jsonify({'error': 'Server components not ready.'}), 503
    try:
        report_meta = report_store.get_report(report_id) # Assumes ReportStore stores metadata
        if not report_meta:
            logger.warning(f"Report metadata not found for ID: {report_id}")
            return jsonify({'error': 'Report metadata not found'}), 404
        logger.info(f"Retrieved report metadata for ID: {report_id}")
        # Optionally, add a link to the actual report file served by /generated_reports/
        # report_meta['file_url'] = url_for('view_report_file', filename=f"{report_id}.md", _external=True) # Requires url_for
        return jsonify(report_meta)
    except Exception as e:
        logger.error(f"Error retrieving report metadata {report_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports') # Endpoint to list available report *files*
def list_report_files(): # Renamed function
    """API endpoint to list generated report files"""
    if not ANALYZERS_READY: # Check if components are ready
         return jsonify({'reports': [], 'error': 'Server components not ready.'}), 503
    try:
        # List files directly from the reports directory
        if not os.path.exists(GENERATED_REPORTS_DIR):
             logger.warning(f"Reports directory not found: {GENERATED_REPORTS_DIR}")
             return jsonify({'reports': []}) # Return empty list if dir doesn't exist
        report_files = [f for f in os.listdir(GENERATED_REPORTS_DIR) if os.path.isfile(os.path.join(GENERATED_REPORTS_DIR, f)) and f.endswith('.md')] # Assuming markdown reports
        reports_data = []
        for filename in report_files:
            report_id = filename.replace('.md', '') # Simple ID from filename
            creation_time = None
            try:
                file_path = os.path.join(GENERATED_REPORTS_DIR, filename)
                creation_time = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
            except Exception as time_e:
                logger.warning(f"Could not get creation time for {filename}: {time_e}")
            reports_data.append({
                'id': report_id,
                'filename': filename,
                'created_at': creation_time
                # TODO: Add target address/token if parsable from filename or stored elsewhere
            })
        # Sort reports, e.g., by creation time descending
        reports_data.sort(key=lambda x: x.get('created_at') or '', reverse=True)
        logger.info(f"Listed {len(reports_data)} report files from {GENERATED_REPORTS_DIR}")
        return jsonify({'reports': reports_data})
    except Exception as e:
        logger.error(f"Error listing report files: {str(e)}")
        return jsonify({'error': f'Failed to list reports: {str(e)}'}), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint to search for addresses/entities"""
    if not ANALYZERS_READY: # Check if components are ready
         return jsonify({'error': 'Server components not ready.'}), 503
    data = request.json
    query = data.get('query')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    try:
        logger.info(f"Performing search for query: {query}")
        # Assuming address_db is initialized correctly
        results = address_db.search_entities(query)
        logger.info(f"Search for '{query}' returned {len(results)} results.")
        return jsonify({
            'success': True,
            'query': query,
            'results': results
        })
    except Exception as e:
        logger.error(f"Error searching for {query}: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add a health check endpoint
@app.route('/api/health')
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',  # You can add version info here
        'timestamp': datetime.now().isoformat()
    })

# --- Route for serving generated report files (Markdown and Images) ---
@app.route('/generated_reports/<path:filename>')
def view_report_file(filename): # Renamed function
    """Serves generated report files (MD, PNG, etc.) directly from the output directory"""
    logger.info(f"Request received for report file: {filename}")
    # Basic security check: prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        logger.warning(f"Attempted directory traversal: {filename}")
        abort(404)
    try:
        # Determine mimetype based on file extension
        mimetype = mimetypes.guess_type(filename)[0]
        logger.debug(f"Serving file {filename} with mimetype {mimetype}")
        # Use send_from_directory for safer file serving
        return send_from_directory(GENERATED_REPORTS_DIR, filename, mimetype=mimetype)
    except FileNotFoundError:
        logger.error(f"Report file not found: {filename} in {GENERATED_REPORTS_DIR}")
        abort(404) # Return 404 if file doesn't exist
    except Exception as e:
        logger.error(f"Error serving report file {filename}: {e}")
        abort(500)

# --- Removed all HTML rendering routes ---

if __name__ == '__main__':
    if not ANALYZERS_READY:
        logger.error("Application cannot start because core components failed to initialize.")
        sys.exit(1)
    logger.info(f"Starting Sentinel AI server on http://{API_HOST}:{API_PORT}")
    # Use production server if installed, otherwise fall back to Flask dev server
    try:
        import waitress
        logger.info("Using Waitress production server")
        waitress.serve(app, host=API_HOST, port=API_PORT)
    except ImportError:
        logger.warning("Waitress not installed - using Flask development server")
        logger.warning("This is not recommended for production use!")
        app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG)