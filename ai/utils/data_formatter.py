"""
Data formatter for preparing input data for AI analysis
"""
import json
import logging
import os
import sys
import pandas as pd
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)

class DataFormatter:
    """
    Format data for AI analysis
    """
    
    def __init__(self):
        pass
    
    def format_transaction_data(self, transactions, max_transactions=50):
        """
        Format transaction data for AI analysis
        
        Args:
            transactions (list): List of transactions
            max_transactions (int): Maximum number of transactions to include
            
        Returns:
            str: Formatted transaction data
        """
        if not transactions:
            return "No transaction data available."
        
        # Limit number of transactions
        if len(transactions) > max_transactions:
            transactions = transactions[:max_transactions]
            logger.info(f"Limiting to {max_transactions} transactions")
        
        # Create a pandas DataFrame
        df = pd.DataFrame(transactions)
        
        # Extract key fields
        formatted_data = "Transaction Data:\n\n"
        
        for i, tx in enumerate(transactions):
            formatted_data += f"Transaction #{i+1}:\n"
            
            # Add timestamp
            if 'block_time' in tx:
                formatted_data += f"  Time: {tx['block_time']}\n"
            elif 'blockTime' in tx:
                try:
                    block_time = datetime.fromtimestamp(tx['blockTime']).strftime('%Y-%m-%d %H:%M:%S')
                    formatted_data += f"  Time: {block_time}\n"
                except:
                    formatted_data += f"  Time: {tx['blockTime']}\n"
            
            # Add sender and receiver
            if 'sender' in tx:
                if isinstance(tx['sender'], dict):
                    sender_info = f"{tx['sender'].get('wallet', '')}"
                    if 'entity' in tx['sender'] and tx['sender']['entity']:
                        sender_info += f" (Entity: {tx['sender']['entity'].get('name', '')})"
                    if 'labels' in tx['sender'] and tx['sender']['labels']:
                        sender_info += f" [Labels: {', '.join(tx['sender']['labels'])}]"
                    formatted_data += f"  Sender: {sender_info}\n"
                else:
                    formatted_data += f"  Sender: {tx['sender']}\n"
            
            if 'receiver' in tx:
                if isinstance(tx['receiver'], dict):
                    receiver_info = f"{tx['receiver'].get('wallet', '')}"
                    if 'entity' in tx['receiver'] and tx['receiver']['entity']:
                        receiver_info += f" (Entity: {tx['receiver']['entity'].get('name', '')})"
                    if 'labels' in tx['receiver'] and tx['receiver']['labels']:
                        receiver_info += f" [Labels: {', '.join(tx['receiver']['labels'])}]"
                    formatted_data += f"  Receiver: {receiver_info}\n"
                else:
                    formatted_data += f"  Receiver: {tx['receiver']}\n"
            
            # Add amount
            if 'amount' in tx:
                formatted_data += f"  Amount: {tx['amount']}"
                if 'amount_usd' in tx:
                    formatted_data += f" (${tx['amount_usd']})"
                formatted_data += "\n"
            
            # Add signature
            if 'signature' in tx:
                formatted_data += f"  Signature: {tx['signature']}\n"
            
            # Add program ID
            if 'program_id' in tx:
                formatted_data += f"  Program: {tx['program_id']}\n"
            elif 'program' in tx and isinstance(tx['program'], dict) and 'id' in tx['program']:
                formatted_data += f"  Program: {tx['program']['id']}"
                if 'name' in tx['program']:
                    formatted_data += f" ({tx['program']['name']})"
                formatted_data += "\n"
            
            # Add instruction name
            if 'instruction_name' in tx:
                formatted_data += f"  Instruction: {tx['instruction_name']}\n"
            
            formatted_data += "\n"
        
        return formatted_data
    
    def format_address_data(self, address_data):
        """
        Format address data for AI analysis
        
        Args:
            address_data (dict): Address data
            
        Returns:
            str: Formatted address data
        """
        if not address_data:
            return "No address data available."
        
        formatted_data = "Address Information:\n\n"
        
        # Basic address info
        formatted_data += f"Address: {address_data.get('address', 'Unknown')}\n"
        formatted_data += f"Network: {address_data.get('network', 'solana')}\n"
        
        # Entity information
        if 'entity_name' in address_data and address_data['entity_name']:
            formatted_data += f"Entity: {address_data['entity_name']}\n"
        
        if 'entity_type' in address_data and address_data['entity_type']:
            formatted_data += f"Entity Type: {address_data['entity_type']}\n"
        
        # Labels
        if 'labels' in address_data and address_data['labels']:
            if isinstance(address_data['labels'], list):
                formatted_data += f"Labels: {', '.join(address_data['labels'])}\n"
            else:
                formatted_data += f"Labels: {address_data['labels']}\n"
        
        # Risk information
        if 'risk_score' in address_data and address_data['risk_score'] is not None:
            formatted_data += f"Risk Score: {address_data['risk_score']}/100\n"
        
        if 'risk_level' in address_data and address_data['risk_level']:
            formatted_data += f"Risk Level: {address_data['risk_level']}\n"
        
        if 'risk_factors' in address_data and address_data['risk_factors']:
            if isinstance(address_data['risk_factors'], list):
                formatted_data += "Risk Factors:\n"
                for factor in address_data['risk_factors']:
                    formatted_data += f"  - {factor}\n"
            elif isinstance(address_data['risk_factors'], str):
                try:
                    risk_factors = json.loads(address_data['risk_factors'])
                    formatted_data += "Risk Factors:\n"
                    for factor in risk_factors:
                        if isinstance(factor, dict):
                            formatted_data += f"  - {factor.get('name', '')}: {factor.get('description', '')}\n"
                        else:
                            formatted_data += f"  - {factor}\n"
                except json.JSONDecodeError:
                    formatted_data += f"Risk Factors: {address_data['risk_factors']}\n"
        
        # Activity information
        if 'first_seen' in address_data and address_data['first_seen']:
            formatted_data += f"First Seen: {address_data['first_seen']}\n"
        
        if 'last_seen' in address_data and address_data['last_seen']:
            formatted_data += f"Last Seen: {address_data['last_seen']}\n"
        
        formatted_data += "\n"
        
        return formatted_data
    
    def format_token_data(self, token_data):
        """
        Format token data for AI analysis
        
        Args:
            token_data (dict): Token data
            
        Returns:
            str: Formatted token data
        """
        if not token_data:
            return "No token data available."
        
        formatted_data = "Token Information:\n\n"
        
        # Basic token info
        formatted_data += f"Mint Address: {token_data.get('mint', 'Unknown')}\n"
        
        if 'name' in token_data and token_data['name']:
            formatted_data += f"Name: {token_data['name']}\n"
        
        if 'symbol' in token_data and token_data['symbol']:
            formatted_data += f"Symbol: {token_data['symbol']}\n"
        
        if 'decimals' in token_data and token_data['decimals'] is not None:
            formatted_data += f"Decimals: {token_data['decimals']}\n"
        
        # Supply information
        if 'supply' in token_data and token_data['supply'] is not None:
            formatted_data += f"Total Supply: {token_data['supply']}\n"
        
        # Creator information
        if 'creator' in token_data and token_data['creator']:
            formatted_data += f"Creator: {token_data['creator']}\n"
        
        if 'mint_authority' in token_data and token_data['mint_authority']:
            formatted_data += f"Mint Authority: {token_data['mint_authority']}\n"
        
        if 'freeze_authority' in token_data and token_data['freeze_authority']:
            formatted_data += f"Freeze Authority: {token_data['freeze_authority']}\n"
        
        # Price information
        if 'price_usd' in token_data and token_data['price_usd'] is not None:
            formatted_data += f"Price (USD): ${token_data['price_usd']}\n"
        
        if 'market_cap' in token_data and token_data['market_cap'] is not None:
            formatted_data += f"Market Cap: ${token_data['market_cap']}\n"
        
        # Risk information
        if 'risk_score' in token_data and token_data['risk_score'] is not None:
            formatted_data += f"Risk Score: {token_data['risk_score']}/100\n"
        
        if 'risk_level' in token_data and token_data['risk_level']:
            formatted_data += f"Risk Level: {token_data['risk_level']}\n"
        
        if 'risk_factors' in token_data and token_data['risk_factors']:
            if isinstance(token_data['risk_factors'], list):
                formatted_data += "Risk Factors:\n"
                for factor in token_data['risk_factors']:
                    if isinstance(factor, dict):
                        formatted_data += f"  - {factor.get('name', '')}: {factor.get('description', '')}\n"
                    else:
                        formatted_data += f"  - {factor}\n"
            elif isinstance(token_data['risk_factors'], str):
                try:
                    risk_factors = json.loads(token_data['risk_factors'])
                    formatted_data += "Risk Factors:\n"
                    for factor in risk_factors:
                        if isinstance(factor, dict):
                            formatted_data += f"  - {factor.get('name', '')}: {factor.get('description', '')}\n"
                        else:
                            formatted_data += f"  - {factor}\n"
                except json.JSONDecodeError:
                    formatted_data += f"Risk Factors: {token_data['risk_factors']}\n"
        
        formatted_data += "\n"
        
        return formatted_data
    
    def format_pattern_data(self, pattern_data):
        """
        Format pattern data for AI analysis
        
        Args:
            pattern_data (dict): Pattern data
            
        Returns:
            str: Formatted pattern data
        """
        if not pattern_data:
            return "No pattern data available."
        
        formatted_data = "Detected Patterns:\n\n"
        
        for pattern_name, pattern_info in pattern_data.items():
            formatted_data += f"Pattern: {pattern_name}\n"
            formatted_data += f"  Score: {pattern_info.get('score', 0):.2f}\n"
            formatted_data += f"  Description: {pattern_info.get('description', 'No description')}\n"
            
            # Format evidence
            if 'evidence' in pattern_info and pattern_info['evidence']:
                formatted_data += "  Evidence:\n"
                for key, value in pattern_info['evidence'].items():
                    if isinstance(value, list) and len(value) > 0:
                        formatted_data += f"    {key}:\n"
                        for item in value[:3]:  # Limit to first 3 items
                            if isinstance(item, dict):
                                formatted_data += f"      - {json.dumps(item)}\n"
                            else:
                                formatted_data += f"      - {item}\n"
                    elif isinstance(value, dict):
                        formatted_data += f"    {key}: {json.dumps(value)}\n"
                    else:
                        formatted_data += f"    {key}: {value}\n"
            
            formatted_data += "\n"
        
        return formatted_data
    
    def format_relationship_data(self, relationship_data):
        """
        Format relationship data for AI analysis
        
        Args:
            relationship_data (dict): Relationship data
            
        Returns:
            str: Formatted relationship data
        """
        if not relationship_data:
            return "No relationship data available."
        
        formatted_data = "Entity Relationships:\n\n"
        
        # Direct relationships
        direct_relationships = relationship_data.get('direct', [])
        if direct_relationships:
            formatted_data += "Direct Relationships:\n"
            for i, rel in enumerate(direct_relationships[:5]):  # Limit to first 5 relationships
                formatted_data += f"  {i+1}. "
                if 'direction' in rel and rel['direction'] == 'outgoing':
                    formatted_data += f"To: {rel.get('target', 'Unknown')}"
                else:
                    formatted_data += f"From: {rel.get('source', 'Unknown')}"
                
                if 'transaction_count' in rel:
                    formatted_data += f", Transactions: {rel['transaction_count']}"
                
                if 'total_value_usd' in rel:
                    formatted_data += f", Value: ${rel['total_value_usd']:.2f}"
                
                if 'relationship_types' in rel:
                    formatted_data += f", Types: {', '.join(rel['relationship_types'])}"
                
                formatted_data += "\n"
            
            if len(direct_relationships) > 5:
                formatted_data += f"  ... and {len(direct_relationships) - 5} more direct relationships\n"
        
        # Indirect relationships
        indirect_relationships = relationship_data.get('indirect', [])
        if indirect_relationships:
            formatted_data += "\nIndirect Relationships:\n"
            for i, rel in enumerate(indirect_relationships[:5]):  # Limit to first 5 relationships
                formatted_data += f"  {i+1}. Path: {rel.get('path', 'Unknown')}\n"
            
            if len(indirect_relationships) > 5:
                formatted_data += f"  ... and {len(indirect_relationships) - 5} more indirect relationships\n"
        
        # Central addresses
        central_addresses = relationship_data.get('central_addresses', [])
        if central_addresses:
            formatted_data += "\nCentral Addresses in Network:\n"
            for i, addr in enumerate(central_addresses[:5]):  # Limit to first 5 central addresses
                formatted_data += f"  {i+1}. {addr.get('address', 'Unknown')}, Centrality: {addr.get('combined_centrality', 0):.4f}\n"
        
        # Communities
        communities = relationship_data.get('communities', [])
        if communities:
            formatted_data += "\nAddress Communities:\n"
            for i, comm in enumerate(communities[:3]):  # Limit to first 3 communities
                formatted_data += f"  {i+1}. Community (Size: {comm.get('size', 0)}): "
                formatted_data += ", ".join([addr[:8] + "..." for addr in comm.get('addresses', [])[:5]])
                if len(comm.get('addresses', [])) > 5:
                    formatted_data += f"... and {len(comm.get('addresses', [])) - 5} more"
                formatted_data += "\n"
        
        formatted_data += "\n"
        
        return formatted_data
    
    def format_ai_prompt(self, data, analysis_type, extra_context=None):
        """
        Format AI prompt for specific analysis type
        
        Args:
            data (dict): Data for analysis
            analysis_type (str): Type of analysis
            extra_context (str, optional): Additional context for the prompt
            
        Returns:
            str: Formatted AI prompt
        """
        if not data:
            return "No data available for analysis."
        
        # Base prompt
        prompt = f"# Analysis Request: {analysis_type.title()} Analysis\n\n"
        
        if extra_context:
            prompt += f"{extra_context}\n\n"
        
        # Add relevant data sections based on analysis type
        if analysis_type == "ico":
            # ICO analysis needs token and transaction data
            if 'token_data' in data:
                prompt += self.format_token_data(data['token_data'])
            
            if 'creator_data' in data:
                prompt += self.format_address_data(data['creator_data'])
            
            if 'transactions' in data:
                prompt += self.format_transaction_data(data['transactions'])
            
            if 'patterns' in data:
                prompt += self.format_pattern_data(data['patterns'])
            
            if 'relationships' in data:
                prompt += self.format_relationship_data(data['relationships'])
            
            # Add specific ICO analysis instructions
            prompt += """
# Analysis Instructions
Please provide a comprehensive analysis of this Initial Coin Offering (ICO) or token launch based on the data provided. 
Your analysis should cover:

1. Token Information: Basic details about the token
2. Creator Profile: Analysis of the creator wallet and its history
3. Funding Flow: How funds were raised and distributed
4. Risk Assessment: Evaluation of potential risks and red flags
5. Conclusion: Overall assessment with a risk rating (1-10)

Be specific about patterns you observe and support your conclusions with the data provided.
"""
        
        elif analysis_type == "laundering":
            # Money laundering analysis needs transaction and pattern data
            if 'address_data' in data:
                prompt += self.format_address_data(data['address_data'])
            
            if 'transactions' in data:
                prompt += self.format_transaction_data(data['transactions'])
            
            if 'patterns' in data:
                prompt += self.format_pattern_data(data['patterns'])
            
            if 'relationships' in data:
                prompt += self.format_relationship_data(data['relationships'])
            
            # Add specific money laundering analysis instructions
            prompt += """
# Analysis Instructions
Please provide a comprehensive analysis of potential money laundering activity based on the data provided.
Your analysis should cover:

1. Transaction Patterns: Identify suspicious transaction patterns and explain why they are concerning
2. Flow of Funds: Trace the flow of funds through the network
3. Counterparties: Analyze the entities involved in suspicious transactions
4. Risk Assessment: Evaluate the likelihood that this activity represents money laundering
5. Conclusion: Overall assessment with a confidence rating (1-10)

Be specific about techniques you identify (layering, smurfing, etc.) and support your conclusions with the data provided.
"""
        
        elif analysis_type == "rugpull":
            # Rugpull analysis needs token and liquidity data
            if 'token_data' in data:
                prompt += self.format_token_data(data['token_data'])
            
            if 'creator_data' in data:
                prompt += self.format_address_data(data['creator_data'])
            
            if 'liquidity_data' in data:
                prompt += f"Liquidity Information:\n"
                for key, value in data['liquidity_data'].items():
                    prompt += f"  {key}: {value}\n"
                prompt += "\n"
            
            if 'patterns' in data:
                prompt += self.format_pattern_data(data['patterns'])
            
            if 'relationships' in data:
                prompt += self.format_relationship_data(data['relationships'])
            
            # Add specific rugpull analysis instructions
            prompt += """
# Analysis Instructions
Please provide a comprehensive analysis of the rugpull risk for this token based on the data provided.
Your analysis should cover:

1. Token Structure: Analyze token design, authorities, and supply
2. Creator Profile: Evaluate the creator's history and other projects
3. Liquidity Analysis: Assess the token's liquidity and any locking mechanisms
4. Warning Signs: Identify specific red flags that suggest rugpull risk
5. Conclusion: Overall assessment with a rugpull risk rating (1-10)

Be specific about warning signs and support your conclusions with the data provided.
"""
        
        elif analysis_type == "mixer":
            # Mixer analysis needs transaction and pattern data
            if 'address_data' in data:
                prompt += self.format_address_data(data['address_data'])
            
            if 'transactions' in data:
                prompt += self.format_transaction_data(data['transactions'])
            
            if 'patterns' in data:
                prompt += self.format_pattern_data(data['patterns'])
            
            if 'relationships' in data:
                prompt += self.format_relationship_data(data['relationships'])
            
            # Add specific mixer analysis instructions
            prompt += """
# Analysis Instructions
Please provide a comprehensive analysis of this potential mixing service based on the data provided.
Your analysis should cover:

1. Operational Pattern: How this mixing service appears to operate
2. User Behavior: Patterns in how users interact with the service
3. Volume Analysis: Assessment of transaction volumes and frequency
4. Comparison: How this compares to known mixing services
5. Conclusion: Confidence level that this is a mixing service (1-10)

Be specific about mixing techniques identified and support your conclusions with the data provided.
"""
        
        elif analysis_type == "dusting":
            # Dusting analysis needs transaction and pattern data
            if 'address_data' in data:
                prompt += self.format_address_data(data['address_data'])
            
            if 'transactions' in data:
                prompt += self.format_transaction_data(data['transactions'])
            
            if 'patterns' in data:
                prompt += self.format_pattern_data(data['patterns'])
            
            if 'relationships' in data:
                prompt += self.format_relationship_data(data['relationships'])
            
            # Add specific dusting analysis instructions
            prompt += """
# Analysis Instructions
Please provide a comprehensive analysis of potential address dusting activity based on the data provided.
Your analysis should cover:

1. Dusting Pattern: Identify the pattern of dust transactions
2. Source Analysis: Evaluate the source(s) of dusting transactions
3. Purpose Assessment: Analyze the likely purpose of the dusting (tracking, phishing, etc.)
4. Similar Addresses: Identify addresses with similar patterns that may be related
5. Conclusion: Overall assessment of the dusting campaign with a severity rating (1-10)

Be specific about dusting techniques identified and support your conclusions with the data provided.
"""
        
        else:
            # Generic analysis
            if 'address_data' in data:
                prompt += self.format_address_data(data['address_data'])
            
            if 'token_data' in data:
                prompt += self.format_token_data(data['token_data'])
            
            if 'transactions' in data:
                prompt += self.format_transaction_data(data['transactions'])
            
            if 'patterns' in data:
                prompt += self.format_pattern_data(data['patterns'])
            
            if 'relationships' in data:
                prompt += self.format_relationship_data(data['relationships'])
            
            # Add generic analysis instructions
            prompt += """
# Analysis Instructions
Please provide a comprehensive security analysis based on the data provided.
Your analysis should cover:

1. Entity Identification: What kind of entity is this (exchange, mixer, individual, etc.)?
2. Behavior Patterns: What patterns of activity are evident?
3. Risk Assessment: What security risks are present?
4. Recommendations: What further analysis would be valuable?
5. Conclusion: Overall security assessment with a risk rating (1-10)

Be specific about patterns you observe and support your conclusions with the data provided.
"""
        
        return prompt

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    # Create data formatter
    formatter = DataFormatter()
    
    # Test with sample data
    sample_transactions = [
        {
            "signature": "sig1",
            "block_time": "2023-05-01T12:00:00",
            "sender": {"wallet": "wallet1", "entity": {"name": "Exchange A"}, "labels": ["exchange"]},
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
        }
    ]
    
    formatted_tx = formatter.format_transaction_data(sample_transactions)
    print(formatted_tx)
    
    sample_address_data = {
        "address": "wallet1",
        "network": "solana",
        "entity_name": "Exchange A",
        "entity_type": "exchange",
        "labels": ["exchange", "high_volume"],
        "risk_score": 25,
        "risk_level": "low",
        "risk_factors": ["known_exchange", "regulated"]
    }
    
    formatted_addr = formatter.format_address_data(sample_address_data)
    print(formatted_addr)
    
    # Test prompt formatting
    sample_data = {
        "address_data": sample_address_data,
        "transactions": sample_transactions,
        "patterns": {
            "high_volume": {
                "score": 0.85,
                "description": "High transaction volume",
                "evidence": {
                    "transaction_count": 1000,
                    "daily_average": 50
                }
            }
        }
    }
    
    prompt = formatter.format_ai_prompt(sample_data, "laundering")
    print(prompt)