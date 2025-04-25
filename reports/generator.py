"""
Report generator for creating detailed security reports
"""
import os # Added missing import
import sys # Added missing import
import logging # Added missing import
from datetime import datetime
import pandas as pd # Added missing import
import matplotlib.pyplot as plt # Added missing import
import networkx as nx # Added missing import
from matplotlib.lines import Line2D # Added missing import for legend

# Add the project root (c:\Users\subas\sentinel-ai\sentinel) to the Python path
# This allows absolute imports from the 'sentinel' package
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Use absolute imports from the 'sentinel' package
# If the linter still shows errors, it might be a configuration issue.
# Removed unused import causing the error: from sentinel.data.storage.address_db import get_address_data, get_token_data

logger = logging.getLogger(__name__)

# Define report templates directory relative to this file
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Define reports output directory relative to project root's sentinel dir
REPORTS_DIR = os.path.join(PROJECT_ROOT, "sentinel", "reports", "output")
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True) # Ensure templates dir exists

def generate_report(target, data, report_type): # Added target parameter
    """
    Generate a report based on analysis data

    Args:
        target (str): The address or token mint analyzed.
        data (dict): Analysis data for the specific report type.
        report_type (str): Type of report to generate.

    Returns:
        str: Path to the generated report or None if type is invalid or data is missing.
    """
    if not data:
        logger.warning(f"No data provided for {report_type} report generation for target {target}.")
        return None

    logger.info(f"Generating {report_type} report for target: {target}")

    # Use target for filename generation
    safe_target_part = target.replace('/', '_').replace('\\', '_')[:12] # Make target safe for filename

    if report_type == "ico":
        return generate_ico_report(safe_target_part, data)
    elif report_type == "money_laundering": # Corrected type name
        return generate_laundering_report(safe_target_part, data)
    elif report_type == "rugpull":
        return generate_rugpull_report(safe_target_part, data)
    elif report_type == "mixer":
        return generate_mixer_report(safe_target_part, data)
    elif report_type == "dusting":
        return generate_dusting_report(safe_target_part, data)
    # Add cases for 'wallet' and 'transaction' if specific reports are needed
    # elif report_type == "wallet":
    #     return generate_wallet_report(safe_target_part, data)
    # elif report_type == "transaction":
    #     return generate_transaction_report(safe_target_part, data)
    else:
        logger.error(f"Invalid report type specified: {report_type} for target {target}")
        return None

def generate_ico_report(target_part, data): # Added target_part parameter
    """
    Generate a report for ICO analysis

    Args:
        target_part (str): Safe string derived from the token mint for filename.
        data (dict): ICO analysis data.

    Returns:
        str: Path to the generated report or None on error.
    """
    # Load template
    template_path = os.path.join(TEMPLATES_DIR, "ico_report.md")
    try:
        with open(template_path, "r") as file:
            template = file.read() # Added missing read()
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_path}")
        # Attempt to create a default template if missing
        create_default_templates()
        try:
            with open(template_path, "r") as file:
                template = file.read()
        except FileNotFoundError:
             logger.error(f"Still cannot find template: {template_path}")
             return None

    # Extract data (use .get with defaults)
    token_data = data.get("token_data", {})
    creator_data = data.get("creator_data", {})
    funding_flow = data.get("funding_flow", {})
    risk_assessment = data.get("risk_assessment", {})
    suspicious_patterns = data.get("suspicious_patterns", {}) # Added

    # Format variables
    token_name = token_data.get("name", "Unknown")
    token_symbol = token_data.get("symbol", "Unknown")
    token_price = token_data.get("price_usd") # Keep as number or None
    market_cap = token_data.get("market_cap") # Keep as number or None

    creator_wallet = creator_data.get("address", "Unknown")
    team_wallets_list = creator_data.get("team_wallets", [])
    team_wallets = "\n".join([f"* `{wallet}`" for wallet in team_wallets_list]) if team_wallets_list else "No team wallets identified"

    total_raised = funding_flow.get('total_raised_usd') # Keep as number or None
    investor_count = funding_flow.get('investor_count', 0)

    # Format suspicious patterns
    detected_patterns = suspicious_patterns.get("detected_patterns", [])
    patterns_list = "\n".join([f"* **{p.get('pattern', 'Unknown Pattern')}**: {p.get('description', 'N/A')} (Confidence: {p.get('confidence', 0):.2f})" for p in detected_patterns]) if detected_patterns else "No specific suspicious patterns detected."


    # Generate visualizations (ensure these functions return relative paths or handle errors)
    funding_flow_image_path = None
    if funding_flow:
        try:
            funding_flow_image_path = generate_funding_flow_visualization(funding_flow)
            if funding_flow_image_path:
                funding_flow_image_path = os.path.basename(funding_flow_image_path) # Use relative path for MD
        except Exception as e:
            logger.error(f"Error generating funding flow visualization: {e}")

    token_distribution_image_path = None
    if "distribution" in token_data:
        try:
            token_distribution_image_path = generate_token_distribution_chart(token_data["distribution"])
            if token_distribution_image_path:
                token_distribution_image_path = os.path.basename(token_distribution_image_path) # Use relative path
        except Exception as e:
            logger.error(f"Error generating token distribution chart: {e}")

    # Format risk factors
    risk_factors_list = risk_assessment.get("risk_factors", [])
    risk_factors_md = "\n".join([f"* {factor}" for factor in risk_factors_list]) if risk_factors_list else "No specific risk factors identified"

    # Fill template
    report_content = template.format(
        token_name=token_name,
        token_symbol=token_symbol,
        token_price=f"${token_price:,.8f}" if token_price is not None else "N/A",
        market_cap=f"${market_cap:,.2f}" if market_cap is not None else "N/A",
        creator_wallet=f"`{creator_wallet}`" if creator_wallet != "Unknown" else "Unknown",
        team_wallets=team_wallets,
        total_raised=f"${total_raised:,.2f}" if total_raised is not None else "N/A",
        investor_count=investor_count,
        funding_flow_image=f"![Funding Flow](./{funding_flow_image_path})" if funding_flow_image_path else "No funding flow visualization available.",
        token_distribution_image=f"![Token Distribution](./{token_distribution_image_path})" if token_distribution_image_path else "No token distribution visualization available.",
        suspicious_patterns=patterns_list, # Added patterns
        risk_level=risk_assessment.get("risk_level", "Unknown"),
        risk_score=risk_assessment.get("risk_score", 0),
        risk_factors=risk_factors_md,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Save report
    report_name = f"ico_report_{target_part}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    report_path = os.path.join(REPORTS_DIR, report_name)

    try:
        with open(report_path, "w", encoding='utf-8') as file: # Added encoding
            file.write(report_content)
    except IOError as e:
        logger.error(f"Error writing report file {report_path}: {e}")
        return None

    logger.info(f"ICO report generated: {report_path}")
    return report_path # Return the full path

def generate_laundering_report(target_part, data): # Added target_part parameter
    """
    Generate a report for money laundering analysis

    Args:
        target_part (str): Safe string derived from the address for filename.
        data (dict): Money laundering analysis data.

    Returns:
        str: Path to the generated report or None on error.
    """
    # Load template
    template_path = os.path.join(TEMPLATES_DIR, "laundering_report.md")
    try:
        with open(template_path, "r", encoding='utf-8') as file: # Added encoding
            template = file.read()
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_path}")
        create_default_templates()
        try:
            with open(template_path, "r", encoding='utf-8') as file:
                template = file.read()
        except FileNotFoundError:
             logger.error(f"Still cannot find template: {template_path}")
             return None

    # Extract data
    address = data.get("address", "Unknown")
    detected_techniques = data.get("detected_techniques", []) # Use detected_techniques
    mixer_interactions = data.get("mixer_interactions", [])
    cross_chain_transfers = data.get("cross_chain_transfers", [])
    exchange_interactions = data.get("exchange_interactions", [])
    risk_assessment = data.get("risk_assessment", {})
    money_laundering_routes = data.get("money_laundering_routes", []) # Added

    # Format variables
    techniques_list = "\n".join([
        f"* **{tech.get('technique', 'Unknown Technique')}**: {tech.get('description', 'N/A')} (Confidence: {tech.get('confidence', 0):.2f})"
        for tech in detected_techniques
    ]) if detected_techniques else "No specific money laundering techniques detected."

    mixer_interactions_list = "\n".join([
        f"* **{mixer.get('name', 'Unknown Mixer')}**: {mixer.get('transaction_count', 0)} transactions, " +
        f"total volume ${mixer.get('volume_usd', 0):,.2f}"
        for mixer in mixer_interactions
    ]) if mixer_interactions else "No mixer interactions detected."

    cross_chain_list = "\n".join([
        f"* **{transfer.get('source_chain', '?')} → {transfer.get('destination_chain', '?')}** "
        f"via {transfer.get('bridge_name', 'Unknown Bridge')}: "
        f"${transfer.get('amount_usd', 0):,.2f} ({transfer.get('timestamp', 'N/A')})"
        for transfer in cross_chain_transfers
    ]) if cross_chain_transfers else "No cross-chain transfers detected."

    exchange_list = "\n".join([
        f"* **{exchange.get('name', 'Unknown Exchange')}**: {exchange.get('transaction_count', 0)} transactions, " +
        f"total volume ${exchange.get('volume_usd', 0):,.2f}"
        for exchange in exchange_interactions
    ]) if exchange_interactions else "No notable exchange interactions detected."

    routes_list = "\n".join([
        f"* **Route to {route.get('destination_type', '?')}**: Value ${route.get('total_value_usd', 0):,.2f}, "
        f"Path Length: {route.get('path_length', '?')}, Techniques: {', '.join(route.get('techniques_used', []))}"
        for route in money_laundering_routes
    ]) if money_laundering_routes else "No specific money laundering routes identified."


    # Generate visualizations
    flow_graph_image_path = None
    # Pass relevant data for visualization
    viz_data = {
        "address": address,
        "mixer_interactions": mixer_interactions,
        "exchange_interactions": exchange_interactions,
        "cross_chain_transfers": cross_chain_transfers
    }
    try:
        flow_graph_image_path = generate_flow_visualization(viz_data)
        if flow_graph_image_path:
            flow_graph_image_path = os.path.basename(flow_graph_image_path)
    except Exception as e:
        logger.error(f"Error generating flow visualization: {e}")

    timeline_image_path = None
    # Combine transfers for timeline
    all_transfers_for_timeline = []
    for item in mixer_interactions + exchange_interactions + cross_chain_transfers:
        ts = item.get('timestamp', item.get('last_seen')) # Try to get a timestamp
        vol = item.get('volume_usd', item.get('amount_usd'))
        typ = item.get('type', 'unknown') # Determine type if possible
        if 'bridge_name' in item: typ = 'cross_chain'
        elif 'mixer' in item.get('name', '').lower(): typ = 'mixer'
        elif 'exchange' in item.get('name', '').lower(): typ = 'exchange'

        if ts and vol is not None:
            all_transfers_for_timeline.append({'timestamp': ts, 'volume_usd': vol, 'type': typ})

    if all_transfers_for_timeline:
        try:
            timeline_image_path = generate_timeline_visualization(all_transfers_for_timeline)
            if timeline_image_path:
                timeline_image_path = os.path.basename(timeline_image_path)
        except Exception as e:
            logger.error(f"Error generating timeline visualization: {e}")

    # Format risk factors
    risk_factors_list = risk_assessment.get("risk_factors", [])
    risk_factors_md = "\n".join([f"* {factor}" for factor in risk_factors_list]) if risk_factors_list else "No specific risk factors identified"


    # Fill template
    report_content = template.format(
        address=f"`{address}`" if address != "Unknown" else "Unknown",
        detected_techniques=techniques_list, # Use techniques list
        mixer_interactions=mixer_interactions_list,
        cross_chain_transfers=cross_chain_list,
        exchange_interactions=exchange_list,
        money_laundering_routes=routes_list, # Added routes
        flow_graph_image=f"![Money Flow](./{flow_graph_image_path})" if flow_graph_image_path else "No money flow visualization available.",
        timeline_image=f"![Transaction Timeline](./{timeline_image_path})" if timeline_image_path else "No transaction timeline visualization available.",
        risk_level=risk_assessment.get("risk_level", "Unknown"),
        risk_score=risk_assessment.get("overall_risk_score", risk_assessment.get("risk_score", 0)), # Check for overall score
        risk_factors=risk_factors_md,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Save report
    report_name = f"laundering_report_{target_part}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    report_path = os.path.join(REPORTS_DIR, report_name)

    try:
        with open(report_path, "w", encoding='utf-8') as file: # Added encoding
            file.write(report_content)
    except IOError as e:
        logger.error(f"Error writing report file {report_path}: {e}")
        return None

    logger.info(f"Money laundering report generated: {report_path}")
    return report_path # Return the full path

def generate_rugpull_report(target_part, data): # Added target_part parameter
    """
    Generate a report for rugpull analysis

    Args:
        target_part (str): Safe string derived from the token mint for filename.
        data (dict): Rugpull analysis data.

    Returns:
        str: Path to the generated report or None on error.
    """
    # Load template
    template_path = os.path.join(TEMPLATES_DIR, "rugpull_report.md")
    try:
        with open(template_path, "r", encoding='utf-8') as file: # Added encoding
            template = file.read()
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_path}")
        create_default_templates()
        try:
            with open(template_path, "r", encoding='utf-8') as file:
                template = file.read()
        except FileNotFoundError:
             logger.error(f"Still cannot find template: {template_path}")
             return None

    # Extract data
    token_data = data.get("token_data", {})
    creator_data = data.get("creator_analysis", data.get("creator_data", {})) # Check both keys
    liquidity_data = data.get("liquidity_analysis", data.get("liquidity_data", {})) # Check both keys
    risk_assessment = data.get("risk_assessment", {})
    detected_methods = data.get("detected_methods", []) # Added

    # Format variables
    token_name = token_data.get("name", "Unknown")
    token_symbol = token_data.get("symbol", "Unknown")
    token_mint = token_data.get("mint", "Unknown")
    token_creator = creator_data.get("address", creator_data.get("creator_address", "Unknown"))
    creation_date = token_data.get("creation_date", "Unknown")
    total_supply = token_data.get('total_supply') # Keep as number or None
    current_price = token_data.get('current_price', token_data.get('price_usd')) # Keep as number or None

    liquidity_usd = liquidity_data.get('total_liquidity_usd', liquidity_data.get('current_liquidity_usd')) # Keep as number or None
    locked_percentage = liquidity_data.get('liquidity_locked_pct', liquidity_data.get('locked_percentage')) # Keep as number or None
    lock_expiry = liquidity_data.get("lock_expiry", "Not locked or Unknown")

    previous_tokens_list = creator_data.get("previous_tokens", [])
    creator_previous_tokens = "\n".join([f"* `{token}`" for token in previous_tokens_list]) if previous_tokens_list else "No previous tokens found"

    insider_wallets_list = creator_data.get("insider_wallets", []) # Might be under team_analysis too
    if not insider_wallets_list and "team_analysis" in data:
        insider_wallets_list = data["team_analysis"].get("team_wallets", [])
    insider_wallets = "\n".join([f"* `{wallet}`" for wallet in insider_wallets_list]) if insider_wallets_list else "No insider wallets identified"

    # Format detected methods
    methods_list = "\n".join([
        f"* **{meth.get('method', 'Unknown Method')}**: {meth.get('description', 'N/A')} (Confidence: {meth.get('confidence', 0):.2f})"
        for meth in detected_methods
    ]) if detected_methods else "No specific rugpull methods detected."


    # Generate visualizations
    liquidity_chart_path = None
    if "history" in liquidity_data:
        try:
            liquidity_chart_path = generate_liquidity_chart(liquidity_data["history"])
            if liquidity_chart_path:
                liquidity_chart_path = os.path.basename(liquidity_chart_path)
        except Exception as e:
            logger.error(f"Error generating liquidity chart: {e}")

    token_price_chart_path = None
    if "price_history" in token_data:
        try:
            token_price_chart_path = generate_price_chart(token_data["price_history"])
            if token_price_chart_path:
                token_price_chart_path = os.path.basename(token_price_chart_path)
        except Exception as e:
            logger.error(f"Error generating price chart: {e}")

    holder_distribution_chart_path = None
    if "holders" in token_data: # Assuming holders data is structured correctly
        try:
            holder_distribution_chart_path = generate_holder_distribution_chart(token_data["holders"])
            if holder_distribution_chart_path:
                holder_distribution_chart_path = os.path.basename(holder_distribution_chart_path)
        except Exception as e:
            logger.error(f"Error generating holder distribution chart: {e}")

    # Format risk factors
    risk_factors_list = risk_assessment.get("risk_factors", [])
    risk_factors_md = "\n".join([f"* {factor}" for factor in risk_factors_list]) if risk_factors_list else "No specific risk factors identified"


    # Fill template
    report_content = template.format(
        token_name=token_name,
        token_symbol=token_symbol,
        token_mint=f"`{token_mint}`" if token_mint != "Unknown" else "Unknown",
        token_creator=f"`{token_creator}`" if token_creator != "Unknown" else "Unknown",
        creation_date=creation_date,
        total_supply=f"{total_supply:,.0f}" if total_supply is not None else "N/A",
        current_price=f"${current_price:,.8f}" if current_price is not None else "N/A",
        liquidity_usd=f"${liquidity_usd:,.2f}" if liquidity_usd is not None else "N/A",
        liquidity_locked_percentage=f"{locked_percentage:.1f}%" if locked_percentage is not None else "N/A",
        lock_expiry=lock_expiry,
        creator_previous_tokens=creator_previous_tokens,
        insider_wallets=insider_wallets,
        detected_methods=methods_list, # Added methods
        token_price_chart=f"![Token Price](./{token_price_chart_path})" if token_price_chart_path else "No price chart available.",
        liquidity_chart=f"![Liquidity](./{liquidity_chart_path})" if liquidity_chart_path else "No liquidity chart available.",
        holder_distribution_chart=f"![Holder Distribution](./{holder_distribution_chart_path})" if holder_distribution_chart_path else "No holder distribution chart available.",
        risk_level=risk_assessment.get("risk_level", "Unknown"),
        risk_score=risk_assessment.get("risk_score", 0),
        risk_factors=risk_factors_md,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Save report
    report_name = f"rugpull_report_{target_part}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    report_path = os.path.join(REPORTS_DIR, report_name)

    try:
        with open(report_path, "w", encoding='utf-8') as file: # Added encoding
            file.write(report_content)
    except IOError as e:
        logger.error(f"Error writing report file {report_path}: {e}")
        return None

    logger.info(f"Rugpull report generated: {report_path}")
    return report_path # Return the full path

def generate_mixer_report(target_part, data): # Added target_part parameter
    """
    Generate a report for mixer analysis

    Args:
        target_part (str): Safe string derived from the address for filename.
        data (dict): Mixer analysis data.

    Returns:
        str: Path to the generated report or None on error.
    """
    # Load template
    template_path = os.path.join(TEMPLATES_DIR, "mixer_report.md")
    try:
        with open(template_path, "r", encoding='utf-8') as file: # Added encoding
            template = file.read()
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_path}")
        create_default_templates()
        try:
            with open(template_path, "r", encoding='utf-8') as file:
                template = file.read()
        except FileNotFoundError:
             logger.error(f"Still cannot find template: {template_path}")
             return None

    # Extract data
    mixer_address = data.get("address", "Unknown")
    users = data.get("top_users", data.get("users", [])) # Check both keys
    volume_data = data.get("volume_analysis", data.get("volume_data", {})) # Check both keys
    patterns = data.get("detected_patterns", data.get("patterns", {})) # Check both keys
    risk_assessment = data.get("risk_assessment", {})

    # Format variables
    user_list = "\n".join([
        f"* **`{user.get('address', 'Unknown')[:8]}...{user.get('address', 'Unknown')[-4:]}`**: {user.get('transaction_count', 0)} transactions, " +
        f"volume ${user.get('volume_usd', 0):,.2f}"
        for user in users[:10] # Limit to top 10 users for display
    ]) if users else "No user data available."

    # Format patterns (handle dict or list)
    if isinstance(patterns, list):
         patterns_list = "\n".join([f"* **{p.get('pattern', 'Unknown Pattern')}**: {p.get('description', 'N/A')} (Confidence: {p.get('confidence', 0):.2f})" for p in patterns])
    elif isinstance(patterns, dict):
         patterns_list = "\n".join([f"* **{key}**: {value}" for key, value in patterns.items()])
    else:
         patterns_list = "No specific patterns detected."
    if not patterns: patterns_list = "No specific patterns detected."


    # Generate visualizations
    volume_chart_path = None
    if "history" in volume_data:
        try:
            volume_chart_path = generate_volume_chart(volume_data["history"])
            if volume_chart_path:
                volume_chart_path = os.path.basename(volume_chart_path)
        except Exception as e:
            logger.error(f"Error generating volume chart: {e}")

    user_graph_path = None
    if users:
        try:
            user_graph_path = generate_user_graph(users)
            if user_graph_path:
                user_graph_path = os.path.basename(user_graph_path)
        except Exception as e:
            logger.error(f"Error generating user graph: {e}")

    # Format risk factors
    risk_factors_list = risk_assessment.get("risk_factors", [])
    risk_factors_md = "\n".join([f"* {factor}" for factor in risk_factors_list]) if risk_factors_list else "No specific risk factors identified"


    # Fill template
    report_content = template.format(
        mixer_address=f"`{mixer_address}`" if mixer_address != "Unknown" else "Unknown",
        first_seen=volume_data.get("first_seen", "Unknown"),
        last_seen=volume_data.get("last_seen", "Unknown"),
        total_volume=f"${volume_data.get('total_volume_usd', 0):,.2f}",
        transaction_count=volume_data.get("transaction_count", 0),
        unique_users=volume_data.get("unique_users", len(users)), # Use value from volume_data if available
        top_users=user_list,
        volume_chart=f"![Volume History](./{volume_chart_path})" if volume_chart_path else "No volume chart available.",
        user_graph=f"![User Graph](./{user_graph_path})" if user_graph_path else "No user graph available.",
        patterns=patterns_list,
        risk_level=risk_assessment.get("risk_level", "Unknown"),
        risk_score=risk_assessment.get("risk_score", 0),
        risk_factors=risk_factors_md,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Save report
    report_name = f"mixer_report_{target_part}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    report_path = os.path.join(REPORTS_DIR, report_name)

    try:
        with open(report_path, "w", encoding='utf-8') as file: # Added encoding
            file.write(report_content)
    except IOError as e:
        logger.error(f"Error writing report file {report_path}: {e}")
        return None

    logger.info(f"Mixer report generated: {report_path}")
    return report_path # Return the full path

def generate_dusting_report(target_part, data): # Added target_part parameter
    """
    Generate a report for address dusting analysis

    Args:
        target_part (str): Safe string derived from the address for filename.
        data (dict): Dusting analysis data.

    Returns:
        str: Path to the generated report or None on error.
    """
    # Load template
    template_path = os.path.join(TEMPLATES_DIR, "dusting_report.md")
    try:
        with open(template_path, "r", encoding='utf-8') as file: # Added encoding
            template = file.read()
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_path}")
        create_default_templates()
        try:
            with open(template_path, "r", encoding='utf-8') as file:
                template = file.read()
        except FileNotFoundError:
             logger.error(f"Still cannot find template: {template_path}")
             return None

    # Extract data
    target_address = data.get("address", "Unknown")
    # Use poisoning_attempts from top-level first, then risk_assessment
    poisoning_attempts = data.get("poisoning_attempts", [])
    if not poisoning_attempts and "risk_assessment" in data:
         poisoning_attempts = data["risk_assessment"].get("poisoning_attempts_details", [])

    dusting_campaigns = data.get("dusting_campaigns", [])
    address_relationships = data.get("address_relationships", []) # Placeholder
    victim_patterns = data.get("victim_patterns", {}) # Placeholder
    risk_assessment = data.get("risk_assessment", {})

    # Format variables
    all_attempts_formatted = []
    # Format poisoning attempts
    for attempt in poisoning_attempts:
        sim_score = attempt.get("similarity", {}).get("visual_similarity", 0)
        all_attempts_formatted.append(
            f"* **Poisoning Attempt**: Attacker ` {attempt.get('poisoning_address', '?')[:8]}...{attempt.get('poisoning_address', '?')[-4:]} ` "
            f"(Similarity: {sim_score:.2f} to `{attempt.get('legitimate_counterparty', '?')[:8]}...`), "
            f"{attempt.get('transaction_count', '?')} txs, Last Seen: {attempt.get('last_seen', 'N/A')}"
        )
    # Format dusting campaigns targeting this address
    for campaign in dusting_campaigns:
        campaign_info = f"Part of larger campaign ({campaign.get('campaign_size', '?')} recipients)" if campaign.get('part_of_larger_campaign') else ""
        all_attempts_formatted.append(
            f"* **Dusting Campaign**: Sender ` {campaign.get('sender_address', '?')[:8]}...{campaign.get('sender_address', '?')[-4:]} `, "
            f"{campaign.get('dust_transaction_count', '?')} dust txs to this address. "
            f"Last Seen: {campaign.get('last_seen', 'N/A')}. {campaign_info}"
        )

    dusting_list = "\n".join(all_attempts_formatted) if all_attempts_formatted else "No specific dusting or poisoning attempts detected targeting this address."

    # Get first/last seen from the combined data if possible
    first_attempt_ts = None
    last_attempt_ts = None
    all_timestamps = []
    for attempt in poisoning_attempts + dusting_campaigns:
        ts_str = attempt.get('last_seen', attempt.get('first_seen'))
        if ts_str:
            try:
                # Handle potential 'Z' timezone indicator
                ts_str = ts_str.replace('Z', '+00:00')
                all_timestamps.append(datetime.fromisoformat(ts_str))
            except ValueError:
                logger.warning(f"Could not parse timestamp: {ts_str}")
                pass # Ignore unparseable timestamps

    if all_timestamps:
        first_attempt_ts = min(all_timestamps).strftime("%Y-%m-%d %H:%M:%S")
        last_attempt_ts = max(all_timestamps).strftime("%Y-%m-%d %H:%M:%S")


    relationships_list = "\n".join([
        f"* **`{rel.get('address', '?')[:8]}...{rel.get('address', '?')[-4:]}`**: {rel.get('relationship_type', 'Related')}, " +
        f"Similarity Score: {rel.get('similarity_score', 0):.2f}"
        for rel in address_relationships
    ]) if address_relationships else "No specific address relationships detected."

    patterns_list = "\n".join([f"* **{key}**: {value}" for key, value in victim_patterns.items()]) if victim_patterns else "No specific victim patterns detected."

    # Generate visualizations
    dusting_timeline_path = None
    # Create data suitable for timeline viz
    timeline_data = []
    for attempt in poisoning_attempts:
         ts = attempt.get('last_seen', attempt.get('first_seen'))
         if ts: timeline_data.append({'timestamp': ts, 'volume_usd': 0, 'type': 'poisoning'}) # Use 0 volume for poisoning
    for campaign in dusting_campaigns:
         ts = campaign.get('last_seen', campaign.get('first_seen'))
         if ts: timeline_data.append({'timestamp': ts, 'volume_usd': campaign.get('total_dust_value_usd', 0.01), 'type': 'dust_campaign'}) # Use small volume

    if timeline_data:
        try:
            dusting_timeline_path = generate_dusting_timeline(timeline_data)
            if dusting_timeline_path:
                dusting_timeline_path = os.path.basename(dusting_timeline_path)
        except Exception as e:
            logger.error(f"Error generating dusting timeline: {e}")

    relationship_graph_path = None
    if address_relationships:
        try:
            relationship_graph_path = generate_relationship_graph(target_address, address_relationships)
            if relationship_graph_path:
                relationship_graph_path = os.path.basename(relationship_graph_path)
        except Exception as e:
            logger.error(f"Error generating relationship graph: {e}")

    # Format risk factors from risk_assessment
    risk_factors_list_data = risk_assessment.get("risk_factors", [])
    risk_factors_md = "\n".join([f"* {factor.get('description', factor.get('factor', 'Unknown Factor'))}" for factor in risk_factors_list_data]) if risk_factors_list_data else "No specific risk factors identified."


    # Fill template
    report_content = template.format(
        target_address=f"`{target_address}`" if target_address != "Unknown" else "Unknown",
        dusting_attempts_count=risk_assessment.get("poisoning_attempts", 0) + risk_assessment.get("dust_transactions", 0), # Use counts from risk assessment
        first_attempt=first_attempt_ts or "N/A",
        last_attempt=last_attempt_ts or "N/A",
        dusting_attempts=dusting_list,
        address_relationships=relationships_list,
        victim_patterns=patterns_list,
        dusting_timeline=f"![Dusting Timeline](./{dusting_timeline_path})" if dusting_timeline_path else "No dusting timeline available.",
        relationship_graph=f"![Relationship Graph](./{relationship_graph_path})" if relationship_graph_path else "No relationship graph available.",
        risk_level=risk_assessment.get("risk_level", "Unknown"),
        risk_score=risk_assessment.get("risk_score", 0),
        risk_factors=risk_factors_md,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Save report
    report_name = f"dusting_report_{target_part}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    report_path = os.path.join(REPORTS_DIR, report_name)

    try:
        with open(report_path, "w", encoding='utf-8') as file: # Added encoding
            file.write(report_content)
    except IOError as e:
        logger.error(f"Error writing report file {report_path}: {e}")
        return None

    logger.info(f"Dusting attack report generated: {report_path}")
    return report_path # Return the full path

def generate_funding_flow_visualization(funding_flow):
    """
    Generate a visualization of ICO funding flow
    
    Args:
        funding_flow (dict): Funding flow data
    
    Returns:
        str: Path to the saved visualization or None on error
    """
    try:
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes
        ico_contract = funding_flow.get("ico_contract", "ICO Contract")
        G.add_node(ico_contract, type="contract", label=ico_contract[:6]+"...")
        
        investors = funding_flow.get("investors", [])
        destinations = funding_flow.get("fund_destinations", [])
        
        # Add investor nodes and edges (limit for clarity)
        for i, investor in enumerate(investors[:20]):
            addr = investor.get("address", f"Investor_{i}")
            label = addr[:6]+"..."
            G.add_node(addr, type="investor", label=label)
            G.add_edge(addr, ico_contract, weight=investor.get("amount_usd", 1))
        
        # Add destination nodes and edges (limit for clarity)
        for i, dest in enumerate(destinations[:10]):
            addr = dest.get("address", f"Destination_{i}")
            label = addr[:6]+"..."
            G.add_node(addr, type="destination", label=label)
            G.add_edge(ico_contract, addr, weight=dest.get("amount_usd", 1))
        
        # Create figure
        plt.figure(figsize=(14, 10)) # Adjusted size
        
        # Create positions
        pos = nx.spring_layout(G, k=0.6, iterations=60) # Adjust layout parameters
        
        # Draw nodes
        node_colors = []
        node_sizes = []
        labels = {}
        for node, data in G.nodes(data=True):
            labels[node] = data.get("label", node)
            if data.get("type") == "contract":
                node_colors.append("red")
                node_sizes.append(1500)
            elif data.get("type") == "investor":
                node_colors.append("blue")
                node_sizes.append(500)
            elif data.get("type") == "destination":
                node_colors.append("green")
                node_sizes.append(800)
            else:
                node_colors.append("grey")
                node_sizes.append(300)
        
        
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.8)
        
        # Draw edges
        edges = G.edges(data=True)
        # Normalize weights for better visualization
        max_weight = max((data["weight"] for _, _, data in edges if data.get("weight")), default=1)
        min_weight_display = 0.5
        max_weight_display = 5.0
        weights = [min_weight_display + (max_weight_display - min_weight_display) * (data.get("weight", 0) / max_weight)
                   for _, _, data in edges]
        
        nx.draw_networkx_edges(G, pos, width=weights, alpha=0.5, edge_color="gray", arrows=True, arrowsize=15, connectionstyle='arc3,rad=0.1') # Added connectionstyle
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, font_family="sans-serif") # Use generated labels
        
        # Add legend (using proxy artists)
        legend_elements = [Line2D([0], [0], marker='o', color='w', label='ICO Contract', markerfacecolor='red', markersize=10),
                           Line2D([0], [0], marker='o', color='w', label='Investors', markerfacecolor='blue', markersize=10),
                           Line2D([0], [0], marker='o', color='w', label='Fund Destinations', markerfacecolor='green', markersize=10)]
        plt.legend(handles=legend_elements, loc='best')
        
        plt.title("ICO Funding Flow (Sampled)")
        plt.axis('off') # Turn off axis
        plt.tight_layout()
        
        # Save the figure
        # Use target_part in filename if available, else timestamp
        target_part = funding_flow.get("token_symbol", datetime.now().strftime('%Y%m%d%H%M%S'))
        image_path = os.path.join(REPORTS_DIR, f"funding_flow_{target_part}.png")
        plt.savefig(image_path)
        plt.close()
        
        return image_path # Return full path
    except Exception as e:
        logger.error(f"Error in generate_funding_flow_visualization: {e}")
        plt.close() # Ensure plot is closed even on error
        return None

def generate_token_distribution_chart(distribution):
    """
    Generate a token distribution chart
    
    Args:
        distribution (list): Token distribution data (list of dicts with 'category', 'percentage')
    
    Returns:
        str: Path to the saved chart or None on error
    """
    try:
        if not distribution:
            logger.warning("No distribution data provided for chart.") # Added warning
            return None
            
        # Create dataframe
        df = pd.DataFrame(distribution)
        
        # Ensure required columns exist
        if 'category' not in df.columns or 'percentage' not in df.columns:
            logger.error("Distribution data missing 'category' or 'percentage' column.") # Added error log
            return None
        
        # Convert percentage to numeric, handling errors
        df['percentage'] = pd.to_numeric(df['percentage'], errors='coerce')
        df = df.dropna(subset=['percentage']) # Remove rows where conversion failed
        
        if df.empty:
             logger.warning("No valid numeric percentage data found for distribution chart.")
             return None
        
        # Aggregate small slices into 'Other' if necessary
        threshold = 2.0 # Combine slices smaller than 2%
        small_slices = df[df['percentage'] < threshold]
        if not small_slices.empty and len(df) > 5: # Only group if there are small slices and enough total slices
            other_sum = small_slices['percentage'].sum()
            df = df[df['percentage'] >= threshold]
            other_row = pd.DataFrame([{'category': 'Other', 'percentage': other_sum}])
            df = pd.concat([df, other_row], ignore_index=True)
        
        
        # Sort by percentage for better visualization
        df = df.sort_values('percentage', ascending=False)
        
        # Create pie chart
        plt.figure(figsize=(10, 8))
        wedges, texts, autotexts = plt.pie(df["percentage"], labels=df["category"], autopct="%1.1f%%", startangle=90, shadow=True, pctdistance=0.85) # Adjust pctdistance
        plt.axis("equal")
        plt.title("Token Distribution")
        
        # Improve label readability if needed
        plt.setp(autotexts, size=8, weight="bold", color="white")
        plt.setp(texts, size=10)
        
        plt.tight_layout()
        
        # Save the figure
        # Use category name or timestamp for filename part
        filename_part = distribution[0].get('category', 'dist') if distribution else 'dist'
        image_path = os.path.join(REPORTS_DIR, f"token_distribution_{filename_part}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        plt.savefig(image_path)
        plt.close()
        
        return image_path # Return full path
    except Exception as e:
        logger.error(f"Error in generate_token_distribution_chart: {e}")
        plt.close()
        return None

def generate_flow_visualization(data):
    """
    Generate a money flow visualization
    
    Args:
        data (dict): Money flow data including address, interactions
    
    Returns:
        str: Path to the saved visualization or None on error
    """
    try:
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add main address
        main_address = data.get("address", "Unknown")
        main_node_label = main_address[:6] + "..." + main_address[-4:]
        G.add_node(main_address, type="main", label=main_node_label)
        
        # Add mixer nodes and edges (limit for clarity)
        for i, mixer in enumerate(data.get("mixer_interactions", [])[:10]):
            mixer_name = mixer.get("name", f"Mixer_{i}")
            mixer_addr = mixer.get("address", mixer_name) # Use address if available
            label = mixer_name[:10] + ("..." if len(mixer_name)>10 else "")
            G.add_node(mixer_addr, type="mixer", label=label)
            # Assume flow is both ways for mixers unless specified
            G.add_edge(main_address, mixer_addr, weight=mixer.get("volume_usd", 1), type="mixer_out")
            G.add_edge(mixer_addr, main_address, weight=mixer.get("volume_usd", 1), type="mixer_in") # Simplified
        
        # Add exchange nodes and edges (limit for clarity)
        for i, exchange in enumerate(data.get("exchange_interactions", [])[:10]):
            exchange_name = exchange.get("name", f"Exchange_{i}")
            exchange_addr = exchange.get("address", exchange_name) # Use address if available
            label = exchange_name[:10] + ("..." if len(exchange_name)>10 else "")
            G.add_node(exchange_addr, type="exchange", label=label)
            # Assume flow is both ways for exchanges unless specified
            G.add_edge(main_address, exchange_addr, weight=exchange.get("volume_usd", 1), type="exchange_out")
            G.add_edge(exchange_addr, main_address, weight=exchange.get("volume_usd", 1), type="exchange_in") # Simplified
        
        # Add cross-chain transfer nodes (simplified)
        for i, transfer in enumerate(data.get("cross_chain_transfers", [])[:5]):
             dest_chain = transfer.get("destination_chain", f"Chain_{i}")
             label = dest_chain[:10] + ("..." if len(dest_chain)>10 else "")
             G.add_node(dest_chain, type="chain", label=label)
             G.add_edge(main_address, dest_chain, weight=transfer.get("volume_usd", 1), type="cross_chain")
        
        
        # Create figure
        plt.figure(figsize=(14, 10))
        
        # Create positions
        pos = nx.spring_layout(G, k=0.7, iterations=70)
        
        # Draw nodes
        node_colors = []
        node_sizes = []
        labels = {}
        for node, node_data in G.nodes(data=True): # Renamed inner variable
            labels[node] = node_data.get("label", node)
            node_type = node_data.get("type")
            if node_type == "main":
                node_colors.append("purple")
                node_sizes.append(2000)
            elif node_type == "mixer":
                node_colors.append("orange")
                node_sizes.append(1200)
            elif node_type == "exchange":
                node_colors.append("cyan")
                node_sizes.append(1200)
            elif node_type == "chain":
                node_colors.append("lightgreen")
                node_sizes.append(1000)
            else:
                node_colors.append("grey")
                node_sizes.append(500)
        
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9)
        
        # Draw edges
        edges = G.edges(data=True)
        max_weight = max((edge_data.get("weight", 0) for _, _, edge_data in edges), default=1) # Renamed inner variable
        min_weight_display = 0.5
        max_weight_display = 6.0
        weights = [min_weight_display + (max_weight_display - min_weight_display) * (edge_data.get("weight", 0) / max_weight)
                   for _, _, edge_data in edges]
        
        nx.draw_networkx_edges(G, pos, width=weights, alpha=0.6, edge_color="black", arrows=True, arrowsize=20, connectionstyle='arc3,rad=0.1')
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_family="sans-serif")
        
        # Add legend
        legend_elements = [Line2D([0], [0], marker='o', color='w', label='Target Address', markerfacecolor='purple', markersize=12),
                           Line2D([0], [0], marker='o', color='w', label='Mixer', markerfacecolor='orange', markersize=12),
                           Line2D([0], [0], marker='o', color='w', label='Exchange', markerfacecolor='cyan', markersize=12),
                           Line2D([0], [0], marker='o', color='w', label='Cross-Chain', markerfacecolor='lightgreen', markersize=12)]
        plt.legend(handles=legend_elements, loc='best')
        
        plt.title(f"Money Flow Visualization for {main_node_label} (Sampled)")
        plt.axis('off')
        plt.tight_layout()
        
        # Save the figure
        main_address = data.get("address", "Unknown")
        target_part = main_address[:8] if main_address != "Unknown" else datetime.now().strftime('%Y%m%d%H%M%S')
        image_path = os.path.join(REPORTS_DIR, f"money_flow_{target_part}.png")
        plt.savefig(image_path)
        plt.close()
        
        return image_path # Return full path
    
    except Exception as e:
        logger.error(f"Error in generate_flow_visualization: {e}") # Added logging
        plt.close()
        return None

def generate_timeline_visualization(transfers):
    """
    Generate a timeline visualization of transfers
    
    Args:
        transfers (list): List of transfer data (dicts with 'timestamp', 'volume_usd', 'type')
    
    Returns:
        str: Path to the saved visualization or None on error
    """
    try:
        if not transfers:
            logger.warning("No transfer data provided for timeline visualization.")
            return None
        
        df = pd.DataFrame(transfers)
        
        # Ensure required columns exist and convert timestamp
        if 'timestamp' not in df.columns or 'volume_usd' not in df.columns:
             logger.error("Timeline data missing 'timestamp' or 'volume_usd'.")
             return None
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        df['volume_usd'] = pd.to_numeric(df['volume_usd'], errors='coerce').fillna(0)
        df = df.sort_values('timestamp')
        
        if df.empty:
            logger.warning("No valid timestamp data found for timeline.")
            return None
        
        # Create plot
        plt.figure(figsize=(12, 6))
        
        # Use different markers/colors for different types if 'type' column exists
        if 'type' in df.columns:
            colors = {'mixer': 'orange', 'exchange': 'cyan', 'cross_chain': 'green', 'other': 'grey'}
            markers = {'mixer': 'X', 'exchange': 's', 'cross_chain': '^', 'other': '.'}
            for t_type, group in df.groupby('type'):
                plt.scatter(group['timestamp'], group['volume_usd'],
                            label=t_type.replace('_', ' ').title(),
                            color=colors.get(t_type, 'grey'),
                            marker=markers.get(t_type, '.'),
                            s=50, alpha=0.7) # Adjust size and alpha
            plt.legend()
        else:
            plt.scatter(df['timestamp'], df['volume_usd'], s=50, alpha=0.7)
        
        plt.xlabel("Time")
        plt.ylabel("Transaction Volume (USD)")
        plt.title("Transaction Timeline")
        plt.yscale('log') # Use log scale if volumes vary widely
        plt.grid(True, which="both", ls="--", alpha=0.5)
        plt.tight_layout()
        
        # Save the figure
        # Use a generic name or derive from data if possible
        image_path = os.path.join(REPORTS_DIR, f"timeline_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        plt.savefig(image_path)
        plt.close()
        
        return image_path # Return full path
    
    except Exception as e:
        logger.error(f"Error in generate_timeline_visualization: {e}") # Added logging
        plt.close()
        return None

def generate_liquidity_chart(liquidity_history):
    """
    Generate a liquidity chart
    
    Args:
        liquidity_history (list): Liquidity history data (dicts with 'timestamp', 'liquidity_usd')
    
    Returns:
        str: Path to the saved chart or None on error
    """
    try:
        if not liquidity_history:
            logger.warning("No liquidity history provided for chart.")
            return None
        
        df = pd.DataFrame(liquidity_history)
        if 'timestamp' not in df.columns or 'liquidity_usd' not in df.columns:
            logger.error("Liquidity history missing 'timestamp' or 'liquidity_usd'.")
            return None
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['liquidity_usd'] = pd.to_numeric(df['liquidity_usd'], errors='coerce')
        df = df.dropna().sort_values('timestamp')
        
        if df.empty:
            logger.warning("No valid data points for liquidity chart.")
            return None
        
        plt.figure(figsize=(10, 5))
        plt.plot(df['timestamp'], df['liquidity_usd'], marker='.', linestyle='-')
        plt.xlabel("Time")
        plt.ylabel("Liquidity (USD)")
        plt.title("Liquidity History")
        plt.grid(True, alpha=0.5)
        plt.tight_layout()
        
        # Use a generic name or derive from data if possible
        image_path = os.path.join(REPORTS_DIR, f"liquidity_chart_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        plt.savefig(image_path)
        plt.close()
        return image_path # Return full path
    
    except Exception as e:
        logger.error(f"Error in generate_liquidity_chart: {e}") # Added logging
        plt.close()
        return None

def generate_price_chart(price_history):
    """
    Generate a price chart
    
    Args:
        price_history (list): Price history data (dicts with 'timestamp', 'price_usd')
    
    Returns:
        str: Path to the saved chart or None on error
    """
    try:
        if not price_history:
            logger.warning("No price history provided for chart.")
            return None
        
        df = pd.DataFrame(price_history)
        if 'timestamp' not in df.columns or 'price_usd' not in df.columns:
            logger.error("Price history missing 'timestamp' or 'price_usd'.")
            return None
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['price_usd'] = pd.to_numeric(df['price_usd'], errors='coerce')
        df = df.dropna().sort_values('timestamp')
        
        if df.empty:
            logger.warning("No valid data points for price chart.")
            return None
        
        plt.figure(figsize=(10, 5))
        plt.plot(df['timestamp'], df['price_usd'], marker='.', linestyle='-', color='green')
        plt.xlabel("Time")
        plt.ylabel("Price (USD)")
        plt.title("Token Price History")
        plt.yscale('log') # Often useful for price charts
        plt.grid(True, which="both", ls="--", alpha=0.5)
        plt.tight_layout()
        
        # Use a generic name or derive from data if possible
        image_path = os.path.join(REPORTS_DIR, f"price_chart_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        plt.savefig(image_path)
        plt.close()
        return image_path # Return full path
    
    except Exception as e:
        logger.error(f"Error in generate_price_chart: {e}") # Added logging
        plt.close()
        return None

def generate_holder_distribution_chart(holders):
    """
    Generate a holder distribution chart (e.g., top N holders pie chart)
    
    Args:
        holders (list): Holder data (list of dicts with 'address', 'percentage')
    
    Returns:
        str: Path to the saved chart or None on error
    """
    try:
        if not holders:
            logger.warning("No holder data provided for distribution chart.")
            return None
        
        df = pd.DataFrame(holders)
        if 'address' not in df.columns or 'percentage' not in df.columns:
             logger.error("Holder data missing 'address' or 'percentage'.")
             return None
        
        df['percentage'] = pd.to_numeric(df['percentage'], errors='coerce')
        df = df.dropna(subset=['percentage']).sort_values('percentage', ascending=False)
        
        if df.empty:
            logger.warning("No valid percentage data for holder chart.")
            return None
        
        # Take top N holders + 'Other'
        top_n = 10
        df_top = df.head(top_n).copy()
        other_percentage = df.iloc[top_n:]['percentage'].sum()
        
        if other_percentage > 0.1: # Only add 'Other' if it's significant
             other_row = pd.DataFrame([{'address': 'Other Holders', 'percentage': other_percentage}])
             df_top = pd.concat([df_top, other_row], ignore_index=True)
        
        # Shorten addresses for labels
        df_top['label'] = df_top['address'].apply(lambda x: x[:6] + '...' + x[-4:] if x != 'Other Holders' else x)
        
        plt.figure(figsize=(10, 8))
        wedges, texts, autotexts = plt.pie(df_top["percentage"], labels=df_top["label"], autopct="%1.1f%%", startangle=90, pctdistance=0.85)
        plt.axis("equal")
        plt.title(f"Top {top_n} Holder Distribution")
        plt.setp(autotexts, size=8, weight="bold", color="white")
        plt.setp(texts, size=9)
        plt.tight_layout()
        
        # Use a generic name or derive from data if possible
        image_path = os.path.join(REPORTS_DIR, f"holder_distribution_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        plt.savefig(image_path)
        plt.close()
        return image_path # Return full path
    
    
    except Exception as e:
        logger.error(f"Error in generate_holder_distribution_chart: {e}") # Added logging
        plt.close()
        return None

# --- Placeholder functions for missing visualizations ---

def generate_volume_chart(volume_history):
    """Placeholder for generating mixer volume chart"""
    logger.warning("generate_volume_chart is not implemented. Returning None.")
    # Add basic plotting logic here if needed later
    # Similar to generate_price_chart or generate_liquidity_chart
    try:
        if not volume_history: return None
        df = pd.DataFrame(volume_history)
        if 'timestamp' not in df.columns or 'volume_usd' not in df.columns: return None
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['volume_usd'] = pd.to_numeric(df['volume_usd'], errors='coerce')
        df = df.dropna().sort_values('timestamp')
        if df.empty: return None

        plt.figure(figsize=(10, 5))
        plt.plot(df['timestamp'], df['volume_usd'], marker='.', linestyle='-', color='orange')
        plt.xlabel("Time")
        plt.ylabel("Volume (USD)")
        plt.title("Mixer Volume History")
        plt.yscale('log')
        plt.grid(True, which="both", ls="--", alpha=0.5)
        plt.tight_layout()
        image_path = os.path.join(REPORTS_DIR, f"mixer_volume_chart_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        plt.savefig(image_path)
        plt.close()
        return image_path # Return full path
    except Exception as e:
        logger.error(f"Error in placeholder generate_volume_chart: {e}")
        plt.close()
        return None


def generate_user_graph(users):
    """Placeholder for generating mixer user graph"""
    logger.warning("generate_user_graph is not implemented. Returning None.")
    # Add basic graph logic here if needed later
    # Similar to generate_flow_visualization but focusing on users
    return None

def generate_dusting_timeline(dusting_attempts):
    """Generate a timeline visualization of dusting/poisoning attempts"""
    logger.info("Generating dusting timeline visualization...")
    # Similar to generate_timeline_visualization but specific for dusting
    try:
        if not dusting_attempts:
            logger.warning("No dusting attempt data provided for timeline.")
            return None

        df = pd.DataFrame(dusting_attempts)
        if 'timestamp' not in df.columns:
             logger.error("Dusting timeline data missing 'timestamp'.")
             return None
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp']).sort_values('timestamp')
        # Add a small constant value for plotting if volume is 0 or missing
        df['plot_value'] = df.get('volume_usd', 0.01) # Use volume if available, else small value
        df.loc[df['plot_value'] <= 0, 'plot_value'] = 0.01


        if df.empty:
            logger.warning("No valid timestamp data found for dusting timeline.")
            return None

        plt.figure(figsize=(12, 6))
        colors = {'poisoning': 'red', 'dust_campaign': 'orange', 'dust': 'grey'}
        markers = {'poisoning': 'x', 'dust_campaign': 's', 'dust': '.'}

        for t_type, group in df.groupby('type'):
            plt.scatter(group['timestamp'], group['plot_value'],
                        label=t_type.replace('_', ' ').title(),
                        color=colors.get(t_type, 'grey'),
                        marker=markers.get(t_type, '.'),
                        s=60, alpha=0.8)
        plt.legend()

        plt.xlabel("Time")
        plt.ylabel("Indicator (Log Scale)") # Y-axis doesn't represent volume directly
        plt.title("Dusting and Poisoning Attempt Timeline")
        plt.yscale('log')
        plt.grid(True, which="both", ls="--", alpha=0.5)
        plt.tight_layout()

        image_path = os.path.join(REPORTS_DIR, f"dusting_timeline_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        plt.savefig(image_path)
        plt.close()
        return image_path # Return full path
    except Exception as e:
        logger.error(f"Error in generate_dusting_timeline: {e}")
        plt.close()
        return None


def generate_relationship_graph(target_address, relationships):
    """Placeholder for generating address relationship graph"""
    logger.warning("generate_relationship_graph is not implemented. Returning None.")
    # Add basic graph logic here if needed later
    # Similar to generate_flow_visualization but showing relationships/similarity
    return None

# --- End Placeholder functions ---

def create_default_templates():
    """Creates default markdown template files if they don't exist."""
    logger.info(f"Checking for report templates in {TEMPLATES_DIR}...")
    templates = {
        "ico_report.md": """# ICO Analysis Report: {token_name} ({token_symbol})

**Report Generated:** {timestamp}

## Summary
- **Token:** {token_name} ({token_symbol})
- **Risk Level:** {risk_level}
- **Risk Score:** {risk_score}/100

## Token Information
- **Name:** {token_name}
- **Symbol:** {token_symbol}
- **Current Price:** {token_price}
- **Market Cap:** {market_cap}

## Creator Information
- **Creator Wallet:** {creator_wallet}
- **Identified Team Wallets:**
{team_wallets}

## Funding Flow
- **Total Raised (Estimated):** {total_raised}
- **Investor Count (Estimated):** {investor_count}

{funding_flow_image}

## Token Distribution
{token_distribution_image}

## Suspicious Patterns Detected
{suspicious_patterns}

## Risk Assessment Details
- **Overall Risk Level:** {risk_level}
- **Overall Risk Score:** {risk_score}/100
- **Key Risk Factors:**
{risk_factors}

## Conclusion
This report provides an automated analysis based on available data. Further investigation may be required for a definitive assessment.
""",

        "laundering_report.md": """# Money Laundering Analysis Report

**Report Generated:** {timestamp}

## Summary
- **Subject Address:** {address}
- **Risk Level:** {risk_level}
- **Risk Score:** {risk_score}/100

## Key Findings

### Detected Techniques
{detected_techniques}

### Mixer Interactions
{mixer_interactions}

### Cross-Chain Transfers
{cross_chain_transfers}

### Exchange Interactions
{exchange_interactions}

### Identified Laundering Routes
{money_laundering_routes}

## Visualizations

### Money Flow Graph (Sampled)
{flow_graph_image}

### Transaction Timeline
{timeline_image}

## Risk Assessment Details
- **Overall Risk Level:** {risk_level}
- **Overall Risk Score:** {risk_score}/100
- **Key Risk Factors:**
{risk_factors}

## Conclusion
This report provides an automated analysis based on available data. Further investigation may be required for a definitive assessment.
""",

        "rugpull_report.md": """# Rugpull Risk Analysis Report

**Report Generated:** {timestamp}

## Summary
- **Token:** {token_name} ({token_symbol})
- **Mint Address:** {token_mint}
- **Risk Level:** {risk_level}
- **Risk Score:** {risk_score}/100

## Token Information
- **Name:** {token_name}
- **Symbol:** {token_symbol}
- **Creator:** {token_creator}
- **Creation Date:** {creation_date}
- **Total Supply:** {total_supply}
- **Current Price:** {current_price}

## Liquidity Analysis
- **Current Liquidity (USD):** {liquidity_usd}
- **Liquidity Locked:** {liquidity_locked_percentage}
- **Lock Expiry:** {lock_expiry}

## Creator Background
- **Previous Tokens Created:**
{creator_previous_tokens}

## Insider Wallets / Team Holdings
{insider_wallets}

## Detected Rugpull Methods / Warning Signs
{detected_methods}

## Visualizations

### Token Price History
{token_price_chart}

### Liquidity History
{liquidity_chart}

### Holder Distribution (Top Holders)
{holder_distribution_chart}

## Risk Assessment Details
- **Overall Risk Level:** {risk_level}
- **Overall Risk Score:** {risk_score}/100
- **Key Risk Factors:**
{risk_factors}

## Conclusion
This report provides an automated analysis based on available data. Further investigation may be required for a definitive assessment.
""",

        "mixer_report.md": """# Mixer Analysis Report

**Report Generated:** {timestamp}

## Summary
- **Mixer Address:** {mixer_address}
- **Risk Level:** {risk_level}
- **Risk Score:** {risk_score}/100

## Activity Summary
- **First Seen:** {first_seen}
- **Last Seen:** {last_seen}
- **Total Volume (USD):** {total_volume}
- **Transaction Count:** {transaction_count}
- **Unique Users (Estimated):** {unique_users}

## Top Users (Sampled)
{top_users}

## Visualizations

### Volume History
{volume_chart}

### User Relationship Graph (Conceptual)
{user_graph}

## Behavioral Patterns Detected
{patterns}

## Risk Assessment Details
- **Overall Risk Level:** {risk_level}
- **Overall Risk Score:** {risk_score}/100
- **Key Risk Factors:**
{risk_factors}

## Conclusion
This report provides an automated analysis based on available data. Further investigation may be required for a definitive assessment.
""",

        "dusting_report.md": """# Address Dusting Analysis Report

**Report Generated:** {timestamp}

## Summary
- **Target Address:** {target_address}
- **Risk Level:** {risk_level}
- **Risk Score:** {risk_score}/100

## Attack Summary
- **Total Dusting/Poisoning Incidents:** {dusting_attempts_count}
- **First Incident:** {first_attempt}
- **Last Incident:** {last_attempt}

## Detected Incidents Targeting Address
{dusting_attempts}

## Related Address Analysis (Placeholder)
{address_relationships}

## Victim Activity Patterns (Placeholder)
{victim_patterns}

## Visualizations

### Dusting/Poisoning Timeline
{dusting_timeline}

### Address Relationship Graph (Conceptual)
{relationship_graph}

## Risk Assessment Details
- **Overall Risk Level:** {risk_level}
- **Overall Risk Score:** {risk_score}/100
- **Key Risk Factors:**
{risk_factors}

## Conclusion
This report provides an automated analysis based on available data. Be cautious when interacting with unknown tokens or addresses. Verify counterparty addresses carefully before sending transactions.
"""
    }

    for name, content in templates.items():
        template_path = os.path.join(TEMPLATES_DIR, name)
        if not os.path.exists(template_path):
            try:
                # Ensure directory exists before writing
                os.makedirs(os.path.dirname(template_path), exist_ok=True)
                with open(template_path, "w", encoding='utf-8') as f: # Added encoding
                    f.write(content)
                logger.info(f"Created default template: {name}")
            except IOError as e:
                logger.error(f"Failed to create default template {name}: {e}")


class ReportGenerator:
    """
    Class wrapper for report generation functions.
    Allows passing instance-specific configurations if needed later.
    """
    def generate_report(self, target, data, report_type):
        # Find the specific data block for the report type if 'data' contains multiple results
        report_data = data.get(report_type) if isinstance(data.get(report_type), dict) else data
        return generate_report(target, report_data, report_type) # Call module-level function

    def generate_ico_report(self, target, data):
        return generate_ico_report(target, data) # Call module-level function

    def generate_laundering_report(self, target, data):
        return generate_laundering_report(target, data) # Call module-level function

    def generate_rugpull_report(self, target, data):
        return generate_rugpull_report(target, data) # Call module-level function

    def generate_mixer_report(self, target, data):
        return generate_mixer_report(target, data) # Call module-level function

    def generate_dusting_report(self, target, data):
        return generate_dusting_report(target, data) # Call module-level function

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)

    # Create report templates directory if it doesn't exist
    create_default_templates()

    # Example usage (can be removed or commented out)
    print(f"Reports will be saved in: {REPORTS_DIR}")
    print(f"Templates are expected in: {TEMPLATES_DIR}")

    # Example: Test dusting report generation
    test_target_address = "TestDustAddr1234567890abcdefghijKLMNOP"
    test_dusting_data = {
        "address": test_target_address,
        "risk_assessment": {
            "risk_score": 75.5,
            "risk_level": "high",
            "risk_factors": [
                {"factor": "address_poisoning", "description": "Detected 3 address poisoning attempts"},
                {"factor": "incoming_dust", "description": "Received 15 dust transactions"},
                {"factor": "multiple_dust_senders", "description": "Dust received from 5 different addresses"}
            ],
            "poisoning_attempts": 3, # Count
            "dust_transactions": 15, # Count
            # "poisoning_attempts_details": [...] # Details might be here or top level
        },
         "poisoning_attempts": [ # Example top-level details
             {"poisoning_address": "FakeCounterPartyAddrSimilarToRealOne123", "legitimate_counterparty": "RealCounterPartyAddrVeryDifferent12345", "similarity": {"visual_similarity": 0.85}, "transaction_count": 2, "first_seen": "2023-10-26T10:00:00Z", "last_seen": "2023-10-27T11:00:00Z"},
             {"poisoning_address": "AnotherFakeAddrSimilarToRealOne987", "legitimate_counterparty": "RealCounterPartyAddrVeryDifferent12345", "similarity": {"visual_similarity": 0.88}, "transaction_count": 1, "first_seen": "2023-10-28T09:30:00Z", "last_seen": "2023-10-28T09:30:00Z"},
        ],
        "dusting_campaigns": [
            {"sender_address": "DustSenderCampaign1Addr", "dust_transaction_count": 10, "common_amount": 0.00001, "first_seen": "2023-10-20T08:00:00Z", "last_seen": "2023-10-25T09:00:00Z", "part_of_larger_campaign": True, "campaign_size": 500},
            {"sender_address": "DustSenderSingleTxAddr", "dust_transaction_count": 1, "common_amount": 0.00005, "first_seen": "2023-10-29T14:00:00Z", "last_seen": "2023-10-29T14:00:00Z", "part_of_larger_campaign": False},
        ],
        # "address_relationships": [
        #     {"address": "RelatedAddrPossiblyAttacker", "relationship_type": "Suspicious Sender", "similarity_score": 0.1}
        # ],
        # "victim_patterns": {"activity_level": "medium", "common_tokens": ["USDC", "SOL"]},
        "analysis_timeframe": "30 days",
        "timestamp": "2023-10-28T12:00:00Z"
    }
    print("\nTesting Dusting Report Generation...")
    # Use the class instance
    generator = ReportGenerator()
    report_path = generator.generate_dusting_report(test_target_address, test_dusting_data)
    if report_path:
        print(f"Dusting report generated: {report_path}")
    else:
        print("Dusting report generation failed.")

    # Example: Test ICO report generation
    test_token_mint = "TestICOtokEnMint1234567890abcdefghijkl"
    test_ico_data = {
        "token_data": {"name": "TestICO", "symbol": "TICO", "price_usd": 0.5, "market_cap": 5000000, "distribution": [{"category": "Team", "percentage": 20}, {"category": "Investors", "percentage": 60}, {"category": "Reserve", "percentage": 20}]},
        "creator_data": {"address": "CreatorWalletAddrICOtest", "team_wallets": ["TeamWallet1", "TeamWallet2"]},
        "funding_flow": {"total_raised_usd": 1000000, "investor_count": 500, "investors": [{"address": "Investor1", "amount_usd": 1000}, {"address": "Investor2", "amount_usd": 5000}], "fund_destinations": [{"address": "ExchangeDepositAddr", "amount_usd": 200000}]},
        "risk_assessment": {"risk_level": "Medium", "risk_score": 55, "risk_factors": ["High team allocation", "Funds moved quickly to exchange"]},
        "suspicious_patterns": {"detected_patterns": [{"pattern": "Large Transfer Post-ICO", "description": "Large amount sent to CEX shortly after raise.", "confidence": 0.7}]}
    }
    print("\nTesting ICO Report Generation...")
    report_path_ico = generator.generate_ico_report(test_token_mint, test_ico_data)
    if report_path_ico:
        print(f"ICO report generated: {report_path_ico}")
    else:
        print("ICO report generation failed.")
