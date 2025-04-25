"""
Result parser for extracting structured data from AI outputs
"""
import json
import logging
import os
import sys
import re
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)

class ResultParser:
    """
    Parse results from AI analysis
    """
    
    def __init__(self):
        pass
    
    def parse_analysis_result(self, ai_output, analysis_type):
        """
        Parse AI analysis result into structured data
        
        Args:
            ai_output (str): Raw AI output
            analysis_type (str): Type of analysis
            
        Returns:
            dict: Parsed analysis result
        """
        if not ai_output:
            return {"error": "No AI output provided"}
        
        # Choose parser based on analysis type
        if analysis_type == "ico":
            return self.parse_ico_analysis(ai_output)
        elif analysis_type == "laundering":
            return self.parse_laundering_analysis(ai_output)
        elif analysis_type == "rugpull":
            return self.parse_rugpull_analysis(ai_output)
        elif analysis_type == "mixer":
            return self.parse_mixer_analysis(ai_output)
        elif analysis_type == "dusting":
            return self.parse_dusting_analysis(ai_output)
        else:
            # Generic parser
            return self.parse_generic_analysis(ai_output)
    
    def parse_ico_analysis(self, ai_output):
        """
        Parse ICO analysis result
        
        Args:
            ai_output (str): Raw AI output
            
        Returns:
            dict: Parsed ICO analysis
        """
        result = {
            "token_info": {},
            "creator_profile": {},
            "funding_flow": {},
            "risk_assessment": {},
            "conclusion": {},
            "raw_analysis": ai_output,
            "timestamp": datetime.now().isoformat()
        }
        
        # Extract token information
        token_info_match = re.search(r'(?:Token Information|Token Info):(.*?)(?:Creator Profile|Creator Info|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if token_info_match:
            token_info_text = token_info_match.group(1).strip()
            
            # Extract token name
            name_match = re.search(r'(?:Name|Token name):\s*(.+?)(?:\n|$)', token_info_text, re.IGNORECASE)
            if name_match:
                result["token_info"]["name"] = name_match.group(1).strip()
            
            # Extract token symbol
            symbol_match = re.search(r'(?:Symbol|Ticker):\s*(.+?)(?:\n|$)', token_info_text, re.IGNORECASE)
            if symbol_match:
                result["token_info"]["symbol"] = symbol_match.group(1).strip()
            
            # Extract token supply
            supply_match = re.search(r'(?:Supply|Total supply):\s*(.+?)(?:\n|$)', token_info_text, re.IGNORECASE)
            if supply_match:
                result["token_info"]["supply"] = supply_match.group(1).strip()
            
            # Extract token price
            price_match = re.search(r'(?:Price|Current price):\s*(.+?)(?:\n|$)', token_info_text, re.IGNORECASE)
            if price_match:
                result["token_info"]["price"] = price_match.group(1).strip()
        
        # Extract creator profile
        creator_profile_match = re.search(r'(?:Creator Profile|Creator Info):(.*?)(?:Funding Flow|Fund Flow|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if creator_profile_match:
            creator_profile_text = creator_profile_match.group(1).strip()
            
            # Extract creator address
            address_match = re.search(r'(?:Address|Wallet):\s*(.+?)(?:\n|$)', creator_profile_text, re.IGNORECASE)
            if address_match:
                result["creator_profile"]["address"] = address_match.group(1).strip()
            
            # Extract creator history
            history_match = re.search(r'(?:History|Background):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', creator_profile_text, re.DOTALL | re.IGNORECASE)
            if history_match:
                result["creator_profile"]["history"] = history_match.group(1).strip()
            
            # Extract other projects
            projects_match = re.search(r'(?:Other projects|Previous tokens):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', creator_profile_text, re.DOTALL | re.IGNORECASE)
            if projects_match:
                projects_text = projects_match.group(1).strip()
                projects = [p.strip() for p in re.split(r'[,;\n]', projects_text) if p.strip()]
                result["creator_profile"]["other_projects"] = projects
        
        # Extract funding flow
        funding_flow_match = re.search(r'(?:Funding Flow|Fund Flow):(.*?)(?:Risk Assessment|Risk Evaluation|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if funding_flow_match:
            funding_flow_text = funding_flow_match.group(1).strip()
            
            # Extract total raised
            raised_match = re.search(r'(?:Total raised|Amount raised):\s*(.+?)(?:\n|$)', funding_flow_text, re.IGNORECASE)
            if raised_match:
                result["funding_flow"]["total_raised"] = raised_match.group(1).strip()
            
            # Extract investor count
            investor_match = re.search(r'(?:Investor count|Number of investors):\s*(.+?)(?:\n|$)', funding_flow_text, re.IGNORECASE)
            if investor_match:
                result["funding_flow"]["investor_count"] = investor_match.group(1).strip()
            
            # Extract distribution
            distribution_match = re.search(r'(?:Distribution|Fund distribution):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', funding_flow_text, re.DOTALL | re.IGNORECASE)
            if distribution_match:
                result["funding_flow"]["distribution"] = distribution_match.group(1).strip()
        
        # Extract risk assessment
        risk_assessment_match = re.search(r'(?:Risk Assessment|Risk Evaluation):(.*?)(?:Conclusion|Summary|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if risk_assessment_match:
            risk_assessment_text = risk_assessment_match.group(1).strip()
            
            # Extract risk factors
            factors = []
            for line in risk_assessment_text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    factors.append(line.strip()[1:].strip())
            
            if factors:
                result["risk_assessment"]["risk_factors"] = factors
            
            # Extract risk level
            level_match = re.search(r'(?:Risk level|Risk rating):\s*(.+?)(?:\n|$)', risk_assessment_text, re.IGNORECASE)
            if level_match:
                result["risk_assessment"]["risk_level"] = level_match.group(1).strip()
        
        # Extract conclusion
        conclusion_match = re.search(r'(?:Conclusion|Summary):(.*?)$', ai_output, re.DOTALL | re.IGNORECASE)
        if conclusion_match:
            conclusion_text = conclusion_match.group(1).strip()
            
            # Extract rating
            rating_match = re.search(r'(?:Rating|Risk rating|Overall rating):\s*(\d+(?:\.\d+)?)\s*(?:\/\s*\d+)?', conclusion_text, re.IGNORECASE)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                    result["conclusion"]["rating"] = rating
                except ValueError:
                    pass
            
            # Extract summary
            result["conclusion"]["summary"] = conclusion_text
        
        return result
    
    def parse_laundering_analysis(self, ai_output):
        """
        Parse money laundering analysis result
        
        Args:
            ai_output (str): Raw AI output
            
        Returns:
            dict: Parsed money laundering analysis
        """
        result = {
            "transaction_patterns": {},
            "fund_flow": {},
            "counterparties": {},
            "risk_assessment": {},
            "conclusion": {},
            "raw_analysis": ai_output,
            "timestamp": datetime.now().isoformat()
        }
        
        # Extract transaction patterns
        patterns_match = re.search(r'(?:Transaction Patterns|Suspicious Patterns):(.*?)(?:Flow of Funds|Fund Flow|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if patterns_match:
            patterns_text = patterns_match.group(1).strip()
            
            # Extract patterns
            patterns = []
            pattern_blocks = re.findall(r'(?:[-*•]|\d+\.)\s+(.+?)(?=(?:[-*•]|\d+\.)\s+|$)', patterns_text, re.DOTALL)
            for block in pattern_blocks:
                pattern_name_match = re.search(r'^(.*?)(?::|-)(.*)$', block.strip(), re.DOTALL)
                if pattern_name_match:
                    pattern = {
                        "name": pattern_name_match.group(1).strip(),
                        "description": pattern_name_match.group(2).strip()
                    }
                else:
                    pattern = {"description": block.strip()}
                patterns.append(pattern)
            
            result["transaction_patterns"]["patterns"] = patterns
        
        # Extract fund flow
        flow_match = re.search(r'(?:Flow of Funds|Fund Flow):(.*?)(?:Counterparties|Entity Analysis|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if flow_match:
            flow_text = flow_match.group(1).strip()
            
            # Extract source
            source_match = re.search(r'(?:Source|Origin):\s*(.+?)(?:\n|$)', flow_text, re.IGNORECASE)
            if source_match:
                result["fund_flow"]["source"] = source_match.group(1).strip()
            
            # Extract destination
            dest_match = re.search(r'(?:Destination|Target):\s*(.+?)(?:\n|$)', flow_text, re.IGNORECASE)
            if dest_match:
                result["fund_flow"]["destination"] = dest_match.group(1).strip()
            
            # Extract path description
            path_match = re.search(r'(?:Path|Route|Flow path):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', flow_text, re.DOTALL | re.IGNORECASE)
            if path_match:
                result["fund_flow"]["path"] = path_match.group(1).strip()
            
            # Extract amount
            amount_match = re.search(r'(?:Amount|Total value|Volume):\s*(.+?)(?:\n|$)', flow_text, re.IGNORECASE)
            if amount_match:
                result["fund_flow"]["amount"] = amount_match.group(1).strip()
        
        # Extract counterparties
        counterparties_match = re.search(r'(?:Counterparties|Entity Analysis):(.*?)(?:Risk Assessment|Risk Evaluation|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if counterparties_match:
            counterparties_text = counterparties_match.group(1).strip()
            
            # Extract key entities
            entities = []
            entity_blocks = re.findall(r'(?:[-*•]|\d+\.)\s+(.+?)(?=(?:[-*•]|\d+\.)\s+|$)', counterparties_text, re.DOTALL)
            for block in entity_blocks:
                entity_name_match = re.search(r'^(.*?)(?::|-)(.*)$', block.strip(), re.DOTALL)
                if entity_name_match:
                    entity = {
                        "name": entity_name_match.group(1).strip(),
                        "description": entity_name_match.group(2).strip()
                    }
                else:
                    entity = {"description": block.strip()}
                entities.append(entity)
            
            result["counterparties"]["entities"] = entities
        
        # Extract risk assessment
        risk_assessment_match = re.search(r'(?:Risk Assessment|Risk Evaluation):(.*?)(?:Conclusion|Summary|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if risk_assessment_match:
            risk_assessment_text = risk_assessment_match.group(1).strip()
            
            # Extract risk factors
            factors = []
            for line in risk_assessment_text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    factors.append(line.strip()[1:].strip())
            
            if factors:
                result["risk_assessment"]["risk_factors"] = factors
            
            # Extract risk level
            level_match = re.search(r'(?:Risk level|Risk rating|Likelihood):\s*(.+?)(?:\n|$)', risk_assessment_text, re.IGNORECASE)
            if level_match:
                result["risk_assessment"]["risk_level"] = level_match.group(1).strip()
        
        # Extract conclusion
        conclusion_match = re.search(r'(?:Conclusion|Summary):(.*?)$', ai_output, re.DOTALL | re.IGNORECASE)
        if conclusion_match:
            conclusion_text = conclusion_match.group(1).strip()
            
            # Extract confidence rating
            rating_match = re.search(r'(?:Confidence|Rating|Score):\s*(\d+(?:\.\d+)?)\s*(?:\/\s*\d+)?', conclusion_text, re.IGNORECASE)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                    result["conclusion"]["confidence"] = rating
                except ValueError:
                    pass
            
            # Extract summary
            result["conclusion"]["summary"] = conclusion_text
        
        return result
    
    def parse_rugpull_analysis(self, ai_output):
        """
        Parse rugpull analysis result
        
        Args:
            ai_output (str): Raw AI output
            
        Returns:
            dict: Parsed rugpull analysis
        """
        result = {
            "token_structure": {},
            "creator_profile": {},
            "liquidity_analysis": {},
            "warning_signs": {},
            "conclusion": {},
            "raw_analysis": ai_output,
            "timestamp": datetime.now().isoformat()
        }
        
        # Extract token structure
        token_structure_match = re.search(r'(?:Token Structure|Token Design):(.*?)(?:Creator Profile|Creator Analysis|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if token_structure_match:
            token_structure_text = token_structure_match.group(1).strip()
            
            # Extract token name and symbol
            name_match = re.search(r'(?:Name|Token name):\s*(.+?)(?:\n|$)', token_structure_text, re.IGNORECASE)
            if name_match:
                result["token_structure"]["name"] = name_match.group(1).strip()
            
            symbol_match = re.search(r'(?:Symbol|Ticker):\s*(.+?)(?:\n|$)', token_structure_text, re.IGNORECASE)
            if symbol_match:
                result["token_structure"]["symbol"] = symbol_match.group(1).strip()
            
            # Extract authorities
            mint_auth_match = re.search(r'(?:Mint authority|Minting authority):\s*(.+?)(?:\n|$)', token_structure_text, re.IGNORECASE)
            if mint_auth_match:
                result["token_structure"]["mint_authority"] = mint_auth_match.group(1).strip()
            
            freeze_auth_match = re.search(r'(?:Freeze authority):\s*(.+?)(?:\n|$)', token_structure_text, re.IGNORECASE)
            if freeze_auth_match:
                result["token_structure"]["freeze_authority"] = freeze_auth_match.group(1).strip()
            
            # Extract concerns
            concerns = []
            for line in token_structure_text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    concerns.append(line.strip()[1:].strip())
            
            if concerns:
                result["token_structure"]["concerns"] = concerns
        
        # Extract creator profile
        creator_profile_match = re.search(r'(?:Creator Profile|Creator Analysis):(.*?)(?:Liquidity Analysis|Liquidity Assessment|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if creator_profile_match:
            creator_profile_text = creator_profile_match.group(1).strip()
            
            # Extract creator address
            address_match = re.search(r'(?:Address|Wallet):\s*(.+?)(?:\n|$)', creator_profile_text, re.IGNORECASE)
            if address_match:
                result["creator_profile"]["address"] = address_match.group(1).strip()
            
            # Extract history
            history_match = re.search(r'(?:History|Background):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', creator_profile_text, re.DOTALL | re.IGNORECASE)
            if history_match:
                result["creator_profile"]["history"] = history_match.group(1).strip()
            
            # Extract other projects
            projects_match = re.search(r'(?:Other projects|Previous tokens):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', creator_profile_text, re.DOTALL | re.IGNORECASE)
            if projects_match:
                projects_text = projects_match.group(1).strip()
                projects = [p.strip() for p in re.split(r'[,;\n]', projects_text) if p.strip()]
                result["creator_profile"]["other_projects"] = projects
            
            # Extract reputation assessment
            reputation_match = re.search(r'(?:Reputation|Assessment):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', creator_profile_text, re.DOTALL | re.IGNORECASE)
            if reputation_match:
                result["creator_profile"]["reputation"] = reputation_match.group(1).strip()
        
        # Extract liquidity analysis
        liquidity_match = re.search(r'(?:Liquidity Analysis|Liquidity Assessment):(.*?)(?:Warning Signs|Red Flags|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if liquidity_match:
            liquidity_text = liquidity_match.group(1).strip()
            
            # Extract current liquidity
            current_match = re.search(r'(?:Current liquidity|Liquidity amount):\s*(.+?)(?:\n|$)', liquidity_text, re.IGNORECASE)
            if current_match:
                result["liquidity_analysis"]["current_liquidity"] = current_match.group(1).strip()
            
            # Extract locked percentage
            locked_match = re.search(r'(?:Locked percentage|Lock status):\s*(.+?)(?:\n|$)', liquidity_text, re.IGNORECASE)
            if locked_match:
                result["liquidity_analysis"]["locked_percentage"] = locked_match.group(1).strip()
            
            # Extract lock expiry
            expiry_match = re.search(r'(?:Lock expiry|Unlock date):\s*(.+?)(?:\n|$)', liquidity_text, re.IGNORECASE)
            if expiry_match:
                result["liquidity_analysis"]["lock_expiry"] = expiry_match.group(1).strip()
            
            # Extract liquidity concerns
            concerns = []
            for line in liquidity_text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    concerns.append(line.strip()[1:].strip())
            
            if concerns:
                result["liquidity_analysis"]["concerns"] = concerns
        
        # Extract warning signs
        warning_match = re.search(r'(?:Warning Signs|Red Flags):(.*?)(?:Conclusion|Summary|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if warning_match:
            warning_text = warning_match.group(1).strip()
            
            # Extract warning signs
            warnings = []
            warning_blocks = re.findall(r'(?:[-*•]|\d+\.)\s+(.+?)(?=(?:[-*•]|\d+\.)\s+|$)', warning_text, re.DOTALL)
            for block in warning_blocks:
                warning_name_match = re.search(r'^(.*?)(?::|-)(.*)$', block.strip(), re.DOTALL)
                if warning_name_match:
                    warning = {
                        "name": warning_name_match.group(1).strip(),
                        "description": warning_name_match.group(2).strip()
                    }
                else:
                    warning = {"description": block.strip()}
                warnings.append(warning)
            
            result["warning_signs"]["warnings"] = warnings
        
        # Extract conclusion
        conclusion_match = re.search(r'(?:Conclusion|Summary):(.*?)$', ai_output, re.DOTALL | re.IGNORECASE)
        if conclusion_match:
            conclusion_text = conclusion_match.group(1).strip()
            
            # Extract rugpull risk rating
            rating_match = re.search(r'(?:Risk rating|Rugpull risk|Rating):\s*(\d+(?:\.\d+)?)\s*(?:\/\s*\d+)?', conclusion_text, re.IGNORECASE)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                    result["conclusion"]["risk_rating"] = rating
                except ValueError:
                    pass
            
            # Extract rugpull likelihood
            likelihood_match = re.search(r'(?:Likelihood|Probability):\s*(.+?)(?:\n|$)', conclusion_text, re.IGNORECASE)
            if likelihood_match:
                result["conclusion"]["likelihood"] = likelihood_match.group(1).strip()
            
            # Extract summary
            result["conclusion"]["summary"] = conclusion_text
        
        return result
    
    def parse_mixer_analysis(self, ai_output):
        """
        Parse mixer analysis result
        
        Args:
            ai_output (str): Raw AI output
            
        Returns:
            dict: Parsed mixer analysis
        """
        result = {
            "operational_pattern": {},
            "user_behavior": {},
            "volume_analysis": {},
            "comparison": {},
            "conclusion": {},
            "raw_analysis": ai_output,
            "timestamp": datetime.now().isoformat()
        }
        
        # Extract operational pattern
        pattern_match = re.search(r'(?:Operational Pattern|Operation):(.*?)(?:User Behavior|Usage Patterns|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if pattern_match:
            pattern_text = pattern_match.group(1).strip()
            
            # Extract mixing technique
            technique_match = re.search(r'(?:Technique|Method|Approach):\s*(.+?)(?:\n|$)', pattern_text, re.IGNORECASE)
            if technique_match:
                result["operational_pattern"]["technique"] = technique_match.group(1).strip()
            
            # Extract general description
            result["operational_pattern"]["description"] = pattern_text
        
        # Extract user behavior
        behavior_match = re.search(r'(?:User Behavior|Usage Patterns):(.*?)(?:Volume Analysis|Transaction Volume|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if behavior_match:
            behavior_text = behavior_match.group(1).strip()
            
            # Extract user count
            count_match = re.search(r'(?:User count|Number of users):\s*(.+?)(?:\n|$)', behavior_text, re.IGNORECASE)
            if count_match:
                result["user_behavior"]["user_count"] = count_match.group(1).strip()
            
            # Extract user types
            types_match = re.search(r'(?:User types|Categories):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', behavior_text, re.DOTALL | re.IGNORECASE)
            if types_match:
                types_text = types_match.group(1).strip()
                types = [t.strip() for t in re.split(r'[,;\n]', types_text) if t.strip()]
                result["user_behavior"]["user_types"] = types
            
            # Extract patterns
            patterns = []
            for line in behavior_text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    patterns.append(line.strip()[1:].strip())
            
            if patterns:
                result["user_behavior"]["patterns"] = patterns
            
            # Extract general description
            result["user_behavior"]["description"] = behavior_text
        
        # Extract volume analysis
        volume_match = re.search(r'(?:Volume Analysis|Transaction Volume):(.*?)(?:Comparison|Known Mixers|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if volume_match:
            volume_text = volume_match.group(1).strip()
            
            # Extract total volume
            total_match = re.search(r'(?:Total volume|Overall volume):\s*(.+?)(?:\n|$)', volume_text, re.IGNORECASE)
            if total_match:
                result["volume_analysis"]["total_volume"] = total_match.group(1).strip()
            
            # Extract average transaction size
            avg_match = re.search(r'(?:Average transaction|Avg transaction size):\s*(.+?)(?:\n|$)', volume_text, re.IGNORECASE)
            if avg_match:
                result["volume_analysis"]["average_transaction"] = avg_match.group(1).strip()
            
            # Extract transaction frequency
            freq_match = re.search(r'(?:Frequency|Transaction frequency):\s*(.+?)(?:\n|$)', volume_text, re.IGNORECASE)
            if freq_match:
                result["volume_analysis"]["frequency"] = freq_match.group(1).strip()
            
            # Extract general description
            result["volume_analysis"]["description"] = volume_text
        
        # Extract comparison
        comparison_match = re.search(r'(?:Comparison|Known Mixers):(.*?)(?:Conclusion|Summary|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if comparison_match:
            comparison_text = comparison_match.group(1).strip()
            
            # Extract similar mixers
            similar_match = re.search(r'(?:Similar to|Comparable with):\s*(.+?)(?:\n|$)', comparison_text, re.IGNORECASE)
            if similar_match:
                similar_text = similar_match.group(1).strip()
                similar = [s.strip() for s in re.split(r'[,;\n]', similar_text) if s.strip()]
                result["comparison"]["similar_mixers"] = similar
            
            # Extract differences
            diff_match = re.search(r'(?:Differences|Distinctions):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', comparison_text, re.DOTALL | re.IGNORECASE)
            if diff_match:
                result["comparison"]["differences"] = diff_match.group(1).strip()
            
            # Extract general description
            result["comparison"]["description"] = comparison_text
        
        # Extract conclusion
        conclusion_match = re.search(r'(?:Conclusion|Summary):(.*?)$', ai_output, re.DOTALL | re.IGNORECASE)
        if conclusion_match:
            conclusion_text = conclusion_match.group(1).strip()
            
            # Extract confidence rating
            rating_match = re.search(r'(?:Confidence|Rating|Score):\s*(\d+(?:\.\d+)?)\s*(?:\/\s*\d+)?', conclusion_text, re.IGNORECASE)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                    result["conclusion"]["confidence"] = rating
                except ValueError:
                    pass
            
            # Extract assessment
            assessment_match = re.search(r'(?:Assessment|Determination):\s*(.+?)(?:\n|$)', conclusion_text, re.IGNORECASE)
            if assessment_match:
                result["conclusion"]["assessment"] = assessment_match.group(1).strip()
            
            # Extract summary
            result["conclusion"]["summary"] = conclusion_text
        
        return result
    
    def parse_dusting_analysis(self, ai_output):
        """
        Parse dusting analysis result
        
        Args:
            ai_output (str): Raw AI output
            
        Returns:
            dict: Parsed dusting analysis
        """
        result = {
            "dusting_pattern": {},
            "source_analysis": {},
            "purpose_assessment": {},
            "similar_addresses": {},
            "conclusion": {},
            "raw_analysis": ai_output,
            "timestamp": datetime.now().isoformat()
        }
        
        # Extract dusting pattern
        pattern_match = re.search(r'(?:Dusting Pattern|Attack Pattern):(.*?)(?:Source Analysis|Attacker Analysis|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if pattern_match:
            pattern_text = pattern_match.group(1).strip()
            
            # Extract pattern type
            type_match = re.search(r'(?:Type|Pattern type):\s*(.+?)(?:\n|$)', pattern_text, re.IGNORECASE)
            if type_match:
                result["dusting_pattern"]["type"] = type_match.group(1).strip()
            
            # Extract frequency
            freq_match = re.search(r'(?:Frequency|Timing):\s*(.+?)(?:\n|$)', pattern_text, re.IGNORECASE)
            if freq_match:
                result["dusting_pattern"]["frequency"] = freq_match.group(1).strip()
            
            # Extract amount
            amount_match = re.search(r'(?:Amount|Dust size):\s*(.+?)(?:\n|$)', pattern_text, re.IGNORECASE)
            if amount_match:
                result["dusting_pattern"]["amount"] = amount_match.group(1).strip()
            
            # Extract targets
            targets_match = re.search(r'(?:Targets|Target selection):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', pattern_text, re.DOTALL | re.IGNORECASE)
            if targets_match:
                result["dusting_pattern"]["targets"] = targets_match.group(1).strip()
            
            # Extract general description
            result["dusting_pattern"]["description"] = pattern_text
        
        # Extract source analysis
        source_match = re.search(r'(?:Source Analysis|Attacker Analysis):(.*?)(?:Purpose Assessment|Intent Analysis|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if source_match:
            source_text = source_match.group(1).strip()
            
            # Extract source address
            address_match = re.search(r'(?:Source address|Attacker address):\s*(.+?)(?:\n|$)', source_text, re.IGNORECASE)
            if address_match:
                result["source_analysis"]["address"] = address_match.group(1).strip()
            
            # Extract profile
            profile_match = re.search(r'(?:Profile|Characteristics):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', source_text, re.DOTALL | re.IGNORECASE)
            if profile_match:
                result["source_analysis"]["profile"] = profile_match.group(1).strip()
            
            # Extract other activities
            activities_match = re.search(r'(?:Other activities|Related attacks):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', source_text, re.DOTALL | re.IGNORECASE)
            if activities_match:
                activities_text = activities_match.group(1).strip()
                activities = [a.strip() for a in re.split(r'[,;\n]', activities_text) if a.strip()]
                result["source_analysis"]["other_activities"] = activities
            
            # Extract general description
            result["source_analysis"]["description"] = source_text
        
        # Extract purpose assessment
        purpose_match = re.search(r'(?:Purpose Assessment|Intent Analysis):(.*?)(?:Similar Addresses|Related Addresses|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if purpose_match:
            purpose_text = purpose_match.group(1).strip()
            
            # Extract primary purpose
            primary_match = re.search(r'(?:Primary purpose|Main intent):\s*(.+?)(?:\n|$)', purpose_text, re.IGNORECASE)
            if primary_match:
                result["purpose_assessment"]["primary_purpose"] = primary_match.group(1).strip()
            
            # Extract likelihood
            likelihood_match = re.search(r'(?:Likelihood|Probability):\s*(.+?)(?:\n|$)', purpose_text, re.IGNORECASE)
            if likelihood_match:
                result["purpose_assessment"]["likelihood"] = likelihood_match.group(1).strip()
            
            # Extract potential impacts
            impacts = []
            for line in purpose_text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    impacts.append(line.strip()[1:].strip())
            
            if impacts:
                result["purpose_assessment"]["potential_impacts"] = impacts
            
            # Extract general description
            result["purpose_assessment"]["description"] = purpose_text
        
        # Extract similar addresses
        similar_match = re.search(r'(?:Similar Addresses|Related Addresses):(.*?)(?:Conclusion|Summary|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if similar_match:
            similar_text = similar_match.group(1).strip()
            
            # Extract addresses
            addresses = []
            address_blocks = re.findall(r'(?:[-*•]|\d+\.)\s+(.+?)(?=(?:[-*•]|\d+\.)\s+|$)', similar_text, re.DOTALL)
            for block in address_blocks:
                address_match = re.search(r'^(.*?)(?::|-)(.*)$', block.strip(), re.DOTALL)
                if address_match:
                    address = {
                        "address": address_match.group(1).strip(),
                        "description": address_match.group(2).strip()
                    }
                else:
                    address = {"description": block.strip()}
                addresses.append(address)
            
            result["similar_addresses"]["addresses"] = addresses
            
            # Extract relationship pattern
            pattern_match = re.search(r'(?:Relationship pattern|Connection pattern):\s*(.+?)(?:\n|$)', similar_text, re.IGNORECASE)
            if pattern_match:
                result["similar_addresses"]["relationship_pattern"] = pattern_match.group(1).strip()
            
            # Extract general description
            result["similar_addresses"]["description"] = similar_text
        
        # Extract conclusion
        conclusion_match = re.search(r'(?:Conclusion|Summary):(.*?)$', ai_output, re.DOTALL | re.IGNORECASE)
        if conclusion_match:
            conclusion_text = conclusion_match.group(1).strip()
            
            # Extract severity rating
            rating_match = re.search(r'(?:Severity|Rating|Score):\s*(\d+(?:\.\d+)?)\s*(?:\/\s*\d+)?', conclusion_text, re.IGNORECASE)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                    result["conclusion"]["severity"] = rating
                except ValueError:
                    pass
            
            # Extract recommended actions
            actions_match = re.search(r'(?:Recommended actions|Recommendations):\s*(.+?)(?:\n\n|\n\d\.|\n[A-Z]|$)', conclusion_text, re.DOTALL | re.IGNORECASE)
            if actions_match:
                actions_text = actions_match.group(1).strip()
                actions = [a.strip() for a in re.split(r'[;\n]', actions_text) if a.strip()]
                result["conclusion"]["recommended_actions"] = actions
            
            # Extract summary
            result["conclusion"]["summary"] = conclusion_text
        
        return result
    
    def parse_generic_analysis(self, ai_output):
        """
        Parse generic analysis result
        
        Args:
            ai_output (str): Raw AI output
            
        Returns:
            dict: Parsed generic analysis
        """
        result = {
            "entity_identification": {},
            "behavior_patterns": {},
            "risk_assessment": {},
            "recommendations": {},
            "conclusion": {},
            "raw_analysis": ai_output,
            "timestamp": datetime.now().isoformat()
        }
        
        # Extract entity identification
        entity_match = re.search(r'(?:Entity Identification|Entity Type):(.*?)(?:Behavior Patterns|Activity Patterns|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if entity_match:
            entity_text = entity_match.group(1).strip()
            
            # Extract entity type
            type_match = re.search(r'(?:Type|Entity type):\s*(.+?)(?:\n|$)', entity_text, re.IGNORECASE)
            if type_match:
                result["entity_identification"]["type"] = type_match.group(1).strip()
            
            # Extract confidence
            confidence_match = re.search(r'(?:Confidence|Certainty):\s*(.+?)(?:\n|$)', entity_text, re.IGNORECASE)
            if confidence_match:
                result["entity_identification"]["confidence"] = confidence_match.group(1).strip()
            
            # Extract characteristics
            characteristics = []
            for line in entity_text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    characteristics.append(line.strip()[1:].strip())
            
            if characteristics:
                result["entity_identification"]["characteristics"] = characteristics
            
            # Extract general description
            result["entity_identification"]["description"] = entity_text
        
        # Extract behavior patterns
        behavior_match = re.search(r'(?:Behavior Patterns|Activity Patterns):(.*?)(?:Risk Assessment|Security Risks|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if behavior_match:
            behavior_text = behavior_match.group(1).strip()
            
            # Extract patterns
            patterns = []
            pattern_blocks = re.findall(r'(?:[-*•]|\d+\.)\s+(.+?)(?=(?:[-*•]|\d+\.)\s+|$)', behavior_text, re.DOTALL)
            for block in pattern_blocks:
                pattern_name_match = re.search(r'^(.*?)(?::|-)(.*)$', block.strip(), re.DOTALL)
                if pattern_name_match:
                    pattern = {
                        "name": pattern_name_match.group(1).strip(),
                        "description": pattern_name_match.group(2).strip()
                    }
                else:
                    pattern = {"description": block.strip()}
                patterns.append(pattern)
            
            result["behavior_patterns"]["patterns"] = patterns
            
            # Extract general description
            result["behavior_patterns"]["description"] = behavior_text
        
        # Extract risk assessment
        risk_match = re.search(r'(?:Risk Assessment|Security Risks):(.*?)(?:Recommendations|Further Analysis|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if risk_match:
            risk_text = risk_match.group(1).strip()
            
            # Extract risk level
            level_match = re.search(r'(?:Risk level|Overall risk):\s*(.+?)(?:\n|$)', risk_text, re.IGNORECASE)
            if level_match:
                result["risk_assessment"]["risk_level"] = level_match.group(1).strip()
            
            # Extract risk factors
            factors = []
            for line in risk_text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    factors.append(line.strip()[1:].strip())
            
            if factors:
                result["risk_assessment"]["risk_factors"] = factors
            
            # Extract general description
            result["risk_assessment"]["description"] = risk_text
        
        # Extract recommendations
        recommendations_match = re.search(r'(?:Recommendations|Further Analysis):(.*?)(?:Conclusion|Summary|\d\.)', ai_output, re.DOTALL | re.IGNORECASE)
        if recommendations_match:
            recommendations_text = recommendations_match.group(1).strip()
            
            # Extract recommendations
            recommendations = []
            for line in recommendations_text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    recommendations.append(line.strip()[1:].strip())
            
            if recommendations:
                result["recommendations"]["items"] = recommendations
            
            # Extract general description
            result["recommendations"]["description"] = recommendations_text
        
        # Extract conclusion
        conclusion_match = re.search(r'(?:Conclusion|Summary):(.*?)$', ai_output, re.DOTALL | re.IGNORECASE)
        if conclusion_match:
            conclusion_text = conclusion_match.group(1).strip()
            
            # Extract rating
            rating_match = re.search(r'(?:Rating|Risk rating|Score):\s*(\d+(?:\.\d+)?)\s*(?:\/\s*\d+)?', conclusion_text, re.IGNORECASE)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                    result["conclusion"]["rating"] = rating
                except ValueError:
                    pass
            
            # Extract summary
            result["conclusion"]["summary"] = conclusion_text
        
        return result

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    # Create result parser
    parser = ResultParser()
    
    # Test with sample ICO analysis
    sample_ico_output = """
# ICO Analysis

## Token Information:
- Name: ExampleToken
- Symbol: EXT
- Supply: 1,000,000,000
- Price: $0.01
- Contract: 0x1234...5678

## Creator Profile:
- Address: 0xabcd...efgh
- History: New developer with no previous projects
- Other projects: None found

## Funding Flow:
- Total raised: $5,000,000
- Investor count: 1,200
- Distribution: 40% to development, 30% to marketing, 20% to team, 10% to reserves

## Risk Assessment:
- Mint authority is still active
- Team wallets hold 40% of supply
- No lock-up period for team tokens
- Limited social media presence
- Vague roadmap with no specific milestones

## Conclusion:
This ICO shows multiple red flags that suggest high risk. The team holds a large portion of the supply without any vesting period, and the mint authority remains active. The project's documentation lacks specificity, and the team's background is unverifiable.

Rating: 8/10 (High Risk)
"""
    
    ico_result = parser.parse_analysis_result(sample_ico_output, "ico")
    print("ICO Analysis Result:")
    print(json.dumps(ico_result, indent=2))
    
    # Test with sample money laundering analysis
    sample_laundering_output = """
# Money Laundering Analysis

## Transaction Patterns:
- Layering: Multiple intermediate addresses used to obscure the flow of funds
- Smurfing: Large amounts broken into smaller transactions to avoid detection
- Round-trip: Some funds returned to the original address after passing through multiple hops

## Flow of Funds:
- Source: Exchange wallet (Binance)
- Destination: Multiple unidentified wallets
- Path: Funds were sent through 5 intermediate addresses before reaching final destinations
- Amount: Approximately $500,000 total

## Counterparties:
- Wallet A: Known exchange hot wallet
- Wallet B: Previously identified in other suspicious transactions
- Wallet C: New wallet with high velocity of transactions

## Risk Assessment:
- High transaction velocity
- Use of known mixing techniques
- Connection to previously flagged addresses
- Pattern matches known money laundering typologies
- Risk level: High

## Conclusion:
The transaction patterns strongly indicate deliberate obfuscation consistent with money laundering. The use of multiple layering techniques and the connection to previously flagged addresses raise significant concerns.

Confidence: 8/10
"""
    
    laundering_result = parser.parse_analysis_result(sample_laundering_output, "laundering")
    print("\nMoney Laundering Analysis Result:")
    print(json.dumps(laundering_result, indent=2))