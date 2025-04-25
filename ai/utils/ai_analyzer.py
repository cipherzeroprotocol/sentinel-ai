"""
AI Analysis Engine for performing security analysis using AI models
"""
import json
import logging
import os
import sys
import time
import warnings
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Use absolute imports assuming the script is run within the package structure
# or the project root is in PYTHONPATH
from sentinel.ai.utils.data_formatter import DataFormatter
from sentinel.ai.utils.result_parser import ResultParser
from sentinel.data.config import OPENAI_API_KEY

# Add the project root to the Python path - This might be needed if running the script directly
# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# if PROJECT_ROOT not in sys.path:
#     sys.path.insert(0, PROJECT_ROOT)


logger = logging.getLogger(__name__)

# Import OpenAI safely
try:
    # Use the new import structure
    from openai import OpenAI, AuthenticationError, RateLimitError
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not installed. AI analysis capabilities will be limited. Install with: pip install openai")
    OPENAI_AVAILABLE = False
    OpenAI, AuthenticationError, RateLimitError = None, None, None # Define placeholders

# Get API key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY and OPENAI_AVAILABLE: # Check OPENAI_AVAILABLE here
    logger.warning("OPENAI_API_KEY not found in environment variables. AI Analyzer will not function. Please set the OPENAI_API_KEY environment variable.")

class AIAnalyzer:
    """
    AI-powered analysis tools for Sentinel.
    Uses OpenAI's API for advanced analysis when available.
    Falls back to rule-based analysis when API is unavailable.
    """
    
    def __init__(self):
        """Initialize the AI analyzer with optional API key."""
        self.api_key = OPENAI_API_KEY
        self.client = None
        self.ai_available = False
        self.model = "gpt-4o-mini" # Define a default model

        # Check if API key is available and OpenAI is installed
        if not self.api_key:
            # Warning already issued above
            pass
        elif not OPENAI_AVAILABLE:
            # Warning already issued above
            pass
        else:
            # Initialize OpenAI client using the new method
            try:
                self.client = OpenAI(api_key=self.api_key)
                # Optional: Test connection with a simple request like listing models
                # self.client.models.list()
                self.ai_available = True
                logger.info(f"AI analysis capabilities initialized successfully using model {self.model}")
            except AuthenticationError as auth_err:
                logger.error(f"OpenAI Authentication Error during initialization: {auth_err}. Check your API key configuration.")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}")

        self.data_formatter = DataFormatter()
        self.result_parser = ResultParser()
        
        # Load prompt templates
        self.prompt_templates = {}
        self._load_prompt_templates()
    
    def _load_prompt_templates(self):
        """
        Load prompt templates from files in the 'prompts' subdirectory.
        """
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts") # Correct path relative to this file

        # Ensure template directory exists
        os.makedirs(template_dir, exist_ok=True)

        # Define template files mapping analysis_type to filename
        template_files = {
            "ico": "ico_analysis.txt",
            "money_laundering": "money_laundering_detection.txt", # Corrected key and filename
            "rugpull": "rugpull_analysis.txt",
            "mixer": "mixer_analysis.txt",
            "dusting": "dusting_analysis.txt",
            # Add other types if needed, e.g., 'wallet', 'transaction'
            "wallet": "wallet_profiling.txt",
            "transaction": "transaction_analysis.txt",
            "generic": "generic_analysis.txt" # Added generic template file
        }

        # Load templates from files, or use defaults and create files
        for analysis_type, filename in template_files.items():
            template_path = os.path.join(template_dir, filename)

            if os.path.exists(template_path):
                try:
                    with open(template_path, "r", encoding='utf-8') as file: # Added encoding
                        self.prompt_templates[analysis_type] = file.read()
                    logger.info(f"Loaded prompt template for {analysis_type} analysis from {filename}")
                except Exception as e:
                    logger.error(f"Error loading prompt template for {analysis_type} from {filename}: {str(e)}")
                    # Fallback to default template if loading fails
                    self.prompt_templates[analysis_type] = self._get_default_template(analysis_type)
            else:
                # Create template file with default template
                try:
                    default_template = self._get_default_template(analysis_type)
                    # Ensure directory exists before writing
                    os.makedirs(os.path.dirname(template_path), exist_ok=True)
                    with open(template_path, "w", encoding='utf-8') as file: # Added encoding
                        file.write(default_template)
                    self.prompt_templates[analysis_type] = default_template
                    logger.info(f"Created default prompt template file for {analysis_type} analysis: {filename}")
                except Exception as e:
                    logger.error(f"Error creating prompt template file for {analysis_type} ({filename}): {str(e)}")
                    # Use default template in memory even if file creation fails
                    self.prompt_templates[analysis_type] = self._get_default_template(analysis_type)
    
    def _get_default_template(self, analysis_type):
        """
        Get default prompt template for a specific analysis type
        
        Args:
            analysis_type (str): Type of analysis
            
        Returns:
            str: Default prompt template
        """
        if analysis_type == "ico":
            return """
# ICO and Token Launch Analysis

## Context
You are an AI expert in blockchain security and token analysis. Your task is to analyze the information provided about this token launch or ICO (Initial Coin Offering) and assess its legitimacy and risk factors.

## Data
{data}

## Analysis Instructions
Please provide a comprehensive analysis of this Initial Coin Offering (ICO) or token launch based on the data provided. 

Your analysis should be structured as follows:

### Token Information
- Provide a summary of the basic token details (name, symbol, supply, etc.)
- Evaluate the token structure and any technical concerns
- Assess if the token's characteristics are appropriate for its stated purpose

### Creator Profile
- Analyze the creator wallet's history and reputation
- Evaluate the team's background and credibility
- Identify any previous projects by the same creator(s) and their outcomes

### Funding Flow
- Analyze how funds were raised and distributed
- Evaluate the fairness of token distribution
- Identify any suspicious movement of funds during or after the ICO

### Risk Assessment
- Identify specific red flags and concerns
- Evaluate the likelihood of a rug pull or scam
- Compare this ICO to known legitimate and fraudulent projects

### Conclusion
- Provide an overall assessment of the ICO/token
- Assign a risk rating on a scale of 1-10 (where 10 is extremely high risk)
- Offer specific recommendations for investors or investigators

Be specific about patterns you observe and support your conclusions with the data provided. Identify potential security risks, fraudulent activity, or legitimate characteristics based on your analysis.
"""
        elif analysis_type == "money_laundering":
            # Renamed to match the key used in _load_prompt_templates
            return """
# Money Laundering Detection Analysis

## Context
You are an AI expert in blockchain forensics, specializing in detecting money laundering patterns. Your task is to analyze the blockchain data provided and identify potential money laundering activities, techniques, and risk indicators.

## Data
{data}

## Analysis Instructions
Please provide a comprehensive analysis of potential money laundering activity based on the data provided.

Your analysis should be structured as follows:

### Transaction Patterns
- Identify suspicious transaction patterns (layering, smurfing, round-trip transactions, etc.)
- Explain why these patterns are concerning from an anti-money laundering perspective
- Highlight any techniques used to obfuscate the flow of funds

### Flow of Funds
- Trace the path of funds through the network
- Identify the source and destination entities when possible
- Quantify the total value of suspicious transactions
- Visualize or describe the multi-hop transaction flow

### Counterparties
- Analyze the entities involved in suspicious transactions
- Identify any known high-risk entities (exchanges, mixers, etc.)
- Evaluate relationships between the counterparties

### Risk Assessment
- Evaluate the likelihood that this activity represents money laundering
- Assess the sophistication of the techniques used
- Identify which money laundering stage this activity represents (placement, layering, integration)
- Compare to known money laundering typologies

### Conclusion
- Provide an overall assessment of the suspected money laundering activity
- Assign a confidence rating on a scale of 1-10 for your assessment
- Recommend next investigative steps or areas for further analysis

Be specific about techniques you identify (layering, smurfing, etc.) and support your conclusions with the data provided. Focus on patterns that distinguish legitimate financial activity from money laundering operations.
"""
        elif analysis_type == "rugpull":
            return """
# Rugpull Risk Analysis

## Context
You are an AI expert in blockchain security, specializing in token rugpull detection. Your task is to analyze the provided token data and evaluate the likelihood of a rugpull scam, where developers abandon the project after withdrawing liquidity or otherwise defrauding investors.

## Data
{data}

## Analysis Instructions
Please provide a comprehensive analysis of the rugpull risk for this token based on the data provided.

Your analysis should be structured as follows:

### Token Structure
- Analyze the token design, including supply, authorities, and token economics
- Evaluate the mint and freeze authorities (if applicable)
- Assess any suspicious features in the token's contract design
- Identify any backdoors or problematic functions

### Creator Profile
- Evaluate the creator's history and reputation
- Analyze previous projects by the same creator(s) and their outcomes
- Assess the team's transparency and credibility
- Identify connections to previous rugpulls or scams

### Liquidity Analysis
- Assess the token's liquidity and market depth
- Evaluate liquidity locking mechanisms and timeframes
- Analyze the distribution of LP tokens
- Identify concentration risks in liquidity provision

### Warning Signs
- Identify specific red flags that suggest rugpull risk
- Evaluate token distribution for signs of insider concentration
- Analyze transaction patterns that may indicate preparation for a rugpull
- Assess marketing tactics and community engagement for scam indicators

### Conclusion
- Provide an overall assessment of rugpull risk
- Assign a rugpull risk rating on a scale of 1-10
- Estimate the likelihood and potential timeframe for a rugpull
- Offer recommendations for investors or investigators

Be specific about warning signs and support your conclusions with the data provided. Compare this token's characteristics to known legitimate projects and previous rugpulls to provide context for your assessment.
"""
        elif analysis_type == "mixer":
            return """
# Mixing Service Analysis

## Context
You are an AI expert in blockchain forensics, specializing in identifying and analyzing cryptocurrency mixing services. Your task is to analyze the provided blockchain data and determine if the address or service in question is functioning as a mixer (also called a tumbler or mixing service).

## Data
{data}

## Analysis Instructions
Please provide a comprehensive analysis of this potential mixing service based on the data provided.

Your analysis should be structured as follows:

### Operational Pattern
- Describe how this mixing service appears to operate
- Identify the specific mixing techniques being used
- Analyze the transaction structure and mechanics
- Assess the level of anonymity provided

### User Behavior
- Analyze patterns in how users interact with the service
- Identify typical deposit and withdrawal behaviors
- Assess user profiles and characteristics
- Determine if there are recurring users or one-time users

### Volume Analysis
- Evaluate transaction volumes and frequency
- Analyze the denomination patterns of transactions
- Assess temporal patterns (time of day, day of week, seasonal)
- Identify growth or decline trends in usage

### Comparison
- Compare this service to known mixing services
- Evaluate how sophisticated this mixer is relative to others
- Identify unique features or innovations in this mixing service
- Assess if this appears to be a custom or widely-used mixing protocol

### Conclusion
- Provide your assessment of whether this is a mixing service
- Assign a confidence level from 1-10 on your determination
- Estimate the scale and impact of this mixing operation
- Recommend further investigative approaches

Be specific about mixing techniques identified and support your conclusions with the data provided. Focus on differentiating legitimate privacy-preserving behaviors from illicit money laundering operations.
"""
        elif analysis_type == "dusting":
            return """
# Address Dusting Attack Analysis

## Context
You are an AI expert in blockchain security, specializing in address dusting attacks and address poisoning threats. Your task is to analyze the provided blockchain data and determine if the activity represents a dusting attack, who is behind it, and what the purpose might be.

## Data
{data}

## Analysis Instructions
Please provide a comprehensive analysis of potential address dusting activity based on the data provided.

Your analysis should be structured as follows:

### Dusting Pattern
- Identify the pattern of dust transactions
- Analyze the timing, frequency, and amount of dust transactions
- Evaluate how the targets were selected
- Determine the scale of the dusting campaign

### Source Analysis
- Evaluate the source(s) of dusting transactions
- Analyze the attacker's wallet(s) and their transaction history
- Identify any patterns that reveal the attacker's identity or motives
- Assess the sophistication level of the attacker

### Purpose Assessment
- Analyze the likely purpose of the dusting (tracking, phishing, address poisoning, etc.)
- Evaluate whether this is targeted or broad-spectrum dusting
- Assess any follow-up transactions or attempts to capitalize on the dusting
- Determine what information the attacker may be trying to gather

### Similar Addresses
- Identify addresses with similar patterns that may be related
- Analyze addresses with similar naming or structure to the victim address
- Detect potential address poisoning attempts
- Evaluate connections between addresses in the attack network

### Conclusion
- Provide an overall assessment of the dusting campaign
- Assign a severity rating on a scale of 1-10
- Recommend protective measures for the targeted addresses
- Suggest further investigative steps

Be specific about dusting techniques identified and support your conclusions with the data provided. Focus on the unique characteristics of this attack and how it compares to known dusting campaigns.
"""
        # Added default templates for wallet, transaction, and generic
        elif analysis_type == "wallet":
            return """
# Wallet Profiling Analysis

## Context
You are an AI expert in blockchain analysis, specializing in wallet profiling and classification. Your task is to analyze the provided wallet data (transactions, interactions, balances) and generate a profile.

## Data
{data}

## Analysis Instructions
Please provide a comprehensive profile of this wallet based on the data provided.

Your analysis should be structured as follows:

### Wallet Classification
- What is the likely primary type of this wallet (e.g., Individual User, Exchange Deposit, Smart Contract, DeFi Protocol, NFT Collector, Bot)?
- Provide a confidence score (1-10) for the primary classification.
- List any secondary classifications and their confidence scores.
- Explain the reasoning behind your classifications based on the data.

### Activity Summary
- Summarize the wallet's key activity metrics (transaction count, volume, active period, token diversity, program interactions).
- Describe the typical transaction patterns (frequency, size, timing).
- Identify the main counterparties (other wallets, contracts, exchanges).

### Behavioral Insights
- What are the dominant behaviors observed (e.g., trading, staking, NFT minting, bridging, receiving airdrops)?
- Are there any unusual or noteworthy patterns in the wallet's behavior?
- How does this wallet's activity compare to typical wallets of its classified type?

### Risk Assessment
- Identify any potential risks associated with this wallet's activity (e.g., interaction with high-risk entities, involvement in suspicious schemes).
- Assign an overall risk score (1-10) based on observed behavior and interactions.

### Conclusion
- Provide a concise summary of the wallet's profile.
- Suggest potential next steps for further investigation if warranted.

Focus on extracting meaningful insights from the provided data to build a clear and accurate profile of the wallet.
"""
        elif analysis_type == "transaction":
            return """
# Transaction Analysis

## Context
You are an AI expert in blockchain transaction analysis. Your task is to analyze the details of the provided blockchain transaction(s) and identify any noteworthy characteristics, potential risks, or suspicious elements.

## Data
{data}

## Analysis Instructions
Please provide a detailed analysis of the transaction(s) based on the data provided.

Your analysis should cover the following aspects:

### Transaction Overview
- Summarize the key details of the transaction (sender, receiver, amount, token, timestamp, involved programs/contracts).
- Explain the likely purpose or nature of the transaction based on context.

### Involved Entities
- Analyze the sender and receiver addresses. What is known about them (labels, history, risk scores)?
- Identify any intermediary addresses or contracts involved.
- Assess the reputation or risk level of the involved entities.

### Financial Aspects
- Evaluate the transaction amount. Is it unusually large or small? Does it fit known patterns (e.g., round numbers)?
- Analyze the token involved. Is it a major cryptocurrency, a stablecoin, or a less common token?
- Consider the USD value of the transaction and its significance.

### Technical Details
- Examine the instructions or function calls within the transaction. Are they standard or unusual?
- Identify the programs or smart contracts interacted with. Are they well-known and audited, or potentially risky?
- Note any complex interactions or multi-step processes within the transaction.

### Risk Assessment
- Identify any red flags or suspicious indicators associated with the transaction (e.g., links to illicit activity, interaction with high-risk services, unusual structure).
- Assess the likelihood that this transaction is part of a larger illicit scheme (e.g., money laundering, scam, exploit).
- Assign a risk score (1-10) to the transaction.

### Conclusion
- Provide an overall assessment of the transaction's nature and risk.
- Suggest any necessary follow-up actions or further analysis.

Focus on interpreting the transaction details within the broader context of blockchain security and financial crime.
"""
        else: # Generic template
            return """
# Security Analysis

## Context
You are an AI expert in blockchain security. Your task is to analyze the provided blockchain data and identify any security concerns, suspicious activity, or noteworthy patterns.

## Data
{data}

## Analysis Instructions
Please provide a comprehensive security analysis based on the data provided.

Your analysis should be structured as follows:

### Entity Identification
- What kind of entity is this (exchange, mixer, individual, etc.)?
- What are the key characteristics of this entity?
- How confident are you in this classification?

### Behavior Patterns
- What patterns of activity are evident?
- Are there any unusual or suspicious transaction patterns?
- How does this behavior compare to typical activity for this entity type?

### Risk Assessment
- What security risks are present?
- Are there signs of malicious activity or vulnerabilities?
- What is the overall risk level for this entity?

### Recommendations
- What further analysis would be valuable?
- What security measures would be appropriate?
- What monitoring should be implemented?

### Conclusion
- Summarize your key findings
- Provide an overall security assessment
- Assign a risk rating on a scale of 1-10

Be specific about patterns you observe and support your conclusions with the data provided.
"""
    
    def analyze(self, data, analysis_type, extra_context=None):
        """
        Perform AI analysis on data
        
        Args:
            data (dict): Data to analyze
            analysis_type (str): Type of analysis
            extra_context (str, optional): Additional context for the analysis
            
        Returns:
            dict: Analysis results
        """
        if not self.ai_available or not self.client:
            logger.warning(f"AI analysis unavailable for {analysis_type}. API key or OpenAI client not configured.")
            # Optionally return a specific structure indicating fallback or unavailability
            return {"error": "AI analysis unavailable", "analysis_type": analysis_type, "method": "unavailable"}

        if not data:
            logger.error("No data provided for analysis")
            return {"error": "No data provided for analysis"}
        
        # Check if we have a template for this analysis type
        # Use 'generic' if the specific type is missing or empty
        template = self.prompt_templates.get(analysis_type)
        if not template:
            logger.warning(f"No template found or template empty for {analysis_type} analysis, using generic template.")
            template = self.prompt_templates.get("generic", self._get_default_template("generic")) # Fallback to default generic

        # Format data for AI input
        formatted_data = self.data_formatter.format_ai_prompt(data, analysis_type, extra_context)
        
        # Create prompt from template
        prompt = template.replace("{data}", formatted_data)
        
        try:
            # Send request to OpenAI API using the new client format
            logger.info(f"Sending {analysis_type} analysis request to OpenAI API (model: {self.model})")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert blockchain security analyst specializing in detecting suspicious activity."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000 # Consider adjusting based on model and expected output length
            )

            # Extract response text using the new response object structure
            if response and response.choices and len(response.choices) > 0:
                analysis_text = response.choices[0].message.content

                # Parse the results
                parsed_result = self.result_parser.parse_analysis_result(analysis_text, analysis_type)

                # Add metadata
                parsed_result["analysis_type"] = analysis_type
                parsed_result["model"] = self.model
                parsed_result["timestamp"] = datetime.now().isoformat()
                parsed_result["method"] = "ai" # Indicate AI was used

                return parsed_result
            else:
                logger.error("Invalid response structure from OpenAI API")
                return {"error": "Invalid response structure from OpenAI API", "raw_response": response}

        except AuthenticationError as auth_err:
             logger.error(f"OpenAI Authentication Error: {str(auth_err)}. Check your API key.")
             return {"error": "OpenAI Authentication Error. Check API Key configuration."}
        except RateLimitError as rate_err:
             logger.error(f"OpenAI Rate Limit Error: {str(rate_err)}. Consider adding delays or requesting higher limits.")
             return {"error": "OpenAI Rate Limit Error. Please try again later."}
        except Exception as e:
             # Catch other potential API errors or general exceptions
             logger.error(f"Error performing AI analysis: {str(e)}")
             return {"error": f"Error performing AI analysis: {str(e)}"}
    
    def batch_analyze(self, data_list, analysis_type, extra_context=None):
        """
        Perform batch AI analysis on multiple data points
        
        Args:
            data_list (list): List of data to analyze
            analysis_type (str): Type of analysis
            extra_context (str, optional): Additional context for the analysis
            
        Returns:
            list: List of analysis results
        """
        results = []
        
        for i, data in enumerate(data_list):
            logger.info(f"Analyzing item {i+1}/{len(data_list)}")
            
            # Analyze data
            result = self.analyze(data, analysis_type, extra_context)
            results.append(result)
            
            # Rate limiting (to avoid hitting OpenAI rate limits)
            if i < len(data_list) - 1:
                time.sleep(1)
        
        return results

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text using AI.
        Falls back to basic analysis when AI is unavailable.
        
        Args:
            text: Text content to analyze
            
        Returns:
            Analysis results as a dictionary
        """
        if not self.ai_available or not OPENAI_AVAILABLE:
            logger.info("AI analysis unavailable, using fallback analysis")
            return self._fallback_text_analysis(text)
        
        try:
            # Simple analysis using OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a blockchain security analyst."},
                    {"role": "user", "content": f"Analyze the following text and identify potential security risks: {text}"}
                ]
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "analysis": analysis,
                "method": "ai",
                "success": True
            }
            
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}. Using fallback analysis.")
            return self._fallback_text_analysis(text)
    
    def _fallback_text_analysis(self, text: str) -> Dict[str, Any]:
        """Simple rule-based text analysis when AI is unavailable."""
        # Simple keyword-based analysis
        risk_keywords = ["hack", "steal", "rug", "scam", "exploit", "vulnerable"]
        risk_score = sum(1 for keyword in risk_keywords if keyword.lower() in text.lower())
        risk_level = "low"
        if risk_score > 3:
            risk_level = "high"
        elif risk_score > 1:
            risk_level = "medium"
            
        return {
            "risk_score": min(risk_score * 20, 100),  # Scale to 0-100
            "risk_level": risk_level,
            "keywords_found": [kw for kw in risk_keywords if kw.lower() in text.lower()],
            "method": "rule-based",
            "success": True
        }
    
    def analyze_transaction_pattern(self, transactions: List[Dict]) -> Dict[str, Any]:
        """
        Analyze transaction patterns to identify suspicious behavior.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Analysis results with risk assessment
        """
        if not transactions:
            return {"error": "No transactions provided", "success": False}
        
        # Basic analysis always runs
        basic_analysis = self._basic_transaction_analysis(transactions)
        
        # Only attempt AI analysis if available
        if self.ai_available and OPENAI_AVAILABLE:
            try:
                # This would be a more sophisticated analysis using the OpenAI API
                # Simplified for this implementation
                return {**basic_analysis, "method": "hybrid"}
            except Exception as e:
                logger.warning(f"AI transaction analysis failed: {e}")
                
        return basic_analysis
    
    def _basic_transaction_analysis(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Basic rule-based transaction pattern analysis."""
        # Simple pattern detection (placeholder implementation)
        tx_count = len(transactions)
        unique_recipients = len(set(tx.get('recipient') for tx in transactions if tx.get('recipient')))
        unique_senders = len(set(tx.get('sender') for tx in transactions if tx.get('sender')))
        
        # Calculate avg transaction value
        values = [float(tx.get('amount', 0)) for tx in transactions if tx.get('amount')]
        avg_value = sum(values) / len(values) if values else 0
        
        # Basic risk assessment
        risk_score = 0
        risk_factors = []
        
        # Check for many small transactions to different addresses
        if tx_count > 20 and unique_recipients > 15 and avg_value < 0.01:
            risk_score += 30
            risk_factors.append("Multiple small transactions to many addresses")
            
        # Check for single large outgoing transaction
        max_value = max(values) if values else 0
        if max_value > 10 * avg_value and avg_value > 0:
            risk_score += 25
            risk_factors.append("Unusually large transaction detected")
        
        # Determine risk level
        risk_level = "low"
        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
            
        return {
            "transaction_count": tx_count,
            "unique_recipients": unique_recipients,
            "unique_senders": unique_senders,
            "avg_transaction_value": avg_value,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "method": "rule-based",
            "success": True
        }

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    # Create AI analyzer
    analyzer = AIAnalyzer()
    
    # Test with sample data
    sample_data = {
        "token_data": {
            "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "name": "Test Token",
            "symbol": "TEST",
            "decimals": 9,
            "supply": 1000000000,
            "creator": "VinesRG7K3ubzKLbxXz197c1RHV3cACkvGr9Zca7BSw",
            "mint_authority": "VinesRG7K3ubzKLbxXz197c1RHV3cACkvGr9Zca7BSw",
            "freeze_authority": "VinesRG7K3ubzKLbxXz197c1RHV3cACkvGr9Zca7BSw"
        },
        "transactions": [
            {
                "signature": "sig1",
                "block_time": "2023-05-01T12:00:00",
                "sender": {"wallet": "VinesRG7K3ubzKLbxXz197c1RHV3cACkvGr9Zca7BSw"},
                "receiver": {"wallet": "wallet2"},
                "amount": 1000000,
                "amount_usd": 1000
            }
        ],
        "patterns": {
            "high_concentration": {
                "score": 0.85,
                "description": "High token concentration in few wallets",
                "evidence": {
                    "top_holder_percentage": 80
                }
            }
        }
    }
    
    # Run analysis
    result = analyzer.analyze(sample_data, "ico")
    
    # Print result
    print(json.dumps(result, indent=2))
